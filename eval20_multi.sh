#!/usr/bin/env bash
set -Eeuo pipefail

: "${DATASET_ARG:=${1:-dataset.tsv}}"
: "${N:=20}"
: "${MODEL:=gpt-4o-mini}"
: "${MAX_TOKENS:=512}"
: "${SYSTEM_PROMPT:=You are a concise assistant. Answer only the final answer.}"
: "${PRICE_IN:=0}"
: "${PRICE_OUT:=0}"
: "${OPENAI_API_KEY:?set OPENAI_API_KEY}"

for cmd in curl jq awk grep; do command -v "$cmd" >/dev/null 2>&1 || { echo "need: $cmd" >&2; exit 1; }; done
if ! command -v sha1sum >/dev/null 2>&1 && ! command -v shasum >/dev/null 2>&1; then echo "need: sha1sum or shasum" >&2; exit 1; fi

STAMP="$(date +'%Y%m%d_%H%M%S')"
OUTDIR="runs/$STAMP"
mkdir -p "$OUTDIR/cache"
RESULTS_TSV="$OUTDIR/results.tsv"
SUMMARY_TXT="$OUTDIR/summary.txt"

# dataset
if [ "$DATASET_ARG" = "-" ] || [ "$DATASET_ARG" = "/dev/stdin" ]; then
  DATASET="$OUTDIR/dataset.tsv"; cat > "$DATASET"
else
  DATASET="$DATASET_ARG"
fi
[ -f "$DATASET" ] || { echo "dataset not found: $DATASET" >&2; exit 1; }

echo -e "id\tcategory\tquestion\tanswer_regex\tprovider:model\tanswer\tprompt_tokens\tcompletion_tokens\tcorrect" > "$RESULTS_TSV"

# sample
if command -v shuf >/dev/null 2>&1; then
  tail -n +2 "$DATASET" | shuf | head -n "$N" > "$OUTDIR/_sample.tsv"
else
  tail -n +2 "$DATASET" | head -n "$N" > "$OUTDIR/_sample.tsv"
fi

hash_key() {
  if command -v sha1sum >/dev/null 2>&1; then printf '%s' "$1" | sha1sum | awk '{print $1}'
  else printf '%s' "$1" | shasum -a 1 | awk '{print $1}'; fi
}

call_openai() {
  local question="$1" resp_file="$2"
  local payload http_code
  payload="$(jq -n --arg model "$MODEL" --arg sys "$SYSTEM_PROMPT" --arg q "$question" --argjson max_tokens "$MAX_TOKENS" \
    '{model:$model,temperature:0,max_tokens:$max_tokens,messages:[{role:"system",content:$sys},{role:"user",content:$q}]}')"
  for a in 1 2 3 4 5; do
    http_code="$(curl -sS -o "$resp_file" -w "%{http_code}" \
      -X POST "https://api.openai.com/v1/chat/completions" \
      -H "Authorization: Bearer '"$OPENAI_API_KEY"'" \
      -H "Content-Type: application/json" \
      -d "$payload")"
    case "$http_code" in
      200) return 0;;
      429|5*) sleep $((2**(a-1)));;
      *) echo "[ERROR] HTTP $http_code: $(cat "$resp_file")" >&2; return 1;;
    esac
  done
  echo "[ERROR] retry exceeded" >&2; return 1
}

processed=0
while IFS=$'\t' read -r id category question answer_regex; do
  [ -n "${id:-}" ] || continue
  processed=$((processed+1))
  key="$(hash_key "openai|$MODEL|$question")"
  cache="$OUTDIR/cache/$key.json"
  if [ -f "$cache" ]; then resp="$cache"; else resp="$OUTDIR/resp_${processed}.json"; call_openai "$question" "$resp"; cp "$resp" "$cache" || true; fi

  answer="$(jq -r '.choices[0].message.content // ""' < "$resp")"
  p_tokens="$(jq -r '.usage.prompt_tokens // 0' < "$resp")"
  c_tokens="$(jq -r '.usage.completion_tokens // 0' < "$resp")"

  correct=0
  if [ -n "${answer_regex:-}" ] && printf '%s' "$answer" | tr -d '\r' | grep -Eiq -- "$answer_regex"; then correct=1; fi

  printf "%s\t%s\t%s\t%s\t%s\t%s\t%d\t%d\t%d\n" \
    "$id" "$category" "$question" "$answer_regex" "openai:$MODEL" \
    "$(printf '%s' "$answer" | tr '\n' ' ' | sed 's/\t/    /g')" \
    "$p_tokens" "$c_tokens" "$correct" >> "$RESULTS_TSV"

  echo "[DONE] $processed/$N id=$id cat=$category ok=$correct (p=$p_tokens,c=$c_tokens)"
done < "$OUTDIR/_sample.tsv"

total_p="$(awk -F'\t' 'NR>1{s+=$7}END{print s+0}' "$RESULTS_TSV")"
total_c="$(awk -F'\t' 'NR>1{s+=$8}END{print s+0}' "$RESULTS_TSV")"
acc="$(awk -F'\t' 'NR>1{n++;c+=$9}END{printf(n? "%.2f":"0.00", (c/n*100))}' "$RESULTS_TSV")"

cost_in="N/A"; cost_out="N/A"; cost_total="N/A"
if awk 'BEGIN{exit !(ENVIRON["PRICE_IN"]+0>0 && ENVIRON["PRICE_OUT"]+0>0)}'; then
  cost_in="$(awk -v t="$total_p" -v p="$PRICE_IN" 'BEGIN{printf "%.6f", t/1000*p}')"
  cost_out="$(awk -v t="$total_c" -v p="$PRICE_OUT" 'BEGIN{printf "%.6f", t/1000*p}')"
  cost_total="$(awk -v a="$cost_in" -v b="$cost_out" 'BEGIN{printf "%.6f", a+b}')"
fi

{
  echo "==== SUMMARY ($STAMP) ===="
  echo "Provider/Model : openai / $MODEL"
  echo "Samples        : $N"
  echo "Prompt tokens  : $total_p"
  echo "Output tokens  : $total_c"
  echo "Unit price (/1K): in=$PRICE_IN, out=$PRICE_OUT (USD)"
  echo "Est. cost      : in=$cost_in, out=$cost_out, total=$cost_total (USD)"
  echo
  echo "Overall accuracy (micro): ${acc}%"
  echo
  echo "Artifacts:"
  echo "- Results TSV : $RESULTS_TSV"
} | tee "$SUMMARY_TXT"

echo "[INFO] done -> $OUTDIR/"
