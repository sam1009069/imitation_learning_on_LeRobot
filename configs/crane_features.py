"""CRANE+ V2 旋回タスク用のデータセット定義（講義資料 第5回 p.43 の configs/crane_features.py に対応）。

ここに書いた値は
  - scripts/rosbag2lerobot.py（変換）
  - scripts/train.py（学習）
の両方から読まれる。タスクを変えるときは、まずこのファイルの下側
（repo_id / root / task_name）を書き換える。
"""

# 関節の並び順（このリポジトリ全体でこの順番に統一する）
#   observation.state / action はどちらも 5 次元: [joint1, joint2, joint3, joint4, gripper]
#   joint1 = ベース（旋回軸）。旋回タスクで主に動かすのはここ。
JOINT_NAMES = ["joint1", "joint2", "joint3", "joint4", "gripper"]

features = {
    "observation.state": {
        "dtype": "float32",
        "shape": (5,),
        "names": JOINT_NAMES,
    },
    # ACT は「画像」か「environment_state」のどちらかが必須なので、
    # カメラを使わない今回は state と同じ値を environment_state にも入れる（講義 p.48 と同じ方針）。
    "observation.environment_state": {
        "dtype": "float32",
        "shape": (5,),
        "names": JOINT_NAMES,
    },
    "action": {
        "dtype": "float32",
        "shape": (5,),
        "names": JOINT_NAMES,
    },
}

# ---- 変換（rosbag2lerobot.py）で使う設定 ----
robot_type = "crane_plus"
repo_id = "crane_plus_spin"                                  # データセット名（講義: crane_plus_pekori）
root = "/home/ubuntu/dataset/lerobot_dataset/crane_plus_spin"  # 保存先
task_name = "spin"                                           # タスク名（講義: pekori）
