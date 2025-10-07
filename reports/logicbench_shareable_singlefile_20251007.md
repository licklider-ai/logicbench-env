# 📦 LogicBench 共有用ワンファイル・パケット（2025-10-07 JST）

## 1) 実行環境と前提
- モデル: gpt-4o-mini / 20問 / eval_runner.py
- 出力フォーマット: 最終行を「Answer: YES/NO」固定

## 2) 本日の評価結果（貼付用）
Overall: Total=20 Correct=0 Acc=0.00%
Category: 全カテゴリ 0/1
Cost: Prompt=580 / Completion=164 / Est=$0.0054

## 3) 失敗分析と改善
- 正規化不足で YES/NO 一致せず → 全滅
- System prompt で最終行1行のみを強制
- normalize_pred: TRUE/FALSE/T/F/Y/N/1/0 → YES/NO、"Answer:" 行優先抽出

## 4) 再現コマンド
python3 scripts/eval_runner.py data/dev_20.jsonl runs/pred_from_logs.jsonl
# 評価は手元のスクリプト/手順に合わせて実行

## 5) 期待する入出力フォーマット
pred.jsonl: {"id":"...", "prediction":"Answer: YES"}
gold.jsonl: {"id":"...","gold":"YES","category":"..."}

## 6) 次アクション
- 改善版プロンプト＋正規化で再評価
- 必要なら Few-shot 追加
