#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-$ROOT_DIR/.env}"

load_env_file() {
  local env_file="$1"
  if [[ ! -f "$env_file" ]]; then
    return
  fi

  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%$'\r'}"
    [[ -z "$line" ]] && continue
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ "$line" != *=* ]] && continue

    local key="${line%%=*}"
    local value="${line#*=}"

    key="${key#"${key%%[![:space:]]*}"}"
    key="${key%"${key##*[![:space:]]}"}"
    value="${value#"${value%%[![:space:]]*}"}"
    value="${value%"${value##*[![:space:]]}"}"

    if [[ "$value" =~ ^\".*\"$ || "$value" =~ ^\'.*\'$ ]]; then
      value="${value:1:${#value}-2}"
    fi

    if [[ -z "${!key+x}" ]]; then
      export "$key=$value"
    fi
  done < "$env_file"
}

load_env_file "$ENV_FILE"

SOURCE_DIR="${SOURCE_DIR:-$ROOT_DIR}"
OUTPUT_DIR="${OUTPUT_DIR:-$ROOT_DIR/dist}"
CACHE_DIR="${CACHE_DIR:-$ROOT_DIR/.cache/build_appstore}"
IMAGE_SIZE_CACHE_FILE="${IMAGE_SIZE_CACHE_FILE:-$CACHE_DIR/image-size-cache.json}"
IMAGE_DIGEST_CACHE_FILE="${IMAGE_DIGEST_CACHE_FILE:-$CACHE_DIR/image-digest-cache.json}"
BASE_URL="${BASE_URL:-}"

mkdir -p "$CACHE_DIR"

CMD=(
  python3
  "$ROOT_DIR/scripts/build_appstore.py"
  --source "$SOURCE_DIR"
  --output "$OUTPUT_DIR"
  --cache-file "$IMAGE_SIZE_CACHE_FILE"
  --digest-cache-file "$IMAGE_DIGEST_CACHE_FILE"
)

if [[ -n "$BASE_URL" ]]; then
  CMD+=(--base-url "$BASE_URL")
fi

CMD+=("$@")

echo "Building appstore dist"
echo "  source: $SOURCE_DIR"
echo "  output: $OUTPUT_DIR"
if [[ -f "$ENV_FILE" ]]; then
  echo "  env file: $ENV_FILE"
else
  echo "  env file: (not found)"
fi
echo "  image size cache: $IMAGE_SIZE_CACHE_FILE"
echo "  image digest cache: $IMAGE_DIGEST_CACHE_FILE"
if [[ -n "$BASE_URL" ]]; then
  echo "  base url: $BASE_URL"
else
  echo "  base url: (relative paths)"
fi
if [[ -n "${DOCKERHUB_USERNAME:-}" && -n "${DOCKERHUB_TOKEN:-}" ]]; then
  echo "  docker hub auth: enabled for user $DOCKERHUB_USERNAME"
else
  echo "  docker hub auth: disabled"
fi

exec "${CMD[@]}"
