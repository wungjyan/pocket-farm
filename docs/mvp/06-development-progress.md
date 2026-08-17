# MVP 开发进度

本文档记录“掌上农场”MVP 的实际开发状态。`05-development-plan.md` 是计划基线；本文件只记录已完成的工作、当前阶段和验证结果。

## 维护规则

- 每个 Phase 完成并完成验证后，更新对应阶段的状态、完成日期和交付内容。
- 记录实际新增的 API、Alembic migration、测试结果和未解决问题。
- 只记录已完成且已验证的内容；未开始的阶段不提前标记完成。
- 开始下一阶段前，以“当前阶段”一节为准确认开发范围。

## 当前阶段

**Phase 0：工程初始化已完成。**

下一阶段为 **Phase 1：Auth + User**。尚未开始，当前不存在 `users` 或其他业务表。

## 阶段状态

| Phase | 内容 | 状态 | 完成日期 |
| --- | --- | --- | --- |
| 0 | 工程初始化 | 已完成 | 2026-08-17 |
| 1 | Auth + User | 未开始 | - |
| 2 | Farm + FarmMember | 未开始 | - |
| 3 | Plot | 未开始 | - |
| 4 | Species + Production | 未开始 | - |
| 5 | FarmOperation | 未开始 | - |
| 6 | HarvestRecord | 未开始 | - |
| 7 | 结束种养 | 未开始 | - |
| 8 | 地块完整详情 | 未开始 | - |
| 9 | 小程序完整联调 | 未开始 | - |

## Phase 0 交付记录

### 工程与运行环境

- 后端位于 `apps/api/`，使用 Python 3.12 和 uv 独立管理依赖，不加入 pnpm workspace。
- 已配置 FastAPI、pydantic-settings、SQLAlchemy 2.x、aiomysql、Alembic、pytest、httpx 与 Ruff。
- 已提供 `.env.example`；本地运行需在 `apps/api/` 创建 `.env` 并提供数据库连接和 JWT 密钥。
- 本地 MySQL 使用 `mysql:8.0`，数据库访问链路均为 async / await。

### 基础能力

- `Settings`、异步 Engine、`async_sessionmaker` 和每请求独立的 `AsyncSession` Dependency 已就绪。
- 已建立带命名约定的 SQLAlchemy `DeclarativeBase`。
- 已建立基础应用异常结构，响应格式为 `detail.code` 和 `detail.message`。
- 已提供 `GET /health`，通过异步 `SELECT 1` 验证数据库连接。

### Migration

- 当前 Alembic revision：`ea649aaf28e0`（`initialize schema`）。
- revision 仅建立 Alembic 的版本基线，不包含业务表 DDL。
- 数据库中仅有 `alembic_version`，没有业务表。

### 验证结果

- `uv run alembic current`：通过，当前为 `ea649aaf28e0 (head)`。
- `uv run alembic check`：通过，无待生成 migration。
- `uv run pytest`：通过（1 passed）。
- `uv run ruff check .` 和 `uv run ruff format --check .`：通过。
- 启动 Uvicorn 后，`GET /health` 返回 `200 {"status":"ok"}`。

### 未解决问题

无阻塞问题。
