# Assets and Localization

This page groups two protocol behaviors that strongly affect generated output: asset processing and localized text expansion.

## Assets

All built assets are written to `apps/{app-id}/assets/`.

`{app-id}` is the normalized value of the source top-level `x-casaos.id`.

### Supported source formats

| Asset | Input formats | Output behavior |
|------|---------------|----------------|
| `icon` | `.svg`, `.png`, `.jpg`, `.webp` | SVG is preserved and may get PNG fallback; raster icons are copied |
| `thumbnail` | `.png`, `.jpg`, `.jpeg`, `.webp` | optimized when tooling is available; final extension follows generated output |
| `screenshot-{n}` | `.png`, `.jpg`, `.jpeg`, `.webp` | optimized when tooling is available; final extension follows generated output |

### Asset behavior details

#### `icon`

- expected for every app
- ideally provided as `icon.svg`
- may also produce PNG fallback output when tooling is available

#### `thumbnail`

- optional
- mainly used for richer store presentation
- normalized into a built asset path

#### `screenshot-{n}`

- optional
- supports multiple numbered screenshots
- normalized into built asset paths

## Asset recommendations

- prefer `icon.svg` when possible
- use a dedicated thumbnail for store presentation
- keep screenshots representative of the actual UI

Non-icon raster assets are optimized during build and may be resized when too wide.
Depending on the build action version and available image tooling, generated thumbnails and screenshots may keep their source extension or be emitted as optimized WebP files. Use the paths written to `index.json` and `meta.json` as the authoritative output.

## Icon behavior

Icons appear in two places:

- app listings, using the icon path emitted in `index.json`
- the installed dashboard entry, using `x-casaos.icon` in built compose

During build, the icon URL in built compose is rewritten to the built asset URL under your configured `--base-url`.

## Locale keys

Locale keys should use `ll_CC` format:

- `en_US`
- `zh_CN`
- `de_DE`

The build script normalizes locale keys automatically, but source files should still follow the expected format.

## Localization source fields

Store-level localized text:

- `store-config.json.name`
- `store-config.json.description`

App-level localized text:

- `x-casaos.title`
- `x-casaos.tagline`
- `x-casaos.description`
- `x-casaos.release_notes`
- locale-keyed values under `x-casaos.tips`

## Multi-language output

Candidate locales come from `supported-languages.json`.

Important behavior:

- default output is always generated
- locale-specific files are generated only when that locale is explicitly defined
- if `supported-languages.json` is missing, only `en_US` output is generated

## Locale generation rules

Think of locale generation in two stages:

1. `supported-languages.json` declares which locales are candidates.
2. Source localization fields determine which locale-specific files are actually emitted.

So a locale may appear in the candidate list and still produce no output if no store or app field explicitly defines it.

## Example

Source:

```yaml
title:
  en_US: My App
  zh_CN: 我的应用
```

Possible output:

- `dist/index.json`
- `dist/index.zh_CN.json`
- `dist/apps/com.example.myapp/meta.json`
- `dist/apps/com.example.myapp/meta.zh_CN.json`

Here `com.example.myapp` represents the normalized source `x-casaos.id`.

## Common mistakes

- expecting `supported-languages.json` alone to create localized files
- assuming assets are duplicated per locale
- forgetting that icons affect both listing display and installed dashboard display
