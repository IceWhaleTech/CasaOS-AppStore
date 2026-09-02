# Store Config

`store-config.json` defines store identity at the repository level.

## Purpose

The build script reads `store-config.json` and generates:

- `dist/store.json`
- `dist/store.{locale}.json` for locales explicitly defined in store localized text fields

## Minimal example

```json
{
  "version": 2,
  "store_id": "my-awesome-apps",
  "name": {
    "en_US": "My Awesome Apps",
    "zh_CN": "我的应用商店"
  },
  "description": {
    "en_US": "A collection of apps for home server enthusiasts"
  },
  "maintainer": "your-github-username",
  "url": "https://github.com/username/my-appstore"
}
```

## Fields

| Field | Type | Required | Notes |
|------|------|----------|------|
| `version` | `int` | Yes | Must be `2` |
| `store_id` | `string` | Yes | Unique store identifier |
| `name` | `object` | Yes | Locale-keyed display name |
| `description` | `object` | No | Locale-keyed store description |
| `maintainer` | `string` | Yes | Maintainer or owner name |
| `url` | `string` | No | Project or homepage URL |
| `icon` | `string` | No | Store icon URL |

## Field reference

### `version`

- required
- must be the integer `2`
- identifies the source protocol version used by the build flow

### `store_id`

- required
- primary identity of the store
- should remain stable after users start subscribing
- should be chosen as a globally distinctive value

### `name`

- required
- must be a locale-keyed object, not a plain string
- should always include `en_US`
- becomes the display name in generated `store.json`

### `description`

- optional
- locale-keyed object
- useful for store overview text shown in clients

### `maintainer`

- required
- plain string naming the store maintainer, owner, or organization

### `url`

- optional
- public project, repository, or homepage URL

### `icon`

- optional
- public store-level icon URL
- unlike per-app assets, this is not generated from an app directory asset pipeline

## `store_id` rules

- letters, digits, `.`, `_`, and `-` only
- uppercase input is allowed but normalized to lowercase
- must contain at least one letter or digit
- must be globally distinctive
- do not use reserved values such as `zimaos-appstore`

## Validation expectations

Treat these as source contract rules:

- the file must be valid JSON
- `version` must match the active protocol version
- `name` should be an object
- locale keys should use `ll_CC` format
- URL fields should already be public and reachable

## Localization behavior

The build script resolves store-level localized text from:

- `name`
- `description`

Only locales explicitly defined in these fields are emitted as `store.{locale}.json`.

## Output behavior

The build script always emits a default-locale file:

- `dist/store.json`

It additionally emits locale-suffixed files only when that locale is explicitly present in store localized text:

- `dist/store.zh_CN.json`
- `dist/store.de_DE.json`

This keeps the output small while still supporting localized store metadata.

## Input to output mapping

| Source field | Generated location | Notes |
|---|---|---|
| `version` | `store.json.version` | carried through as protocol metadata |
| `store_id` | `store.json.store_id` | normalized during build if needed |
| `name.<locale>` | `store.{locale}.name` | resolved per locale file |
| `description.<locale>` | `store.{locale}.description` | emitted only for explicit locales |
| `maintainer` | `store.json.maintainer` | copied as plain string |
| `url` | `store.json.url` | copied as plain string |
| `icon` | `store.json.icon` | copied as plain string URL |

## Practical guidance

- Always provide `name.en_US`
- Add `description` when the store needs a visible introduction in the client
- Keep `store_id` stable once users start subscribing to your store

## Common mistakes

- writing `name` as a plain string instead of a locale-keyed object
- changing `store_id` after clients already use the store
- using locale keys like `en_us` instead of `en_US`
- assuming every locale in `supported-languages.json` will automatically produce `store.{locale}.json`
