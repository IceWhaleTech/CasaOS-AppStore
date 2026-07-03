#!/usr/bin/env python3
"""
Build script for ZimaOS AppStore online metadata.

Generates a flat output layout:

  dist/
    index.json
    index.{locale}.json            # only when locale is explicitly defined in app i18n
    store.json
    store.{locale}.json            # only when locale is explicitly defined in store i18n
    apps/{app_id}/
      docker-compose.yml
      docker-compose.{architecture}.yml
      meta.json
      meta.{locale}.json           # only when locale is explicitly defined in app i18n
      assets/
        icon.svg
        thumbnail.webp
        screenshot-1.webp
"""

import argparse
import base64
import copy
import hashlib
import json
from json import JSONDecodeError
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

import yaml

try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    print("Warning: Pillow not installed. Image optimization disabled.", file=sys.stderr)


# Fields to keep in docker-compose.yml x-casaos block (runtime essentials)
COMPOSE_KEEP_FIELDS = {
    "id",
    "main",
    "index",
    "port_map",
    "scheme",
    "icon",
    "title",
    "version",
}

# Image file extensions to copy
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}

# Image optimization settings
MAX_IMAGE_WIDTH = 1280
WEBP_QUALITY = 85

# Store config input filename
STORE_CONFIG_FILE = "store-config.json"

# Supported languages config filename
SUPPORTED_LANGUAGES_FILE = "supported-languages.json"

# Default / fallback locale
DEFAULT_LOCALE = "en_US"

# Fields in x-casaos that contain i18n locale dicts
I18N_FIELDS = {"title", "tagline", "description", "release_notes"}
# Fields that contain nested i18n dicts (e.g. tips.before_install)
I18N_NESTED_FIELDS = {"tips"}

# Index-level i18n fields
INDEX_I18N_FIELDS = {"title", "tagline"}

DOCKER_MANIFEST_ACCEPT = ", ".join([
    "application/vnd.oci.image.index.v1+json",
    "application/vnd.docker.distribution.manifest.list.v2+json",
    "application/vnd.oci.image.manifest.v1+json",
    "application/vnd.docker.distribution.manifest.v2+json",
])

IMAGE_SIZE_CACHE = {}
DIGEST_CACHE_ENTRIES = {}
IMAGE_DIGEST_CACHE = {}
REGISTRY_TOKEN_CACHE = {}
RATE_LIMITED_REGISTRIES = {}
RATE_LIMIT_WARNED_REGISTRIES = set()
PENDING_DIGEST_WARNINGS = {}
PENDING_IMAGE_SIZE_WARNINGS = {}
REGISTRY_MANIFEST_CACHE = {}
REGISTRY_CHILD_MANIFEST_CACHE = {}
IMAGE_SIZE_CACHE_FILE = None
DIGEST_CACHE_FILE = None
DOCKERHUB_USERNAME = os.environ.get("DOCKERHUB_USERNAME", "").strip()
DOCKERHUB_TOKEN = os.environ.get("DOCKERHUB_TOKEN", "").strip()
NETWORK_RETRY_ATTEMPTS = 4
NETWORK_RETRYABLE_HTTP_CODES = {408, 425, 429, 500, 502, 503, 504}
SEMVER_PATTERN = re.compile(
    r"^(0|[1-9]\d*)\."
    r"(0|[1-9]\d*)\."
    r"(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)
SAFE_ID_PATTERN = re.compile(
    r"^(?=.*[a-z0-9])[a-z0-9._-]+$"
)
REVERSE_DOMAIN_APP_ID_PATTERN = re.compile(
    r"^(?=.{3,}$)(?=.*[a-z0-9])[a-z0-9_-]+(?:\.[a-z0-9_-]+)+$"
)


class ArchitectureMismatchError(RuntimeError):
    """Raised when an app declares an architecture unsupported by its image."""


def normalize_safe_id(value):
    """Normalize a store/app identifier by trimming whitespace and lowercasing."""
    return str(value or "").strip().lower()


def validate_safe_id(raw_value, field_name, context_label):
    """Validate a safe identifier shared by store_id and x-casaos.id."""
    normalized_value = normalize_safe_id(raw_value)
    if not normalized_value:
        raise ValueError(f"{context_label} is missing required {field_name}.")

    if not SAFE_ID_PATTERN.fullmatch(normalized_value):
        raise ValueError(
            f"{context_label} has invalid {field_name} '{raw_value}'. It may only "
            "contain letters, digits, dots (.), underscores (_), and hyphens (-), "
            "and must include at least one letter or digit."
        )

    return normalized_value


def validate_reverse_domain_app_id(raw_value, context_label):
    """Validate x-casaos.id as a reverse-domain style safe identifier."""
    normalized_value = validate_safe_id(raw_value, "x-casaos.id", context_label)
    if not REVERSE_DOMAIN_APP_ID_PATTERN.fullmatch(normalized_value):
        raise ValueError(
            f"{context_label} has invalid x-casaos.id '{raw_value}'. It must "
            "use reverse-domain style such as 'com.example.myapp', with at least "
            "two non-empty dot-separated segments, using only letters, digits, "
            "dots (.), underscores (_), and hyphens (-)."
        )
    return normalized_value


# ---------------------------------------------------------------------------
# Arguments / utility helpers
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Build ZimaOS AppStore online metadata"
    )
    parser.add_argument(
        "--source",
        default=".",
        help="Source repository root (default: current directory)",
    )
    parser.add_argument(
        "--output",
        default="dist",
        help="Output directory (default: dist)",
    )
    parser.add_argument(
        "--base-url",
        default="",
        help="Base URL prefix for resource links (e.g. https://user.github.io/repo)",
    )
    parser.add_argument(
        "--cache-file",
        default="",
        help="Optional JSON cache file for image metadata (default: <source>/.cache/build_appstore/image-size-cache.json)",
    )
    parser.add_argument(
        "--digest-cache-file",
        default="",
        help="Optional JSON cache file for image digest metadata (default: <source>/.cache/build_appstore/image-digest-cache.json)",
    )
    return parser.parse_args()


def content_hash(*parts):
    """Compute a short SHA-256 hash over multiple content strings/bytes."""
    h = hashlib.sha256()
    for p in parts:
        if isinstance(p, str):
            p = p.encode("utf-8")
        h.update(p)
    return h.hexdigest()[:8]


def registry_request(url, headers=None):
    """Perform an HTTP request with a standard user agent."""
    request_headers = {
        "User-Agent": "ZimaOS-AppStore-Build/1.0",
        "Accept": "*/*",
    }
    if headers:
        request_headers.update(headers)
    request = Request(url, headers=request_headers)
    return urlopen(request, timeout=30)


def is_retryable_network_error(exc):
    """Return True for transient network / registry errors worth retrying."""
    if isinstance(exc, HTTPError):
        return exc.code in NETWORK_RETRYABLE_HTTP_CODES
    if isinstance(exc, URLError):
        return True
    if isinstance(exc, TimeoutError):
        return True
    if isinstance(exc, socket.timeout):
        return True
    if isinstance(exc, ConnectionResetError):
        return True
    return False


def open_url_with_retries(request, timeout=30, attempts=NETWORK_RETRY_ATTEMPTS):
    """Open a URL with simple retry/backoff for transient network failures."""
    last_exc = None
    for attempt in range(1, attempts + 1):
        try:
            return urlopen(request, timeout=timeout)
        except Exception as exc:
            last_exc = exc
            if not is_retryable_network_error(exc) or attempt == attempts:
                raise
            time.sleep(min(8, 2 ** (attempt - 1)))
    raise last_exc


def parse_www_authenticate(header_value):
    """Parse a WWW-Authenticate Bearer challenge header."""
    if not header_value or not header_value.startswith("Bearer "):
        return None
    params_str = header_value[len("Bearer "):]
    matches = re.findall(r'(\w+)="([^"]+)"', params_str)
    return {key: value for key, value in matches}


