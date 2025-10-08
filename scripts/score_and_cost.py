import json, sys, os
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

GOLD_PATH = os.getenv("LB_GOLD", "data/gold.jsonl")
PRED_PATH = sys.argv[1] if len(sys.argv) > 1 else "runs/dev20_pred.jsonl"
USG_PATH  = PRED_PATH.replace(".jsonl","_usage.jsonl")

# 単価(1K tokensあたり)は環境変数で与える：未設定なら0
# 例) export PRICE_IN=0.005; export PRICE_OUT=0.015
PIN  = Decimal(os.getenv("PRICE_IN",  "0"))
POUT = Decimal(os.getenv("PRICE_OUT", "0"))

def d(x): return Decimal(str(x))

# 1) gold 読み込み
gold = {}
cat_map = {}
with open(GOLD_PATH, "r") as f:
    for line in f:
        ex = json.loads(line)
        gid = ex.get("id")
        gold[gid] = str(ex.get("answer")).strip()
        cat = ex.get("category")
        if not cat:
            # 簡易カテゴリ推定（IDに規則名が含まれる前提の例）
            sid = str(gid).lower()
            if "modus_ponens" in sid or "mp" in sid: cat = "modus_ponens"
            elif "modus_tollens" in sid or "mt" in sid: cat = "modus_tollens"
            elif "disjunctive" in sid or "or" in sid: cat = "disjunction"
            elif "syllogism" in sid: cat = "syllogism"
            else: cat = "other"
        cat_map[gid] = cat

# 2) pred 読み込み & 採点
total = 0
correct = 0
per_cat_total = defaultdict(int)
per_cat_correct = defaultdict(int)
details = []

with open(PRED_PATH,"r") as f:
    for line in f:
        ex = json.loads(line)
        pid = ex.get("id")
        pred = str(ex.get("pred")).strip()
        if pid not in gold: 
            continue
        total += 1
        g = gold[pid]
        ok = (pred == g)
        if ok: correct += 1
        c = cat_map.get(pid, "other")
        per_cat_total[c] += 1
        per_cat_correct[c] += 1 if ok else 0
        details.append({"id":pid,"pred":pred,"gold":g,"ok":ok,"category":c})

acc = (correct/total if total else 0.0)

# 3) 料金試算（usageログがあればSDK優先・なければ概算）
pt=ct=0
if os.path.exists(USG_PATH):
    with open(USG_PATH,"r") as f:
        for line in f:
            u = json.loads(line)
            pt += u.get("prompt_tokens_sdk") or u.get("prompt_tokens_est") or 0
            ct += u.get("completion_tokens_sdk") or u.get("completion_tokens_est") or 0

# 単価は 1K tokens あたり
cost_in  = (d(pt)/d(1000)) * PIN
cost_out = (d(ct)/d(1000)) * POUT
cost_sum = (cost_in + cost_out).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

# 4) 表示
print("=== Overall Accuracy ===")
print(f"Total: {total}  Correct: {correct}  Acc: {acc*100:.2f}%\n")

print("=== Accuracy by Category ===")
for c in sorted(per_cat_total.keys()):
    t = per_cat_total[c]
    k = per_cat_correct[c]
    a = (k/t*100) if t else 0
    print(f"{c:20s}  {k:3d}/{t:3d}  ({a:5.1f}%)")
print()

print("=== Token Usage & Cost ===")
print(f"Prompt tokens:    {pt}")
print(f"Completion tokens:{ct}")
print(f"Price (per 1K):   in=${PIN}  out=${POUT}")
print(f"Estimated cost:   ${cost_sum}")
