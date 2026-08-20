# MVP 开发进度

本文档记录“掌上农场”MVP 的实际开发状态。`05-development-plan.md` 是计划基线；本文件只记录已完成的工作、当前阶段和验证结果。

## 维护规则

- 每个 Phase 完成并完成验证后，更新对应阶段的状态、完成日期和交付内容。
- 记录实际新增的 API、Alembic migration、测试结果和未解决问题。
- 只记录已完成且已验证的内容；未开始的阶段不提前标记完成。
- 开始下一阶段前，以“当前阶段”一节为准确认开发范围。

## 当前阶段

**Phase 7：结束种养已完成。**

下一阶段为 **Phase 8：地块完整详情**。尚未开始。

## 阶段状态

| Phase | 内容 | 状态 | 完成日期 |
| --- | --- | --- | --- |
| 0 | 工程初始化 | 已完成 | 2026-08-17 |
| 1 | Auth + User | 已完成 | 2026-08-17 |
| 2 | Farm + FarmMember | 已完成 | 2026-08-18 |
| 3 | Plot | 已完成 | 2026-08-18 |
| 4 | Species + Production | 已完成 | 2026-08-19 |
| 5 | FarmOperation | 已完成 | 2026-08-19 |
| 6 | HarvestRecord | 已完成 | 2026-08-20 |
| 7 | 结束种养 | 已完成 | 2026-08-20 |
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

## Phase 5 交付记录

### 农事

- 新增 `farm_operations` 与 `operation_types` 表：预置施肥、翻耕、起垄、用药、灌溉、除草、修剪、喂料、消毒、清粪、配种、投料、换水、清塘和测水温等 MVP 基础农事类型；类型以数据表维护，`ACTIVE` / `DISABLED` 状态支持下架，历史记录仍保留关联类型。
- FarmOperation 归属于 Plot，`production_id` 在创建请求中必传但允许为 `null`；非空时后端校验 Production 属于同一 Plot 且仍为 ACTIVE。
- `operator_id` 默认当前用户，也可指定同一 Farm 的其他有效成员；`created_by` 始终由 JWT 当前用户写入，编辑不会修改记录人或创建时间。
- `operated_at` 接受带时区 ISO 8601 时间，转换为 UTC 保存；关联 Production 的农事不得早于其开始日期，所有农事均不得晚于当前时间。
- 已接入 Production 与农事的关联限制：存在关联农事后，不允许修改 Production 的 `plotId`、`speciesId`、`startedOn` 或删除。HarvestRecord 的对应限制留待 Phase 6 接入。

### API 与 Migration

- `GET /api/v1/plots/{plotId}/operations`
- `POST /api/v1/plots/{plotId}/operations`
- `PATCH /api/v1/operations/{operationId}`
- `DELETE /api/v1/operations/{operationId}`
- `GET /api/v1/operation-types`
- 新增 migration：`2c972e3fc98e`（`create farm operations`）及 `54698bd6b5f1`（`manage operation types`）。

### 小程序

- 新增 FarmOperation API Service、农事记录列表页和创建／编辑表单页；地块详情提供“记农事”和“查看记录”入口，首页“记农事”直接进入同一表单。
- 农事类型改为独立平铺选择页，只显示后端返回的 ACTIVE 类型；表单默认人工、当前时间和当前用户，操作人可选择当前 Farm 成员。
- 创建农事时，地块是表单首个必填项：首页进入时先在表单内选择；从地块详情或农事列表进入时自动带入，但仍可重选当前农场内的地块。编辑既有农事时地块保持锁定。
- 种养关联默认整个地块，改用批次卡片选择；卡片展示种类、品种、开始日期和初始数量，避免同种类批次难以分辨。请求始终提交 `productionId`，包括显式 `null`。
- 已支持编辑、删除 ACTIVE Production 关联的农事；关联已结束种养的记录展示锁定状态，前端不提供编辑和删除入口。
- 农事列表保持为独立页面，未提前实现 Phase 8 的地块详情三栏聚合布局。
- 首页已接入当前农场的地块数、进行中种养和最近农事；全部通过现有按地块接口聚合，不新增收获、结束种养或新的后端 API。快捷入口支持先选地块后开始种养，并直接进入农事表单选择地块；收获入口明确提示等待 Phase 6。

### 验证结果

