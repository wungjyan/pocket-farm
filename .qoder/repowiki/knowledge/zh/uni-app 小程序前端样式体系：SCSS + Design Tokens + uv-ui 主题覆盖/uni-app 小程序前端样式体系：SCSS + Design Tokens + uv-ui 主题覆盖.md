---
kind: frontend_style
name: uni-app 小程序前端样式体系：SCSS + Design Tokens + uv-ui 主题覆盖
category: frontend_style
scope:
    - '**'
source_files:
    - apps/miniapp/src/styles/design-tokens.scss
    - apps/miniapp/src/styles/pocket-farm.scss
    - apps/miniapp/src/uni.scss
    - apps/miniapp/package.json
    - apps/miniapp/src/components/PfPageHeader.vue
    - apps/miniapp/src/pages/home/index.vue
---

## 1. 系统概览

Pocket Farm 的前端基于 **uni-app + Vue 3**（`apps/miniapp`），样式采用 **SCSS 预处理**，通过一套自研的 **Design Tokens（设计令牌）** 统一管理颜色、间距、圆角与阴影，并以此覆盖第三方组件库 **uv-ui** 的主题变量，实现全站视觉一致性。构建工具链使用 Vite（`@dcloudio/vite-plugin-uni`）+ `sass` 预处理器。

## 2. 关键文件与包

- `apps/miniapp/src/styles/design-tokens.scss`：原始色阶 → 语义色 → 尺寸/动效 三层 token 定义，是全局唯一的设计源。
- `apps/miniapp/src/styles/pocket-farm.scss`：基于 token 的全局页面级样式（`.pf-page`、`.pf-card`、`.pf-list-card`、`.pf-section-*`、`.pf-tappable` 等原子类）。
- `apps/miniapp/src/uni.scss`：uni-app 入口样式，导入 uv-ui 主题与项目 token，并将 `$pf-*` 映射到 `$uv-*`、`$uni-*` 等框架变量，使第三方组件自动继承品牌色。
- `apps/miniapp/package.json`：声明依赖 `sass ^1.102.0`、`vite 5.2.8`、`vue ^3.4.21` 及全套 `@dcloudio/*` uni-app 多端运行时。
- `apps/miniapp/src/components/PfPageHeader.vue`、`src/pages/home/index.vue` 等页面/组件：以 `<style lang="scss" scoped>` 引入 `design-tokens.scss`，仅使用 token 变量，不出现硬编码色值。
- `apps/miniapp/src/uni_modules/uv-ui-tools/theme.scss`：uv-ui 主题源，被 `uni.scss` 覆盖后生效。

## 3. 架构与约定

### 3.1 三层 Design Token 体系
`design-tokens.scss` 明确分为三段：
- **Primitive（原始色阶）**：`$pf-green-800/700/100/50`、`$pf-neutral-950~50`、`$pf-red/amber/blue` 系列。
- **Semantic（语义色）**：将原始色映射为业务语义，如 `$pf-color-primary`、`$pf-color-text`、`$pf-color-danger`、`$pf-color-surface-accent` 等；并为“收获/农事”主流程保留 `$pf-color-harvest` / `$pf-color-water` 兼容别名。
- **Spacing & Shape & Motion**：统一间距 `$pf-space-1..8`（单位 `rpx`）、圆角 `$pf-radius-control/list/card/card-lg`、阴影 `$pf-shadow-card/raised`、动画时长 `$pf-duration-fast`。

### 3.2 全局样式层
`pocket-farm.scss` 提供页面骨架与通用 UI 块：
- `.pf-page` / `.pf-page-content`：页面容器与内边距。
- `.pf-section-heading` / `.pf-section-title` / `.pf-section-note` / `.pf-section-action`：区块标题与说明。
- `.pf-card` / `.pf-card--emphasis` / `.pf-list-card` / `.pf-list-divider`：卡片与列表样式。
- `.pf-tappable`：统一的点击态（opacity + scale 过渡）。

### 3.3 第三方组件主题覆盖
`uni.scss` 在顶部先 `@import '@/uni_modules/uv-ui-tools/theme.scss'`，再 `@import '@/styles/design-tokens.scss'`，随后把 `$pf-*` 全部映射到 `$uv-*`（如 `$uv-primary: $pf-color-primary`、`$uv-success: $pf-color-primary`、`$uv-error: $pf-color-danger`、`$uv-info: $pf-color-info`）以及 uni-app 内置变量（`$uni-color-*`、`$uni-bg-color`、`$uni-border-color`、`$uni-font-size-*` 等）。这样所有 `uv-button`、`uv-icon`、`uv-toast` 等组件自动使用品牌绿色调。

### 3.4 组件内样式组织
每个 `.vue` 组件使用 `<style lang="scss" scoped>`，并通过 `@import "../styles/design-tokens.scss"` 或 `../../styles/design-tokens.scss` 获取 token。组件内部只引用 token 变量，不直接写十六进制色值（除个别 `uv-icon` 的 `color="#17231B"` 等硬编码外，整体遵循 token 优先）。命名采用 BEM 风格（如 `.pf-page-header__title`、`.pf-page-header--tab`）。

### 3.5 响应式策略
移动端使用 `rpx` 作为统一长度单位（间距、字号、圆角、阴影均用 `rpx`），适配不同屏幕宽度；未使用媒体查询做断点切换，布局主要依赖 flex/grid 与百分比/`minmax` 自适应（如首页 action-grid 的 `repeat(2, minmax(0, 1fr))`）。

## 4. 约定与约束

- **颜色必须来自 token**：`design-tokens.scss` 注释明确“原始色阶 → 语义色 → 组件尺寸，页面不直接使用原始色值”，页面与组件应通过 `$pf-color-*` 引用，而非硬编码 hex。
- **间距与圆角走 token**：统一使用 `$pf-space-*`、`$pf-radius-*`，避免散落 `8rpx`/`16rpx` 等魔法数字。
- **全局样式集中管理**：页面级公共样式放在 `pocket-farm.scss`，组件私有样式写在各自 `<style scoped>` 中，不污染全局。
- **uv-ui 主题通过变量覆盖**：新增品牌色时只需修改 `design-tokens.scss`，再由 `uni.scss` 映射到 `$uv-*`，无需逐个改组件。
- **单位统一为 rpx**：所有间距、字号、圆角、阴影半径均以 `rpx` 表达，保证多端一致。
- **交互态统一**：可点击元素使用 `.pf-tappable` 获得一致的 opacity/scale 过渡（`$pf-duration-fast`）。
- **文档站独立**：`docs/` 目录使用 VitePress，与小程序前端样式体系隔离，不参与本样式规则。