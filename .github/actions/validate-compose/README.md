# `validate-compose`

Validates AppStore `docker-compose.yml` files and writes a structured JSON report.

## Checks

- Compose file discovery under `Apps/`
- Top-level `name` format: `^[a-z0-9_-]+$`
- Top-level `x-casaos.id` presence and reverse-domain format
- `docker compose config -q` syntax validation unless explicitly skipped

## Inputs

- `app-path`: Optional app folder name under `Apps/`
- `report-json`: Path to the output report JSON
- `skip-compose-config`: Set to `true` to skip Docker Compose validation

## Output

- `report-json`: Path to the generated report

## Example

```yaml
- name: Validate app metadata
  uses: ./.github/actions/validate-compose
  with:
    report-json: out/validation-report.json
```
