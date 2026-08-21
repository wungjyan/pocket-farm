---
kind: build_system
name: 基于 pnpm workspace 的 Monorepo 构建与脚本体系
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

## 1. 使用的系统/方法

本项目采用 **pnpm workspace** 作为 monorepo 根级构建编排工具，将三个子应用（`apps/api`、`apps/miniapp`、`docs`）聚合在一个仓库中，通过根 `package.json` 的 `scripts` 统一暴露开发入口。Python 后端使用 **uv** 作为包管理与运行器（`uv run uvicorn ...`），并通过 `pyproject.toml` 声明依赖与工具配置；前端小程序使用 **uni-app + Vite** 构建多端产物；文档站使用 **VitePress** 构建静态站点。

## 2. 关键文件

- `package.json`：根工作区脚本入口，定义 `docs:dev/build/preview`、`api:dev`、`miniapp:dev/build` 等命令，并通过 `devEngines.packageManager` 强制要求 pnpm ^11.0.8。
- `pnpm-workspace.yaml`：声明工作区包含 `packages/*` 与 `apps/miniapp`，并通过 `allowBuilds` 白名单放行 `@parcel/watcher`、`puppeteer` 的原生编译。
- `apps/api/pyproject.toml`：后端 Python 项目元数据，声明 Python ≥3.12、FastAPI 等运行时依赖，以及 `dev` 依赖组（httpx、pytest、ruff），并内嵌 pytest/ruff 配置。
- `apps/api/.env.example` / `.env`：后端环境变量模板。
- `apps/miniapp/package.json`：uni-app 小程序工程，提供针对多端（mp-weixin、mp-alipay、mp-h5 等）的 `dev:*` / `build:*` 脚本，当前根脚本仅启用微信小程序目标。
- `apps/miniapp/vite.config.ts`：基于 `@dcloudio/vite-plugin-uni` 的最小化 Vite 配置。
- `docs/.vitepress/config.mts`：VitePress 文档站配置。

## 3. 架构与约定

- **Monorepo 分层**：根目录只负责编排，各子应用独立维护自己的依赖与构建脚本。根 `scripts` 通过 `uv run --directory apps/api` 和 `pnpm --filter uni-preset-vue` 分别调用后端与小程序。
- **后端构建**：不经过传统打包步骤，直接以 `uvicorn app.main:app` 启动 FastAPI 应用；数据库迁移通过 Alembic（`alembic.ini` + `alembic/versions/*.py`）管理。
- **前端构建**：小程序通过 uni-app CLI 按平台生成对应产物（如 `dist/dev/mp-weixin`），根脚本默认绑定到微信小程序 (`mp-weixin`)。
- **文档构建**：VitePress 在 `docs/` 目录下独立构建，根脚本提供 dev/build/preview 三种模式。
- **版本策略**：根 `package.json` 固定版本号 `1.0.0`，后端 `server` 为 `0.1.0`，小程序 `uni-preset-vue` 为 `0.0.0`，各子应用各自维护自身版本，未见统一的版本同步脚本。

## 4. 约定与约束

- **包管理器锁定**：根 `package.json` 的 `devEngines.packageManager` 要求 pnpm ^11.0.8，并在失败时自动下载，确保团队环境一致。
- **Python 版本约束**：`pyproject.toml` 要求 `requires-python = ">=3.12"`，Ruff 目标版本也设为 py312。
- **代码质量工具**：Ruff 规则集限定为 `E`（pycodestyle）、`F`（pyflakes）、`I`（isort），行宽限制 100 列，且显式排除 `alembic/versions` 目录。
- **测试路径**：pytest 通过 `testpaths = ["tests"]` 与 `pythonpath = ["."]` 限定测试发现范围。
- **原生模块白名单**：`pnpm-workspace.yaml` 的 `allowBuilds` 仅允许 `@parcel/watcher` 与 `puppeteer` 进行原生编译，其他含 C++ 扩展的包需显式放开。
- **无容器化/CI**：仓库中未发现 Dockerfile、docker-compose、GitHub Actions、GitLab CI 或 Makefile 等持续集成/部署配置，构建与发布目前依赖本地脚本与命令行手动执行。
- **环境变量**：后端通过 `.env` / `.env.example` 注入配置（由 pydantic-settings 读取），小程序通过 `.env.local` 覆盖默认环境。

总结：该仓库是一个以 pnpm workspace 为核心的轻量 monorepo，构建流程集中在根 `package.json` 的脚本层，后端走 uv+uvicorn 直启模式，小程序走 uni-app 多端构建，文档走 VitePress；尚未引入容器化与自动化 CI/CD 流水线。