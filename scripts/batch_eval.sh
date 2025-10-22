#!/usr/bin/env bash
set -euo pipefail

# 使い方:
#   scripts/batch_eval.sh gpt-3.5-turbo gpt-4-32k o3 got-5
# ※ eval_runner.py が MODEL 環境変数を読む前提（今の実装はそうなっているはず）。
#   読まない場合は、eval_runner.py 冒頭の MODEL= を sed で差し替えるロジックを追加します。

MODELS=("$@")
[ ${#MODELS[@]} -gt 0 ] || { echo "モデル名を引数で指定してください"; exit 2; }

TS=$(date +%Y%m%d_%H%M%S)

# gold はすでに data/gold_50.for_pred.jsonl に整備済みを想定
GOLD=data/gold_50.for_pred.jsonl
if [ ! -s "$GOLD" ]; then
  echo "gold が見つからない/空です: $GOLD"; exit 3
fi

for M in "${MODELS[@]}"; do
  echo "===== MODEL: $M ====="
  export MODEL="$M"

  # 1) 50問実行（runs/pred_normalized.jsonl を上書きするので per-model に退避）
  python3 scripts/eval_runner.py

  # 2) 予測を id, label → id, output に正規化（score_and_cost_simple の仕様に合わせる）
  jq -c '{
    id,
    label: (
      (.label // .output // .prediction // .answer // .final // .raw // .choice // .y)
      | tostring | ascii_upcase
      | capture("(?<x>[A-D])") | .x
    )
  }' runs/pred_normalized.jsonl > "runs/${M}_pred_for_score.jsonl"

  jq -c '{id, output: .label}' "runs/${M}_pred_for_score.jsonl" \
    > "runs/${M}_pred_for_score_out.jsonl"

  # 3) 採点（確実版スコアラー）
  python3 - <<'PY' "$M" "$TS"
import json, csv, pathlib, sys
model = sys.argv[1]; ts=sys.argv[2]
pred_p = pathlib.Path(f"runs/{model}_pred_for_score_out.jsonl")
gold_p = pathlib.Path("data/gold_50.for_pred.jsonl")
out_csv = pathlib.Path(f"reports/summary_{ts}_{model}_dev50.csv")
pred = {j["id"]: j["output"] for j in map(json.loads, open(pred_p, encoding="utf-8"))}
gold = {j["id"]: j["label"]  for j in map(json.loads, open(gold_p, encoding="utf-8"))}
ids = sorted(set(pred) & set(gold))
rows=[]; correct=0
for k in ids:
    p=(pred[k] or "").strip().upper()[:1]
    g=(gold[k] or "").strip().upper()[:1]
    ok=int(p==g and p in "ABCD")
    correct += ok
    rows.append({"id":k,"pred":p,"gold":g,"correct":ok})
acc = correct/len(ids) if ids else 0.0
out_csv.parent.mkdir(parents=True, exist_ok=True)
with open(out_csv,"w",newline="",encoding="utf-8") as f:
    w=csv.writer(f); w.writerow(["id","pred","gold","correct"])
    for r in rows: w.writerow([r["id"],r["pred"],r["gold"],r["correct"]])
    w.writerow([]); w.writerow(["TOTAL",len(ids),"CORRECT",correct])
    w.writerow(["ACCURACY",f"{acc:.3f}"])
print(f"[{model}] pairs={len(ids)} correct={correct} acc={acc:.3f} -> {out_csv}")
PY

done

# 4) まとめサマリ（モデルごとの Accuracy を1行で俯瞰）
python3 - <<'PY' "$TS"
import csv, glob, sys, re
ts=sys.argv[1]
paths=sorted(glob.glob(f"reports/summary_{ts}_*_dev50.csv"))
print("model,accuracy,pairs,correct,csv")
for p in paths:
    acc=""; pairs=""; corr=""
    with open(p,encoding="utf-8") as f:
        rows=list(csv.reader(f))
    for i in range(len(rows)-1,-1,-1):
        if rows[i] and rows[i][0]=="ACCURACY":
            acc=rows[i][1]; break
    for i in range(len(rows)-1,-1,-1):
        if rows[i] and rows[i][0]=="TOTAL":
            pairs=rows[i][1]; corr=rows[i][3]; break
    m=re.search(r"summary_"+ts+"_(.+?)_dev50\.csv$", p)
    model=m.group(1) if m else "unknown"
    print(f"{model},{acc},{pairs},{corr},{p}")
PY
