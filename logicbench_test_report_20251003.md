# LogicBench ローカルテスト報告（2025-10-03）

## 使用コード
- scripts/run_eval.py（推論）
- scripts/score.py（採点）
- scripts/report.py（集計）

## 実行コマンド
```bash
python scripts/run_eval.py data/dev.jsonl runs/dev_raw_fix.jsonl
python scripts/score.py runs/dev_raw_fix.jsonl data/gold.jsonl runs/dev_scored_fix.csv
python scripts/report.py runs/dev_scored_fix.csv reports/summary_fix.csv
```

## 結果（サマリ）
- サンプル数: 3  
- 正答率 (acc): **0.667**  
- 平均レイテンシ: **2382 ms（約2.4秒）**

## 各サンプル
| sample_id | gold | final_answer | correct | latency_ms |
|---|---|---|---:|---:|
| p1 | 7   | 7     | 1 | 2563 |
| p2 | Yes | 不確実 | 0 | 2561 |
| p3 | A   | A     | 1 | 2022 |

## 生成物
- runs/dev_raw_fix.jsonl
- runs/dev_scored_fix.csv
- reports/summary_fix.csv

## 所見
- 環境～実行パイプラインは正常完走。  
- 出力形式と評価規則の整合が課題（例：「不確実」→ Yes/No へ正規化など）。

