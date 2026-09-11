# Compose and x-casaos

Each app lives under `Apps/<folder>/docker-compose.yml`.

## Scope of this page

This page focuses on the top-level `x-casaos` block, which is the store-specific metadata contract used by the build pipeline.

For the rest of the Compose file:

- follow the official Docker Compose file reference: https://docs.docker.com/reference/compose-file/
- use the official `services` reference for service definitions: https://docs.docker.com/reference/compose-file/services/
- use the official top-level `name` reference: https://docs.docker.com/reference/compose-file/version-and-name/

In other words:

- standard container runtime configuration belongs to Docker Compose
- store-facing app metadata belongs to `x-casaos`

## Source model

You author one compose file per app. That file contains:

- standard Docker Compose content
- one top-level `x-casaos` block

The source directory name under `Apps/` is not the protocol identity. The build process reads identity from the compose content itself, especially top-level `name` and `x-casaos.id`.

## Minimal example

```yaml
name: my-app
services:
  my-app:
    image: myrepo/my-app:1.0.0
    ports:
      - target: 8080
        published: "8080"
        protocol: tcp
    restart: unless-stopped
x-casaos:
  id: com.example.myapp
  main: my-app
  index: /
  port_map: "8080"
  scheme: http
  icon: https://cdn.example.com/my-app/icon.svg
  title:
    en_US: My App
  tagline:
    en_US: Does amazing things
  description:
    en_US: A great app that does amazing things.
  author: Your Name
  developer: Original Developer
  category: Productivity
  architectures:
    - amd64
  version: "1.0.0"
  update_at: "2026-03-01"
  release_notes:
    en_US: First release
```

## Compose rules outside `x-casaos`

For all non-`x-casaos` content, this repository does not redefine Docker Compose semantics. Use the official documentation as the source of truth:

- Compose file reference: https://docs.docker.com/reference/compose-file/
- Services reference: https://docs.docker.com/reference/compose-file/services/
- Project `name` reference: https://docs.docker.com/reference/compose-file/version-and-name/
- Project naming behavior: https://docs.docker.com/compose/how-tos/project-name/

Repo-specific expectations are limited to:

- compose must be valid YAML
- compose must pass `docker compose config -q`
- top-level `name` must satisfy repo validation expectations
- service-level `services.<name>.x-casaos` blocks are legacy and removed during v2 build processing

## x-casaos overview

The top-level `x-casaos` block contains two kinds of fields:

- runtime/display entry fields that remain in built `docker-compose.yml`
- metadata fields that are extracted into built `meta.json`

## Field matrix

| Field | Type | Required | Localized in source | Built output location |
|---|---|---:|---:|---|
| `id` | `string` | Yes | No | built compose + `meta.json`/index-derived outputs |
| `main` | `string` | Yes | No | built compose |
| `index` | `string` | Yes in practice | No | built compose |
| `port_map` | `string` | Yes | No | built compose |
| `scheme` | `string` | No | No | built compose |
| `icon` | `string` | Yes | No | built compose, rewritten during build |
| `title` | `object` | Yes | Yes | built compose, resolved per locale |
| `tagline` | `object` | Recommended | Yes | `meta.json`, index listing |
| `description` | `object` | Recommended | Yes | `meta.json` |
| `thumbnail` | `string` | No | No | `meta.json` as built asset path |
| `screenshot_link` | `string[]` | No | No | `meta.json` as built asset paths |
| `tips` | `object` | No | Yes | `meta.json` |
| `author` | `string` | Recommended | No | `meta.json`, index listing |
| `developer` | `string` | Recommended | No | `meta.json`, index listing |
| `category` | `string` | Yes | No | `meta.json`, index listing |
| `architectures` | `string[]` | Recommended | No | `meta.json`, index listing |
| `version` | `string` | Yes | No | `meta.json`, index listing |
| `update_at` | `string` | No | No | `meta.json` |
| `release_notes` | `object` | No | Yes | `meta.json.release_note` |
| `website` | `string` | No | No | `meta.json` |
| `repo` | `string` | No | No | `meta.json` |
| `support` | `string` | No | No | `meta.json` |
| `docs` | `string` | No | No | `meta.json` |

## Runtime fields

### `id`

Purpose:
Stable store-protocol application identity.

Rules:

- required in every source app compose
- must use reverse-domain style such as `com.example.myapp`
- only letters, digits, `.`, `_`, and `-` are allowed
- normalized to lowercase during build
- must contain at least two non-empty dot-separated segments

Build behavior:

- remains present in built compose
- also propagates into built metadata and listing data

Common mistakes:

- treating the app directory name as the identity
- using a short non-domain-style string

### `main`

Purpose:
Names the service that provides the primary browser-facing UI.

Rules:

- required
- must match a service name under `services`
- should point to the user-facing web service, not a helper container

Build behavior:

- remains in built compose

Common mistakes:

- pointing `main` at a database container

### `index`

Purpose:
Defines the path appended to the app entry URL when clients open the UI.

Rules:

- usually `/`
- should reflect the app's actual web entry path

Build behavior:

- remains in built compose

### `port_map`

Purpose:
Defines the published web UI port exposed to users.

Rules:

- required
- must be a YAML string, for example `"8080"`
- should match the port users actually open in the browser

Build behavior:

- remains in built compose

Common mistakes:

- writing `port_map: 8080` without quotes

### `scheme`

Purpose:
Specifies whether the app should be opened with `http` or `https`.

Rules:

- optional
- should match the actual exposed protocol

Build behavior:

- remains in built compose

### `icon`

Purpose:
Provides the installed-dashboard icon URL.

Rules:

- required
- source compose may use any reachable URL
- build output rewrites the field to the built asset URL under `--base-url`