def get_registry_bearer_token(auth_header):
    """Get a bearer token from a registry auth challenge."""
    params = parse_www_authenticate(auth_header)
    if not params or "realm" not in params:
        raise RuntimeError(f"Unsupported registry auth challenge: {auth_header}")

    query = []
    for key in ("service", "scope"):
        if key in params:
            query.append(f"{key}={params[key]}")
    token_url = params["realm"]
    if query:
        separator = "&" if "?" in token_url else "?"
        token_url = f"{token_url}{separator}{'&'.join(query)}"

    if token_url in REGISTRY_TOKEN_CACHE:
        return REGISTRY_TOKEN_CACHE[token_url]

    request_headers = {
        "User-Agent": "ZimaOS-AppStore-Build/1.0",
        "Accept": "application/json",
    }
    if DOCKERHUB_USERNAME and DOCKERHUB_TOKEN and "auth.docker.io" in token_url:
        credentials = f"{DOCKERHUB_USERNAME}:{DOCKERHUB_TOKEN}".encode("utf-8")
        basic_token = base64.b64encode(credentials).decode("ascii")
        request_headers["Authorization"] = f"Basic {basic_token}"

    request = Request(token_url, headers=request_headers)
    with open_url_with_retries(request, timeout=30) as response:
        body = response.read().decode("utf-8")
    try:
        payload = json.loads(body)
    except JSONDecodeError as exc:
        raise RuntimeError(f"Invalid registry token response: {token_url}") from exc
    token = payload.get("token") or payload.get("access_token")
    if not token:
        raise RuntimeError(f"Registry token response missing token: {token_url}")
    REGISTRY_TOKEN_CACHE[token_url] = token
    return token


def mark_registry_rate_limited(registry, exc):
    """Remember that a registry is rate-limited for the remainder of this run."""
    if registry and registry not in RATE_LIMITED_REGISTRIES:
        RATE_LIMITED_REGISTRIES[registry] = str(exc)


def is_registry_rate_limited_error(exc):
    """Return True when an exception means the registry is currently rate-limited."""
    return "Registry rate limited:" in str(exc)


def warn_registry_rate_limited_once(app_id, registry, image_ref, operation):
    """Emit a single warning per registry when it becomes rate-limited."""
    if not registry or registry in RATE_LIMIT_WARNED_REGISTRIES:
        return
    RATE_LIMIT_WARNED_REGISTRIES.add(registry)
    print(
        f"  WARN  App '{app_id}' {operation} for image '{image_ref}' because "
        f"registry '{registry}' is rate-limited; remaining images from this "
        f"registry will be skipped for this build run."
    )


def record_digest_warning(app_id, service_name, image_ref, architecture, exc):
    """Aggregate digest pinning warnings across architectures."""
    key = (app_id, service_name, image_ref, str(exc))
    PENDING_DIGEST_WARNINGS.setdefault(key, set()).add(architecture)


def record_image_size_warning(app_id, service_name, image_ref, architecture, exc):
    """Aggregate image-size warnings across architectures."""
    key = (app_id, service_name, image_ref, str(exc))
    PENDING_IMAGE_SIZE_WARNINGS.setdefault(key, set()).add(architecture)


def format_architecture_list(architectures):
    """Render a stable architecture list for logs."""
    return ", ".join(sorted(architectures))


def flush_app_warnings(app_id):
    """Emit aggregated warnings for one app and clear them from memory."""
    digest_keys = [key for key in PENDING_DIGEST_WARNINGS if key[0] == app_id]
    for key in sorted(digest_keys):
        _, service_name, image_ref, error_text = key
        architectures = format_architecture_list(PENDING_DIGEST_WARNINGS.pop(key))
        print(
            f"  WARN  App '{app_id}' could not pin image digest for "
            f"service '{service_name}' on architectures [{architectures}]: "
            f"{image_ref} ({error_text})"
        )

    image_size_keys = [key for key in PENDING_IMAGE_SIZE_WARNINGS if key[0] == app_id]
    for key in sorted(image_size_keys):
        _, service_name, image_ref, error_text = key
        architectures = format_architecture_list(PENDING_IMAGE_SIZE_WARNINGS.pop(key))
        print(
            f"  WARN  App '{app_id}' could not estimate image size for "
            f"service '{service_name}' on architectures [{architectures}]: "
            f"{image_ref} ({error_text})"
        )


def registry_json_request(url, headers=None, registry=None):
    """Perform a registry JSON request, retrying with bearer auth if required."""
    if registry and registry in RATE_LIMITED_REGISTRIES:
        raise RuntimeError(
            f"Registry rate limited: {registry} ({RATE_LIMITED_REGISTRIES[registry]})"
        )

    try:
        request_headers = {
            "User-Agent": "ZimaOS-AppStore-Build/1.0",
            "Accept": "*/*",
        }
        if headers:
            request_headers.update(headers)
        request = Request(url, headers=request_headers)
        with open_url_with_retries(request, timeout=30) as response:
            return response.read().decode("utf-8"), response.headers
    except HTTPError as exc:
        if exc.code == 429:
            mark_registry_rate_limited(registry, exc)
            raise RuntimeError(f"Registry rate limited: {registry}") from exc
        if exc.code != 401:
            raise
        token = get_registry_bearer_token(exc.headers.get("WWW-Authenticate"))
        auth_headers = dict(headers or {})
        auth_headers["Authorization"] = f"Bearer {token}"
        request_headers = {
            "User-Agent": "ZimaOS-AppStore-Build/1.0",
            "Accept": "*/*",
        }
        request_headers.update(auth_headers)
        request = Request(url, headers=request_headers)
        try:
            with open_url_with_retries(request, timeout=30) as response:
                return response.read().decode("utf-8"), response.headers
        except HTTPError as auth_exc:
            if auth_exc.code == 429:
                mark_registry_rate_limited(registry, auth_exc)
                raise RuntimeError(f"Registry rate limited: {registry}") from auth_exc
            raise


def load_digest_cache(cache_file):
    """Load persisted digest cache from disk."""
    global DIGEST_CACHE_FILE
    DIGEST_CACHE_FILE = cache_file
    if not cache_file.exists():
        return
    try:
        payload = json.loads(cache_file.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"  WARN  Failed to load image digest cache: {cache_file} ({exc})")
        return

    entries = payload.get("image_digest_cache", {})
    if not isinstance(entries, dict):
        return

    for cache_key, image_value in entries.items():
        if isinstance(cache_key, str) and isinstance(image_value, str) and image_value.strip():
            IMAGE_DIGEST_CACHE[cache_key] = image_value.strip()


def save_digest_cache():
    """Persist digest cache to disk atomically."""
    if not DIGEST_CACHE_FILE:
        return
    DIGEST_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "image_digest_cache": {
            cache_key: image_ref
            for cache_key, image_ref in sorted(IMAGE_DIGEST_CACHE.items())
        },
    }
    tmp_file = DIGEST_CACHE_FILE.with_suffix(".tmp")
    tmp_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp_file, DIGEST_CACHE_FILE)


def update_digest_cache_entry(image_ref, architecture, resolved_image):
    """Store one resolved digest-pinned image and immediately persist cache."""
    IMAGE_DIGEST_CACHE[get_cache_key(image_ref, architecture)] = resolved_image
    save_digest_cache()


def map_architecture_to_platform(architecture):
    """Map CasaOS architecture names to OCI manifest platform values."""
    arch = normalize_architecture_name(architecture)
    mapping = {
        "amd64": ("linux", "amd64", None),
        "arm64": ("linux", "arm64", None),
        "386": ("linux", "386", None),
        "arm": ("linux", "arm", None),
    }
    return mapping.get(arch, ("linux", arch, None))


