import re

LETTERS = "ABCD"

def to_label(text: str, choices: list[str]) -> str:
    """自由文 text を choices に対する A–D ラベルへ正規化。失敗時は '' を返す。"""
    if not text or not choices:
        return ""
    s  = str(text).strip()
    up = s.upper()
    lm = {LETTERS[i]: c for i, c in enumerate(choices) if i < 4}

    # 1) 直接 A–D を拾う（最優先）
    for pat in (r'\b([A-D])\b',
                r'(?:ANSWER|OPTION|FINAL)\s*[:=]?\s*\(?([A-D])\)?'):
        m = re.search(pat, up)
        if m and m.group(1) in lm:
            return m.group(1)

    # 2) Yes/No を 2 択にマップ（A/ B）
    if len(choices) >= 2:
        if up in {"YES","Y","TRUE","T"}:  return "A"
        if up in {"NO","N","FALSE","F"}:  return "B"

    # 3) 選択肢本文の包含でマップ（大小無視）
    sl = s.lower()
    for L, c in lm.items():
        if str(c).strip().lower() in sl:
            return L

    # 4) 数値近似（出力と選択肢の数値が近いものを選ぶ）
    def nums(t: str):
        return [float(x.replace(',', '')) for x in re.findall(r'-?\d+(?:\.\d+)?', str(t))]
    cand = []
    for L, c in lm.items():
        nn = nums(c)
        if nn:
            cand.append((L, nn[0]))
    outn = nums(s)
    if cand and outn:
        v = outn[0]
        try:
            return min(cand, key=lambda t: abs(t[1] - v))[0]
        except Exception:
            pass

    return ""
