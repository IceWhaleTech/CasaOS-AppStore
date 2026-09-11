# `render-report`

Renders a structured `report.json` file into a standalone HTML report suitable for:

- GitHub Actions artifacts
- PR review attachments
- release notes support files

## Inputs

- `report-json`: Path to the source JSON report.
- `report-html`: Path to the generated HTML file. Default: `report.html`
- `title`: Optional title override.

## Output

- `report-html`: Path to the generated HTML report.

## Expected report shape

The renderer is intentionally tolerant, but works best with a report like:

```json
{
  "kind": "build-v2",
  "status": "failed",
  "summary": {
    "apps_total": 120,
    "apps_passed": 119,
    "apps_failed": 1
  },
  "context": {
    "repo": "owner/repo",
    "ref": "refs/heads/main",
    "sha": "abc123",
    "trigger": "push"
  },
  "issues": [
    {
      "severity": "error",
      "code": "MISSING_X_CASAOS_ID",
      "file": "Apps/2FAuth/docker-compose.yml",
      "message": "Missing required x-casaos.id",
      "suggestion": "Add a top-level x-casaos.id using reverse-domain format."
    }
  ],
  "artifacts": [
    {
      "name": "dist.zip",
      "path": "dist.zip"
    }
  ]
}
```

## Example

```yaml
- name: Render validation report
  uses: ./.github/actions/render-report
  with:
    report-json: out/validation-report.json
    report-html: out/validation-report.html
    title: "Validation Report"
```
