# 资源与本地化

这一页把两个强相关的协议行为放在一起说明：资源处理和多语言文本展开。

## 资源文件

所有构建后的资源都会写入 `apps/{app-id}/assets/`。

`{app-id}` 是源码顶层 `x-casaos.id` 规范化后的值。

### 支持的源格式

| 资源 | 输入格式 | 输出行为 |
|------|----------|----------|
| `icon` | `.svg`、`.png`、`.jpg`、`.webp` | SVG 保留，并可能生成 PNG 回退；位图图标按规则复制 |
| `thumbnail` | `.png`、`.jpg`、`.jpeg`、`.webp` | 在工具可用时优化；最终扩展名以生成产物为准 |
| `screenshot-{n}` | `.png`、`.jpg`、`.jpeg`、`.webp` | 在工具可用时优化；最终扩展名以生成产物为准 |

### 资源行为细节

#### `icon`

- 每个应用都应提供
- 最好优先使用 `icon.svg`
- 如果构建环境支持，也可能生成 PNG 回退图标

#### `thumbnail`

- 可选
- 主要用于更丰富的商店展示
- 构建后会规范化成应用资产路径

#### `screenshot-{n}`

- 可选
- 支持多个按编号命名的截图
- 构建后会规范化成资产路径列表

## 资源建议

- 优先使用 `icon.svg`
- 单独准备一张适合商店展示的 `thumbnail`
- 截图尽量反映真实 UI

非图标类位图资源在构建过程中通常会被优化，过宽时也可能被缩放。
根据构建 action 版本和图像工具可用情况，生成后的缩略图和截图可能保留源扩展名，也可能输出为优化后的 WebP。最终应以 `index.json` 和 `meta.json` 中写入的路径为准。

## 图标行为

图标会出现在两个位置：

- 商店列表，使用 `index.json` 中的图标路径
- 安装后的仪表盘入口，使用构建后 compose 中的 `x-casaos.icon`

构建时，compose 里的图标 URL 会按照 `--base-url` 被重写为构建产物 URL。

## locale 键格式

locale 键建议使用 `ll_CC` 格式：

- `en_US`
- `zh_CN`
- `de_DE`

虽然构建脚本会做规范化处理，但源码里仍建议直接遵循标准格式。

## 本地化源字段

商店级本地化文本：

- `store-config.json.name`
- `store-config.json.description`

应用级本地化文本：

- `x-casaos.title`
- `x-casaos.tagline`
- `x-casaos.description`
- `x-casaos.release_notes`
- `x-casaos.tips` 下各 locale 值

## 多语言输出

候选语言列表来自 `supported-languages.json`。

关键行为：

- 默认输出始终会生成
- 只有显式声明过的 locale 才会生成对应语言文件
- 如果缺少 `supported-languages.json`，则只生成 `en_US` 输出

## 语言文件生成规则

可以把多语言输出理解成两个阶段：

1. `supported-languages.json` 先声明哪些 locale 有资格参与生成。
2. 源码中的本地化字段再决定这些 locale 是否真的会生成文件。

所以某个 locale 即使出现在候选列表里，只要没有对应的商店字段或应用字段显式定义，也可能不会产出任何语言文件。

## 示例

源码：

```yaml
title:
  en_US: My App
  zh_CN: 我的应用
```

可能输出：

- `dist/index.json`
- `dist/index.zh_CN.json`
- `dist/apps/com.example.myapp/meta.json`
- `dist/apps/com.example.myapp/meta.zh_CN.json`

这里的 `com.example.myapp` 表示源码 `x-casaos.id` 规范化后的值。

## 常见错误

- 误以为只要写了 `supported-languages.json` 就一定会生成所有语言文件
- 误以为资源文件会按语言各复制一份
- 忘记图标同时影响商店列表展示和安装后仪表盘展示
