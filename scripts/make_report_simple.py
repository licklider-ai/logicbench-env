import csv, argparse, pathlib
from collections import defaultdict

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("summary_csv")
    ap.add_argument("out_md")
    args=ap.parse_args()

    rows=[]
    with open(args.summary_csv) as f:
        rd=csv.DictReader(f)
        for r in rd:
            rows.append(r)

    total=len(rows)
    hit=sum(int(r["correct"]) for r in rows)
    cost=sum(float(r["cost_usd"]) for r in rows)
    acc=hit/total if total else 0.0

    by_cat=defaultdict(list)
    for r in rows: by_cat[r["category"]].append(r)
    lines=[]
    lines.append(f"# LogicBench テストレポート\n")
    lines.append(f"- 合計: **{total}**  / 正解: **{hit}**  / 正答率: **{acc:.3f}**")
    lines.append(f"- 推定APIコスト: **${cost:.4f}** (実行時トークンから概算)\n")
    lines.append("## カテゴリ別集計\n")
    lines.append("| Category | Count | Correct | Accuracy | Cost (USD) |")
    lines.append("|---|---:|---:|---:|---:|")
    for cat, lst in sorted(by_cat.items()):
        c=len(lst); h=sum(int(r["correct"]) for r in lst)
        a=h/c if c else 0.0
        cc=sum(float(r["cost_usd"]) for r in lst)
        lines.append(f"| {cat} | {c} | {h} | {a:.3f} | {cc:.4f} |")
    lines.append("\n## 明細（上位20件）\n")
    for r in rows[:20]:
        lines.append(f"- `{r['id']}` [{r['category']}] gold=`{r['gold']}` pred=`{r['pred']}` correct={r['correct']} cost=${r['cost_usd']}")
    pathlib.Path(args.out_md).write_text("\n".join(lines), encoding="utf-8")

if __name__=="__main__":
    main()
