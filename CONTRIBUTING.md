# Contributing to ZimaOS AppStore

This guide is for contributors submitting changes to **this repository**.

If you are building your own external store, use:
- [docs/guides/third-party-store-guide.md](docs/guides/third-party-store-guide.md)

## 1. Submission Process

1. Fork this repository and work in your own branch.
2. Test the app on a local ZimaOS environment.
3. Open a Pull Request and include:
   - new app or update
   - what changed
   - test evidence (install success + WebUI reachable)

## 2. Required App Files

Each app directory under `Apps/` should include at least:
- `docker-compose.yml` (or `docker-compose.yaml`)
- `icon.svg` or `icon.png`
- at least one screenshot (`screenshot-1.png` / `.jpg`)

## 3. Compose Rules (Repo Policy)

- Compose file must be valid YAML.
- Do not use image tag `latest`; pin explicit versions.
- Top-level `name` is the app ID and must be unique.
- `services.<service>.container_name` should usually match service name.

Supported runtime variables include `$PUID`, `$PGID`, `$TZ`, `$AppID`.

## 4. Top-level `x-casaos` Rules

Top-level `x-casaos` should follow this field grouping order:

1. Access entry: `main`, `index`, `port_map`, `scheme`
2. Display: `title`, `icon`, `thumbnail`, `screenshot_link`, `tagline`, `description`, `tips`
3. Metadata: `author`, `developer`, `category`, `architectures`
4. Version: `version`, `update_at`, `release_notes`
5. Links: `website`, `repo`, `support`, `docs`

Field semantics:
- `author`: appstore-side maintainer/submitter
- `developer`: upstream project developer

For full field reference and build output behavior, see:
- [docs/guides/third-party-store-guide.md](docs/guides/third-party-store-guide.md)
- [docs/internal-dev-guide.md](docs/internal-dev-guide.md)

## 5. i18n Rules

Locale keys must use `ll_CC` format (e.g. `en_US`, `zh_CN`).

At minimum, include `en_US` for i18n blocks.

## 6. Build/Validation Before PR

Run local build validation before submitting:

```bash
python3 scripts/build_appstore.py \
  --source . \
  --output dist \
  --base-url "https://cdn.jsdelivr.net/gh/IceWhaleTech/CasaOS-AppStore@gh-pages"
```

Expected result:
- build succeeds without errors
- `dist/index.json` generated
- changed app has updated `dist/apps/<app-id>/docker-compose.yml` and `meta.json`

## 7. CI Notes

Repository CI validates compose and build pipeline automatically on PR.

Please keep changes compatible with:
- `.github/workflows/validator.yml`
- `.github/workflows/release.yml`

## 8. Asset Recommendations

For apps intended for recommendation/featured placement:
- `icon`: transparent background, recommended 256x256 SVG/PNG
- `thumbnail`: recommended 784x442 (publish pipeline converts to WebP)
- `screenshot`: recommended 1280x800 (16:10, pipeline converts to WebP)

If you have suggestions for this process, please open an Issue or PR.
