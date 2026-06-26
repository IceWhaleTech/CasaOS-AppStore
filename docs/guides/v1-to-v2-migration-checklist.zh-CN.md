# v1 -> v2 迁移清单（最小改动版）

这是一页版清单，面向已经发布过 v1（zip 分发）商店的第三方开发者。  
目标是用最小改动完成可用迁移，并保留旧用户的一键恢复提示能力。

> 完整背景与协议细节请参考：
> - [第三方商店指南（中文）](./third-party-store-guide.zh-CN.md)

## 5 分钟迁移路径

```text
v1 仓库
  │
  ├─ 1) 添加 store-config.json
  │
  ├─ 2) 给每个应用补齐必填的 x-casaos.app_id
  │
  ├─ 3) 统一 category 到 9 个官方分类
  │
  ├─ 4) 运行 build_appstore.py 生成 dist/
  │
  ├─ 5) 部署 dist/ 到静态托管（URL = --base-url）
  │
  └─ 6)（推荐）在 v1 zip 中包含同一个 store-config.json
         → 让老用户在 v2 中看到“一键恢复旧商店”
```

## 你只需要按顺序做这 6 件事

## 1. 添加 `store-config.json`（必做）

在仓库根目录新增：

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

检查点：
- `store_id` 全局唯一，格式 `[a-z0-9-]`
- 至少有 `name.en_US`

## 2. 给每个应用添加 `x-casaos.app_id`（必做）

在每个应用顶层 `x-casaos` 块中添加一个域名倒置格式的应用标识：

```yaml
x-casaos:
  app_id: com.example.myapp
```

检查点：
- 每个源 `docker-compose.yml` 都声明了 `x-casaos.app_id`
- 使用域名倒置格式
- 仅允许小写字母、数字和点号

## 3. 统一应用分类（必做）

把每个 app 的 `x-casaos.category` 改为官方 9 类之一：

`Media`、`Productivity`、`Home`、`Networking`、`AI`、`Finance`、`Social`、`Developer`、`Others`

## 4. 使用构建脚本生成 v2 输出（必做）

```bash
python3 scripts/build_appstore.py \
  --source . \
  --output dist \
  --base-url "https://your-store-domain"
```

检查点：
- 生成 `dist/{locale}/store.json`
- 生成 `dist/{locale}/index.json`
- 生成 `dist/{locale}/apps/<app-id>/docker-compose.yml` 与 `meta.json`
- 生成后的 `index.json`、`meta.json`、`docker-compose.yml` 都包含 `app_id`

## 5. 部署 `dist/` 到静态托管（必做）

可选平台：GitHub Pages / Netlify / Cloudflare Pages / 自建 Nginx。  
最终用户添加的商店 URL 应与 `--base-url` 对应。

## 6. 保留 v1 -> v2 迁移提示能力（强烈建议）

在 v1/v2 并存阶段，`store-config.json` 本身已经是 v2 商店必备文件。

对于迁移提醒，额外要求只有一条：

- 在 v1 zip 包中包含同一个 `store-config.json` 文件

客户端行为：

- 若 v1 zip 包含 `store-config.json`，用户升级到 v2 后可看到“一键恢复旧商店”提示
- 若 v1 zip 不包含 `store-config.json`，用户仍可手动重加，但不会出现自动迁移提示。

## 最终自检（发布前 30 秒）

- [ ] `store-config.json` 已添加且字段有效
- [ ] 每个 app 都有合法的 `x-casaos.app_id`
- [ ] 所有 app 的 `category` 已标准化
- [ ] `dist/{locale}/store.json` 可访问
- [ ] `dist/{locale}/index.json` 可访问
- [ ] v1 zip 包包含同一个 `store-config.json`（如你有 v1 历史用户）
