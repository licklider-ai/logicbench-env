#!/usr/bin/env bash
set -euxo pipefail

# --- 前提チェック ---
test -s .venv/bin/activate
test -s data/gold_20.jsonl
test -s runs/pred_normalized.jsonl
python3 -V >/dev/null

# 仮想環境を有効化
. .venv/bin/activate

echo "=== Step 1: robust抽出 ==="
python3 - <<'PY'
import json, pathlib
from scripts.extract_utils import extract_letter_strict

src = pathlib.Path("runs/pred_normalized.jsonl")
dst = pathlib.Path("runs/pred_fixed.jsonl")

def pick_first(o):
    for k in ("pred","prediction","answer","output","text","response","label","choice","y","final"):
        if k in o and o[k] is not None:
            return str(o[k])
    return ""

with src.open() as fin, dst.open("w") as fout:
    for line in fin:
        if not line.strip():
            continue
        o = json.loads(line)
        o["pred"] = extract_letter_strict(pick_first(o))
        fout.write(json.dumps(o, ensure_ascii=False) + "\n")
print("WROTE:", dst)
PY

echo "=== Step 2: gold/pred 突合 & CSV生成 ==="
python3 - <<'PY'
import json, pathlib, csv, sys

gold = [json.loads(l) for l in pathlib.Path("data/gold_20.jsonl").open() if l.strip()]
pred = [json.loads(l) for l in pathlib.Path("runs/pred_fixed.jsonl").open() if l.strip()]

# joinキー検出（全件ユニーク）
ignore = {"gold","label","answer","options","opts","choices","question","prompt","context","category","cat"}
keys = set().union(*map(set, gold))
cands = []
for k in keys - ignore:
    vals = [g.get(k) for g in gold]
    if any(v is None for v in vals):
        continue
    if len(set(map(str, vals))) == len(vals):
        cands.append(k)
prio = ["id","name","sample_id","question_id","qid","uid","problem_id","sample","task_id","example_id"]
jk = sorted(cands, key=lambda k: (prio.index(k) if k in prio else 999, k))[0]

# gold ラベルキー検出
lk = None
for k in ("gold","label","answer"):
    if k in gold[0]:
        lk = k
        break
if lk is None:
    for k in gold[0]:
        vs = [str(r.get(k)).strip() for r in gold]
        if all(v in {"A","B","C","D"} for v in vs):
            lk = k
            break
if lk is None:
    sys.exit("ERR: gold label key not found")

# pred マップ（id候補を総当たり）
id_keys = [jk,"id","name","sample_id","question_id","qid","uid","problem_id","sample","task_id","example_id"]
def pid(d):
    for k in id_keys:
        if k in d and d[k] is not None:
            return str(d[k])
    return None

def pval(d):
    for k in ("pred","prediction","answer","output","text","response","label","choice","y","final"):
        if k in d and d[k] is not None:
            return str(d[k]).strip().upper()
    return "NONE"

pmap = {}
for pr in pred:
    i = pid(pr)
    if i is None:
        continue
    pmap[i] = pval(pr)

# CSV 出力（make_report_simple.py 互換：cost_usd 列名）
out = pathlib.Path("reports/summary_latest_override.csv")
out.parent.mkdir(parents=True, exist_ok=True)
with out.open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["id","category","gold","pred","correct","cost_usd"])
    for g in gold:
        gid = str(g[jk])
        gold_lab = str(g[lk]).strip().upper()
        pred_lab = pmap.get(gid, "NONE")
        w.writerow([gid, g.get("category","unknown"), gold_lab, pred_lab, int(pred_lab == gold_lab), "0.000000"])
print("WROTE:", out)
PY

echo "=== Step 3: レポート生成 ==="
python3 scripts/make_report_simple.py \
  reports/summary_latest_override.csv \
  reports/logicbench_test_report_latest_override.md

echo "=== Step 4: 結果確認 ==="
tail -n 5 reports/summary_latest_override.csv || true
tail -n 20 reports/logicbench_test_report_latest_override.md || true

echo "=== 完了: override pipeline 実行成功 ==="
