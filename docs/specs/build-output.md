# Build Output

The protocol is consumed from generated files under `dist/`.

## Output files

The build script can generate:

- `dist/store.json`
- `dist/store.{locale}.json`
- `dist/index.json`
- `dist/index.{locale}.json`
- `dist/apps/<app-id>/docker-compose.yml`
- `dist/apps/<app-id>/docker-compose.{architecture}.yml`
- `dist/apps/<app-id>/meta.json`
- `dist/apps/<app-id>/meta.{locale}.json`
- `dist/apps/<app-id>/assets/*`

## `index.json`

`index.json` is the store-wide app listing.

Each app item includes data such as:

- `id`
- `title`
- `tagline`
- `category`
- `version`
- `author`
- `developer`
- `architectures`
- `icon`
- `thumbnail`
- `compose_url`
- `meta_url`
- `content_hash`

### Listing field meanings

#### `id`

- normalized app identifier from the source top-level `x-casaos.id`
- also used as the generated app output folder name under `dist/apps/`

#### `title`

- resolved app display name for the target locale

#### `tagline`

- resolved short summary for the target locale

#### `category`

- standardized category value used for display and grouping

#### `version`

- app version from `x-casaos.version`
- important for user-facing upgrade understanding and version tracking

#### `author`

- packager or store-side attribution

#### `developer`

- upstream project attribution

#### `architectures`

- supported CPU architectures list
- used by the build to emit architecture-specific compose variants when possible

#### `icon`

- built asset path or URL relative to `--base-url`

#### `thumbnail`

- built thumbnail path or URL relative to `--base-url`

#### `compose_url`

- path to the built per-app compose file

#### `meta_url`

- path to the built per-app metadata file

#### `content_hash`

- hash representing all relevant generated files for the app
- used for incremental client update detection

It is emitted as:

- `dist/index.json`
- `dist/index.{locale}.json` when at least one app explicitly defines that locale in listing-facing fields

## Built `docker-compose.yml`

Built compose files keep only runtime-facing `x-casaos` fields:

- `id`
- `main`
- `index`
- `port_map`
- `scheme`
- `icon`
- `title`

All metadata is removed from built compose and moved to `meta.json`.

### Built compose behavior

Built compose is not a direct copy of source compose.

During build:

- non-runtime `x-casaos` metadata is removed
- `icon` is rewritten
- locale-keyed `title` is resolved to a plain string for the generated locale

## Built `meta.json`

Built `meta.json` holds app metadata, including upgrade- and display-related fields:

- `version`
- `update_at`
- `release_note`
- `website`
- `repo`
- `support`
- `docs`

In practice, `version` should not be treated as a cosmetic extra. It is a key
field for communicating application upgrades in the new store.

`title` and `icon` are intentionally not written into `meta.json`, because they remain part of built compose runtime/display information.

### Built metadata field groups

In practice, built `meta.json` groups:

- descriptive content such as `tagline` and `description`
- presentation assets such as `thumbnail` and `screenshot_link`
- attribution such as `author` and `developer`
- compatibility data such as `architectures`
- optional enhancement fields such as `version`, `update_at`, and `release_note`

## Path behavior

Generated app-relative paths usually look like:

- `apps/com.example.myapp/docker-compose.yml`
- `apps/com.example.myapp/meta.json`
- `apps/com.example.myapp/assets/icon.svg`

In these examples, `com.example.myapp` is the normalized value of source `x-casaos.id`.

These paths are resolved relative to the configured `--base-url`.

The same logical build can therefore be published under different public hosts by changing `--base-url`.

## Content hash

`content_hash` is computed from the files under each generated app directory, including:

- built compose
- architecture-specific compose variants
- meta variants
- assets

This is what enables efficient client-side incremental updates.

## Update behavior

Client update checks are driven by `index.json` and each app's `content_hash`.

That means:

- unchanged apps are skipped
- changed apps trigger fetches for only their compose and meta files
- the store does not need full-package redownloads for every update

## Common mistakes

- assuming `dist/` files should be authored by hand
- assuming `meta.json` contains `title`
- treating `content_hash` as a manual version field
- forgetting that locale-specific index and meta files exist only for explicitly defined locales
