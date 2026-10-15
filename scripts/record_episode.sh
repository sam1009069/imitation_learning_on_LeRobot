#!/bin/bash
# 1エピソード分の rosbag を、ep0, ep1, ... と番号を自動で増やして記録する。
# 講義資料 第5回 p.40「データ収集：記録の手順」の
#   ros2 bag record -a -o ~/dataset/rosbags/pekori/ep0
# を、番号の付け間違い（上書き・欠番）が起きないようにしたもの。
#
# 使い方（コンテナ内。Gazeboとテレオペノードを起動した状態で、新しいターミナルから）:
#   bash /workspace/scripts/record_episode.sh          # 既定: ~/dataset/rosbags/spin
#   bash /workspace/scripts/record_episode.sh my_task  # タスク名を変える場合
# 旋回し終えたら、このターミナルで Ctrl+C を押して記録を止める。
set -e
TASK=${1:-spin}
DIR=$HOME/dataset/rosbags/$TASK
mkdir -p "$DIR"

N=0
while [ -e "$DIR/ep$N" ]; do N=$((N+1)); done

echo "記録開始: $DIR/ep$N   （止めるには Ctrl+C）"
ros2 bag record -a -o "$DIR/ep$N"
echo "保存しました: $DIR/ep$N"
echo "次の手順: テレオペのターミナルで x を押して直立姿勢に戻してから、もう一度このスクリプトを実行"
