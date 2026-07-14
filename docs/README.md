# Documentation

This folder contains the VitePress documentation site for the ZimaOS AppStore source repository.

## Main Structure

- [Home](./index.md): Documentation entry page and reading paths.
- [Create a Store](./quick-start/overview.md): Build a compatible store from scratch.
- [Migrate from v1](./migration/overview.md): Add v2 support to an existing v1 store while preserving v1 compatibility.
- [Protocol Reference](./specs/overview.md): Required files, fields, generated output, assets, and localization rules.
- [CI/CD](./cicd/overview.md): Validation, build, release, publish, and official action reuse.
- [Resources](./resources/recommended-third-party-stores.md): Community resource pages such as awesome public third-party store sources.
- [FAQ](./faq/overview.md): Short answers to common protocol and migration questions.

## Locales

- [Simplified Chinese](./zh/index.md): Chinese mirror of the documentation structure.

## Compatibility Pages

- [Third-party Store Guide](./guides/third-party-store-guide.md): Compact legacy guide map that points into the current structure.
- [Official Actions and Workflows](./guides/official-actions-and-workflows.md): Moved-page entry that points to [CI/CD / Official Actions Reuse](./cicd/official-actions-and-workflows.md).

## Contribution

- [Contributing Guide](https://github.com/IceWhaleTech/CasaOS-AppStore/blob/main/CONTRIBUTING.md): Rules and process for contributing apps to this repository.

## Local Docs Development

From this directory:

```bash
pnpm i
pnpm dev
```

This docs site currently uses `pnpm` with `pnpm-lock.yaml` as the source of
truth for Node dependencies.

Default build output:

- `docs/.vitepress/dist/`

This default output path works well with platforms such as Cloudflare Pages.

## Notes

- The current public docs describe the v2 static `dist/` layout: `store.json`, `index.json`, locale variants, and `apps/{app-id}/...`.
- Existing v1 stores should start from the migration section, not the fresh-start guide.
