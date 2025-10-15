#!/usr/bin/env bash
set -Eeuo pipefail

: "${OPENAI_API_KEY:?set OPENAI_API_KEY}"
DATASET="${1:-dataset.tsv}"
N="${N:-1}"
MODEL="${MODEL:-gpt-4o-mini}"
MAX_TOKENS="${MAX_TOKENS:-64}"
SYSTEM_PROMPT="${SYSTEM_PROMPT:-You are a concise assistant. Answer only the final answer.}"

[ -f "$DATASET" ] || { echo "dataset not found: $DATASET" >&2; exit 1; }
for c in curl jq awk; do command -v "$c" >/dev/null || { echo "need: $c" >&2; exit 1; }; done

STAMP="$(date +'%Y%m%d_%H%M%S')"
OUT="runs/$STAMP"; mkdir -p "$OUT"
RES="$OUT/results.tsv"
echo -e "id\tcategory\tquestion\tanswer_regex\tprovider:model\tanswer\tprompt_tokens\tcompletion_tokens\tcorrect" > "$RES"

# サンプル抽出
if command -v shuf >/dev/null; then
  tail -n +2 "$DATASET" | shuf | head -n "$N" > "$OUT/_sample.tsv"
else
  tail -n +2 "$DATASET" | head -n "$N" > "$OUT/_sample.tsv"
fi

call_openai() {
  local question="$1" resp="$2"
  local payload http
  payload="$(jq -n --arg m "$MODEL" --arg s "$SYSTEM_PROMPT" --arg q "$question" --argjson max "$MAX_TOKENS" \
    '{model:$m,temperature:0,max_tokens:$max,messages:[{role:"system",content:$s},{role:"user",content:$q}]}')"
  for a in 1 2 3 4 5; do
    http="$(curl -sS -o "$resp" -w "%{http_code}" \
      -X POST https://api.openai.com/v1/chat/completions \
      -H "Authorization: Bearer '"$OPENAI_API_KEY"'" \
      -H "Content-Type: application/json" \
      -d "$payload")"
    case "$http" in
      200) return 0;;
      429|5*) sleep $((2**(a-1)));;
      *) echo "[ERROR] HTTP $http: $(cat "$resp")" >&2; return 1;;
    esac
  done
  echo "[ERROR] retry exceeded" >&2; return 1
}

i=0
while IFS=$'\t' read -r id cat q regex; do
  [ -n "$id" ] || continue
  i=$((i+1))
  resp="$OUT/resp_$i.json"
  call_openai "$q" "$resp" || exit 1
  ans="$(jq -r '.choices[0].message.content // ""' < "$resp")"
  p="$(jq -r '.usage.prompt_tokens // 0' < "$resp")"
  c="$(jq -r '.usage.completion_tokens // 0' < "$resp")"
  ok=0; [ -n "$regex" ] && printf '%s' "$ans" | tr -d '\r' | grep -Eiq -- "$regex" && ok=1
  printf "%s\t%s\t%s\t%s\t%s\t%s\t%d\t%d\t%d\n" \
    "$id" "$cat" "$q" "$regex" "openai:$MODEL" \
    "$(printf '%s' "$ans" | tr '\n' ' ')" "$p" "$c" "$ok" >> "$RES"
  echo "[DONE] $i/$N id=$id ok=$ok (p=$p,c=$c)"
done < "$OUT/_sample.tsv"

echo "[INFO] done: $RES"
