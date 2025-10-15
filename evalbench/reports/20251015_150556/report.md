# Eval Report (20251015_150556)

## Overview
- Total samples: 20
- Overall accuracy: **90.00%** (18/20)

## Tokens & Cost
- Prompt tokens: N/A
- Completion tokens: N/A
- Unit price (/1K): N/A
- Est. cost: N/A

## Per-category accuracy

| category | samples | correct | acc(%) |
|---|---:|---:|---:|
| math | 20 | 18 | 90.00 |

## Misses (first 20)

| run | id | category | question | model_answer | answer_regex |
|---|---|---|---|---|---|
| logicbench-eval/runs/20251015_150556 | rebuild:016 | math | What is 7 + 5? Choices: A. 13 B. 15 C. 11 D. 12 Answer: | A | ^(?:D\.?\|D\.\s*12\|12)$ |
| logicbench-eval/runs/20251015_150556 | rebuild:019 | math | What is 3 + 8? Choices: A. 13 B. 12 C. 14 D. 11 Answer: | A | ^(?:D\.?\|D\.\s*11\|11)$ |

## Artifacts
- Combined TSV: `reports/20251015_150556/all_results.tsv`
- Per-category TSV: `reports/20251015_150556/per_category.tsv`
- Misses TSV: `reports/20251015_150556/misses.tsv`
