#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SETTINGS_FILE="${SETTINGS_FILE:-$SCRIPT_DIR/.settings.env}"

load_env_file() {
  local env_file="$1"

  if [[ ! -f "$env_file" ]]; then
    echo "Missing env file: $env_file" >&2
    exit 1
  fi

  set -a
  # shellcheck source=/dev/null
  source "$env_file"
  set +a
}

resolve_path() {
  local value="$1"

  if [[ "$value" = /* ]]; then
    printf '%s\n' "$value"
  else
    printf '%s/%s\n' "$SCRIPT_DIR" "$value"
  fi
}

load_env_file "$SETTINGS_FILE"

if [[ -z "${ENV_FILE:-}" ]]; then
  echo "Missing required variable in $SETTINGS_FILE: ENV_FILE" >&2
  exit 1
fi

ENV_FILE="$(resolve_path "$ENV_FILE")"
export ENV_FILE

load_env_file "$ENV_FILE"

if [[ -n "${PYTHON_BIN:-}" ]]; then
  python_bin="$PYTHON_BIN"
elif command -v python3 >/dev/null 2>&1; then
  python_bin="python3"
else
  python_bin="python"
fi

cd "$SCRIPT_DIR"
exec "$python_bin" "$SCRIPT_DIR/deploy.py" "$@"
