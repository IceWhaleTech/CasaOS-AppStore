# Protocol Reference Overview

This section is the canonical reference for the v2 store protocol.

Use the start and migration guides for task flow. Use this section when you need exact file requirements, field meanings, or build output behavior.

## Required source files

A v2 source repository is built from:

- `store-config.json`: store identity and store-level localized fields.
- `supported-languages.json`: candidate locale list.
- `Apps/<App>/docker-compose.yml`: app runtime configuration and top-level `x-casaos` metadata.
- app assets referenced by each app, commonly `icon`, `thumbnail`, and `screenshot-{n}` files.

## Generated files

The build produces static protocol output under `dist/`:

- `store.json` and optional `store.{locale}.json`
- `index.json` and optional `index.{locale}.json`
- `apps/<app-id>/docker-compose.yml`
- optional architecture-specific compose files
- `apps/<app-id>/meta.json` and optional `meta.{locale}.json`
- `apps/<app-id>/assets/*`

`<app-id>` is the normalized value of the source top-level `x-casaos.id`.

## Reading order

1. [Store Config](store-config.md): root store identity file and fields.
2. [Compose and x-casaos](compose-and-x-casaos.md): app source compose and every top-level `x-casaos` field.
3. [Build Output](build-output.md): generated files, listing fields, metadata split, paths, and `content_hash`.
4. [Assets and Localization](assets-and-i18n.md): asset handling, locale keys, and localized text output rules.

## Related task guides

- [Create a Store](../quick-start/overview.md)
- [Migrate from v1](../migration/overview.md)
- [CI/CD Overview](../cicd/overview.md)
