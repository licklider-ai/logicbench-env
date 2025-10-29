import json, sys, pathlib

SRC = pathlib.Path(sys.argv[1])
DST = pathlib.Path(sys.argv[2])

FEW_SHOT = """You are a careful multiple-choice solver. Pick the single best option.

### Solved Example 1 (do not copy)
Question: Which number is even?
A) 3
B) 8
C) 9
D) 11
Correct: B

### Solved Example 2 (do not copy)
Question: Some Snerbs are Torks. All Torks are Vlips. Which is true?
A) No Snerbs are Vlips
B) Some Vlips are not Snerbs
C) All Snerbs are Vlips
D) Some Snerbs are Vlips
Correct: D

### Output rule (must follow)
Return ONLY one final line in the exact format:
Answer: <A|B|C|D>
Do not include explanations or any other text.
Do not copy answers from the solved examples above.
"""

SUFFIX = (
    "\n\n---\n"
    "Now solve this new problem.\n"
    "Return ONLY one final line:\n"
    "Answer: <A|B|C|D>\n"
    "Answer: "  # forced prefill
)

def rows(p):
    for line in p.read_text(encoding="utf-8").splitlines():
        line=line.strip()
        if not line: continue
        yield json.loads(line)

out=[]
for o in rows(SRC):
    q  = (o.get("question") or "").strip()
    ch = (o.get("choices") or o.get("options") or [])
    choices_block = "\n".join(f"{'ABCD'[i]}) {t}" for i,t in enumerate(ch))
    inp = f"{FEW_SHOT}\n\nQuestion: {q}\n{choices_block}{SUFFIX}"
    out.append({**o, "input": inp})

with open(DST, "w", encoding="utf-8") as f:
    for o in out:
        f.write(json.dumps(o, ensure_ascii=False) + "\n")

print(f"[OK] materialized input -> {DST} (rows={len(out)})")
