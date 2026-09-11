# v1 to v2 Minimum Change Checklist

Use this checklist when you already have a v1 store and want the smallest practical set of changes for v2 support.

Goal: one source repository, v2 static output, and optional v1 zip compatibility.

## 1. Keep the existing app tree

Keep your existing layout:

```text
Apps/
└── MyApp/
    ├── docker-compose.yml
    ├── icon.png
    ├── thumbnail.png
    └── screenshot-1.png
```

You can add SVG icons or cleaner assets later. Asset replacement is not the first migration blocker.

## 2. Add `store-config.json`

Create this file at the repository root:

```json
{
  "version": 2,
  "store_id": "your-store-id",
  "name": {
    "en_US": "Your Store Name"
  },
  "maintainer": "your-name",
  "url": "https://github.com/username/your-appstore"
}
```

Checks:

- `version` is `2`
- `store_id` is globally distinctive and stable
- `store_id` uses only letters, digits, dots (`.`), underscores (`_`), and hyphens (`-`)
- `name.en_US` is present

## 3. Add `supported-languages.json`

Create this file at the repository root:

```json
[
  "en_US"
]
```

Add every locale that your source metadata may define, such as `zh_CN` or `de_DE`.

## 4. Add `x-casaos.id` to every app

Each app needs a stable top-level app ID:

```yaml
x-casaos:
  id: com.example.myapp
```

Checks:

- every source `docker-compose.yml` includes top-level `x-casaos.id`
- use reverse-domain style such as `com.example.myapp`
- the ID has at least two non-empty dot-separated segments
- use only letters, digits, dots (`.`), underscores (`_`), and hyphens (`-`)

## 5. Normalize legacy metadata layout

Common v1-to-v2 cleanups:

| Legacy source | v2 source |
|---|---|
| `en_us` | `en_US` |
| `zh_cn` | `zh_CN` |
| `appfile.json` display metadata | top-level `x-casaos` fields |

You do not need to preserve `appfile.json` for v2. If your v1 packaging still uses it, keep it only for the legacy pipeline.

## 6. Normalize categories

Set every app `x-casaos.category` to one of:

`Media`, `Productivity`, `Home`, `Networking`, `AI`, `Finance`, `Social`, `Developer`, `Others`

For example, old `Utilities` values usually need to become the closest v2 category, often `Productivity` or `Others`.

## 7. Build v2 output

```bash
BASE_URL="https://your-store-domain" \
./scripts/build_dist.sh
```

Checks:

- `dist/store.json` exists
- `dist/index.json` exists
- `dist/apps/<app-id>/docker-compose.yml` exists, where `<app-id>` is the normalized `x-casaos.id`
- `dist/apps/<app-id>/meta.json` exists
- generated app listing items include `id`, `compose_url`, `meta_url`, and `content_hash`

## 8. Add version and other display fields

`version` is required in the new store, even if older source repositories did
not carry an equivalent field.

The remaining fields are not required for compatibility, but they improve the
store experience:

| Field | Type | Note |
|---|---|---|
| `version` | `string` | New and required. Future app upgrade decisions rely on this field. Use a semver-style value whenever possible. |
| `update_at` | `string` | New, optional update date. Use `YYYY-MM-DD` when possible. |
| `release_notes` | `object` | New, optional locale-keyed release notes. Each locale value is plain text. |
| `website` | `string` | New, optional official website URL. |
| `repo` | `string` | New, optional source repository URL. |
| `support` | `string` | New, optional support URL. |
| `docs` | `string` | New, optional documentation URL. |

## 9. Keep v1 compatibility if needed

If old clients still depend on your v1 store, keep a workflow step that builds:

```text
dist/store/main.zip
```

The official repository does this by running the v1 build after the v2 build. That lets one source tree serve both:

- v2 static store consumers
- legacy v1 zip consumers

## 10. Deploy the generated files

Publish `dist/` to static hosting. The URL users add should match the build `base-url`.

## Final pre-release check

- [ ] `store-config.json` is present and valid
- [ ] `supported-languages.json` is present and valid
- [ ] every app has a valid `x-casaos.id`
- [ ] old locale keys are normalized
- [ ] `x-casaos.version` is present and updated for this release
- [ ] optional display fields are added where useful
- [ ] all app categories use v2 values
- [ ] `dist/store.json` and `dist/index.json` are reachable
- [ ] `dist/store/main.zip` is built if v1 compatibility is still required
