# `build-store-v1`

Builds the legacy v1 AppStore `main.zip` package and writes a structured JSON report.

## Inputs

- `source`
- `output-zip`
- `report-json`
- `report-title`

## Outputs

- `output-zip`
- `report-json`
- `status`

## Behavior

- Packages the legacy `build/` tree plus app metadata into `main.zip`
- Writes a JSON report describing success or failure
- Intended to be followed by `./.github/actions/render-report`

## Example

```yaml
- name: Build v1 store
  id: build_v1
  uses: ./.github/actions/build-store-v1
  with:
    output-zip: dist/store/main.zip
    report-json: out/build-v1-report.json
```
