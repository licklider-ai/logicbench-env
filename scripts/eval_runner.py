import os, argparse
import time
import sys, pathlib; sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))
from openai import OpenAI
from lb_runtime import (
    LLMCaller, RetryPolicy, load_jsonl, dump_obj, log_path, make_dbg_id
)

MODEL_DEFAULT = os.getenv("LB_MODEL", "gpt-4o-mini")

def ask_model(caller: LLMCaller, model: str, prompt: str,
              temperature: float | None, top_p: float | None, dbg_id: str) -> str:
    try:
        return caller.call_chat(
            model=model, system="You are a helpful judge.",
            user=prompt, dbg_id=dbg_id,
            temperature=temperature, top_p=top_p,
        )
    except Exception:
        return caller.call_responses(
            model=model, input_text=prompt, dbg_id=dbg_id,
            temperature=temperature, top_p=top_p,
        )

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("in_path")
    ap.add_argument("out_path")
    ap.add_argument("--model", default=MODEL_DEFAULT)
    ap.add_argument("--temperature", type=float, default=None)
    ap.add_argument("--top_p", type=float, default=None)
    ap.add_argument("--retries", type=int, default=8)
    ap.add_argument("--base_delay", type=float, default=1.0)
    ap.add_argument("--max_delay", type=float, default=60.0)
    args = ap.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY が未設定です。")

    client = OpenAI(api_key=api_key)
    policy = RetryPolicy(retries=args.retries, base_delay=args.base_delay, max_delay=args.max_delay)
    caller = LLMCaller(client, retry=policy)

    items = load_jsonl(args.in_path)
    outputs = []
    for i, row in enumerate(items):
        dbg_id = make_dbg_id(i, prefix="eval")
        prompt = row.get("prompt") or row.get("input") or ""
        ans = ask_model(
            caller, args.model, prompt,
            temperature=args.temperature, top_p=args.top_p, dbg_id=dbg_id
        )
        outputs.append({"id": row.get("id", i), "output": ans, "dbg_id": dbg_id})

    dump_obj(outputs, args.out_path)
    dump_obj({
        "model": args.model,
        "temperature": args.temperature,
        "top_p": args.top_p,
        "count": len(outputs),
    }, log_path("runs", f"runmeta-{make_dbg_id(prefix='meta')}.json"))

if __name__ == "__main__":
    main()
