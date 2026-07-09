# `build-store-v2`

Builds the v2 AppStore output and writes a structured JSON report that can later
be rendered to HTML.

## Inputs

- `source`
- `output`
- `base-url`
- `cache-file`
- `digest-cache-file`
- `report-json`
- `report-title`

## Outputs

- `output-dir`
- `report-json`
- `status`

## Behavior

- Internally forwards to `IceWhaleTech/build-appstore-action@v1`
- Uses the upstream action's native structured build report support
- Keeps this local wrapper as a stable repo-local entrypoint for workflows

## Example

```yaml
- name: Build v2 store
  id: build_v2
  continue-on-error: true
  uses: ./.github/actions/build-store-v2
  with:
    output: dist
    report-json: out/build-v2-report.json
```
