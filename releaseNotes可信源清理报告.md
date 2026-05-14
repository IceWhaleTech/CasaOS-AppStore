# releaseNotes 可信源清理报告

- 生成时间：`2026-05-14 15:20:00`
- 应用总数：`163`
- 保留 releaseNotes：`110`
- 清空 releaseNotes：`53`
- 首轮 GitHub Release 命中：`88`
- 首轮 GitLab Release 命中：`1`
- 官方文档/官网补充恢复：`21`

## 处理口径

- 先查官方 GitHub/GitLab release tag。
- 再补查 compose 中的 `website` / `docs` / `repo` / `support` 指向的官方文档、官网 changelog、官方发布页。
- 只有能和当前 `version` 或镜像 tag 关联上的可信来源才保留 `releaseNotes`；找不到可信来源的留空。

## 补充恢复清单

| app | version | source_status | source |
| --- | --- | --- | --- |
| Anaconda3 | `2024.10-1` | `verified_official_docs_manual` | https://www.anaconda.com/docs/getting-started/anaconda/release/2024 |
| Emby | `4.9.1` | `verified_github_release_manual` | https://github.com/MediaBrowser/Emby.Releases/releases/tag/4.9.1.80 |
| Emby_Nvidia | `4.9.1` | `verified_github_release_manual` | https://github.com/MediaBrowser/Emby.Releases/releases/tag/4.9.1.80 |
| Embystat | `0.2.0` | `verified_github_release_prefix` | https://github.com/mregni/EmbyStat/releases/tag/0.2.0-beta.38 |
| FlowiseAi | `3.0.11` | `verified_github_release_manual` | https://github.com/FlowiseAI/Flowise/releases/tag/flowise%403.0.11 |
| Gitea | `1.25` | `verified_github_release_exact` | https://github.com/go-gitea/gitea/releases/tag/v1.25.0 |
| HomeAssistant | `2025.11` | `verified_github_release_exact` | https://github.com/home-assistant/core/releases/tag/2025.11.0 |
| Lidarr | `3.1.0` | `verified_github_release_prefix` | https://github.com/Lidarr/Lidarr/releases/tag/v3.1.0.4875 |
| MariaDB | `11.4.8` | `verified_official_docs` | https://mariadb.com/docs/release-notes/ |
| Memos | `0.25` | `verified_github_release_exact` | https://github.com/usememos/memos/releases/tag/v0.25.0 |
| Mongo | `8.2.2` | `verified_official_docs` | https://www.mongodb.com/docs/manual/release-notes/8.2/ |
| N8n | `1.123.0` | `verified_github_release_variant` | https://github.com/n8n-io/n8n/releases/tag/n8n%401.123.0 |
| Nextcloud | `32.0` | `verified_github_release_exact` | https://github.com/nextcloud/server/releases/tag/v32.0.0 |
| OpenHands | `0.59` | `verified_github_release_exact` | https://github.com/All-Hands-AI/OpenHands/releases/tag/0.59.0 |
| PhotoPrism | `250228` | `verified_github_release_prefix` | https://github.com/photoprism/photoprism/releases/tag/250228-43447fa38 |
| PostgreSQL | `17.4` | `verified_official_docs` | https://www.postgresql.org/docs/release/17.4/ |
| Prowlarr | `2.3.5` | `verified_github_release_prefix` | https://github.com/Prowlarr/Prowlarr/releases/tag/v2.3.5.5327 |
| Radarr | `6.1.1` | `verified_github_release_prefix` | https://github.com/Radarr/Radarr/releases/tag/v6.1.1.10360 |
| Sonarr | `4.0.17` | `verified_github_release_prefix` | https://github.com/Sonarr/Sonarr/releases/tag/v4.0.17.2967 |
| Unifi-controller | `8.0.7` | `verified_github_release_prefix` | https://github.com/linuxserver-archive/docker-unifi-controller/releases/tag/8.0.7-ls218 |
| UptimeKuma | `1.23.16-alpine` | `verified_github_release_exact` | https://github.com/louislam/uptime-kuma/releases/tag/1.23.16 |

## 已清空清单

