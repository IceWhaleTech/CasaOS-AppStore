# CI/CD 总览

CI/CD 说明源码文件如何被校验、构建并发布成商店产物。

对大多数第三方商店来说，实际目标是：

1. 在 pull request 上校验应用 compose
2. 构建 v2 `dist/`
3. 按需构建旧版 v1 `dist/store/main.zip`
4. 将 `dist/` 发布到静态托管

## 当前官方工作流拆分

本仓库使用三个主要 GitHub Actions workflow：

- [`validator.yml`](https://github.com/IceWhaleTech/CasaOS-AppStore/blob/main/.github/workflows/validator.yml)：校验 compose 文件并运行完整 v2 构建检查。
- [`release.yml`](https://github.com/IceWhaleTech/CasaOS-AppStore/blob/main/.github/workflows/release.yml)：构建 v2 和 v1 产物，供检查或复用。
- [`release-store.yml`](https://github.com/IceWhaleTech/CasaOS-AppStore/blob/main/.github/workflows/release-store.yml)：将带 tag 的商店输出发布到 `gh-pages` 和 GitHub Releases。

## 工作流职责

| Workflow | 触发时机 | 主要作用 | 主要产物 |
|---|---|---|---|
| Validator | pull request 或手动运行 | 尽早发现无效源码 | 校验与构建报告 |
| Release | 推送到 `main` 或手动运行 | 生成可复用构建产物 | `dist/`、`main.zip`、报告 |
| Release-store | release tag 或手动运行 | 发布商店 | `gh-pages`、GitHub Release 资源 |

## 仓库内 action

这些 workflow 由几个小 action 组成：

- `validate-compose`：校验源码 compose。
- `build-store-v2`：对 `IceWhaleTech/build-appstore-action` 的仓库内包装。
- `build-store-v1`：构建旧版 `main.zip`。
- `write-job-summary`：将报告 JSON 写入 GitHub Actions summary。
- `render-report`：需要时将报告 JSON 转为 HTML。

外部维护者推荐直接使用公开入口 `IceWhaleTech/build-appstore-action`。见 [复用官方 Actions](official-actions-and-workflows.md)。

## 构建报告和 job summary

当设置了 `report-json` 时，v2 构建 action 会写出结构化 report JSON。本仓库会上传这份 report artifact，并把它渲染到 GitHub Actions job summary。

查看方式：

1. 打开对应的 GitHub Actions run。
2. 进入相关 job，例如 `validate`、`build` 或 `release`。
3. 在 job 页面顶部查看 summary。
4. 需要完整细节时，下载对应的 report artifact。

常见 artifact 名称：

- `validation-report`
- `build-v2-validation-report`
- `build-v2-report`
- `release-build-v2-report`

summary 会包含构建状态、应用数量、warning/error 数量、主要问题、生成产物和仓库上下文。

## 构建错误行为

action 会区分应用级问题和全局失败。

应用级错误会被收集起来，后续应用仍会继续处理。只要存在应用级 error，report 会先写出，v2 构建最终仍会失败。常见例子包括应用元数据无效、缺少必需的 `x-casaos.id`、引用资源缺失、YAML 无效、架构不匹配。

warning 会被记录，但只要仍能生成输出，就不会让 v2 构建失败。常见例子包括缺少 `supported-languages.json`、没有顶层 `x-casaos` 的应用目录被跳过、registry 限流、镜像 digest pinning 失败、镜像大小估算失败、`x-casaos.version` 不是 semver。

全局失败会让整个仓库构建停止。常见例子包括 `base-url` 无效、缺少 `Apps/`、store config JSON 无效、`store_id` 无效、`supported-languages.json` 无效，或依赖安装失败。

## 兼容行为

官方工作流会有意同时构建两类输出：

- 面向新客户端的 v2 静态文件
- 面向旧客户端的 v1 `dist/store/main.zip`

如果你的商店是全新的，并且不需要 v1 支持，可以省略 v1 构建步骤。

## 下一步

- [复用官方 Actions](official-actions-and-workflows.md)
- [Validator 工作流](validator-workflow.md)
- [Release 工作流](release-workflow.md)
- [Release-store 工作流](release-store-workflow.md)
