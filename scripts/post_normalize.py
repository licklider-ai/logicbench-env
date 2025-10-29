#!/usr/bin/env python3
import os, sys, json, glob

from scripts.utils_normalize import to_label

def load_choices(data_path):
    id2choices = {}
    with open(data_path, encoding="utf-8") as f:
        for l in f:
            if not l.strip(): continue
            o = json.loads(l)
            qid = o.get("id")
            ch  = o.get("choices")
            if not isinstance(ch, list):
                opt = o.get("options") or {}
                ch = [opt.get(k) for k in ("A","B","C","D") if opt.get(k) is not None]
            if qid and ch:
                id2choices[qid] = [str(x) for x in ch]
    return id2choices

def pick_text(rec):
    # 生出力の取り得るキーを総なめ
    for k in ("output","pred","answer","label","choice","selected"):
        v = rec.get(k)
        if isinstance(v, str) and v.strip(): return v.strip()
        if isinstance(v, dict):
            for kk in ("output","pred","answer","label","choice","selected"):
                vv = v.get(kk)
                if isinstance(vv, str) and vv.strip(): return vv.strip()
    return ""

def main(data_path, raw_pred_path, out_path):
    id2choices = load_choices(data_path)
    n_in = n_out = 0
    with open(raw_pred_path, encoding="utf-8") as f, open(out_path, "w", encoding="utf-8") as w:
        for l in f:
            if not l.strip(): continue
            r = json.loads(l); n_in += 1
            qid = r.get("id")
            ch  = id2choices.get(qid, [])
            txt = pick_text(r)
            lab = to_label(txt, ch)
            w.write(json.dumps({"id": qid, "pred": lab, "output": lab}, ensure_ascii=False) + "\n")
            n_out += 1
    print(f"[post-normalize] read={n_in} wrote={n_out} -> {out_path}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("usage: post_normalize.py <data.jsonl> <raw_pred.jsonl> <out.jsonl>")
        sys.exit(2)
    main(sys.argv[1], sys.argv[2], sys.argv[3])
