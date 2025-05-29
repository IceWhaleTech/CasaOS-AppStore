import os
import re
import io
import zipfile
import requests
import yaml

OUTPUT_FILE = "digest_cache.txt"

ZIP_URLS = [
    "https://cdn.jsdelivr.net/gh/IceWhaleTech/CasaOS-AppStore@gh-pages/store/main.zip",
    "https://play.cuse.eu.org/Cp0204-AppStore-Play.zip",
    "https://github.com/bigbeartechworld/big-bear-casaos/archive/refs/heads/master.zip",
    "https://casaos-appstore.paodayag.dev/linuxserver.zip",
]

DOCKER_USER = os.getenv("DOCKER_USERNAME", "")
DOCKER_TOKEN = os.getenv("DOCKER_TOKEN", "")

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
        print(f"⚠️ YAML Parse Error: {e}")
        return []

def normalize_image_name(image):
    if ':' not in image:
        image += ":latest"
    return image

def get_digest_ghcr(image):
    try:
        image = image.replace("ghcr.io/", "")
        repo, tag = image.rsplit(":", 1)
        token_url = f"https://ghcr.io/token?scope=repository:{repo}:pull"
        r = requests.get(token_url)
        r.raise_for_status()
        token = r.json()["token"]
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.docker.distribution.manifest.v2+json"
        }
        manifest_url = f"https://ghcr.io/v2/{repo}/manifests/{tag}"
        r = requests.get(manifest_url, headers=headers)
        r.raise_for_status()
        return r.headers.get("Docker-Content-Digest")
    except Exception as e:
        print(f"⚠️ GHCR query failed for {image}: {e}")
        return None

def get_digest_dockerhub(image):
    try:
        stripped = re.sub(r"^(docker\.io/|ghcr\.io/|lscr\.io/)?", "", image)
        if '/' not in stripped.split(":")[0]:
            stripped = "library/" + stripped
        repo, tag = stripped.rsplit(":", 1)

        token_url = "https://auth.docker.io/token"
        if DOCKER_USER and DOCKER_TOKEN:
            r = requests.get(token_url, params={
                "service": "registry.docker.io",
                "scope": f"repository:{repo}:pull"
            }, auth=(DOCKER_USER, DOCKER_TOKEN))
        else:
            r = requests.get(token_url, params={
                "service": "registry.docker.io",
                "scope": f"repository:{repo}:pull"
            })
        r.raise_for_status()
        token = r.json()["token"]
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.docker.distribution.manifest.v2+json"
        }
        manifest_url = f"https://registry-1.docker.io/v2/{repo}/manifests/{tag}"
        r = requests.get(manifest_url, headers=headers)
        r.raise_for_status()
        return r.headers.get("Docker-Content-Digest")
    except Exception as e:
        print(f"⚠️ DockerHub query failed for {image}: {e}")
        return None

def get_digest(image):
    image = normalize_image_name(image)
    if image.startswith("ghcr.io/"):
        digest = get_digest_ghcr(image)
        if digest:
            return digest
        else:
            # 降级为 DockerHub 查询
            return get_digest_dockerhub(image)
    else:
        return get_digest_dockerhub(image)

def append_to_output(image, digest):
    line = f"{image} {digest}"
    with open(OUTPUT_FILE, "a") as f:
        f.write(line + "\n")
    print(f"✅ {line}")

def process_zip(url):
    images = set()
    try:
        r = requests.get(url)
        r.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            for name in z.namelist():
                if re.search(r'/Apps/[^/]+/docker-compose\.ya?ml$', name):
                    with z.open(name) as f:
                        content = f.read()
                        imgs = parse_images_from_compose(content)
                        images.update(imgs)
    except Exception as e:
        print(f"⚠️ Error processing zip {url}: {e}")
    return images

def main():
    existing = set()
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r") as f:
            for line in f:
                parts = line.strip().split(" ")
                if parts:
                    existing.add(parts[0])

    all_images = set()
    for url in ZIP_URLS:
        print(f"📦 Downloading: {url}")
        imgs = process_zip(url)
        all_images.update(imgs)

    for image in sorted(all_images):
        if image in existing:
            continue
        digest = get_digest(image)
        if digest:
            append_to_output(image, digest)

if __name__ == "__main__":
    main()

