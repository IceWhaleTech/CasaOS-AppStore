#!/usr/bin/env python3
"""Render a machine-readable AppStore report as standalone HTML."""

from __future__ import annotations

import argparse
import json
from html import escape
from pathlib import Path


STATUS_COLORS = {
    "success": "#167c3a",
    "warning": "#9a6700",
    "failed": "#b42318",
    "error": "#b42318",
    "unknown": "#475467",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render AppStore HTML report")
    parser.add_argument("--input", required=True, help="Path to input report JSON")
    parser.add_argument("--output", required=True, help="Path to output HTML")
    parser.add_argument("--title", default="", help="Optional title override")
    return parser.parse_args()


def safe_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def labelize(name: str) -> str:
    return name.replace("_", " ").replace("-", " ").title()


def render_key_value_table(data: dict[str, object]) -> str:
    if not data:
        return "<p class='muted'>No data available.</p>"

    rows = []
    for key, value in data.items():
        rows.append(
            "<tr>"
            f"<th>{escape(labelize(str(key)))}</th>"
            f"<td>{escape(safe_text(value))}</td>"
            "</tr>"
        )
    return (
        "<table class='kv-table'>"
        "<tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


def render_issues(issues: list[object]) -> str:
    if not issues:
        return "<p class='muted'>No issues recorded.</p>"

    rows = []
    for issue in issues:
        if not isinstance(issue, dict):
            continue
        severity = safe_text(issue.get("severity") or "info").lower()
        code = safe_text(issue.get("code"))
        file_path = safe_text(issue.get("file"))
        message = safe_text(issue.get("message"))
        suggestion = safe_text(issue.get("suggestion"))
        rows.append(
            "<tr>"
            f"<td><span class='badge badge-{escape(severity)}'>{escape(severity.upper())}</span></td>"
            f"<td>{escape(code)}</td>"
            f"<td><code>{escape(file_path)}</code></td>"
            f"<td>{escape(message)}</td>"
            f"<td>{escape(suggestion)}</td>"
            "</tr>"
        )

    if not rows:
        return "<p class='muted'>No structured issues recorded.</p>"

    return (
        "<table>"
        "<thead><tr>"
        "<th>Severity</th><th>Code</th><th>File</th><th>Message</th><th>Suggested Fix</th>"
        "</tr></thead>"
        "<tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


def render_artifacts(artifacts: list[object]) -> str:
    if not artifacts:
        return "<p class='muted'>No artifacts recorded.</p>"

    items = []
    for artifact in artifacts:
        if isinstance(artifact, dict):
            name = safe_text(artifact.get("name") or artifact.get("path") or "artifact")
            path = safe_text(artifact.get("path"))
            note = safe_text(artifact.get("note"))
            details = f"<code>{escape(path)}</code>" if path else ""
            if note:
                details = f"{details}<span class='muted'>{escape(note)}</span>"
            items.append(f"<li><strong>{escape(name)}</strong>{details}</li>")
        else:
            items.append(f"<li>{escape(safe_text(artifact))}</li>")
    return "<ul class='artifact-list'>" + "".join(items) + "</ul>"


def render_logs(logs: object) -> str:
    if not logs:
        return "<p class='muted'>No logs attached.</p>"
    return f"<pre>{escape(safe_text(logs))}</pre>"


def render_section(title: str, content: str) -> str:
    return (
        "<section class='card'>"
        f"<h2>{escape(title)}</h2>"
        f"{content}"
        "</section>"
    )


def render_html(report: dict[str, object], title_override: str) -> str:
    title = title_override or safe_text(report.get("title") or "AppStore Report")
    status = safe_text(report.get("status") or "unknown").lower()
    kind = safe_text(report.get("kind") or "report")
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    context = report.get("context") if isinstance(report.get("context"), dict) else {}
    metadata = report.get("metadata") if isinstance(report.get("metadata"), dict) else {}
    issues = report.get("issues") if isinstance(report.get("issues"), list) else []
    artifacts = report.get("artifacts") if isinstance(report.get("artifacts"), list) else []
    logs = report.get("logs")
    notes = report.get("notes")
    started_at = safe_text(report.get("started_at"))
    finished_at = safe_text(report.get("finished_at"))
    color = STATUS_COLORS.get(status, STATUS_COLORS["unknown"])

    overview_rows = {
        "kind": kind,
        "status": status,
        "started_at": started_at,
        "finished_at": finished_at,
    }
    overview_rows = {k: v for k, v in overview_rows.items() if v}

    sections = [
        render_section("Overview", render_key_value_table(overview_rows)),
        render_section("Summary", render_key_value_table(summary)),
        render_section("Context", render_key_value_table(context)),
    ]

    if metadata:
        sections.append(render_section("Metadata", render_key_value_table(metadata)))

    sections.append(render_section("Issues", render_issues(issues)))
    sections.append(render_section("Artifacts", render_artifacts(artifacts)))

    if notes:
        sections.append(render_section("Notes", f"<pre>{escape(safe_text(notes))}</pre>"))

    if logs:
        sections.append(render_section("Logs", render_logs(logs)))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <style>
    :root {{
      --bg: #f5f7fb;
      --card: #ffffff;
      --ink: #101828;
      --muted: #475467;
      --line: #d0d5dd;
      --accent: {color};
      --accent-soft: rgba(16, 24, 40, 0.06);
      --success: #167c3a;
      --warning: #9a6700;
      --error: #b42318;
      --info: #175cd3;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "SFMono-Regular", "Menlo", "Consolas", monospace;
      background: linear-gradient(180deg, #eef3ff 0%, var(--bg) 100%);
      color: var(--ink);
    }}
    .wrap {{
      max-width: 1120px;
      margin: 0 auto;
      padding: 32px 20px 48px;
    }}
    .hero {{
      background: linear-gradient(135deg, var(--accent) 0%, #0f172a 100%);
      color: #fff;
      border-radius: 20px;
      padding: 28px;
      box-shadow: 0 16px 48px rgba(16, 24, 40, 0.18);
      margin-bottom: 24px;
    }}
    .hero h1 {{
      margin: 0 0 8px;
      font-size: 32px;
      line-height: 1.1;
    }}
    .hero p {{
      margin: 0;
      color: rgba(255, 255, 255, 0.86);
      font-size: 14px;
    }}
    .status-pill {{
      display: inline-block;
      margin-top: 16px;
      padding: 8px 12px;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.15);
      font-weight: 700;
      letter-spacing: 0.04em;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 18px;
    }}
    .card {{
      background: var(--card);
      border: 1px solid rgba(16, 24, 40, 0.08);
      border-radius: 18px;
      padding: 20px;
      box-shadow: 0 10px 30px rgba(16, 24, 40, 0.06);
    }}
    .card h2 {{
      margin: 0 0 14px;
      font-size: 18px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}
    th, td {{
      text-align: left;
      vertical-align: top;
      padding: 10px 12px;
      border-top: 1px solid var(--line);
    }}
    th {{
      width: 20%;
      color: var(--muted);
      font-weight: 700;
    }}
    thead th {{
      color: var(--ink);
      border-top: 0;
      background: var(--accent-soft);
    }}
    .kv-table th {{
      width: 34%;
    }}
    .muted {{
      color: var(--muted);
    }}
    code {{
      font-family: inherit;
      background: #f2f4f7;
      padding: 2px 6px;
      border-radius: 6px;
      word-break: break-word;
    }}
    pre {{
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      background: #0f172a;
      color: #e2e8f0;
      border-radius: 14px;
      padding: 16px;
      font-size: 12px;
      line-height: 1.55;
      overflow: auto;
    }}
    .badge {{
      display: inline-block;
      padding: 4px 8px;
      border-radius: 999px;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.03em;
      color: #fff;
    }}
    .badge-success {{ background: var(--success); }}
    .badge-warning {{ background: var(--warning); }}
    .badge-error, .badge-failed {{ background: var(--error); }}
    .badge-info, .badge-unknown {{ background: var(--info); }}
    .artifact-list {{
      margin: 0;
      padding-left: 20px;
    }}
    .artifact-list li {{
      margin: 0 0 10px;
    }}
    .artifact-list strong {{
      display: inline-block;
      min-width: 120px;
      margin-right: 8px;
    }}
    @media (max-width: 720px) {{
      .hero h1 {{ font-size: 26px; }}
      th, td {{ padding: 8px; }}
      .grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <main class="wrap">
    <header class="hero">
      <h1>{escape(title)}</h1>
      <p>{escape(labelize(kind))} report generated for AppStore automation.</p>
      <div class="status-pill">STATUS: {escape(status.upper())}</div>
    </header>
    <div class="grid">
      {''.join(sections)}
    </div>
  </main>
</body>
</html>
"""


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    report = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise ValueError("Report JSON must be an object")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_html(report, args.title), encoding="utf-8")
    print(f"Rendered HTML report: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
