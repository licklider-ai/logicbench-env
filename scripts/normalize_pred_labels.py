import re, json, argparse, sys, pathlib

def extract_label(s: str):
    if not s: return None
    s = str(s).strip()
    # 明示の "Answer:" / "Final answer:" を最優先で抽出
    m = re.search(r'(?i)\b(?:final\s+answer|answer)\s*[:：]\s*([A-Z]|YES|NO|TRUE|FALSE|-?\d+)\b', s)
    if m:
        tok = m.group(1).upper()
    else:
        last = s.splitlines()[-1].strip()
        # 単独の A〜Z / YES/NO / 数値を拾う
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

def normalize_obj(o: dict):
    # 候補フィールドから予測文字列を抽出
    candidates = ['pred','answer','label','final','completion','output','text','response','prediction','model_output']
    lab = None
    for k in candidates:
        v = o.get(k)
        if isinstance(v, str) and v.strip():
            lab = extract_label(v)
            if lab: break
    # choice/index 系の数値や文字も拾う
    if not lab:
        for k in ['choice','selected','prediction_index','index']:
            v = o.get(k)
            if isinstance(v, str) and re.fullmatch(r'[A-Za-z]', v.strip()):
                lab = v.strip().upper(); break
            if isinstance(v, (int,)) or (isinstance(v,str) and re.fullmatch(r'-?\d+', v.strip())):
                lab = str(v).strip(); break
    if lab:
        o['pred']=lab
        o['answer']=lab
        o['label']=lab
    return o

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--inp', required=True)
    ap.add_argument('--out', required=True)
    args=ap.parse_args()
    pin = pathlib.Path(args.inp); pout = pathlib.Path(args.out)
    n=0
    with pin.open(encoding="utf-8") as fi, pout.open('w',encoding='utf-8') as fo:
        for line in fi:
            line=line.strip()
            if not line: continue
            try:
                o=json.loads(line)
            except:
                continue
            o=normalize_obj(o)
            fo.write(json.dumps(o, ensure_ascii=False)+"\n"); n+=1
    print(f"[OK] normalized {n} lines -> {pout}")
if __name__=="__main__":
    main()
