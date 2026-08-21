---
kind: configuration_system
name: 基于 pydantic-settings 与 Vite 环境变量的分层配置系统
category: configuration_system
scope:
    - '**'
source_files:
    - apps/api/app/core/config.py
    - apps/api/.env.example
    - apps/api/alembic/env.py
    - apps/api/pyproject.toml
    - apps/miniapp/src/services/http.ts
    - apps/miniapp/.env.example
    - apps/miniapp/vite.config.ts
    - docs/.vitepress/config.mts
---

## 1. 整体方案

本仓库采用按子应用隔离、统一模式的配置体系：
- 后端（apps/api）：使用 pydantic-settings 的 BaseSettings，从环境变量或 .env 文件加载并强类型校验所有运行时配置。
- 小程序前端（apps/miniapp）：通过 Vite 的 import.meta.env.VITE_* 注入构建期环境变量，默认指向本地 API。
- 文档站（docs/.vitepress）：以静态 config.mts 内联站点元信息，无外部配置文件。

三个子项目互不共享配置，各自维护自己的 .env.example 模板。

## 2. 关键文件与职责

- apps/api/app/core/config.py：定义 Settings 模型，集中声明全部应用级配置项（数据库 URL、JWT、时区、调试开关等），并通过 Settings() 单例暴露。
- apps/api/.env.example：提供完整的环境变量模板，含数据库连接串、JWT 密钥、测试登录开关等。
- apps/api/alembic/env.py：Alembic 迁移脚本直接复用 app.core.config.settings.database_url，保证迁移与运行期共用同一数据源配置。
- apps/api/pyproject.toml：声明 pydantic-settings 为依赖，并通过 tool.ruff、tool.pytest.ini_options 固化开发期工具行为。
- apps/miniapp/src/services/http.ts：读取 import.meta.env.VITE_API_BASE_URL 作为后端基址，未设置时回退到 http://127.0.0.1:8000/api/v1。
- apps/miniapp/.env.example：提供 VITE_API_BASE_URL 模板，注释说明微信开发者工具与真机调试地址差异。
- apps/miniapp/vite.config.ts：最小化 Vite 配置，仅启用 uni 插件，其余由 uni-app/Vite 默认约定。
- docs/.vitepress/config.mts：文档站点的标题、导航、侧边栏等静态配置，直接写在代码中。

## 3. 架构与约定

### 后端配置加载顺序（pydantic-settings）
SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore") 表明：
1. 首先尝试从当前工作目录下的 .env 文件加载；
2. 随后用同名环境变量覆盖（操作系统/容器/进程环境变量优先级更高）；
3. 未知字段被忽略（extra="ignore"），避免拼写错误导致启动失败。

所有配置项在 Settings 类中以 Pydantic 字段声明，具备类型与默认值：
- 必填项：database_url、jwt_secret_key（类型为 SecretStr，避免日志泄露）
- 带默认值的可选项：debug=False、api_v1_prefix="/api/v1"、jwt_algorithm="HS256"、jwt_expire_minutes=10080、app_timezone="Asia/Shanghai"、test_login_enabled=False、test_login_code="8888"

模块级 settings = Settings() 作为全局单例，被 main.py、db/session.py、alembic/env.py 等直接 import 使用。

### 前端配置注入（Vite + uni-app）
- 通过 import.meta.env.VITE_API_BASE_URL 读取，前缀 VITE_ 是 Vite 暴露给客户端的唯一约定。
- 若未设置，硬编码回退到 http://127.0.0.1:8000/api/v1，便于本地开发开箱即用。
- .env.example 提供模板，实际 .env.local（见 miniapp 根目录）用于覆盖。

### 迁移与运行配置共享
alembic/env.py 直接 from app.core.config import settings 并调用 settings.database_url，确保数据库迁移与 API 服务使用完全一致的连接字符串，避免本地能跑、迁移失败的分歧。

## 4. 约定与约束

- 敏感信息不进仓库：.env 文件本身不在版本控制中（.gitignore 排除），仅提交 .env.example 作为契约模板。
- 配置即类型：新增配置必须先在 Settings 类中添加字段，再在 .env.example 补充对应键，否则无法被读取且不会静默失败（Pydantic 会抛错）。
- JWT 密钥强制 SecretStr：jwt_secret_key 使用 SecretStr 类型，序列化/打印时自动脱敏。
- API 路径前缀集中管理：api_v1_prefix 同时影响 FastAPI 路由注册与小程序 http.ts 中的默认基址 /api/v1，修改需两端同步。
- 测试开关与环境隔离：TEST_LOGIN_ENABLED / TEST_LOGIN_CODE 允许测试环境绕过真实认证，生产部署时应关闭。
- Alembic 不单独维护数据库 URL：迁移脚本不读 alembic.ini 中的 sqlalchemy.url，而是通过 config.set_main_option("sqlalchemy.url", settings.database_url) 动态注入，来源唯一。
- 文档站配置内联：VitePress 配置直接写在 config.mts 中，没有拆分到 .json/.yaml，因为站点结构稳定、变更频率低。

## 5. 适用性说明

该配置系统覆盖后端运行期配置、前端构建期配置以及数据库迁移配置，但不包含 feature flag 机制、远程配置中心或运行时热更新——这些能力在当前代码库中不存在。