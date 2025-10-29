#!/usr/bin/env python3
import json, sys, pathlib, re

INP  = pathlib.Path(sys.argv[1])   # pred_....norm.jsonl （id, output/pred/pred_raw 等）
DATA = pathlib.Path(sys.argv[2])   # dataset （choices/options を持つ）
OUT  = pathlib.Path(sys.argv[3])   # 出力：*.choicesaware.jsonl

LETTERS = ['A','B','C','D']

def norm_token(s):
    if s is None: return ""
    u = str(s).strip()
    U = u.upper()
    m = re.search(r'ANSWER:\s*([A-Z]|YES|NO|TRUE|FALSE|[-+]?\d+)\b', U)
    if m: U = m.group(1)
    if U == "TRUE":  U = "YES"
    if U == "FALSE": U = "NO"
    return U.split()[0].strip(",.;:") if U else ""


def to_letter_index_from_choices(tok, choices):
    """tok を choices から探し index を返す。まず大小無視の完全一致、次に先頭語一致を試す。なければ None。"""
    if not isinstance(choices, list): 
        return None
    # 正規化
    tok_str = str(tok).strip()
    tok_cf  = tok_str.casefold()

    c_raw = [str(x) for x in choices]
    c_norm = [c.strip() for c in c_raw]
    c_cf   = [c.casefold() for c in c_norm]

    # 1) 大小無視の完全一致
    if tok_cf in c_cf:
        return c_cf.index(tok_cf)

    # 2) 先頭語一致（例: "EMILY" vs "Emily Brontë"）
    tok_first = tok_cf.split()[0] if tok_cf else ""
    if tok_first:
        for i, cc in enumerate(c_cf):
            first = cc.split()[0] if cc else ""
            if tok_first == first:
                return i

    return None


def main():
    # dataset を id->obj に
    ds = {}
    with DATA.open(encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if not line: continue
            try:
                o=json.loads(line)
                ds[str(o.get("id"))]=o
            except:
                pass

    out = OUT.open("w", encoding="utf-8")
    with INP.open(encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if not line: continue
            o = json.loads(line)
            rid = str(o.get("id"))
            row = {
                "id": rid,
                "category": o.get("category") or "unknown",
            }

            # 生出力をできるかぎり拾って pred_raw に保存
            raw_src = (
                o.get("pred_raw")
                or o.get("pred")
                or o.get("label")
                or o.get("answer")
                or o.get("output")
                or ""
            )
            row["pred_raw"] = str(raw_src)

            # レター候補（A-D/YES/NO/数値…）へ正規化
            tok = norm_token(raw_src)

            # データセット側の choices/options
            dso = ds.get(rid) or {}
            choices = dso.get("choices") if isinstance(dso.get("choices"), list) else dso.get("options")
            if not isinstance(choices, list):
                choices = None

            # 1) 既に A-D ならそれを採用
            label = tok if tok in LETTERS else None

            # 2) YES/NO はそのまま（採点側で扱う前提）
            if label is None and tok in ("YES","NO"):
                label = tok

            # 3) 数値や文字列が choices のどれかに一致すれば A-D へ逆写像
            if label is None and choices:
                idx = to_letter_index_from_choices(tok, choices)
                if idx is not None and 0 <= idx < len(LETTERS):
                    label = LETTERS[idx]

            # 4) それでも決まらない場合は無指定のまま（絶対に既定で "A" などにしない）
            if label:
                row["label"] = label
                row["pred"]  = label  # scorer 互換

            # usage はあれば保持
            if "usage" in o:
                row["usage"] = o["usage"]

            out.write(json.dumps(row, ensure_ascii=False) + "\n")
    out.close()

if __name__ == "__main__":
    main()
