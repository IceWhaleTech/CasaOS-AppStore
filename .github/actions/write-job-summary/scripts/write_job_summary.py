#!/usr/bin/env python3
"""Write GitHub Actions job summary markdown from structured report JSON files."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write job summary from report JSON files")
    parser.add_argument("--title", default="AppStore Workflow Summary")
    parser.add_argument("--report-jsons", required=True, help="Newline-separated report JSON paths")
    return parser.parse_args()


def safe_text(value: object) -> str:
    if value is None:
        return ""
    return str(value)


def md_escape(value: object) -> str:
    text = safe_text(value)
    return text.replace("|", "\\|").replace("\n", "<br>")


def format_status(status: object) -> str:
    value = safe_text(status).upper() or "UNKNOWN"
    return value


def issue_line(issue: dict) -> str:
    severity = safe_text(issue.get("severity", "info")).upper()
    code = safe_text(issue.get("code", "UNKNOWN"))
    message = safe_text(issue.get("message", ""))
    suggestion = safe_text(issue.get("suggestion", ""))
    file_path = safe_text(issue.get("file", ""))

    line = f"- `{severity}` `{code}`"
    if file_path:
        line += f" in `{file_path}`"
    if message:
        line += f": {message}"
    if suggestion:
        line += f" Fix: {suggestion}"
    return line


def format_summary_table(summary: dict) -> list[str]:
    if not summary:
        return []

    lines = ["| Metric | Value |", "| --- | --- |"]
    for key, value in summary.items():
        lines.append(f"| {md_escape(key.replace('_', ' ').title())} | `{md_escape(value)}` |")
    return lines


def format_artifact_line(artifact: dict) -> str:
    name = safe_text(artifact.get("name") or artifact.get("path") or "artifact")
    path = safe_text(artifact.get("path") or "")
    note = safe_text(artifact.get("note") or "")

    line = f"- `{name}`"
    if path:
        line += f" -> `{path}`"
    if note:
        line += f" ({note})"
    return line


def summarize_report(report_path: Path) -> str:
    if not report_path.exists():
        return f"## Missing Report\n- `{report_path}` was not found.\n"

    report = json.loads(report_path.read_text(encoding="utf-8"))
    title = safe_text(report.get("title") or report.get("kind") or report_path.name)
    status = safe_text(report.get("status") or "unknown").upper()
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    context = report.get("context") if isinstance(report.get("context"), dict) else {}
    issues = report.get("issues") if isinstance(report.get("issues"), list) else []
    artifacts = report.get("artifacts") if isinstance(report.get("artifacts"), list) else []

    lines = [f"## {title}", f"- Status: `{format_status(status)}`"]

    summary_table = format_summary_table(summary)
    if summary_table:
        lines.extend(["", *summary_table])

    if issues:
        lines.append("")
        lines.append("### Top Issues")
        for issue in issues[:5]:
            if isinstance(issue, dict):
                lines.append(issue_line(issue))
    else:
        lines.append("")
        lines.append("### Top Issues")
        lines.append("- None")

    if artifacts:
        lines.append("")
        lines.append("### Artifacts")
        for artifact in artifacts[:5]:
            if isinstance(artifact, dict):
                lines.append(format_artifact_line(artifact))

    repo = safe_text(context.get("repo"))
    ref = safe_text(context.get("ref"))
    sha = safe_text(context.get("sha"))
    if repo or ref or sha:
        lines.append("")
        lines.append("### Context")
        if repo:
            lines.append(f"- Repo: `{repo}`")
        if ref:
            lines.append(f"- Ref: `{ref}`")
        if sha:
            lines.append(f"- SHA: `{sha}`")

    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        raise RuntimeError("GITHUB_STEP_SUMMARY is not set")

    report_paths = [Path(line.strip()) for line in args.report_jsons.splitlines() if line.strip()]
    content = [f"# {args.title}\n"]
    for report_path in report_paths:
        content.append(summarize_report(report_path))

    Path(summary_path).write_text("\n".join(content), encoding="utf-8")
    print(f"Wrote job summary to {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
