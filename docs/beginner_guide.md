# 初心者向けガイド：VS Code と GitHub Desktop

対象：`C:\Users\sam10\Documents\PAI1_final_project\imitation_learning_on_LeRobot`

## 0. 用語（これだけ分かれば大丈夫）

| 用語 | 意味 |
|---|---|
| リポジトリ（repository） | Git で履歴管理しているフォルダ。普通のフォルダ＋隠しフォルダ `.git` |
| コミット（commit） | 「ここまでの変更」を履歴に1つ記録すること（セーブポイント） |
| プッシュ（push） | ローカルのコミットを GitHub に送ること |
| `.gitignore` | 「Git に入れないファイル」を書いたリスト |
| ローカル / リモート | 自分のPC / GitHub 上 |

## 1. フォルダを置く

1. 渡した zip を `C:\Users\sam10\Documents\PAI1_final_project\` に展開します。
2. 結果が次の形になっていれば OK です（`imitation_learning_on_LeRobot` の下に直接 `README.md` がある）。

```
PAI1_final_project\
└─ imitation_learning_on_LeRobot\
   ├─ README.md
   ├─ pixi.toml
   ├─ configs\
   ├─ scripts\
   └─ ...
```

## 2. VS Code で開く

1. VS Code を起動 → **File（ファイル）→ Open Folder（フォルダーを開く）** → `imitation_learning_on_LeRobot` を選ぶ。
   - 「作成者を信頼しますか？」と出たら **信頼する**。
2. 右下に「推奨拡張機能をインストールしますか？」と出たら **インストール**（Python / YAML / TOML / Markdown / Docker）。
3. 左のエクスプローラーで `README.md` を右クリック → **Open Preview** で整形表示できます（`Ctrl+Shift+V`）。
4. ターミナルは **Terminal → New Terminal**（`Ctrl+@`）。開いた場所は自動でこのフォルダです。

> 見えない `.gitignore` などは、エクスプローラーにそのまま表示されます（ドット始まりのファイルも標準で表示されます）。

## 3. GitHub Desktop でリポジトリ化して GitHub に上げる

事前に GitHub のアカウントを作り、GitHub Desktop にサインインしておきます（**File → Options → Accounts**）。

### 3-1. ローカルにリポジトリを作る
1. **File → Add local repository…** → `imitation_learning_on_LeRobot` フォルダを選ぶ。
2. 「This directory does not appear to be a Git repository」と出るので、青い文字の **create a repository** をクリック。
3. 画面の項目：
   - Name：`imitation_learning_on_LeRobot`（そのままで OK。GitHub 上の名前になります）
   - Description：`CRANE+ V2 spin imitation learning with LeRobot`（任意）
   - Git ignore：**None**（すでに `.gitignore` があるため）
   - License：後で決めるなら **None**
4. **Create repository** を押す。

### 3-2. 最初のコミット
1. 左側の **Changes** に、ファイルの一覧が出ます。
   - ✅ 確認：`.pixi` フォルダや `*.db3`、`checkpoints` などが**出ていなければ** `.gitignore` が効いています。
2. 左下の Summary に `Initial commit` と入力（Description は空で OK）。
3. **Commit to main** を押す。

### 3-3. GitHub に公開（コピー）する
1. 画面上部の **Publish repository** を押す。
2. **Keep this code private** に ✅ を入れる（非公開）。
   - 講義資料は第三者への開示が禁止されているため、**まずは Private を推奨**します。
   - Public にする場合は `docs/slide_mapping.md` を削除してください。
3. **Publish repository** を押す → ブラウザで github.com の自分のアカウントを開き、リポジトリがあれば成功。

### 3-4. 2回目以降（毎回この流れ）
1. VS Code でファイルを編集して **保存**（`Ctrl+S`）。
2. GitHub Desktop を開くと、変更が **Changes** に出る。
3. Summary に変更内容を書く（例：`旋回用の train_config を調整`）→ **Commit to main**。
4. **Push origin** を押す。

> ふだん使うのはこの4ステップだけです。`pull` / `branch` は慣れてから で大丈夫です。

## 4. やってはいけないこと

| ダメなこと | 理由 | 対策 |
|---|---|---|
| APIキー（wandb など）をファイルに書く | GitHub 上に残って漏れる | キーは `pixi run wandb login` で入力するだけ。`.env` は `.gitignore` 済み |
| 巨大ファイル（rosbag・データセット・学習済みモデル）をコミット | GitHub は1ファイル 100MB まで | `.gitignore` 済み。もし Changes に出ていたらコミットしない |
| `.pixi` フォルダをコミット | 環境本体で数GBになる | `.gitignore` 済み |
| Windows のメモ帳で `.sh` を編集して保存 | 改行が CRLF になりコンテナで動かない | VS Code で編集する（設定で LF 固定済み） |

## 5. コンテナで実行するときの連携イメージ

```
 Windows 側                                     Docker コンテナ（Ubuntu + ROS 2）
 ┌───────────────────────────────┐             ┌────────────────────────────────┐
 │ VS Code で編集                │  マウント    │ /workspace （同じフォルダ）    │
 │ GitHub Desktop で commit/push │ ◀─────────▶ │ pixi run convert / train / …   │
 │ C:\...\imitation_learning_... │             │ ~/dataset, ~/checkpoints       │
 └───────────────────────────────┘             └────────────────────────────────┘
```

- **コードの編集と Git 操作は Windows 側だけ**で行い、**実行はコンテナ内**で行います。
- ロボットデータ（rosbag・データセット・学習済みモデル）はコンテナ内の `~/dataset` と `~/checkpoints` に作られ、リポジトリには入りません。
  - コンテナを `docker rm` すると消えます。残したいときは Windows 側へコピーしてください（README の「データのバックアップ」参照）。
- コンテナ内で最初に `pixi install` をすると `pixi.lock` が作られ、Windows 側のフォルダにも現れます。これは**コミットしてよい**ファイルです（同じ環境を再現するための記録）。

## 6. よくあるつまずき

| 症状 | 対処 |
|---|---|
| PowerShell で「スクリプトの実行が無効」と出る | `powershell -ExecutionPolicy Bypass -File .\scripts\run_container.ps1` で実行 |
| GitHub Desktop の Changes に大量のファイルが出る | `.gitignore` が効いていない可能性。フォルダ直下に `.gitignore` があるか確認 |
| `LF will be replaced by CRLF` という警告 | 無視して OK（`.gitattributes` で扱いを決めてあります） |
| Push で認証エラー | GitHub Desktop の **File → Options → Accounts** で再サインイン |
