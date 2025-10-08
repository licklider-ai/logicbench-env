import os, json, time, argparse, sys
from pathlib import Path
from typing import Dict, Any
from openai import OpenAI

MODEL = os.getenv("LB_MODEL", os.getenv("OPENAI_MODEL", "o1-mini"))
SLEEP_SEC = 2

def pick_text(sample: Dict[str, Any]) -> str:
    for k in ["prompt","question","input","query","text","problem"]:
        if k in sample and isinstance(sample[k], str) and sample[k].strip():
            return sample[k]
    if "choices" in sample and isinstance(sample["choices"], list):
        return f"{sample.get('question','')}\nChoices: " + ", ".join(map(str,sample["choices"]))
    return json.dumps(sample, ensure_ascii=False)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dev_path")
    ap.add_argument("out_path")
    ap.add_argument("--max", type=int, default=20)
    args = ap.parse_args()

    dev_path = Path(args.dev_path)
    out_path = Path(args.out_path)

    client = OpenAI()

    done = 0
    out_f = out_path.open("w", encoding="utf-8")

    print(f"[start] {dev_path} -> {out_path} (model={MODEL})", flush=True)
    with dev_path.open() as f:
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
                resp = client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {"role":"system","content":"Answer as briefly and decisively as possible."},
                        {"role":"user","content":user_text}
                    ],
                    temperature=0.2,
                )
                raw = resp.choices[0].message.content.strip()
                usage = getattr(resp, "usage", None)
                in_tok = getattr(usage, "prompt_tokens", None) if usage else None
                out_tok = getattr(usage, "completion_tokens", None) if usage else None
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
            time.sleep(SLEEP_SEC)
    out_f.close()
    print(f"[done] wrote {done} predictions to {out_path}", flush=True)

if __name__ == "__main__":
    main()
