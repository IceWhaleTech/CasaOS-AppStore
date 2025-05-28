import os
import re
import requests
import zipfile
import io
import yaml
import hashlib
import json
from urllib.parse import urlparse

CACHE_FILE = "digest_cache.json"
OUTPUT_FILE = "output.txt"
ZIP_URLS = [
    "https://cdn.jsdelivr.net/gh/IceWhaleTech/CasaOS-AppStore@gh-pages/store/main.zip",
    "https://play.cuse.eu.org/Cp0204-AppStore-Play.zip",
    "https://github.com/bigbeartechworld/big-bear-casaos/archive/refs/heads/master.zip",
    "https://casaos-appstore.paodayag.dev/linuxserver.zip",
]

digest_cache = {}

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_cache():
    with open(CACHE_FILE, "w") as f:
        json.dump(digest_cache, f, indent=2)

def parse_images_from_compose(yml_bytes):
    try:
        content = yaml.safe_load(yml_bytes)
        images = []
        if isinstance(content, dict) and 'services' in content:
            for service in content['services'].values():
                image = service.get('image')
                if image:
                    images.append(image.strip())
        return images
    except Exception as e:
        print(f"⚠️ Failed to parse YAML: {e}")
        return []

def normalize_image_name(image):
    # Remove ghcr.io, lscr.io, docker.io prefix
    for prefix in ["ghcr.io/", "lscr.io/", "docker.io/"]:
        if image.startswith(prefix):
            image = image[len(prefix):]
            break

    # If no org, assume library/
    if '/' not in image.split(":")[0]:
        image = "library/" + image

    # If no tag, assume latest
    if ":" not in image:
        image += ":latest"

    return image

def get_digest(image):
    if image in digest_cache:
        return digest_cache[image]

    normalized = normalize_image_name(image)
    repo, tag = normalized.rsplit(":", 1)
    registry_url = "https://registry-1.docker.io"
    token_url = "https://auth.docker.io/token"

    try:
        # Step 1: Get auth token
        token_resp = requests.get(token_url, params={
            "service": "registry.docker.io",
            "scope": f"repository:{repo}:pull"
        })
        token_resp.raise_for_status()
        token = token_resp.json()["token"]

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.docker.distribution.manifest.v2+json"
        }

        manifest_url = f"{registry_url}/v2/{repo}/manifests/{tag}"
        r = requests.get(manifest_url, headers=headers)
        r.raise_for_status()

        digest = r.headers.get("Docker-Content-Digest")
        if digest:
            digest_cache[image] = digest
            return digest
        else:
            print(f"⚠️ No digest found in headers for {image}")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code in (401, 403):
            print(f"⚠️ Access denied to {image}. Skipping.")
        elif e.response.status_code == 429:
            print(f"⚠️ Rate limited when accessing {image}. Skipping.")
        else:
            print(f"⚠️ Failed to get digest for {image}: {e}")
    except Exception as e:
        print(f"⚠️ Error getting digest for {image}: {e}")

    return None

def process_zip(url):
    images = set()
    try:
        r = requests.get(url)
        r.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            for name in z.namelist():
                if name.endswith("docker-compose.yml") and "default.new/Apps" in name:
                    with z.open(name) as f:
                        content = f.read()
                        imgs = parse_images_from_compose(content)
                        images.update(imgs)
    except Exception as e:
        print(f"⚠️ Error processing {url}: {e}")
    return images

def main():
    global digest_cache
    digest_cache = load_cache()

    all_images = set()
    for url in ZIP_URLS:
        print(f"📦 Processing {url}")
        imgs = process_zip(url)
        all_images.update(imgs)

    output_lines = []
    existing_lines = set()
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r") as f:
            existing_lines = set(line.strip() for line in f)

    for image in sorted(all_images):
        if any(image in line for line in existing_lines):
            continue
        digest = get_digest(image)
        if digest:
            line = f"{image} {digest}"
            output_lines.append(line)
            print(f"✅ {line}")

    if output_lines:
        with open(OUTPUT_FILE, "a") as f:
            for line in output_lines:
                f.write(line + "\n")

    save_cache()

if __name__ == "__main__":
    main()

