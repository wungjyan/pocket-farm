# Pocket Farm Agent Instructions

本仓库是“掌上农场”MVP。

开始任何开发任务前：

1. 阅读 `docs/00-project-overview.md`。
2. 根据当前任务阅读对应的技术、领域和业务文档。
3. 阅读 `docs/05-development-plan.md`，确认当前 Phase。
4. 只实现当前明确要求的 Phase，不提前开发后续功能。

## 开发原则

- 优先保持实现简单、清晰、可维护。
- 不为了未来扩展提前增加复杂抽象。
- 不擅自增加需求中不存在的功能。
- 不引入微服务、Redis、MQ、Celery、Elasticsearch 等当前不需要的基础设施。
- 不建立 GenericRepository、BaseService 等无实际价值的通用抽象。
- 前端展示业务数值时统一复用 `apps/miniapp/src/utils/number.ts` 的 `formatNumber`：整数不显示小数部分，小数去除末尾无意义的 0；不得直接拼接接口返回的数值。
- 数据库结构变化必须使用 Alembic migration。
- 不修改已经执行过的历史 migration。
- 所有农场数据访问必须检查当前用户的 FarmMember 权限。
- 数据库使用 BIGINT AUTO_INCREMENT 主键，不使用 UUID。
- SQLAlchemy Model 不直接作为 API Response。
- 后端统一使用 SQLAlchemy AsyncSession + aiomysql，不要新增同步数据库访问路径。
- Router 只负责 HTTP 层，核心业务规则放在 Service。
- 重要业务流程必须补充测试。
- 需求存在歧义时先询问，不自行猜测。
- 每个 Phase 完成后运行测试并停止，等待确认。

## 后端常用命令

依赖：

`uv sync`

启动 MySQL：

`docker compose up -d mysql`

执行迁移：

`uv run alembic upgrade head`

启动 API：

`uv run uvicorn app.main:app --reload`

测试：

`uv run pytest`

代码检查：

`uv run ruff check .`
