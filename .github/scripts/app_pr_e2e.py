#!/usr/bin/env python3
"""Select PR Compose data and publish reports without executing PR code."""

import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import urllib.parse
import urllib.request
import zipfile


API = os.environ.get("GITHUB_API_URL", "https://api.github.com")
REPO = os.environ.get("GITHUB_REPOSITORY", "")
MARKER = "<!-- app-pr-e2e-report -->"
COMPOSE_NAMES = {"docker-compose.yml", "docker-compose.yaml"}


def api(path, payload=None, method=None):
    request = urllib.request.Request(
        API + path,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Authorization": "Bearer " + os.environ["GH_TOKEN"],
                 "Accept": "application/vnd.github+json",
                 "Content-Type": "application/json"},
        method=method,
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def pages(path):
    result = []
    for page in range(1, 101):
        batch = api(path + ("&" if "?" in path else "?") + f"per_page=100&page={page}")
        result.extend(batch)
        if len(batch) < 100:
            return result
    raise ValueError("API pagination limit exceeded")


def selected(files):
    apps = {}
    for item in files:
        path = PurePosixPath(item["filename"])
        if len(path.parts) != 3 or path.parts[0] != "Apps" or path.name not in COMPOSE_NAMES:
            continue
        if any(part in {".", ".."} for part in path.parts):
            raise ValueError("Unsafe application path")
        name = str(path)
        apps[name] = {"path": name, "app": path.parts[1],
                      "key": "app-" + hashlib.sha256(name.encode()).hexdigest()[:24],
                      "status": "DELETED" if item["status"] == "removed" else "PENDING"}
    if len(apps) > 100:
        raise ValueError("More than 100 changed Compose files; split the PR")
    return [apps[name] for name in sorted(apps)]


def prepare():
    number = os.environ["PR_NUMBER"]
    if not re.fullmatch(r"[1-9][0-9]*", number):
        raise ValueError("Expected a PR number")
    pr = api(f"/repos/{REPO}/pulls/{number}")
    if pr["state"] != "open":
        raise ValueError("PR is not open")
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    if "pull_request" in event and event["pull_request"]["head"]["sha"] != pr["head"]["sha"]:
        raise ValueError("PR changed before preparation; use the newer run")
    files = pages(f"/repos/{REPO}/pulls/{number}/files")
    if len(files) != pr["changed_files"]:
        raise ValueError("Incomplete PR file list")
    apps = selected(files)
    root = Path("out/app-e2e")
    root.mkdir(parents=True, exist_ok=True)
    for app in apps:
        if app["status"] == "DELETED":
            continue
        source = api(f"/repos/{REPO}/contents/{urllib.parse.quote(app['path'], safe='/')}?ref={pr['head']['sha']}")
        if source.get("type") != "file" or source.get("size", 0) not in range(1, 4 * 1024 * 1024 + 1):
            raise ValueError("Compose must be a regular file of at most 4 MiB")
        import base64
        data = base64.b64decode(source["content"], validate=False)
        if len(data) != source["size"]:
            # GitHub's Contents API omits inline content for large files.
            raise ValueError("Compose exceeds GitHub inline-content limit")
        target = root / app["key"]
        target.mkdir()
        (target / "compose.yaml").write_bytes(data)
    manifest = {"pr": int(number), "sha": pr["head"]["sha"], "apps": apps}
    (root / "manifest.json").write_text(json.dumps(manifest))
    matrix = {"include": [{"key": app["key"]} for app in apps if app["status"] == "PENDING"]}
    with open(os.environ["GITHUB_OUTPUT"], "a") as output:
        output.write("matrix=" + json.dumps(matrix) + "\n")
        output.write("has-apps=" + str(bool(matrix["include"])).lower() + "\n")


