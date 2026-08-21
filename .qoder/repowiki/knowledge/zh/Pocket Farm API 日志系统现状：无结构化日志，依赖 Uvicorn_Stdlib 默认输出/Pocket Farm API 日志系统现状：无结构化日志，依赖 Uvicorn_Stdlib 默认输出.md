---
kind: logging_system
name: Pocket Farm API 日志系统现状：无结构化日志，依赖 Uvicorn/Stdlib 默认输出
category: logging_system
scope:
    - '**'
source_files:
    - apps/api/pyproject.toml
    - apps/api/app/main.py
    - apps/api/app/core/config.py
    - apps/api/app/core/exceptions.py
    - apps/api/alembic/env.py
---

## 1. 使用的系统/方案

当前仓库的 Pocket Farm 后端（`apps/api`）没有引入任何第三方日志框架。代码中未出现 `loguru`、`structlog`、`python-json-logger`、`logging.config.dictConfig` 等配置；`pyproject.toml` 的运行时依赖仅包含 FastAPI、SQLAlchemy、Uvicorn、Pydantic Settings 等，不包含任何日志库。

因此，应用日志输出完全依赖以下两层默认行为：
- **Uvicorn 访问日志**：由 `uvicorn[standard]` 在启动时按默认格式输出请求级日志（method、path、status、duration），可通过环境变量或命令行参数调整级别与格式。
- **Python 标准库 `logging`**：仅在 Alembic 迁移脚本中被显式启用——`alembic/env.py` 通过 `from logging.config import fileConfig` 并调用 `fileConfig(config.config_file_name)` 加载 `alembic.ini` 中的日志配置，用于记录 SQL 迁移过程。

业务代码本身（FastAPI 路由、服务层、异常处理器）中没有任何 `print` 或 `logging` 调用，也没有自定义 logger 实例。

## 2. 关键文件

| 文件 | 作用 |
|---|---|
| `apps/api/pyproject.toml` | 声明依赖，确认未引入任何日志库 |
| `apps/api/app/main.py` | FastAPI 应用入口，仅注册异常处理器与路由，无日志初始化 |
| `apps/api/app/core/config.py` | 基于 Pydantic Settings 的配置类，包含 `app_name`、`debug`、`api_v1_prefix`、`database_url`、`jwt_*`、`app_timezone` 等字段，但**没有** `LOG_LEVEL`、`LOG_FORMAT`、`LOG_FILE` 等日志相关配置项 |
| `apps/api/app/core/exceptions.py` | 统一异常处理器（`AppException`、`RequestValidationError`、`HTTPException`、兜底 `Exception`），将异常转换为 JSON 响应，**不记录日志** |
| `apps/api/alembic/env.py` | 唯一使用 Python `logging` 的位置，通过 `fileConfig` 加载 Alembic 自身的日志配置 |

## 3. 架构与约定

- **日志来源单一**：生产环境可见的日志几乎全部来自 Uvicorn 进程的标准输出（stdout/stderr），包括 HTTP 访问日志和可能的异常堆栈。
- **无结构化日志**：由于未集成结构化日志框架，所有输出均为人类可读的纯文本，无法直接以 JSON 形式被日志采集器解析。
- **无日志级别管理**：`Settings` 中没有日志级别字段，无法通过环境变量切换 `DEBUG/INFO/WARNING/ERROR` 等级别；调试开关仅体现在 FastAPI 的 `debug=settings.debug` 上，影响的是开发模式下的自动文档与详细错误页。
- **异常处理与日志解耦**：异常处理器只负责返回标准化的 JSON 错误响应（`ApiResponse.error_response`），不记录错误上下文到日志，也不向外部告警系统推送。
- **Alembic 独立日志**：数据库迁移的日志由 Alembic 自身通过 `logging.config.fileConfig` 控制，与应用主流程隔离。

## 4. 约定与约束

- **业务代码禁止自行打印日志**：现有代码路径中未发现任何 `print()` 或 `logging.info/debug/error` 调用，说明团队尚未建立业务日志习惯；若未来需要添加日志，应遵循“先定义配置再实现”的原则。
- **日志配置必须集中化**：当前 `config.py` 是唯一的配置入口，新增日志相关设置（如 `LOG_LEVEL`、`LOG_FORMAT`、`LOG_OUTPUT`）应在此处以 Pydantic Settings 字段声明，并通过环境变量注入。
- **异常信息不应泄露给客户端**：`unhandled_exception_handler` 对未捕获异常统一返回固定消息 `Internal server error.`，避免内部细节外泄；这间接表明日志应作为内部诊断手段而非对外响应的一部分。
- **前端（miniapp）无服务端日志需求**：小程序端为 uni-app/Vue 项目，不涉及服务器日志；其网络请求封装位于 `src/services/http.ts`，如需前端日志需另行设计。

## 5. 总结

该仓库目前处于“无应用级日志系统”的状态：FastAPI 应用依赖 Uvicorn 默认访问日志，Alembic 迁移通过 stdlib `logging` 单独输出。缺少统一的日志框架、结构化字段、日志级别配置与日志收集策略。若后续需要增强可观测性，建议优先引入 `loguru` 或 `structlog`，并在 `app/core/config.py` 中增加日志相关配置项，同时在异常处理器中补充错误上下文记录。