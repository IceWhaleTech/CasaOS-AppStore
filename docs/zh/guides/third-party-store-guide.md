# 第三方商店指南

这一页保留为旧链接的精简兼容入口。当前文档已经改成五个更清晰的分区。

## 选择你的路径

- 新建商店：[创建应用商店](../quick-start/overview.md)
- 已有 v1 商店：[从 v1 迁移](../migration/overview.md)
- 文件与字段参考：[协议规范](../specs/overview.md)
- 构建与发布自动化：[CI/CD 总览](../cicd/overview.md)
- 短答案：[FAQ](../faq/overview.md)

## v2 核心流程

1. 编写 `store-config.json`、`supported-languages.json` 和 `Apps/*/docker-compose.yml` 等源码文件。
2. 运行公开构建 action 或 `./scripts/build_dist.sh`。
3. 发布生成后的 `dist/` 目录。
4. 由客户端消费 `store.json`、`index.json`、构建后的 compose、元数据文件和资源文件。

## 最小源码结构

```text
my-appstore/
├── Apps/
│   └── MyApp/
│       ├── docker-compose.yml
│       └── icon.svg
├── store-config.json
└── supported-languages.json
```

如果需要本地构建，可以额外添加 `scripts/build_dist.sh`。

## 关键参考

- [仓库结构](../quick-start/repository-structure.md)
- [商店配置](../specs/store-config.md)
- [Compose 与应用元数据](../specs/compose-and-x-casaos.md)
- [构建产物](../specs/build-output.md)
- [资源与本地化](../specs/assets-and-i18n.md)
- [复用官方 Actions](../cicd/official-actions-and-workflows.md)
