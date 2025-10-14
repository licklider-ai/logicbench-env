#!/usr/bin/env bash
set -Eeuo pipefail

# 使い方:
#   PRICE_IN=0.150 PRICE_OUT=0.600 ./merge_and_report.sh              # runs/* を全部マージ
#   ./merge_and_report.sh runs/20251014_112434 runs/2025...           # 指定ランだけ

TARGETS=("$@")
if [ ${#TARGETS[@]} -eq 0 ]; then
  mapfile -t TARGETS < <(find runs -maxdepth 1 -type d -name "20*" -o -name "202*" | sort)
fi
[ ${#TARGETS[@]} -gt 0 ] || { echo "No runs/* found"; exit 1; }

STAMP="$(date +'%Y%m%d_%H%M%S')"
OUTDIR="reports/$STAMP"
mkdir -p "$OUTDIR"

COMBINED_TSV="$OUTDIR/all_results.tsv"
COMBINED_CSV="$OUTDIR/all_results.csv"
REPORT_MD="$OUTDIR/report.md"

# 1) マージ（run列を付与、ヘッダは一つだけ）
echo -e "run\tid\tcategory\tquestion\tanswer_regex\tmodel\tanswer\tprompt_tokens\tcompletion_tokens\tcorrect" > "$COMBINED_TSV"
for d in "${TARGETS[@]}"; do
  f="$d/results.tsv"
  [ -f "$f" ] || { echo "[WARN] skip (missing): $f" >&2; continue; }
  awk -F'\t' -v run="$d" 'NR>1{print run "\t" $0}' "$f" >> "$COMBINED_TSV"
done

# 2) 集計
TOTAL_Q=$(awk -F'\t' 'NR>1{n++}END{print n+0}' "$COMBINED_TSV")
TOTAL_CORRECT=$(awk -F'\t' 'NR>1{c+=$10}END{print c+0}' "$COMBINED_TSV")
ACC=$(awk -v n="$TOTAL_Q" -v c="$TOTAL_CORRECT" 'BEGIN{printf "%.2f", (n?c/n*100:0)}')

PROMPT_TOK=$(awk -F'\t' 'NR>1{s+=$8}END{print s+0}' "$COMBINED_TSV")
COMP_TOK=$(awk -F'\t' 'NR>1{s+=$9}END{print s+0}' "$COMBINED_TSV")

# 3) 料金（環境変数の単価を使用）
PRICE_IN="${PRICE_IN:-0}"; PRICE_OUT="${PRICE_OUT:-0}"
COST_IN="N/A"; COST_OUT="N/A"; COST_TOTAL="N/A"
if awk 'BEGIN{exit !(ENVIRON["PRICE_IN"]+0>0 && ENVIRON["PRICE_OUT"]+0>0)}'; then
  COST_IN=$(awk -v t="$PROMPT_TOK" -v p="$PRICE_IN" 'BEGIN{printf "%.6f", t/1000*p}')
  COST_OUT=$(awk -v t="$COMP_TOK" -v p="$PRICE_OUT" 'BEGIN{printf "%.6f", t/1000*p}')
  COST_TOTAL=$(awk -v a="$COST_IN" -v b="$COST_OUT" 'BEGIN{printf "%.6f", a+b}')
fi

# 4) カテゴリ別
CAT_TSV="$OUTDIR/per_category.tsv"
awk -F'\t' '
  NR==1{next}
  {cnt[$3]++; cor[$3]+=$10}
  END{
    print "category\tsamples\tcorrect\tacc(%)"
    for (k in cnt) {
      acc = (cor[k]/cnt[k]*100)
      printf "%s\t%d\t%d\t%.2f\n", k, cnt[k], cor[k], acc
    }
  }' "$COMBINED_TSV" | sort -k4,4nr -k2,2nr > "$CAT_TSV"

# 5) Misses 抜粋（先頭20件）
MISSES_TSV="$OUTDIR/misses.tsv"
{
  echo -e "run\tid\tcategory\tquestion\tmodel_answer\tanswer_regex"
  awk -F'\t' 'NR>1 && $10==0 {print $1"\t"$2"\t"$3"\t"$4"\t"$7"\t"$5}' "$COMBINED_TSV" | head -n 20
} > "$MISSES_TSV"

# 6) CSV も作成（表計算用）
awk -F'\t' -v OFS=',' 'NR==1{print; next}{for(i=1;i<=NF;i++){gsub(/"/,"\"\"",$i); $i="\"" $i "\""}; print}' "$COMBINED_TSV" > "$COMBINED_CSV"

# 7) Markdown レポート
{
  echo "# Eval Report ($STAMP)"
  echo
  echo "## Overview"
  echo "- Runs merged: ${#TARGETS[@]}"
  echo "- Total samples: $TOTAL_Q"
  echo "- Overall accuracy: **${ACC}%**"
  echo
  echo "## Tokens & Cost"
  echo "- Prompt tokens: $PROMPT_TOK"
  echo "- Completion tokens: $COMP_TOK"
  echo "- Unit price (/1K): in=\$${PRICE_IN}, out=\$${PRICE_OUT}"
  echo "- Est. cost: in=\$${COST_IN}, out=\$${COST_OUT}, total=\$${COST_TOTAL}"
  echo
  echo "## Per-category accuracy"
  echo
  echo "| category | samples | correct | acc(%) |"
  echo "|---|---:|---:|---:|"
  awk -F'\t' 'NR>1{printf "| %s | %d | %d | %.2f |\n",$1,$2,$3,$4}' "$CAT_TSV"
  echo
  echo "## Misses (first 20)"
  echo
  echo "| run | id | category | question | model_answer | answer_regex |"
  echo "|---|---|---|---|---|---|"
  awk -F'\t' 'NR>1{printf "| %s | %s | %s | %s | %s | %s |\n",$1,$2,$3,$4,$5,$6}' "$MISSES_TSV"
  echo
  echo "## Artifacts"
  echo "- Combined TSV: \`$COMBINED_TSV\`"
  echo "- Combined CSV: \`$COMBINED_CSV\`"
  echo "- Per-category TSV: \`$CAT_TSV\`"
  echo "- Misses TSV: \`$MISSES_TSV\`"
} > "$REPORT_MD"

echo "[OK] Report generated at: $REPORT_MD"
