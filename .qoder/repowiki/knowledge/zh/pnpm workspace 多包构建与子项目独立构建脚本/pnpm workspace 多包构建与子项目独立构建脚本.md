---
kind: build_system
name: pnpm workspace 多包构建与子项目独立构建脚本
category: build_system
scope:
    - '**'
source_files:
    - package.json
    - pnpm-workspace.yaml
    - apps/api/pyproject.toml
    - apps/api/alembic.ini
    - apps/miniapp/package.json
    - apps/miniapp/vite.config.ts
    - docs/.vitepress/config.mts
---

## 1. 整体方案

仓库采用 **pnpm workspace** 作为 monorepo 编排层，聚合三个子项目：
- `apps/api`：Python FastAPI 后端（uv + pyproject.toml 管理）
- `apps/miniapp`：uni-app + Vue 3 小程序（@dcloudio/vite-plugin-uni 构建）
- `docs`：VitePress 文档站（根级 scripts 直接调用 vitepress）

根 `package.json` 通过 `scripts` 暴露统一入口，所有跨子项目的开发/构建命令均经此转发，形成“单仓多产物”的构建契约。

## 2. 关键文件

| 文件 | 作用 |
|---|---|
| `package.json` | 根工作区脚本、`devEngines.packageManager` 锁定 pnpm 版本（^11.0.8）、声明 docs/api/miniapp 三大入口 |
| `pnpm-workspace.yaml` | 声明 workspace 成员（`packages/*`、`apps/miniapp`），并通过 `allowBuilds` 放行 `@parcel/watcher`、`puppeteer` 的原生编译 |
| `apps/api/pyproject.toml` | Python 依赖、pytest/ruff 配置、Alembic 迁移目录 |
| `apps/miniapp/package.json` | uni-app 全平台 dev/build 脚本（mp-weixin / mp-alipay / h5 等）及 TypeScript/Sass 工具链 |
| `apps/miniapp/vite.config.ts` | 仅启用 `@dcloudio/vite-plugin-uni`，其余由 uni-cli 驱动 |
| `apps/api/alembic.ini` + `alembic/versions/*.py` | 数据库迁移构建产物 |
| `docs/.vitepress/config.mts` | VitePress 站点构建配置 |

## 3. 架构与约定

### 3.1 根级脚本即构建入口
根 `package.json` 定义以下脚本，作为开发者唯一入口：
- `pnpm docs:dev` / `docs:build` / `docs:preview` → 启动/构建 VitePress 文档站
- `pnpm api:dev` → `uv run --directory apps/api uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`，以热重载方式运行 FastAPI
- `pnpm miniapp:dev` / `miniapp:build` → `pnpm --filter uni-preset-vue dev:mp-weixin` / `build:mp-weixin`，通过 `--filter` 精确定位到 `apps/miniapp`（其 package name 为 `uni-preset-vue`）

### 3.2 子项目各自维护构建系统
- **后端**：使用 `uv` 作为 Python 运行时/包管理器（见 `api:dev` 中的 `uv run`），依赖锁定在 `uv.lock`；测试通过 `pytest`（`[tool.pytest]` 指定 `testpaths = ["tests"]`）；代码风格由 ruff 约束（`line-length = 100`，排除 alembic 生成文件）。
- **小程序**：基于 uni-app CLI（`@dcloudio/uni-cli-shared`），通过 `dev:*` / `build:*` 脚本支持微信、支付宝、百度、QQ、头条、Harmony、H5 等多端；TypeScript 类型检查走 `vue-tsc --noEmit`；Sass 预处理器由 `sass` 提供。
- **文档**：VitePress 直接由根脚本驱动，无需额外构建脚本。

### 3.3 工作区隔离
`pnpm-workspace.yaml` 仅将 `packages/*` 和 `apps/miniapp` 纳入 workspace；`apps/api` 是独立的 Python 工程，不参与 pnpm workspace 解析，通过根脚本的 `--directory` 参数间接协作。这种设计使 Python 与 Node 生态解耦。

## 4. 约定与约束

- **Node 版本锁定**：根 `package.json` 的 `devEngines.packageManager` 强制要求 pnpm ^11.0.8，不满足时自动下载指定版本。
- **原生模块白名单**：`pnpm-workspace.yaml` 中 `allowBuilds` 显式允许 `@parcel/watcher` 与 `puppeteer` 进行原生编译，其他未列出的原生包默认禁止构建。
- **后端依赖隔离**：`apps/api` 使用 `uv` 虚拟环境（`.venv/`），依赖通过 `pyproject.toml` + `uv.lock` 锁定，不在根 workspace 中共享。
- **小程序多端构建**：所有目标平台（mp-weixin、mp-alipay、h5 等）均通过统一的 `dev:*` / `build:*` 脚本族暴露，新增平台只需追加对应脚本条目。
- **无 CI/Dockerfile**：仓库中未发现 `.github/workflows`、`Dockerfile`、`docker-compose.yml`、`Makefile` 或 `build*.sh` 等持续集成/容器化配置，发布流程未在代码中体现。
- **Alembic 迁移**：数据库 schema 变更通过 `alembic/versions/*.py` 版本化，迁移脚本由 Alembic 自身管理，不属于通用构建脚本。

## 5. 结论

该仓库的构建体系以 **pnpm workspace 为协调层**，各子项目保留各自的构建工具链（uv+FastAPI、uni-app/Vite、VitePress），根 `package.json` 仅提供面向开发者的统一脚本入口。没有发现统一的 CI/CD、Docker 镜像或制品发布流程，构建关注点集中在本地开发与多端打包阶段。