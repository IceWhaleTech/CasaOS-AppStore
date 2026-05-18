# Metadata Fix Review Record

This file records the app metadata changes made from the CSV repair list so the
changes can be reviewed later.

## Confirmed Rules

- `releaseNotes` should use official release notes when reasonably sized. If
  the official changelog is very long, an AI summary is acceptable, but it must
  not add facts that are not present upstream.
- If the Docker image tag and the upstream application release do not match,
  find the release notes for the actual application version used by the app.
- If a GitHub tag exists but the GitHub Release API has no release object, look
  for release notes on the official website or other official changelog pages.
- If a GitHub Release body is empty, first look for official release notes
  elsewhere; use compare/tag diffs only when no better source exists.
- For `latest`, `main`, and `master` tags, do not change the tag for now; use
  release notes for the latest actual version.
- Digest-style versions such as `sha256:*` stay as-is for now.
- For `website`, prefer the product homepage. Use docs only when the product
  effectively has no separate homepage.
- For multi-service apps, `version` follows the main application.
- `releaseNotes` should include multiple locales, not only `en_US`.

## Pushed Checkpoints

| Commit | Summary | Review scope |
| --- | --- | --- |
| `430349f` | `fix verified app metadata issues` | Filled blank release notes, fixed one incorrect release note, and canonicalized a small set of links. |
| `52d408f` | `add localized release notes` | Added multiple locale entries for the release notes introduced in `430349f`. |
| `8b07888` | `localize verified release notes` | Localized additional verified release notes. |
| `48d6c80` | `localize additional release notes` | Localized another batch of verified release notes. |

## Current Batch

