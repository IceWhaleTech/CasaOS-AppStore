# Third-party Store Guide

This page is kept as a compact compatibility entry for older links. The documentation now uses five clearer sections.

## Choose your path

- New store: [Create a Store](../quick-start/overview.md)
- Existing v1 store: [Migrate from v1](../migration/overview.md)
- File and field reference: [Protocol Reference](../specs/overview.md)
- Build and publish automation: [CI/CD Overview](../cicd/overview.md)
- Short answers: [FAQ](../faq/overview.md)

## Core v2 flow

1. Write source files such as `store-config.json`, `supported-languages.json`, and `Apps/*/docker-compose.yml`.
2. Run the public build action or `./scripts/build_dist.sh`.
3. Publish the generated `dist/` directory.
4. Let clients consume `store.json`, `index.json`, built compose files, metadata files, and assets.

## Minimal source structure

```text
my-appstore/
├── Apps/
│   └── MyApp/
│       ├── docker-compose.yml
│       └── icon.svg
├── store-config.json
└── supported-languages.json
```

For local builds, optionally add `scripts/build_dist.sh`.

## Key references

- [Repository Structure](../quick-start/repository-structure.md)
- [Store Config](../specs/store-config.md)
- [Compose and x-casaos](../specs/compose-and-x-casaos.md)
- [Build Output](../specs/build-output.md)
- [Assets and Localization](../specs/assets-and-i18n.md)
- [Official Actions Reuse](../cicd/official-actions-and-workflows.md)
