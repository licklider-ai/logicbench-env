# LogicBench × GPT 評価環境（Python優先・低工数）
*Last updated: 2025-10-03*

本リポジトリは、**LogicBench を用いた GPT の論理推論評価**を、**Python 単体・低工数・高再現性**で回すためのスターターです。  
WSL / macOS / Linux 向け。**APIキー無し（DRY-RUN）でも配線確認が可能**です。

---

## 🧭 TL;DR（最速手順）
```bash
# 1) 依存インストール（仮想環境推奨）
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt

# 2) DRY-RUN（APIキー不要）
python scripts/run_eval.py data/dev.jsonl runs/dev_raw.jsonl
python scripts/score.py runs/dev_raw.jsonl data/gold.jsonl runs/dev_scored.csv
python scripts/report.py runs/dev_scored.csv reports/summary.csv

# 3) 実APIで回す（任意）
# .env を作成: OPENAI_API_KEY=sk-...
# その後に 2) と同じ3本を実行
```

---

## 🎯 目的と評価原則
- **目的**：LogicBench による GPT の論理推論力を **正答率 / 再現性 / 堅牢性 / コスト**の観点で軽量に測定
- **原則**：
  - **低工数**：重厚なMLOpsや外部DBを避け、スクリプト3本で完結
  - **再現性**：バージョン固定・フォーマット固定・ログの完全保存
  - **Python優先**：実行・整形・集計を Python だけで行う

---

## 📁 ディレクトリ構成
```
logicbench_env/
├─ data/                  # 入力データ（JSONL）とゴールド（正解）
│  ├─ dev.jsonl           # 例: { "id":"ex1","prompt":"..." }
│  └─ gold.jsonl          # 例: { "id":"ex1","answer":"Yes" }
├─ scripts/               # 実行・採点・レポート
│  ├─ run_eval.py         # モデル実行（DRY-RUN対応）
│  ├─ score.py            # 採点（頑健なフォールバック実装）
│  └─ report.py           # 集計（CSV/簡易可視化）
├─ configs/               # 設定・堅牢性用辞書
│  ├─ settings.json       # モデル名/温度/リトライ等
│  └─ synonyms.example.json
├─ runs/                  # 生出力・中間成果物（Git管理外）
├─ reports/               # 集計結果（Git管理外）
├─ .env.example           # 環境変数テンプレ（APIキー用）
├─ requirements.txt
└─ README.md              # このファイル
```

---

## 🔧 セットアップ
### 要件
- Python **3.11+**
- OS: WSL(Ubuntu) / macOS / Linux
- VS Code 推奨（Remote - WSL 拡張）

### 仮想環境と依存
```bash
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt
```

---

## ▶️ 実行方法
### A. DRY-RUN（APIキー不要）
ダミー応答で配線とログを確認します。
```bash
python scripts/run_eval.py data/dev.jsonl runs/dev_raw.jsonl
python scripts/score.py runs/dev_raw.jsonl data/gold.jsonl runs/dev_scored.csv
python scripts/report.py runs/dev_scored.csv reports/summary.csv
```
出力例：
- `runs/dev_raw.jsonl`（生出力）
- `runs/dev_scored.csv`（採点）
- `reports/summary.csv`（acc / avg_latency_ms / n）

### B. 本番モード（実API）※任意
1) `.env` を作成：
```
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```
> **注意**：1行のみ／空白・引用符・重複行禁止。  
> 401 が出る場合は、キー末尾の不可視文字混入や重複を疑ってください。

2) A と同じ 3 コマンドで実行（DRY-RUN警告が消え、`avg_latency_ms > 0` になります）。

---

## 🧪 入力データ形式（JSONL）
- **問題**：`data/dev.jsonl`
```json
{"id":"ex1","prompt":"AさんはBさんより年上。BさんはCさんより年上。最年長は？"}
{"id":"ex2","prompt":"今日は雨？ yes/no で答えて"}
```
- **正解**：`data/gold.jsonl`
```json
{"id":"ex1","answer":"A"}
{"id":"ex2","answer":"Yes"}
```

---

## 📊 指標とレポート
- **正答率（acc）**：`runs/dev_scored.csv` → `reports/summary.csv`
- **平均レイテンシ（avg_latency_ms）**：実API時のみ有意
- **件数（n）**：採点対象数

`score.py` は以下の**頑健化**を実施：
- `parsed` が無い場合でも `raw_text` から **JSON/数値/Yes-No** を抽出
- 文字正規化（`True/False/はい/いいえ` → `Yes/No` 等）
- 数値は許容誤差で比較（将来拡張用）

---

## 🔀 A/B テスト（低コスト運用）
- `configs/settings.json` で温度や出力フォーマットの差分を保持
- **プロンプト文**はスクリプト内のテンプレを ID 切替（例：`--prompt_id` を追加して運用）
- 比較指標：**acc とコスト（出力トークン）**を中心に、差が大きい場合のみ有意性検定

---

## 🧱 軽量堅牢性テスト（任意）
- `configs/synonyms.example.json` をベースに **同義語置換・語順変更・不要一文挿入** を適用した問題を生成
- 既存フロー（run_eval → score → report）にそのまま流すだけで、**変換前後の Acc を比較**可能

---

## 🔐 セキュリティと Git 運用
- `.env`・`.venv`・`runs/`・`reports/` は **Git 管理対象外**（`.gitignore` 済み）
- APIキーは **公開リポに絶対入れない**。漏えい時は**即ローテーション**
- GitHub へ push する場合：
  ```bash
  git init && git add . && git commit -m "init"
  git branch -M main
  git remote add origin https://github.com/<you>/logicbench-env.git
  git push -u origin main
  ```
  認証は **PAT（Personal Access Token）** 推奨（`repo` 権限）。

---

## 🩺 トラブルシューティング
- **401 invalid_api_key**：
  - `.env` の重複行を削除（`OPENAI_API_KEY` は 1 行のみ）
  - キー末尾の不可視文字を除去（`tr -cd 'A-Za-z0-9-_'` など）
  - 新規キーを**完全表示**で再発行して貼り直し
- **Windows パスを WSL に渡して失敗**：`C:\` ではなく `/mnt/c/...` を使用、または `wslpath` で変換
- **`file -i` の使い方**：`file -i <path>`（`-i` とパスの間は**半角スペース**）
- **`python3-venv` が無い**：`sudo apt-get install -y python3-venv`
- **モデルの JSON が揺れて採点できない**：付属 `score.py` は `raw_text` フォールバックで吸収します

---

## 📝 よくある質問（FAQ）
**Q. APIキーは環境構築に必要？**  
A. **不要**。DRY-RUN で配線確認まで可能。本番計測時のみ必要です。

**Q. どのモデルを使うべき？**  
A. 既定は `configs/settings.json` の `model_name` を参照。権限のある軽量モデル（例：`gpt-4o-mini`）から開始し、必要に応じて切り替え。

**Q. 出力が JSON にならない**  
A. プロンプトで **JSON出力のみ**を強制。どうしても崩れる場合は `score.py` がフォールバックします。

---

## 📄 ライセンス
社内利用想定。外部公開時は適切なライセンス表記を追加してください。

---

## 🤝 コントリビューション
- Issue / PR 歓迎。PR は小さな差分で、再現手順と目的（`feat:`/`fix:`/`chore:`）を明記してください。

---

## 🧩 参考：開発メモ
- 低工数・再現性・Python優先を満たすため、**スクリプト3本**＋**CSV/JSONL**で完結
- A/B と堅牢性は **既存フローに載せるだけ**で評価可能
- DRY-RUN 固定でも配線検証・ログ整備は十分に進められます
