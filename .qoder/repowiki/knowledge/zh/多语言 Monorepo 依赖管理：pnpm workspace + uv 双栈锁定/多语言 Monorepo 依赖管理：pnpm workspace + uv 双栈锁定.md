---
kind: dependency_management
name: 多语言 Monorepo 依赖管理：pnpm workspace + uv 双栈锁定
category: dependency_management
scope:
    - '**'
source_files:
    - pnpm-workspace.yaml
    - package.json
    - pnpm-lock.yaml
    - apps/api/pyproject.toml
    - apps/api/uv.lock
    - apps/miniapp/package.json
---

## 1. 使用的系统/方法

本仓库是一个包含 Python FastAPI 后端、uni-app（Vue 3）小程序前端与 VitePress 文档站的 monorepo，采用**按语言分治**的依赖管理策略：
- **Node.js 侧**：使用 **pnpm v11** 作为包管理器，通过根级 `pnpm-workspace.yaml` 将 `apps/miniapp` 纳入工作区；根 `package.json` 通过 `devEngines.packageManager` 强制要求 pnpm `^11.0.8`，并在 `onFail: download` 时自动下载指定版本。
- **Python 侧**：使用 **uv** 作为包管理器，声明在 `apps/api/pyproject.toml` 中，并通过 `uv.lock` 锁定所有依赖及其传递依赖的精确版本与哈希。
- **文档站**：VitePress 等文档工具作为根 `devDependencies` 直接安装，不参与 workspace。

未检出任何私有 npm registry、`.npmrc`、`pip.conf`、`uv.toml` 或 `pyproject.toml` 中的 `[tool.uv.sources]` 配置，所有包均从公共源拉取：npmjs.org（pnpm）、pypi.org/simple（uv）。不存在 vendoring（无 `vendor/` 目录），但 uni-app 小程序通过 `uni_modules/` 以源码形式内聚了大量 uView 组件（每个子组件带独立 `package.json`），属于框架约定的“模块内联”而非传统 vendoring。

## 2. 关键文件

| 文件 | 作用 |
|---|---|
| `pnpm-workspace.yaml` | 定义 workspace 成员（`packages/*`、`apps/miniapp`），并显式允许 `@parcel/watcher`、`puppeteer` 执行构建脚本 |
| `package.json`（根） | 统一脚本入口（`api:dev`、`miniapp:dev`、`docs:*`），声明 pnpm 引擎约束与文档站 devDependencies |
| `pnpm-lock.yaml` | Node 依赖锁定文件（lockfileVersion 9.0），锁定 pnpm 自身及所有 workspace 依赖 |
| `apps/api/pyproject.toml` | Python 项目元数据、运行时依赖（FastAPI、SQLAlchemy、Alembic 等）与 dev dependency groups（pytest、ruff、httpx） |
| `apps/api/uv.lock` | uv 生成的完整依赖图锁定文件，含每个包的 sha256 hash 与来源 registry |
| `apps/miniapp/package.json` | uni-app 小程序依赖声明（`@dcloudio/uni-*` 系列、vue、sass、typescript 等） |
| `apps/miniapp/uni_modules/*/package.json` | 各 uView 组件的独立 package.json，作为 uni-app 插件机制的内联依赖 |

## 3. 架构与约定

- **Monorepo 边界清晰**：Node 与 Python 两套依赖体系完全隔离，互不引用。根 `package.json` 仅编排跨语言脚本（如 `uv run --directory apps/api uvicorn ...`），不引入 Python 依赖。
- **Workspace 粒度**：workspace 仅包含 `apps/miniapp`，文档站（VitePress）直接挂在根 `devDependencies`，避免被误纳入 workspace 解析。
- **严格锁定**：pnpm 与 uv 均生成 lockfile，确保团队与 CI 环境复现一致；Python 侧进一步对每个 wheel/sdist 记录 sha256，提升可验证性。
- **构建脚本白名单**：`pnpm-workspace.yaml` 的 `allowBuilds` 仅放行 `@parcel/watcher` 与 `puppeteer`，防止其他包意外执行原生编译。
- **依赖分组**：Python 侧通过 `[dependency-groups].dev` 区分运行时与开发依赖，便于生产镜像裁剪。
- **平台兼容**：pnpm 锁文件中为不同 OS/CPU/libc 组合提供平台特定二进制（如 `@reflink/reflink-darwin-arm64`、`@pnpm/linux-x64`），由 pnpm 在安装时按需选择。

## 4. 约定与约束

- **必须使用 pnpm ^11.0.8**：根 `package.json` 的 `devEngines.packageManager` 强制该版本，否则安装失败。
- **Python 最低版本 >=3.12**：`pyproject.toml` 的 `requires-python = ">=3.12"` 限制运行环境。
- **新增 workspace 成员需同步更新 `pnpm-workspace.yaml`**：当前只显式注册了 `apps/miniapp`，新 Node 应用需加入此列表才能被 `pnpm -filter` 识别。
- **构建型原生包需显式 allowBuilds**：若新增需要编译的原生依赖，需在 `pnpm-workspace.yaml` 的 `allowBuilds` 中添加其包名，否则会拒绝执行构建脚本。
- **Python 依赖变更需提交 `uv.lock`**：修改 `pyproject.toml` 后应通过 `uv lock` 重新生成锁定文件，保证依赖图与哈希一致。
- **uni-app 第三方 UI 以 `uni_modules/` 内联方式引入**：uView 组件以源码形式驻留在仓库中，升级需手动替换对应目录下的文件，不受 pnpm 管理。
- **无私有源/代理配置**：仓库未检出 `.npmrc`、`pnpm-workspace.yaml` 中的 `registry`、`always-auth`，也未检出 `uv` 的 `--index-url` 或 `PYPI_INDEX_URL` 相关配置，默认走公网源。

## 5. 风险与建议

- 根 `package.json` 的 `devEngines` 仅约束 pnpm 版本，未约束 Node 版本；建议补充 `engines.node` 字段以避免环境差异。
- `pnpm-workspace.yaml` 的 `packages` 模式 `packages/*` 目前为空，若未来创建共享 `packages/` 包，需确保命名规范与依赖发布策略。
- 小程序端大量依赖以 `uni_modules/` 源码形式内联，升级成本较高且难以享受 pnpm 的增量缓存优势；可评估是否迁移至 npm 包形式。
- 未发现自动化依赖更新流程（如 Dependabot/Renovate），建议引入以跟踪上游安全更新。
