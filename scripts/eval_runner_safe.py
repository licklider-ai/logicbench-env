from openai import OpenAI
import os, re, json, sys, pathlib, time

PROMPT_KEYS = ["prompt", "question", "input", "problem", "text", "stem"]

def _usage_to_dict(usage):
    if usage is None:
        return {}
    if isinstance(usage, dict):
        return usage
    if hasattr(usage, "model_dump"):
        return usage.model_dump()
    if hasattr(usage, "dict"):
        return usage.dict()
    out = {}
    for k in ("prompt_tokens","completion_tokens","total_tokens",
              "cache_write_tokens","cache_read_tokens"):
        if hasattr(usage, k):
            v = getattr(usage, k)
            if v is not None:
                out[k] = v
    return out

def iter_samples(path):
    """JSONLの各行を辞書に正規化"""
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            s = line.strip()
            if not s:
                continue
            try:
                obj = json.loads(s)
            except Exception:
                obj = s
            if isinstance(obj, str):
                yield {"id": f"auto:{i}", "prompt": obj}
            elif isinstance(obj, dict):
                if "id" not in obj:
                    obj["id"] = f"auto:{i}"
                if not any(k in obj for k in PROMPT_KEYS):
                    obj["prompt"] = json.dumps(obj, ensure_ascii=False)
                yield obj
            else:
                yield {"id": f"auto:{i}", "prompt": str(obj)}

def extract_user_prompt(sample: dict) -> str:
    # stem+choices がある場合は A) 形式で連結
    if isinstance(sample.get("stem"), str) and isinstance(sample.get("choices"), list):
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        lines = [f"Question: {sample['stem']}"]
        for i, c in enumerate(sample["choices"]):
            lines.append(f"{letters[i]}) {c}")
        return "\n".join(lines)
    # 通常キー優先
    for k in PROMPT_KEYS:
        v = sample.get(k)
        if isinstance(v, str) and v.strip():
            return v
    return json.dumps(sample, ensure_ascii=False)

def call_single_token_answer(client, model_name: str, user_prompt: str):
    LB_MODEL = os.getenv("LB_MODEL", model_name)
    system_rule = "Answer with a single token only: A|B|C|D|YES|NO. No explanations."
    prompt = user_prompt + "\n\nReturn ONLY one final line in the exact format:\nAnswer: <A|B|C|D|YES|NO>"
    messages = [
        {"role": "system", "content": system_rule},
        {"role": "user", "content": prompt},
    ]
    resp = client.chat.completions.create(
        model=LB_MODEL, messages=messages,
        temperature=0, top_p=1, max_tokens=8, stop=["\n"],
    )
    text = (resp.choices[0].message.content or "").strip()
    usage = _usage_to_dict(getattr(resp, "usage", None))
    m = re.search(r'^\s*Answer:\s*(A|B|C|D|YES|NO)\s*$', text, re.I)
    if m:
        token = m.group(1).upper()
    else:
        m2 = re.search(r'\b(A|B|C|D|YES|NO)\b', text.upper())
        token = m2.group(1) if m2 else "A"
    return f"Answer: {token}", usage

def main():
    if len(sys.argv) != 3:
        print("Usage: python scripts/eval_runner_safe.py <dev_jsonl> <out_jsonl>", file=sys.stderr)
        sys.exit(2)
    in_path  = sys.argv[1]
    out_path = sys.argv[2]
    pathlib.Path(os.path.dirname(out_path) or ".").mkdir(parents=True, exist_ok=True)

    client = OpenAI()
    model_name = os.environ["LB_MODEL"]
    sleep_s = float(os.getenv("LB_SLEEP", "0"))

    total = 0
    with open(out_path, "w", encoding="utf-8") as out:
        for sample in iter_samples(in_path):
            total += 1
            sid = sample.get("id", f"auto:{total}")
            user_prompt = extract_user_prompt(sample)
            pred_text, usage = call_single_token_answer(client, model_name, user_prompt)
            row = {
                "id": sid,
                "prompt": user_prompt,
                "prediction": pred_text,
                "model": os.getenv("LB_MODEL", model_name),
                "usage": usage,
            }
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
            out.flush()
            if sleep_s > 0:
                time.sleep(sleep_s)
    print(f"[done] {in_path} -> {out_path} (n={total})")

if __name__ == "__main__":
    main()
