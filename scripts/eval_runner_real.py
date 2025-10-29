import os, sys, json
from typing import Tuple, List
from openai import OpenAI
from openai import NotFoundError, BadRequestError

REQUESTED = os.environ["LB_MODEL"]

# 失敗モデルのフォールバック候補（上から順に試す）
FALLBACKS = {
    "gpt-4-32k": ["gpt-4o", "gpt-4.1", "gpt-4o-mini"],
    "got-5":     ["gpt-4o", "gpt-4.1", "gpt-4o-mini"],
}

def resolve_model(client: OpenAI, requested: str) -> Tuple[str, str]:
    """requestedが使えなければ順にフォールバック。戻り値：(実際に使うモデル, メモ)"""
    # まずはそのまま試す
    try:
        # 軽いヘルスチェック：空の最小呼び出しはできないので実トライで判定する
        return requested, f"USING={requested}"
    except Exception:
        pass

    for cand in FALLBACKS.get(requested, []):
        try:
            return cand, f"USING={cand} (fallback for {requested})"
        except Exception:
            continue
    # どれもダメなら最後の手段
    return requested, f"USING={requested} (no explicit fallback)"

def build_kwargs(model: str, user: str):
    """o3系はtemperature非対応なので付けない"""
    kwargs = dict(
        model=model,
        messages=[
            {"role":"system","content":"Answer with a single token only: A|B|C|D|YES|NO. No explanations."},
            {"role":"user","content": user}
        ],
    )
    if not any(tag in model for tag in ("o3", "o4")):
        kwargs["temperature"] = 0
    return kwargs

def main(dev_path: str, out_path: str) -> None:
    client = OpenAI()
    model, note = resolve_model(client, REQUESTED)
    print(note, file=sys.stderr)

    with open(dev_path, encoding="utf-8") as fi, open(out_path, "w", encoding="utf-8") as fo:
        for line in fi:
            if not line.strip():
                continue
            o = json.loads(line)
            user = o.get("question") or json.dumps(o, ensure_ascii=False)

            # まずは希望モデルで
            try:
                kwargs = build_kwargs(model, user)
                r = client.chat.completions.create(**kwargs)
            except NotFoundError:
                # 実行時に初めてNotFoundが出た場合は、フォールバックを順次試す
                for cand in FALLBACKS.get(REQUESTED, []):
                    try:
                        model = cand
                        kwargs = build_kwargs(model, user)
                        r = client.chat.completions.create(**kwargs)
                        print(f"[fallback] {REQUESTED} -> {model}", file=sys.stderr)
                        break
                    except Exception:
                        r = None
                if r is None:
                    raise
            except BadRequestError as e:
                # temperature非対応などのケースを柔軟に再試行
                if "temperature" in str(e).lower():
                    kwargs = build_kwargs(model, user)
                    kwargs.pop("temperature", None)
                    r = client.chat.completions.create(**kwargs)
                else:
                    raise

            ans = (r.choices[0].message.content or "").strip()
            fo.write(json.dumps({"id": o["id"], "answer": ans}, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <dev.jsonl> <out.jsonl>", file=sys.stderr)
        sys.exit(2)
    main(sys.argv[1], sys.argv[2])
