# 构建产物

协议真正被客户端消费的是 `dist/` 下的构建产物。

## 输出文件

构建脚本可能生成：

- `dist/store.json`
- `dist/store.{locale}.json`
- `dist/index.json`
- `dist/index.{locale}.json`
- `dist/apps/<app-id>/docker-compose.yml`
- `dist/apps/<app-id>/docker-compose.{architecture}.yml`
- `dist/apps/<app-id>/meta.json`
- `dist/apps/<app-id>/meta.{locale}.json`
- `dist/apps/<app-id>/assets/*`

## `index.json`

`index.json` 是整个商店的应用索引。

单个应用项通常会包含：

- `id`
- `title`
- `tagline`
- `category`
- `version`
- `author`
- `developer`
- `architectures`
- `icon`
- `thumbnail`
- `compose_url`
- `meta_url`
- `content_hash`

### 列表字段含义

#### `id`

- 来自源码顶层 `x-casaos.id` 的规范化应用标识
- 同时作为 `dist/apps/` 下生成应用输出目录名

#### `title`

- 目标语言下解析后的应用显示名称

#### `tagline`

- 目标语言下解析后的短摘要

#### `category`

- 用于商店分组和展示的标准分类值

#### `version`

- 来自 `x-casaos.version` 的应用版本号
- 对用户理解升级目标版本和版本追踪很重要

#### `author`

- 打包者或商店侧署名

#### `developer`

- 上游项目署名

#### `architectures`

- 支持的 CPU 架构列表
- 构建流程会基于它尽可能生成按架构拆分的 compose 变体

#### `icon`

- 相对于 `--base-url` 的构建资源路径或 URL

#### `thumbnail`

- 相对于 `--base-url` 的缩略图路径或 URL

#### `compose_url`

- 指向构建后单应用 compose 的路径

#### `meta_url`

- 指向构建后单应用元数据文件的路径

#### `content_hash`

- 表示该应用全部相关生成文件状态的哈希
- 客户端会据此判断是否需要增量更新

`index.json` 的生成位置通常是：

- `dist/index.json`
- `dist/index.{locale}.json`，当至少一个应用在列表相关字段中显式定义了该 locale 时生成

## 构建后的 `docker-compose.yml`

构建后的 compose 只保留运行时相关的 `x-casaos` 字段：

- `id`
- `main`
- `index`
- `port_map`
- `scheme`
- `icon`
- `title`

其余元数据都会移出 compose，进入 `meta.json`。

### 构建后 compose 的行为

构建后的 compose 不是简单复制源文件。

构建过程会：

- 去掉非运行时的 `x-casaos` 元数据
- 重写图标 URL
- 将多语言 `title` 解析成当前目标语言的纯字符串

这样做是为了只保留运行时和安装后仪表盘真正需要的信息，而不重复承载更丰富的商店元数据。

## 构建后的 `meta.json`

构建后的 `meta.json` 承载应用展示与升级相关元数据，包括这些字段：

- `version`
- `update_at`
- `release_note`
- `website`
- `repo`
- `support`
- `docs`

实际使用中，不应把 `version` 视为单纯的展示补充字段。它是新版商店中用于表达应用升级的重要字段。

`title` 和 `icon` 不会写入 `meta.json`，因为它们仍然归属于构建后 compose 的运行时 / 展示信息。

### 构建后元数据的分组

实践上可以把 `meta.json` 看成几组内容：

- 描述内容，例如 `tagline`、`description`
- 展示资源，例如 `thumbnail`、`screenshot_link`
- 署名信息，例如 `author`、`developer`
- 兼容信息，例如 `architectures`
- 增强展示字段，例如 `version`、`update_at`、`release_note`

## 路径行为

生成后的应用相关路径通常长这样：

- `apps/com.example.myapp/docker-compose.yml`
- `apps/com.example.myapp/meta.json`
- `apps/com.example.myapp/assets/icon.svg`

这些示例中的 `com.example.myapp` 是源码 `x-casaos.id` 规范化后的值。

这些路径都相对于构建时传入的 `--base-url` 进行解析。

这意味着同一份逻辑构建，只要切换 `--base-url`，就可以发布到不同的公开主机上。

## 更新行为

客户端更新判断依赖 `index.json` 及每个应用项的 `content_hash`。

这意味着：

- 未变化应用会被跳过
- 变化应用只会增量拉取自己的 compose 和 meta
- 商店更新不再需要每次都重新下载完整压缩包

## Content hash

`content_hash` 会根据每个生成后应用目录下的相关文件计算，包括：

- 构建后的 compose
- 按架构拆分的 compose 变体
- meta 多语言变体
- 资源文件

这使客户端可以进行更高效的增量更新。

## 常见错误

- 误以为 `dist/` 文件应该手工维护
- 误以为 `meta.json` 里也会包含 `title`
- 把 `content_hash` 当成手工版本号来维护
- 忘记只有显式定义过的 locale 才会生成对应语言的 index 或 meta 文件
