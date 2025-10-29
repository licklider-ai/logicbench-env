from openai import OpenAI
import os, re, json

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
    text  = (resp.choices[0].message.content or "").strip()
    usage = getattr(resp, "usage", None) or {}

    m = re.search(r'^\s*Answer:\s*(A|B|C|D|YES|NO)\s*$', text, re.I)
    if m:
        token = m.group(1).upper()
    else:
        m2 = re.search(r'\b(A|B|C|D|YES|NO)\b', text.upper())
        token = m2.group(1) if m2 else "A"
    return f"Answer: {token}", usage

if __name__ == "__main__":
    client = OpenAI()
    model_name = os.environ["LB_MODEL"]
    user_prompt = "Question: Which number is even?\nA) 3\nB) 8\nC) 9\nD) 11"
    pred_text, usage = call_single_token_answer(client, model_name, user_prompt)
    print(pred_text)
