"""変換・デプロイで共通して使う関数。

LeRobot や ROS に依存しない処理だけをここに置いている（そのため tests/ で単体テストできる）。
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import yaml


def load_yaml(path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_config_py(path):
    """configs/crane_features.py のような .py 設定ファイルを読み込む。"""
    spec = importlib.util.spec_from_file_location("crane_features", str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sample_and_hold(times, values, target_times):
    """直前値保持（Zero-Order Hold）でリサンプリングする。講義 p.48 の処理。

    times        : (N,)   元データのタイムスタンプ（昇順）
    values       : (N, D) 元データの値
    target_times : (M,)   サンプリングしたい時刻
    戻り値        : (M, D) 各 target_time 以前で一番近いサンプルの値
    """
    times = np.asarray(times)
    values = np.asarray(values)
    if values.ndim == 1:
        values = values.reshape(-1, 1)
    idx = np.searchsorted(times, target_times, side="right") - 1
    idx = np.clip(idx, 0, len(times) - 1)  # 先頭より前の時刻は最初の値を使う
    return values[idx]


def reorder_by_name(names, values, wanted_names, default=0.0):
    """names の並びで入っている values を、wanted_names の順に並べ替える。

    ROSの JointState / JointTrajectory は「関節名のリスト」と「値のリスト」が別になっていて、
    並び順がノードによって違うことがある。名前で引き直すことで順番ミスを防ぐ。
    names が空のときは、すでに wanted_names の順だとみなしてそのまま返す。
    """
    values = list(values)
    if not names:
        out = values[: len(wanted_names)]
        out += [default] * (len(wanted_names) - len(out))
        return out
    table = dict(zip(names, values))
    return [float(table.get(n, default)) for n in wanted_names]


def make_target_times(start_ns: int, end_ns: int, fps: float) -> np.ndarray:
    """start〜end の間を fps ちょうどの等間隔で区切った時刻列 [ns] を返す。"""
    num_frames = int((end_ns - start_ns) * fps / 1e9)
    return start_ns + (np.arange(num_frames) * (1e9 / fps)).astype(np.int64)


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent
