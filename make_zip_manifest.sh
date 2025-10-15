#!/usr/bin/env bash
set -Eeuo pipefail

ZIP="${1:?Usage: make_zip_manifest.sh <zip_path> [out_manifest_path] [max_bytes_per_file] }"
OUT="${2:-zip_manifest.md}"
MAX="${3:-51200}"   # 1ファイルあたり最大 50KB

# 収集対象の拡張子（必要に応じて追加）
INCLUDE_EXT='md|txt|csv|tsv|json|yaml|yml|py|sh|js|ts|tsx|jsx|java|kt|go|rb|php|rs|c|h|cpp|hpp|cs|swift|sql|ini|cfg|toml|makefile|dockerfile|env|log'

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

unzip -qq "$ZIP" -d "$WORK"

{
  echo "# ZIP Manifest"
  echo
  echo "- Source ZIP: $(basename "$ZIP")"
  echo "- Generated at: $(date -Iseconds)"
  echo "- Max bytes per file: $MAX"
} > "$OUT"

find "$WORK" -type f | while read -r f; do
  rel="${f#$WORK/}"
  lower="$(echo "$rel" | tr '[:upper:]' '[:lower:]')"

  case "$lower" in
    *.*) ext="${lower##*.}" ;;
    dockerfile|makefile|license|readme) ext="$lower" ;;
    *) ext="" ;;
  esac

  # 拡張子フィルタに合わなければスキップ
  if [ -n "$ext" ] && ! echo "$ext" | grep -Eq "^(($INCLUDE_EXT))$"; then
    continue
  fi

  # バイナリっぽいファイルは除外（NUL含むかで簡易判定）
  if LC_ALL=C grep -Iq . "$f"; then
    echo -e "\n\n---\n# FILE: $rel\n\`\`\`\n" >> "$OUT"
    head -c "$MAX" "$f" >> "$OUT"
    echo -e "\n\`\`\`" >> "$OUT"
  fi
done

echo "[OK] Manifest: $OUT"
