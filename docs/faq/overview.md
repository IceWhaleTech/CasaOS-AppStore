# FAQ

This page collects short answers to recurring questions about stores using the v2 protocol, migration, hosting, and compatibility.

## Can I use the same app ID as the official store?

Yes. Official store apps and third-party store apps are isolated in ZimaOS and can coexist even when the source `id` matches.

For third-party stores, still choose stable reverse-domain IDs so your own users get predictable updates.

## What if another third-party store uses the same app ID as mine?

ZimaOS isolates installations by store context, so identical source app IDs across different stores do not collide at the Docker project level.

## Do I need `supported-languages.json`?

Yes for this repository's v2 source structure. It declares the locale candidates the build should consider.

It does not automatically create localized output by itself. Locale-specific files are emitted only when matching localized fields exist in source files.

## Do I need to run the build script?

Yes. The build turns source files into the protocol output consumed by clients:

- `store-config.json` to `store.json`
- source compose to built compose plus `meta.json`
- store-wide app listings with `content_hash`
- optimized assets and locale-specific outputs

## Which build problems are warnings and which ones fail the workflow?

The build action tries to keep processing independent apps so the summary can show more than one problem in a single run.

Warnings that do not fail the v2 build:

- missing `supported-languages.json`: the build falls back to `en_US`
- missing `store-config.json`: app output can still be built, but `store.json` is skipped
- app directories without a top-level `x-casaos`: the app is skipped
- registry rate limits, digest pinning failures, or image-size estimation failures: the app keeps building when possible and the issue is reported as a warning
- image optimization or SVG-to-PNG fallback conversion failures: the original asset is kept when possible and the warning appears in logs
- non-semver `x-casaos.version`: the version is skipped in `index.json`

Errors that are collected per app, then fail the v2 build after other apps are processed:

- invalid app metadata, including missing or invalid `x-casaos.id`
- invalid app YAML
- missing referenced icon, thumbnail, or screenshot
- declared architecture not supported by the container image
- other app-level compose, metadata, asset, or registry processing failures

Errors that stop the build at the global level:

- invalid `base-url`
- missing `Apps/` directory
- invalid `store-config.json` or invalid `store_id`
- invalid JSON in `supported-languages.json`
- dependency setup failures before the build script starts

## Where can I read the build summary?

Open the GitHub Actions run, choose the build or validation job, and read the job summary at the top of the job page. This repository writes the summary from structured report JSON files.

The raw report is also uploaded as a workflow artifact, such as `build-v2-report`, `build-v2-validation-report`, or `validation-report`.

## Can I host my store somewhere other than GitHub Pages?

Yes. Any HTTPS static hosting target works as long as the generated files are reachable.

## Do I have to use jsDelivr?

No. `jsDelivr` is just one possible CDN path. Any correct `base-url` is acceptable.

## Why is `base-url` important?

Because generated listing data contains asset and app file paths that need a resolvable public host prefix.

Set it to the final public URL where `dist/` is served.

## Can I keep v1 compatibility?

Yes. Keep producing the legacy artifact:

```text
dist/store/main.zip
```

The official repository builds v2 static files and then builds this v1 zip from the same source tree.

## What is the minimum viable store structure?

```text
my-appstore/
├── Apps/
│   └── MyApp/
│       ├── docker-compose.yml
│       └── icon.svg
├── store-config.json
└── supported-languages.json
```

Add `scripts/build_dist.sh` if you want a local helper. CI can call `IceWhaleTech/build-appstore-action` directly.
