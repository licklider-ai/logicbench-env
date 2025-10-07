# 🧪 LogicBench ローカルテストレポート（2025-10-07）

## ✅ 概要
- モデル: gpt-4o-mini
- データ: data/dev_20.jsonl（20問）
- 生成: scripts/eval_runner.py
- 評価: eval（YES/NO 厳密一致）

## 📊 Overall Accuracy
Total: 20  Correct: 0  Acc: 0.00%

## 📂 Accuracy by Category（要約）
全カテゴリ 0/1（0.0%）

## 💰 Token Usage & Cost
Prompt=580, Completion=164, in=$0.005, out=$0.015, Est=$0.0054

## 🧭 所感・対応
- 原因: 出力フォーマット逸脱 & 正規化不足
- 対応: 「Answer: YES/NO」強制、normalize_pred 改修案を作成
