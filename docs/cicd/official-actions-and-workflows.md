# Official Actions Reuse

This page shows the recommended way for third-party store maintainers to reuse the official build and release flow.

## Recommended reuse path

For external repositories, prefer these layers:

1. Use the upstream public build action `IceWhaleTech/build-appstore-action`.
2. Keep your own repository workflow responsible for validation, artifact upload, and publishing.
3. Treat helper actions under this repository's `.github/actions/` as examples or repo-local wrappers unless you intentionally vendor them.

## What each action is for

- `IceWhaleTech/build-appstore-action`: public v2 build engine. Use this to generate `dist/` in your own repository workflow.
- `.github/actions/build-store-v2`: repo-local wrapper around the public build action.
- `.github/actions/build-store-v1`: packages the legacy `dist/store/main.zip` artifact for old clients.
- `.github/actions/validate-compose`: checks app compose metadata before building.
- `.github/actions/write-job-summary`: writes structured JSON reports into the GitHub Actions job summary.
- `.github/actions/render-report`: converts JSON reports into standalone HTML artifacts.

## Recommended workflow split

The official repository separates concerns this way:

- `validator.yml`: validate compose input and confirm the v2 build succeeds.
- `release.yml`: build v2 `dist/`, build v1 `main.zip`, upload artifacts, and save caches.
- `release-store.yml`: publish tagged releases, deploy `dist/` to `gh-pages`, and create a GitHub Release bundle.

For most third-party stores, use the same split:

- one validation workflow for PRs
- one build workflow for reusable artifacts
- one publish workflow for tags or releases

## Minimal validation workflow

```yaml
name: Validate Store

on:
  pull_request:
  workflow_dispatch:

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build v2 dist
        uses: IceWhaleTech/build-appstore-action@v1
        with:
          source: .
          output: dist
          base-url: https://cdn.jsdelivr.net/gh/${{ github.repository }}@gh-pages
          cache-file: .cache/build_appstore/image-size-cache.json
          digest-cache-file: .cache/build_appstore/image-digest-cache.json
```

## Minimal publish workflow

```yaml
name: Release Store

on:
  push:
    tags:
      - "v*"

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build v2 dist
        uses: IceWhaleTech/build-appstore-action@v1
        with:
          source: .
          output: dist
          base-url: https://cdn.jsdelivr.net/gh/${{ github.repository }}@gh-pages
          cache-file: .cache/build_appstore/image-size-cache.json
          digest-cache-file: .cache/build_appstore/image-digest-cache.json

      - name: Deploy dist
        uses: peaceiris/actions-gh-pages@v4
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_branch: gh-pages
          publish_dir: ./dist
```

## Compatibility note

If you still support legacy v1 clients, add a step that also produces `dist/store/main.zip`. The official repository does this through `.github/actions/build-store-v1` after the v2 build succeeds.

## Local builds

Use `./scripts/build_dist.sh` when you want local development to match the upstream build action closely. Use GitHub Actions directly for real third-party store CI.
