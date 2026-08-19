# MVP 开发进度

本文档记录“掌上农场”MVP 的实际开发状态。`05-development-plan.md` 是计划基线；本文件只记录已完成的工作、当前阶段和验证结果。

## 维护规则

- 每个 Phase 完成并完成验证后，更新对应阶段的状态、完成日期和交付内容。
- 记录实际新增的 API、Alembic migration、测试结果和未解决问题。
- 只记录已完成且已验证的内容；未开始的阶段不提前标记完成。
- 开始下一阶段前，以“当前阶段”一节为准确认开发范围。

## 当前阶段

**Phase 4：Species + Production 已完成。**

下一阶段为 **Phase 5：FarmOperation**。尚未开始。

## 阶段状态

| Phase | 内容 | 状态 | 完成日期 |
| --- | --- | --- | --- |
| 0 | 工程初始化 | 已完成 | 2026-08-17 |
| 1 | Auth + User | 已完成 | 2026-08-17 |
| 2 | Farm + FarmMember | 已完成 | 2026-08-18 |
| 3 | Plot | 已完成 | 2026-08-18 |
| 4 | Species + Production | 已完成 | 2026-08-19 |
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
- 已建立统一响应结构：`success`、`data`、`error`。
- 成功响应将业务结果放在 `data`；错误响应将 `data` 置为 `null`，并在 `error` 中返回 `code`、`message` 和可选的 `details`。
- 已统一处理业务异常、参数校验错误、HTTP 错误和未处理异常。
- 已提供 `GET /health`，通过异步 `SELECT 1` 验证数据库连接。

统一响应示例：

```json
{
  "success": true,
  "data": { "status": "ok" },
  "error": null
}
```

### Migration

- Phase 0 完成时的 Alembic revision：`ea649aaf28e0`（`initialize schema`）。
- 该 revision 仅建立 Alembic 的版本基线，不包含业务表 DDL。

### 验证结果

- `uv run alembic current`：通过，当前为 `ea649aaf28e0 (head)`。
- `uv run alembic check`：通过，无待生成 migration。
- `uv run pytest`：通过（3 passed）。
- `uv run ruff check .` 和 `uv run ruff format --check .`：通过。
- 启动 Uvicorn 后，`GET /health` 返回 `200 {"status":"ok"}`。

### 未解决问题

无阻塞问题。

## Phase 1 交付记录

### 用户与认证

- 新增 `users` 表，使用 BIGINT UNSIGNED AUTO_INCREMENT 主键和唯一 `phone_number`。
- 新增手机号格式校验和环境配置的测试验证码登录。
- 新增 JWT 签发与校验，Token 仅包含 `sub`、`iat` 和 `exp`。
- 新增 `get_current_user` Bearer Token Dependency。
- 测试登录由 `TEST_LOGIN_ENABLED` 控制，生产环境必须关闭该开关。

### API

- `POST /api/v1/auth/login`
- `GET /api/v1/users/me`
- `PATCH /api/v1/users/me`

用户资料接口只允许修改 `nickname`，不允许修改手机号。

所有接口使用统一响应结构：

- 成功响应：`success = true`，业务结果放在 `data`，`error = null`。
- 错误响应：`success = false`，`data = null`，错误信息放在 `error`，包含 `code`、`message` 和可选的 `details`。

### Migration 与验证

- 新增 migration：`f67d91555137`（`create users`）。
- 当前 Alembic revision：`f67d91555137 (head)`。
- `uv run alembic current`：通过，当前为 `f67d91555137 (head)`。
- `uv run alembic check`：通过，无待生成 migration。
- `uv run pytest`：通过（9 passed）。
- `uv run ruff check .` 和 `uv run ruff format --check .`：通过。

### 未解决问题

无阻塞问题。Farm、Plot、Production、FarmOperation 和 HarvestRecord 仍未开始实现，按计划等待后续 Phase 开发。

## Phase 2 交付记录

### 农场与成员

