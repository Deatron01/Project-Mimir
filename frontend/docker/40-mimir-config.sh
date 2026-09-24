#!/bin/sh
# Writes /config.json from environment variables at container start (FE-03), so one image can run against
# any backend. Variables that are not set keep the values baked in at build time.
set -eu
OUT=/usr/share/nginx/html/config.json

esc() { printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'; }

fields=""
add() { # name value is_bool
  [ -z "$2" ] && return 0
  if [ "$3" = "bool" ]; then v="$2"; else v="\"$(esc "$2")\""; fi
  fields="${fields}${fields:+,}\"$1\":$v"
}
add apiBaseUrl "${MIMIR_API_BASE_URL:-}" str
add apiMode "${MIMIR_API_MODE:-}" str
case "${MIMIR_USE_MOCKS:-}" in true|false) add useMocks "$MIMIR_USE_MOCKS" bool ;; "") ;; *) echo "MIMIR_USE_MOCKS must be true or false" >&2; exit 1 ;; esac
add privacyEmail "${MIMIR_PRIVACY_EMAIL:-}" str

if [ -n "$fields" ]; then
  printf '{%s}\n' "$fields" > "$OUT"
  echo "mimir: wrote $OUT"
else
  rm -f "$OUT"
fi
