import json, sys, pathlib

pred = pathlib.Path(sys.argv[1])
gold = pathlib.Path(sys.argv[2])
out  = pathlib.Path(sys.argv[3])

gold_ids = set()
with gold.open(encoding='utf-8') as f:
    for line in f:
        line=line.strip()
        if not line: 
            continue
        try:
            o=json.loads(line)
        except:
            continue
        i = o.get("id")
        if i is not None:
            gold_ids.add(str(i))

n_in = n_out = 0
with pred.open(encoding='utf-8') as fi, out.open('w', encoding='utf-8') as fo:
    for line in fi:
        line = line.strip()
        if not line:
            continue
        n_in += 1
        try:
            o = json.loads(line)
        except:
            continue
        i = o.get("id")
        if i is not None and str(i) in gold_ids:
            fo.write(json.dumps(o, ensure_ascii=False) + "\n")
            n_out += 1

print(f"[OK] filtered {n_out}/{n_in} lines -> {out}")