def resolve_image_to_digest(image_ref, architecture):
    """Resolve any tagged image reference to a digest-pinned reference for one architecture."""
    parsed = parse_image_reference(image_ref)
    if not parsed or not parsed.get("tag"):
        return image_ref

    cache_key = get_cache_key(image_ref, architecture)
    cached = IMAGE_DIGEST_CACHE.get(cache_key)
    if cached:
        digest = cached.split("@", 1)[1] if "@" in cached else None
        if digest:
            DIGEST_CACHE_ENTRIES.setdefault(image_ref, digest)
        return cached

    try:
        manifest_payload, response_headers, manifest_parsed = fetch_registry_manifest(image_ref)
    except Exception as exc:
        if is_registry_rate_limited_error(exc):
            raise
        raise RuntimeError(f"Failed to resolve image digest: {image_ref}") from exc

    media_type = manifest_payload.get("mediaType", "")
    digest = response_headers.get("Docker-Content-Digest")

    if media_type in (
        "application/vnd.docker.distribution.manifest.list.v2+json",
        "application/vnd.oci.image.index.v1+json",
    ):
        chosen = pick_platform_manifest(manifest_payload, architecture)
        digest = chosen.get("digest")
        if not digest:
            raise RuntimeError(
                f"Manifest list did not contain a digest for architecture '{architecture}': {image_ref}"
            )

    if not digest:
        raise RuntimeError(f"Registry did not return digest for image: {image_ref}")

    DIGEST_CACHE_ENTRIES.setdefault(image_ref, digest)
    resolved_image = f"{parsed['name']}:{parsed['tag']}@{digest}"
    update_digest_cache_entry(image_ref, architecture, resolved_image)
    return resolved_image


def pin_service_images_to_digests(compose_data, app_id, architecture):
    """Replace all tagged service images with digest-pinned references for one architecture."""
    services = compose_data.get("services", {})
    if not isinstance(services, dict):
        return

    for service_name, service_def in services.items():
        if not isinstance(service_def, dict):
            continue
        image_ref = service_def.get("image")
        if not isinstance(image_ref, str):
            continue
        if "@" in image_ref:
            continue
        parsed = parse_image_reference(image_ref)
        if not parsed or not parsed.get("tag"):
            continue
        try:
            service_def["image"] = resolve_image_to_digest(image_ref, architecture)
        except ArchitectureMismatchError as exc:
            raise ArchitectureMismatchError(
                f"App '{app_id}' declares architecture '{architecture}', but service "
                f"'{service_name}' image '{image_ref}' does not provide that platform. "
                f"Please fix x-casaos.architectures or use an image tag that supports it. "
                f"Details: {exc}"
            ) from exc
        except Exception as exc:
            registry = parsed.get("registry") if isinstance(parsed, dict) else None
            if is_registry_rate_limited_error(exc):
                warn_registry_rate_limited_once(
                    app_id,
                    registry,
                    image_ref,
                    f"skipped image digest pinning for architecture '{architecture}'",
                )
                continue
            # Keep the original tagged reference if the registry cannot resolve
            # the digest during this build run.
            record_digest_warning(app_id, service_name, image_ref, architecture, exc)


def hash_directory_files(root_dir):
    """Compute a stable short hash from all files under a directory."""
    h = hashlib.sha256()
    files = sorted(
        p for p in root_dir.rglob("*")
        if p.is_file()
    )
    for file_path in files:
        rel = file_path.relative_to(root_dir).as_posix().encode("utf-8")
        h.update(rel)
        h.update(b"\0")
        h.update(file_path.read_bytes())
        h.update(b"\0")
    return h.hexdigest()[:8]


def normalize_base_url(base):
    """Normalize base URL without trailing '/'."""
    if not base:
        return ""
    return base.rstrip("/")


def default_cache_file(source_root):
    """Return the default on-disk cache file path."""
    return source_root / ".cache" / "build_appstore" / "image-size-cache.json"


def default_digest_cache_file(source_root):
    """Return the default on-disk digest cache file path for v2 builds."""
    return source_root / ".cache" / "build_appstore" / "image-digest-cache.json"


def normalize_architecture_name(architecture):
    """Normalize architecture names to stable lowercase identifiers."""
    return str(architecture or "").strip().lower()


def get_cache_key(image_ref, architecture):
    """Build a cache key for an image reference and target architecture."""
    return f"{image_ref}|{normalize_architecture_name(architecture)}"


def get_supported_architectures(original_xcasaos):
    """Return normalized, de-duplicated architecture list from x-casaos."""
    values = original_xcasaos.get("architectures", [])
    if not isinstance(values, list):
        return []

    architectures = []
    seen = set()
    for value in values:
        arch = normalize_architecture_name(value)
        if not arch or arch in seen:
            continue
        seen.add(arch)
        architectures.append(arch)
    return architectures


def serialize_image_descriptors(descriptors):
    """Convert cached descriptors to JSON-safe form."""
    return [{"digest": digest, "size": int(size)} for digest, size in descriptors]


def deserialize_image_descriptors(payload):
    """Convert JSON-loaded descriptors to tuple form."""
    out = []
    if not isinstance(payload, list):
        return out
    for item in payload:
        if not isinstance(item, dict):
            continue
        digest = item.get("digest")
        size = item.get("size")
        if not digest or size is None:
            continue
        out.append((str(digest), int(size)))
    return out


def load_image_size_cache(cache_file):
    """Load persisted image descriptor cache from disk."""
    global IMAGE_SIZE_CACHE_FILE
    IMAGE_SIZE_CACHE_FILE = cache_file
    if not cache_file.exists():
        return
    try:
        payload = json.loads(cache_file.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"  WARN  Failed to load image size cache: {cache_file} ({exc})")
        return

    entries = payload.get("image_size_cache", {})
    if not isinstance(entries, dict):
        return

    for cache_key, descriptors in entries.items():
        parsed = deserialize_image_descriptors(descriptors)
        if parsed:
            IMAGE_SIZE_CACHE[str(cache_key)] = parsed


def save_image_size_cache():
    """Persist image descriptor cache to disk atomically."""
    if not IMAGE_SIZE_CACHE_FILE:
        return
    IMAGE_SIZE_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "image_size_cache": {
            image_ref: serialize_image_descriptors(descriptors)
            for image_ref, descriptors in sorted(IMAGE_SIZE_CACHE.items())
        },
    }
    tmp_file = IMAGE_SIZE_CACHE_FILE.with_suffix(".tmp")
    tmp_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp_file, IMAGE_SIZE_CACHE_FILE)


def update_image_size_cache_entry(image_ref, architecture, descriptors):
    """Store one resolved image entry and immediately persist cache to disk."""
    IMAGE_SIZE_CACHE[get_cache_key(image_ref, architecture)] = descriptors
    save_image_size_cache()


def parse_memory_to_bytes(value):
    """Convert docker-style memory strings like 64M / 1G to bytes."""
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return int(value)

    text = str(value).strip()
    match = re.fullmatch(r"(?i)(\d+(?:\.\d+)?)\s*([kmgtp]?i?b?|b)?", text)
    if not match:
        return 0

    number = float(match.group(1))
    unit = (match.group(2) or "b").lower()
    factors = {
        "b": 1,
        "k": 1024,
        "kb": 1024,
        "kib": 1024,
        "m": 1024 ** 2,
        "mb": 1024 ** 2,
        "mib": 1024 ** 2,
        "g": 1024 ** 3,
        "gb": 1024 ** 3,
        "gib": 1024 ** 3,
        "t": 1024 ** 4,
        "tb": 1024 ** 4,
        "tib": 1024 ** 4,
        "p": 1024 ** 5,
        "pb": 1024 ** 5,
        "pib": 1024 ** 5,
    }
    return int(number * factors.get(unit, 1))


