import json, re, sys, pathlib

def extract_token(s: str):
    if not s: return None
    s = str(s).strip()
    m = re.search(r'(?i)\b(?:final\s+answer|answer)\s*[:：]\s*([A-Z]|YES|NO|TRUE|FALSE|-?\d+)\b', s)
    if m:
        tok = m.group(1).upper()
    else:
        last = s.splitlines()[-1].strip()
        for pat in [r'^([A-Z])\.?$', r'\b(YES|NO|TRUE|FALSE)\b', r'(-?\d+)\b']:
            m = re.search(pat, last, re.I)
            if m:
                tok = m.group(1).upper()
                break
        else:
            tok = None
    if tok in ('TRUE','T'): tok='YES'
    if tok in ('FALSE','F'): tok='NO'
    return tok

def expected_type(lbl):
    if lbl is None: return "any"
    s = str(lbl).strip().upper()
    if re.fullmatch(r'[A-D]', s): return "letters"
    if s in ("YES","NO","TRUE","FALSE"): return "yn"
    if re.fullmatch(r'-?\d+', s): return "int"
    return "any"

def num_to_letter(n: int):
    return chr(ord('A') + n - 1) if 1 <= n <= 26 else None

def canonicalize(pred_obj, exp_type):
    for k in ["label","answer","pred","final","output","text","response"]:
        v = pred_obj.get(k)
        if v is None: continue
        tok = extract_token(v) if isinstance(v, str) else (str(v).upper() if v is not None else None)
        if not tok: continue
        if exp_type == "letters":
            if re.fullmatch(r'[A-D]', tok): return tok
            if re.fullmatch(r'-?\d+', tok):
                t = num_to_letter(int(tok))
                if t in ("A","B","C","D"): return t
            m = re.match(r'([A-D])', tok)
            if m: return m.group(1)
            return None
        elif exp_type == "yn":
            return tok if tok in ("YES","NO") else None
        elif exp_type == "int":
            return str(int(tok)) if re.fullmatch(r'-?\d+', tok) else None
        else:
            return tok
    return None

def load_jsonl(p):
    rows=[]
    with open(p, encoding='utf-8') as f:
        for line in f:
            line=line.strip()
            if not line: continue
            try:
                rows.append(json.loads(line))
            except:
                pass
    return rows

def main():
    if len(sys.argv) != 4:
        print("usage: normalize_pred_with_options.py <pred_norm.jsonl> <gold.jsonl> <out.jsonl>")
        sys.exit(2)
    pred_p = pathlib.Path(sys.argv[1])
    gold_p = pathlib.Path(sys.argv[2])
    out_p  = pathlib.Path(sys.argv[3])

    preds = load_jsonl(pred_p)
    golds = [g for g in load_jsonl(gold_p) if isinstance(g, dict) and "id" in g and "label" in g]
    gold_by_id = {str(g["id"]): g for g in golds}

    total_in = len(preds)
    total_out = 0
    with open(out_p, "w", encoding="utf-8") as fo:
        for o in preds:
            if not isinstance(o, dict) or "id" not in o: continue
            oid = str(o["id"])
            g   = gold_by_id.get(oid)
            lbl = g.get("label") if g else None
            et  = expected_type(lbl)
            canon = canonicalize(o, et)
            newo = dict(o)
            newo["label"] = canon
            fo.write(json.dumps(newo, ensure_ascii=False) + "\n")
            total_out += 1

    spec = {}
    if any(re.fullmatch(r'[A-D]', str(g.get("label","")).strip().upper()) for g in golds):
        spec["type"] = "letters"; spec["letters"] = ["A","B","C","D"]
    print(f"[OK] options-aware normalized {total_out}/{total_in} -> {out_p} spec={spec}")

if __name__ == "__main__":
    main()
