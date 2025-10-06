
# scripts/run_eval.py
from __future__ import annotations
import os, json, time, sys
from dataclasses import dataclass
from typing import Any, Dict
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError
from rich import print
from rich.progress import track

# Optional: OpenAI client (real run). If not configured, fallback to dry-run.
try:
    from openai import OpenAI
except Exception:
    OpenAI = None  # type: ignore

SYSTEM_PROMPT = (
    "あなたは論理推論タスクを解くアシスタントです。"
    "回答は『短い要点サマリ（2–4行）』と『最終回答』のみ。"
    "出力は日本語、かつ 指定のJSON形式のみ（前後の説明禁止）。"
    "不確実なら不確実と明示。"
)

JSON_INSTRUCTION = (
    "以下のJSONのみを返してください。"
    '{"key_step_summary":"…","final_answer":<値>,"confidence":0.0}'
)

class ModelOut(BaseModel):
    key_step_summary: str
    final_answer: object
    confidence: float | None = None

def call_openai(model: str, user_prompt: str, temperature: float = 0.0, max_tokens: int = 300) -> str:
    if OpenAI is None:
        raise RuntimeError("openai パッケージが見つかりません（requirements を確認）。")
    client = OpenAI()
    resp = client.chat.completions.create(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format={"type":"json_object"},
        messages=[
            {"role":"system","content": SYSTEM_PROMPT},
            {"role":"user","content": user_prompt + "\n\n" + JSON_INSTRUCTION}
        ]
    )
    return resp.choices[0].message.content or ""

def main(in_path: str, out_path: str, model: str | None = None):
    load_dotenv()
    with open("configs/settings.json","r",encoding="utf-8") as f:
        cfg = json.load(f)
    model = model or cfg.get("model_name","gpt-4o")
    temperature = cfg.get("temperature", 0.0)
    max_tokens = cfg.get("max_tokens", 300)
    retry_times = int(cfg.get("retry_times", 1))

    # Check API key
    has_key = bool(os.environ.get("OPENAI_API_KEY"))
    if not has_key:
        print("[yellow]OPENAI_API_KEY が未設定のため DRY-RUN モードで動作します（ダミー出力）。[/yellow]")

    inputs = [json.loads(line) for line in open(in_path,"r",encoding="utf-8") if line.strip()]
    results = []
    for ex in track(inputs, description="Running..."):
        t0 = time.time()
        raw_text = ""
        if has_key:
            # Real call with light retry
            err = None
            for _ in range(max(1, retry_times)):
                try:
                    raw_text = call_openai(model, ex["prompt"], temperature, max_tokens)
                    break
                except Exception as e:
                    err = e
                    time.sleep(0.5)
            if raw_text == "" and err is not None:
                raw_text = json.dumps({"error": str(err)}, ensure_ascii=False)
        else:
            # DRY-RUN: produce a minimal plausible JSON
            if "足す" in ex["prompt"] and "3" in ex["prompt"] and "4" in ex["prompt"]:
                raw_text = json.dumps({"key_step_summary":"加法の基本。3と4の合計は7。","final_answer":7,"confidence":0.9}, ensure_ascii=False)
            else:
                raw_text = json.dumps({"key_step_summary":"前提関係から推論。","final_answer":"Yes","confidence":0.7}, ensure_ascii=False)
        latency_ms = int((time.time() - t0)*1000)

        parsed = None
        parse_error = None
        try:
            parsed = ModelOut.model_validate_json(raw_text).model_dump()
        except ValidationError as e:
            parse_error = str(e)

        results.append({
            "sample_id": ex.get("id"),
            "prompt": ex.get("prompt"),
            "model": model,
            "raw_text": raw_text,
            "parsed": parsed,
            "parse_error": parse_error,
            "latency_ms": latency_ms
        })

    with open(out_path,"w",encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"[green]Wrote {out_path}[/green]")

if __name__ == "__main__":
    # Minimal CLI: python scripts/run_eval.py data/dev.jsonl runs/dev_raw.jsonl
    in_path = sys.argv[1] if len(sys.argv)>1 else "data/dev.jsonl"
    out_path = sys.argv[2] if len(sys.argv)>2 else "runs/dev_raw.jsonl"
    model = sys.argv[3] if len(sys.argv)>3 else None
    main(in_path, out_path, model)
