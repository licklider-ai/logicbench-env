You must output exactly one token from {A,B,C,D}. No words, spaces, or punctuation.

Decision rubric (avoid over-predicting A):
- Prefer D over A when evidence is incomplete, contradictory, or the question contains negations/exception phrases.
- Choose C only when a specific condition matches precisely; otherwise consider D.
- Choose B when two candidates are plausible but one has a clear factual/data support.
- Choose A only when the statement is explicitly, unambiguously satisfied by the passage/facts.

Hard negatives (few-shot):
Q: The rule applies unless X occurs, and X occurs. -> A?  
A: D

Q: Two options fit, but only one matches the numeric threshold exactly. -> A?  
A: B

Q: Condition seems likely but is not stated and no proxy evidence exists. -> A?  
A: D

Q: Choice C looks similar in wording but mismatches the required scope. -> A?  
A: C
