# 🧩 LogicBench テストレポート（改善後テンプレ）— 2025-10-07

## 1) 概要
- ブランチ/Commit: （記入）
- モデル: gpt-4o-mini
- データ: data/dev_20.jsonl
- 出力: runs/pred_after_fix.jsonl

## 2) 評価結果（貼付欄）
### Overall
# === Overall Accuracy ===
# Total: __  Correct: __  Acc: __%
### By Category
# （eval出力を貼付）
### Token/Cost
# （eval出力を貼付）

## 3) 改善内容
- 「Answer: YES/NO」強制
- normalize_pred 改修（TRUE/FALSE/T/F/Y/N/1/0 等）

## 4) 以前との比較
- 以前: Acc 0.00%（20/0）
- 今回: Acc __%（__/20）
- 差分: +__%

## 5) 次アクション
- 取りこぼしカテゴリの Few-shot 追加／ルール最短定義を前置

