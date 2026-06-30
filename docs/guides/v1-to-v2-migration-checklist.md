# v1 -> v2 Migration Checklist (Minimum Changes)

This one-page checklist is for third-party developers who already published a v1 (zip-based) store.  
Goal: migrate with minimal effort and keep one-click restore hints for existing users.

> For full protocol details, see:
> - [Third-party Store Guide](./third-party-store-guide.md)

## 5-Minute Migration Path

```text
v1 repository
  │
  ├─ 1) Add store-config.json
  │
  ├─ 2) Add required x-casaos.app_id to every app
  │
  ├─ 3) Normalize category to the 9 official categories
  │
  ├─ 4) Run build_appstore.py to generate dist/
  │
  ├─ 5) Deploy dist/ to static hosting (URL = --base-url)
  │
  └─ 6) (Recommended) Include the same store-config.json in v1 zip
         -> users can see one-click "restore old store" in v2
```

## Do These 6 Steps in Order

## 1. Add `store-config.json` (Required)

Create this file at repo root:

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
- `store_id` is globally unique
- `store_id` uses only letters, digits, dots (`.`), underscores (`_`), and hyphens (`-`)
- uppercase input is normalized to lowercase during build
- `store_id` contains at least one letter or digit
- at least `name.en_US` is present

## 2. Add `x-casaos.app_id` to Every App (Required)

Add an app identifier to each app's top-level `x-casaos` block:

```yaml
x-casaos:
  app_id: com.example.myapp
```

Checks:
- every source `docker-compose.yml` includes `x-casaos.app_id`
- use reverse-domain style such as `com.example.myapp`
- use only letters, digits, dots (`.`), underscores (`_`), and hyphens (`-`)
- uppercase input is normalized to lowercase during build
- the value contains at least one letter or digit
- the value contains at least two non-empty dot-separated segments

## 3. Normalize App Categories (Required)

Set every app `x-casaos.category` to one of:

`Media`, `Productivity`, `Home`, `Networking`, `AI`, `Finance`, `Social`, `Developer`, `Others`

## 4. Build v2 Output (Required)

```bash
python3 scripts/build_appstore.py \
  --source . \
  --output dist \
  --base-url "https://your-store-domain"
```

Checks:
- `dist/{locale}/store.json` exists
- `dist/{locale}/index.json` exists
- `dist/{locale}/apps/<app-id>/docker-compose.yml` and `meta.json` exist
- generated `index.json`, `meta.json`, and `docker-compose.yml` include `app_id`

## 5. Deploy `dist/` to Static Hosting (Required)

Use GitHub Pages / Netlify / Cloudflare Pages / self-hosted Nginx.  
The store URL users add should match your `--base-url`.

## 6. Keep v1 -> v2 Migration Hints (Strongly Recommended)

In the v1/v2 coexistence phase, `store-config.json` is already mandatory for v2 stores.

For migration reminders, the only extra requirement is:

- Include the same `store-config.json` file in your v1 zip package

Client behavior:

- If v1 zip contains `store-config.json`, users can see a one-click "restore old store" prompt after upgrading to v2
- If v1 zip does not contain `store-config.json`, users can still re-add manually, but no migration reminder is shown.

## 30-Second Pre-Release Check

- [ ] `store-config.json` is present and valid
- [ ] every app has a valid `x-casaos.app_id`
- [ ] all app `category` fields are normalized
- [ ] `dist/{locale}/store.json` is reachable
- [ ] `dist/{locale}/index.json` is reachable
- [ ] v1 zip package includes the same `store-config.json` (if you have v1 users)
