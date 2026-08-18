import { defineConfig } from "vitepress";

// https://vitepress.dev/reference/site-config
export default defineConfig({
  lang: "zh-CN",
  title: "掌上农场产品与研发文档",
  description: "掌上农场的 MVP 基线、产品优化与重构记录",
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: "文档首页", link: "/" },
      {
        text: "MVP 规划",
        items: [
          {
            text: "掌上农场 MVP 项目总览",
            link: "/mvp/00-project-overview",
          },
          {
            text: "技术架构与工程规范",
            link: "/mvp/01-technical-architecture",
          },
          { text: "核心领域模型", link: "/mvp/02-domain-model" },
          { text: "核心业务规则", link: "/mvp/03-business-rules" },
          { text: "API 与安全设计", link: "/mvp/04-api-security" },
          { text: "MVP 开发计划", link: "/mvp/05-development-plan" },
          { text: "MVP 开发进度", link: "/mvp/06-development-progress" },
          {
            text: "小程序页面架构与视觉基线",
            link: "/mvp/07-miniapp-information-architecture",
          },
        ],
      },
    ],

    sidebar: [
      {
        text: "MVP 规划",
        items: [
          {
            text: "掌上农场 MVP 项目总览",
            link: "/mvp/00-project-overview",
          },
          {
            text: "技术架构与工程规范",
            link: "/mvp/01-technical-architecture",
          },
          { text: "核心领域模型", link: "/mvp/02-domain-model" },
          { text: "核心业务规则", link: "/mvp/03-business-rules" },
          { text: "API 与安全设计", link: "/mvp/04-api-security" },
          { text: "MVP 开发计划", link: "/mvp/05-development-plan" },
          { text: "MVP 开发进度", link: "/mvp/06-development-progress" },
          {
            text: "小程序页面架构与视觉基线",
            link: "/mvp/07-miniapp-information-architecture",
          },
        ],
      },
    ],

    socialLinks: [{ icon: "github", link: "https://github.com/wungjyan" }],
  },
});
