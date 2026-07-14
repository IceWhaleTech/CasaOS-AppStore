# Release 工作流

这一页说明的是 [`.github/workflows/release.yml`](https://github.com/IceWhaleTech/CasaOS-AppStore/blob/main/.github/workflows/release.yml)，也就是“构建产物”工作流。

## 作用

它负责把仓库中的源码定义转换成可复用的构建产物。

## 触发条件

- `main` 分支 push
- 手动 `workflow_dispatch`

## 主要阶段

1. 拉取仓库源码。
2. 恢复构建缓存。
3. 构建协议 v2 所需的 `dist/`。
4. 构建兼容旧版的 v1 zip 产物。
5. 上传构建报告和交付产物。
6. 保存构建缓存。
7. 写入 job summary。

## 构建产物

当前工作流至少会产出：

- 面向 v2 协议的静态 `dist/`
- 旧版兼容文件 `dist/store/main.zip`
- v1 与 v2 构建结果对应的 JSON 报告

## 为什么重要

这个工作流解释了仓库的构建契约：

- 源文件本身不是最终对外协议
- `dist/` 才是真正的发布产物
- 上传的报告文件属于排障辅助信息，不属于协议规范

## 相关发布工作流

真正的 tag 发布流程现在见 [Release-store 工作流](release-store-workflow.md)。

如果你是在设计第三方商店仓库，建议继续阅读[复用官方 Actions](official-actions-and-workflows.md)。
