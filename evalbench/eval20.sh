#!/usr/bin/env bash
set -Eeuo pipefail

# ===== ユーザ設定（環境変数で上書き可）=========================
: "${OPENAI_API_KEY:?環境変数 OPENAI_API_KEY を設定してください}"

DATASET_ARG="${1:-dataset.tsv}"     # 第1引数: データセット（'-' なら STDIN）
N="${N:-20}"                        # 何問走らせるか（デフォルト20）
MODEL="${MODEL:-gpt-4o-mini}"       # 利用モデル（任意に変更）
MAX_TOKENS="${MAX_TOKENS:-512}"     # 出力上限
SYSTEM_PROMPT="${SYSTEM_PROMPT:-You are a concise assistant. Answer only the final answer.}"

# 単価（USD, /1K tokens）— 必ず現行価格を確認して設定してください
PRICE_IN="${PRICE_IN:-0}"           # 入力トークン単価（例: 0.150）
PRICE_OUT="${PRICE_OUT:-0}"         # 出力トークン単価（例: 0.600）
# ===============================================================

# 依存コマンド確認
for cmd in curl jq awk grep; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "依存コマンドがありません: $cmd" >&2; exit 1; }
done
if ! command -v sha1sum >/dev/null 2>&1 && ! command -v shasum >/dev/null 2>&1; then
  echo "依存コマンドがありません: sha1sum または shasum" >&2; exit 1
fi

# 実行ディレクトリ
STAMP="$(date +'%Y%m%d_%H%M%S')"
OUTDIR="runs/$STAMP"
mkdir -p "$OUTDIR/cache"

RESULTS_TSV="$OUTDIR/results.tsv"
SUMMARY_TXT="$OUTDIR/summary.txt"
MISSES_TSV="$OUTDIR/misses.tsv"

# データセットの取り込み（'-' なら STDIN を取り込んで保存）
if [ "$DATASET_ARG" = "-" ] || [ "$DATASET_ARG" = "/dev/stdin" ]; then
  DATASET="$OUTDIR/dataset.tsv"
  cat > "$DATASET"
else
  DATASET="$DATASET_ARG"
fi
[ -f "$DATASET" ] || { echo "データセットが見つかりません: $DATASET" >&2; exit 1; }

echo "[INFO] 実行開始: $STAMP"
echo "[INFO] データセット: $DATASET"
echo "[INFO] モデル: $MODEL / N=$N"
if [ "$(printf '%.3f' "$PRICE_IN")" = "0.000" ] || [ "$(printf '%.3f' "$PRICE_OUT")" = "0.000" ]; then
  echo "[WARN] 単価(PRICE_IN/PRICE_OUT)が0です。費用は『概算不能』として表示されます。"
fi

# 結果TSV ヘッダ
echo -e "id\tcategory\tquestion\tanswer_regex\tmodel\tanswer\tprompt_tokens\tcompletion_tokens\tcorrect" > "$RESULTS_TSV"

# ランダムサンプルN件（ヘッダ除外）
if command -v shuf >/dev/null 2>&1; then
  awk 'NR>1' "$DATASET" | shuf | head -n "$N" > "$OUTDIR/_sample.tsv"
else
  echo "[WARN] shuf が見つかりません。先頭から $N 件を使用します。"
  awk 'NR>1' "$DATASET" | head -n "$N" > "$OUTDIR/_sample.tsv"
fi

# API呼び出し（429/5xxは指数バックオフで再試行）
call_api() {
  local question="$1"
  local resp_file="$2"
  local payload
  payload="$(jq -n \
      --arg model "$MODEL" \
      --arg sys "$SYSTEM_PROMPT" \
      --arg q "$question" \
      --argjson max_tokens "$MAX_TOKENS" \
      '{
        model: $model,
        temperature: 0,
        max_tokens: $max_tokens,
        messages: [
          {role:"system", content:$sys},
          {role:"user",   content:$q}
        ]
      }'
  )"

  local attempt http_code
  for attempt in 1 2 3 4 5; do
    http_code="$(curl -sS ${CURL_OPTS:-} -o "$resp_file" -w "%{http_code}" \
      --resolve api.openai.com:443:172.66.0.243 \
      --resolve api.openai.com:443:172.66.0.243 \
      -X POST "https://api.openai.com/v1/chat/completions" \
      -H "Authorization: Bearer '"$OPENAI_API_KEY"'" \
      -H "Content-Type: application/json" \
      -H "OpenAI-Project: ${OPENAI_PROJECT:-}" \
      -H "OpenAI-Project: ${OPENAI_PROJECT:-}" \
      -H "OpenAI-Project: ${OPENAI_PROJECT:-}" \
      -d "$payload")"

    if [ "$http_code" = "200" ]; then
      return 0
    elif [ "$http_code" = "429" ] || [ "${http_code:0:1}" = "5" ]; then
      local backoff=$((2**(attempt-1)))
      echo "[WARN] HTTP $http_code -> 再試行 (${attempt}/5) ${backoff}s" >&2
      sleep "$backoff"
    else
      echo "[ERROR] HTTP $http_code / 応答: $(cat "$resp_file")" >&2
      return 1
    fi
  done
  echo "[ERROR] リトライ上限到達。" >&2
  return 1
}

