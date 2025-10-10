import os
from openai import OpenAI

assert os.getenv("OPENAI_API_KEY"), "Set OPENAI_API_KEY first!"
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

stem = "What is 1+1?"
choices = ["1","2","3","4"]
LETTERS = "ABCD"
valid = LETTERS[:len(choices)]

system = (
    f"Answer with EXACTLY ONE uppercase letter from this set: {','.join(valid)}. "
    "No words, no punctuation, no spaces, no quotes, no explanation."
)
user = (
    stem + "\n\nChoices:\n" +
    "\n".join(f"{LETTERS[i]}. {c}" for i,c in enumerate(choices)) +
    f"\n\nReturn only one letter from [{valid}] and nothing else."
)

resp = client.chat.completions.create(
    model=os.getenv("LB_MODEL","gpt-4o-mini"),
    messages=[{"role":"system","content":system},{"role":"user","content":user}],
    temperature=0.0,
    max_completion_tokens=16,
    stop=["\n"],
)
print("RAW:", resp.choices[0].message.content)