def calculate_min_memory(compose_data):
    """Sum deploy.resources.reservations.memory across all services."""
    total = 0
    services = compose_data.get("services", {})
    if not isinstance(services, dict):
        return total

    for service_def in services.values():
        if not isinstance(service_def, dict):
            continue
        deploy = service_def.get("deploy", {})
        resources = deploy.get("resources", {}) if isinstance(deploy, dict) else {}
        reservations = resources.get("reservations", {}) if isinstance(resources, dict) else {}
        memory = reservations.get("memory") if isinstance(reservations, dict) else None
        total += parse_memory_to_bytes(memory)
    return total


def parse_image_reference_with_digest(image_ref):
    """Parse an image reference, supporting both tag and digest references."""
    digest = None
    reference = None
    name = image_ref
    if "@" in image_ref:
        name, digest = image_ref.split("@", 1)
        reference = digest
        last_slash = name.rfind("/")
        last_colon = name.rfind(":")
        if last_colon > last_slash:
            name = name[:last_colon]
    else:
        last_slash = image_ref.rfind("/")
        last_colon = image_ref.rfind(":")
        if last_colon > last_slash:
            name = image_ref[:last_colon]
            reference = image_ref[last_colon + 1:]
        else:
            reference = "latest"

    first_part, _, remainder = name.partition("/")
    if "." in first_part or ":" in first_part or first_part == "localhost":
        registry = first_part
        repository = remainder
    else:
        registry = "registry-1.docker.io"
        repository = name

    if registry == "docker.io":
        registry = "registry-1.docker.io"

    if registry == "registry-1.docker.io" and "/" not in repository:
        repository = f"library/{repository}"

    if not repository or not reference:
        return None

    return {
        "registry": registry,
        "repository": repository,
        "reference": reference,
        "name": name,
    }


def fetch_registry_manifest(image_ref):
    """Fetch the registry manifest or manifest list payload for an image reference."""
    cached = REGISTRY_MANIFEST_CACHE.get(image_ref)
    if cached is not None:
        return cached

    parsed = parse_image_reference_with_digest(image_ref)
    if not parsed:
        raise RuntimeError(f"Unsupported image reference: {image_ref}")

    manifest_url = (
        f"https://{parsed['registry']}/v2/{parsed['repository']}/manifests/{parsed['reference']}"
    )
    payload, headers = registry_json_request(
        manifest_url,
        headers={"Accept": DOCKER_MANIFEST_ACCEPT},
        registry=parsed["registry"],
    )
    result = (json.loads(payload), headers, parsed)
    REGISTRY_MANIFEST_CACHE[image_ref] = result
    return result


def pick_platform_manifest(index_payload, architecture):
    """Choose the target platform manifest from a manifest list/index."""
    manifests = index_payload.get("manifests", [])
    if not isinstance(manifests, list) or not manifests:
        raise RuntimeError("Manifest list/index did not contain manifests")

    target_os, target_arch, target_variant = map_architecture_to_platform(architecture)

    for item in manifests:
        platform = item.get("platform", {})
        if (
            isinstance(platform, dict)
            and platform.get("os") == target_os
            and platform.get("architecture") == target_arch
            and (target_variant is None or platform.get("variant") == target_variant)
        ):
            return item

    for item in manifests:
        platform = item.get("platform", {})
        if (
            isinstance(platform, dict)
            and platform.get("os") == target_os
            and platform.get("architecture") == target_arch
        ):
            return item

    raise ArchitectureMismatchError(
        f"Manifest list/index did not contain a matching platform for architecture '{architecture}'"
    )


def fetch_child_manifest(parsed, digest):
    """Fetch a platform-specific child manifest by digest."""
    cache_key = f"{parsed['registry']}/{parsed['repository']}@{digest}"
    cached = REGISTRY_CHILD_MANIFEST_CACHE.get(cache_key)
    if cached is not None:
        return cached

    manifest_url = f"https://{parsed['registry']}/v2/{parsed['repository']}/manifests/{digest}"
    payload, _headers = registry_json_request(
        manifest_url,
        headers={"Accept": DOCKER_MANIFEST_ACCEPT},
        registry=parsed["registry"],
    )
    result = json.loads(payload)
    REGISTRY_CHILD_MANIFEST_CACHE[cache_key] = result
    return result


def estimate_image_blob_descriptors(image_ref, architecture):
    """Return unique blob descriptors that make up an image's storage footprint."""
    manifest_payload, _headers, parsed = fetch_registry_manifest(image_ref)
    media_type = manifest_payload.get("mediaType", "")

    if media_type in (
        "application/vnd.docker.distribution.manifest.list.v2+json",
        "application/vnd.oci.image.index.v1+json",
    ):
        chosen = pick_platform_manifest(manifest_payload, architecture)
        manifest_payload = fetch_child_manifest(parsed, chosen.get("digest"))

    descriptors = []
    config = manifest_payload.get("config")
    if isinstance(config, dict) and config.get("digest") and config.get("size") is not None:
        descriptors.append((config["digest"], int(config["size"])))

    for layer in manifest_payload.get("layers", []) or []:
        if isinstance(layer, dict) and layer.get("digest") and layer.get("size") is not None:
            descriptors.append((layer["digest"], int(layer["size"])))
    return descriptors


def calculate_min_image_size(compose_data, app_id, architecture):
    """Estimate image storage size by summing unique blobs across all service images."""
    services = compose_data.get("services", {})
    if not isinstance(services, dict):
        return 0

    seen = set()
    total = 0
    for service_name, service_def in services.items():
        if not isinstance(service_def, dict):
            continue
        image_ref = service_def.get("image")
        if not isinstance(image_ref, str) or not image_ref.strip():
            continue
        parsed = parse_image_reference_with_digest(image_ref)
        registry = parsed.get("registry") if isinstance(parsed, dict) else None
        try:
            cache_key = get_cache_key(image_ref, architecture)
            descriptors = IMAGE_SIZE_CACHE.get(cache_key)
            if descriptors is None:
                descriptors = estimate_image_blob_descriptors(image_ref, architecture)
                update_image_size_cache_entry(image_ref, architecture, descriptors)
            for digest, size in descriptors:
                if digest in seen:
                    continue
                seen.add(digest)
                total += size
        except ArchitectureMismatchError as exc:
            raise ArchitectureMismatchError(
                f"App '{app_id}' declares architecture '{architecture}', but service "
                f"'{service_name}' image '{image_ref}' does not provide that platform. "
                f"Please fix x-casaos.architectures or use an image tag that supports it. "
                f"Details: {exc}"
            ) from exc
        except Exception as exc:
            if is_registry_rate_limited_error(exc):
                warn_registry_rate_limited_once(
                    app_id,
                    registry,
                    image_ref,
                    f"skipped image-size estimation for architecture '{architecture}'",
                )
                continue
            record_image_size_warning(app_id, service_name, image_ref, architecture, exc)
    return total


def url_join(base, path):
    """Join base URL and path where path should start with '/'."""
    path = path if str(path).startswith("/") else f"/{path}"
    if not base:
        return path
    return f"{base.rstrip('/')}{path}"


def normalize_locale_key(key):
    """Normalize locale key to ll_CC format (e.g. en_us -> en_US)."""
    parts = key.split("_", 1)
    if len(parts) == 2:
        return f"{parts[0].lower()}_{parts[1].upper()}"
    return key


def normalize_locale_dict(d):
    """Normalize locale keys in i18n dicts."""
    if not isinstance(d, dict):
        return d
    return {normalize_locale_key(k): v for k, v in d.items()}


def parse_image_reference(image_ref):
    """Parse a container image reference into registry/repository/tag parts."""
    digest_sep = image_ref.split("@", 1)
    if len(digest_sep) == 2:
        return None

    last_slash = image_ref.rfind("/")
    last_colon = image_ref.rfind(":")
    if last_colon > last_slash:
        name = image_ref[:last_colon]
        tag = image_ref[last_colon + 1:]
    else:
        name = image_ref
        tag = None

    if not tag:
        return None

    first_part, _, remainder = name.partition("/")
    if "." in first_part or ":" in first_part or first_part == "localhost":
        registry = first_part
        repository = remainder
    else:
        registry = "registry-1.docker.io"
        repository = name

    if registry == "docker.io":
        registry = "registry-1.docker.io"

    if registry == "registry-1.docker.io" and "/" not in repository:
        repository = f"library/{repository}"

    if not repository:
        return None

    return {
        "registry": registry,
        "repository": repository,
        "tag": tag,
        "name": name,
    }


