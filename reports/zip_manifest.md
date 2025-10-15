# ZIP Manifest

- Source ZIP: logicbench_eval_pack_v3.zip
- Generated at: 2025-10-14T15:54:14+09:00
- Max bytes per file: 51200


---
# FILE: logicbench_eval_pack/requirements.txt
```

openai>=1.0.0
tiktoken>=0.11.0

```


---
# FILE: logicbench_eval_pack/scripts/eval_runner.py
```

import os, json, time, sys, re
from pathlib import Path
import tiktoken
from openai import OpenAI
from openai import RateLimitError, APIConnectionError, APITimeoutError, APIError

MODEL    = os.getenv("LB_MODEL", "gpt-4o-mini")
IN_PATH  = sys.argv[1] if len(sys.argv) > 1 else "data/dev_20.jsonl"
OUT_PATH = sys.argv[2] if len(sys.argv) > 2 else "runs/pred.jsonl"
USG_PATH = OUT_PATH.replace(".jsonl","_usage.jsonl")
SLEEP_SEC = float(os.getenv("SLEEP_SEC", "0"))  # レート制限が厳しい環境では 21 などを指定

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
enc = tiktoken.get_encoding("cl100k_base")
def tok(s): 
    try: return len(enc.encode(s or "")); 
    except: return 0

# 既存結果をスキップ（途中再開OK）
done_ids=set()
if os.path.exists(OUT_PATH):
    with open(OUT_PATH,encoding="utf-8") as f:
        for l in f:
            try: done_ids.add(json.loads(l)["id"])
            except: pass

Path("runs").mkdir(exist_ok=True)
rows=[json.loads(l) for l in open(IN_PATH,encoding="utf-8") if l.strip()]
total=len(rows)
print(f"[start] {IN_PATH} -> {OUT_PATH} (total={total}, model={MODEL}, skip={len(done_ids)})", flush=True)

with open(OUT_PATH,"a",encoding="utf-8") as f_out, open(USG_PATH,"a",encoding="utf-8") as f_usg:
    done=len(done_ids)
    for ex in rows:
        qid=ex.get("id")
        if qid in done_ids:
            continue
        prompt=ex.get("input") or ""
        while True:
            try:
                resp=client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {"role":"system","content":"Answer briefly. If multiple-choice, return only the option letter or exact answer."},
                        {"role":"user","content":prompt}
                    ],
                    timeout=120,
                )
                break
            except RateLimitError as e:
                msg=str(e); m=re.search(r"try again in (\d+)s", msg)
                wait=int(m.group(1)) if m else max(20,int(SLEEP_SEC) or 20)
                print(f"[429] waiting {wait}s ...", flush=True)
                time.sleep(wait)
            except (APIConnectionError, APITimeoutError, APIError) as e:
                print(f"[warn] API error: {type(e).__name__}: {e} -> retry in 5s", flush=True)
                time.sleep(5)

        ans=resp.choices[0].message.content.strip()
        json.dump({"id":qid,"pred":ans}, f_out, ensure_ascii=False); f_out.write("\n")
        u=getattr(resp,"usage",None)
        usage={
            "id":qid,
            "prompt_tokens_sdk":getattr(u,"prompt_tokens",None) if u else None,
            "completion_tokens_sdk":getattr(u,"completion_tokens",None) if u else None,
            "prompt_tokens_est":tok(prompt),
            "completion_tokens_est":tok(ans),
            "model":MODEL,
            "ts":int(time.time()),
        }
        json.dump(usage, f_usg, ensure_ascii=False); f_usg.write("\n")

        done+=1
        if SLEEP_SEC>0:
            print(f"[{done}/{total}] {qid} ✓  sleeping {int(SLEEP_SEC)}s", flush=True)
            time.sleep(SLEEP_SEC)
        else:
            print(f"[{done}/{total}] {qid} ✓", flush=True)

print(f"[done] outputs: {OUT_PATH}\n[done] usage:   {USG_PATH}")

```


