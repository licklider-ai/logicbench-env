#!/usr/bin/env bash
set -euo pipefail

IN="${1:?usage: eval_runner.sh <in.jsonl> [OUT]}"
RUN_ID="${RUN_ID:-$(date +%Y%m%d_%H%M%S)}"
mkdir -p runs reports logs tmp

# OUT の決定（第2引数があれば尊重、なければ従来の名前に合わせる）
if [[ $# -ge 2 ]]; then
  OUT="$2"
else
  base="$(basename "$IN")"
  OUT="runs/pred_${RUN_ID}_${base}"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] [start-min] $IN -> $OUT"

# 最小ランナーは第2引数(OUT)に **直接** 書く
python3 scripts/eval_runner.py "$IN" "$OUT"

# 空ファイルガード
if [[ ! -s "$OUT" ]]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] [error] OUT is missing or empty -> $OUT"
  exit 1
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] [done-min] wrote $OUT (size=$(wc -l < "$OUT") lines)"
exit 0
