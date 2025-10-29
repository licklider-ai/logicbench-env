import json, re, sys, pathlib

def extract_token_from_text(s: str):
    if not s: return None
    s = str(s).strip()
    # 明示 "Answer: X" を優先
    m = re.search(r'(?i)\b(?:final\s+answer|answer)\s*[:：]\s*([A-D]|YES|NO|TRUE|FALSE|-?\d+)\b', s)
    if m:
        tok = m.group(1).upper()
    else:
        last = s.splitlines()[-1].strip()
        for pat in [r'^([A-D])\.?$', r'\b(YES|NO|TRUE|FALSE)\b', r'(-?\d+)\b']:
            m = re.search(pat, last, re.I)
            if m:
                tok = m.group(1).upper()
                break
        else:
            tok = None
    if tok in ('TRUE','T'): tok='YES'
    if tok in ('FALSE','F'): tok='NO'
    return tok

def label_expected_type(gold_label):
    if gold_label is None: return "any"
    s = str(gold_label).strip().upper()
    if re.fullmatch(r'[A-D]', s): return "letters"
    if s in ('YES','NO','TRUE','FALSE'): return "yn"
    if re.fullmatch(r'-?\d+', s): return "int"
    return "any"

def to_letter_from_numeric(tok):
    # "1..4" → "A..D"
    if tok is None: return None
    if re.fullmatch(r'-?\d+', tok):
        n = int(tok)
        if 1 <= n <= 4:
            return "ABCD"[n-1]
    return None

def extract_label_from_pred_obj(o):
    # 候補フィールド優先順
    for k in ("label","answer","final","pred","output","text","response"):
        v = o.get(k)
        if isinstance(v, str) and v.strip():
            t = extract_token_from_text(v)
            if t: return t
    return None

def main():
    argv = sys.argv
    pred_p = pathlib.Path(argv[argv.index("--pred")+1])
    gold_p = pathlib.Path(argv[argv.index("--gold")+1])
    out_p  = pathlib.Path(argv[argv.index("--out")+1])

    gold_by_id = {}
    with gold_p.open(encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if not line: continue
            try:
                g=json.loads(line)
            except:
                continue
            gid = str(g.get("id")) if g.get("id") is not None else None
            if not gid: continue
            lab = g.get("label")
            if isinstance(lab, str):
                lab = lab.strip().upper()
                if lab in ("TRUE","T"):  lab="YES"
                if lab in ("FALSE","F"): lab="NO"
            gold_by_id[gid]=lab

    total_in = total_out = 0
    with pred_p.open(encoding="utf-8") as fin, out_p.open("w", encoding="utf-8") as fout:
        for line in fin:
            line=line.strip()
            if not line: continue
            total_in += 1
            try:
                o=json.loads(line)
            except:
                continue
            oid = str(o.get("id")) if o.get("id") is not None else None
            if not oid or oid not in gold_by_id:
                # GOLD にないIDはスキップ（採点対象外）
                continue

            gold_lab = gold_by_id[oid]
            exp = label_expected_type(gold_lab)

            tok = extract_label_from_pred_obj(o)

            # GOLD が letters のときは 1..4 → A..D 変換も試す
            if exp == "letters" and tok and re.fullmatch(r'-?\d+', tok):
                mapped = to_letter_from_numeric(tok)
                if mapped: tok = mapped

            # 型に従って整合性チェック（不一致なら None にして出力は残す）
            if tok:
                if   exp=="letters" and not re.fullmatch(r'[A-D]', tok): tok=None
                elif exp=="yn"      and tok not in ("YES","NO"):         tok=None
                elif exp=="int"     and not re.fullmatch(r'-?\d+', tok): tok=None

            o["label"] = tok  # 採点側は .label を比較する
            fout.write(json.dumps(o, ensure_ascii=False) + "\n")
            total_out += 1

    print(f"[OK] gold-aware normalized per-row {total_out}/{total_in} -> {out_p}")

if __name__ == "__main__":
    main()
