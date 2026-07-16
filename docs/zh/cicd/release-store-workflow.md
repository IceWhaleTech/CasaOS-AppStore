# Release-store 工作流

这一页说明 [`.github/workflows/release-store.yml`](https://github.com/IceWhaleTech/CasaOS-AppStore/blob/main/.github/workflows/release-store.yml)，也就是用于 tag 发布的正式发布工作流。

## 作用

它负责把可发布的构建产物推送到对外可访问的交付目标。

## 触发条件

- 匹配 `v*` 的 tag push
- 手动 `workflow_dispatch`

## 主要阶段

1. 拉取仓库源码。
2. 恢复构建缓存。
3. 构建协议 v2 所需的 `dist/`。
4. 构建兼容旧版的 v1 zip 产物。
5. 生成 release bundle。
6. 上传 release 产物和报告。
7. 保存构建缓存。
8. 写入 release summary。
9. 将 `dist/` 部署到 `gh-pages`。
10. 刷新 CDN 缓存。
11. 创建带附件的 GitHub Release。

## 发布产物

这个工作流当前会发布或附带：

- 发布到 `gh-pages` 的 v2 协议静态 `dist/`
- 兼容旧版 v1 的 `main.zip`
- 供下载使用的打包 release bundle
- 便于排障的 JSON 构建报告

## 为什么重要

如果你希望第三方商店仓库尽量贴近官方发布路径，这个工作流就是最接近的参考实现。

它清楚展示了官方仓库如何拆分：

- 构建阶段产物
- 发布阶段部署
- 供人工下载的 release 附件

## 相关构建工作流

不负责正式发布的构建工作流见 [Release 工作流](release-workflow.md)。

如果你是在设计外部仓库，建议继续阅读[复用官方 Actions](official-actions-and-workflows.md)。
