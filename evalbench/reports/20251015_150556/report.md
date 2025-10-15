# Eval Report (20251015_150556)

## Overview
- Total samples: 20
- Overall accuracy: **90.00%** (18/20)

## Per-category accuracy

| category | samples | correct | acc(%) |
|---|---:|---:|---:|
| math | 20 | 18 | 90.00 |

## Misses (first 20)

| id | category | model_answer | gold | answer_regex |
|---|---|---|---|---|
| rebuild:016 | math | A | D. 12 | ^(?:D\.?|D\.\s*12|12)$ |
| rebuild:019 | math | A | D. 11 | ^(?:D\.?|D\.\s*11|11)$ |

## Artifacts
- Combined TSV: `reports/20251015_150556/all_results.tsv`
- Per-category TSV: `reports/20251015_150556/per_category.tsv`
- Misses TSV: `reports/20251015_150556/misses.tsv`
