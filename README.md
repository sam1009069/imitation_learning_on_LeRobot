# imitation_learning_on_LeRobot

Gazebo 上の **CRANE+ V2** を `teleop_keyboard` で操作してデータを集め、**LeRobot の ACT** で模倣学習する。
講義「Physical AI 応用編1 第5回」の演習（お辞儀 / pekori）を、**旋回（spin：ベース関節 joint1 を回す）** に変えたもの。

```
 テレオペ準備 → データ収集(rosbag2) → 形式変換(LeRobotDataset) → 学習(ACT) → デプロイ(Gazebo) → デバッグ
```

> 講義資料のどの部分に対応するかは [`docs/slide_mapping.md`](docs/slide_mapping.md)、
> VS Code / GitHub Desktop の使い方は [`docs/beginner_guide.md`](docs/beginner_guide.md) を参照。

## フォルダ構成

```
imitation_learning_on_LeRobot/
├─ README.md                  この文書
├─ pixi.toml                  環境構築（Python / ffmpeg / rosbags / LeRobot）
├─ .gitignore  .gitattributes  Git の設定
├─ .vscode/                   VS Code の推奨拡張機能・設定
├─ configs/
│   ├─ crane_features.py      特徴量・repo_id・task_name（タスク名はここ）
│   ├─ conversion_config.yaml 変換の設定（入力bag・出力先・fps）
│   ├─ train_config.yaml      ACT 学習の設定
│   └─ infer_config.yaml      デプロイ（推論ノード）の設定
├─ scripts/
│   ├─ run_container.ps1/.sh  Docker コンテナの作成・起動
│   ├─ setup_ros_workspace.sh テレオペ用パッケージの取得・ビルド
│   ├─ record_episode.sh      rosbag を ep0, ep1, … と自動採番して記録
│   ├─ rosbag2lerobot.py      rosbag2 → LeRobotDataset 変換
│   ├─ plot_episode.py        変換後データのグラフ確認
│   ├─ train.py               ACT 学習
│   ├─ infer.py               Gazebo へのデプロイ（ROS 2 ノード）
│   ├─ debug_policy.py        推論と正解(GT)の比較
│   └─ common.py              共通関数（リサンプリング等）
├─ tests/test_resample.py     単体テスト
└─ docs/                      資料との対応表・初心者ガイド
```

## 動作環境

- Windows 11 + Docker Desktop（講義と同じ `airobotbook/ros2-desktop-ai-robot-book-humble` イメージ）
- 編集: VS Code ／ バージョン管理: GitHub Desktop
- 実行（ROS 2 / Gazebo / pixi / 学習）はすべて**コンテナ内**（Ubuntu 22.04 + ROS 2 Humble）

## 手順

### 0. 準備（Windows 側・1回だけ）

1. Docker Desktop を起動する。
2. VS Code のターミナル（PowerShell）をこのフォルダで開き、コンテナを作る:
   ```powershell
   .\scripts\run_container.ps1
   ```
   （実行がブロックされる場合: `powershell -ExecutionPolicy Bypass -File .\scripts\run_container.ps1`）
3. ブラウザで <http://localhost:6080/> を開く（デスクトップ画面が出る）。

> このフォルダはコンテナの `/workspace` に見えています。以降の「コンテナ内」の作業は、
> デスクトップ画面の Terminator（`Ctrl+Shift+E` で縦分割 / `Ctrl+Shift+O` で横分割）で行います。

### 1. 環境構築（コンテナ内・1回だけ）

```bash
# pixi のインストール
curl -fsSL https://pixi.sh/install.sh | bash
echo 'eval "$(pixi completion --shell bash)"' >> ~/.bashrc
source ~/.bashrc

# Windows のフォルダ(/workspace)に巨大な環境を作らないための設定
pixi config set detached-environments true

# LeRobot などをインストール（初回は数分〜十数分）
cd /workspace
pixi install
pixi run test          # "all tests passed" と出れば OK
```

