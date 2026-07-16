# 协议规范总览

这一部分是商店 v2 协议的权威参考。

任务流程请看新建和迁移指南；当你需要确认必要文件、字段含义或构建产物行为时，再查这一部分。

## 必要源码文件

v2 源码仓库由这些内容构建：

- `store-config.json`：商店身份和商店级本地化字段。
- `supported-languages.json`：候选语言列表。
- `Apps/<App>/docker-compose.yml`：应用运行时配置和顶层 `x-casaos` 元数据。
- 每个应用引用的资源，常见为 `icon`、`thumbnail` 和 `screenshot-{n}` 文件。

## 生成文件

构建会在 `dist/` 下生成静态协议产物：

- `store.json` 和可选的 `store.{locale}.json`
- `index.json` 和可选的 `index.{locale}.json`
- `apps/<app-id>/docker-compose.yml`
- 可选的架构专用 compose 文件
- `apps/<app-id>/meta.json` 和可选的 `meta.{locale}.json`
- `apps/<app-id>/assets/*`

`<app-id>` 是源码顶层 `x-casaos.id` 规范化后的值。

## 阅读顺序

1. [商店配置](store-config.md)：根目录商店身份文件和字段。
2. [Compose 与应用元数据](compose-and-x-casaos.md)：应用源码 compose 和每个顶层 `x-casaos` 字段。
3. [构建产物](build-output.md)：生成文件、列表字段、元数据拆分、路径和 `content_hash`。
4. [资源与本地化](assets-and-i18n.md)：资源处理、locale key 和本地化文本产物规则。

## 相关任务指南

- [创建应用商店](../quick-start/overview.md)
- [从 v1 迁移](../migration/overview.md)
- [CI/CD 总览](../cicd/overview.md)
