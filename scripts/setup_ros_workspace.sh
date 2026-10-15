#!/bin/bash
# コンテナ内で1回だけ実行: テレオペ用パッケージ physicalai_teleop を取得・ビルドする
# 講義資料 第5回 p.36「テレオペ用パッケージ取得」と同じ手順
#   コンテナ内で:  bash /workspace/scripts/setup_ros_workspace.sh
set -e
mkdir -p ~/pai_ws/src
cd ~/pai_ws/src
[ -d physicalai_teleop ] || git clone https://github.com/matsuolab/physicalai_teleop.git

cd ~/pai_ws
rosdep install --from-paths src --ignore-src -r -y          # 依存パッケージ
colcon build --symlink-install --packages-select physicalai_teleop

echo
echo "完了。新しいターミナルで次を実行すると使えるようになります:"
echo "  source ~/pai_ws/install/setup.bash"