---
# FILE: logicbench_eval_pack/scripts/score_and_cost.py
```

import json, sys, os, re
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

GOLD_PATH = os.getenv("LB_GOLD", "data/gold_20.jsonl")
PRED_PATH = sys.argv[1] if len(sys.argv) > 1 else "runs/pred.jsonl"
USG_PATH  = PRED_PATH.replace(".jsonl","_usage.jsonl")

PIN  = Decimal(os.getenv("PRICE_IN",  "0"))
POUT = Decimal(os.getenv("PRICE_OUT", "0"))
def d(x): return Decimal(str(x))

YES = {"yes","y","true","t","1"}
NO  = {"no","n","false","f","0"}

def normalize(s: str):
    if s is None: return ""
    s = str(s).strip()
    # "Answer:" / "Prediction:" などの接頭辞を除去
    s = re.sub(r"^(answer|prediction)\s*[:\-]\s*", "", s, flags=re.I).strip()
    # 先頭行だけ使う & 末尾の句読点を除去
    s = s.splitlines()[0].strip().rstrip(".。")
    # (A) / A) / A. / A: など -> "A"
    m = re.match(r"^\(?([A-D])\)?[)\.\:]?\s*$", s, flags=re.I)
    if m: return m.group(1).upper()
    # Yes/No 類の正規化
    low = s.lower()
    if low in YES: return "Yes"
    if low in NO:  return "No"
    if re.search(r"\byes\b", low): return "Yes"
    if re.search(r"\bno\b",  low): return "No"
    if re.search(r"\btrue\b", low):  return "Yes"
    if re.search(r"\bfalse\b", low): return "No"
    return s

# gold 読み込み
gold, cat_map = {}, {}
with open(GOLD_PATH, "r", encoding="utf-8") as f:
    for line in f:
        ex = json.loads(line)
        gid = ex.get("id")
        gold[gid] = normalize(ex.get("answer"))
        cat_map[gid] = ex.get("category") or "other"

# 採点
total = correct = 0
per_cat_total = defaultdict(int)
per_cat_correct = defaultdict(int)
missing = 0

with open(PRED_PATH,"r", encoding="utf-8") as f:
    for line in f:
        ex = json.loads(line)
        pid = ex.get("id")
        if pid not in gold:
            missing += 1
            continue
        pred = normalize(ex.get("pred"))
        g = gold[pid]
        total += 1
        ok = (pred == g)
        if ok: correct += 1
        c = cat_map.get(pid, "other")
        per_cat_total[c] += 1
        per_cat_correct[c] += 1 if ok else 0

acc = (correct/total if total else 0.0)

# 料金試算
pt=ct=0
if os.path.exists(USG_PATH):
    with open(USG_PATH,"r", encoding="utf-8") as f:
        for line in f:
            u = json.loads(line)
            pt += u.get("prompt_tokens_sdk") or u.get("prompt_tokens_est") or 0
            ct += u.get("completion_tokens_sdk") or u.get("completion_tokens_est") or 0

cost_in  = (d(pt)/d(1000)) * PIN
cost_out = (d(ct)/d(1000)) * POUT
cost_sum = (cost_in + cost_out).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

# 表示
print("=== Overall Accuracy ===")
print(f"Total: {total}  Correct: {correct}  Acc: {acc*100:.2f}%")
if missing:
    print(f"(note) {missing} predictions had unknown IDs and were ignored.")

print("\n=== Accuracy by Category ===")
for c in sorted(per_cat_total.keys()):
    t = per_cat_total[c]; k = per_cat_correct[c]
    a = (k/t*100) if t else 0
    print(f"{c:40s}  {k:3d}/{t:3d}  ({a:5.1f}%)")

print("\n=== Token Usage & Cost ===")
print(f"Prompt tokens:    {pt}")
print(f"Completion tokens:{ct}")
print(f"Price (per 1K):   in=${PIN}  out=${POUT}")
print(f"Estimated cost:   ${cost_sum}")

```


---
# FILE: logicbench_eval_pack/README_RUN.md
```

# LogicBench 20問・比較評価パック

このパックは **同一条件**で他AIモデルを評価するための最小一式です。

## 構成
- `data/dev_20.jsonl` … 入力（20問、各行 `{id, input}`)
- `data/gold_20.jsonl` … 正解とカテゴリ（各行 `{id, answer, category}`)
- `scripts/eval_runner.py` … モデル呼び出し → 予測JSONL生成（OpenAI互換）
- `scripts/score_and_cost.py` … 採点（カテゴリ別）＋料金試算

## 準備
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install openai tiktoken
export OPENAI_API_KEY="YOUR_KEY"            # OpenAI互換APIなら必須
export LB_MODEL="gpt-4o-mini"               # モデル名（任意で変更）
export PRICE_IN=0.005                       # 入力トークンの単価(USD/1K)
export PRICE_OUT=0.015                      # 出力トークンの単価(USD/1K)
# レート制限が厳しい場合のみ（例：RPM=3なら21秒）
export SLEEP_SEC=21

```
