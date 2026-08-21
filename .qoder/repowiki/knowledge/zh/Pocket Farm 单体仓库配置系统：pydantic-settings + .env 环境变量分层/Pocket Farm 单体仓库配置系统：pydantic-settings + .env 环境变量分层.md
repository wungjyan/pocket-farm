---
kind: configuration_system
name: Pocket Farm 单体仓库配置系统：pydantic-settings + .env 环境变量分层
category: configuration_system
scope:
    - '**'
source_files:
    - apps/api/app/core/config.py
    - apps/api/.env.example
    - apps/api/.env
    - apps/api/alembic.ini
    - apps/api/alembic/env.py
    - apps/miniapp/src/services/http.ts
    - apps/miniapp/.env.example
    - apps/miniapp/.env.local
    - apps/api/pyproject.toml
---

## 1. 使用的系统与工具

- **后端（FastAPI）**：使用 `pydantic-settings` 的 `BaseSettings` 作为统一配置加载器，通过 `.env` 文件与环境变量注入应用设置。
- **前端（uni-app + Vite）**：使用 Vite 内置的 `import.meta.env.*` 机制读取以 `VITE_` 为前缀的环境变量，配合 `.env.example` 与 `.env.local` 进行本地覆盖。
- **数据库迁移（Alembic）**：通过 `alembic.ini` 中的 `sqlalchemy.url` 占位符，在运行时由 `alembic/env.py` 从后端的 `settings.database_url` 动态覆写。

## 2. 关键文件

| 组件 | 文件 | 作用 |
|---|---|---|
| 后端核心配置 | `apps/api/app/core/config.py` | 定义 `Settings` 模型，声明所有应用级配置项及默认值 |
| 后端环境模板 | `apps/api/.env.example` | 列出全部必需/可选环境变量键名与示例值 |
| 后端本地环境 | `apps/api/.env` | 开发者本地实际生效的配置（含数据库 URL、JWT Secret） |
| Alembic 配置 | `apps/api/alembic.ini` | 迁移脚本路径、日志级别、占位数据库 URL |
| Alembic 运行入口 | `apps/api/alembic/env.py` | 将 `settings.database_url` 注入 Alembic 上下文 |
| 前端 API 基地址 | `apps/miniapp/src/services/http.ts` | 通过 `import.meta.env.VITE_API_BASE_URL` 读取后端地址 |
| 前端环境模板 | `apps/miniapp/.env.example` | 提供 `VITE_API_BASE_URL` 示例 |
| 前端本地覆盖 | `apps/miniapp/.env.local` | 真机调试时覆盖为局域网地址 |
| 项目依赖声明 | `apps/api/pyproject.toml` | 声明 `pydantic-settings`、`fastapi`、`uvicorn` 等依赖 |

## 3. 架构与约定

### 后端配置加载链
1. `apps/api/app/core/config.py` 中定义 `Settings(BaseSettings)`，通过 `model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")` 指定仅从当前工作目录的 `.env` 文件加载，忽略未知字段。
2. 模块顶部实例化全局 `settings = Settings()`，其他模块通过 `from app.core.config import settings` 获取单例。
3. 配置项分为三类：
   - 字符串/布尔/整型基础配置：`APP_NAME`、`DEBUG`、`API_V1_PREFIX`、`APP_TIMEZONE`、`TEST_LOGIN_ENABLED`、`TEST_LOGIN_CODE`。
   - 连接凭据：`DATABASE_URL`、`JWT_SECRET_KEY`（类型为 `SecretStr`，避免被打印）。
   - JWT 行为：`JWT_ALGORITHM`（默认 `HS256`）、`JWT_EXPIRE_MINUTES`（默认 7 天）。
4. 所有配置项均通过环境变量命名（全大写），与 `.env.example` 一一对应；未显式声明的额外环境变量会被 `extra="ignore"` 静默丢弃。

### Alembic 配置复用
- `alembic.ini` 中 `sqlalchemy.url` 填写占位值 `mysql+aiomysql://placeholder:placeholder@127.0.0.1:3306/placeholder`，禁止直接提交真实数据库 URL。
- `alembic/env.py` 在启动时调用 `config.set_main_option("sqlalchemy.url", settings.database_url)`，强制使用后端 `Settings` 中的数据库 URL，从而让迁移命令复用同一份 `.env` 配置。
- 同时导入所有 `app.models` 子模块（以触发 `Base.metadata` 注册），确保自动迁移能对比当前模型与数据库状态。

### 前端配置
- `apps/miniapp/src/services/http.ts` 在模块顶层读取 `import.meta.env.VITE_API_BASE_URL`，若未设置则回退到 `http://127.0.0.1:8000/api/v1`，并去除末尾斜杠。
- 通过 `VITE_` 前缀遵循 Vite 暴露给客户端的约定；`.env.example` 给出开发默认值，`.env.local` 用于覆盖为局域网地址以便真机调试。
- 前端无独立配置类，所有运行时配置均以常量形式集中在此文件中。

## 4. 约定与约束

- **单一事实源**：后端所有可配置项集中在 `app/core/config.py` 的 `Settings` 模型中，新增配置必须在此声明类型与默认值，否则无法被 pydantic-settings 解析。
- **敏感信息不入库**：`JWT_SECRET_KEY` 使用 `SecretStr` 类型，避免在日志或 repr 中泄露；`.env` 文件已在 `.gitignore` 中排除，仅 `.env.example` 提交到版本库。
- **环境变量命名规范**：后端配置项采用全大写蛇形命名（如 `DATABASE_URL`、`JWT_EXPIRE_MINUTES`），与 `.env.example` 保持一致；前端配置采用 `VITE_` 前缀加驼峰命名（如 `VITE_API_BASE_URL`）。
- **数据库 URL 只通过环境变量传入**：Alembic 的 `alembic.ini` 中不允许硬编码真实数据库 URL，必须经由 `settings.database_url` 注入，防止凭据泄漏。
- **忽略未知配置**：`extra="ignore"` 使 `Settings` 对 `.env` 中拼写错误或多出的键名保持静默，但这也意味着配置错误不会在启动时报错，需依赖 `.env.example` 与代码审查保证一致性。
- **测试开关**：`TEST_LOGIN_ENABLED` / `TEST_LOGIN_CODE` 允许测试环境绕过正常认证流程，生产部署时应确保这两个环境变量为关闭状态。
- **时区固定**：默认 `APP_TIMEZONE=Asia/Shanghai`，如需多时区支持应在该配置项上扩展而非在各模块内硬编码。