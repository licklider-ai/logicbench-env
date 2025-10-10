import json, re, unicodedata
from pathlib import Path
from collections import Counter

def load_jsonl(p):
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line: yield json.loads(line)

data_p = Path("data/dev_20.jsonl")
gold_p = Path("data/gold_20.jsonl")
from glob import glob
pred_p = Path(sorted(glob("runs/pred_gpt-4o-mini_*.jsonl"))[-1])

print("FILES:")
print("  DATA:", data_p.exists(), data_p)
print("  GOLD:", gold_p.exists(), gold_p)
print("  PRED:", pred_p.exists(), pred_p)

# gold のキー候補を推定
gold_rows = list(load_jsonl(gold_p))
cand = ["answer","gold","label","correct","correct_answer","target","solution","ideal"]
gkey=None
for r in gold_rows[:5]:
    for k in cand:
        if k in r: gkey=k; break
    if gkey: break
print("\nDetected gold-key:", gkey)

print("\nGOLD sample (first 3):")
for r in gold_rows[:3]:
    print({k:r.get(k) for k in ["id","qid","sample_id"]+[gkey] if k})

pred_rows = list(load_jsonl(pred_p))
print("\nPRED sample (first 3):")
for r in pred_rows[:3]:
    print(r)

# ざっくり分布
from collections import Counter
gold_vals = [r.get(gkey,"") for r in gold_rows] if gkey else []
pred_vals = [ (r.get("prediction") or r.get("answer") or "") for r in pred_rows ]
print("\nRAW distributions (not normalized):")
print("  gold:", Counter(gold_vals))
print("  pred:", Counter(pred_vals))
