# scripts/score.py (robust fallback & normalizer)
import sys, json, re
import pandas as pd

ASCII_PUNCT = r"[\\.,!?:;'\"()\\[\\]{}]"

def norm_text(s):
    if s is None:
        return ""
    s = str(s).strip().lower()
    s = s.replace("はい","yes").replace("いいえ","no")
    s = s.replace("true","yes").replace("false","no")
    s = s.replace("y","yes").replace("n","no")
    s = re.sub(r"\s+","", s)
    s = re.sub(ASCII_PUNCT,"", s)
    return s

def try_parse_json(s):
    try:
        return json.loads(s)
    except Exception:
        return None

ALT_KEYS = ["final_answer","final","answer","result","output","prediction"]

def extract_final(parsed, raw_text):
    # 1) parsed に期待キーがあればそれを使う
    if isinstance(parsed, dict):
        for k in ALT_KEYS:
            if k in parsed:
                return parsed[k]
    # 2) raw_text が JSON なら同様に探す
    j = try_parse_json(raw_text or "")
    if isinstance(j, dict):
        for k in ALT_KEYS:
            if k in j:
                return j[k]
    # 3) JSONでない場合は簡易抽出（数値 / Yes-No 系）
    txt = (raw_text or "").strip()
    m = re.search(r"-?\\d+(?:\\.\\d+)?", txt)
    if m:
        return m.group(0)
    m = re.search(r"\\b(yes|no|true|false|はい|いいえ)\\b", txt, re.I)
    if m:
        w = m.group(1).lower()
        return {"true":"Yes","false":"No","はい":"Yes","いいえ":"No"}.get(w, w.title())
    return None

def is_correct(pred, gold, tol_abs=0.0, tol_rel=0.0):
    try:
        p = float(pred); g = float(gold)
        return abs(p-g) <= max(tol_abs, tol_rel*abs(g))
    except Exception:
        return norm_text(pred) == norm_text(gold)

def main(in_path, gold_path, out_csv):
    preds = [json.loads(l) for l in open(in_path,"r",encoding="utf-8") if l.strip()]
    gold  = {}
    with open(gold_path,"r",encoding="utf-8") as f:
        for l in f:
            if not l.strip(): continue
            o = json.loads(l); gold[o["id"]] = o.get("answer", o.get("output"))


    rows = []
    for r in preds:
        sid = r.get("sample_id")
        pred = extract_final(r.get("parsed"), r.get("raw_text"))
        g = gold.get(sid)
        ok = is_correct(pred, g)
        rows.append({
            "sample_id": sid,
            "final_answer": pred,
            "gold": g,
            "correct": int(ok),
            "latency_ms": r.get("latency_ms")
        })

    df = pd.DataFrame(rows)
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")
    acc = df["correct"].mean() if len(df) else 0.0
    print(f"acc={acc:.3f}, wrote {out_csv}")

if __name__ == "__main__":
    in_path  = sys.argv[1] if len(sys.argv)>1 else "runs/dev_raw.jsonl"
    gold_path= sys.argv[2] if len(sys.argv)>2 else "data/gold.jsonl"
    out_csv  = sys.argv[3] if len(sys.argv)>3 else "runs/dev_scored.csv"
    main(in_path, gold_path, out_csv)
