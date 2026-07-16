# Compose 与应用元数据

每个应用都位于 `Apps/<目录>/docker-compose.yml` 中。

## 本页范围

这一页重点说明顶层 `x-casaos` 块，因为它是当前商店构建流程所使用的“商店侧元数据契约”。

对于 `x-casaos` 之外的 Compose 内容：

- 以 Docker Compose 官方文件参考为准：https://docs.docker.com/reference/compose-file/
- 服务定义以官方 `services` 参考为准：https://docs.docker.com/reference/compose-file/services/
- 顶层 `name` 以官方说明为准：https://docs.docker.com/reference/compose-file/version-and-name/

也就是说：

- 标准容器运行配置属于 Docker Compose 官方规范
- 面向商店展示和安装入口的元数据属于 `x-casaos`

## 源码模型

你为每个应用维护一个 compose 文件。它同时包含：

- 标准 Docker Compose 内容
- 一个顶层 `x-casaos` 块

`Apps/` 下的目录名本身并不是协议层的应用身份。构建过程真正读取的是 compose 内容，尤其是顶层 `name` 和 `x-casaos.id`。

## 最小示例

```yaml
name: my-app
services:
  my-app:
    image: myrepo/my-app:1.0.0
    ports:
      - target: 8080
        published: "8080"
        protocol: tcp
    restart: unless-stopped
x-casaos:
  id: com.example.myapp
  main: my-app
  index: /
  port_map: "8080"
  scheme: http
  icon: https://cdn.example.com/my-app/icon.svg
  title:
    en_US: My App
  tagline:
    en_US: Does amazing things
  description:
    en_US: A great app that does amazing things.
  author: Your Name
  developer: Original Developer
  category: Productivity
  architectures:
    - amd64
  version: "1.0.0"
  update_at: "2026-03-01"
  release_notes:
    en_US: First release
```

## `x-casaos` 之外的 Compose 规则

对于所有非 `x-casaos` 内容，这个仓库不重新定义 Docker Compose 语义，直接以官方文档为准：

- Compose file reference: https://docs.docker.com/reference/compose-file/
- Services reference: https://docs.docker.com/reference/compose-file/services/
- Project `name` reference: https://docs.docker.com/reference/compose-file/version-and-name/
- Project naming behavior: https://docs.docker.com/compose/how-tos/project-name/

仓库自身额外关心的只有：

- compose 必须是合法 YAML
- compose 必须能通过 `docker compose config -q`
- 顶层 `name` 必须满足仓库校验规则
- `services.<name>.x-casaos` 属于旧式写法，v2 构建时会被清理

## x-casaos 总览

顶层 `x-casaos` 中的字段可以分成两类：

- 构建后仍保留在 `docker-compose.yml` 中的运行时 / 入口字段
- 构建后提取到 `meta.json` 中的元数据字段

## 字段矩阵

| 字段 | 类型 | 必填 | 源码是否本地化 | 构建输出位置 |
|---|---|---:|---:|---|
| `id` | `string` | 是 | 否 | 构建后 compose + `meta.json` / index 派生输出 |
| `main` | `string` | 是 | 否 | 构建后 compose |
| `index` | `string` | 实际上建议视为必填 | 否 | 构建后 compose |
| `port_map` | `string` | 是 | 否 | 构建后 compose |
| `scheme` | `string` | 否 | 否 | 构建后 compose |
| `icon` | `string` | 是 | 否 | 构建后 compose，构建时会重写 |
| `title` | `object` | 是 | 是 | 构建后 compose，按 locale 解析 |
| `tagline` | `object` | 建议提供 | 是 | `meta.json`，也可能进入 index 列表 |
| `description` | `object` | 建议提供 | 是 | `meta.json` |
| `thumbnail` | `string` | 否 | 否 | `meta.json` 中的构建后资源路径 |
| `screenshot_link` | `string[]` | 否 | 否 | `meta.json` 中的构建后资源路径列表 |
| `tips` | `object` | 否 | 是 | `meta.json` |
| `author` | `string` | 建议提供 | 否 | `meta.json`，也常进入 index 列表 |
| `developer` | `string` | 建议提供 | 否 | `meta.json`，也常进入 index 列表 |
| `category` | `string` | 是 | 否 | `meta.json`，也常进入 index 列表 |
| `architectures` | `string[]` | 建议提供 | 否 | `meta.json`，也常进入 index 列表 |
| `version` | `string` | 是 | 否 | `meta.json`，也可能进入 index 列表 |
| `update_at` | `string` | 否 | 否 | `meta.json` |
| `release_notes` | `object` | 否 | 是 | `meta.json.release_note` |
| `website` | `string` | 否 | 否 | `meta.json` |
| `repo` | `string` | 否 | 否 | `meta.json` |
| `support` | `string` | 否 | 否 | `meta.json` |
| `docs` | `string` | 否 | 否 | `meta.json` |

