# Eval Report (20251014_114043)

## Overview
- Runs merged: 21
- Total samples: 40
- Overall accuracy: **77.50%**

## Tokens & Cost
- Prompt tokens: 1562
- Completion tokens: 126
- Unit price (/1K): in=$0.150, out=$0.600
- Est. cost: in=$0.234300, out=$0.075600, total=$0.309900

## Per-category accuracy

| category | samples | correct | acc(%) |
|---|---:|---:|---:|
| coding | 8 | 8 | 100.00 |
| knowledge | 12 | 10 | 83.33 |
| devops | 4 | 1 | 25.00 |
| lang | 2 | 0 | 0.00 |
| logic | 2 | 0 | 0.00 |
| category | 0 | 0 | 0.00 |

## Misses (first 20)

| run | id | category | question | model_answer | answer_regex |
|---|---|---|---|---|---|
| runs/20251014_112434 | q19 | lang | 英語で「ありがとう」を答えてください（短く）。 | Thank you. | ^(thank\s*you|thanks)$ |
| runs/20251014_112434 | q7 | knowledge | 2024年はうるう年ですか？はい/いいえのみ。 | はい。 | ^(はい|yes)$ |
| runs/20251014_112434 | q18 | devops | Dockerで実行中コンテナ一覧コマンドは？コマンドのみ。 | `docker ps` | ^docker\s+ps$ |
| runs/20251014_112434 | q11 | logic | 57は奇数ですか？はい/いいえのみ。 | はい。 | ^(はい|yes)$ |
| runs/20251014_113425 | q18 | devops | Dockerで実行中コンテナ一覧コマンドは？コマンドのみ。 | `docker ps` | ^docker\s+ps$ |
| runs/20251014_113425 | q11 | logic | 57は奇数ですか？はい/いいえのみ。 | はい。 | ^(はい|yes)$ |
| runs/20251014_113425 | q17 | devops | Gitで最新コミットの短縮ハッシュを表示するコマンドは？コマンドのみ。 | `git rev-parse --short HEAD` | ^git\s+rev-parse\s+--short\s+HEAD$ |
| runs/20251014_113425 | q19 | lang | 英語で「ありがとう」を答えてください（短く）。 | Thank you. | ^(thank\s*you|thanks)$ |
| runs/20251014_113425 | q7 | knowledge | 2024年はうるう年ですか？はい/いいえのみ。 | はい。 | ^(はい|yes)$ |

## Artifacts
- Combined TSV: `reports/20251014_114043/all_results.tsv`
- Combined CSV: `reports/20251014_114043/all_results.csv`
- Per-category TSV: `reports/20251014_114043/per_category.tsv`
- Misses TSV: `reports/20251014_114043/misses.tsv`