| App | Field | Action | Source / evidence | Review note |
| --- | --- | --- | --- | --- |
| TaskingAI | `website` | No change after review | `https://www.tasking.ai/` returned 404; `https://docs.tasking.ai/` returned 200. | Keeping docs as website is consistent with the rule when no usable product homepage is found. |
| Trilium | `website` | No change after review | `https://triliumnext.github.io/` returned 404; `https://triliumnext.github.io/Docs/` returned 200. | Keeping docs as website is consistent with the rule when no usable product homepage is found. |
| CloudBeaver | `releaseNotes` | Added `zh_CN`, `de_DE`, `fr_FR`, `ja_JP`, and `ko_KR` translations for the existing `en_US` note. | GitHub Release API for `dbeaver/cloudbeaver` tag `25.2.5` has no release object; GitHub web tag page exists. | Kept the note as a source-mapping explanation instead of inventing release details. |
| Crafty | `releaseNotes` | Added `zh_CN`, `de_DE`, `fr_FR`, `ja_JP`, and `ko_KR` translations for the existing `en_US` note. | Upstream release source is the Crafty GitLab release path from the CSV. | Kept the note tied to the GitLab release source. |
| ESPHome | `releaseNotes` | Added `zh_CN`, `de_DE`, `fr_FR`, `ja_JP`, and `ko_KR` translations for the existing `en_US` note. | Official ESPHome 2025.11.0 changelog URL from the CSV. | Kept this as a pointer note because the official changelog is long. |
| Logseq | `releaseNotes` | Added `zh_CN`, `de_DE`, `fr_FR`, `ja_JP`, and `ko_KR` translations for the existing `en_US` note. | GitHub tag exists, but no GitHub Release object is published for the tag. | Kept the note as an explicit source limitation. |
| Ombi | `releaseNotes` | Added `zh_CN`, `de_DE`, `fr_FR`, `ja_JP`, and `ko_KR` translations for the existing `en_US` note. | GitHub Release page exists for `v4.47.1`, but body is empty. | Kept the note as an exact-tag limitation rather than adding compare-derived details. |
| PsiTransfer | `releaseNotes` | Added `zh_CN`, `de_DE`, `fr_FR`, `ja_JP`, and `ko_KR` translations for the existing `en_US` note. | Existing note was already tied to the v2.4.1 source/commit context from the CSV. | No version or port metadata changed. |
| CopyParty | `releaseNotes` | Added `zh_CN`, `de_DE`, `fr_FR`, `ja_JP`, and `ko_KR` translations for the existing `en_US` summary. | GitHub release `v1.20.13` from the CSV. | Preserved the existing summary; did not copy the long upstream changelog verbatim. |
| Jellyfin | `releaseNotes` | Added `zh_CN`, `de_DE`, `fr_FR`, `ja_JP`, and `ko_KR` translations for the existing `en_US` summary. | Jellyfin Server `10.10.7` release forum URL from the CSV. | Preserved reverse-proxy warning and fix summary. |
| Jellyfin_Nvidia | `releaseNotes` | Added `zh_CN`, `de_DE`, `fr_FR`, `ja_JP`, and `ko_KR` translations for the existing `en_US` summary. | Jellyfin Server `10.10.6` release forum URL from the CSV. | Nvidia entry kept aligned to the configured Jellyfin image version. |
| Lucky | `releaseNotes` | Added `zh_CN`, `de_DE`, `fr_FR`, `ja_JP`, and `ko_KR` translations for the existing `en_US` summary. | GitHub release `v2.20.2` from the CSV. | Preserved the concise summary of certificate, OIDC, ACME, and Filebrowser changes. |
| RomM | `releaseNotes` | Added `zh_CN`, `de_DE`, `fr_FR`, `ja_JP`, and `ko_KR` translations for the existing `en_US` summary. | GitHub release `4.0.1` from the CSV. | Preserved the concise task-system and fix summary. |
| Sickchill | `releaseNotes` | Added `zh_CN`, `de_DE`, `fr_FR`, `ja_JP`, and `ko_KR` translations for the existing `en_US` summary. | GitHub release body is empty; existing note is based on upstream tag compare. | Did not add new compare-derived facts beyond the existing note. |
| Tailscale | `releaseNotes` | Added `zh_CN`, `de_DE`, `fr_FR`, `ja_JP`, and `ko_KR` translations for the existing `en_US` summary. | Tailscale changelog URL from the CSV. | Preserved TS-2025-008 container-image note. |
| TaskingAI | `releaseNotes` | Added `zh_CN`, `de_DE`, `fr_FR`, `ja_JP`, and `ko_KR` translations for the existing `en_US` summary. | GitHub compare `v0.2.2...v0.3.0` from the CSV. | Preserved the main-app version summary; website field left unchanged after review. |
| ArchiveBox | `releaseNotes` | Added `zh_CN`, `de_DE`, `fr_FR`, `ja_JP`, and `ko_KR` translations for the existing `en_US` summary. | GitHub release `v0.7.3` from the CSV. | Kept the Docker-dependency summary; did not add Python-code changes. |
| BeaverHabitTracker | `releaseNotes` | Added `zh_CN`, `de_DE`, `fr_FR`, `ja_JP`, and `ko_KR` translations for the existing `en_US` summary. | GitHub release `v0.7.3` from the CSV. | Preserved the short Python/NiceGUI stack update note. |
| ChatGPT-Next-Web | `releaseNotes` | Added `zh_CN`, `de_DE`, `fr_FR`, `ja_JP`, and `ko_KR` translations for the existing `en_US` summary. | GitHub release `v2.16.1` from the CSV. | Kept the existing AI-provider/model and frontend-build summary. |
| Emby | `releaseNotes` | Added `zh_CN`, `de_DE`, `fr_FR`, `ja_JP`, and `ko_KR` translations for the existing `en_US` summary. | Existing note describes Emby Server `4.9.1`. | Kept the standard Emby entry aligned to the main app version. |
| Emby_Nvidia | `releaseNotes` | Added `zh_CN`, `de_DE`, `fr_FR`, `ja_JP`, and `ko_KR` translations for the existing `en_US` summary. | Existing note describes Emby Server `4.9.1`. | GPU entry kept aligned with the standard Emby release metadata. |
| FlareSolverr | `releaseNotes` | Added `zh_CN`, `de_DE`, `fr_FR`, `ja_JP`, and `ko_KR` translations for the existing `en_US` summary. | GitHub release `v3.4.5` from the CSV. | Preserved runtime and Dockerfile/changelog-generation fix note. |
| FreshRSS | `releaseNotes` | Added `zh_CN`, `de_DE`, `fr_FR`, `ja_JP`, and `ko_KR` translations for the existing `en_US` summary. | FreshRSS `1.27.1` changelog URL from the CSV. | Preserved security-fix summary. |
| HomeAssistant | `releaseNotes` | Added `zh_CN`, `de_DE`, `fr_FR`, `ja_JP`, and `ko_KR` translations for the existing `en_US` summary. | Home Assistant 2025.11 release URL from the CSV. | Kept the summary because the official changelog is long. |
| LLaMA-Factory_Nvidia | `releaseNotes` | Added `zh_CN`, `de_DE`, `fr_FR`, `ja_JP`, and `ko_KR` translations for the existing `en_US` summary. | GitHub release `v0.9.4` from the CSV. | Kept the main-app version summary for the Nvidia entry. |
| Node-RED | `releaseNotes` | Added `zh_CN`, `de_DE`, `fr_FR`, `ja_JP`, and `ko_KR` translations for the existing `en_US` summary. | GitHub release `4.1.2` from the CSV. | Preserved the bugfix-only summary. |
| RagFlow | `releaseNotes` | Added `zh_CN`, `de_DE`, `fr_FR`, `ja_JP`, and `ko_KR` translations for the existing `en_US` summary. | GitHub release `v0.21.1` from the CSV. | Preserved MinerU/Infinity/video parsing summary. |
| Transmission | `releaseNotes` | Added `zh_CN`, `de_DE`, `fr_FR`, `ja_JP`, and `ko_KR` translations for the existing `en_US` summary. | GitHub release `4.0.4` from the CSV. | Preserved bugfix-only release summary. |
| Embystat | `releaseNotes` | Added `zh_CN`, `de_DE`, `fr_FR`, `ja_JP`, and `ko_KR` translations for the existing `en_US` note. | Existing note records that configured EmbyStat `0.2.0` does not map to a matching stable GitHub Release object. | No new release facts added; source-limitation wording preserved. |
| Lidarr | `releaseNotes` | Added `zh_CN`, `de_DE`, `fr_FR`, `ja_JP`, and `ko_KR` translations for the existing `en_US` summary. | Existing note summarizes Lidarr `3.1.0`. | Preserved IPv6, qBittorrent login-check, and Docker update guidance. |
| Mongo | `releaseNotes` | Added `zh_CN`, `de_DE`, `fr_FR`, `ja_JP`, and `ko_KR` translations for the existing `en_US` note. | Existing note records MongoDB `8.2.2` as the database image version. | No version/tag changes; Docker tag remains image metadata. |
| PhotoPrism | `releaseNotes` | Added `zh_CN`, `de_DE`, `fr_FR`, `ja_JP`, and `ko_KR` translations for the existing `en_US` summary. | Existing note summarizes PhotoPrism build `250228`. | Preserved Retina 5K thumbnail, viewer, WebDAV, and M4V details. |
| PostgreSQL | `releaseNotes` | Added `zh_CN`, `de_DE`, `fr_FR`, `ja_JP`, and `ko_KR` translations for the existing `en_US` summary. | Existing note summarizes PostgreSQL `17.4`. | Preserved CVE-2025-1094/libpq, pg_createsubscriber, and Meson details. |
| Unifi-controller | `releaseNotes` | Added `zh_CN`, `de_DE`, `fr_FR`, `ja_JP`, and `ko_KR` translations for the existing `en_US` note. | Existing note records UniFi Controller `8.0.7` as the application version. | No additional release details added because the existing note points to UniFi release notes. |
| MongoDB4 | `releaseNotes` | Replaced blank releaseNotes with `en_US`, `zh_CN`, `de_DE`, `fr_FR`, `ja_JP`, and `ko_KR` notes. | Official MongoDB Community release announcement for `4.4.22`: `https://www.mongodb.com/community/forums/t/mongodb-4-4-22-is-released/227152`. | Used the official fixed-issue summary; no Docker tag/version changes. |
| Pihole | `releaseNotes` | Replaced blank releaseNotes with `en_US`, `zh_CN`, `de_DE`, `fr_FR`, `ja_JP`, and `ko_KR` notes. | Official `pi-hole/docker-pi-hole` GitHub release `2025.11.1`: `https://github.com/pi-hole/docker-pi-hole/releases/tag/2025.11.1`. | Summarized Docker-specific changes plus bundled FTL/Web/Core versions from the official release body. |
| Index-TTS | `releaseNotes` | Replaced blank releaseNotes with `en_US`, `zh_CN`, `de_DE`, `fr_FR`, `ja_JP`, and `ko_KR` notes. | Official `index-tts/index-tts` README update for IndexTTS-2: `https://github.com/index-tts/index-tts`. | Used upstream IndexTTS2 feature summary; no image/version changes. |
| Index-TTS_Nvidia | `releaseNotes` | Replaced blank releaseNotes with `en_US`, `zh_CN`, `de_DE`, `fr_FR`, `ja_JP`, and `ko_KR` notes. | Official `index-tts/index-tts` README update for IndexTTS-2: `https://github.com/index-tts/index-tts`. | Kept Nvidia entry aligned to the same main application version. |
| WireGuardEasy | `releaseNotes` | Replaced blank releaseNotes with `en_US`, `zh_CN`, `de_DE`, `fr_FR`, `ja_JP`, and `ko_KR` notes. | Official `wg-easy/wg-easy` GitHub release `v13.0.0`: `https://github.com/wg-easy/wg-easy/releases/tag/v13.0.0`. | Used only the concise official release body: h3 framework, `UI_CHART_TYPE`, and bug fixes. |
| AnythingLLM | `releaseNotes` | Replaced blank releaseNotes with latest-release notes in `en_US`, `zh_CN`, `de_DE`, `fr_FR`, `ja_JP`, and `ko_KR`; kept `version: latest`. | Official GitHub latest release `v1.12.1`: `https://github.com/Mintplex-Labs/anything-llm/releases/tag/v1.12.1`. | Applied the confirmed floating-tag rule: tag unchanged, releaseNotes use latest actual upstream release. |
| Homebridge | `releaseNotes` | Replaced blank releaseNotes with latest-release notes in `en_US`, `zh_CN`, `de_DE`, `fr_FR`, `ja_JP`, and `ko_KR`; kept `version: latest`. | Official GitHub latest release `v1.9.0`: `https://github.com/homebridge/homebridge/releases/tag/v1.9.0`. | Used upstream release body and dependency note. |
| Pinchflat | `releaseNotes` | Replaced blank releaseNotes with latest-release notes in `en_US`, `zh_CN`, `de_DE`, `fr_FR`, `ja_JP`, and `ko_KR`; kept `version: latest`. | Official GitHub latest release `v2025.9.26`: `https://github.com/kieraneglin/pinchflat/releases/tag/v2025.9.26`. | Preserved the important upstream issue pointer and Dockerfile change. |
| Pingvin-Share | `releaseNotes` | Replaced blank releaseNotes with latest-release notes in `en_US`, `zh_CN`, `de_DE`, `fr_FR`, `ja_JP`, and `ko_KR`; kept `version: latest`. | Official GitHub latest release `v1.13.0`: `https://github.com/stonith404/pingvin-share/releases/tag/v1.13.0`. | Repository is archived, but latest release body is available and was used directly. |
| Teable | `releaseNotes` | Replaced blank releaseNotes with latest-release notes in `en_US`, `zh_CN`, `de_DE`, `fr_FR`, `ja_JP`, and `ko_KR`; kept `version: latest`. | Official GitHub latest release `release.2026-05-12T16-05-24Z.1665`: `https://github.com/teableio/teable/releases/tag/release.2026-05-12T16-05-24Z.1665`. | Summarized the official release body because it is long. |

