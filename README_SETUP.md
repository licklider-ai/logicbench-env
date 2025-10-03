
# LogicBench × GPT 評価 環境セットアップ手順（Python優先・低工数）

最終更新: 2025-10-02

この手順は、**Pythonだけ**で LogicBench × GPT の評価環境を最小構成で準備するためのものです。  
コマンドは macOS / Linux / Windows（PowerShell）で動く標準的なものを想定しています。

---

## 1. 事前準備（インストール）
1) **Python 3.11 以上** をインストール  
   - macOS: `python3 --version` で確認（なければ公式インストーラまたは Homebrew）  
   - Windows: Microsoft Store または公式インストーラで Python を導入  
   - Linux: ディストリ標準パッケージか pyenv 等

2) **Git** と **エディタ（VS Code 推奨）** を用意  
   - VS Code では「Python」拡張機能を入れておくと便利です。

---

## 2. プロジェクトの作成（このフォルダの使い方）
このスターターは以下の構成です：
```
logicbench_env/
  data/         # 入力データ（LogicBenchサンプル等）
  scripts/      # 実行スクリプト（後で追加）
  runs/         # 生出力・採点結果（自動生成）
  reports/      # 集計・レポート（自動生成）
  configs/      # 設定（例: モデル名・パラメータ）
  .env.example  # 秘密情報の雛形（コピーして .env を作成）
  requirements.txt
  .gitignore
  README_SETUP.md
```

---

## 3. 仮想環境の作成と起動
- macOS / Linux:
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```
- Windows (PowerShell):
  ```powershell
  python -m venv .venv
  .venv\Scripts\Activate.ps1
  ```

> 以降のコマンドは仮想環境が **有効化された状態** で実行します。

---

## 4. 依存パッケージのインストール
```bash
pip install -U pip
pip install -r requirements.txt
```

- 最小セットに絞っています（pandas, pydantic, typer, orjson, rich, jsonschema, matplotlib, openpyxl）。  
- 後から必要に応じて追加してください。

---

## 5. 秘密情報（APIキー）の設定
1) `.env.example` をコピーして `.env` を作成  
2) `OPENAI_API_KEY` 等の値を設定（※鍵は**絶対に**共有しない・Git管理しない）

> スクリプト側では `os.environ` または `python-dotenv` で読み込みます（必要に応じて requirements に追加）。

---

## 6. 設定ファイル（configs）
- `configs/settings.example.json` を `settings.json` にコピーして編集  
- 例：モデル名・温度・最大トークン・採点ルールなど
- `configs/synonyms.example.json` は堅牢性テスト用の簡易同義語辞書の雛形です。必要に応じて `synonyms.json` として利用します。

---

## 7. データの準備
- `data/` に LogicBench の **サブセット** を配置（JSONL/CSV など）  
- PoC 段階では **全体の10〜30%** を層化抽出し、開発用・検証用・最終評価用に分割してください。

---

## 8. 実行スクリプトの配置
- `scripts/` に以下の3つを用意する想定（後で追加）：
  - `run_eval.py`：モデル実行（要点サマリ＋最終回答のJSON出力）
  - `score.py`：自動採点（厳密一致／数値許容／自由記述の正規化）
  - `report.py`：集計・簡易レポート（CSV/Excel/HTML）

> まずは `run_eval.py → score.py → report.py` の **3ステップだけ** で回すのが低工数です。

---

## 9. ログと命名規則
- 実行のたびに `run_id` を採番し、`runs/` 配下に成果物を保存  
- ファイル名例：`dev_raw_<model>_T0_<date>_<run_id>.jsonl`  
- ログ列の最小セット：`dataset_id, sample_id, run_id, model, temperature, seed, input_tokens, output_tokens, total_tokens, latency_ms, status, parsed_json`

---

## 10. 共有（Google スプレッドシート）
- `score.py` が出力する CSV をそのまま **スプレッドシートにインポート**  
- 列例：`run_id, model, subset, sample_id, final_answer, gold, correct, latency_ms, input_tokens, output_tokens`  
- 承認欄（Approved/Approver/Date）をシートに追加して、意思決定を記録します。

---

## 11. 品質ゲート（目安）
- 正答率（Acc） ≥ 80%  
- 再現性 ≥ 90%（温度固定）  
- 堅牢性（軽微変換）：一致率 ≥ 70% **または** 正答率低下 ≤ 10pp  
- 重大な論理破綻（−2） ≤ 2%  
- コスト：正答1件あたりトークン上限内

---

## 12. よくあるつまずき
- **JSON以外の出力が混ざる** → プロンプトで「**JSONのみ**」を強制  
- **答えの型がバラバラ** → タスク別にフォーマット（選択肢/数値/短文）を固定  
- **説明が冗長でコスト増** → 要点サマリは **2–4行** に制限  
- **評価が重い** → 人手は **10–20% 抜き取り** に限定

---

## 13. 次の一手（任意）
- `python-dotenv` で `.env` 自動ロード  
- `ruff`/`black` でコード整形を自動化  
- `duckdb` で軽量クエリ集計  
- `gspread` 等でスプレッドシート自動更新（必要になったら）

以上です。まずはこのフォルダを開き、仮想環境作成 → 依存インストール → `.env`/設定ファイル作成 の順で着手してください。


---

## クイックスタート（お試しラン）
1) 仮想環境を有効化し、`pip install -r requirements.txt`

2) サンプルで実行（APIキー未設定でもDRY-RUN可）:
   - `python scripts/run_eval.py data/dev.jsonl runs/dev_raw.jsonl`
   - `python scripts/score.py runs/dev_raw.jsonl data/gold.jsonl runs/dev_scored.csv`
   - `python scripts/report.py runs/dev_scored.csv reports/summary.csv`

3) 本番実行（APIキー設定後）: `.env` に `OPENAI_API_KEY` を設定し、同コマンドで実行すると実API呼び出しになります。
