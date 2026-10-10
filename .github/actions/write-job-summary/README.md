# `write-job-summary`

Writes one or more structured report JSON files into the GitHub Actions job summary.

## Inputs

- `title`: Optional summary title
- `report-jsons`: Newline-separated list of report JSON paths

## Example

```yaml
- name: Write workflow summary
  if: always()
  uses: ./.github/actions/write-job-summary
  with:
    title: Validation Summary
    report-jsons: |
      out/validation-report.json
      out/build-v2-validation-report.json
```
