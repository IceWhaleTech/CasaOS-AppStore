# v1 到 v2 最小改动清单

当你已经有 v1 商店，并希望用最小实际改动支持 v2 时，按这份清单处理。

目标：一个源码仓库，产出 v2 静态文件，并按需保留 v1 zip 兼容。

## 1. 保留现有应用目录

保留现有布局：

```text
Apps/
└── MyApp/
    ├── docker-compose.yml
    ├── icon.png
    ├── thumbnail.png
    └── screenshot-1.png
```

你可以之后再替换 SVG 图标或优化资源。资源替换不是迁移的第一阻塞点。

## 2. 添加 `store-config.json`

在仓库根目录创建：

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

检查项：

- `version` 为 `2`
- `store_id` 全局可区分且稳定
- `store_id` 只使用字母、数字、点号（`.`）、下划线（`_`）和连字符（`-`）
- 存在 `name.en_US`

## 3. 添加 `supported-languages.json`

在仓库根目录创建：

```json
[
  "en_US"
]
```

将源码元数据中可能出现的语言都加入列表，例如 `zh_CN` 或 `de_DE`。

## 4. 给每个应用添加 `x-casaos.id`

每个应用都需要稳定的顶层应用 ID：

```yaml
x-casaos:
  id: com.example.myapp
```

检查项：

- 每个源码 `docker-compose.yml` 都包含顶层 `x-casaos.id`
- 使用类似 `com.example.myapp` 的反向域名风格
- ID 至少有两个非空的点分段
- 只使用字母、数字、点号（`.`）、下划线（`_`）和连字符（`-`）

## 5. 规范旧元数据布局

常见 v1 到 v2 清理项：

| 旧版源码 | v2 源码 |
|---|---|
| `en_us` | `en_US` |
| `zh_cn` | `zh_CN` |
| `appfile.json` 中的展示元数据 | 顶层 `x-casaos` 字段 |

v2 不需要保留 `appfile.json`。如果你的 v1 打包仍然使用它，只把它留给旧版流水线即可。

## 6. 规范分类

每个应用的 `x-casaos.category` 必须是以下之一：

`Media`, `Productivity`, `Home`, `Networking`, `AI`, `Finance`, `Social`, `Developer`, `Others`

例如旧的 `Utilities` 通常需要改成最接近的 v2 分类，常见是 `Productivity` 或 `Others`。

## 7. 构建 v2 输出

```bash
BASE_URL="https://your-store-domain" \
./scripts/build_dist.sh
```

检查项：

- `dist/store.json` 存在
- `dist/index.json` 存在
- `dist/apps/<app-id>/docker-compose.yml` 存在，其中 `<app-id>` 是规范化后的 `x-casaos.id`
- `dist/apps/<app-id>/meta.json` 存在
- 生成的应用列表包含 `id`、`compose_url`、`meta_url` 和 `content_hash`

## 8. 补充版本号和其他展示字段

其中 `version` 在新版商店里是必填字段。即使旧仓库里没有等价字段，也建议在迁移时补齐。

其余字段不是兼容性的必需项，但可以提升商店展示效果：

| 字段 | 类型 | 说明 |
|---|---|---|
| `version` | `string` | **新增，且必填。** 未来应用升级判断会依赖这个字段。建议尽量使用 semver 风格值。 |
| `update_at` | `string` | **新增，可选。** 应用更新日期，建议使用 `YYYY-MM-DD`。 |
| `release_notes` | `object` | **新增，可选。** locale-keyed 更新日志，每个 locale 的值是纯字符串。 |
| `website` | `string` | **新增，可选。** 官方网站地址。 |
| `repo` | `string` | **新增，可选。** 源码仓库地址。 |
| `support` | `string` | **新增，可选。** 支持地址。 |
| `docs` | `string` | **新增，可选。** 文档地址。 |

## 9. 按需保留 v1 兼容

如果旧客户端仍然依赖 v1 商店，保留一个 workflow 步骤生成：

```text
dist/store/main.zip
```

官方仓库是在 v2 构建成功后继续运行 v1 构建。这样一个源码树可以同时服务：

- v2 静态商店消费者
- 旧版 v1 zip 消费者

## 10. 部署生成文件

将 `dist/` 发布到静态托管。用户添加的商店 URL 应该和构建时的 `base-url` 一致。

## 发布前最终检查

- [ ] `store-config.json` 存在且有效
- [ ] `supported-languages.json` 存在且有效
- [ ] 每个应用都有有效的 `x-casaos.id`
- [ ] 旧 locale key 已规范
- [ ] `x-casaos.version` 已填写，并与本次发布对应
- [ ] 已按需补充其他展示字段
- [ ] 所有应用分类都使用 v2 值
- [ ] `dist/store.json` 和 `dist/index.json` 可访问
- [ ] 如果仍需 v1 兼容，已构建 `dist/store/main.zip`