## 运行时字段

### `id`

作用：
稳定的应用协议身份标识。

规则：

- 每个源 compose 都必须声明
- 必须使用类似 `com.example.myapp` 的域名倒置格式
- 仅允许字母、数字、`.`、`_`、`-`
- 构建时会规范化为小写
- 至少包含两个非空的点分段

构建行为：

- 保留在构建后 compose 中
- 同时传播到构建后的元数据和列表数据中

常见错误：

- 把应用目录名当作应用身份
- 使用过短、非域名风格的字符串

### `main`

作用：
指定提供主要浏览器界面的服务名。

规则：

- 必填
- 必须匹配 `services` 里的某个服务名
- 应指向真正面向用户的 Web 服务，而不是辅助容器

构建行为：

- 保留在构建后 compose 中

常见错误：

- 把 `main` 指向数据库容器

### `index`

作用：
定义客户端打开应用时附加的入口路径。

规则：

- 通常写成 `/`
- 应与应用真实 Web 入口一致

构建行为：

- 保留在构建后 compose 中

### `port_map`

作用：
定义用户实际访问的 Web UI 对外端口。

规则：

- 必填
- 必须写成 YAML 字符串，例如 `"8080"`
- 应对应浏览器实际打开的发布端口

构建行为：

- 保留在构建后 compose 中

常见错误：

- 写成 `port_map: 8080` 而不是带引号的字符串

### `scheme`

作用：
指定客户端应以 `http` 还是 `https` 打开应用。

规则：

- 可选
- 应与实际对外暴露的访问协议一致

构建行为：

- 保留在构建后 compose 中

### `icon`

作用：
提供安装后仪表盘展示用的图标 URL。

规则：

- 必填
- 源 compose 中可以先写任意可访问 URL
- 构建输出会把它重写为 `--base-url` 下的构建图标地址

构建行为：

- 保留在构建后 compose 中
- 最终会重写为 `apps/{app-id}/assets/icon.*`

常见错误：

- 误以为源 compose 里的这个值会原样保留到构建产物中

### `title`

作用：
提供应用显示名称。

规则：

- 必填
- 源码中必须是多语言对象
- 应至少包含 `en_US`

构建行为：

- 保留在构建后 compose 中
- 在每个生成语言版本中解析成纯字符串

常见错误：

- 把它写成纯字符串而不是 locale-keyed 对象

## 元数据字段

### `tagline`

作用：
提供一句话短摘要，用于列表和详情等展示场景。

规则：

- 建议提供
- 源码中是多语言对象

构建行为：

- 提取到构建后的 `meta.json`
- 也可能进入 `index.json` 等列表数据

### `description`

作用：
提供应用长描述。

规则：

- 建议提供
- 源码中是多语言对象
- 可包含 markdown 文本，具体渲染效果取决于客户端

构建行为：

- 提取到构建后的 `meta.json`
- 在每个生成语言版本中解析成纯字符串

### `thumbnail`

作用：
提供更适合详情页或商店展示的大图。

规则：

- 可选
- 源值通常是应用目录中的某个文件名

构建行为：

- 在 `meta.json` 中表现为构建后的资源路径
- 源文件会被处理后输出到 `apps/{app-id}/assets/`

### `screenshot_link`

作用：
提供一个或多个应用截图，用于详情页展示。

规则：

- 可选
- 源码中是截图文件名数组

构建行为：

- 在 `meta.json` 中表现为构建后的资源路径列表

### `tips`

作用：
承载安装前或安装过程中的用户提示。

规则：

- 可选
- 是一个对象，其值通常是多语言文本

示例：

```yaml
tips:
  before_install:
    en_US: This app requires at least 4GB RAM.
    zh_CN: This app requires at least 4GB RAM.
```

构建行为：

- 提取到构建后的 `meta.json`
- 各 locale 值会按生成语言解析

