#!/usr/bin/env python3
"""Validate AppStore compose files and emit a structured JSON report."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import yaml


NAME_PATTERN = re.compile(r"^[a-z0-9_-]+$")
REVERSE_DOMAIN_PATTERN = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*(?:\.[a-z0-9]+(?:[._-][a-z0-9]+)*)+$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate AppStore compose files")
    parser.add_argument("--app-path", default="", help="Optional app folder name under Apps/")
    parser.add_argument("--report-json", required=True, help="Output JSON report path")
    parser.add_argument("--skip-compose-config", action="store_true", help="Skip docker compose config validation")
    return parser.parse_args()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_xcasaos_id(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def valid_reverse_domain_app_id(value: str) -> bool:
    return bool(REVERSE_DOMAIN_PATTERN.fullmatch(value))


def issue(severity: str, code: str, file_path: Path, message: str, suggestion: str, details: str = "") -> dict[str, str]:
    payload = {
        "severity": severity,
        "code": code,
        "file": file_path.as_posix(),
        "message": message,
        "suggestion": suggestion,
    }
    if details:
        payload["details"] = details
    return payload


def discover_compose_files(search_root: Path) -> list[Path]:
    return sorted(
        path
        for path in search_root.rglob("*")
        if path.is_file() and path.name in {"docker-compose.yml", "docker-compose.yaml"}
    )


def load_yaml(file_path: Path) -> dict:
    data = yaml.safe_load(file_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Compose file must parse to a mapping object.")
    return data


def validate_name(compose_data: dict, file_path: Path) -> list[dict[str, str]]:
    issues = []
    name_value = compose_data.get("name")
    if not isinstance(name_value, str) or not NAME_PATTERN.fullmatch(name_value.strip()):
        issues.append(
            issue(
                "error",
                "INVALID_COMPOSE_NAME",
                file_path,
                "Top-level `name` must match ^[a-z0-9_-]+$.",
                "Set the top-level `name` field to a lowercase identifier using letters, digits, `_`, or `-`.",
                f"Current value: {name_value!r}",
            )
        )
    return issues


def validate_x_casaos_id(compose_data: dict, file_path: Path) -> list[dict[str, str]]:
    issues = []
    xcasaos = compose_data.get("x-casaos")
    if not isinstance(xcasaos, dict):
        issues.append(
            issue(
                "error",
                "MISSING_X_CASAOS_BLOCK",
                file_path,
                "Missing top-level `x-casaos` block.",
                "Add a top-level `x-casaos:` section with required metadata including `id`.",
            )
        )
        return issues

    app_id = normalize_xcasaos_id(xcasaos.get("id"))
    if not app_id:
        expected = file_path.parent.name.lower()
        issues.append(
            issue(
                "error",
                "MISSING_X_CASAOS_ID",
                file_path,
                "Missing required top-level `x-casaos.id`.",
                f"Add `x-casaos.id` using reverse-domain format, for example `org.icewhale.{expected}`.",
            )
        )
        return issues

    if not valid_reverse_domain_app_id(app_id):
        issues.append(
            issue(
                "error",
                "INVALID_X_CASAOS_ID",
                file_path,
                "Top-level `x-casaos.id` must use reverse-domain format.",
                "Use a stable reverse-domain identifier such as `org.example.myapp`.",
                f"Current value: {app_id}",
            )
        )
    return issues


def validate_compose_config(file_path: Path) -> tuple[bool, str]:
    process = subprocess.run(
        ["docker", "compose", "-f", str(file_path), "config", "-q"],
        capture_output=True,
        text=True,
        check=False,
    )
    output = "\n".join(part for part in [process.stdout.strip(), process.stderr.strip()] if part).strip()
    return process.returncode == 0, output


def build_report(report_path: Path, app_path: str, compose_files: list[Path], issues: list[dict[str, str]]) -> dict:
    error_count = sum(1 for item in issues if item.get("severity") == "error")
    warning_count = sum(1 for item in issues if item.get("severity") == "warning")
    status = "failed" if error_count else ("warning" if warning_count else "success")
    return {
        "title": "Compose Validation Report",
        "kind": "validation",
        "status": status,
        "started_at": report_path.stem,
        "finished_at": now_iso(),
        "summary": {
            "files_total": len(compose_files),
            "files_failed": len({item["file"] for item in issues if item.get("severity") == "error"}),
            "issues_total": len(issues),
            "errors_total": error_count,
            "warnings_total": warning_count,
        },
        "context": {
            "search_root": f"Apps/{app_path}" if app_path else "Apps",
            "report_json": report_path.as_posix(),
        },
        "issues": issues,
        "artifacts": [
            {
                "name": "validation-report.json",
                "path": report_path.as_posix(),
                "note": "Upload this file as a workflow artifact for debugging and HTML rendering.",
            }
        ],
    }


def main() -> int:
    args = parse_args()
    started_at = now_iso()
    search_root = Path("Apps") / args.app_path if args.app_path else Path("Apps")
    compose_files = discover_compose_files(search_root)
    issues: list[dict[str, str]] = []

    if not search_root.exists():
        issues.append(
            issue(
                "error",
                "SEARCH_ROOT_NOT_FOUND",
                search_root,
                "Requested search root does not exist.",
                "Check the `app-path` input and make sure the app folder exists under `Apps/`.",
            )
        )
    elif not compose_files:
        issues.append(
            issue(
                "error",
                "NO_COMPOSE_FILES_FOUND",
                search_root,
                "No docker-compose.yml or docker-compose.yaml files were found.",
                "Add a compose file under the selected app folder or validate the `app-path` input.",
            )
        )

    for file_path in compose_files:
        try:
            compose_data = load_yaml(file_path)
        except Exception as exc:
            issues.append(
                issue(
                    "error",
                    "INVALID_YAML",
                    file_path,
                    "Compose file could not be parsed as YAML.",
                    "Fix the YAML syntax and re-run validation.",
                    str(exc),
                )
            )
            continue

        issues.extend(validate_name(compose_data, file_path))
        issues.extend(validate_x_casaos_id(compose_data, file_path))

        if not args.skip_compose_config:
            ok, output = validate_compose_config(file_path)
            if not ok:
                issues.append(
                    issue(
                        "error",
                        "DOCKER_COMPOSE_CONFIG_FAILED",
                        file_path,
                        "`docker compose config -q` failed for this file.",
                        "Run `docker compose -f <file> config -q` locally and fix the reported compose syntax or interpolation error.",
                        output,
                    )
                )

    report_path = Path(args.report_json)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = build_report(report_path, args.app_path, compose_files, issues)
    report["started_at"] = started_at
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Validation report written to {report_path}")
    for item in issues:
        print(f"[{item['severity'].upper()}] {item['code']}: {item['file']} - {item['message']}")

    return 1 if any(item.get("severity") == "error" for item in issues) else 0


if __name__ == "__main__":
    raise SystemExit(main())
