import { defineConfig } from "vitepress";
import llmstxt from "vitepress-plugin-llms";

const enNav = [
  { text: "Home", link: "/" },
  { text: "Create a Store", link: "/quick-start/overview" },
  { text: "Migrate from v1", link: "/migration/overview" },
  { text: "Protocol Reference", link: "/specs/overview" },
  { text: "CI/CD", link: "/cicd/overview" },
  { text: "Resources", link: "/resources/recommended-third-party-stores" },
  { text: "FAQ", link: "/faq/overview" }
];

const zhNav = [
  { text: "首页", link: "/zh/" },
  { text: "创建应用商店", link: "/zh/quick-start/overview" },
  { text: "从 v1 迁移", link: "/zh/migration/overview" },
  { text: "协议规范", link: "/zh/specs/overview" },
  { text: "CI/CD", link: "/zh/cicd/overview" },
  { text: "生态资源", link: "/zh/resources/recommended-third-party-stores" },
  { text: "FAQ", link: "/zh/faq/overview" }
];

const enSidebar = {
  "/quick-start/": [
    {
      text: "Create a Store",
      items: [
        { text: "Build From Scratch", link: "/quick-start/overview" },
        { text: "Repository Structure", link: "/quick-start/repository-structure" }
      ]
    }
  ],
  "/guides/": [
    {
      text: "Compatibility Pages",
      items: [
        { text: "Third-party Store Guide", link: "/guides/third-party-store-guide" },
        { text: "Official Actions Reuse", link: "/guides/official-actions-and-workflows" }
      ]
    }
  ],
  "/resources/": [
    {
      text: "Resources",
      items: [
        { text: "Awesome Third-party Stores", link: "/resources/recommended-third-party-stores" }
      ]
    }
  ],
  "/specs/": [
    {
      text: "Protocol Reference",
      items: [
        { text: "Overview", link: "/specs/overview" },
        { text: "Store Config", link: "/specs/store-config" },
        { text: "Compose and x-casaos", link: "/specs/compose-and-x-casaos" },
        { text: "Build Output", link: "/specs/build-output" },
        { text: "Assets and Localization", link: "/specs/assets-and-i18n" }
      ]
    }
  ],
  "/migration/": [
    {
      text: "Migrate from v1",
      items: [
        { text: "Migration Strategy", link: "/migration/overview" },
        { text: "Minimum Change Checklist", link: "/migration/v1-to-v2-migration-checklist" }
      ]
    }
  ],
  "/faq/": [
    {
      text: "FAQ",
      items: [{ text: "Overview", link: "/faq/overview" }]
    }
  ],
  "/cicd/": [
    {
      text: "CI/CD",
      items: [
        { text: "Overview", link: "/cicd/overview" },
        { text: "Official Actions Reuse", link: "/cicd/official-actions-and-workflows" },
        { text: "Validator Workflow", link: "/cicd/validator-workflow" },
        { text: "Release Workflow", link: "/cicd/release-workflow" },
        { text: "Release-store Workflow", link: "/cicd/release-store-workflow" }
      ]
    }
  ]
};

const zhSidebar = {
  "/zh/quick-start/": [
    {
      text: "创建应用商店",
      items: [
        { text: "从零搭建", link: "/zh/quick-start/overview" },
        { text: "仓库结构", link: "/zh/quick-start/repository-structure" }
      ]
    }
  ],
  "/zh/guides/": [
    {
      text: "兼容入口",
      items: [
        { text: "第三方商店指南", link: "/zh/guides/third-party-store-guide" },
        { text: "复用官方 Actions", link: "/zh/guides/official-actions-and-workflows" }
      ]
    }
  ],
  "/zh/resources/": [
    {
      text: "生态资源",
      items: [
        { text: "推荐第三方商店源", link: "/zh/resources/recommended-third-party-stores" }
      ]
    }
  ],
  "/zh/specs/": [
    {
      text: "协议规范",
      items: [
        { text: "总览", link: "/zh/specs/overview" },
        { text: "商店配置", link: "/zh/specs/store-config" },
        { text: "Compose 与应用元数据", link: "/zh/specs/compose-and-x-casaos" },
        { text: "构建产物", link: "/zh/specs/build-output" },
        { text: "资源与本地化", link: "/zh/specs/assets-and-i18n" }
      ]
    }
  ],
  "/zh/migration/": [
    {
      text: "从 v1 迁移",
      items: [
        { text: "迁移策略", link: "/zh/migration/overview" },
        { text: "最小改动清单", link: "/zh/migration/v1-to-v2-migration-checklist" }
      ]
    }
  ],
  "/zh/faq/": [
    {
      text: "FAQ",
      items: [{ text: "总览", link: "/zh/faq/overview" }]
    }
  ],
  "/zh/cicd/": [
    {
      text: "CI/CD",
      items: [
        { text: "总览", link: "/zh/cicd/overview" },
        { text: "复用官方 Actions", link: "/zh/cicd/official-actions-and-workflows" },
        { text: "Validator 工作流", link: "/zh/cicd/validator-workflow" },
        { text: "Release 工作流", link: "/zh/cicd/release-workflow" },
        { text: "Release-store 工作流", link: "/zh/cicd/release-store-workflow" }
      ]
    }
  ]
};

export default defineConfig({
  title: "App Store Developer Docs",
  description: "Development documentation for the ZimaOS AppStore repository and third-party stores.",
  cleanUrls: true,
  ignoreDeadLinks: true,
  vite: {
    plugins: [
      llmstxt({
        // Keep generated LLM docs aligned with the public English site content only.
        ignoreFiles: ["README.md", "zh/**"],
        injectLLMHint: false
      })
    ]
  },
  head: [
    ["link", { rel: "icon", href: "/zimaos-logo.svg", type: "image/svg+xml" }]
  ],
  themeConfig: {
    logo: "/zimaos-logo.svg",
    search: {
      provider: "local"
    },
    socialLinks: [
      { icon: "github", link: "https://github.com/IceWhaleTech/CasaOS-AppStore" }
    ]
  },
  locales: {
    root: {
      label: "English",
      lang: "en",
      themeConfig: {
        nav: enNav,
        sidebar: enSidebar
      }
    },
    zh: {
      label: "简体中文",
      lang: "zh-CN",
      link: "/zh/",
      themeConfig: {
        nav: zhNav,
        sidebar: zhSidebar
      }
    }
  }
});
