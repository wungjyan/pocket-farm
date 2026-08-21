---
kind: frontend_style
name: 掌上农场小程序 SCSS 设计令牌与 uv-ui 主题定制
category: frontend_style
scope:
    - '**'
source_files:
    - apps/miniapp/src/styles/design-tokens.scss
    - apps/miniapp/src/styles/pocket-farm.scss
    - apps/miniapp/src/uni.scss
    - apps/miniapp/src/components/PfPageHeader.vue
    - apps/miniapp/package.json
---

## 1. 使用的系统与工具

- **框架**：uni-app（Vue 3）+ Vite 构建，通过 `@dcloudio/vite-plugin-uni` 编译。
- **样式语言**：SCSS（依赖 `sass ^1.102.0`），所有页面/组件 `<style lang="scss">` 均可直接使用 `$pf-*` 变量。
- **UI 组件库**：`uv-ui`（以 uni_modules 形式内联引入，位于 `src/uni_modules/uv-*`），提供按钮、表单、弹窗、导航等基础组件。
- **设计系统**：自研 SCSS 设计令牌（Design Tokens），集中定义在 `src/styles/design-tokens.scss`，并通过 `src/uni.scss` 注入到 uni-app 全局作用域。

## 2. 关键文件

- `apps/miniapp/src/styles/design-tokens.scss`：原始色阶（Primitive）、语义色（Semantic）、间距（Spacing）、圆角与阴影（Shape & Motion）的单一来源。
- `apps/miniapp/src/styles/pocket-farm.scss`：基于 token 的全局原子类（`.pf-page`、`.pf-card`、`.pf-list-card`、`.pf-section-heading`、`.pf-tappable` 等）。
- `apps/miniapp/src/uni.scss`：项目入口样式，import uv-ui 默认主题后覆盖其 `$uv-*` 变量，并映射 uni-app 内置 `$uni-*` 变量到本项目的 `$pf-*` token。
- `apps/miniapp/src/components/PfPageHeader.vue`：业务级组件示例，使用 BEM 风格 class（`pf-page-header__*`、`pf-page-header--*`）并直接 import `design-tokens.scss`。
- `apps/miniapp/package.json`：声明 `sass`、`vite`、`vue` 等前端依赖；无 Tailwind、CSS-in-JS 或 CSS Modules 相关配置。

## 3. 架构与约定

### 3.1 三层 Token 体系
`design-tokens.scss` 明确分层：
- **Primitive（原始值）**：如 `$pf-green-800`、`$pf-neutral-50`、`$pf-white` 等十六进制色值，以及 `8rpx` 步进的间距 `$pf-space-1..8`。
- **Semantic（语义层）**：将原始值映射为用途明确的变量，如 `$pf-color-primary`、`$pf-color-text`、`$pf-color-danger`、`$pf-color-surface` 等，并保留历史兼容别名 `$pf-color-harvest` / `$pf-color-water`。
- **Layout/Motion**：圆角 `$pf-radius-control/list/card/card-lg`、阴影 `$pf-shadow-card/raised`、动画时长 `$pf-duration-fast: 160ms`。

### 3.2 全局样式注入路径
`uni.scss` 是 uni-app 自动加载的全局样式入口。它按顺序：
1. `@import '@/uni_modules/uv-ui-tools/theme.scss'` 加载 uv-ui 默认主题。
2. `@import '@/styles/design-tokens.scss'` 暴露 `$pf-*` 变量。
3. 覆盖 uv-ui 的主题变量（`$uv-main-color`、`$uv-primary`、`$uv-success`、`$uv-warning`、`$uv-error`、`$uv-info` 等均指向对应 `$pf-color-*`）。
4. 覆盖 uni-app 内置变量（`$uni-color-*`、`$uni-text-color`、`$uni-bg-color`、`$uni-border-color`、字号/间距/圆角等）。

这使得第三方 uv-ui 组件和 uni 原生组件在视觉上统一为“掌上农场”品牌绿主色调。

### 3.3 原子类与业务组件
`pocket-farm.scss` 提供跨页面复用的原子类：页面容器 `.pf-page`、内容区 `.pf-page-content`、区块标题 `.pf-section-heading`、卡片 `.pf-card` / `.pf-card--emphasis`、列表卡片 `.pf-list-card`、分割线 `.pf-list-divider`、可点击态 `.pf-tappable`。
业务组件（如 `PfPageHeader`）采用 BEM 命名（block__element--modifier），并在 scoped style 中直接 `@import "../styles/design-tokens.scss"` 使用 token，避免硬编码颜色与尺寸。

### 3.4 单位策略
全部使用 `rpx`（微信小程序响应式像素）作为长度单位，保证在不同屏幕宽度下保持一致的比例布局。

## 4. 约定与约束

- **禁止在页面/组件中直接写死十六进制颜色或像素值**：token 文件注释明确要求“页面不直接使用原始色值”，应通过 `$pf-color-*` 语义变量引用。
- **所有新增视觉属性必须先在 `design-tokens.scss` 中声明**，再在组件中使用，保持单一来源。
- **uv-ui 组件主题不可在组件内局部覆盖**：统一通过 `uni.scss` 中的 `$uv-*` 变量覆盖，确保全应用一致。
- **BEM 命名用于业务组件**，原子类用于通用 UI 片段，二者分工清晰。
- **响应式策略**：依赖 uni-app 的 `rpx` 单位 + 多端构建（mp-weixin、h5、mp-alipay 等），不在代码中编写媒体查询。
- **无 CSS Modules / Tailwind / CSS-in-JS**：整个前端样式体系建立在 SCSS + 设计令牌之上，未引入其他样式方案。

综上，该仓库的前端样式体系以 SCSS 设计令牌为核心，通过 `uni.scss` 桥接 uni-app 与 uv-ui 两套生态变量，形成“原始色 → 语义色 → 组件主题 → 页面/组件”的单向依赖链，保证了多端小程序视觉一致性。