---
kind: logging_system
name: 日志系统：基于 Uvicorn/FastAPI 默认日志与 Alembic 文件配置，业务层未引入结构化日志框架
category: logging_system
scope:
    - '**'
source_files:
    - apps/api/app/main.py
    - apps/api/app/core/config.py
    - apps/api/alembic/env.py
    - apps/api/pyproject.toml
---

## 1. 使用的系统与方案

- **后端（apps/api）**：项目依赖 `uvicorn[standard]`（见 `apps/api/pyproject.toml`），FastAPI 应用通过 `create_application()` 在 `app/main.py` 中创建，并传入 `debug=settings.debug`。Uvicorn 作为 ASGI 服务器会自带标准 Python `logging` 模块的访问请求日志（access log）；FastAPI 本身不额外注册 logger。
- **迁移工具（Alembic）**：`apps/api/alembic/env.py` 通过 `from logging.config import fileConfig` 加载 `alembic.ini` 中的日志配置（第 36–37 行），用于控制 Alembic 自身的 SQL/迁移日志输出。
- **小程序前端（apps/miniapp）**：代码中未发现自研日志模块或统一日志 SDK；第三方组件 `uv-qrcode`、`uv-transition`、`uv-skeleton` 等直接调用 `console.log / console.warn / console.error` 输出调试信息，属于 uni-app 运行时的控制台输出。

## 2. 关键文件

| 文件 | 作用 |
|---|---|
| `apps/api/app/main.py` | FastAPI 应用入口，仅设置 `debug`，无自定义 logger 初始化 |
| `apps/api/app/core/config.py` | Pydantic Settings，包含 `debug`、`app_name`、`app_timezone` 等配置项，但**没有** `log_level` / `log_format` 字段 |
| `apps/api/alembic/env.py` | 通过 `logging.config.fileConfig` 加载 Alembic 日志配置 |
| `apps/api/pyproject.toml` | 声明依赖 `uvicorn[standard]`，是运行时日志的唯一来源 |
| `apps/miniapp/src/uni_modules/.../*.vue` | 第三方 UI 组件内嵌的 `console.*` 调试输出 |

## 3. 架构与约定

- **无中心化 Logger 模块**：仓库中没有 `logger.py`、`log.py`、`logging_config.py` 之类的集中式日志初始化文件；各模块若需要记录日志，只能自行 `import logging` 获取 logger。
- **日志级别由环境驱动**：FastAPI/Uvicorn 的行为受 `settings.debug` 影响（`debug=True` 时返回详细错误页），但应用内部没有统一的 `LOG_LEVEL` 环境变量约定。
- **结构化字段缺失**：当前没有任何地方使用 `python-json-logger`、`structlog`、`loguru` 等结构化日志库；日志输出为 Uvicorn 默认的纯文本格式。
- **请求级日志**：仅由 Uvicorn 在启动后自动打印 HTTP 访问日志，业务代码中未见对请求 ID、用户 ID、租户 ID 等上下文字段的注入。
- **异常日志**：`app/main.py` 调用 `register_exception_handlers(app)`（位于 `app/core/exceptions.py`）注册全局异常处理器，但未看到在其中追加结构化日志字段。

## 4. 约定与约束

- **后端**：
  - 日志来源主要是 Uvicorn 的默认 access/error 日志；业务层未强制要求使用特定 logger。
  - Alembic 迁移日志通过 `alembic.ini` + `fileConfig` 管理，迁移脚本不应自行 `print` 替代日志。
  - 配置项集中在 `Settings`（`app/core/config.py`），目前未定义 `log_level` 字段，因此日志级别无法通过 `.env` 动态切换。
- **前端（小程序）**：
  - 业务代码中未发现 `console.log/warn/error` 调用（仅在 `uni_modules` 第三方组件中存在），说明业务层尚未主动输出调试日志。
  - 所有 `console.*` 调用均来自第三方 `uv-*` 组件，非项目自有实现。
- **约束性规则**：仓库中不存在可被 lint/test 强制执行的日志规范（如禁止 `print`、要求结构化字段等）；Ruff 配置仅启用 `E`、`F`、`I` 规则，未包含日志相关规则。

## 5. 现状总结

该仓库的“日志系统”处于**极轻量状态**：后端依赖 Uvicorn 默认日志 + Alembic 文件配置，无业务层结构化日志；前端仅依赖 uni-app 控制台输出且业务代码未主动打点。若需增强，可在 `app/core/config.py` 增加 `log_level`、在 `main.py` 启动时配置 `logging.basicConfig` 或使用 `python-json-logger`/`loguru` 统一输出格式与 sink。