テレオペ用の ROS パッケージ（講義と同じ `physicalai_teleop`）:

```bash
bash /workspace/scripts/setup_ros_workspace.sh
```

### 2. シミュレータとテレオペを起動（コンテナ内）

ターミナルを2つ使う。**新しいターミナルを開くたびに** `source ~/pai_ws/install/setup.bash` が必要。

```bash
# ターミナルA: Gazebo + CRANE+ V2
ros2 launch crane_plus_gazebo crane_plus_with_table.launch.py

# ターミナルB: キーボードテレオペ
source ~/pai_ws/install/setup.bash
ros2 run physicalai_teleop teleop_keyboard
```

テレオペのキー: `Q/E` 関節選択、`W/S` 選択中の関節を＋／−、`X` 直立姿勢に戻す、`ESC` 終了。
起動直後は **`Selected joint: crane_plus_joint1`**（= 旋回軸）が選ばれている。

### 3. 旋回デモを 10〜20 エピソード集める（コンテナ内）

1エピソード = 1 rosbag。

```bash
# ターミナルC（新しいターミナル）
bash /workspace/scripts/record_episode.sh      # ep0 が作られ、記録が始まる
```

1. ターミナルB（テレオペ）をクリックし、`Selected joint: crane_plus_joint1` を確認
2. **`W` を 20 回**押して旋回（≒ 1.0 rad ≒ 57°。回数は毎回そろえる）
3. ターミナルCをクリックし、**`Ctrl+C`** で記録停止
4. ターミナルBで **`X`** を1回押して直立姿勢に戻す
5. 1〜4 を繰り返す（次は自動で ep1, ep2, … になる）。終わったらテレオペは `Ctrl+C`

**データ収集のコツ（旋回向け）**

| 注意点 | やり方 |
|---|---|
| 初期状態をそろえる | 毎回 `X` で直立に戻してから記録開始 |
| 軌道を一意にする | `W` の回数を毎回同じにする（今回は 20 回）。向きも1方向に固定 |
| 途中で止めない | 記録開始の直後に動かし、旋回し終えたらすぐ `Ctrl+C` |
| 長さをそろえる | 操作速度（キーを押す速さ）もなるべく一定に |

記録できたか確認: `ros2 bag info ~/dataset/rosbags/spin/ep0`
（`/joint_states`、`/crane_plus_arm_controller/joint_trajectory`、`/crane_plus_gripper_controller/joint_trajectory` が入っていること）

### 4. LeRobotDataset に変換して確認（コンテナ内）

```bash
cd /workspace
pixi run convert                          # configs/conversion_config.yaml に従って変換
pixi run plot-episode --episode-index 0   # outputs/episode_0.png を作る
pixi run plot-episode --all               # 全エピソードを重ねて、ばらつきを確認
```