def normalize_i18n_in_dict(data):
    """Normalize locale keys for all known i18n fields in a dict."""
    for field in I18N_FIELDS:
        if field in data and isinstance(data[field], dict):
            data[field] = normalize_locale_dict(data[field])
    for field in I18N_NESTED_FIELDS:
        if field in data and isinstance(data[field], dict):
            for sub_key, sub_val in data[field].items():
                if isinstance(sub_val, dict):
                    data[field][sub_key] = normalize_locale_dict(sub_val)
    return data


def resolve_i18n(value, locale):
    """Resolve an i18n dict to plain text with fallback chain."""
    if not isinstance(value, dict):
        return value if value is not None else ""
    if locale in value:
        return value[locale]
    if DEFAULT_LOCALE in value:
        return value[DEFAULT_LOCALE]
    return next(iter(value.values()), "")


def resolve_i18n_strict(value, locale):
    """Resolve i18n without fallback; return empty string when locale missing."""
    if not isinstance(value, dict):
        return value if value is not None else ""
    return value.get(locale, "")


def resolve_i18n_nested(value, locale, strict=False):
    """Resolve a nested i18n structure (like tips) for a given locale."""
    if not isinstance(value, dict):
        return value
    resolver = resolve_i18n_strict if strict else resolve_i18n
    result = {}
    for key, sub_val in value.items():
        result[key] = resolver(sub_val, locale)
    return result


def collect_locales_from_i18n(data, fields=None, nested_fields=None):
    """Collect explicitly defined locales from i18n dict fields."""
    if not isinstance(data, dict):
        return set()

    fields = fields or I18N_FIELDS
    nested_fields = nested_fields or I18N_NESTED_FIELDS
    locales = set()

    for field in fields:
        value = data.get(field)
        if isinstance(value, dict):
            locales.update(value.keys())

    for field in nested_fields:
        value = data.get(field)
        if not isinstance(value, dict):
            continue
        for sub_val in value.values():
            if isinstance(sub_val, dict):
                locales.update(sub_val.keys())

    return locales


