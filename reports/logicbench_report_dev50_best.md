# LogicBench dev50 モデル比較

| Model | Accuracy | Correct/Total | CSV |
|---|---:|---:|---|
| gpt-4o-mini | 0.880 | 44 / 50 | reports/summary_20251027_133322_gpt-4o-mini_dev50.csv |
| gpt-4.1-mini | 0.840 | 42 / 50 | reports/summary_20251027_133322_gpt-4.1-mini_dev50.csv |
| got-5 | 0.820 | 41 / 50 | reports/summary_20251027_142459_got-5_dev50.csv |
| o3-mini | 0.820 | 41 / 50 | reports/summary_20251027_134731_o3-mini_dev50.csv |
| o3 | 0.820 | 41 / 50 | reports/summary_20251027_140302_o3_dev50.csv |
| gpt-4-32k | 0.820 | 41 / 50 | reports/summary_20251027_142459_gpt-4-32k_dev50.csv |
| gpt-3.5-turbo | 0.540 | 27 / 50 | reports/summary_20251027_140302_gpt-3.5-turbo_dev50.csv |

*注: `gpt-4-32k` と `got-5` はフォールバックで実体 `gpt-4o` を使用*
