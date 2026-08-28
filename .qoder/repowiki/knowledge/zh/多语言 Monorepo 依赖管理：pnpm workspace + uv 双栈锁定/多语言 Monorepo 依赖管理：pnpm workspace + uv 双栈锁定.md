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

## 1. 使用的系统与工具

本仓库是一个包含 Python FastAPI 后端、uni-app 小程序前端与 VitePress 文档站的 Monorepo，采用**按语言/子项目隔离的包管理器**策略：

- **Node.js 侧（apps/miniapp、docs、根 scripts）**：使用 **pnpm v11** 作为工作区包管理器，通过 `pnpm-workspace.yaml` 声明工作区成员，并使用根级 `package.json` 的 `devEngines.packageManager` 强制要求 pnpm 版本（`^11.0.8`，`onFail: download` 自动下载）。
- **Python 侧（apps/api）**：使用 **uv** 作为包管理与虚拟环境工具，以 `pyproject.toml` 声明运行时与开发依赖，并以 `uv.lock` 进行精确锁定。

两个子系统各自维护独立的锁文件（`pnpm-lock.yaml`、`uv.lock`），互不干扰。

## 2. 关键文件

| 文件 | 作用 |
|---|---|
| `pnpm-workspace.yaml` | 声明工作区成员为 `packages/*` 与 `apps/miniapp`；通过 `allowBuilds` 显式允许 `@parcel/watcher`、`puppeteer` 的原生构建 |
| `package.json`（根） | 定义跨子项目的统一脚本（`api:dev`、`miniapp:dev`、`docs:*`），并通过 `devEngines` 约束 pnpm 版本 |
| `pnpm-lock.yaml` | Node 依赖的完整锁定文件 |
| `apps/api/pyproject.toml` | 声明 Python 运行时依赖（FastAPI、SQLAlchemy、Alembic 等）与 `dev` 依赖组（pytest、ruff、httpx） |
| `apps/api/uv.lock` | uv 生成的全量锁定文件，记录每个包的来源（`registry = https://pypi.org/simple`）、hash 与 wheel/sdist 地址 |
| `apps/miniapp/package.json` | uni-app 小程序的依赖声明（`@dcloudio/uni-*` 系列、Vue 3、Vite 等） |
| `apps/miniapp/uni_modules/` | 以源码形式内联引入的 uni-app 插件（如 `uv-ui` 组件库），不走 npm 安装，属于**vendoring**模式 |

## 3. 架构与约定

### 3.1 工作区划分
- pnpm 工作区仅包含 `apps/miniapp` 和 `packages/*`（当前无共享 packages），文档站（VitePress）通过根 `package.json` 的 `scripts` 直接调用 `vitepress`，不属于工作区成员。
- Python 后端完全独立于 pnpm 生态，由 uv 管理。

### 3.2 版本约束风格
- **Node 侧**：广泛使用 `^` 语义化版本范围（如 `vue: ^3.5.41`、`sass: ^1.102.0`），具体版本由 `pnpm-lock.yaml` 锁定。
- **Python 侧**：在 `pyproject.toml` 中使用 `>=` 宽松范围（如 `fastapi>=0.141.1`、`sqlalchemy>=2.0.51`），实际版本由 `uv.lock` 固定。

### 3.3 原生模块处理
- 通过 `pnpm-workspace.yaml` 的 `allowBuilds` 白名单机制，仅允许 `@parcel/watcher` 与 `puppeteer` 执行原生构建，其他包默认禁止。这是 pnpm 对带原生扩展的包的安全管控手段。

### 3.4 私有源/镜像
- 未发现 `.npmrc`、`.pypirc`、`pip.conf`、`uv.toml` 或环境变量中配置私有 registry 的证据。所有依赖均从公共源拉取：PyPI (`https://pypi.org/simple`) 与 npm 默认源。

### 3.5 依赖分组
- Python 侧通过 `[dependency-groups] dev = [...]` 将测试、lint 工具与运行时依赖分离，符合 PEP 735 规范。
- Node 侧未使用 workspaces 间共享依赖，miniapp 与 docs 各自声明自己的依赖。

## 4. 约定与约束

| 规则 | 依据 |
|---|---|
| 必须使用 pnpm v11.x 运行 Node 相关命令 | 根 `package.json` 的 `devEngines.packageManager.version = "^11.0.8"`，且 `onFail: download` 会在版本不符时尝试自动下载 |
| 原生构建包需显式放行 | `pnpm-workspace.yaml` 的 `allowBuilds` 仅允许 `@parcel/watcher` 与 `puppeteer`，其余含原生扩展的包将被拒绝 |
| Python 依赖变更必须更新 `uv.lock` | `uv.lock` 是受版本控制的可复现锁定文件，新增/升级依赖后应提交该文件 |
| 小程序第三方 UI 组件以源码 vendoring 方式引入 | `apps/miniapp/uni_modules/uv-*` 目录直接存放组件源码及各自的 `package.json`，不走 npm 安装流程 |
| 跨子项目启动统一通过根脚本 | 根 `package.json` 的 `scripts` 提供 `api:dev`、`miniapp:dev`、`docs:dev` 等入口，避免各子项目自行调用底层命令 |
| 工作区成员仅限 `packages/*` 与 `apps/miniapp` | `pnpm-workspace.yaml` 的 `packages` 字段明确限定，不在该列表中的目录不会被识别为工作区成员 |

## 5. 总结

该项目采用**多包管理器并行的 Monorepo 模式**：Node 生态用 pnpm workspace + 锁文件保证可复现安装，Python 生态用 uv + pyproject.toml + uv.lock 实现同样的目标。两者通过根级 `package.json` 的 scripts 统一编排，形成“一个仓库、两套依赖系统”的清晰边界。没有发现统一的私有 registry 或跨语言共享依赖方案，依赖更新分别在各子项目内完成并提交对应锁文件。