import os, sys, json, re, argparse, random, time
from pathlib import Path
from typing import Dict, Any, List, Tuple
from collections import deque
from openai import OpenAI

LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# ---------------- Rate limiter (RPM) ----------------
class RateLimiter:
    def __init__(self, rpm: int = 3):
        self.rpm = max(1, int(rpm))
        self.events = deque()

    def wait(self):
        now = time.time()
        window = 60.0
        while self.events and (now - self.events[0]) > window:
            self.events.popleft()
        if len(self.events) >= self.rpm:
            sleep_s = window - (now - self.events[0]) + 0.05
            time.sleep(max(0.0, sleep_s))
        self.events.append(time.time())

# ---------------- IO helpers ----------------
def load_jsonl(p: Path) -> List[Dict[str, Any]]:
    items=[]
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line: items.append(json.loads(line))
    return items

def dump_jsonl(rows: List[Dict[str, Any]], p: Path):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False)+"\n")

# ---------------- parsing ----------------
def stem_from_example(ex: Dict[str,Any]) -> str:
    if isinstance(ex.get("input"), list):
        for t in ex["input"]:
            if t.get("role")=="user":
                u = t.get("content") or ""
                m = re.split(r"\n\s*Choices:\s*", u, maxsplit=1)
                return (m[0] if m else u).strip()
    return (ex.get("question") or ex.get("stem") or ex.get("input") or "").strip()

def choices_from_example(ex: Dict[str,Any]) -> List[str]:
    ch = ex.get("choices")
    if isinstance(ch, list) and len(ch)>=2:
        return [str(c) for c in ch][:10]
    # Fallback: 2択 yes/no
    return ["yes","no"]

# ---------------- extraction (robust) ----------------
def extract_letter_strict(raw: str, k: int) -> str:
    if not raw: return ""
    t = (raw or "").strip().upper()
    # 厳格 1文字
    m = re.fullmatch(r"\s*([A-Z])[\.\s]*\s*", t)
    if m:
        c = m.group(1)
        return c if c in LETTERS[:k] else ""
    # 寛容: 文中の最初の A.. を拾う
    m2 = re.search(r"[A-Z]", t)
    if m2:
        c = m2.group(0)
        return c if c in LETTERS[:k] else ""
    return ""

# ---------------- prompting ----------------
def build_messages_k(stem: str, choices: List[str], perm: List[int]) -> Tuple[List[Dict[str,str]], str]:
    k = len(choices)
    valid = "".join([chr(ord('A')+i) for i in range(k)])
    system = (f"Answer with EXACTLY ONE uppercase letter from this set: {','.join(list(valid))}. "
              "No words, no punctuation, no spaces, no quotes, no explanations.")
    disp = stem + "\n\nChoices:\n" + "\n".join(
        f"{chr(ord('A')+i)}. {choices[perm[i]]}" for i in range(k)
    ) + f"\n\nReturn only one letter from [{valid}] and nothing else."
    # few-shot（A/B が均等になる2本）
    shots = [
        {"role":"user","content":"2 is an even number.\n\nChoices:\nA. yes\nB. no\n\nReturn only one letter from [AB] and nothing else."},
        {"role":"assistant","content":"A"},
        {"role":"user","content":"9 is an even number.\n\nChoices:\nA. yes\nB. no\n\nReturn only one letter from [AB] and nothing else."},
        {"role":"assistant","content":"B"},
    ]
    return [{"role":"system","content":system}, *shots, {"role":"user","content":disp}], valid

def unpermute(letter: str, perm: List[int]) -> str:
    if not letter: return ""
    i = ord(letter)-ord('A')
    return chr(ord('A') + perm[i]) if 0 <= i < len(perm) else ""

# ---------------- API call with limiter & backoff ----------------
def ask_once(client: OpenAI, model: str, messages: List[Dict[str,str]], max_tokens: int, temperature: float,
             limiter: RateLimiter, retries: int = 5) -> str:
    for t in range(retries):
        try:
            limiter.wait()
            r = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                top_p=1.0,
                max_completion_tokens=max_tokens,
                stop=["\n"],
            )
            return (r.choices[0].message.content or "").strip()
        except Exception as e:
            msg = str(e).lower()
            if "rate limit" in msg or "429" in msg:
                back = (2 ** t) + random.random()  # 指数バックオフ + ジッタ
                time.sleep(back)
                continue
            return f"[error:{e}]"
    return "[error:giveup_after_retries]"

# ---------------- predict (k 択, 置換 × tries の投票) ----------------
def predict_k(client: OpenAI, model: str, stem: str, choices: List[str], tries: int, temperature: float, limiter: RateLimiter) -> Tuple[str, Dict[str,Any]]:
    k = max(2, min(len(choices), 10))
    votes, raws, perms = [], [], []
    for _ in range(tries):
        perm = list(range(k))
        random.shuffle(perm)
        msgs, valid = build_messages_k(stem, choices, perm)
        raw = ask_once(client, model, msgs, max_tokens=2, temperature=temperature, limiter=limiter)
        p = extract_letter_strict(raw, k)
        p_orig = unpermute(p, perm)
        raws.append(raw); perms.append(perm)
        if p_orig: votes.append(p_orig)

    # 多数決（同数なら最初の票）／票ゼロは無作為フォールバック
    if votes:
        best = max(set(votes), key=votes.count)
        final = best
    else:
        valid_letters = LETTERS[:k]
        final = random.choice(list(valid_letters))

    dbg = {"raws": raws, "perms": perms, "votes": votes}
    return final, dbg

# ---------------- main ----------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("infile")
    ap.add_argument("outfile")
    ap.add_argument("--model", default=os.environ.get("LB_MODEL","gpt-4o-mini"))
    ap.add_argument("--temp", type=float, default=float(os.environ.get("LB_TEMP","0.0")))
    ap.add_argument("--tries", type=int, default=int(os.environ.get("LB_TRIES","3")))
    ap.add_argument("--sleep", type=float, default=float(os.environ.get("LB_SLEEP","0.0")))
    ap.add_argument("--seed", type=int, default=int(os.environ.get("LB_SEED","0")))
    args = ap.parse_args()

    random.seed(args.seed)

    in_p  = Path(args.infile); out_p = Path(args.outfile)
    items = load_jsonl(in_p)

    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        print("OPENAI_API_KEY not set", file=sys.stderr); sys.exit(2)
    client = OpenAI(api_key=key)

    rpm = int(os.environ.get('LB_RPM', '3'))  # 組織の上限に合わせる
    limiter = RateLimiter(rpm=rpm)

    outputs=[]
    for idx, ex in enumerate(items, 1):
        stem    = stem_from_example(ex)
        choices = choices_from_example(ex)
        pred, dbg = predict_k(client, args.model, stem, choices, tries=args.tries, temperature=args.temp, limiter=limiter)
        outputs.append({"id": ex.get("id"), "prediction": pred, "debug": dbg})
        print(f"[{idx}/{len(items)}] {ex.get('id')} -> {pred}  (k={len(choices)})")
        if args.sleep > 0:
            time.sleep(args.sleep)

    dump_jsonl(outputs, out_p)
    print("wrote:", out_p)

if __name__ == "__main__":
    main()
