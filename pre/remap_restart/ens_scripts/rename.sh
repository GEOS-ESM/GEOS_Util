#!/bin/bash
set -euo pipefail

# ===== CONFIGURE =====
# Base directory
ROOT="/discover/nobackup/projects/gmao/obsdev/eyang2/PBLH/Exp/pblhl/atmens"
# Text to replace
FROM="f5295_fp"
TO="pblhl"
# Preview mode (1 = show only, 0 = actually rename)
DRY_RUN=0
# =====================

# escape slashes and ampersands for safe substitution in regex/commands
esc_from=$(printf '%s' "$FROM" | sed 's/[\/&]/\\&/g')
esc_to=$(printf '%s' "$TO"   | sed 's/[\/&]/\\&/g')

# detect rename variant: try --version output, fallback to --help
REN_TYPE=""
if command -v rename >/dev/null 2>&1; then
  ver_out=$(rename --version 2>&1 || true)
  if printf '%s' "$ver_out" | tr '[:upper:]' '[:lower:]' | grep -q 'util-linux'; then
    REN_TYPE="util"
  else
    # assume perl-style if not reporting util-linux
    REN_TYPE="perl"
  fi
else
  echo "ERROR: 'rename' command not found in PATH." >&2
  exit 2
fi

echo "Detected rename type: $REN_TYPE"
echo "Searching under: $ROOT for files matching '*$FROM*'"
echo "Dry-run: $DRY_RUN"
echo

# find files and call rename individually
find "$ROOT" -type f -name "*$FROM*" -print0 |
while IFS= read -r -d '' file; do
  if [[ "$REN_TYPE" == "perl" ]]; then
    # perl rename uses a perl substitution script: s/from/to/g
    if [[ $DRY_RUN -eq 1 ]]; then
      echo "PREVIEW: rename -n 's/${esc_from}/${esc_to}/g' -- \"$file\""
    else
      rename "s/${esc_from}/${esc_to}/g" -- "$file" && \
        echo "RENAMED: $file"
    fi
  else
    # util-linux rename uses: rename from to file...
    if [[ $DRY_RUN -eq 1 ]]; then
      echo "PREVIEW: rename \"$FROM\" \"$TO\" -- \"$file\""
    else
      rename "$FROM" "$TO" -- "$file" && \
        echo "RENAMED: $file"
    fi
  fi
done

