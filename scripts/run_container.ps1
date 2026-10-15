# Windows (PowerShell) 用: 演習用Dockerコンテナを作成・起動する
# 講義資料 第5回 p.7〜9「演習環境の準備」の Windows 版
#
# 使い方（このリポジトリのフォルダで）:
#   1. Docker Desktop を起動しておく
#   2. PowerShell で:  .\scripts\run_container.ps1
#   3. ブラウザで http://localhost:6080/ を開く（講義と同じ）
#
# ポイント
#   -p 9090:9090 -p 9876:9876 : rerun のWebビューア用（講義 p.7）
#   -v ${PWD}:/workspace       : このリポジトリをコンテナの /workspace に見せる
#                                （Windows側のVS Codeで編集 -> コンテナ内でそのまま実行できる）

$ContainerName = "pai_ros2"
$Image = "airobotbook/ros2-desktop-ai-robot-book-humble:latest"

docker info *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker に接続できません。Docker Desktop を起動してからもう一度実行してください。"
    exit 1
}

$exists = docker ps -a --format "{{.Names}}" | Select-String -Pattern "^$ContainerName$"
if ($exists) {
    Write-Host "コンテナ $ContainerName は既にあります。起動します (docker start)。"
    docker start $ContainerName
} else {
    docker pull $Image
    docker run -d --name $ContainerName `
        -p 6080:80 --shm-size=512m `
        -p 9090:9090 -p 9876:9876 `
        -v "${PWD}:/workspace" `
        $Image
}
Write-Host "ブラウザで http://localhost:6080/ を開いてください。"
