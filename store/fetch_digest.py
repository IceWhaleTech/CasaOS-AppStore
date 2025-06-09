import os
import requests
import zipfile
import io
import yaml
from urllib.parse import urlparse
from bs4 import BeautifulSoup

ZIP_URLS = [
    "https://cdn.jsdelivr.net/gh/IceWhaleTech/CasaOS-AppStore@gh-pages/store/main.zip",
    "https://play.cuse.eu.org/Cp0204-AppStore-Play.zip",
    "https://github.com/bigbeartechworld/big-bear-casaos/archive/refs/heads/master.zip",
    "https://casaos-appstore.paodayag.dev/linuxserver.zip",
]

CACHE_FILE = "digest_cache.txt"
DIGEST_CACHE = {}

# 环境变量支持
DOCKER_USERNAME = os.getenv("DOCKER_USERNAME")
DOCKER_TOKEN = os.getenv("DOCKER_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# 读取已有缓存
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) == 2:
                DIGEST_CACHE[parts[0]] = parts[1]

def normalize_image(image):
    image = image.strip()
    if "@sha256:" in image:
        return image  # Already has digest
    for prefix in ["docker.io/", "ghcr.io/", "lscr.io/"]:
        if image.startswith(prefix):
            image = image[len(prefix):]
    if "/" not in image.split(":")[0]:
        image = "library/" + image
    if ":" not in image:
        image += ":latest"
    return image

def is_latest_tag(image):
    return image.endswith(":latest") or ":" not in image

def get_dockerhub_digest(image):
    repo, _, tag = image.partition(":")
    if not tag:
        tag = "latest"

    headers = {
        "Accept": "application/vnd.docker.distribution.manifest.v2+json"
    }

    r = requests.get(f"https://auth.docker.io/token?service=registry.docker.io&scope=repository:{repo}:pull",
                     auth=(DOCKER_USERNAME, DOCKER_TOKEN) if DOCKER_USERNAME and DOCKER_TOKEN else None)
    if r.status_code != 200:
        return None
    token = r.json().get("token")
    headers["Authorization"] = f"Bearer {token}"

    r = requests.head(f"https://registry-1.docker.io/v2/{repo}/manifests/{tag}", headers=headers)
    if r.status_code == 401:
        return None
    r.raise_for_status()
    return r.headers.get("Docker-Content-Digest")

def get_ghcr_digest(image):
    repo, _, tag = image.partition(":")
    if not tag:
        tag = "latest"
    headers = {
        "Accept": "application/vnd.docker.distribution.manifest.v2+json",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    try:
        r = requests.head(f"https://ghcr.io/v2/{repo}/manifests/{tag}", headers=headers)
        if r.status_code in [401, 403]:
            # fallback to GitHub pkg page scrape
            print(f"🔁 Falling back to GitHub page scrape for {repo}:{tag}")
            return get_digest_from_github_page(repo, tag)
        r.raise_for_status()
        return r.headers.get("Docker-Content-Digest")
    except Exception:
        return None

def get_digest_from_github_page(repo, tag):
    try:
        print(f"🌐 Scraping GitHub page for {repo}:{tag}")
        ghcr_url = f"https://ghcr.io/{repo}"
        r = requests.get(ghcr_url, allow_redirects=False)
        if r.status_code not in (301, 302):
            return None
        github_url = r.headers.get("Location")
        if not github_url:
            return None
        print(f"➡️ Redirected to: {github_url}")

        pkg_page = requests.get(github_url)
        soup = BeautifulSoup(pkg_page.text, "html.parser")
        tag_links = soup.find_all("a", class_="Label mr-1 mb-2 text-normal")
        for a in tag_links:
            if a.text.strip() == tag:
                detail_url = f"https://github.com{a['href']}"
                print(f"🔍 Visiting tag detail page: {detail_url}")
                detail_page = requests.get(detail_url)
                detail_soup = BeautifulSoup(detail_page.text, "html.parser")
                code = detail_soup.find("code")
                if code and code.text.startswith("sha256:"):
                    return code.text.strip()
        return None
    except Exception as e:
        print(f"❌ GitHub page scrape failed: {e}")
        return None

def get_digest(image):
    image = normalize_image(image)
    if "@sha256:" in image:
        return image.split("@")[-1]  # already has digest
    force_update = is_latest_tag(image)

    if image in DIGEST_CACHE and not force_update:
        return DIGEST_CACHE[image]

    digest = None
    if image.startswith("ghcr.io/"):
        digest = get_ghcr_digest(image[len("ghcr.io/" ):])
        if not digest:
            digest = get_dockerhub_digest(image)
    else:
        digest = get_dockerhub_digest(image)

    if digest:
        DIGEST_CACHE[image] = digest
        with open(CACHE_FILE, "a") as f:
            f.write(f"{image} {digest}\n")
    return digest

def extract_images_from_yaml(content):
    try:
        yml = yaml.safe_load(content)
        services = yml.get("services", {})
        return [svc.get("image") for svc in services.values() if "image" in svc]
    except Exception:
        return []

def process_zip(url):
    print(f"📦 Downloading zip from {url}")
    r = requests.get(url)
    r.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        for zipinfo in z.infolist():
            if zipinfo.filename.endswith("docker-compose.yml") and "/Apps/" in zipinfo.filename:
                try:
                    with z.open(zipinfo.filename) as f:
                        content = f.read().decode()
                        images = extract_images_from_yaml(content)
                        for image in images:
                            if not image:
                                continue
                            digest = get_digest(image)
                            if digest:
                                print(f"🔍 {image} -> {digest}")
                            else:
                                print(f"⚠️ Failed to get digest for {image}")
                except Exception as e:
                    print(f"❌ Failed to process {zipinfo.filename}: {e}")

if __name__ == "__main__":
    for zip_url in ZIP_URLS:
        process_zip(zip_url)

