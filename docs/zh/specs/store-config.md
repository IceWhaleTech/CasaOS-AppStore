# 商店配置

`store-config.json` 用于在仓库级别定义商店身份。

## 作用

构建脚本会读取 `store-config.json` 并生成：

- `dist/store.json`
- 对应已显式定义 locale 的 `dist/store.{locale}.json`

## 最小示例

```json
{
  "version": 2,
  "store_id": "my-awesome-apps",
  "name": {
    "en_US": "My Awesome Apps",
    "zh_CN": "我的应用商店"
  },
  "description": {
    "en_US": "A collection of apps for home server enthusiasts"
  },
  "maintainer": "your-github-username",
  "url": "https://github.com/username/my-appstore"
}
```

## 字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `version` | `int` | 是 | 必须为 `2` |
| `store_id` | `string` | 是 | 商店唯一标识 |
| `name` | `object` | 是 | 多语言商店名称 |
| `description` | `object` | 否 | 多语言商店描述 |
| `maintainer` | `string` | 是 | 维护者名称 |
| `url` | `string` | 否 | 项目主页 |
| `icon` | `string` | 否 | 商店图标 URL |

## 字段详解

### `version`

- 必填
- 必须是整数 `2`
- 用于标识当前构建流程所面向的协议版本

### `store_id`

- 必填
- 是商店的主身份标识
- 一旦已有用户订阅，建议保持稳定
- 应尽量选成全局可区分的值

### `name`

- 必填
- 必须是 locale 到文本的对象，而不是纯字符串
- 应始终至少包含 `en_US`
- 最终会成为生成后 `store.json` 中的展示名称

### `description`

- 可选
- 也是按 locale 组织的对象
- 适合为客户端中的商店提供简短介绍

### `maintainer`

- 必填
- 用普通字符串表示维护者、组织或拥有者名称

### `url`

- 可选
- 可以是项目主页、仓库地址或其他公开页面

### `icon`

- 可选
- 这是商店级别的直接 URL 字段
- 和应用资源不同，它不是从应用目录资产构建出来的路径

## `store_id` 规则

- 只允许字母、数字、`.`、`_`、`-`
- 允许大写输入，但构建时会规范化为小写
- 必须至少包含一个字母或数字
- 应尽量保证全局可区分
- 不要使用 `zimaos-appstore` 之类的保留值

## 校验预期

可以把下面这些当作输入契约：

- 文件本身必须是合法 JSON
- `version` 必须匹配当前协议版本
- `name` 应该是对象而不是纯字符串
- locale 键应使用 `ll_CC` 格式
- URL 类型字段应当已经是公开可访问地址

## 本地化行为

商店级本地化文本来自：

- `name`
- `description`

只有这些字段里显式声明过的 locale 才会生成对应的 `store.{locale}.json`。

## 输入到输出的映射

| 源字段 | 生成位置 | 说明 |
|---|---|---|
| `version` | `store.json.version` | 作为协议元数据保留 |
| `store_id` | `store.json.store_id` | 构建时按规则规范化 |
| `name.<locale>` | `store.{locale}.name` | 按生成语言解析 |
| `description.<locale>` | `store.{locale}.description` | 仅对显式定义的 locale 生成 |
| `maintainer` | `store.json.maintainer` | 作为纯字符串复制 |
| `url` | `store.json.url` | 作为纯字符串复制 |
| `icon` | `store.json.icon` | 作为纯字符串 URL 复制 |

## 输出行为

构建脚本总会生成默认语言文件：

- `dist/store.json`

只有当某个 locale 在商店本地化文本中被显式定义时，才会额外生成：

- `dist/store.zh_CN.json`
- `dist/store.de_DE.json`

这样既支持多语言展示，也避免无意义地膨胀输出。

## 实践建议

- 至少提供 `name.en_US`
- 如果希望客户端里能看到商店简介，就补上 `description`
- 一旦有用户开始订阅，尽量不要再修改 `store_id`

## 常见错误

- 把 `name` 写成单个字符串，而不是多语言对象
- 在已有用户使用后修改 `store_id`
- 使用 `en_us` 而不是 `en_US`
- 误以为 `supported-languages.json` 中列出的每个语言都会自动生成 `store.{locale}.json`
