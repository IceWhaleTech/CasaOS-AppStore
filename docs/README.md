# Documentation

This folder contains project documentation for the ZimaOS AppStore source repository.

## Guides

- [Third-party Store Guide](./guides/third-party-store-guide.md): Build and deploy a ZimaOS-compatible third-party app store source.
- [v1 -> v2 Migration Checklist](./guides/v1-to-v2-migration-checklist.md): One-page minimum-change checklist for existing zip-based third-party stores.
- [Build Action README](../actions/build-appstore/README.md): Reusable GitHub Action for building AppStore `dist/`.

## Contribution

- [Contributing Guide](../CONTRIBUTING.md): Rules and process for contributing apps to this repository.

## Notes

- `internal-dev-guide.md` and `CONTRIBUTING_v2.md` are currently not part of the main public doc navigation.
- The third-party guides describe the latest flat `dist/` layout (`index.json` + `index.{locale}.json`, `store.json` + `store.{locale}.json`, and `apps/{app-id}/...`).