def to_json_safe(obj):
    """Recursively convert Python objects to JSON-serializable values."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: to_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_json_safe(v) for v in obj]
    return obj


def load_supported_languages(source):
    """Load supported languages list from config file."""
    lang_path = source / SUPPORTED_LANGUAGES_FILE
    if not lang_path.exists():
        print(
            f"  WARN  {SUPPORTED_LANGUAGES_FILE} not found, using {DEFAULT_LOCALE} only",
            file=sys.stderr,
        )
        return [DEFAULT_LOCALE]
    with open(lang_path, "r", encoding="utf-8") as f:
        languages = json.load(f)
    if DEFAULT_LOCALE not in languages:
        languages.insert(0, DEFAULT_LOCALE)
    return [normalize_locale_key(l) for l in languages]


# ---------------------------------------------------------------------------
# Image processing
# ---------------------------------------------------------------------------

def optimize_and_convert_image(src_path, dst_path, max_width=MAX_IMAGE_WIDTH, quality=WEBP_QUALITY):
    """Optimize and convert image to WebP format. Returns output filename."""
    src_ext = src_path.suffix.lower()

    if src_ext == ".svg":
        shutil.copy2(src_path, dst_path)
        return dst_path.name

    # Keep animated GIFs in their original format to avoid losing frames.
    if src_ext == ".gif":
        shutil.copy2(src_path, dst_path)
        return dst_path.name

    if not PILLOW_AVAILABLE:
        shutil.copy2(src_path, dst_path)
        return dst_path.name

    if src_ext == ".webp":
        try:
            with Image.open(src_path) as img:
                if img.width <= max_width:
                    shutil.copy2(src_path, dst_path)
                    return dst_path.name
        except Exception:
            shutil.copy2(src_path, dst_path)
            return dst_path.name

    try:
        with Image.open(src_path) as img:
            if img.mode in ("RGBA", "LA", "P"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                background.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
                img = background
            elif img.mode != "RGB":
                img = img.convert("RGB")

            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

            webp_path = dst_path.with_suffix(".webp")
            img.save(webp_path, "WEBP", quality=quality, method=6)
            return webp_path.name

    except Exception as e:
        print(f"    WARN: Failed to optimize {src_path.name}: {e}", file=sys.stderr)
        shutil.copy2(src_path, dst_path)
        return dst_path.name


def convert_svg_icon_to_png(src_svg, dst_png):
    """Convert icon.svg to icon.png using rsvg-convert."""
    try:
        subprocess.run(
            ["rsvg-convert", str(src_svg), "-o", str(dst_png)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        return dst_png.name
    except FileNotFoundError:
        print("    WARN: rsvg-convert not found, cannot convert icon.svg to icon.png", file=sys.stderr)
    except subprocess.CalledProcessError as e:
        err = (e.stderr or "").strip()
        print(f"    WARN: Failed to convert {src_svg.name} -> {dst_png.name}: {err}", file=sys.stderr)
    return None


def is_remote_asset_ref(value):
    """Return True when the asset reference points to an HTTP(S) URL."""
    if not value or not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"}


def candidate_local_asset_paths(source_root, app_dir, asset_ref, prefer_icon_svg=False):
    """Build candidate local file paths for an asset reference."""
    candidates = []
    seen = set()

    def add_candidate(path):
        try:
            resolved = path.resolve()
        except FileNotFoundError:
            resolved = path
        key = str(resolved)
        if key in seen:
            return
        seen.add(key)
        candidates.append(path)

    ref_str = str(asset_ref).strip()
    if not ref_str:
        return candidates

    parsed = urlparse(ref_str)
    raw_path = parsed.path if parsed.scheme else ref_str
    raw_path = raw_path.strip()

    if raw_path:
        add_candidate(app_dir / raw_path)
        if raw_path.startswith("/"):
            add_candidate(source_root / raw_path.lstrip("/"))
        raw_name = Path(raw_path).name
        if raw_name:
            add_candidate(app_dir / raw_name)
            stem = Path(raw_name).stem
            if stem:
                for ext in sorted(IMAGE_EXTENSIONS):
                    add_candidate(app_dir / f"{stem}{ext}")
                    add_candidate(source_root / f"{stem}{ext}")

        path_parts = Path(raw_path).parts
        if "Apps" in path_parts:
            apps_index = path_parts.index("Apps")
            repo_relative = Path(*path_parts[apps_index:])
            add_candidate(source_root / repo_relative)
            repo_name = repo_relative.name
            if repo_name:
                add_candidate(source_root / "Apps" / repo_relative.parent.name / repo_name)

    if prefer_icon_svg:
        add_candidate(app_dir / "icon.svg")

    return candidates


def download_remote_asset(asset_ref, download_dir):
    """Download a remote asset into a temporary local file."""
    parsed = urlparse(asset_ref)
    filename = Path(parsed.path).name or "downloaded-asset"
    dst_path = download_dir / filename
    try:
        request = Request(
            asset_ref,
            headers={
                "User-Agent": "ZimaOS-AppStore-Build/1.0",
                "Accept": "*/*",
            },
        )
        with open_url_with_retries(request, timeout=30) as response, open(dst_path, "wb") as out_file:
            shutil.copyfileobj(response, out_file)
    except Exception as exc:
        raise RuntimeError(f"Failed to download asset: {asset_ref}") from exc
    return dst_path


def resolve_asset_source(source_root, app_dir, asset_ref, download_dir, prefer_icon_svg=False):
    """Resolve an asset reference to a local file, downloading if needed."""
    for candidate in candidate_local_asset_paths(
        source_root,
        app_dir,
        asset_ref,
        prefer_icon_svg=prefer_icon_svg,
    ):
        if candidate.is_file() and candidate.suffix.lower() in IMAGE_EXTENSIONS:
            return candidate

    if is_remote_asset_ref(asset_ref):
        return download_remote_asset(asset_ref, download_dir)

    raise FileNotFoundError(f"Referenced asset not found locally: {asset_ref}")


def resolve_asset_source_with_context(
    source_root,
    app_dir,
    asset_ref,
    download_dir,
    app_id,
    asset_field,
    prefer_icon_svg=False,
):
    """Resolve an asset and raise context-rich errors for CI logs."""
    try:
        return resolve_asset_source(
            source_root,
            app_dir,
            asset_ref,
            download_dir,
            prefer_icon_svg=prefer_icon_svg,
        )
    except Exception as exc:
        raise RuntimeError(
            f"App '{app_id}' failed to resolve {asset_field}: {asset_ref}"
        ) from exc


def collect_asset_references(original_xcasaos, meta):
    """Collect the image references actually used by the app metadata."""
    refs = {
        "icon": original_xcasaos.get("icon"),
        "thumbnail": meta.get("thumbnail"),
        "screenshots": [],
    }
    screenshot_refs = meta.get("screenshot_link")
    if isinstance(screenshot_refs, list):
        refs["screenshots"] = [ref for ref in screenshot_refs if ref]
    return refs


def process_icon_asset(src_path, assets_output):
    """Process the referenced icon and return copied files plus preferred output name."""
    copied_images = []
    image_mapping = {}

    if src_path.suffix.lower() == ".svg":
        shutil.copy2(src_path, assets_output / "icon.svg")
        copied_images.append("icon.svg")
        image_mapping[src_path.name] = "icon.svg"
        png_name = convert_svg_icon_to_png(src_path, assets_output / "icon.png")
        if png_name:
            copied_images.append(png_name)
            image_mapping["icon.png"] = png_name
        return copied_images, image_mapping, "icon.svg"

    dst_name = f"icon{src_path.suffix.lower()}"
    dst_path = assets_output / dst_name
    shutil.copy2(src_path, dst_path)
    copied_images.append(dst_name)
    image_mapping[src_path.name] = dst_name
    return copied_images, image_mapping, dst_name


def process_general_asset(src_path, assets_output):
    """Process a referenced non-icon image."""
    dst_path = assets_output / src_path.name
    output_name = optimize_and_convert_image(src_path, dst_path)
    return output_name


def process_app_assets(source_root, app_dir, assets_output, original_xcasaos, meta):
    """Process only YAML-referenced images for a single app."""
    assets_output.mkdir(parents=True, exist_ok=True)

    copied_images = []
    image_mapping = {}
    refs = collect_asset_references(original_xcasaos, meta)
    icon_filename = "icon.png"
    app_id = app_dir.name

    with tempfile.TemporaryDirectory(prefix="appstore-assets-") as temp_dir:
        download_dir = Path(temp_dir)

        icon_ref = refs.get("icon")
        if icon_ref:
            icon_src = resolve_asset_source_with_context(
                source_root,
                app_dir,
                icon_ref,
                download_dir,
                app_id,
                "icon",
                prefer_icon_svg=True,
            )
            icon_copied, icon_mapping, icon_filename = process_icon_asset(icon_src, assets_output)
            copied_images.extend(icon_copied)
            image_mapping.update(icon_mapping)
            image_mapping[str(icon_ref)] = icon_filename
            image_mapping[Path(str(icon_ref).rsplit("/", 1)[-1]).name] = icon_filename

        thumbnail_ref = refs.get("thumbnail")
        if thumbnail_ref:
            thumb_src = resolve_asset_source_with_context(
                source_root,
                app_dir,
                thumbnail_ref,
                download_dir,
                app_id,
                "thumbnail",
            )
            output_name = process_general_asset(thumb_src, assets_output)
            copied_images.append(output_name)
            image_mapping[thumb_src.name] = output_name
            image_mapping[str(thumbnail_ref)] = output_name
            image_mapping[Path(str(thumbnail_ref).rsplit("/", 1)[-1]).name] = output_name

        for index, screenshot_ref in enumerate(refs.get("screenshots", []), start=1):
            screenshot_src = resolve_asset_source_with_context(
                source_root,
                app_dir,
                screenshot_ref,
                download_dir,
                app_id,
                f"screenshot_link[{index}]",
            )
            output_name = process_general_asset(screenshot_src, assets_output)
            copied_images.append(output_name)
            image_mapping[screenshot_src.name] = output_name
            image_mapping[str(screenshot_ref)] = output_name
            image_mapping[Path(str(screenshot_ref).rsplit("/", 1)[-1]).name] = output_name

    return copied_images, image_mapping, icon_filename


# ---------------------------------------------------------------------------
# Config loaders
# ---------------------------------------------------------------------------

def validate_app_id(compose_path, compose_data, xcasaos):
    """Validate required x-casaos.id field and return its normalized value."""
    raw_app_id = xcasaos.get("id")
    if raw_app_id is None or not str(raw_app_id).strip():
        expected_name = compose_data.get("name") or compose_path.parent.name.lower()
        raise ValueError(
            f"App '{compose_path.parent.name}' is missing required x-casaos.id "
            f"in {compose_path}. Expected a reverse-domain style ID like "
            f"'com.example.{re.sub(r'[^a-z0-9._-]+', '-', str(expected_name).lower()).strip('-') or 'app'}'."
        )

    return validate_reverse_domain_app_id(
        raw_app_id,
        f"App '{compose_path.parent.name}' in {compose_path}",
    )


def normalize_categories(category_value):
    """Normalize category metadata to a lowercase category-id array."""
    if not category_value:
        return []
    if isinstance(category_value, (list, tuple, set)):
        values = category_value
    else:
        values = [category_value]

    categories = []
    seen = set()
    for value in values:
        if value is None:
            continue
        cat_id = str(value).strip().lower()
        if not cat_id or cat_id in seen:
            continue
        seen.add(cat_id)
        categories.append(cat_id)
    return categories


def load_store_config(source):
    """Load store-config.json and return store config dict."""
    config_path = source / STORE_CONFIG_FILE
    if not config_path.exists():
        return None
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    raw_store_id = config.get("store_id")
    config["store_id"] = validate_safe_id(
        raw_store_id,
        "store_id",
        f"{STORE_CONFIG_FILE} ({config_path})",
    )
    for field in ("name", "description"):
        if field in config and isinstance(config[field], dict):
            config[field] = normalize_locale_dict(config[field])
    return config


def split_compose(compose_data):
    """Split parsed docker-compose.yml into clean compose + meta dict."""
    xcasaos = compose_data.pop("x-casaos", {})

    if "port_map" in xcasaos and not isinstance(xcasaos["port_map"], str):
        xcasaos["port_map"] = str(xcasaos["port_map"])

    compose_xcasaos = {}
    meta = {}
    for key, value in xcasaos.items():
        if key == "store_app_id":
            continue
        if key in COMPOSE_KEEP_FIELDS:
            compose_xcasaos[key] = value
        else:
            meta[key] = value

    services = compose_data.get("services", {})
    if isinstance(services, dict):
        for svc_def in services.values():
            if not isinstance(svc_def, dict):
                continue
            if "x-casaos" in svc_def:
                del svc_def["x-casaos"]
            labels = svc_def.get("labels", {})
            if isinstance(labels, dict) and "icon" in labels:
                del labels["icon"]
                if not labels:
                    del svc_def["labels"]

    compose_data["x-casaos"] = compose_xcasaos
    return compose_data, meta


# ---------------------------------------------------------------------------
# Per-app processing
# ---------------------------------------------------------------------------

def parse_app(app_dir):
    """Parse a single app directory and return raw data.

    Returns (app_id, compose_data, meta, original_xcasaos) or None if skipped.
    """
    compose_path = app_dir / "docker-compose.yml"
    if not compose_path.exists():
        compose_path = app_dir / "docker-compose.yaml"
    if not compose_path.exists():
        return None

    with open(compose_path, "r", encoding="utf-8") as f:
        raw_content = f.read()

    try:
        compose_data = yaml.safe_load(raw_content)
    except yaml.YAMLError as e:
        print(f"  YAML ERROR: {app_dir.name}: {e}", file=sys.stderr)
        return None

    if not compose_data or not isinstance(compose_data, dict):
        return None
    if "x-casaos" not in compose_data:
        return None

    original_xcasaos = dict(compose_data.get("x-casaos", {}))
    validated_source_app_id = validate_app_id(compose_path, compose_data, original_xcasaos)
    original_xcasaos["id"] = validated_source_app_id
    app_id = validated_source_app_id

    compose_data, meta = split_compose(compose_data)

    normalize_i18n_in_dict(compose_data.get("x-casaos", {}))
    normalize_i18n_in_dict(meta)
    normalize_i18n_in_dict(original_xcasaos)

    return app_id, compose_data, meta, original_xcasaos


def resolve_asset_filename(url_or_name, image_mapping, copied_images):
    """Extract filename from URL, map to converted output name."""
    if not url_or_name:
        return None
    fname = url_or_name.rsplit("/", 1)[-1] if "/" in str(url_or_name) else str(url_or_name)
    if fname in image_mapping:
        return image_mapping[fname]
    webp_name = f"{Path(fname).stem}.webp"
    if webp_name in copied_images:
        return webp_name
    return fname


def build_meta_payload(meta, locale, assets_path, copied_images, image_mapping, base_url,
                       title_i18n=None, strict=False, min_memory=0, min_image_size=None,
                       app_id="", source_version=""):
    """Build locale-resolved meta payload."""
    meta_l = copy.deepcopy(meta)
    category = meta_l.get("category", "")

    resolver = resolve_i18n_strict if strict else resolve_i18n
    if title_i18n is not None:
        meta_l["title"] = resolver(title_i18n, locale)
    for field in I18N_FIELDS:
        if field in meta_l:
            meta_l[field] = resolver(meta_l[field], locale)
    for field in I18N_NESTED_FIELDS:
        if field in meta_l and isinstance(meta_l[field], dict):
            meta_l[field] = resolve_i18n_nested(meta_l[field], locale, strict=strict)

    meta_l.pop("icon", None)
    if "release_notes" in meta_l:
        meta_l["release_note"] = meta_l.pop("release_notes")

    if "thumbnail" in meta_l:
        thumb_fname = resolve_asset_filename(meta_l["thumbnail"], image_mapping, copied_images)
        meta_l["thumbnail"] = f"{assets_path}/{thumb_fname}" if thumb_fname else ""
    if "screenshot_link" in meta_l:
        raw = meta_l["screenshot_link"]
        if raw and isinstance(raw, list):
            meta_l["screenshot_link"] = [
                f"{assets_path}/{resolved}"
                for u in raw
                for resolved in [resolve_asset_filename(u, image_mapping, copied_images)]
                if resolved
            ]
        else:
            meta_l["screenshot_link"] = []

    meta_l["base_url"] = normalize_base_url(base_url)
    meta_l["id"] = app_id
    meta_l["version"] = source_version
    meta_l["categories"] = normalize_categories(category)
    meta_l["min_memory"] = int(min_memory)
    meta_l["min_image_size"] = {
        normalize_architecture_name(arch): int(size)
        for arch, size in sorted((min_image_size or {}).items())
    }
    return meta_l


def build_meta_i18n_overlay(app_id, meta, locale, title_i18n=None):
    """Build locale overlay meta file with id + i18n-only fields."""
    out = {"id": app_id}
    if isinstance(title_i18n, dict) and locale in title_i18n:
        out["title"] = title_i18n[locale]
    for field in I18N_FIELDS:
        value = meta.get(field)
        if isinstance(value, dict) and locale in value:
            output_field = "release_note" if field == "release_notes" else field
            out[output_field] = value[locale]
    for field in I18N_NESTED_FIELDS:
        value = meta.get(field)
        if not isinstance(value, dict):
            continue
        nested = {}
        for sub_key, sub_val in value.items():
            if isinstance(sub_val, dict) and locale in sub_val:
                nested[sub_key] = sub_val[locale]
        if nested:
            out[field] = nested
    return out


def normalize_index_version(app_id, version_value):
    """Return a semver-compliant version string for index.json, or None."""
    if version_value is None:
        return None

    version = str(version_value).strip()
    if not version:
        return None

    if SEMVER_PATTERN.fullmatch(version):
        return version

    print(
        f"  WARN  App '{app_id}' has non-semver x-casaos.version '{version}'; "
        "skipping version in index.json"
    )
    return None


def build_index_entry(app_id, original_xcasaos, locale, assets_path, icon_filename,
                      thumbnail, compose_url, meta_url, content_hash_value, strict=False):
    """Build one index entry for a locale."""
    resolver = resolve_i18n_strict if strict else resolve_i18n
    category = original_xcasaos.get("category", "")
    entry = {
        "id": app_id,
        "title": resolver(original_xcasaos.get("title", ""), locale),
        "tagline": resolver(original_xcasaos.get("tagline", ""), locale),
        "category": category,
        "categories": normalize_categories(category),
        "author": original_xcasaos.get("author", ""),
        "developer": original_xcasaos.get("developer", ""),
        "architectures": original_xcasaos.get("architectures", []),
        "icon": f"{assets_path}/{icon_filename}",
        "thumbnail": thumbnail,
        "compose_url": compose_url,
        "meta_url": meta_url,
        "content_hash": content_hash_value,
    }

    version = normalize_index_version(app_id, original_xcasaos.get("version"))
    if version is not None:
        entry["version"] = version
    return entry


def build_index_i18n_overlay_entry(app_id, original_xcasaos, locale):
    """Build locale overlay index entry with id + i18n-only fields."""
    out = {"id": app_id}
    for field in INDEX_I18N_FIELDS:
        value = original_xcasaos.get(field)
        if isinstance(value, dict) and locale in value:
            out[field] = value[locale]
    return out


def build_store_i18n_overlay(store_config, locale):
    """Build locale overlay store file with store_id + i18n-only fields."""
    out = {"store_id": store_config.get("store_id", "")}
    for field in ("name", "description"):
        value = store_config.get(field)
        if isinstance(value, dict) and locale in value:
            out[field] = value[locale]
    return out


def write_json(path, data):
    path.write_text(json.dumps(to_json_safe(data), ensure_ascii=False, indent=2), encoding="utf-8")


def write_digest_cache(path):
    """Write legacy digest cache mapping as 'image_ref digest' lines."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"{image_ref} {digest}"
        for image_ref, digest in sorted(DIGEST_CACHE_ENTRIES.items())
    ]
    content = "\n".join(lines)
    if content:
        content += "\n"
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    args = parse_args()
    source = Path(args.source).resolve()
    output = Path(args.output).resolve()
    base_url = args.base_url
    cache_file = Path(args.cache_file).resolve() if args.cache_file else default_cache_file(source)
    digest_cache_file = (
        Path(args.digest_cache_file).resolve()
        if args.digest_cache_file
        else default_digest_cache_file(source)
    )

    print(f"Source: {source}")
    print(f"Output: {output}")
    print(f"Base URL: {base_url or '(relative)'}")
    print(f"Cache file: {cache_file}")
    print(f"Digest cache file: {digest_cache_file}")
    print(
        "Docker Hub auth: "
        + (f"enabled for user '{DOCKERHUB_USERNAME}'" if DOCKERHUB_USERNAME and DOCKERHUB_TOKEN else "disabled")
    )
    print()

    load_image_size_cache(cache_file)
    load_digest_cache(digest_cache_file)

    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    apps_dir = source / "Apps"
    if not apps_dir.exists():
        print(f"Error: Apps directory not found at {apps_dir}", file=sys.stderr)
        sys.exit(1)

    languages = load_supported_languages(source)
    supported_locales = set(languages)
    print(f"Languages (candidate): {len(languages)} ({', '.join(languages)})")
    print()

    store_config = load_store_config(source)
    if store_config:
        print(f"  STORE {store_config.get('store_id', '(unknown)')}")
    else:
        print(f"  WARN  {STORE_CONFIG_FILE} not found, skipping store.json")

    print("\n── Processing apps ──")
    app_records = []
    skipped = []

    for app_dir in sorted(apps_dir.iterdir()):
        if not app_dir.is_dir():
            continue

        try:
            result = parse_app(app_dir)
        except ValueError as exc:
            print(f"  WARN  {exc}", file=sys.stderr)
            sys.exit(1)
        if result is None:
            skipped.append(app_dir.name)
            print(f"  SKIP {app_dir.name}")
            continue

        app_id, compose_data, meta, original_xcasaos = result

        try:
            app_output = output / "apps" / app_id
            assets_output = app_output / "assets"
            copied_images, image_mapping, icon_filename = process_app_assets(
                source,
                app_dir,
                assets_output,
                original_xcasaos,
                meta,
            )

            assets_path = f"/apps/{app_id}/assets"

            min_memory = calculate_min_memory(compose_data)
            architectures = get_supported_architectures(original_xcasaos)
            min_image_size = {}

            compose_default = copy.deepcopy(compose_data)
            compose_xc = compose_default.get("x-casaos", {})
            compose_xc["icon"] = url_join(base_url, f"{assets_path}/{icon_filename}")
            compose_default["x-casaos"] = compose_xc

            app_output.mkdir(parents=True, exist_ok=True)
            compose_content = yaml.dump(
                compose_default,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )
            compose_path = app_output / "docker-compose.yml"
            compose_path.write_text(compose_content, encoding="utf-8")

            for architecture in architectures:
                compose_arch = copy.deepcopy(compose_default)
                pin_service_images_to_digests(compose_arch, app_id, architecture)
                min_image_size[architecture] = calculate_min_image_size(
                    compose_arch,
                    app_id,
                    architecture,
                )
                compose_arch_content = yaml.dump(
                    compose_arch,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                )
                compose_arch_path = app_output / f"docker-compose.{architecture}.yml"
                compose_arch_path.write_text(compose_arch_content, encoding="utf-8")
        except ArchitectureMismatchError as exc:
            print(f"  ERROR {exc}", file=sys.stderr)
            sys.exit(1)

        meta_default = build_meta_payload(
            meta,
            DEFAULT_LOCALE,
            assets_path,
            copied_images,
            image_mapping,
            base_url,
            title_i18n=original_xcasaos.get("title"),
            strict=False,
            min_memory=min_memory,
            min_image_size=min_image_size,
            app_id=app_id,
            source_version=str(original_xcasaos.get("version", "")).strip(),
        )
        meta_default_content = json.dumps(to_json_safe(meta_default), ensure_ascii=False, indent=2)
        (app_output / "meta.json").write_text(meta_default_content, encoding="utf-8")

        meta_locales = collect_locales_from_i18n(meta)
        meta_locales = {
            loc for loc in meta_locales
            if loc in supported_locales and loc != DEFAULT_LOCALE
        }
        for locale in sorted(meta_locales):
            meta_locale = build_meta_i18n_overlay(
                app_id,
                meta,
                locale,
                title_i18n=original_xcasaos.get("title"),
            )
            write_json(app_output / f"meta.{locale}.json", meta_locale)

        chash = hash_directory_files(app_output)

        index_locales = collect_locales_from_i18n(
            original_xcasaos,
            fields=INDEX_I18N_FIELDS,
            nested_fields=set(),
        )
        index_locales = {
            loc for loc in index_locales
            if loc in supported_locales and loc != DEFAULT_LOCALE
        }

        app_records.append({
            "app_id": app_id,
            "original_xcasaos": original_xcasaos,
            "assets_path": assets_path,
            "icon_filename": icon_filename,
            "thumbnail": meta_default.get("thumbnail", ""),
            "content_hash": chash,
            "index_locales": index_locales,
        })
        flush_app_warnings(app_id)
        print(f"  OK   {app_id}")

    app_records.sort(key=lambda x: x["app_id"])

    print("\n── Generating store/index files ──")

    if store_config:
        store_default = {
            "version": store_config.get("version", 2),
            "store_id": store_config.get("store_id", ""),
            "name": resolve_i18n(store_config.get("name", ""), DEFAULT_LOCALE),
            "description": resolve_i18n(store_config.get("description", ""), DEFAULT_LOCALE),
            "maintainer": store_config.get("maintainer", ""),
            "url": store_config.get("url", ""),
        }
        write_json(output / "store.json", store_default)

        store_locales = set()
        for field in ("name", "description"):
            value = store_config.get(field)
            if isinstance(value, dict):
                store_locales.update(value.keys())
        store_locales = {
            loc for loc in store_locales
            if loc in supported_locales and loc != DEFAULT_LOCALE
        }

        for locale in sorted(store_locales):
            store_locale = build_store_i18n_overlay(store_config, locale)
            write_json(output / f"store.{locale}.json", store_locale)
            print(f"  store.{locale}.json")

    default_entries = []
    for record in app_records:
        app_id = record["app_id"]
        default_entries.append(
            build_index_entry(
                app_id=app_id,
                original_xcasaos=record["original_xcasaos"],
                locale=DEFAULT_LOCALE,
                assets_path=record["assets_path"],
                icon_filename=record["icon_filename"],
                thumbnail=record["thumbnail"],
                compose_url=f"/apps/{app_id}/docker-compose.yml",
                meta_url=f"/apps/{app_id}/meta.json",
                content_hash_value=record["content_hash"],
                strict=False,
            )
        )

    index_default = {
        "version": 2,
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "app_count": len(default_entries),
        "base_url": normalize_base_url(base_url),
        "apps": default_entries,
    }
    write_json(output / "index.json", index_default)

    candidate_index_locales = set()
    for record in app_records:
        candidate_index_locales.update(record["index_locales"])

    for locale in sorted(candidate_index_locales):
        locale_entries = []
        for record in app_records:
            if locale not in record["index_locales"]:
                continue
            app_id = record["app_id"]
            entry = build_index_i18n_overlay_entry(
                app_id=app_id,
                original_xcasaos=record["original_xcasaos"],
                locale=locale,
            )
            # Keep sparse locale files: id + explicitly translated i18n fields only.
            if len(entry) > 1:
                locale_entries.append(entry)

        if not locale_entries:
            continue

        index_locale = {"apps": locale_entries}
        write_json(output / f"index.{locale}.json", index_locale)
        print(f"  index.{locale}.json ({len(locale_entries)} apps)")

    write_digest_cache(output / "store" / "digest_cache.txt")

    print(f"\n{'=' * 50}")
    print(f"Done! {len(app_records)} apps")
    print(f"Output: {output}/")
    print("  index.json")
    print("  index.{locale}.json (only when locale is explicitly defined)")
    print("  store.json / store.{locale}.json")
    print("  apps/{app_id}/docker-compose.yml")
    print("  apps/{app_id}/docker-compose.{architecture}.yml")
    print("  apps/{app_id}/meta.json / meta.{locale}.json")
    print("  apps/{app_id}/assets/*")
    if skipped:
        print(f"  Skipped: {', '.join(skipped)}")

    save_image_size_cache()
    save_digest_cache()


if __name__ == "__main__":
    main()
