import sys, json, re, unicodedata

TOKEN_RE = re.compile(r'(YES|NO|TRUE|FALSE|[A-D]|-?\d+)', flags=re.I)

def to_token(text: str) -> str:
    s = unicodedata.normalize("NFKC", (text or "").strip())
    ms = TOKEN_RE.findall(s)
    if not ms:
        return ""
    t = ms[-1].upper()  # 最後のマッチを採用（"No explanations: C" → C）
    return {"TRUE":"YES", "FALSE":"NO"}.get(t, t)

def pick_text(o: dict) -> str:
    for k in ("answer","output","pred","prediction","final","content","text","completion"):
        v = o.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    for m in o.get("messages", []):
        if isinstance(m, dict):
            v = m.get("content")
            if isinstance(v, str) and v.strip():
                return v.strip()
    return ""

inp = sys.argv[1]
with open(inp, encoding="utf-8") as f:
    for line in f:
        o = json.loads(line)
        raw = pick_text(o)
        ans = to_token(raw)
        sys.stdout.write(json.dumps({"id": o.get("id"), "answer": ans}, ensure_ascii=False) + "\n")
