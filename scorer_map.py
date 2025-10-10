import json, re, unicodedata, string
from pathlib import Path
from collections import Counter
from datetime import datetime

LETTERS = "ABCDEFGHIJ"

def nfkc(s): return unicodedata.normalize("NFKC", str(s))
def nfkc_lower(s): return nfkc(s).lower().strip()
def strip_punct_ws(s):
    tbl = str.maketrans("", "", string.punctuation + "、。・，，：；！？”“’'\"（）()[]{}")
    return nfkc_lower(s).translate(tbl).replace(" ", "").replace("\u3000","")

MAP_NUM = {
 "10":"J","1":"A","2":"B","3":"C","4":"D","5":"E","6":"F","7":"G","8":"H","9":"I",
 "①":"A","②":"B","③":"C","④":"D","⑤":"E","⑥":"F","⑦":"G","⑧":"H","⑨":"I","⑩":"J",
 "Ⅰ":"A","Ⅱ":"B","Ⅲ":"C","Ⅳ":"D","Ⅴ":"E","Ⅵ":"F","Ⅶ":"G","Ⅷ":"H","Ⅸ":"I","Ⅹ":"J",
}
def num_to_letter(t:str)->str:
    t = nfkc(t)
    if re.search(r"\b10\b", t): return "J"
    for k,v in MAP_NUM.items():
        if k in t: return v
    m = re.search(r"[A-Za-z]", t)
    return m.group(0).upper() if m else ""

def load_jsonl(p: Path):
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line:
                yield json.loads(line)

def extract_choices(ex: dict):
    # 1) choices: [...]
    if isinstance(ex.get("choices"), list) and ex["choices"]:
        return [str(c) for c in ex["choices"]]
    # 2) A/B/C/... キー
    ls=[]
    for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        if ch in ex: ls.append(str(ex[ch]))
        else: break
    if len(ls)>=2: return ls
    # 3) messages(user).content 埋め込み
    if isinstance(ex.get("input"), list):
        user_txt = ""
        for t in ex["input"]:
            if t.get("role")=="user":
                user_txt = str(t.get("content") or "")
                break
        if user_txt:
            m = re.findall(r"(?m)^[\s]*([A-J])[\.\):：]\s*(.+?)\s*$", user_txt)
            if m:
                return [c.strip() for _,c in sorted(m, key=lambda x:x[0])]
            nums = re.findall(r"(?m)^[\s]*(10|[1-9])[\.\):：]\s*(.+?)\s*$", user_txt)
            if nums:
                return [c.strip() for _,c in sorted([(int(n),c) for n,c in nums])]
    return []

# 入力ファイル
data_path = Path("data/dev_20.jsonl")
gold_path = Path("data/gold_20.jsonl")
pred_path = max(Path("runs").glob("pred_gpt-4o-mini_*.jsonl"), key=lambda p: p.stat().st_mtime)

# id -> choices
id2choices = {}
for ex in load_jsonl(data_path):
    i = ex.get("id", ex.get("qid", ex.get("sample_id")))
    id2choices[i] = extract_choices(ex)

# gold のキー推定
cands=["answer","gold","label","correct","correct_answer","target","solution","ideal"]
gkey=None
gold_rows=list(load_jsonl(gold_path))
for r in gold_rows:
    for k in cands:
        if k in r: gkey=k; break
    if gkey: break

# gold を A/B/... に正規化（テキストは choices と突き合わせ）
gold_map={}
for r in gold_rows:
    i = r.get("id", r.get("qid", r.get("sample_id")))
    raw = str(r.get(gkey,""))
    letter = num_to_letter(raw)
    if not letter:
        choices = id2choices.get(i, [])
        if choices:
            raw_n = nfkc_lower(raw); raw_s = strip_punct_ws(raw)
            hit = [idx for idx,c in enumerate(choices) if nfkc_lower(c)==raw_n]
            if not hit:
                hit = [idx for idx,c in enumerate(choices) if strip_punct_ws(c)==raw_s]
            if not hit and raw_n:
                hit = [idx for idx,c in enumerate(choices) if raw_n in nfkc_lower(c) or nfkc_lower(c) in raw_n]
            if len(hit)==1:
                letter = LETTERS[hit[0]]
    gold_map[i] = letter or ""

# pred を読み込み
pred_map={}
for r in load_jsonl(pred_path):
    i = r.get("id", r.get("qid", r.get("sample_id")))
    p = (r.get("prediction") or r.get("answer") or "").strip().upper()
    pred_map[i] = p[:1] if p[:1] in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" else ""

# 共通ID集合で採点
ids = sorted(set(gold_map.keys()) & set(pred_map.keys()))
ok=n=0; rows=[]
for i in ids:
    yt = gold_map.get(i,"")
    yp = pred_map.get(i,"")
    corr = int(yp!="" and yt!="" and yp==yt)
    ok += corr; n += 1
    rows.append((i, yt, yp, corr))
acc = ok/n if n else 0.0
print(f"accuracy={acc:.3f}  ({ok}/{n})")
print("gold dist:", Counter([v for v in gold_map.values() if v]))
print("pred dist:", Counter([v for v in pred_map.values() if v]) or {"''": sum(1 for v in pred_map.values() if not v)})

# スコアCSV
out = Path("runs")/f"dev_scored_mapped_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
out.write_text("id,gold,pred,correct\n" + "\n".join(",".join(map(str,r)) for r in rows), encoding="utf-8")
print("wrote:", out)