### `author`

作用：
标识打包者或商店侧维护者。

规则：

- 建议提供
- 纯字符串

构建行为：

- 写入 `meta.json`
- 也常被包含进应用列表数据

### `developer`

作用：
标识上游项目或原始开发者。

规则：

- 建议提供
- 纯字符串

构建行为：

- 写入 `meta.json`
- 也常被包含进应用列表数据

### `category`

作用：
把应用归类到标准化的 ZimaOS 商店分类中。

规则：

- 实际上应视为必填
- 必须是以下之一：
  - `Media`
  - `Productivity`
  - `Home`
  - `Networking`
  - `AI`
  - `Finance`
  - `Social`
  - `Developer`
  - `Others`

构建行为：

- 写入 `meta.json`
- 也常被包含进应用列表数据

常见错误：

- 使用自由发挥的分类名称

### `architectures`

作用：
声明应用包支持的 CPU 架构。

规则：

- 建议提供
- 是字符串数组
- 常见值包括 `amd64` 和 `arm64`

构建行为：

- 写入 `meta.json`
- 也常被包含进应用列表数据

### `version`

作用：
用于商店展示和升级理解的应用版本号。

规则：

- 对发布到新版商店的应用，必填
- 纯字符串
- 当发布的应用更新发生了用户应感知的变化时，应同步变更
- 建议尽量使用 semver 风格值，例如 `1.2.3`

构建行为：

- 写入 `meta.json`
- 也可能进入列表数据

为什么重要：

- 未来应用升级判断会依赖这个字段来判断用户将升级到哪个版本
- 如果没有这个字段，用户和客户端只能退回到 `content_hash` 这类底层变化信号
- 缺失或非 semver 的版本号会削弱更新透明度，并可能不进入部分面向列表的输出

常见错误：

- 把 `version` 仅当作展示文案
- 有实际更新却不修改版本号
- 使用难以作为正常发布版本解释的随意字符串

### `update_at`

作用：
可选的更新时间字段，用于增强商店展示。

规则：

- 可选
- 推荐格式为 `YYYY-MM-DD`

构建行为：

- 写入 `meta.json`

### `release_notes`

作用：
提供版本说明或更新摘要。

规则：

- 可选
- 源码中是多语言对象
- 源字段名必须保持为 `release_notes`

构建行为：

- 提取到构建后的 `meta.json`
- 字段名会改写为 `release_note`

常见错误：

- 在源码里写成 `release_note` 而不是 `release_notes`

### `website`

作用：
链接到产品官网或主页。

规则：

- 可选
- 纯字符串 URL

构建行为：

- 写入 `meta.json`

### `repo`

作用：
链接到源码仓库或项目仓库。

规则：

- 可选
- 纯字符串 URL

构建行为：

- 写入 `meta.json`

### `support`

作用：
链接到支持页面、issue tracker、论坛或帮助中心。

规则：

- 可选
- 纯字符串 URL

构建行为：

- 写入 `meta.json`

### `docs`

作用：
链接到被打包应用自身的文档页面。

规则：

- 可选
- 纯字符串 URL

构建行为：

- 写入 `meta.json`

## 哪些字段留在构建后 compose，哪些进入 `meta.json`

保留在构建后 compose 中的字段：

- `id`
- `main`
- `index`
- `port_map`
- `scheme`
- `icon`
- `title`

移动到构建后 `meta.json` 的字段：

- `tagline`
- `description`
- `thumbnail`
- `screenshot_link`
- `tips`
- `author`
- `developer`
- `category`
- `architectures`
- `version`
- `update_at`
- `release_note`
- `website`
- `repo`
- `support`
- `docs`

## 字段放置规则

编写源 compose 时建议按下面的分工放置内容：

- 运行入口和访问相关信息放在 `x-casaos` 的运行时字段中
- 商店展示和元数据放在 `x-casaos` 的元数据字段中
- 容器运行细节继续放在标准 Docker Compose 的 `services`、`volumes`、`networks`、`environment` 等块中

## 常见错误汇总

- 在期望 locale-keyed 对象的地方写成纯字符串
- 把 `main` 指向非 UI 服务
- 把 `port_map` 写成整数而不是带引号的字符串
- 使用非官方分类值
- 忘记 `title` 会留在构建后 compose，而 `tagline` 会进入 `meta.json`
