#!/bin/bash
# Linux / macOS / WSL 用: 演習用Dockerコンテナを作成・起動する（講義資料 第5回 p.9 と同等）
# 使い方（リポジトリのルートで）:  ./scripts/run_container.sh
# macOS で警告が出る場合は docker run に `--platform linux/amd64` を追加（講義 p.9）
set -e
NAME=pai_ros2
IMAGE=airobotbook/ros2-desktop-ai-robot-book-humble:latest

if docker ps -a --format '{{.Names}}' | grep -qx "$NAME"; then
  echo "コンテナ $NAME は既にあります。起動します。"
  docker start "$NAME"
else
  docker pull "$IMAGE"
  docker run -d --name "$NAME" \
    -p 6080:80 --shm-size=512m \
    -p 9090:9090 -p 9876:9876 \
    -v "$(pwd)":/workspace \
    "$IMAGE"
fi
echo "ブラウザで http://localhost:6080/ を開いてください。"
