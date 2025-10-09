import json, csv, pathlib, re, sys, unicodedata

def extract_letter_strict(s):
    if s is None: return "NONE"
    t = unicodedata.normalize("NFKC", str(s)).strip().upper()
    if re.fullmatch(r"[ABCD]", t): return t
    _PUNCT = r"[ \t\r\n\f\v\.\,;:!?\)\]\}、。・】）」』]*"
    m = re.fullmatch(rf"([ABCD]){_PUNCT}", t) or re.match(rf"^\s*([ABCD]){_PUNCT}", t)
    if m: return m.group(1)
    m = re.search(r"(?<![A-Z])([ABCD])(?![A-Z])", t)
    return m.group(1) if m else "NONE"

def main(pred_path, gold_path, out_csv):
    gold_rows = [json.loads(l) for l in pathlib.Path(gold_path).open(encoding="utf-8") if l.strip()]
    pred_rows = [json.loads(l) for l in pathlib.Path(pred_path).open(encoding="utf-8") if l.strip()]

    # gold 側の join キー自動検出
    ignore = {"gold","label","answer","options","opts","choices","question","prompt","context","category","cat"}
    keys = set().union(*map(set, gold_rows))
    cands = []
    for k in keys - ignore:
        vals = [g.get(k) for g in gold_rows]
        if any(v is None for v in vals): 
            continue
        sval = list(map(str, vals))
        if len(set(sval)) == len(sval):
            cands.append(k)
    prio = ["id","name","sample_id","question_id","qid","uid","problem_id","sample","task_id","example_id","key","item_id"]
    if not cands:
        print("ERR: could not detect join key from gold", file=sys.stderr); sys.exit(2)
    join_key = sorted(cands, key=lambda k:(prio.index(k) if k in prio else 999, k))[0]

    # gold の正解ラベルキー
    lab_key = next((k for k in ("gold","label","answer") if k in gold_rows[0]), None)
    if lab_key is None:
        for k in gold_rows[0]:
            vs = [str(r.get(k)).strip().upper() for r in gold_rows]
            if all(v in {"A","B","C","D"} for v in vs):
                lab_key = k; break
    if not lab_key:
        print("ERR: gold label key not found", file=sys.stderr); sys.exit(2)

    # pred 側の id/pred/cost を抽出
    id_keys   = [join_key,"id","name","sample_id","question_id","qid","uid","problem_id","sample","task_id","example_id","key","item_id"]
    pred_keys = ("pred","prediction","answer","output","text","response","label","choice","y","final")
    def pick_id(d):
        for k in id_keys:
            if k in d and d[k] is not None:
                return str(d[k])
    def pick_pred(d):
        for k in pred_keys:
            if k in d and d[k] is not None:
                return extract_letter_strict(d[k])
        return "NONE"
    def pick_cost(d):
        for k in ("cost_usd","cost","usd_cost"):
            if k in d and d[k] is not None:
                try: return float(d[k])
                except: pass
        return 0.0

    pmap, cmap = {}, {}
    for pr in pred_rows:
        pid = pick_id(pr)
        if not pid: 
            continue
        pmap[pid] = pick_pred(pr)
        cmap[pid] = pick_cost(pr)

    out_p = pathlib.Path(out_csv)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    with out_p.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id","category","gold","pred","correct","cost_usd"])
        for gr in gold_rows:
            gid = str(gr[join_key])
            g   = str(gr[lab_key]).strip().upper()
            p   = pmap.get(gid, "NONE")
            cor = 1 if p == g else 0
            cat = gr.get("category","unknown")
            w.writerow([gid, cat, g, p, cor, f"{cmap.get(gid,0.0):.6f}"])

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("usage: python scripts/score_and_cost_flexible.py <pred_jsonl> <gold_jsonl> <out_csv>")
        sys.exit(2)
    main(sys.argv[1], sys.argv[2], sys.argv[3])
