# 講義資料（第5回）との対応表

> ⚠️ 講義資料には「許諾なく撮影や第三者への開示を禁止します」とあります。
> この表は**ページ番号と見出しの対応だけ**を書いており、資料の中身は転載していません。
> それでもリポジトリを **Public（公開）にする場合は、このファイル（docs/slide_mapping.md）を削除するか、Private のまま**にしてください。

ページ番号は、スライド右下に印字されている番号です。

## 1. ファイルごとの対応

| このリポジトリのファイル | 内容 | 講義資料のページ | 講義からの変更点 |
|---|---|---|---|
| `pixi.toml` | Python・ffmpeg・rosbags・LeRobot をまとめてインストールする環境定義 | p.31「1. LeRobotの環境構築」 | 講義は `pai_training` の `pyproject.toml` ＋ LeRobot の git submodule。ここでは submodule を使わず、**同じコミットの LeRobot を `pixi.toml` から直接取得**（GitHub Desktop は submodule が扱いにくいため） |
| `pixi.toml` の `[tasks]` | `pixi run convert / train / infer / debug-policy` | p.43（`pixi task list`） | `plot-episode`、`test` を追加 |
| `.gitignore` | Gitに入れないファイルの一覧 | （資料にはない。GitHub利用のため追加） | — |
| `.gitattributes` | 改行コードを LF に統一 | （資料にはない） | Windows で編集 → Linux コンテナで実行するため必要 |
| `.vscode/` | VS Code の推奨拡張機能・設定 | （資料にはない） | 初心者向けの補助 |
| `scripts/run_container.ps1` / `.sh` | Docker コンテナの作成・起動（ポート 6080 / 9090 / 9876、`/workspace` にマウント） | p.7「ポートマッピングの追加」、p.8「既存コンテナの停止」、p.9「起動スクリプトの作成」、p.10（補足） | Windows(PowerShell) 版を追加。コンテナ名 `pai_ros2` は講義と同じ |
| `scripts/setup_ros_workspace.sh` | `physicalai_teleop` の取得・ビルド | p.36「テレオペ用パッケージ取得」 | コマンドを1本のスクリプトにまとめただけ |
| `scripts/record_episode.sh` | rosbag を `ep0, ep1, …` と自動採番して記録 | p.39「お辞儀デモ」、p.40「記録の手順」、p.22（`ros2 bag record -a -o`） | 番号の付け間違い（上書き・欠番）を防ぐ |
| `configs/conversion_config.yaml` | 変換の入力 bag / 出力先 / fps / トピック名 | p.43「変換の実行」 | トピック名・関節名を YAML に出し、`pad_to_longest` を追加 |
| `configs/crane_features.py` | 特徴量（state / action 5次元）、`repo_id`、`task_name` | p.43、p.48（`observation.state` など） | `pekori` → **`spin`**、`crane_plus_pekori` → **`crane_plus_spin`** |
| `scripts/common.py` | 直前値保持リサンプリング、関節名での並べ替え | p.24（非同期データ）、p.48「サンプリングと整形」 | 関節の並びを**名前で揃える**処理を追加（順番ミス防止） |
| `scripts/rosbag2lerobot.py` | rosbag2 → LeRobotDataset 変換 | p.42「rosbag2lerobot変換」、p.47〜48「変換の処理詳細」 | 処理の流れは同じ。時刻列を fps ちょうどの等間隔にした |
| `scripts/plot_episode.py` | 変換後データのグラフ確認 | p.44「変換したデータの可視化」、p.34「可視化のポイント」 | 講義は rerun（Web）。今回はカメラ画像なしなので matplotlib の PNG 出力 |
| `configs/train_config.yaml` | ACT の学習設定、アクションチャンク、wandb 有無 | p.45「学習：ACT」、p.46「wandb」、p.49「アクションチャンク」 | `delta_timestamps.action` は p.49 の指示どおり `[0.0 … 1.5]`。`training_steps` は 200 → 2000 |
| `scripts/train.py` | ACT の学習 | p.45〜46 | wandb を任意にし、`loss_log.csv` を保存 |
| `configs/infer_config.yaml` | 推論ノードの設定（モデルパス・トピック・周期） | p.50「デプロイ」 | 講義はスクリプト内に直書き |
| `scripts/infer.py` | 方策を Gazebo にデプロイする ROS 2 ノード | p.50「デプロイ」、p.51「デプロイ結果」 | 関節の並びを名前で揃える |
| `scripts/debug_policy.py` | 推論と GT の比較（オフラインデバッグ） | p.52「方策のデバッグ」、p.53「デバッグ結果の読み方」 | グラフを PNG 保存 |
| `tests/test_resample.py` | リサンプリング等の単体テスト | （資料にはない） | — |
| `README.md` | 全体の手順書 | p.35「実践演習の全体像」 | — |

## 2. 講義の流れ（工程）と、このリポジトリでの実行コマンド

講義 p.35 の「工程」表に対応させたものです。

| 工程（p.35） | このリポジトリでの実行 |
|---|---|
| テレオペ準備 | `ros2 launch crane_plus_gazebo crane_plus_with_table.launch.py`（p.37）、`ros2 run physicalai_teleop teleop_keyboard`（p.37〜38） |
| データ収集 | `bash /workspace/scripts/record_episode.sh`（p.40） |
| 形式変換 | `pixi run convert`（p.43） |
| （確認） | `pixi run plot-episode --episode-index 0`（p.44） |
| 学習（ACT） | `pixi run train`（p.45） |
| デプロイ | `pixi run infer`（p.50） |
| デバッグ | `pixi run debug-policy --episode-index 1`（p.52） |

## 3. 「お辞儀」→「旋回」で変えたところ

| 項目 | 講義（お辞儀 / pekori） | このリポジトリ（旋回 / spin） |
|---|---|---|
| 動かす関節 | joint3（`Q` を1回押して選択 → `W`） | **joint1**（ベース。起動直後に選択済み → `W`） |
| データ保存先 | `~/dataset/rosbags/pekori/ep*` | `~/dataset/rosbags/spin/ep*` |
| データセット名 | `crane_plus_pekori` | `crane_plus_spin` |
| タスク名 | `pekori` | `spin` |
| 学習済みモデル | `~/checkpoints/train/crane_plus_pekori_act` | `~/checkpoints/train/crane_plus_spin_act` |
| データ・学習・推論のコード | — | **変更なし**（5次元の関節角 → 5次元の action は共通） |
