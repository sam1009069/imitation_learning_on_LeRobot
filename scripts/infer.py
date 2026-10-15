#!/usr/bin/env python3
"""学習した ACT 方策を Gazebo の CRANE+ V2 にデプロイする ROS 2 ノード（講義資料 第5回 p.50〜51）。

  /joint_states を subscribe -> 方策で推論 -> 関節指令トピックに publish

事前に:
  1. Gazebo を起動:  ros2 launch crane_plus_gazebo crane_plus_with_table.launch.py
  2. テレオペノード(teleop_keyboard)は必ず止める（キーを押さなくても20Hzで指令を出し続け、方策と衝突する）
  3. ROS 2 の環境を読み込んだターミナルで実行（コンテナの標準ターミナルなら読み込み済み）

実行:  pixi run infer
       pixi run infer --model-path /home/ubuntu/checkpoints/train/crane_plus_spin_act
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_yaml, reorder_by_name  # noqa: E402

import rclpy  # noqa: E402
from rclpy.node import Node  # noqa: E402
from sensor_msgs.msg import JointState  # noqa: E402
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint  # noqa: E402

from lerobot.common.policies.act.modeling_act import ACTPolicy  # noqa: E402


class InferenceNode(Node):
    def __init__(self, cfg):
        super().__init__("crane_plus_act_infer")
        self.arm_names = cfg["arm_joint_names"]
        self.grip_name = cfg["gripper_joint_name"]
        self.t_from_start = float(cfg.get("time_from_start_sec", 0.1))
        topics = cfg["topics"]

        self.arm_pub = self.create_publisher(JointTrajectory, topics["arm_command"], 10)
        self.grip_pub = self.create_publisher(JointTrajectory, topics["gripper_command"], 10)
        self.create_subscription(JointState, topics["joint_states"], self.on_joint_state, 10)

        self.policy = ACTPolicy.from_pretrained(cfg["model_path"])
        self.policy.eval()
        self.policy.reset()
        self.latest_state = None
        self.create_timer(1.0 / cfg.get("rate_hz", 20), self.step)
        self.get_logger().info(f"model loaded: {cfg['model_path']}")

    def on_joint_state(self, msg: JointState):
        # 学習時と同じ並び [joint1, joint2, joint3, joint4, gripper] に、名前で並べ替える
        vals = reorder_by_name(list(msg.name), msg.position, self.arm_names + [self.grip_name])
        self.latest_state = np.array(vals, dtype=np.float32)

    def step(self):
        if self.latest_state is None:
            return
        state = torch.from_numpy(self.latest_state).unsqueeze(0)  # (1, 5)
        obs = {"observation.state": state, "observation.environment_state": state}
        with torch.no_grad():
            action = self.policy.select_action(obs).cpu().numpy().flatten()  # (5,)

        self.arm_pub.publish(self._traj(self.arm_names, action[:4]))
        self.grip_pub.publish(self._traj([self.grip_name], action[4:5]))
        print("action:", np.round(action[:4], 4), "gripper:", round(float(action[4]), 4))

    def _traj(self, joint_names, positions):
        jt = JointTrajectory()
        jt.joint_names = list(joint_names)
        pt = JointTrajectoryPoint()
        pt.positions = [float(x) for x in positions]
        pt.time_from_start.sec = int(self.t_from_start)
        pt.time_from_start.nanosec = int((self.t_from_start % 1) * 1e9)
        jt.points.append(pt)
        return jt


def main():
    parser = argparse.ArgumentParser(description="ACT 推論ノード（CRANE+ V2 / ROS 2）")
    parser.add_argument("--config", default="configs/infer_config.yaml")
    parser.add_argument("--model-path", default=None, help="学習済みモデルのフォルダ（省略時は設定ファイルの値）")
    args = parser.parse_args()

    cfg = load_yaml(args.config)
    if args.model_path:
        cfg["model_path"] = args.model_path

    rclpy.init()
    node = InferenceNode(cfg)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