Build behavior:

- remains in built compose
- rewritten to point at `apps/{app-id}/assets/icon.*`

Common mistakes:

- assuming this exact source value will remain unchanged after build

### `title`

Purpose:
Provides the app display name.

Rules:

- required
- locale-keyed object in source
- should include `en_US`

Build behavior:

- remains in built compose
- resolved to plain string text in each generated locale output

Common mistakes:

- writing a plain string instead of a locale-keyed object

## Metadata fields

### `tagline`

Purpose:
Short one-line summary used in app listing and detail contexts.

Rules:

- recommended
- locale-keyed object in source

Build behavior:

- extracted to built `meta.json`
- may also be emitted into listing data such as `index.json`

### `description`

Purpose:
Long-form app description.

Rules:

- recommended
- locale-keyed object in source
- may contain markdown text depending on client support

Build behavior:

- extracted to built `meta.json`
- resolved to plain string in each generated locale file

### `thumbnail`

Purpose:
Provides a larger promotional image for richer app presentation.

Rules:

- optional
- usually references a file in the app directory

Build behavior:

- emitted into `meta.json` as a built asset path
- source file is transformed into output under `apps/{app-id}/assets/`

### `screenshot_link`

Purpose:
Provides one or more screenshots for the app detail view.

Rules:

- optional
- array of screenshot filenames in source

Build behavior:

- emitted into `meta.json` as built asset paths

### `tips`

Purpose:
Carries install-time or pre-install user guidance.

Rules:

- optional
- object whose values are locale-keyed text

Example:

```yaml
tips:
  before_install:
    en_US: This app requires at least 4GB RAM.
    zh_CN: This app requires at least 4GB RAM.
```

Build behavior:

- extracted to built `meta.json`
- locale values are resolved per generated locale

### `author`

Purpose:
Identifies the store-side packager or maintainer of the app definition.

Rules:

- recommended
- plain string

Build behavior:

- emitted into `meta.json`
- commonly included in app listing data

### `developer`

Purpose:
Identifies the upstream project or original developer.

Rules:

- recommended
- plain string

Build behavior:

- emitted into `meta.json`
- commonly included in app listing data

### `category`

Purpose:
Assigns the app to a standardized ZimaOS store category.

Rules:

- required in practice for correct display
- must be one of:
  - `Media`
  - `Productivity`
  - `Home`
  - `Networking`
  - `AI`
  - `Finance`
  - `Social`
  - `Developer`
  - `Others`

Build behavior:

- emitted into `meta.json`
- commonly included in app listing data

Common mistakes:

- using free-form category names

### `architectures`

Purpose:
Declares which CPU architectures are supported by the app package.

Rules:

- recommended
- array of strings
- common values include `amd64` and `arm64`

Build behavior:

- emitted into `meta.json`
- commonly included in app listing data

### `version`

Purpose:
Application version shown to users and used to understand upgrades.

Rules:

- required for apps published to the new store
- plain string
- should change when the published app update changes in a way users should receive as a new version
- should use a semver-style value whenever possible, for example `1.2.3`

Build behavior:

- emitted into `meta.json`
- may also appear in listing data

Why it matters:

- future app upgrade decisions rely on this field to determine what version users are moving to
- without it, users and clients must fall back to lower-level change signals such as `content_hash`
- missing or non-semver versions weaken update transparency and may be skipped from some listing-facing output

Common mistakes:

- treating `version` as a cosmetic field only
- forgetting to update it when publishing a meaningful app update
- using ad-hoc strings that do not behave like a normal release version

### `update_at`

Purpose:
Optional update date used to enrich store presentation.

Rules:

- optional
- recommended format: `YYYY-MM-DD`

Build behavior:

- emitted into `meta.json`

### `release_notes`

Purpose:
Provides release notes or changelog summary.

Rules:

- optional
- locale-keyed object in source
- source field name remains `release_notes`

Build behavior:

- extracted to built `meta.json`
- renamed to `release_note`

Common mistakes:

- writing `release_note` in source instead of `release_notes`

### `website`

Purpose:
Links to the official product or homepage.

Rules:

- optional
- plain string URL

Build behavior:

- emitted into `meta.json`

### `repo`

Purpose:
Links to the source repository or project repository.

Rules:

- optional
- plain string URL

Build behavior:

- emitted into `meta.json`

### `support`

Purpose:
Links to the support page, issue tracker, forum, or help center.

Rules:

- optional
- plain string URL

Build behavior:

- emitted into `meta.json`

### `docs`

Purpose:
Links to documentation for the packaged application.

Rules:

- optional
- plain string URL

Build behavior:

- emitted into `meta.json`

## What stays in built compose vs what moves to `meta.json`

Stays in built compose:

- `id`
- `main`
- `index`
- `port_map`
- `scheme`
- `icon`
- `title`

Moves to built `meta.json`:

- `tagline`
- `description`
- `thumbnail`
- `screenshot_link`
- `tips`
- `author`
- `developer`
- `category`
- `architectures`
- `version`
- `update_at`
- `release_note`
- `website`
- `repo`
- `support`
- `docs`

## Field placement rule

Use this split when authoring source compose:

- runtime and launch-entry information belongs in runtime `x-casaos` fields
- store presentation metadata belongs in metadata `x-casaos` fields
- container runtime details belong to standard Docker Compose sections such as `services`, `volumes`, `networks`, and `environment`

## Common mistakes summary

- using plain strings where locale-keyed objects are expected
- pointing `main` to a non-UI service
- using an integer instead of a quoted string for `port_map`
- using unofficial category values
- forgetting that `title` stays in built compose while `tagline` moves to `meta.json`
