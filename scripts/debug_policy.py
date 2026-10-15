#!/usr/bin/env python3
"""方策のオフラインデバッグ（講義資料 第5回 p.52〜53）。

収集したデータセットの観測を方策に入れ、推論した action と実際の action(GT) を比較する。
  予測がGTとずれている          -> 学習がうまくいっていない（データ量・質・学習設定を見直す）
  予測はGTと一致、デプロイは失敗 -> デプロイ時の観測に汎化していない（初期状態の差・データの多様性）

実行例:
  pixi run debug-policy --episode-index 1
  pixi run debug-policy --dataset-root <...> --repo-id crane_plus_spin --policy-path <...> --episode-index 1
結果のグラフは --out に PNG で保存される（画面表示は --show）。
"""
import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import torch  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_yaml  # noqa: E402

from lerobot.common.datasets.lerobot_dataset import LeRobotDataset  # noqa: E402
from lerobot.common.policies.act.modeling_act import ACTPolicy  # noqa: E402

JOINTS = ["joint1", "joint2", "joint3", "joint4", "gripper"]


def main():
    tcfg = load_yaml("configs/train_config.yaml")
    p = argparse.ArgumentParser()
    p.add_argument("--dataset-root", default=tcfg["dataset_root"])
    p.add_argument("--repo-id", default=tcfg["repo_id"])
    p.add_argument("--policy-path", default=tcfg["output_directory"])
    p.add_argument("--episode-index", type=int, default=0)
    p.add_argument("--device", default="cpu")
    p.add_argument("--out", default="outputs/debug_policy.png")
    p.add_argument("--show", action="store_true")
    args = p.parse_args()

    dataset = LeRobotDataset(args.repo_id, root=args.dataset_root)
    print(f"データセット: {len(dataset)} フレーム / {dataset.num_episodes} エピソード")
    start = dataset.episode_data_index["from"][args.episode_index].item()
    end = dataset.episode_data_index["to"][args.episode_index].item()

    policy = ACTPolicy.from_pretrained(args.policy_path)
    policy.to(args.device)
    policy.eval()
    policy.reset()

    preds, gts = [], []
    for i in range(start, end):
        s = dataset[i]
        obs = {
            "observation.state": s["observation.state"].float().unsqueeze(0).to(args.device),
            "observation.environment_state": s["observation.environment_state"].float().unsqueeze(0).to(args.device),
        }
        with torch.no_grad():
            pred = policy.select_action(obs).squeeze(0).cpu().numpy()
        preds.append(pred)
        gts.append(s["action"].float().numpy())

    preds, gts = np.array(preds), np.array(gts)
    err = np.linalg.norm(preds - gts, axis=1)
    print(f"エピソード {args.episode_index}: 平均L2誤差 = {err.mean():.4f}（{len(err)} フレーム）")
    for j, name in enumerate(JOINTS):
        print(f"  {name}: 平均絶対誤差 = {np.abs(preds[:, j] - gts[:, j]).mean():.4f}")

    fig, ax = plt.subplots(figsize=(10, 6))
    for j, name in enumerate(JOINTS):
        ax.plot(gts[:, j], "--", label=f"GT {name}")
        ax.plot(preds[:, j], label=f"Pred {name}")
    ax.set_xlabel("frame")
    ax.set_ylabel("action [rad]")
    ax.set_title(f"GT vs Predicted action (episode {args.episode_index})")
    ax.legend(loc="upper right", ncol=2, fontsize=8)
    fig.tight_layout()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150)
    print(f"グラフを保存しました: {out}")
    if args.show:
        plt.show()


if __name__ == "__main__":
    main()