| app | version | reason | checked/source |
| --- | --- | --- | --- |
| AnythingLLM | `latest` | `no_release_for_candidates` | `latest=404` |
| ChatbotUI | `main` | `no_release_for_candidates` | `main=404` |
| Cloudflared | `2025.2.1` | `no_release_for_candidates` | `2025.2.1=404; v2025.2.1=404` |
| Databag | `0.1.18` | `no_release_for_candidates` | `0.1.18=404; v0.1.18=404` |
| DeepSeek-OCR_Nvidia | `v2.2.0` | `no_release_for_candidates` | `v2.2.0=404; 2.2.0=404` |
| Deluge | `2.2.0` | `no_release_for_candidates` | `2.2.0=404; v2.2.0=404` |
| DuckDNS | `latest` | `no_release_for_candidates` | `latest=404` |
| Duplicati | `2.1.0` | `no_release_for_candidates` | `2.1.0=404; v2.1.0=404` |
| Excalidraw | `latest` | `no_release_for_candidates` | `latest=404` |
| Filedrop | `1.0.1` | `repo_empty` | `` |
| FileFlows | `stable` | `repo_empty` | `` |
| Firefly | `latest` | `no_release_for_candidates` | `latest=404` |
| HermesAgent | `latest` | `no_release_for_candidates` | `latest=404` |
| HoloPlay | `1.12.3` | `no_release_for_candidates` | `1.12.3=404; v1.12.3=404` |
| Homebridge | `latest` | `no_release_for_candidates` | `latest=404` |
| Index-TTS | `2.0` | `no_release_for_candidates` | `2.0=404; v2.0=404` |
| Index-TTS_Nvidia | `2.0` | `no_release_for_candidates` | `2.0=404; v2.0=404` |
| JDownloader2 | `latest` | `repo_empty` | `` |
| Jenkin | `lts-jdk17` | `no_release_for_candidates` | `lts-jdk17=404` |
| Lazylibrarian | `version-169e669f` | `no_release_for_candidates` | `version-169e669f=404` |
| LibreChat | `latest` | `no_release_for_candidates` | `latest=404` |
| Maybe | `latest` | `no_release_for_candidates` | `latest=404` |
| Medusa | `master` | `no_release_for_candidates` | `master=404` |
| MineOS | `latest` | `no_release_for_candidates` | `latest=404` |
| MongoDB4 | `4.4.22` | `no_release_for_candidates` | `4.4.22=404; v4.4.22=404` |
| Motioneye | `master-amd64` | `no_release_for_candidates` | `master-amd64=404` |
| Nzbget | `25.4.20251205` | `no_release_for_candidates` | `25.4.20251205=404; v25.4.20251205=404` |
| OpenSpeedTest | `v2.0.6` | `no_release_for_candidates` | `v2.0.6=404; 2.0.6=404` |
| OpenWebUI | `ollama` | `no_release_for_candidates` | `ollama=404` |
| oPodSync | `latest` | `no_release_for_candidates` | `latest=404` |
| Petio | `sha256:1c5a9276a844f4284601cbe332905864950545ebdeaad74bacb9097ea4f4b333` | `no_release_for_candidates` | `sha256:1c5a9276a844f4284601cbe332905864950545ebdeaad74bacb9097ea4f4b333=404` |
| Pihole | `2025.11.1` | `no_release_for_candidates` | `2025.11.1=404; v2025.11.1=404` |
| Pinchflat | `latest` | `no_release_for_candidates` | `latest=404` |
| Pingvin-Share | `latest` | `no_release_for_candidates` | `latest=404` |
| playit-agent | `latest` | `no_release_for_candidates` | `latest=404` |
| Plex | `1.41.3` | `no_release_for_candidates` | `1.41.3=404; v1.41.3=404` |
| Plex_Nvidia | `1.41.3` | `no_release_for_candidates` | `1.41.3=404; v1.41.3=404` |
| PyLoad | `0.5.0` | `no_release_for_candidates` | `0.5.0=404; v0.5.0=404` |
| RDTClient | `2` | `no_release_for_candidates` | `2=404; v2=404` |
| Readarr | `0.3.10-develop` | `no_release_for_candidates` | `0.3.10-develop=404; v0.3.10-develop=404` |
| Resilio-sync | `2.7.3` | `no_release_for_candidates` | `2.7.3=404; v2.7.3=404` |
| RetroArch | `latest` | `no_release_for_candidates` | `latest=404` |
| Snapdrop | `version-eac78009` | `no_release_for_candidates` | `version-eac78009=404` |
| StableDiffusionWebUI | `latest` | `no_release_for_candidates` | `latest=404` |
| Teable | `latest` | `no_release_for_candidates` | `latest=404` |
| Threadfin | `latest` | `no_release_for_candidates` | `latest=404` |
| TurboDiffusion_Nvidia | `20260312` | `no_release_for_candidates` | `20260312=404; v20260312=404` |
| Twingate | `1` | `repo_empty` | `` |
| Unifi-Network-Application | `latest` | `no_release_for_candidates` | `latest=404` |
| VirtualMachineManager | `latest` | `no_release_for_candidates` | `latest=404` |
| VoceChat | `v0.3.33` | `no_release_for_candidates` | `v0.3.33=404; 0.3.33=404` |
| WebDav | `amd64` | `no_release_for_candidates` | `amd64=404` |
| WireGuardEasy | `13` | `no_release_for_candidates` | `13=404; v13=404` |

## 输出文件

- `releaseNotes可信源校验表.csv`
- `releaseNotes可信源汇总.json`