`outputs/` に PNG ができる（Windows 側の `imitation_learning_on_LeRobot\outputs\` に現れる。Git には入らない）。
**joint1 だけが滑らかに増え、state が action に少し遅れて追従していれば OK。**

### 5. 学習（コンテナ内）

```bash
pixi run train
```

- 設定は `configs/train_config.yaml`（既定: CPU、2000 ステップ、batch 8）
- loss は端末と `~/checkpoints/train/crane_plus_spin_act/loss_log.csv` に出る
- 学習済みモデルは `~/checkpoints/train/crane_plus_spin_act/` に保存される
- wandb でグラフを見たい場合: `use_wandb: true` にして
  ```bash
  pixi add --pypi "wandb>=0.22"    # 古い wandb は新形式のAPIキーで止まるため
  pixi run wandb login
  ```

### 6. デプロイ（コンテナ内）

1. **テレオペノード（teleop_keyboard）を必ず止める**（キー入力がなくても 20Hz で指令を出し続け、方策と衝突する）
2. Gazebo は起動したまま、`X` 相当の直立姿勢の状態で:
   ```bash
   cd /workspace
   pixi run infer
   # モデルを指定する場合
   pixi run infer --model-path /home/ubuntu/checkpoints/train/crane_plus_spin_act
   ```
3. Gazebo 上でロボットが旋回し、端末に推論された `action` が流れれば成功。止めるのは `Ctrl+C`。

> `pixi run infer` は ROS 2 の環境（`rclpy`）が必要。コンテナの標準ターミナルなら読み込み済み。
> `ModuleNotFoundError: rclpy` が出たら `source /opt/ros/humble/setup.bash` を実行して再試行。

### 7. うまく動かないとき：デバッグ

```bash
pixi run debug-policy --episode-index 1     # outputs/debug_policy.png を作る
```

| データセット上での比較 | デプロイ時 | 考えられる原因・次の一手 |
|---|---|---|
| 予測が GT とずれる | 動かない | 学習不足 → `training_steps` を増やす、データ量・品質を見直す |
| 予測は GT とよく一致 | 動かない | デプロイ時の観測に汎化していない → 初期状態の差を確認、データの多様性を増やす |
| 予測は GT とよく一致 | 動く | OK。エピソードや条件を変えて評価を続ける |

まず「学習データ上で正しく振る舞えるか」を確認してから、汎化を疑う。

## 設定を変えたいとき

| やりたいこと | 変更する場所 |
|---|---|
| 別のタスク名にする（例: `spin2`） | `configs/crane_features.py`（`repo_id` / `root` / `task_name`）、`configs/conversion_config.yaml`、`configs/train_config.yaml`、`configs/infer_config.yaml` のパス、`record_episode.sh spin2` |
| 学習を長く / GPU で回す | `configs/train_config.yaml` の `training_steps` / `device: "cuda"` |
| 変換のサンプリング周期 | `configs/conversion_config.yaml` の `target_freq`（`train_config.yaml` の `delta_timestamps` は `1/target_freq` の倍数にする） |
| 往復する旋回にする（拡張課題） | `W` を 20 回 → `S` を 20 回、のように操作を決めてデータを集め直す |

## データのバックアップ

ロボットデータはコンテナ内（`~/dataset`, `~/checkpoints`）にあり、**コンテナを削除すると消えます**。残したいときは Windows 側の PowerShell で:

```powershell
docker cp pai_ros2:/home/ubuntu/dataset  .\backup\dataset
docker cp pai_ros2:/home/ubuntu/checkpoints  .\backup\checkpoints
```

`backup/` は `.gitignore` に入れてあるので、このフォルダ直下に作っても Git には上がりません。

## 困ったとき

| 症状 | 対処 |
|---|---|
| `Cannot connect to the Docker daemon` | Docker Desktop を起動する |
| `pixi install` が遅い / 容量が増え続ける | `pixi config set detached-environments true` を設定済みか確認 |
| `HTTP Error` / `Too many requests` | Hugging Face 側の制限。数秒空けて再実行 |
| 変換で「トピックのメッセージがありません」 | `ros2 bag info` でトピック名を確認し、`conversion_config.yaml` の `topics` を直す |
| ロボットが動かない / 暴れる | テレオペノードが動いたままでないか確認（デプロイ時は必ず停止） |
| エラー全文が長い | 実行したコマンド・環境・エラー全文をそのまま検索 / 生成AI に渡す |

## クレジット

- [LeRobot](https://github.com/huggingface/lerobot)（Hugging Face, Apache-2.0）。`pixi.toml` で講義と同じコミットに固定
- 講義の演習リポジトリ [matsuolab/pai_training](https://github.com/matsuolab/pai_training) / [matsuolab/physicalai_teleop](https://github.com/matsuolab/physicalai_teleop) の構成を参考にしています
- 講義: 松尾・岩澤研究室「Physical AI 応用編1 2026」第5回（講義資料の内容はこのリポジトリに含めていません）