- `uv run alembic check`：通过。
- `uv run pytest`：通过（29 passed）。
- `uv run ruff check .`：通过。
- `pnpm exec vue-tsc --noEmit -p apps/miniapp/tsconfig.json`：通过。
- `pnpm run miniapp:build`：通过；仅有现有 Sass API 与 `@import` 弃用警告。

### 未解决问题

- HarvestRecord 与结束种养仍未开始，按 Phase 6、7 顺序推进。

## Phase 6 交付记录

### 收获记录

- 新增 `harvest_records` 表；每条记录必须关联具体 Production，不重复保存 `plot_id`。一次 Production 可以存在多条收获记录，创建收获不会改变 Production 状态。
- 支持农业／林业采收、渔业捕捞和牧业出栏的统一数据模型；单位由后端根据行业和 Species 自动派生，农业、渔业固定为 `KG`，林业、牧业使用 Species 个体单位。单位创建后作为历史快照且不可编辑；个体单位必须为整数，公斤允许小数。
- `operator_id` 默认当前用户，也可指定或改选同一 Farm 的其他有效成员；`created_by` 始终由 JWT 当前用户写入，编辑保持原始记录人和创建时间。
- `harvested_at` 接受带时区 ISO 8601 时间并转换为 UTC 保存，不得早于 Production 开始日期或晚于当前时间；未传时默认当前时间。
- 仅 ACTIVE Production 允许新增、编辑和删除收获记录；ENDED Production 的既有记录仍可查看，但不可变更。
- 已补齐 Production 纠错限制：存在收获记录后，不允许修改 `plotId`、`speciesId`、`startedOn`，也不允许删除该 Production。

### API 与 Migration

- `GET /api/v1/productions/{productionId}/harvests`
- `POST /api/v1/productions/{productionId}/harvests`
- `GET /api/v1/plots/{plotId}/harvests`
- `PATCH /api/v1/harvests/{harvestId}`
- `DELETE /api/v1/harvests/{harvestId}`
- 新增 migration：`b8e4d2a1c673`（`create harvest records`）。

### 小程序

- 新增 HarvestRecord API Service、完整收获表单、种养选择页，以及按 Production 和按 Plot 查看收获记录的列表页；ACTIVE Production 的记录支持编辑和删除，ENDED Production 的历史记录展示锁定状态。
- 页面按行业使用自然术语和数量字段：农业为“采收重量”、渔业为“捕捞重量”、林业为“采收数量”、牧业为“出栏数量”。表单不提供单位选择器，只展示自动确定的固定单位；个体单位在提交前校验整数，所有数量展示统一去除无意义的尾随 0。
- 首页和地块入口直接进入完整表单，种养是表单首个必填项；选择页以地块、种类、品种、开始日期和初始数量区分具体种养。从种养详情进入时自动带入该次种养，编辑既有记录时种养归属锁定。
- 种养详情新增行业化的记录与查看入口；地块详情新增收获汇总入口，并在每条 ACTIVE 种养卡片上提供对应的“采收／捕捞／出栏”操作。
- 首页“收获”快捷入口已开放，最近动态统一聚合农事和收获记录，收获动态点击后进入对应 Production 的收获列表。
- 收获表单默认当前时间、人工、当前用户和种类名称；允许选择当前 Farm 其他成员作为操作人，产品名称、等级和备注选填。

### 验证结果

- `uv run alembic check`：通过。
- `uv run pytest`：通过（34 passed）。
- `uv run ruff check .` 和 `uv run ruff format --check .`：通过。
- `pnpm exec vue-tsc --noEmit -p apps/miniapp/tsconfig.json`：通过。
- `pnpm run miniapp:build`：通过；仅有现有 Sass API 与 `@import` 弃用警告。

### 未解决问题

- Phase 7 结束种养已在后续阶段完成，详见下一节。

## Phase 7 交付记录

### 结束种养

- 新增 `POST /api/v1/productions/{productionId}/end`，请求可传 `endedOn`，省略时默认业务时区 `Asia/Shanghai` 的当天。
- 仅 ACTIVE 种养可结束；重复结束返回 `409 BUSINESS_CONFLICT`，无成员权限的资源访问继续返回 `404`。
- `endedOn` 不得晚于当天、早于开始日期，或早于关联农事、收获记录的业务日期；结束时更新既有 Production 的 `status = ENDED` 与 `ended_on`，不新增 EndRecord 表或 migration。
- 结束后的 Production 不可编辑或删除；其关联 FarmOperation、HarvestRecord 保持可查但均不可新建、编辑或删除。关联种养的农事创建、编辑与结束操作使用同一 Production 行锁，避免结束与记录变更交错提交。