def manifest_from_artifact(artifact):
    # Download data only. Never extract archive paths or execute artifact contents.
    class ArtifactRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, request, fp, code, msg, headers, newurl):
            redirected = super().redirect_request(request, fp, code, msg, headers, newurl)
            if redirected is not None:
                redirected.remove_header("Authorization")
                if urllib.parse.urlparse(newurl).scheme != "https":
                    raise ValueError("Artifact redirect must use HTTPS")
            return redirected

    request = urllib.request.Request(
        API + f"/repos/{REPO}/actions/artifacts/{artifact['id']}/zip",
        headers={"Authorization": "Bearer " + os.environ["GH_TOKEN"]},
    )
    with urllib.request.build_opener(ArtifactRedirect()).open(request, timeout=60) as response:
        data = response.read(16 * 1024 * 1024 + 1)
    if len(data) > 16 * 1024 * 1024:
        raise ValueError("Input archive too large for report")
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        matches = [info for info in archive.infolist() if info.filename == "manifest.json"]
        if len(matches) != 1 or matches[0].file_size > 128 * 1024:
            raise ValueError("Invalid manifest")
        return json.loads(archive.read(matches[0]))


def validate():
    import yaml
    root = Path("out/app-e2e")
    manifest = json.loads((root / "manifest.json").read_text())
    reports = Path("out/app-e2e-validation")
    reports.mkdir(parents=True, exist_ok=True)
    failed = False
    for app in manifest["apps"]:
        if app["status"] == "DELETED":
            continue
        path = root / app["key"] / "compose.yaml"
        data = yaml.safe_load(path.read_bytes())
        errors = []
        if not isinstance(data, dict) or not isinstance(data.get("services"), dict) or not data["services"]:
            errors.append("Compose must define services")
        else:
            for service in data["services"].values():
                if not isinstance(service, dict):
                    errors.append("Invalid service")
                    continue
                if any(key in service for key in ("build", "env_file", "extends")):
                    errors.append("Compose must be self-contained (no build/env_file/extends)")
            if "include" in data:
                errors.append("Compose include is not supported")
        if not errors:
            result = subprocess.run(["docker", "compose", "--project-name", "app-e2e", "-f", str(path), "config", "-q"],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
            if result.returncode:
                errors.append("docker compose config failed")
        (reports / (app["key"] + ".json")).write_text(json.dumps({"path": app["path"], "errors": errors}))
        if errors:
            print(app["key"] + ": " + "; ".join(errors))
            failed = True
    if failed:
        raise SystemExit("Selected Compose validation failed; no VM tests were started")


def cell(value):
    import html
    return html.escape(str(value)).replace("|", "&#124;").replace("\n", " ").replace("\r", " ").replace("`", "&#96;")


def render(apps, jobs, artifacts, run):
    lines = [MARKER, "## Application Lifecycle E2E", "",
             f"Commit: `{run['tested_sha']}` · Run: [#{run['run_number']}]({run['html_url']})",
             f"Conclusion: **{cell(run['conclusion'])}**", "",
             "Suite: `bbot-cli-install@2.0.0` / `CLI-LIFECYCLE-01` · ZimaOS `1.8.0-beta2`",
             "Scope: install, application running status with completed installation, stop, start, restart, uninstall (not Docker health or business/UI readiness).", "",
             "| Application | Result | Evidence |", "| --- | --- | --- |"]
    for app in apps:
        if app["status"] == "DELETED":
            status, evidence = "DELETED (not tested)", "-"
        else:
            matches = [job for job in jobs if f"E2E {app['key']} / " in job["name"]]
            evidence_name = f"app-e2e-evidence-{run['run_attempt']}-{app['key']}"
            found = [a for a in artifacts if a["name"] == evidence_name and not a["expired"]]
            conclusion = matches[0]["conclusion"] if len(matches) == 1 else None
            status = {"success": "PASS", "failure": "FAIL / ERROR", "cancelled": "CANCELLED",
                      "skipped": "BLOCKED / SKIPPED", "timed_out": "TIMEOUT"}.get(conclusion, "ERROR (missing/ambiguous job)")
            if conclusion == "success" and len(found) != 1:
                status = "ERROR (missing evidence)"
            evidence = f"[Artifact]({run['html_url']}/artifacts/{found[0]['id']})" if len(found) == 1 else "Unavailable"
        lines.append(f"| {cell(app['path'])} | {status} | {evidence} |")
    if not apps:
        lines.append("| No changed application Compose | NOT REQUIRED | - |")
    lines.extend(["", "Readiness requires application status running with completed installation; Docker healthchecks and a stability timer are not required. See job logs for the failing phase.",
                  f"<!-- source-run:{run['id']} attempt:{run['run_attempt']} -->"])
    return "\n".join(lines)


def report():
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    run = api(f"/repos/{REPO}/actions/runs/{event['workflow_run']['id']}")
    if run["repository"]["full_name"] != REPO or run["path"] != ".github/workflows/app-pr-e2e.yml":
        raise ValueError("Unexpected source workflow")
    if run["event"] not in {"pull_request", "workflow_dispatch"}:
        raise ValueError("Unexpected source event")
    artifacts = api(f"/repos/{REPO}/actions/runs/{run['id']}/artifacts?per_page=100")["artifacts"]
    # At most 100 apps plus manifest; do not silently truncate.
    if len(artifacts) == 100:
        artifacts += api(f"/repos/{REPO}/actions/runs/{run['id']}/artifacts?per_page=100&page=2")["artifacts"]
    inputs = [a for a in artifacts if a["name"] == f"app-e2e-manifest-{run['run_attempt']}"]
    manifest = manifest_from_artifact(inputs[0]) if len(inputs) == 1 else None
    prs = run["pull_requests"]
    if not prs and run["event"] == "pull_request":
        associated = pages(f"/repos/{REPO}/commits/{run['head_sha']}/pulls")
        prs = [p for p in associated if p["head"]["sha"] == run["head_sha"]]
    if manifest:
        number, sha = manifest["pr"], manifest["sha"]
        if not isinstance(number, int) or not re.fullmatch(r"[0-9a-f]{40}", sha):
            raise ValueError("Invalid PR identity")
        if run["event"] == "pull_request" and not any(p["number"] == number and p["head"]["sha"] == sha for p in prs):
            raise ValueError("Manifest does not match source PR")
    elif len(prs) == 1:
        number, sha = prs[0]["number"], prs[0]["head"]["sha"]
    else:
        raise ValueError("No authenticated PR identity; inspect preparation logs")
    pr = api(f"/repos/{REPO}/pulls/{number}")
    if pr["state"] != "open" or pr["head"]["sha"] != sha:
        print("Ignoring results for a closed PR or outdated head")
        return
    files = pages(f"/repos/{REPO}/pulls/{number}/files")
    if len(files) != pr["changed_files"]:
        raise ValueError("Incomplete file list")
    apps = selected(files)
    run["tested_sha"] = sha
    # Jobs endpoints return an envelope, unlike issue/comment list endpoints.
    jobs = []
    for page in range(1, 101):
        batch = api(f"/repos/{REPO}/actions/runs/{run['id']}/attempts/{run['run_attempt']}/jobs?per_page=100&page={page}")["jobs"]
        jobs.extend(batch)
        if len(batch) < 100:
            break
    body = render(apps, jobs, artifacts, run)
    comments = pages(f"/repos/{REPO}/issues/{number}/comments")
    existing = [c for c in comments if c["user"]["login"] == "github-actions[bot]" and c["body"].startswith(MARKER)]
    # Recheck after all network reads, immediately before the write.
    current = api(f"/repos/{REPO}/pulls/{number}")
    if current["state"] != "open" or current["head"]["sha"] != sha:
        return
    if existing:
        comment = existing[-1]
        prior = re.search(r"source-run:(\d+) attempt:(\d+)", comment["body"])
        if prior and (int(prior[1]), int(prior[2])) > (run["id"], run["run_attempt"]):
            print("Ignoring older run")
            return
        api(f"/repos/{REPO}/issues/comments/{comment['id']}", {"body": body}, "PATCH")
    else:
        api(f"/repos/{REPO}/issues/{number}/comments", {"body": body}, "POST")


if __name__ == "__main__":
    {"prepare": prepare, "validate": validate, "report": report}[sys.argv[1]]()
