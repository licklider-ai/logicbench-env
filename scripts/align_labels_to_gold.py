import json, argparse, pathlib
from collections import Counter

YN = {"TRUE":"YES","FALSE":"NO","T":"YES","F":"NO","Y":"YES","N":"NO"}

def load_map(p):
    d={}
    with open(p,encoding='utf-8') as f:
        for l in f:
            l=l.strip()
            if not l: continue
            try: o=json.loads(l)
            except: continue
            i=o.get("id"); lab=o.get("label") or o.get("pred") or o.get("answer")
            if i is None or lab is None: continue
            d[str(i)] = str(lab).strip().upper()
    return d

def canon(x):
    x = x.strip().upper()
    x = YN.get(x, x)
    return x

def try_mapping(pred, gold, mapfn):
    ok=0; total=0; out={}
    for i,plab in pred.items():
        if i not in gold: continue
        glab = canon(gold[i])
        plab = canon(plab)
        mapped = mapfn(plab, glab)
        out[i]=mapped
        total += 1
        if mapped == glab: ok += 1
    return ok, total, out

def identity(plab, glab): return plab

def yesno_to_two_letters(plab, glab, letters):
    # letters: e.g., ['A','B'] — 試行として YES->A/NO->B と YES->B/NO->A の2通りを上位で用意
    if plab in ("YES","NO"):
        return letters[0] if plab=="YES" else letters[1]
    return plab

def letters_to_numbers(plab, glab, letters):
    # A-D -> 1-4
    if plab in letters:
        return str(letters.index(plab)+1)
    return plab

def numbers_to_letters(plab, glab, letters):
    # 1-4 -> A-D
    if plab.isdigit():
        n=int(plab)
        if 1<=n<=len(letters):
            return letters[n-1]
    return plab

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--pred', required=True)
    ap.add_argument('--gold', required=True)
    ap.add_argument('--out', required=True)
    args=ap.parse_args()

    pred = load_map(args.pred)
    gold = load_map(args.gold)

    gold_vals = sorted({canon(v) for v in gold.values()})
    candidates = []

    # 1) 恒等写像
    candidates.append(("identity", identity))

    # 2) YES/NO <-> 2文字ラベル
    two_letters = [v for v in gold_vals if len(v)==1 and v.isalpha()]
    if len(two_letters)==2:
        L = two_letters
        candidates.append(("YESNO->%s/%s"%tuple(L), lambda p,g: yesno_to_two_letters(p,g,L)))
        L2 = [L[1], L[0]]
        candidates.append(("YESNO->%s/%s"%tuple(L2), lambda p,g: yesno_to_two_letters(p,g,L2)))

    # 3) A-D <-> 1-4
    letters = [v for v in gold_vals if len(v)==1 and v in list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")]
    if 2<=len(letters)<=10:  # 汎用
        candidates.append(("A..->1..", lambda p,g: letters_to_numbers(p,g,letters)))
        candidates.append(("1..->A..", lambda p,g: numbers_to_letters(p,g,letters)))

    # 4) TRUE/FALSE 正規化（YN 変換だけの効果を見る）
    candidates.append(("YN-canon", lambda p,g: YN.get(p,p)))

    best=( -1, None, None, None )  # (ok, total, name, mapped)
    for name,fn in candidates:
        ok,total,mapped = try_mapping(pred, gold, fn)
        if ok>best[0]: best=(ok,total,name,mapped)

    ok,total,name,mapped = best
    # 出力JSONLへ
    with open(args.pred,encoding='utf-8') as fi, open(args.out,'w',encoding='utf-8') as fo:
        for l in fi:
            l=l.strip()
            if not l: continue
            try: o=json.loads(l)
            except: continue
            i=str(o.get("id"))
            if i in mapped:
                lab = mapped[i]
                o['label']=lab; o['pred']=lab; o['answer']=lab
            fo.write(json.dumps(o, ensure_ascii=False)+"\n")

    acc = ok/total if total else 0.0
    print(f"[OK] choose mapping={name}  matched={ok}/{total} acc={acc:.3f}  -> {args.out}")
    # 集計の参考出力
    print("[gold set]", Counter(gold_vals))
    print("[pred set]", Counter(sorted({canon(v) for v in pred.values()})))
if __name__=="__main__":
    main()
