#!/usr/bin/env python3
"""rosbag2 -> LeRobotDataset 変換（講義資料 第5回 p.42〜43, p.47〜48）。

- configs/conversion_config.yaml : 入力bag・出力先・fps・トピック名
- configs/crane_features.py      : 特徴量・repo_id・task_name

処理の流れ（講義 p.47〜48 の「変換の処理詳細」と同じ）
  1. 設定を読み、LeRobotDataset.create で空のデータセットを作る
  2. bag_dir 以下の rosbag2（metadata.yaml があるフォルダ）をエピソードとして探す
  3. 各エピソードから /joint_states と アーム・グリッパ指令 を読む
  4. 共通の時間範囲を fps 間隔でサンプリング（直前値保持）
  5. observation.state / action を1フレームずつ追加して save_episode()

実行:  pixi run convert
"""
import shutil
import sys
import traceback
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    load_config_py,
    load_yaml,
    make_target_times,
    reorder_by_name,
    sample_and_hold,
)

CONFIG_PATH = Path("configs/conversion_config.yaml")


def read_episode(episode_dir, cfg):
    """1つのbagから必要なトピックだけ読み、関節名で並べ替えて返す。"""
    from rosbags.rosbag2 import Reader
    from rosbags.serde import deserialize_cdr

    topics = cfg["topics"]
    arm_names = cfg["arm_joint_names"]
    grip_name = cfg["gripper_joint_name"]
    wanted_state = arm_names + [grip_name]

    j_t, j_v, a_t, a_v, g_t, g_v = [], [], [], [], [], []
    with Reader(episode_dir) as reader:
        conns = [c for c in reader.connections if c.topic in topics.values()]
        for conn, ts, raw in reader.messages(connections=conns):
            msg = deserialize_cdr(raw, conn.msgtype)
            if conn.topic == topics["joint_states"]:
                j_t.append(ts)
                j_v.append(reorder_by_name(list(msg.name), msg.position, wanted_state))
            elif conn.topic == topics["arm_command"]:
                if not msg.points:
                    continue
                a_t.append(ts)
                a_v.append(reorder_by_name(list(msg.joint_names), msg.points[0].positions, arm_names))
            elif conn.topic == topics["gripper_command"]:
                if not msg.points:
                    continue
                g_t.append(ts)
                g_v.append(reorder_by_name(list(msg.joint_names), msg.points[0].positions, [grip_name]))

    for name, arr in (("joint_states", j_t), ("arm_command", a_t), ("gripper_command", g_t)):
        if not arr:
            raise RuntimeError(f"{episode_dir}: トピック {name} のメッセージがありません（ros2 bag info で確認）")
    return (
        (np.array(j_t), np.array(j_v)),
        (np.array(a_t), np.array(a_v)),
        (np.array(g_t), np.array(g_v)),
    )


def episode_to_arrays(episode_data, fps):
    """読み込んだ非同期データを fps 周期に揃えた (state, action) にする。"""
    (j_t, j_v), (a_t, a_v), (g_t, g_v) = episode_data
    start = max(j_t[0], a_t[0], g_t[0])
    end = min(j_t[-1], a_t[-1], g_t[-1])
    target_times = make_target_times(start, end, fps)
    state = sample_and_hold(j_t, j_v, target_times)             # (T, 5)
    arm = sample_and_hold(a_t, a_v, target_times)               # (T, 4)
    grip = sample_and_hold(g_t, g_v, target_times)              # (T, 1)
    action = np.hstack([arm, grip])                              # (T, 5)
    return state.astype(np.float32), action.astype(np.float32)


def create_dataset(output_dir, fps, feat_cfg):
    from lerobot.common.datasets.lerobot_dataset import LeRobotDataset

    while True:
        try:
            return LeRobotDataset.create(
                repo_id=feat_cfg.repo_id,
                fps=fps,
                root=output_dir,
                robot_type=feat_cfg.robot_type,
                features=feat_cfg.features,
                use_videos=True,
            ), output_dir
        except FileExistsError:
            print(f"[警告] {output_dir} は既に存在します。")
            ans = input("上書きしますか？ (y: 上書き / n: 別の名前を指定): ").strip().lower()
            if ans == "y":
                shutil.rmtree(output_dir)
            else:
                output_dir = output_dir.parent / input("新しいフォルダ名: ").strip()


def main():
    import torch

    cfg = load_yaml(CONFIG_PATH)
    feat_cfg = load_config_py(cfg["config"])
    fps = cfg.get("target_freq", 20)
    pad = cfg.get("pad_to_longest", True)

    bag_root = Path(cfg["bag_dir"]).resolve()
    episode_dirs = sorted(p.parent for p in bag_root.rglob("metadata.yaml"))
    if not episode_dirs:
        raise FileNotFoundError(f"rosbag2 のエピソードが見つかりません: {bag_root}")
    print(f"{len(episode_dirs)} エピソードを検出")

    # 1周目: 読み込み＋リサンプリング（最長エピソードを知るため）
    episodes = []
    for d in episode_dirs:
        try:
            state, action = episode_to_arrays(read_episode(d, cfg), fps)
            episodes.append((d, state, action))
            print(f"  {d.name}: {len(state)} フレーム ({len(state) / fps:.1f} 秒)")
        except Exception as e:  # noqa: BLE001
            print(f"  [スキップ] {d}: {e}")
    if not episodes:
        raise RuntimeError("変換できるエピソードがありません")
    max_frames = max(len(s) for _, s, _ in episodes)

    dataset, out = create_dataset(Path(cfg["output_dir"]).resolve(), fps, feat_cfg)

    # 2周目: データセットへ追加
    for idx, (d, state, action) in enumerate(episodes):
        try:
            n = max_frames if pad else len(state)
            for i in range(n):
                k = min(i, len(state) - 1)  # 足りない分は最終フレームで埋める
                dataset.add_frame(
                    {
                        "observation.state": torch.from_numpy(state[k]),
                        "observation.environment_state": torch.from_numpy(state[k]),
                        "action": torch.from_numpy(action[k]),
                        "task": feat_cfg.task_name,
                    }
                )
            dataset.save_episode()
            print(f"エピソード {idx} ({d.name}) 保存: {n} フレーム")
        except Exception:  # noqa: BLE001
            print(f"[エラー] {d}")
            traceback.print_exc()
    print(f"\nデータセットを保存しました: {dataset.root}")


if __name__ == "__main__":
    main()
