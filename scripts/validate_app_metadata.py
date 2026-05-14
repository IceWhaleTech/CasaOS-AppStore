#!/usr/bin/env python3
"""Validate CasaOS app compose metadata and legacy appfile metadata.

The checker is intentionally local-first. Network checks are optional because
GitHub/CDN reachability can depend on the operator's proxy setup.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - exercised by operators.
    raise SystemExit("PyYAML is required. Install it with: python3 -m pip install PyYAML") from exc


REQUIRED_ROOT_FIELDS = ("version", "updateAt", "releaseNotes", "website", "repo", "support", "docs")
NON_EMPTY_ROOT_FIELDS = ("version", "updateAt")
LINK_ROOT_FIELDS = ("website", "repo", "support", "docs")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass(frozen=True)
class Issue:
    app: str
    file: str
    severity: str
    category: str
    field: str
    expected: str
    actual: str
    detail: str

    def to_row(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class ValidationResult:
    issues: list[Issue]
    traces: list[dict[str, str]]
    summary: dict[str, int]


def relpath(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, dict):
        return not any(not blank(item) for item in value.values())
    if isinstance(value, list):
        return not any(not blank(item) for item in value)
    return False


def stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def is_http_url(value: str) -> bool:
    parsed = urllib.parse.urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def split_image_ref(image: str) -> tuple[str, str]:
    image = (image or "").strip()
    if not image:
        return "", ""
    if "@" in image:
        repo, digest = image.split("@", 1)
        return repo, digest

    last_slash = image.rfind("/")
    last_colon = image.rfind(":")
    if last_colon > last_slash:
        return image[:last_colon], image[last_colon + 1 :]
    return image, "latest"


def normalize_image_repo(repo: str) -> str:
    repo = (repo or "").strip().lower()
    for prefix in ("docker.io/", "index.docker.io/"):
        if repo.startswith(prefix):
            repo = repo[len(prefix) :]
    if repo.startswith("library/"):
        repo = repo[len("library/") :]
    if repo.startswith("lscr.io/linuxserver/"):
        repo = "linuxserver/" + repo[len("lscr.io/linuxserver/") :]
    return repo


def image_parts(image: str) -> tuple[str, str]:
    repo, tag = split_image_ref(image)
    return normalize_image_repo(repo), tag


def parse_update_at(value: Any) -> datetime | None:
    if not isinstance(value, str) or not DATE_RE.match(value):
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def add_issue(
    issues: list[Issue],
    app: str,
    file: str,
    severity: str,
    category: str,
    field: str,
    expected: Any,
    actual: Any,
    detail: str,
) -> None:
    issues.append(
        Issue(
            app=app,
            file=file,
            severity=severity,
            category=category,
            field=field,
            expected=stringify(expected),
            actual=stringify(actual),
            detail=detail,
        )
    )


def service_port_targets(ports: Any) -> set[str]:
    targets: set[str] = set()
    if not isinstance(ports, list):
        return targets
    for item in ports:
        if isinstance(item, dict):
            target = item.get("target")
            if target is not None:
                targets.add(str(target))
        elif isinstance(item, str):
            port = item.split("/", 1)[0]
            targets.add(port.rsplit(":", 1)[-1])
    return targets


def service_volume_targets(volumes: Any) -> set[str]:
    targets: set[str] = set()
    if not isinstance(volumes, list):
        return targets
    for item in volumes:
        if isinstance(item, dict):
            target = item.get("target")
            if target:
                targets.add(str(target))
        elif isinstance(item, str):
            parts = item.split(":")
            if len(parts) == 1:
                targets.add(parts[0])
            elif len(parts) >= 2:
                targets.add(parts[1])
    return targets


def service_env_keys(environment: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(environment, dict):
        keys.update(str(key) for key in environment)
    elif isinstance(environment, list):
        for item in environment:
            if isinstance(item, str):
                keys.add(item.split("=", 1)[0])
    return keys


def metadata_containers(items: Any) -> set[str]:
    values: set[str] = set()
    if not isinstance(items, list):
        return values
    for item in items:
        if isinstance(item, dict):
            for key in ("container", "name", "key", "target"):
                if key in item and item[key] is not None:
                    values.add(str(item[key]))
                    break
    return values


def local_asset_from_url(url: str, root: Path) -> Path | None:
    parsed = urllib.parse.urlparse(url)
    if parsed.netloc == "cdn.jsdelivr.net" and "/gh/IceWhaleTech/CasaOS-AppStore@" in parsed.path:
        marker = "/Apps/"
        if marker in parsed.path:
            return root / "Apps" / parsed.path.split(marker, 1)[1]
    if parsed.netloc == "raw.githubusercontent.com":
        parts = parsed.path.strip("/").split("/")
        if len(parts) >= 5 and parts[0:2] == ["IceWhaleTech", "CasaOS-AppStore"] and parts[3] == "Apps":
            return root / "Apps" / "/".join(parts[4:])
    return None


def collect_appfile_urls(appfile: dict[str, Any]) -> list[tuple[str, str]]:
    urls: list[tuple[str, str]] = []
    for field in ("icon", "thumbnail"):
        value = appfile.get(field)
        if isinstance(value, str) and value:
            urls.append((field, value))
    screenshots = appfile.get("screenshots")
    if isinstance(screenshots, list):
        for index, value in enumerate(screenshots):
            if isinstance(value, str) and value:
                urls.append((f"screenshots[{index}]", value))
    return urls


def check_url(url: str, timeout: int) -> tuple[bool, str]:
    request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "CasaOS-AppStore-validator/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status < 400, str(response.status)
    except urllib.error.HTTPError as exc:
        if exc.code in {403, 405}:
            try:
                get_request = urllib.request.Request(url, headers={"User-Agent": "CasaOS-AppStore-validator/1.0"})
                with urllib.request.urlopen(get_request, timeout=timeout) as response:
                    return response.status < 400, str(response.status)
            except Exception as get_exc:  # noqa: BLE001 - report the original URL failure.
                return False, f"{type(get_exc).__name__}: {get_exc}"
        return False, str(exc.code)
    except Exception as exc:  # noqa: BLE001 - validation report should include network/proxy failures.
        return False, f"{type(exc).__name__}: {exc}"


def validate_root_metadata(
    app: str,
    compose_file: str,
    metadata: Any,
    main_service: dict[str, Any] | None,
    issues: list[Issue],
) -> tuple[str, str, str, str]:
    main_image = ""
    image_tag = ""
    version = ""
    update_at = ""

    if not isinstance(metadata, dict):
        add_issue(issues, app, compose_file, "error", "root_x_casaos_missing", "x-casaos", "mapping", metadata, "Root x-casaos metadata is missing or invalid.")
        return main_image, image_tag, version, update_at

    for field in REQUIRED_ROOT_FIELDS:
        if field not in metadata:
            add_issue(issues, app, compose_file, "error", "required_field_missing", f"x-casaos.{field}", "present", "", "Required root metadata field is missing.")
            continue
        if metadata[field] is None:
            add_issue(issues, app, compose_file, "error", "required_field_null", f"x-casaos.{field}", "non-null", None, "Required root metadata field is null.")
        elif field in NON_EMPTY_ROOT_FIELDS and blank(metadata[field]):
            add_issue(issues, app, compose_file, "error", "required_field_empty", f"x-casaos.{field}", "non-empty", metadata[field], "Required root metadata field is empty.")

    for field in LINK_ROOT_FIELDS:
        value = metadata.get(field)
        if isinstance(value, str) and value.strip() and not is_http_url(value.strip()):
            add_issue(issues, app, compose_file, "error", "url_format", f"x-casaos.{field}", "http(s) URL or empty string", value, "Non-empty link field is not a valid http(s) URL.")

    version = str(metadata.get("version") or "")
    update_at = str(metadata.get("updateAt") or "")
    if metadata.get("updateAt") is not None and parse_update_at(metadata.get("updateAt")) is None:
        add_issue(issues, app, compose_file, "error", "updateAt_format", "x-casaos.updateAt", "YYYY-MM-DD", metadata.get("updateAt"), "updateAt must be a real date in YYYY-MM-DD format.")

    if main_service:
        main_image = str(main_service.get("image") or "")
        if not main_image:
            add_issue(issues, app, compose_file, "error", "main_image_missing", "services.<main>.image", "present", "", "Main service image is missing.")
        image_repo, image_tag = split_image_ref(main_image)
        if image_tag and version and version != image_tag:
            add_issue(issues, app, compose_file, "error", "version_image_mismatch", "x-casaos.version", image_tag, version, "Root version does not match the main image tag or digest.")
    return main_image, image_tag, version, update_at


def validate_service_metadata(
    app: str,
    compose_file: str,
    main_service: dict[str, Any],
    issues: list[Issue],
) -> None:
    service_meta = main_service.get("x-casaos") or {}
    if not isinstance(service_meta, dict):
        service_meta = {}

    checks = (
        ("ports", service_port_targets(main_service.get("ports")), metadata_containers(service_meta.get("ports")), "service_metadata_port_gap"),
        ("volumes", service_volume_targets(main_service.get("volumes")), metadata_containers(service_meta.get("volumes")), "service_metadata_volume_gap"),
        ("envs", service_env_keys(main_service.get("environment")), metadata_containers(service_meta.get("envs")), "service_metadata_env_gap"),
    )
    for field, actual, documented, category in checks:
        missing = sorted(actual - documented)
        if missing:
            add_issue(
                issues,
                app,
                compose_file,
                "warning",
                category,
                f"services.<main>.x-casaos.{field}",
                sorted(actual),
                sorted(documented),
                "Compose declares values not fully represented in service-level x-casaos metadata.",
            )


def validate_appfile(
    root: Path,
    app: str,
    app_dir: Path,
    appfile_path: Path,
    main_image: str,
    update_at: str,
    issues: list[Issue],
) -> list[tuple[str, str]]:
    appfile_rel = relpath(appfile_path, root)
    try:
        appfile = json.loads(appfile_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        add_issue(issues, app, appfile_rel, "error", "appfile_json_error", "appfile.json", "valid JSON", f"line {exc.lineno}: {exc.msg}", "appfile.json cannot be parsed.")
        return []

    if not isinstance(appfile, dict):
        add_issue(issues, app, appfile_rel, "error", "appfile_json_error", "appfile.json", "JSON object", type(appfile).__name__, "appfile.json root must be an object.")
        return []

    container = appfile.get("container")
    appfile_image = container.get("image") if isinstance(container, dict) else None
    if isinstance(appfile_image, str) and main_image:
        compose_repo, compose_tag = image_parts(main_image)
        appfile_repo, appfile_tag = image_parts(appfile_image)
        if compose_repo != appfile_repo:
            add_issue(issues, app, appfile_rel, "error", "appfile_image_repository_mismatch", "container.image", compose_repo, appfile_repo, "appfile image repository does not match compose main image repository.")
        if compose_tag != appfile_tag:
            add_issue(issues, app, appfile_rel, "error", "appfile_image_tag_mismatch", "container.image", compose_tag, appfile_tag, "appfile image tag does not match compose main image tag.")

    latest_update_date = appfile.get("latest_update_date")
    parsed_update_at = parse_update_at(update_at)
    if latest_update_date not in (None, "") and parsed_update_at is not None:
        try:
            appfile_date = datetime.fromtimestamp(int(str(latest_update_date)), tz=timezone.utc).date()
            if appfile_date != parsed_update_at.date():
                add_issue(
                    issues,
                    app,
                    appfile_rel,
                    "warning",
                    "appfile_update_date_mismatch",
                    "latest_update_date",
                    parsed_update_at.date().isoformat(),
                    appfile_date.isoformat(),
                    "appfile latest_update_date does not match compose x-casaos.updateAt.",
                )
        except (TypeError, ValueError):
            add_issue(issues, app, appfile_rel, "warning", "appfile_update_date_invalid", "latest_update_date", "unix timestamp", latest_update_date, "appfile latest_update_date is not a unix timestamp.")

    urls = collect_appfile_urls(appfile)
    for field, url in urls:
        if not is_http_url(url):
            add_issue(issues, app, appfile_rel, "error", "asset_url_format", field, "http(s) URL", url, "appfile asset URL is not a valid http(s) URL.")
            continue
        local_asset = local_asset_from_url(url, root)
        if local_asset is not None and not local_asset.exists():
            add_issue(issues, app, appfile_rel, "error", "asset_missing", field, relpath(local_asset, root), url, "CasaOS-AppStore CDN asset points to a file missing from this repository.")
    return urls


def validate_repo(root: str | Path, check_links: bool = False, timeout: int = 8) -> ValidationResult:
    root = Path(root)
    compose_files = sorted((root / "Apps").glob("*/docker-compose.yml"), key=lambda path: path.parent.name.lower())
    issues: list[Issue] = []
    traces: list[dict[str, str]] = []
    checked_links = 0
    bad_links = 0

    for compose_path in compose_files:
        app = compose_path.parent.name
        compose_file = relpath(compose_path, root)
        before_count = len(issues)
        parse_status = "ok"
        main_name = ""
        main_image = ""
        image_tag = ""
        version = ""
        update_at = ""
        blank_link_fields: list[str] = []
        link_values: list[tuple[str, str]] = []

        try:
            data = yaml.safe_load(compose_path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001 - report parser failure.
            parse_status = "error"
            add_issue(issues, app, compose_file, "error", "compose_yaml_error", "docker-compose.yml", "valid YAML", f"{type(exc).__name__}: {exc}", "Compose file cannot be parsed.")
            data = None

        if isinstance(data, dict):
            services = data.get("services")
            metadata = data.get("x-casaos")
            if not isinstance(services, dict):
                add_issue(issues, app, compose_file, "error", "services_missing", "services", "mapping", services, "Compose services block is missing or invalid.")
                services = {}
            if isinstance(metadata, dict):
                main_name = str(metadata.get("main") or "")
            if not main_name:
                add_issue(issues, app, compose_file, "error", "main_missing", "x-casaos.main", "service name", main_name, "Root x-casaos.main is missing.")
            main_service = services.get(main_name) if main_name else None
            if main_name and not isinstance(main_service, dict):
                add_issue(issues, app, compose_file, "error", "main_service_missing", "x-casaos.main", sorted(services), main_name, "Root x-casaos.main does not point to an existing service.")
                main_service = None

            main_image, image_tag, version, update_at = validate_root_metadata(app, compose_file, metadata, main_service, issues)
            if isinstance(metadata, dict):
                for field in LINK_ROOT_FIELDS:
                    value = metadata.get(field)
                    if value == "":
                        blank_link_fields.append(field)
                    elif isinstance(value, str) and value.strip():
                        link_values.append((f"x-casaos.{field}", value.strip()))
            if main_service:
                validate_service_metadata(app, compose_file, main_service, issues)

            appfile_path = compose_path.parent / "appfile.json"
            if appfile_path.exists():
                link_values.extend(validate_appfile(root, app, compose_path.parent, appfile_path, main_image, update_at, issues))

            if check_links:
                for field, url in link_values:
                    if local_asset_from_url(url, root) is not None:
                        continue
                    checked_links += 1
                    ok, status = check_url(url, timeout)
                    if not ok:
                        bad_links += 1
                        add_issue(issues, app, compose_file, "warning", "url_unreachable", field, "HTTP status < 400", status, "URL did not pass optional network reachability check.")

        app_issues = issues[before_count:]
        errors = sum(1 for issue in app_issues if issue.severity == "error")
        warnings = sum(1 for issue in app_issues if issue.severity == "warning")
        if errors:
            status = "error"
        elif warnings:
            status = "warning"
        elif blank_link_fields:
            status = "ok_with_blank_fields"
        else:
            status = "ok"
        traces.append(
            {
                "app": app,
                "compose_path": compose_file,
                "parse_status": parse_status,
                "main_service": main_name,
                "main_image": main_image,
                "image_tag": image_tag,
                "metadata_version": version,
                "updateAt": update_at,
                "blank_link_fields": ";".join(blank_link_fields),
                "status": status,
                "error_count": str(errors),
                "warning_count": str(warnings),
                "issue_categories": ";".join(sorted({issue.category for issue in app_issues})),
            }
        )

    error_count = sum(1 for issue in issues if issue.severity == "error")
    warning_count = sum(1 for issue in issues if issue.severity == "warning")
    summary = {
        "apps": len(compose_files),
        "issues": len(issues),
        "errors": error_count,
        "warnings": warning_count,
        "ok_apps": sum(1 for trace in traces if trace["status"] in {"ok", "ok_with_blank_fields"}),
        "warning_apps": sum(1 for trace in traces if trace["status"] == "warning"),
        "error_apps": sum(1 for trace in traces if trace["status"] == "error"),
        "checked_links": checked_links,
        "bad_links": bad_links,
    }
    return ValidationResult(issues=issues, traces=traces, summary=summary)


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def print_summary(result: ValidationResult) -> None:
    summary = result.summary
    print(
        "apps={apps} issues={issues} errors={errors} warnings={warnings} "
        "ok_apps={ok_apps} warning_apps={warning_apps} error_apps={error_apps} "
        "checked_links={checked_links} bad_links={bad_links}".format(**summary)
    )
    categories: dict[str, int] = {}
    for issue in result.issues:
        categories[issue.category] = categories.get(issue.category, 0) + 1
    if categories:
        print("issue_categories:")
        for category, count in sorted(categories.items(), key=lambda item: (-item[1], item[0])):
            print(f"  {category}: {count}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate CasaOS AppStore compose and appfile metadata.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--issues-csv", help="Write issue rows to this CSV path.")
    parser.add_argument("--trace-csv", help="Write one validation trace row per app to this CSV path.")
    parser.add_argument("--summary-json", help="Write summary counts to this JSON path.")
    parser.add_argument("--check-links", action="store_true", help="Also perform network checks for non-local URLs.")
    parser.add_argument("--timeout", type=int, default=8, help="Per-URL network timeout for --check-links.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero on warnings as well as errors.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = validate_repo(args.root, check_links=args.check_links, timeout=args.timeout)
    print_summary(result)

    if args.issues_csv:
        write_csv(Path(args.issues_csv), [issue.to_row() for issue in result.issues], list(Issue.__dataclass_fields__))
    if args.trace_csv:
        fieldnames = [
            "app",
            "compose_path",
            "parse_status",
            "main_service",
            "main_image",
            "image_tag",
            "metadata_version",
            "updateAt",
            "blank_link_fields",
            "status",
            "error_count",
            "warning_count",
            "issue_categories",
        ]
        write_csv(Path(args.trace_csv), result.traces, fieldnames)
    if args.summary_json:
        summary_path = Path(args.summary_json)
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(json.dumps(result.summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if result.summary["errors"] or (args.strict and result.summary["warnings"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
