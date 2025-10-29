#!/usr/bin/env python3
import sys, csv, pathlib, statistics as st

if len(sys.argv) < 3:
    print("usage: make_report_simple.py <summary.csv> <report.md>", file=sys.stderr)
    sys.exit(2)

csv_path = pathlib.Path(sys.argv[1])
md_path  = pathlib.Path(sys.argv[2])
rows = []

if not csv_path.exists():
    print(f"[error] CSV not found: {csv_path}", file=sys.stderr)
    sys.exit(1)

with csv_path.open(newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        rows.append(r)

# 総括（列の有無に合わせて柔軟に）
total = len(rows)
n_correct = sum(1 for r in rows if r.get('correct') in ('1','True','true','YES','Yes','yes'))
acc = (n_correct / total) if total else 0.0

# コスト列があれば集計
def f2(x, default=0.0):
    try:
        return float(x)
    except:
        return default

cost_in  = [f2(r.get('cost_in'))  for r in rows if r.get('cost_in')  is not None]
cost_out = [f2(r.get('cost_out')) for r in rows if r.get('cost_out') is not None]
cost_tot = [f2(r.get('cost_total')) for r in rows if r.get('cost_total') is not None]
cost_total = sum(cost_tot) if cost_tot else (sum(cost_in)+sum(cost_out))

# カテゴリ（category 列があれば）
by_cat = {}
for r in rows:
    cat = r.get('category','unknown')
    by_cat.setdefault(cat, []).append(r)

def fmt_row(r):
    cols = ('id','category','pred','gold','correct')
    return " | ".join(str(r.get(c,'')) for c in cols)

with md_path.open('w', encoding='utf-8') as w:
    w.write(f"# LogicBench Report\n\n")
    w.write(f"- CSV: `{csv_path.name}`\n")
    w.write(f"- Total: **{total}**  Correct: **{n_correct}**  Accuracy: **{acc:.3f}**\n")
    w.write(f"- Cost (if any): **${cost_total:.4f}**\n\n")
    if by_cat:
        w.write("## By Category\n")
        for cat, rs in sorted(by_cat.items()):
            n = len(rs)
            c = sum(1 for r in rs if r.get('correct') in ('1','True','true','YES','Yes','yes'))
            a = (c/n) if n else 0.0
            w.write(f"- {cat:12s} n={n:3d} acc={a:.3f}\n")
        w.write("\n")
    # 明細（最大50件）
    w.write("## Samples (up to 50)\n\n")
    w.write("id | category | pred | gold | correct\n")
    w.write("---|---|---|---|---\n")
    for r in rows[:50]:
        w.write(fmt_row(r)+"\n")

print(f"[done] report -> {md_path}")
