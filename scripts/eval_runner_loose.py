#!/usr/bin/env python3
import os, sys, json, re
from pathlib import Path

# ===== Settings =====
MODEL = os.getenv("LB_MODEL", "gpt-4o-mini")
SYSTEM_PROMPT = (
    "You are a careful solver. Consider all four options equally likely a priori. "
    "Read the question and options carefully and answer with EXACTLY ONE letter among {A,B,C,D}. "
    "If unsure, guess uniformly among A,B,C,D. Output ONLY the letter, no punctuation or words."
)

FEW_SHOT = [
    {"role":"user","content":"Question: Is 2+2 equal to 4?\\nRespond with exactly ONE letter from {A,B,C,D}. For yes/no tasks, use A=YES/TRUE, B=NO/FALSE. Do not output anything else."},
    {"role":"assistant","content":"A"},
    {"role":"user","content":"Question: Is the sky green during a normal day?\\nRespond with exactly ONE letter from {A,B,C,D}. For yes/no tasks, use A=YES/TRUE, B=NO/FALSE. Do not output anything else."},
    {"role":"assistant","content":"B"},
]

LETTER_SET = set("ABCD")
RX_ANSWER  = re.compile(r'ANSWER\s*[:\-]?\s*([ABCD])\b', re.I)
RX_SINGLE  = re.compile(r'\b([ABCD])\b', re.I)
RX_OPT     = re.compile(r'(?:choice|option)\s*([ABCD])\b', re.I)

# ===== Helpers =====
def normalize_to_one_letter(s: str) -> str:
    if not s:
        return ""
    t = s.strip()
    if t.upper() in {"NONE","N/A",""}:
        return ""
    m = RX_ANSWER.search(t)
    if m:
        return m.group(1).upper()
    if re.search(r'\b(YES|TRUE|Y)\b', t, re.I):
        return "A"
    if re.search(r'\b(NO|FALSE|N)\b', t, re.I):
        return "B"
    m = re.search(r'^\s*([TF])\s*$', t, re.I)
    if m:
        return "A" if m.group(1).upper()=="T" else "B"
    m = RX_SINGLE.search(t)
    if m:
        return m.group(1).upper()
    m = RX_OPT.search(t)
    if m:
        return m.group(1).upper()
    return ""

def build_prompt(row: dict) -> str:
    q = row.get("question") or row.get("q") or row.get("prompt") or row.get("input") or row.get("text") or ""
    option_fields = ["options","choices","answers","candidates","cand","opts","alternatives"]
    opts = None
    for k in option_fields:
        v = row.get(k)
        if v:
            opts = v
            break
    labels = ["A","B","C","D"]
    if opts is None:
        if all((L in row) for L in labels):
            opts = [row.get(L,"") for L in labels]
    if isinstance(opts, dict):
        if any(k in opts for k in labels):
            opts = [opts.get(L,"") for L in labels if L in opts]
        elif all(k in opts for k in ("0","1","2","3")):
            opts = [opts[k] for k in ("0","1","2","3")]
        elif all(k in opts for k in ("1","2","3","4")):
            opts = [opts[k] for k in ("1","2","3","4")]
        else:
            opts = list(opts.values())[:4]

    lines = [str(q).rstrip(), ""]
    if isinstance(opts, list) and opts:
        for i, opt in enumerate(opts[:4]):
            lines.append(f"{labels[i]}. {opt}")
        lines.append("")
    elif isinstance(opts, str) and opts.strip():
        lines.append(opts.strip())
        lines.append("")

    lines.append(
        "Respond with exactly ONE letter from {A,B,C,D}. "
        "For yes/no tasks, use A=YES/TRUE, B=NO/FALSE. "
        "Do not output anything else."
    )
    return "\n".join(lines).strip()

def call_openai(prompt: str, is_logic: bool):
    # Use OpenAI if available; otherwise fallback to "A"
    try:
        from openai import OpenAI
        client = OpenAI()
        messages = [{"role":"system","content": SYSTEM_PROMPT}] + FEW_SHOT + [{"role":"user","content": prompt}]
        infer = {
            "model": MODEL,
            "messages": messages,
            "max_tokens": (8 if is_logic else 1),
            "temperature": (0.35 if is_logic else 0.0),
            "top_p": 0.0,
            "stop": ["\n"],
        }
        resp = client.chat.completions.create(**infer)
        raw = (resp.choices[0].message.content or "").strip()
        usage = getattr(resp, "usage", None)
        return raw, usage
    except Exception:
        return "A", None

# ===== Main =====
def main():
    if len(sys.argv) < 3:
        print(f"usage: {sys.argv[0]} <dev.jsonl> <out_pred.jsonl>", file=sys.stderr)
        sys.exit(2)

    in_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])
    out_path.parent.mkdir(parents=True, exist_ok=True)

    n = 0
    with in_path.open() as fin, out_path.open("w") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            q = row.get("question") or row.get("q") or row.get("prompt") or ""
            cat = str(row.get("category","")).lower()
            is_logic = ("bqa" in cat) or ("logic" in cat) or (len(q) > 180)

            prompt = build_prompt(row)
            raw, usage = call_openai(prompt, is_logic)
            pred = normalize_to_one_letter(raw)
            if pred not in LETTER_SET:
                pred = "NONE"

            usage_dict = {"prompt_tokens":0,"completion_tokens":0,"total_tokens":0}
            if usage:
                usage_dict = {
                    "prompt_tokens": getattr(usage, "prompt_tokens", 0) or 0,
                    "completion_tokens": getattr(usage, "completion_tokens", 0) or 0,
                    "total_tokens": getattr(usage, "total_tokens", 0) or 0,
                }

            out = {
                "id": row.get("id") or f"auto:{os.getpid()}_{n}",
                "raw": raw,
                "pred": pred,
                "model": MODEL,
                "prompt": prompt,
                **usage_dict,
                "cost_usd": 0.0,
            }
            fout.write(json.dumps(out, ensure_ascii=False) + "\n")
            n += 1

    print(n)

if __name__ == "__main__":
    main()
    # if q looks like serialized chat messages (JSON array), extract user content
    if isinstance(q, str) and q.strip().startswith('['):
        try:
            obj = json.loads(q)
            if isinstance(obj, list) and all(isinstance(x, dict) for x in obj):
                user_msgs = [x.get('content','') for x in obj if x.get('role')=='user']
                if user_msgs:
                    q = user_msgs[-1]
                else:
                    q = '\n'.join([x.get('content','') for x in obj if 'content' in x])
        except Exception:
            pass
