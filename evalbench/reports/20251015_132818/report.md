# Eval Report (20251015_132818)

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
| unknown | 20 | 18 | 90.00 |

## Misses (first 20)
| id | category | model_answer | gold | answer_regex |
|---|---|---|---|---|
| rebuild:016 | unknown | A | D. 12 | ^(?:D\.?\|D\.\s*12\|12)$ |
| rebuild:019 | unknown | A. 13 | D. 11 | ^(?:D\.?\|D\.\s*11\|11)$ |

## Artifacts
- Combined TSV: `reports/20251015_132818/all_results.tsv`
- Per-category TSV: `reports/20251015_132818/per_category.tsv`
- Misses TSV: `reports/20251015_132818/misses.tsv`
