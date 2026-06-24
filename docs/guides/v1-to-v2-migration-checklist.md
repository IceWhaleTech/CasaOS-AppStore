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
  ├─ 2) Normalize category to the 9 official categories
  │
  ├─ 3) Run build_appstore.py to generate dist/
  │
  ├─ 4) Deploy dist/ to static hosting (URL = --base-url)
  │
  └─ 5) (Recommended) Include the same store-config.json in v1 zip
         -> users can see one-click "restore old store" in v2
```

## Do These 5 Steps in Order

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
- `store_id` is globally unique and matches `[a-z0-9-]`
- at least `name.en_US` is present

## 2. Normalize App Categories (Required)

Set every app `x-casaos.category` to one of:

`Media`, `Productivity`, `Home`, `Networking`, `AI`, `Finance`, `Social`, `Developer`, `Others`

## 3. Build v2 Output (Required)

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

## 4. Deploy `dist/` to Static Hosting (Required)

Use GitHub Pages / Netlify / Cloudflare Pages / self-hosted Nginx.  
The store URL users add should match your `--base-url`.

## 5. Keep v1 -> v2 Migration Hints (Strongly Recommended)

In the v1/v2 coexistence phase, `store-config.json` is already mandatory for v2 stores.

For migration reminders, the only extra requirement is:

- Include the same `store-config.json` file in your v1 zip package

Client behavior:

- If v1 zip contains `store-config.json`, users can see a one-click "restore old store" prompt after upgrading to v2
- If v1 zip does not contain `store-config.json`, users can still re-add manually, but no migration reminder is shown.

## 30-Second Pre-Release Check

- [ ] `store-config.json` is present and valid
- [ ] all app `category` fields are normalized
- [ ] `dist/{locale}/store.json` is reachable
- [ ] `dist/{locale}/index.json` is reachable
- [ ] v1 zip package includes the same `store-config.json` (if you have v1 users)
