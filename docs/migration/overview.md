# Migration Strategy

This section is for maintainers who already have a v1 zip-based CasaOS/ZimaOS app store and want to support v2 with minimal source changes.

The important point: you usually do not need to rebuild every app from scratch. Keep the existing `Apps/` tree, normalize the source metadata, add store-level v2 files, then produce both outputs from the same repository.

## What changed from v1 to v2

| Topic | v1 store | v2 store |
|---|---|---|
| Distribution | packaged zip or sysroot bundle | static files under `dist/` |
| Client entry | legacy package such as `main.zip` | `store.json` and `index.json` |
| Store identity | no required store-level identity file | required `store-config.json` |
| Locale list | inferred from app content | declared in `supported-languages.json`, emitted only when fields exist |
| App identity | often based on compose/name conventions | required top-level `x-casaos.id` |
| Metadata | `appfile.json` plus `x-casaos` | top-level `x-casaos`, split into built compose and `meta.json` |
| Categories | legacy/free-form values such as `Utilities` | normalized v2 categories |
| Updates | package refresh | incremental app updates through `content_hash` |
| Compatibility | v1 clients consume zip | v1 compatibility is preserved by still building `dist/store/main.zip` |

## Minimum migration model

1. Keep `Apps/<App>/docker-compose.yml` as your source of truth.
2. Move or confirm app display metadata in the top-level `x-casaos` block.
3. Add a stable `x-casaos.id` to every app.
4. Normalize locale keys such as `en_us` to `en_US`.
5. Normalize app categories to the v2 category list.
6. Add `store-config.json` and `supported-languages.json`.
7. Add optional v2 display fields such as `version`, `update_at`, and `release_notes` when useful.
8. Build v2 `dist/`.
9. Keep building the v1 zip artifact if you still support legacy clients.

## Compatibility pattern

The current repository builds both formats:

- v2: `dist/store.json`, `dist/index.json`, `dist/apps/<app-id>/...`
- v1: `dist/store/main.zip`

Here `<app-id>` is the normalized value of each app's top-level `x-casaos.id`.

This is the safest migration pattern for existing stores. New clients can subscribe to the v2 static URL, while old clients can keep using the v1 artifact until you decide to stop supporting it.

## What can stay

These v1-era files or directories can remain when you still need compatibility:

- `Apps/`
- existing compose runtime configuration
- app assets such as icons, thumbnails, and screenshots
- `category-list.json` and `recommend-list.json` if your v1 packaging still uses them
- v1 packaging workflow steps

The v2 build does not require you to hand-author `dist/` files.

## What must change

At minimum, v2 needs:

- root `store-config.json`
- root `supported-languages.json`
- top-level `x-casaos.id` in every app compose
- supported v2 categories
- normalized locale keys such as `en_US`, `zh_CN`, `de_DE`
- a v2 build and publish workflow

## Version and other display fields added in v2

The migration can stop after the required changes above. However, `version` is
required in the new store. The remaining fields improve app detail pages,
listings, and update presentation.

Add these fields under the top-level `x-casaos` block when the information is available:

| Field | Source type | Migration note |
|---|---|---|
| `version` | `string` | New and required. Used for app version tracking, upgrade communication, and richer store display. |
| `update_at` | `string` | New, optional. App update date, recommended as `YYYY-MM-DD`, for example `"2026-03-01"`. |
| `release_notes` | `object` | New, optional. Locale-keyed release notes in source; each locale value is plain text. Built output uses `release_note`. |
| `website` | `string` | New, optional. Official website URL for richer store display. |
| `repo` | `string` | New, optional. Source repository URL for richer store display. |
| `support` | `string` | New, optional. Support URL for richer store display. |
| `docs` | `string` | New, optional. Documentation URL for richer store display. |

Example:

```yaml
x-casaos:
  version: "1.0.0"
  update_at: "2026-03-01"
  release_notes:
    en_US: "First v2-compatible release."
  website: "https://example.com"
  repo: "https://github.com/example/myapp"
  support: "https://github.com/example/myapp/issues"
  docs: "https://docs.example.com"
```

## Next pages

1. [Minimum Change Checklist](./v1-to-v2-migration-checklist.md)
2. [Store Config](../specs/store-config.md)
3. [Compose and x-casaos](../specs/compose-and-x-casaos.md)
4. [Build Output](../specs/build-output.md)
5. [Official Actions Reuse](../cicd/official-actions-and-workflows.md)