## Deferred For Rule Confirmation

| Category | Current handling |
| --- | --- |
| 301/302 canonical URL changes | Do not continue changing these until the reviewed examples are accepted. |
| Floating tags | Keep image/version tag unchanged; release notes should later be checked against the latest actual app version. |
| Digest versions | Keep digest value unchanged. |
| Docker tags with no matching GitHub Release | Look for official project changelog before editing. |

## Remaining Deferred Items

These entries are still not patched because the current value is not a clear
application release version, or an official changelog for the exact configured
version was not found in this pass.

| App | Current version/tag | Reason kept deferred |
| --- | --- | --- |
| Cloudflared | `2025.2.1` | `wisdomsky/cloudflared-web` does not publish GitHub Releases; no official changelog for this exact image tag was found. |
| Databag | `0.1.18` | Configured Docker tag does not line up with the current upstream GitHub Releases, which are in the `v1.1.x` line. |
| DeepSeek-OCR_Nvidia | `v2.2.0` | Configured IceWhale image tags do not map to an official upstream `rdumasia303/deepseek_ocr_app` release note. |
| HoloPlay | `1.12.3` | Current GitHub Releases observed for upstream stop before this configured image tag, so exact release notes are not confirmed. |
| Jenkin | `lts-jdk17` | This is a moving Jenkins LTS image line, not a fixed application version. |
| Lazylibrarian | `version-169e669f` | This is a LinuxServer commit-style image tag; exact application release notes need source mapping before patching. |
| Motioneye | `master-amd64` | This is a branch/architecture-style tag rather than a fixed release. |
| OpenSpeedTest | `v2.0.6` | The upstream repository did not expose a GitHub Release object or official changelog for this exact tag in this pass. |
| OpenWebUI | `ollama` | This is an image flavor tag, not a fixed Open WebUI application release. |
| PyLoad | `0.5.0` | The configured `pyload-ng` image line does not expose clear official release notes for an exact stable `0.5.0` release. |
| RDTClient | `2` | This is a major-version Docker tag; the exact RDTClient application version must be resolved before releaseNotes can be accurate. |
| Readarr | `0.3.10-develop` | This is a develop image line; exact release-note source must be mapped to the actual application build first. |
| Resilio-sync | `2.7.3` | Official source for exact `2.7.3` release details was not confirmed in this pass. |
| Snapdrop | `version-eac78009` | This is a LinuxServer commit-style image tag; exact upstream app changes need commit/source mapping before patching. |
| TurboDiffusion_Nvidia | `20260312` | Configured image date tag does not map to an official upstream release note. |
| WebDav | `amd64` | This is an architecture tag, not an application release version. |
