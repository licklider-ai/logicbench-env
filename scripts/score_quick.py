#!/usr/bin/env python3
import os, sys, json
from collections import OrderedDict

USAGE = "usage: score_quick.py <pred1.jsonl> [pred2.jsonl ...] <gold.jsonl> <out.csv>"
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def load_choices(data_path):
    """data/*.jsonl から id -> [choices...] を作る（options A/B/C/D にも対応）"""
    id2choices = {}
    if not data_path:
        return id2choices
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                o = json.loads(line)
                qid = o.get("id")
                ch  = o.get("choices")
                if not isinstance(ch, list):
                    opt = o.get("options") or {}
                    ch = [opt.get(k) for k in ("A","B","C","D") if opt.get(k) is not None]
                if qid and ch:
                    id2choices[qid] = [str(x).strip() for x in ch]
    except Exception:
        pass
    return id2choices

def pick_label(rec):
    """pred/output/answer/label/choice/selected/prediction.{label|choice} を順に拾う"""
    keys = ("pred","output","answer","label","choice","selected")
    for k in keys:
        v = rec.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
        if isinstance(v, dict):
            for kk in ("choice","label","pred","output"):
                vv = v.get(kk)
                if isinstance(vv, str) and vv.strip():
                    return vv.strip()
    pr = rec.get("prediction") or rec.get("predictions")
    if isinstance(pr, dict):
        for kk in ("label","choice","pred","output"):
            vv = pr.get(kk)
            if isinstance(vv, str) and vv.strip():
                return vv.strip()
    return ""

def text_to_label(qid, text, id2choices):
    """自由テキストを choices 経由で A/B/C/D に変換"""
    if not text:
        return ""
    text = str(text).strip()
    if len(text) == 1 and text.upper() in "ABCD":
        return text.upper()
    chs = id2choices.get(qid) or []
    # 正規化して完全一致
    low = text.lower().strip()
    for i, c in enumerate(chs):
        if low == str(c).lower().strip():
            return LETTERS[i] if i < len(LETTERS) else ""
    return ""

def main(argv):
    if len(argv) < 4:
        print(USAGE, file=sys.stderr)
        sys.exit(2)
    *pred_files, gold_path, out_csv = argv[1:]

    # choices をロード（環境変数 DATA があればそれを使う。なければ dev_20.norm を既定）
    data_path = os.environ.get("DATA") or "data/dev_20.norm.jsonl"
    id2choices = load_choices(data_path)

    # gold 読み込み（id -> 正解ラベル A/B/C/D）
    gold = OrderedDict()
    with open(gold_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            o = json.loads(line)
            lab = str(o.get("answer","")).strip()
            if not lab and isinstance(o.get("gold"), dict):
                lab = o["gold"].get("label","").strip()
            if o.get("id"):
                gold[o["id"]] = lab

    # 予測を統合
    pred = {}
    for pf in pred_files:
        with open(pf, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                o = json.loads(line)
                qid = o.get("id")
                if not qid:
                    continue
                lab = pick_label(o)
                if lab and lab.upper() in ("A","B","C","D"):
                    pred[qid] = lab.upper()
                else:
                    tlab = text_to_label(qid, lab, id2choices)
                    if tlab:
                        pred[qid] = tlab

    # 採点
    total = len(gold)
    correct = 0
    rows = [("id","category","gold","pred","correct","cost_usd")]
    for qid, g in gold.items():
        p = pred.get(qid, "")
        ok = int(p == g and g != "")
        correct += ok
        rows.append((qid, "unknown", g, p, ok, "0.000000"))

    # サマリ出力
    acc = (correct / total) if total else 0.0
    print("\n== Summary ==")
    print(f"Total: {total:>2}  Correct: {correct}  Accuracy: {acc:.3f}  Cost: $0.0000")
    print("\n== By Category ==")
    print(f"unknown       n={total:>2}  acc={acc:.3f}  cost=$0.0000")

    # CSV 書き出し
    with open(out_csv, "w", encoding="utf-8") as w:
        for r in rows:
            w.write("{},{},{},{},{},{}\n".format(r[0], r[1], r[2], r[3], r[4], r[5]))
    print(f"CSV={out_csv}")

if __name__ == "__main__":
    main(sys.argv)
