import os, json, time, sys, re
import os
SLEEP_SECS = float(os.getenv('LB_SLEEP','3'))

import re, unicodedata

VALID = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
def normalize_choice(text: str) -> str:
    if not text:
        return ""
    t = unicodedata.normalize("NFKC", text)
    m = re.search(r"[A-Za-z]", t)
    if not m:
        return ""
    c = m.group(0).upper()
    return c if c in VALID else ""
from pathlib import Path
import tiktoken
from openai import OpenAI
from openai import RateLimitError, APIConnectionError, APITimeoutError, APIError

MODEL   = os.getenv("LB_MODEL", "gpt-4o-mini")
IN_PATH = sys.argv[1] if len(sys.argv) > 1 else "data/dev_20.jsonl"
OUT_PATH= sys.argv[2] if len(sys.argv) > 2 else "runs/dev20_pred.jsonl"
USG_PATH= OUT_PATH.replace(".jsonl","_usage.jsonl")
SLEEP_SEC = float(os.getenv("SLEEP_SEC", "21"))  # RPM=3に安全側

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
enc = tiktoken.get_encoding("cl100k_base")
def tok(s): 
    try: return len(enc.encode(s or "")); 
    except: return 0

# 既存結果の読み込み（途中再開）
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

f_out=open(OUT_PATH,"a",encoding="utf-8")
f_usg=open(USG_PATH,"a",encoding="utf-8")

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
                    {"role":"system","content":"Return ONLY the final answer with no explanation. For yes/no, output exactly \"Yes\" or \"No\". For multiple-choice, output exactly one letter: A, B, C, or D."},
                    {"role":"user","content":prompt}
                ],
                timeout=120, temperature=0,
            )
            break
        except RateLimitError as e:
            msg=str(e)
            m=re.search(r"try again in (\d+)s", msg)
            wait=int(m.group(1)) if m else max(20,int(SLEEP_SEC))
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
    print(f"[{done}/{total}] {qid} ✓  sleeping {int(SLEEP_SEC)}s", flush=True)
    time.sleep(SLEEP_SEC)

f_out.close(); f_usg.close()
print(f"[done] outputs: {OUT_PATH}\n[done] usage:   {USG_PATH}")
