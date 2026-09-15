#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: verify-jsdelivr-cache.sh --repository OWNER/REPOSITORY --ref REF --paths-file FILE
USAGE
}

REPOSITORY=""
REF=""
PATHS_FILE=""
MAX_ATTEMPTS="${VERIFY_MAX_ATTEMPTS:-3}"
RETRY_DELAY="${VERIFY_RETRY_DELAY:-5}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repository)
      REPOSITORY="$2"
      shift 2
      ;;
    --ref)
      REF="$2"
      shift 2
      ;;
    --paths-file)
      PATHS_FILE="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$REPOSITORY" || -z "$REF" || -z "$PATHS_FILE" ]]; then
  usage >&2
  exit 2
fi
if [[ ! -f "$PATHS_FILE" ]]; then
  echo "Paths file does not exist: $PATHS_FILE" >&2
  exit 2
fi
if [[ ! "$MAX_ATTEMPTS" =~ ^[1-9][0-9]*$ || ! "$RETRY_DELAY" =~ ^[1-9][0-9]*$ ]]; then
  echo "VERIFY_MAX_ATTEMPTS and VERIFY_RETRY_DELAY must be positive integers" >&2
  exit 2
fi

verify_path() {
  local path="$1"
  local raw_url="https://raw.githubusercontent.com/${REPOSITORY}/${REF}/${path}"
  local cdn_url="https://cdn.jsdelivr.net/gh/${REPOSITORY}@${REF}/${path}"
  local attempt raw_file cdn_file raw_code cdn_code raw_hash cdn_hash

  for ((attempt = 1; attempt <= MAX_ATTEMPTS; attempt++)); do
    raw_file="$(mktemp)"
    cdn_file="$(mktemp)"
    raw_code="$(curl -sS --connect-timeout 10 --max-time 60 -o "$raw_file" -w '%{http_code}' "$raw_url" || printf '000')"
    cdn_code="$(curl -sS --connect-timeout 10 --max-time 60 -o "$cdn_file" -w '%{http_code}' "$cdn_url" || printf '000')"

    if [[ "$raw_code" == "$cdn_code" && "$raw_code" =~ ^2[0-9][0-9]$ ]]; then
      raw_hash="$(shasum -a 256 "$raw_file" | awk '{print $1}')"
      cdn_hash="$(shasum -a 256 "$cdn_file" | awk '{print $1}')"
      if [[ "$raw_hash" == "$cdn_hash" ]]; then
        rm -f "$raw_file" "$cdn_file"
        echo "Verified $path"
        return 0
      fi
    elif [[ "$raw_code" == "$cdn_code" && "$raw_code" =~ ^4[0-9][0-9]$ ]]; then
      rm -f "$raw_file" "$cdn_file"
      echo "Verified unavailable $path"
      return 0
    fi

    if (( attempt == MAX_ATTEMPTS )); then
      echo "CDN content mismatch for $path (source HTTP $raw_code, CDN HTTP $cdn_code)" >&2
      if [[ "$raw_code" =~ ^2[0-9][0-9]$ && "$cdn_code" =~ ^2[0-9][0-9]$ ]]; then
        echo "source sha256=$raw_hash CDN sha256=$cdn_hash" >&2
      fi
      rm -f "$raw_file" "$cdn_file"
      return 1
    fi

    echo "Content for $path is not synchronized; retrying in ${RETRY_DELAY}s" >&2
    rm -f "$raw_file" "$cdn_file"
    sleep "$RETRY_DELAY"
  done
}

path_count="$(awk 'NF { count++ } END { print count + 0 }' "$PATHS_FILE")"
if (( path_count == 0 )); then
  echo "No paths to verify"
  exit 0
fi
echo "Verifying $path_count jsDelivr path(s)"

failed=0
while IFS= read -r path; do
  [[ -z "$path" ]] && continue
  if ! verify_path "$path"; then
    failed=1
  fi
done < <(sort -u "$PATHS_FILE")

if (( failed != 0 )); then
  echo "One or more jsDelivr paths are not synchronized" >&2
  exit 1
fi
