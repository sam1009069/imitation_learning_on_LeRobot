#!/usr/bin/env python3
"""ACT（Action Chunking with Transformers）の学習（講義資料 第5回 p.45〜46, p.49）。

設定:
  - configs/train_config.yaml  : ハイパーパラメータ
  - configs/crane_features.py  : 特徴量定義

実行:  pixi run train
wandb を使わない場合でも、<output_directory>/loss_log.csv に loss が残る。

LeRobot の examples/3_train_policy.py をベースにした構成（Apache-2.0）。
"""
import csv
import random
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_config_py, load_yaml  # noqa: E402

from lerobot.common.datasets.lerobot_dataset import LeRobotDataset, LeRobotDatasetMetadata  # noqa: E402
from lerobot.common.datasets.utils import dataset_to_policy_features  # noqa: E402
from lerobot.common.policies.act.configuration_act import ACTConfig  # noqa: E402
from lerobot.common.policies.act.modeling_act import ACTPolicy  # noqa: E402
from lerobot.configs.types import FeatureType  # noqa: E402


def main():
    cfg = load_yaml("configs/train_config.yaml")
    dataset_root = Path(cfg["dataset_root"])
    repo_id = cfg["repo_id"]
    out_dir = Path(cfg["output_directory"])
    device = torch.device(cfg["device"])
    out_dir.mkdir(parents=True, exist_ok=True)

    # 再現性のため乱数を固定
    seed = cfg.get("seed", 1000)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    use_wandb = cfg.get("use_wandb", False)
    if use_wandb:
        import wandb

        wandb.init(project=cfg.get("wandb_project", "pai1_crane_spin"), config=cfg)

    # 特徴量 -> 入力(observation.*) と 出力(action) に分ける
    features = dataset_to_policy_features(load_config_py(cfg["config_path"]).features)
    output_features = {k: v for k, v in features.items() if v.type is FeatureType.ACTION}
    input_features = {k: v for k, v in features.items() if k not in output_features}
    print("input_features :", list(input_features))
    print("output_features:", list(output_features))

    meta = LeRobotDatasetMetadata(repo_id, root=dataset_root)
    act_cfg = ACTConfig(
        input_features=input_features,
        output_features=output_features,
        chunk_size=cfg["chunk_size"],
        n_action_steps=cfg["n_action_steps"],
    )
    policy = ACTPolicy(act_cfg, dataset_stats=meta.stats)
    policy.train()
    policy.to(device)

    dataset = LeRobotDataset(repo_id, root=dataset_root, delta_timestamps=cfg["delta_timestamps"])
    print(f"データセット: {dataset.num_episodes} エピソード / {len(dataset)} フレーム")
    loader = torch.utils.data.DataLoader(
        dataset,
        num_workers=cfg["num_workers"],
        batch_size=cfg["batch_size"],
        shuffle=True,
        pin_memory=False,
        drop_last=True,
    )
    optimizer = torch.optim.Adam(policy.parameters(), lr=cfg["learning_rate"])

    total = cfg["training_steps"]
    log_freq = cfg["log_freq"]
    step = 0
    with open(out_dir / "loss_log.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["step", "loss"])
        while step < total:
            for batch in loader:
                batch = {k: (v.to(device) if isinstance(v, torch.Tensor) else v) for k, v in batch.items()}
                # ACT は観測を (B, D) で受け取るので、時間方向の次元(長さ1)を取り除く
                batch["observation.state"] = batch["observation.state"][:, -1, :]
                batch["observation.environment_state"] = batch["observation.environment_state"][:, -1, :]
                loss, _ = policy.forward(batch)
                loss.backward()
                optimizer.step()
                optimizer.zero_grad()

                if step % log_freq == 0:
                    print(f"step: {step} loss: {loss.item():.4f}")
                    writer.writerow([step, f"{loss.item():.6f}"])
                    f.flush()
                    if use_wandb:
                        wandb.log({"loss": loss.item(), "step": step})
                step += 1
                if step >= total:
                    break

    policy.save_pretrained(out_dir)
    print(f"学習済みモデルを保存しました: {out_dir}")
    if use_wandb:
        wandb.finish()


if __name__ == "__main__":
    main()
