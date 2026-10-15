#!/usr/bin/env python3
"""変換したデータセットの確認用プロット（講義資料 第5回 p.44「変換したデータの可視化」, p.34「可視化のポイント」）。

講義では rerun（Webビューア）で action と state の対応を見ていたが、今回のデータは
関節角の時系列だけでカメラ画像が無いので、まずは matplotlib のグラフ(PNG)で確認する。

確認ポイント（p.34）: state と action が時間的に対応しているか / 値の飛び・欠損が無いか /
開始・終了が意図どおりか（旋回なら joint1 だけが滑らかに動いているか）

実行例:
  pixi run plot-episode --episode-index 0
  pixi run plot-episode --all          # 全エピソードを1枚に重ねる（軌道のばらつき確認）
"""
import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_yaml  # noqa: E402

from lerobot.common.datasets.lerobot_dataset import LeRobotDataset  # noqa: E402

JOINTS = ["joint1", "joint2", "joint3", "joint4", "gripper"]


def episode_arrays(dataset, ep):
    a = dataset.episode_data_index["from"][ep].item()
    b = dataset.episode_data_index["to"][ep].item()
    rows = [dataset[i] for i in range(a, b)]
    state = [r["observation.state"].numpy() for r in rows]
    action = [r["action"].numpy() for r in rows]
    return state, action


def main():
    tcfg = load_yaml("configs/train_config.yaml")
    p = argparse.ArgumentParser()
    p.add_argument("--dataset-root", default=tcfg["dataset_root"])
    p.add_argument("--repo-id", default=tcfg["repo_id"])
    p.add_argument("--episode-index", type=int, default=0)
    p.add_argument("--all", action="store_true")
    p.add_argument("--out", default=None)
    args = p.parse_args()

    ds = LeRobotDataset(args.repo_id, root=args.dataset_root)
    eps = range(ds.num_episodes) if args.all else [args.episode_index]
    fig, axes = plt.subplots(len(JOINTS), 1, figsize=(9, 2.2 * len(JOINTS)), sharex=True)
    for ep in eps:
        state, action = episode_arrays(ds, ep)
        for j, ax in enumerate(axes):
            ax.plot([s[j] for s in action], "--", label=f"action ep{ep}")
            ax.plot([s[j] for s in state], label=f"state ep{ep}")
    for j, ax in enumerate(axes):
        ax.set_ylabel(f"{JOINTS[j]} [rad]")
        ax.grid(alpha=0.3)
    axes[0].legend(ncol=4, fontsize=7)
    axes[-1].set_xlabel(f"frame ({ds.fps} fps)")
    fig.tight_layout()
    out = Path(args.out or ("outputs/dataset_all.png" if args.all else f"outputs/episode_{args.episode_index}.png"))
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150)
    print(f"保存しました: {out}")


if __name__ == "__main__":
    main()
