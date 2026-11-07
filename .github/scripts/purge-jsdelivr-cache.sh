#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: purge-jsdelivr-cache.sh --repository OWNER/REPOSITORY --ref REF --paths-file FILE
USAGE
}

REPOSITORY=""
REF=""
PATHS_FILE=""
MAX_ATTEMPTS="${PURGE_MAX_ATTEMPTS:-5}"
BATCH_SIZE="${PURGE_BATCH_SIZE:-100}"

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
if [[ ! "$BATCH_SIZE" =~ ^[1-9][0-9]*$ || ! "$MAX_ATTEMPTS" =~ ^[1-9][0-9]*$ ]]; then
  echo "PURGE_BATCH_SIZE and PURGE_MAX_ATTEMPTS must be positive integers" >&2
  exit 2
fi

purge_batch() {
  local batch_file="$1"
  local attempt http_code response status throttled reset delay purge_id poll_response poll_code
  local paths_json payload

  paths_json="$(sed "s#^#/gh/${REPOSITORY}@${REF}/#" "$batch_file" | jq -R -s 'split("\n") | map(select(length > 0))')"
  payload="$(jq -cn --argjson paths "$paths_json" '{path: $paths}')"

  for ((attempt = 1; attempt <= MAX_ATTEMPTS; attempt++)); do
    response="$(mktemp)"
    if http_code="$(curl -sS --connect-timeout 10 --max-time 60 -X POST \
      -H 'content-type: application/json' --data "$payload" \
      -o "$response" -w '%{http_code}' 'https://purge.jsdelivr.net/')"; then
      status="$(jq -r '.status // empty' "$response" 2>/dev/null || true)"
      throttled="$(jq -r '[.paths[]?.throttled] | any' "$response" 2>/dev/null || printf 'true')"
      purge_id="$(jq -r '.id // empty' "$response" 2>/dev/null || true)"

      if [[ "$http_code" =~ ^2[0-9][0-9]$ && "$status" == "pending" && -n "$purge_id" ]]; then
        for ((poll = 1; poll <= 30; poll++)); do
          sleep 1
          poll_response="$(mktemp)"
          if poll_code="$(curl -sS --connect-timeout 10 --max-time 60 -o "$poll_response" -w '%{http_code}' "https://purge.jsdelivr.net/status/${purge_id}")"; then
            response="$poll_response"
            http_code="$poll_code"
            status="$(jq -r '.status // empty' "$response" 2>/dev/null || true)"
            throttled="$(jq -r '[.paths[]?.throttled] | any' "$response" 2>/dev/null || printf 'true')"
            if [[ "$status" == "finished" ]]; then
              break
            fi
          fi
        done
      fi

      if [[ "$http_code" =~ ^2[0-9][0-9]$ && "$status" == "finished" && "$throttled" != "true" ]]; then
        rm -f "$response"
        echo "Purged $(wc -l < "$batch_file" | tr -d ' ') path(s)"
        return 0
      fi

      if [[ "$throttled" == "true" ]]; then
        reset="$(jq -r '[.paths[]?.throttlingReset // 0] | max' "$response" 2>/dev/null || printf 'unknown')"
        echo "jsDelivr purge rate limit reached; retry after ${reset}s" >&2
        sed -n '1,80p' "$response" >&2 || true
        rm -f "$response"
        return 1
      fi
    else
      http_code="000"
    fi

    if (( attempt == MAX_ATTEMPTS )); then
      echo "Failed to purge batch (HTTP $http_code, status=${status:-unknown})" >&2
      sed -n '1,40p' "$response" >&2 || true
      rm -f "$response"
      return 1
    fi

    delay=$((2 ** (attempt - 1)))
    if (( delay > 30 )); then delay=30; fi
    echo "Retrying purge batch in ${delay}s (HTTP $http_code, status=${status:-unknown})" >&2
    rm -f "$response"
    sleep "$delay"
  done
}

path_count="$(awk 'NF { count++ } END { print count + 0 }' "$PATHS_FILE")"
if (( path_count == 0 )); then
  echo "No paths to purge"
  exit 0
fi
echo "Purging $path_count jsDelivr path(s) in batches of $BATCH_SIZE"

batch_dir="$(mktemp -d)"
trap 'rm -rf "$batch_dir"' EXIT
sort -u "$PATHS_FILE" | split -l "$BATCH_SIZE" - "$batch_dir/batch-"
for batch_file in "$batch_dir"/batch-*; do
  purge_batch "$batch_file"
done
