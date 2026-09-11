# 复用官方 Actions

这一页说明第三方商店维护者如何复用官方的构建与发布方式。

## 推荐复用方式

对外部仓库来说，推荐按下面三层来用：

1. 直接使用公开构建 action `IceWhaleTech/build-appstore-action`。
2. 由你自己的仓库工作流负责校验、产物上传和发布。
3. 当前仓库 `.github/actions/` 下的辅助 action 更适合作为示例或仓库内部包装层，除非你明确打算把它们 vendoring 到自己的仓库。

## 各个 action 的用途

- `IceWhaleTech/build-appstore-action`：公开的 v2 构建核心。外部仓库生成 `dist/` 时优先使用它。
- `.github/actions/build-store-v2`：对公开构建 action 的仓库内包装。
- `.github/actions/build-store-v1`：打包兼容旧客户端的 `dist/store/main.zip`。
- `.github/actions/validate-compose`：在构建前检查应用 compose 元数据。
- `.github/actions/write-job-summary`：把结构化 JSON 报告写入 GitHub Actions job summary。
- `.github/actions/render-report`：把 JSON 报告渲染成独立 HTML 产物。

## 推荐的工作流拆分

当前官方仓库按下面方式拆分职责：

- `validator.yml`：校验 compose 输入，并确认 v2 构建成功。
- `release.yml`：构建 v2 `dist/`、构建 v1 `main.zip`、上传产物并保存缓存。
- `release-store.yml`：在 tag 发布时部署 `dist/` 到 `gh-pages`，并生成 GitHub Release。

对大多数第三方商店来说，可以沿用这种拆分：

- 一个面向 PR 的校验工作流
- 一个负责产物构建的工作流
- 一个面向 tag 或 release 的发布工作流

## 最小校验工作流

```yaml
name: Validate Store

on:
  pull_request:
  workflow_dispatch:

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build v2 dist
        uses: IceWhaleTech/build-appstore-action@v1
        with:
          source: .
          output: dist
          base-url: https://cdn.jsdelivr.net/gh/${{ github.repository }}@gh-pages
          cache-file: .cache/build_appstore/image-size-cache.json
          digest-cache-file: .cache/build_appstore/image-digest-cache.json
```

## 最小发布工作流

```yaml
name: Release Store

on:
  push:
    tags:
      - "v*"

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build v2 dist
        uses: IceWhaleTech/build-appstore-action@v1
        with:
          source: .
          output: dist
          base-url: https://cdn.jsdelivr.net/gh/${{ github.repository }}@gh-pages
          cache-file: .cache/build_appstore/image-size-cache.json
          digest-cache-file: .cache/build_appstore/image-digest-cache.json

      - name: Deploy dist
        uses: peaceiris/actions-gh-pages@v4
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_branch: gh-pages
          publish_dir: ./dist
```

## 兼容性说明

如果你仍然支持旧版 v1 客户端，需要额外产出 `dist/store/main.zip`。官方仓库是在 v2 构建成功后，通过 `.github/actions/build-store-v1` 完成这一步。

## 本地构建

如果你希望本地开发体验尽量贴近上游构建 action，就使用 `./scripts/build_dist.sh`。真实第三方商店仓库的 CI 则建议直接调用 GitHub Actions。