### 小程序

- 种养详情的 ACTIVE 状态新增“结束种植／结束养殖”入口；已结束状态不展示该入口，原有编辑、记录收获与删除入口继续遵循锁定规则。
- 新增独立的“结束种养”页面，使用原生导航栏，展示种类、地块和结束日期；日期默认当天，并限制在开始日期至当天之间。用户二次确认后提交，返回详情时刷新为已结束状态。
- 页面延用品牌绿、现有 Token、轻量信息卡和克制阴影，不新增说明性内容或额外表单字段。

### 验证结果

- `uv run alembic current`：通过，当前为 `b8e4d2a1c673 (head)`。
- `uv run alembic check`：通过，无待生成 migration。
- `uv run pytest`：通过（35 passed）。
- `uv run ruff check .` 与 `uv run ruff format --check .`：通过。
- `pnpm --dir apps/miniapp exec vue-tsc --noEmit -p tsconfig.json`：通过。
- `pnpm --dir apps/miniapp run build:mp-weixin`：通过；仅有现有 Sass API 与 `@import` 弃用警告。

### 未解决问题

无阻塞问题；Phase 8 按计划等待确认后开始。

## 前端规划记录

- 已完成小程序页面架构和视觉主题基线，详见 [小程序页面架构与视觉基线](./07-miniapp-information-architecture.md)。
- 已确认 TabBar 为“首页 / 农场 / 我的”三个入口。
- Phase 6 完成后已重构三个 Tab 的信息架构与视觉基线：首页调整为四个全局生产入口、当前农场简要状态和最近动态，不再罗列当前种养；农场 Tab 调整为总面积、地块数、进行中种养、闲置地块及当前种养总览；新增独立地块列表页；“我的”补齐页面身份头部并重排账户和农场信息。
- “开始种养”流程已统一：首页和地块详情都直接进入种类选择页，正式表单新增地块必填项和品种选填项；从地块详情进入默认带入地块，从首页进入则在表单内选择。已删除额外的开始种养中间页，并将地块管理与表单选地块收敛到同一个 `pages/plots/index` 页面，不再维护独立 `plots/select`。
- 导航栏已统一：三个 Tab 的自定义头部改为固定定位并保留等高占位，滚动时不移动；其余二级页面全部改用微信原生导航栏，移除了页面内重复头部。编辑农场、编辑地块、创建／编辑种养使用原生离开确认保护未保存内容。
- 视觉系统已收敛为原始色阶、语义色与组件尺寸三层 Token；农事与收获的按钮、选择和焦点统一使用品牌绿，黄色只保留给真实警告状态。页面统一采用 4 px 间距网格，以留白和分隔线组织层级，减少说明性副文案、无目的嵌套卡片和阴影。
- 地块详情已按“概览、快捷操作、当前／历史种养、生产记录”重排：基础信息合并为单张概览卡，开始种养、记农事、记收获集中展示，农事与收获查看入口合并为生产记录；种养行补充品种、开始日期和初始数量以区分同种类批次。地块列表同步精简工具栏和创建按钮，保留同一页面的管理／选择双模式，并明确面积缺失与选中状态。
- “我的”页已简化为身份栏与农场入口：移除账户说明、关于和退出登录，使用设置图标进入新的原生导航设置页。设置页提供昵称编辑、只读脱敏手机号、关于入口和带二次确认的退出登录；暂不展示没有业务闭环的注销账号入口。
- 首页和农场 Tab 的固定头部已统一只显示当前农场名称，由 TabBar 表达页面身份；首页问候区移除“今天准备做点什么”等解释性提示，只保留日期和用户问候。
- AIDesigner 仅用于本地视觉方案生成和预览，生成物保存在忽略提交的 `.aidesigner/` 目录，访问凭据不写入仓库；根工作区保留 Puppeteer 作为本地设计预览依赖。
- 已确认地块详情是核心业务页面，成员管理从“我的 → 我的农场”进入。
- 删除农场、加入农场流程暂不属于 MVP 页面和接口范围。
- 已完成首批小程序基础壳层、登录、三 Tab 页面壳层、我的页面和昵称编辑页面；Phase 2 已接入 Farm 管理，Phase 3 已接入 Plot 列表和地块管理。
- 三个 Tab 与首批核心二级页已统一到同一套 Token、导航和页面层级；Phase 7 的结束种养页已沿用该基线，后续新页面继续沿用。

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
