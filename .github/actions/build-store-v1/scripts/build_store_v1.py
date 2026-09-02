#!/usr/bin/env python3
"""Build the legacy v1 AppStore zip and emit a structured report."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


INCLUDE_FILES = [
    "category-list.json",
    "featured-apps.json",
    "recommend-list.json",
    "README.md",
]

KEEP_NAMES = {
    "category-list.json",
    "featured-apps.json",
    "recommend-list.json",
    "README.md",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build legacy AppStore v1 zip")
    parser.add_argument("--source", default=".")
    parser.add_argument("--output-zip", default="dist/store/main.zip")
    parser.add_argument("--report-json", required=True)
    parser.add_argument("--report-title", default="Build V1 Store Report")
    return parser.parse_args()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def should_keep(file_path: Path) -> bool:
    if file_path.name in KEEP_NAMES:
        return True
    if file_path.suffix in {".yaml", ".yml", ".sh"}:
        return True
    return False


def write_report(report_path: Path, report: dict) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def build_report(args: argparse.Namespace, status: str, zip_exists: bool, issues: list[dict]) -> dict:
    return {
        "title": args.report_title,
        "kind": "build-v1",
        "status": status,
        "started_at": now_iso(),
        "finished_at": now_iso(),
        "summary": {
            "zip_exists": zip_exists,
            "issues_total": len(issues),
        },
        "context": {
            "repo": os.getenv("GITHUB_REPOSITORY", ""),
            "ref": os.getenv("GITHUB_REF", ""),
            "sha": os.getenv("GITHUB_SHA", ""),
            "trigger": os.getenv("GITHUB_EVENT_NAME", ""),
            "source": args.source,
            "output_zip": args.output_zip,
        },
        "issues": issues,
        "artifacts": [
            {
                "name": "build-v1-report.json",
                "path": args.report_json,
                "note": "Upload this file as a workflow artifact for debugging and HTML rendering.",
            },
            {
                "name": "main.zip",
                "path": args.output_zip,
                "note": "Upload the generated v1 package as a workflow artifact.",
            },
        ],
    }


def main() -> int:
    args = parse_args()
    source = Path(args.source).resolve()
    output_zip = Path(args.output_zip).resolve()
    report_path = Path(args.report_json).resolve()
    started_at = now_iso()
    issues: list[dict] = []

    staging_root = Path("/tmp/appstore-v1").resolve()
    build_root = staging_root / "build"
    default_new = build_root / "sysroot/var/lib/casaos/appstore/default.new"

    try:
        if staging_root.exists():
            shutil.rmtree(staging_root)
        default_new.mkdir(parents=True, exist_ok=True)

        shutil.copytree(source / "build", build_root, dirs_exist_ok=True)
        shutil.copytree(source / "Apps", default_new / "Apps", dirs_exist_ok=True)
        for file_name in INCLUDE_FILES:
            shutil.copy2(source / file_name, default_new / file_name)

        for file_path in build_root.rglob("*"):
            if file_path.is_file() and not should_keep(file_path):
                file_path.unlink()

        output_zip.parent.mkdir(parents=True, exist_ok=True)
        if output_zip.exists():
            output_zip.unlink()

        subprocess.run(
            ["zip", "-r", str(output_zip), "build"],
            cwd=staging_root,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["unzip", "-t", str(output_zip)],
            check=True,
            capture_output=True,
            text=True,
        )

        report = build_report(args, "success", output_zip.exists(), issues)
        report["started_at"] = started_at
        write_report(report_path, report)
        print(f"Build report written to {report_path}")
        return 0

    except Exception as exc:
        issues.append(
            {
                "severity": "error",
                "code": "BUILD_V1_FAILED",
                "file": "",
                "message": "The legacy v1 package build failed.",
                "suggestion": (
                    "Check required input files under `build/`, `Apps/`, and root metadata files. "
                    "Then inspect zip/unzip output in workflow logs."
                ),
                "details": str(exc),
            }
        )
        report = build_report(args, "failed", output_zip.exists(), issues)
        report["started_at"] = started_at
        write_report(report_path, report)
        print(f"Build report written to {report_path}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