- 新增 `farms` 和 `farm_members` 表；创建农场与创建当前用户 OWNER 成员在同一事务内完成。
- `farm_code` 唯一；所有农场数据访问均校验当前用户的 FarmMember 权限。
- 实现 OWNER、ADMIN、MEMBER 的成员管理规则：OWNER 可管理所有角色，ADMIN 不能操作或设置 OWNER，MEMBER 不能管理成员；农场始终至少保留一位 OWNER。
- 暂不实现删除农场和加入农场申请流程。

### API

- `GET /api/v1/farms`
- `POST /api/v1/farms`
- `GET /api/v1/farms/{farmId}`
- `PATCH /api/v1/farms/{farmId}`
- `GET /api/v1/farms/{farmId}/members`
- `POST /api/v1/farms/{farmId}/members`
- `PATCH /api/v1/farms/{farmId}/members/{memberId}`
- `DELETE /api/v1/farms/{farmId}/members/{memberId}`
- `DELETE /api/v1/farms/{farmId}/members/me`

### Migration、前端与验证

- 新增 migration：`9c8d9c86e54a`（`create farms and farm_members`）。
- 小程序已接入 Farm API 和当前农场上下文，完成“我的农场”切换、创建农场、农场设置、基本信息编辑和成员管理流程；视觉细节优化留待后续处理。
- `uv run alembic check`：通过。
- `uv run pytest`：通过（15 passed）。
- `uv run ruff check .`：通过。
- `pnpm exec vue-tsc --noEmit -p tsconfig.json`：通过。
- `pnpm run build:mp-weixin`：通过；仅有 Sass 弃用警告。

### 未解决问题

本阶段无阻塞问题；农场删除与加入农场申请流程按 MVP 范围暂不实现。

## Phase 3 交付记录

### 地块与权限

- 新增 `plots` 表，支持地块名称、地块类型、面积原值、面积单位、标准平方米面积和可选边界 JSON。
- `PlotType` 支持大田、水田、大棚、果园、林地、鱼塘、栏舍和其他；`AreaUnit` 支持亩、平方米和公顷。
- `areaM2` 由后端根据 `areaValue` 和 `areaUnit` 计算；边界仅接受带 `coordinateSystem: "GCJ02"` 的 JSON，不覆盖用户填写的面积。
- 所有列表、详情和编辑接口均校验 FarmMember；OWNER/ADMIN 可创建和编辑地块，MEMBER 可查看地块。

### API 与 Migration

- `GET /api/v1/farms/{farmId}/plots`
- `POST /api/v1/farms/{farmId}/plots`
- `GET /api/v1/plots/{plotId}`
- `PATCH /api/v1/plots/{plotId}`
- 新增 migration：`6c41d1c6b6f1`（`create plots`）。
- 修复统一校验错误响应对 Pydantic 自定义校验详情的 JSON 序列化问题。

### 前端与验证

- 农场 Tab 已接入真实地块列表和数量统计。
- 新增创建地块、地块详情和编辑地块页面，复用地块表单组件；暂不加入地图绘制、Species、Production、农事或收获功能。
- 新增统一数字展示格式化工具，去除无意义的尾随 0，整数不显示小数部分；后续业务页面应复用该工具。
- `uv run alembic check`：通过。
- `uv run pytest`：通过（19 passed）。
- `uv run ruff check .`：通过。
- `pnpm exec vue-tsc --noEmit -p tsconfig.json`：通过。
- `pnpm run build:mp-weixin`：通过；仅有 Sass 弃用警告。

### 未解决问题

地图绘制暂不实现；地块删除接口暂不提供，待 Production、农事和收获记录关联规则确定后再设计删除或归档策略；Species、Production 及后续生产业务按计划留待后续 Phase。

## Phase 4 交付记录

### 种类与种养

- 新增 `species` 和 `productions` 表；Species 为系统预置数据，不提供管理接口。
- Alembic 数据 migration 初始化 23 个种类，覆盖农业、林业、牧业和渔业。
- Production 支持一个地块存在多条 ACTIVE 或历史记录；`Plot.type` 不与 `Species.industry` 强绑定。
- Species 维护固定个体单位；预置蔬菜／林木为株、猪牛羊为头、鸡鸭为羽、水产为尾。Production 只保存初始数量数值，不重复保存单位。
- 农业改为可选预计亩产（固定公斤／亩）和可选厘米株间距；林业不提供预计亩产且移栽／播种数量必填；牧业入栏日龄、入栏数量必填且无作业方式；渔业养殖数量、作业方式必填。
- 所有 FarmMember 均可创建、编辑和删除 ACTIVE Production；跨农场访问返回 404。开始日期不得晚于当前日期；各行业的必填和不适用字段由后端校验，固定个体单位的数量必须为整数。

