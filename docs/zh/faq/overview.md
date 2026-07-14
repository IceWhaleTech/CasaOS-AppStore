# FAQ

这一页收集使用 v2 协议的商店、迁移、托管和兼容性的常见短答案。

## 第三方商店的应用 ID 可以和官方商店重复吗？

可以。官方商店应用和第三方商店应用在 ZimaOS 中按商店上下文隔离，即使源码里的 `id` 一样也可以共存。

但第三方商店仍然应该选择稳定的反向域名风格 ID，这样自己的用户才能获得可预测的更新行为。

## 如果其他第三方商店和我用了同一个应用 ID 会怎样？

ZimaOS 会按商店上下文隔离安装，因此不同商店之间相同的源码应用 ID 不会在 Docker project 层面冲突。

## 需要 `supported-languages.json` 吗？

需要。对本仓库的 v2 源码结构来说，它用于声明构建时考虑的候选语言。

但它不会单独自动生成本地化产物。只有源码中存在对应语言字段时，才会生成 locale 专用文件。

## 一定要跑构建脚本吗？

是的。构建会把源码文件转换成客户端消费的协议产物：

- `store-config.json` 转为 `store.json`
- 源码 compose 转为构建后的 compose 和 `meta.json`
- 带 `content_hash` 的商店应用列表
- 优化后的资源和语言专用输出

## 哪些构建问题只是警告，哪些会让 workflow 失败？

构建 action 会尽量继续处理相互独立的应用，这样一次 summary 里可以看到更多问题。

不会导致 v2 构建失败的警告：

- 缺少 `supported-languages.json`：构建会回退到 `en_US`
- 缺少 `store-config.json`：仍可构建应用输出，但会跳过 `store.json`
- 应用目录没有顶层 `x-casaos`：该应用会被跳过
- registry 限流、digest pinning 失败、镜像大小估算失败：能继续时会继续构建，并在报告里记录 warning
- 图片优化或 SVG 转 PNG 回退失败：能继续时会保留原资源，warning 会出现在日志中
- `x-casaos.version` 不是 semver：该版本号不会写入 `index.json`

会按应用收集错误、继续处理其他应用，并最终让 v2 构建失败的问题：

- 应用元数据无效，包括缺少或无效的 `x-casaos.id`
- 应用 YAML 无效
- 引用的 icon、thumbnail 或 screenshot 不存在
- `x-casaos.architectures` 声明了镜像不支持的架构
- 其他应用级 compose、元数据、资源或 registry 处理失败

会在全局层面终止构建的问题：

- `base-url` 无效
- 缺少 `Apps/` 目录
- `store-config.json` 无效或 `store_id` 无效
- `supported-languages.json` 不是合法 JSON
- 构建脚本启动前的依赖安装失败

## 在哪里查看构建 summary？

打开对应的 GitHub Actions run，进入 build 或 validation job，在 job 页面顶部查看 summary。本仓库会根据结构化 report JSON 写入这份 summary。

原始报告也会作为 workflow artifact 上传，例如 `build-v2-report`、`build-v2-validation-report` 或 `validation-report`。

## 可以将商店托管在 GitHub Pages 以外的地方吗？

可以。只要生成的文件可访问，任何 HTTPS 静态托管都可以。

## 必须用 jsDelivr 吗？

不必须。`jsDelivr` 只是一个可选 CDN 路径。任何正确的 `base-url` 都可以。

## 为什么 `base-url` 很重要？

因为生成的应用列表数据里包含资源和应用文件路径，它们需要一个可解析的公开 host 前缀。

它应该设置为 `dist/` 最终被服务的公开 URL。

## 可以保留 v1 兼容吗？

可以。继续产出旧版产物：

```text
dist/store/main.zip
```

官方仓库就是从同一个源码树先构建 v2 静态文件，再构建这个 v1 zip。

## 最小可用商店结构是什么？

```text
my-appstore/
├── Apps/
│   └── MyApp/
│       ├── docker-compose.yml
│       └── icon.svg
├── store-config.json
└── supported-languages.json
```

如果需要本地辅助脚本，可以添加 `scripts/build_dist.sh`。CI 可以直接调用 `IceWhaleTech/build-appstore-action`。
