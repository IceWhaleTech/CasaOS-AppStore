#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-$ROOT_DIR/.env}"
ACTION_REPO="${ACTION_REPO:-IceWhaleTech/build-appstore-action}"
ACTION_REF="${ACTION_REF:-v1}"
ACTION_RAW_BASE="${ACTION_RAW_BASE:-https://raw.githubusercontent.com/$ACTION_REPO/$ACTION_REF}"

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

normalize_base_url() {
  local raw_base_url="${1:-}"
  local source_dir="${2:-$ROOT_DIR}"
  local base_url=""

  case "$raw_base_url" in
    \[*\]\(http://*\)|\[*\]\(https://*\))
      local link_label="${raw_base_url%%]*}"
      local link_target="${raw_base_url##*\(}"
      link_label="${link_label#[}"
      link_target="${link_target%\)}"
      if [[ "$link_label" == http://* || "$link_label" == https://* ]]; then
        base_url="$link_label"
      else
        base_url="$link_target"
      fi
      ;;
    *)
      base_url="$raw_base_url"
      ;;
  esac

  if [[ -z "$base_url" ]]; then
    local repo_url=""
    repo_url="$(git -C "$source_dir" config --get remote.origin.url || true)"
    if [[ "$repo_url" =~ ^https://github.com/([^/]+)/([^/.]+)(\.git)?$ ]]; then
      base_url="https://cdn.jsdelivr.net/gh/${BASH_REMATCH[1]}/${BASH_REMATCH[2]}@gh-pages"
    elif [[ "$repo_url" =~ ^git@github.com:([^/]+)/([^/.]+)(\.git)?$ ]]; then
      base_url="https://cdn.jsdelivr.net/gh/${BASH_REMATCH[1]}/${BASH_REMATCH[2]}@gh-pages"
    fi
  fi

  if [[ -n "$base_url" ]] && [[ ! "$base_url" =~ ^https?://[^[:space:]]+$ ]]; then
    echo "Invalid BASE_URL: $raw_base_url" >&2
    exit 1
  fi

  printf '%s\n' "$base_url"
}

SOURCE_DIR="${SOURCE_DIR:-$ROOT_DIR}"
OUTPUT_DIR="${OUTPUT_DIR:-$ROOT_DIR/dist}"
CACHE_DIR="${CACHE_DIR:-$ROOT_DIR/.cache/build_appstore}"
IMAGE_SIZE_CACHE_FILE="${IMAGE_SIZE_CACHE_FILE:-$CACHE_DIR/image-size-cache.json}"
IMAGE_DIGEST_CACHE_FILE="${IMAGE_DIGEST_CACHE_FILE:-$CACHE_DIR/image-digest-cache.json}"
BASE_URL="$(normalize_base_url "${BASE_URL:-}" "$SOURCE_DIR")"
REMOTE_BUILD_DIR="$(mktemp -d "${TMPDIR:-/tmp}/build-appstore-action.XXXXXX")"

cleanup() {
  rm -rf "$REMOTE_BUILD_DIR"
}

trap cleanup EXIT

mkdir -p "$CACHE_DIR"

fetch_remote_file() {
  local relative_path="$1"
  local destination="$2"
  curl -fsSL "$ACTION_RAW_BASE/$relative_path" -o "$destination"
}

fetch_remote_file "scripts/build_appstore.py" "$REMOTE_BUILD_DIR/build_appstore.py"
fetch_remote_file "requirements.txt" "$REMOTE_BUILD_DIR/requirements.txt"

python3 -m pip install -r "$REMOTE_BUILD_DIR/requirements.txt"

CMD=(
  python3
  "$REMOTE_BUILD_DIR/build_appstore.py"
  --source "$SOURCE_DIR"
  --output "$OUTPUT_DIR"
  --cache-file "$IMAGE_SIZE_CACHE_FILE"
  --digest-cache-file "$IMAGE_DIGEST_CACHE_FILE"
)

CMD+=(--base-url "$BASE_URL")

CMD+=("$@")

echo "Building appstore dist"
echo "  source: $SOURCE_DIR"
echo "  output: $OUTPUT_DIR"
echo "  action repo: $ACTION_REPO"
echo "  action ref: $ACTION_REF"
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
