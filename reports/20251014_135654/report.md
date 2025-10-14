# Eval Report (20251014_135654)

## Overview
- Runs merged: 42
- Total samples: 80
- Overall accuracy: **77.50%**

## Tokens & Cost
- Prompt tokens: 3124
- Completion tokens: 252
- Unit price (/1K): in=$0.150, out=$0.600
- Est. cost: in=$0.468600, out=$0.151200, total=$0.619800

## Per-category accuracy

| category | samples | correct | acc(%) |
|---|---:|---:|---:|
| coding | 16 | 16 | 100.00 |
| knowledge | 24 | 20 | 83.33 |
| devops | 8 | 2 | 25.00 |
| lang | 4 | 0 | 0.00 |
| logic | 4 | 0 | 0.00 |
| category | 0 | 0 | 0.00 |

## Misses (first 20)

| run | id | category | question | model_answer | answer_regex |
|---|---|---|---|---|---|
| /home/iwatsuka/dev/logicbench_env/logicbench-eval/runs/20251014_112434 | q19 | lang | 英語で「ありがとう」を答えてください（短く）。 | Thank you. | ^(thank\s*you|thanks)$ |
| /home/iwatsuka/dev/logicbench_env/logicbench-eval/runs/20251014_112434 | q7 | knowledge | 2024年はうるう年ですか？はい/いいえのみ。 | はい。 | ^(はい|yes)$ |
| /home/iwatsuka/dev/logicbench_env/logicbench-eval/runs/20251014_112434 | q18 | devops | Dockerで実行中コンテナ一覧コマンドは？コマンドのみ。 | `docker ps` | ^docker\s+ps$ |
| /home/iwatsuka/dev/logicbench_env/logicbench-eval/runs/20251014_112434 | q11 | logic | 57は奇数ですか？はい/いいえのみ。 | はい。 | ^(はい|yes)$ |
| /home/iwatsuka/dev/logicbench_env/logicbench-eval/runs/20251014_113425 | q18 | devops | Dockerで実行中コンテナ一覧コマンドは？コマンドのみ。 | `docker ps` | ^docker\s+ps$ |
| /home/iwatsuka/dev/logicbench_env/logicbench-eval/runs/20251014_113425 | q11 | logic | 57は奇数ですか？はい/いいえのみ。 | はい。 | ^(はい|yes)$ |
| /home/iwatsuka/dev/logicbench_env/logicbench-eval/runs/20251014_113425 | q17 | devops | Gitで最新コミットの短縮ハッシュを表示するコマンドは？コマンドのみ。 | `git rev-parse --short HEAD` | ^git\s+rev-parse\s+--short\s+HEAD$ |
| /home/iwatsuka/dev/logicbench_env/logicbench-eval/runs/20251014_113425 | q19 | lang | 英語で「ありがとう」を答えてください（短く）。 | Thank you. | ^(thank\s*you|thanks)$ |
| /home/iwatsuka/dev/logicbench_env/logicbench-eval/runs/20251014_113425 | q7 | knowledge | 2024年はうるう年ですか？はい/いいえのみ。 | はい。 | ^(はい|yes)$ |
| /home/iwatsuka/evalbench/runs/20251014_112434 | q19 | lang | 英語で「ありがとう」を答えてください（短く）。 | Thank you. | ^(thank\s*you|thanks)$ |
| /home/iwatsuka/evalbench/runs/20251014_112434 | q7 | knowledge | 2024年はうるう年ですか？はい/いいえのみ。 | はい。 | ^(はい|yes)$ |
| /home/iwatsuka/evalbench/runs/20251014_112434 | q18 | devops | Dockerで実行中コンテナ一覧コマンドは？コマンドのみ。 | `docker ps` | ^docker\s+ps$ |
| /home/iwatsuka/evalbench/runs/20251014_112434 | q11 | logic | 57は奇数ですか？はい/いいえのみ。 | はい。 | ^(はい|yes)$ |
| /home/iwatsuka/evalbench/runs/20251014_113425 | q18 | devops | Dockerで実行中コンテナ一覧コマンドは？コマンドのみ。 | `docker ps` | ^docker\s+ps$ |
| /home/iwatsuka/evalbench/runs/20251014_113425 | q11 | logic | 57は奇数ですか？はい/いいえのみ。 | はい。 | ^(はい|yes)$ |
| /home/iwatsuka/evalbench/runs/20251014_113425 | q17 | devops | Gitで最新コミットの短縮ハッシュを表示するコマンドは？コマンドのみ。 | `git rev-parse --short HEAD` | ^git\s+rev-parse\s+--short\s+HEAD$ |
| /home/iwatsuka/evalbench/runs/20251014_113425 | q19 | lang | 英語で「ありがとう」を答えてください（短く）。 | Thank you. | ^(thank\s*you|thanks)$ |
| /home/iwatsuka/evalbench/runs/20251014_113425 | q7 | knowledge | 2024年はうるう年ですか？はい/いいえのみ。 | はい。 | ^(はい|yes)$ |

## Artifacts
- Combined TSV: `reports/20251014_135654/all_results.tsv`
- Combined CSV: `reports/20251014_135654/all_results.csv`
- Per-category TSV: `reports/20251014_135654/per_category.tsv`
- Misses TSV: `reports/20251014_135654/misses.tsv`
