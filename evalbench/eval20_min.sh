#!/usr/bin/env bash
set -Eeuo pipefail

: "${OPENAI_API_KEY:?set OPENAI_API_KEY}"
MODEL="${MODEL:-gpt-4o-mini}"
N="${N:-20}"
MAX_TOKENS="${MAX_TOKENS:-512}"
SYSTEM_PROMPT="${SYSTEM_PROMPT:-You are a concise assistant. Answer only the final answer.}"
PRICE_IN="${PRICE_IN:-0}"; PRICE_OUT="${PRICE_OUT:-0}"

# ネットワーク安定化（生 curl と同条件）
CURL_BASE=(curl --http1.1 -4 --connect-timeout 10 --max-time 60 -sS)
# 固定IPを使いたい場合は環境変数で: export CURL_IP=172.66.0.243
[ -n "${CURL_IP:-}" ] && CURL_BASE+=(--resolve "api.openai.com:443:${CURL_IP}")
# プロジェクトキーを使う場合（任意）
PROJ_HEADER=()
[ -n "${OPENAI_PROJECT:-}" ] && PROJ_HEADER+=(-H "OpenAI-Project: ${OPENAI_PROJECT}")

STAMP="$(date +'%Y%m%d_%H%M%S')"
OUT="runs/${STAMP}"; mkdir -p "$OUT"
RES="$OUT/results.tsv"; echo -e "id\tcategory\tquestion\tanswer_regex\tmodel\tanswer\tprompt_tokens\tcompletion_tokens\tcorrect" > "$RES"

# データセット取得（'-' ならSTDIN）
DATASET_ARG="${1:-dataset.tsv}"
if [ "$DATASET_ARG" = "-" ] || [ "$DATASET_ARG" = "/dev/stdin" ]; then
  DATASET="$OUT/dataset.tsv"; cat > "$DATASET"
else
  DATASET="$DATASET_ARG"
fi

# サンプル抽出
if command -v shuf >/dev/null 2>&1; then
  awk 'NR>1' "$DATASET" | shuf | head -n "$N" > "$OUT/_sample.tsv"
else
  awk 'NR>1' "$DATASET" | head -n "$N" > "$OUT/_sample.tsv"
fi

i=0
while IFS=$'\t' read -r id cat q regex; do
  i=$((i+1))
  payload="$(jq -n --arg m "$MODEL" --arg s "$SYSTEM_PROMPT" --arg q "$q" --argjson mt "$MAX_TOKENS" \
    '{model:$m,temperature:0,max_tokens:$mt,messages:[{role:"system",content:$s},{role:"user",content:$q}]}')"
  resp="$OUT/resp_${i}.json"

  # 429/5xx リトライ
  for a in 1 2 3 4 5; do
    code="$("${CURL_BASE[@]}" -o "$resp" -w "%{http_code}" \
      -X POST "https://api.openai.com/v1/chat/completions" \
      -H "Authorization: Bearer ${OPENAI_API_KEY}" \
      -H "Content-Type: application/json" \
      "${PROJ_HEADER[@]}" \
      -d "$payload")"
    [ "$code" = "200" ] && break
    if [ "$code" = "429" ] || [ "${code:0:1}" = "5" ]; then sleep $((2**(a-1))); else echo "[ERROR] $code"; break; fi
  done

  ans="$(jq -r '.choices[0].message.content // ""' < "$resp" 2>/dev/null || echo "")"
  pt="$(jq -r '.usage.prompt_tokens // 0' < "$resp" 2>/dev/null || echo 0)"
  ct="$(jq -r '.usage.completion_tokens // 0' < "$resp" 2>/dev/null || echo 0)"
  ok=0; [ -n "${regex:-}" ] && printf '%s' "$ans" | tr -d '\r' | grep -Eiq -- "$regex" && ok=1
  printf "%s\t%s\t%s\t%s\t%s\t%s\t%d\t%d\t%d\n" \
    "$id" "$cat" "$q" "$regex" "$MODEL" \
    "$(printf '%s' "$ans" | tr '\n' ' ' | sed 's/\t/    /g')" \
    "$pt" "$ct" "$ok" >> "$RES"
  echo "[DONE] $i/$N id=$id ok=$ok (p=$pt,c=$ct)"
done < "$OUT/_sample.tsv"

# 集計
PROMPT_TOK=$(awk -F'\t' 'NR>1{s+=$7}END{print s+0}' "$RES")
COMP_TOK=$(awk -F'\t' 'NR>1{s+=$8}END{print s+0}' "$RES")
ACC=$(awk -F'\t' 'NR>1{n++;c+=$9}END{printf "%.2f", (n?c/n*100:0)}' "$RES")
CAT=$(awk -F'\t' 'NR>1{cnt[$2]++;cor[$2]+=$9}END{print "category\tsamples\tacc(%)";for(k in cnt)printf "%s\t%d\t%.2f\n",k,cnt[k],(cor[k]/cnt[k]*100)}' "$RES")
MIS="$OUT/misses.tsv"; awk -F'\t' 'NR==1{next}$9==0{printf "%s\t%s\t%s\t%s\t%s\n",$1,$2,$3,$6,$4}' "$RES" > "$MIS"

COST_IN="N/A"; COST_OUT="N/A"; COST="N/A"
if awk 'BEGIN{exit !(ENVIRON["PRICE_IN"]+0>0 && ENVIRON["PRICE_OUT"]+0>0)}'; then
  COST_IN=$(awk -v t="$PROMPT_TOK" -v p="$PRICE_IN" 'BEGIN{printf "%.6f", t/1000*p}')
  COST_OUT=$(awk -v t="$COMP_TOK" -v p="$PRICE_OUT" 'BEGIN{printf "%.6f", t/1000*p}')
  COST=$(awk -v a="$COST_IN" -v b="$COST_OUT" 'BEGIN{printf "%.6f", a+b}')
fi

{
  echo "==== SUMMARY ($STAMP) ===="
  echo "Model          : $MODEL"
  echo "Samples        : $N"
  echo "Prompt tokens  : $PROMPT_TOK"
  echo "Output tokens  : $COMP_TOK"
  echo "Unit price (/1K): in=$PRICE_IN, out=$PRICE_OUT (USD)"
  echo "Est. cost      : in=$COST_IN, out=$COST_OUT, total=$COST (USD)"
  echo
  echo "Overall accuracy (micro): ${ACC}%"
  echo
  echo "Per-category accuracy:"
  echo "$CAT"
  echo
  echo "Artifacts:"
  echo "- Results TSV : $RES"
  echo "- Misses TSV  : $MIS"
} | tee "$OUT/summary.txt"