### API 与前端

- `GET /api/v1/species`
- `GET /api/v1/plots/{plotId}/productions`
- `POST /api/v1/plots/{plotId}/productions`
- `GET /api/v1/productions/{productionId}`
- `PATCH /api/v1/productions/{productionId}`
- `DELETE /api/v1/productions/{productionId}`
- 新增 migrations：`1bf2b6d1b674`（`create species and productions`）、`093fa42fe3ad`（`refine production industry fields`）。
- 小程序新增独立种类搜索与行业筛选页、按行业变化的种养表单、创建／编辑／详情与删除流程；地块详情已展示当前和历史种养。创建流程先选择种类和选填品种，再进入只读展示种类的正式表单；返回时保留种类和品种、清空未提交表单。种植方式会动态切换时间与数量术语，单位自动由种类带出。

### 验证结果

- `uv run alembic check`：通过。
- `uv run pytest`：通过（24 passed）。
- `uv run ruff check .` 和 `uv run ruff format --check .`：通过。
- `pnpm exec vue-tsc --noEmit -p tsconfig.json`：通过。
- `pnpm run miniapp:build`：通过；仅有现有 Sass API 与 `@import` 弃用警告。

### 未解决问题

- Phase 4 尚无 FarmOperation、HarvestRecord 表，因此当前 ACTIVE Production 的关联记录限制将在 Phase 5、6 接入相应表后补齐：存在关联农事或收获时，不允许修改 `plotId`、`speciesId`、`startedOn` 或删除。
- 结束种养属于 Phase 7，当前不提供结束操作；历史列表已为该状态预留展示。

## 前端规划记录

- 已完成小程序页面架构和视觉主题基线，详见 [小程序页面架构与视觉基线](./07-miniapp-information-architecture.md)。
- 已确认 TabBar 为“首页 / 农场 / 我的”三个入口。
- 已确认地块详情是核心业务页面，成员管理从“我的 → 我的农场”进入。
- 删除农场、加入农场流程暂不属于 MVP 页面和接口范围。
- 已完成首批小程序基础壳层、登录、三 Tab 页面壳层、我的页面和昵称编辑页面；Phase 2 已接入 Farm 管理，Phase 3 已接入 Plot 列表和地块管理。
- 后续按 Phase 4～9 和本文档顺序推进。

## 小程序首批实现记录

- 使用微信小程序原生 `tabBar`，复用 `apps/miniapp/src/static/tabbar/` 中的 81×81 图标。
- 已配置首页、农场、我的三个 Tab，三个 Tab 使用自定义头部，并处理微信状态栏和右上角胶囊按钮空间；当前农场和地块数据暂不伪造。
- 已接入 `POST /api/v1/auth/login`、`GET /api/v1/users/me` 和 `PATCH /api/v1/users/me`。
- 已完成登录页、首页工作台壳层、农场生产现场壳层、我的页面和个人资料编辑页。
- 登录页在发送验证码前阻止登录；验证码获取后若修改手机号，需要重新获取。
- 已接入 uv-ui 全局基础样式和掌上农场主题色；补充 `sass` 开发依赖以支持 SCSS 构建。
- 根目录已提供 `pnpm miniapp:dev` 和 `pnpm miniapp:build` 微信小程序命令。
- `vue-tsc --noEmit -p apps/miniapp/tsconfig.json`：通过。
- `pnpm run miniapp:build`：通过；仅有 uv-ui 旧版 Sass API 的弃用警告。
- 首批实现阶段未提前实现 Farm、Plot、Production、FarmOperation 或 HarvestRecord 业务页面；后续页面按 Phase 逐步接入。
