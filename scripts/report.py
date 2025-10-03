
# scripts/report.py
import sys, pandas as pd

def main(in_csv, out_csv_summary):
    df = pd.read_csv(in_csv)
    acc = df["correct"].mean() if len(df) else 0.0
    lat = df["latency_ms"].mean() if "latency_ms" in df.columns else None
    summary = pd.DataFrame([{"acc": acc, "avg_latency_ms": lat, "n": len(df)}])
    summary.to_csv(out_csv_summary, index=False, encoding="utf-8-sig")
    print(summary)

if __name__ == "__main__":
    # python scripts/report.py runs/dev_scored.csv reports/summary.csv
    in_csv = sys.argv[1] if len(sys.argv)>1 else "runs/dev_scored.csv"
    out_csv = sys.argv[2] if len(sys.argv)>2 else "reports/summary.csv"
    main(in_csv, out_csv)
