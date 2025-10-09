import re, unicodedata

_PUNCT = r"[ \t\r\n\f\v\.\,;:!?\)\]\}、。・】）」』]*"
_INNER_TOKEN = re.compile(r"(?<![A-Z])([ABCD])(?![A-Z])")

def extract_letter_strict(s: str) -> str:
    """
    モデル出力から {A,B,C,D} を頑強に抽出。失敗時は 'NONE'。
    優先順位:
      1) 完全一致
      2) 末尾の句読点/空白を許容 ("C.", "A)" など)
      3) 文中の単独トークン ("the answer is C.")
      4) NONE
    """
    if s is None:
        return "NONE"
    t = unicodedata.normalize("NFKC", str(s)).strip().upper()

    # 1) 完全一致
    if re.fullmatch(r"[ABCD]", t):
        return t

    # 2) 末尾の句読点/空白のみ付与
    m = re.fullmatch(rf"([ABCD]){_PUNCT}", t)
    if m:
        return m.group(1)

    # 先頭ラベル "A)" "B." "C :" など
    m = re.match(rf"^\s*([ABCD]){_PUNCT}", t)
    if m:
        return m.group(1)

    # 3) 文中の単独トークン
    m = _INNER_TOKEN.search(t)
    if m:
        return m.group(1)

    return "NONE"