# キャッシュ用ハッシュ関数
hash_key() {
  local s="$1"
  if command -v sha1sum >/dev/null 2>&1; then
    printf '%s' "$s" | sha1sum | awk '{print $1}'
  else
    printf '%s' "$s" | shasum -a 1 | awk '{print $1}'
  fi
}

# 1件ずつ処理
processed=0
while IFS=$'\t' read -r id category question answer_regex; do
  [ -n "${id:-}" ] || continue
  processed=$((processed+1))

  key="$(hash_key "$MODEL|$question")"
  cache_file="$OUTDIR/cache/$key.json"
  if [ -f "$cache_file" ]; then
    resp_file="$cache_file"
  else
    resp_file="$OUTDIR/resp_${processed}.json"
    call_api "$question" "$resp_file"
    cp "$resp_file" "$cache_file" || true
  fi

  # 解析
  answer="$(jq -r '.choices[0].message.content // ""' < "$resp_file")"
  p_tokens="$(jq -r '.usage.prompt_tokens // 0' < "$resp_file")"
  c_tokens="$(jq -r '.usage.completion_tokens // 0' < "$resp_file")"

  # 正誤判定（大文字小文字無視）
  correct=0
  if [ -n "${answer_regex:-}" ]; then
    if printf '%s' "$answer" | tr -d '\r' | grep -Eiq -- "$answer_regex"; then
      correct=1
    fi
  fi

  # 出力行
  printf "%s\t%s\t%s\t%s\t%s\t%s\t%d\t%d\t%d\n" \
    "$id" "$category" "$question" "$answer_regex" "$MODEL" \
    "$(printf '%s' "$answer" | tr '\n' ' ' | sed 's/\t/    /g')" \
    "$p_tokens" "$c_tokens" "$correct" >> "$RESULTS_TSV"

  echo "[DONE] $processed/$N  id=$id  cat=$category  correct=$correct  (p=$p_tokens, c=$c_tokens)"
done < "$OUTDIR/_sample.tsv"

# ===== 集計 =====
# トークン合計
total_prompt="$(awk -F'\t' 'NR>1 {s+=$7} END{print s+0}' "$RESULTS_TSV")"
total_completion="$(awk -F'\t' 'NR>1 {s+=$8} END{print s+0}' "$RESULTS_TSV")"

# 全体正答率（micro）
overall_acc="$(awk -F'\t' 'NR>1 {n++; c+=$9} END{ if(n>0){printf "%.2f", (c/n*100)} else {print "0.00"} }' "$RESULTS_TSV")"

# カテゴリ別正答率
cat_acc="$(awk -F'\t' '
  NR>1 { cnt[$2]++; cor[$2]+=$9 }
  END {
    printf "category\tsamples\tacc(%%)\n";
    for (k in cnt) {
      printf "%s\t%d\t%.2f\n", k, cnt[k], (cor[k]/cnt[k]*100)
    }
  }' "$RESULTS_TSV")"

# 不正解リスト
awk -F'\t' 'NR==1 {next} $9==0 {
  # id, category, question, answer, regex
  printf "%s\t%s\t%s\t%s\t%s\n", $1,$2,$3,$6,$4
}' "$RESULTS_TSV" > "$MISSES_TSV"

# コスト概算
cost_prompt="N/A"; cost_completion="N/A"; cost_total="N/A"
if awk 'BEGIN{exit !(ENVIRON["PRICE_IN"]+0>0 && ENVIRON["PRICE_OUT"]+0>0)}'; then
  cost_prompt="$(awk -v t="$total_prompt" -v p="$PRICE_IN" 'BEGIN{printf "%.6f", t/1000.0*p}')"
  cost_completion="$(awk -v t="$total_completion" -v p="$PRICE_OUT" 'BEGIN{printf "%.6f", t/1000.0*p}')"
  cost_total="$(awk -v a="$cost_prompt" -v b="$cost_completion" 'BEGIN{printf "%.6f", a+b}')"
fi

# サマリー出力
{
  echo "==== SUMMARY ($STAMP) ===="
  echo "Model          : $MODEL"
  echo "Samples        : $N"
  echo "Prompt tokens  : $total_prompt"
  echo "Output tokens  : $total_completion"
  echo "Unit price (/1K): in=$PRICE_IN, out=$PRICE_OUT (USD)"
  echo "Est. cost      : in=$cost_prompt, out=$cost_completion, total=$cost_total (USD)"
  echo
  echo "Overall accuracy (micro): ${overall_acc}%"
  echo
  echo "Per-category accuracy:"
  echo "$cat_acc"
  echo
  echo "Artifacts:"
  echo "- Results TSV : $RESULTS_TSV"
  echo "- Misses TSV  : $MISSES_TSV"
} | tee "$SUMMARY_TXT"

echo "[INFO] 完了。結果は $OUTDIR/ 配下に保存しました。"
