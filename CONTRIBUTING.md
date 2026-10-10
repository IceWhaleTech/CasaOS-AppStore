# Contributing to ZimaOS AppStore

This file is the repository-level contribution entry for **this repository**.

The source tree currently contains both:

- v2 app store source and documentation
- legacy v1 compatibility output used by older clients and workflows

## Where To Read The Rules

For **v2 / new app store** contribution rules, use the docs site content under `docs/`:

- [Quick Start](docs/quick-start/overview.md)
- [Protocol Reference](docs/specs/overview.md)
- [CI/CD Overview](docs/cicd/overview.md)
- [Migration Guide](docs/migration/overview.md)

If you are building your own external store, start here:

- [Third-party Store Guide](docs/guides/third-party-store-guide.md)

## What This File Covers

This file only covers the repository contribution flow:

1. Fork this repository and work in your own branch.
2. Make and test your changes locally.
3. Open a Pull Request that explains:
   - whether this is a new app, an update, or a docs change
   - what changed
   - how you validated it

For app metadata fields, file layout, localization, assets, and generated `dist/`
output behavior, treat the v2 docs as the source of truth instead of duplicating
those rules here.

## Local Validation

Before opening a PR, run the local build validation flow:

```bash
./scripts/build_dist.sh
```

If you need to override the generated public path, you can still set `BASE_URL`
explicitly before running the script.

Expected result:

- the build completes without errors
- `dist/index.json` is generated
- changed apps produce updated files under `dist/apps/<app-id>/`

## CI Notes

Repository CI validates compose files and the build pipeline automatically on PRs.

Please keep changes compatible with:

- `.github/workflows/validator.yml`
- `.github/workflows/release.yml`
- `.github/workflows/release-store.yml`

## Legacy v1 Note

This repository still builds the legacy v1 artifact at `dist/store/main.zip` for
compatibility. That legacy output should not be treated as the primary source of
contribution rules for the new store.

If you have suggestions for the process or documentation, please open an Issue
or PR.
