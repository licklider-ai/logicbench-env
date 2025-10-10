#!/bin/bash
set -euo pipefail

# 入力
read -s -p "Enter OpenAI Project key (sk-proj-...): " OPENAI_API_KEY; echo
read -p "Enter OpenAI Project ID (starts with prj_): " OPENAI_PROJECT

# 入力検証
if [[ ! "$OPENAI_PROJECT" =~ ^prj_ ]]; then
  echo "Error: Project ID must start with prj_. You entered: $OPENAI_PROJECT"
  exit 1
fi

# 実行
export OPENAI_API_KEY OPENAI_PROJECT
echo "Project: $OPENAI_PROJECT"
python -u scripts/eval_runner.py data/dev_20.jsonl runs/pred_20251008_proj.jsonl --retries 5 --base_delay 8 --max_delay 60

# 片付け
unset OPENAI_API_KEY OPENAI_PROJECT
