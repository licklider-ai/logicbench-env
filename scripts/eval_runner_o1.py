import os, json, time, argparse, sys
from pathlib import Path
from typing import Dict, Any
from openai import OpenAI

MODEL = os.getenv("LB_MODEL", os.getenv("OPENAI_MODEL", "o1-mini"))
SLEEP_SEC = 2

def pick_text(sample: Dict[str, Any]) -> str:
    for k in ["prompt","question","input","query","text","problem","stem"]:
        if k in sample and isinstance(sample[k], str) and sample[k].strip():
            return sample[k]
    if "choices" in sample and isinstance(sample["choices"], list):
        base = sample.get("question", sample.get("stem",""))
        return f"{base}\nChoices: " + ", ".join(map(str,sample["choices"]))
    return json.dumps(sample, ensure_ascii=False)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dev_path")
    ap.add_argument("out_path")
    ap.add_argument("--max", type=int, default=20)
    ap.add_argument("--sleep", type=float, default=SLEEP_SEC)
    ap.add_argument("--max_output_tokens", type=int, default=64)
    args = ap.parse_args()

    dev_path = Path(args.dev_path)
    out_path = Path(args.out_path)

    client = OpenAI()
    done = 0
    with out_path.open("w", encoding="utf-8") as out_f, dev_path.open() as f:
        print(f"[start] {dev_path} -> {out_path} (model={MODEL})", flush=True)
        for line in f:
            if args.max and done >= args.max:
                break
            try:
                ex = json.loads(line)
            except Exception as e:
                print(f"[warn] JSON parse error → skip: {e}", file=sys.stderr)
                continue

            sid = ex.get("id") or ex.get("_id") or ex.get("uid") or f"auto:{done:06d}"
            user_text = pick_text(ex)
            try:
                # Responses API（o1系はこちら）
                resp = client.responses.create(
                    model=MODEL,
                    input=user_text,
                    temperature=0.2,
                    max_output_tokens=args.max_output_tokens,
                    reasoning={"effort":"low"},
                    instructions=(
                        "Answer briefly and decisively. "
                        "If multiple-choice like A/B/C/D is present, reply with only the single letter."
                    ),
                )
                raw = (getattr(resp, "output_text", None) or "").strip()
                usage = getattr(resp, "usage", None)
                in_tok = getattr(usage, "input_tokens", None) if usage else None
                out_tok = getattr(usage, "output_tokens", None) if usage else None
            except Exception as e:
                print(f"[warn] API error → skip id={sid}: {e}", file=sys.stderr)
                continue

            rec = {
                "id": sid,
                "pred_raw": raw,
                "prompt": user_text,
                "category": ex.get("category"),
                "usage": {"prompt_tokens": in_tok, "completion_tokens": out_tok}
            }
            out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            out_f.flush()
            done += 1
            time.sleep(args.sleep)

    print(f"[done] wrote {done} predictions to {out_path}", flush=True)

if __name__ == "__main__":
    main()
