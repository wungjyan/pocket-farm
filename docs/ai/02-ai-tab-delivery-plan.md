# AI Tab MVP 交付计划

> 状态：A0、A1、A2、A2.5 已完成；A3 需确认后开始。每个阶段完成后必须运行验证并停止，等待确认后再进入下一阶段。

## 1. 交付顺序

| 阶段 | 目标 | 是否写业务数据 |
| --- | --- | --- |
| A0 | 上线前决策与运行基线 | 否 |
| A1 | 后端只读 AI 编排 | 否，运行配额表除外 |
| A2 | 原生 AI Tab 对话页 | 否 |
| A2.5 | 持久化会话与对话管理 | 仅 AI 会话／消息表 |
| A3 | 联调、真机验证与试用 | 否 |
| A4 | 创建地块确认式写入试点 | 是，后续独立确认 |

只有 A0 至 A3 完成并确认后，才可以评审 A4。A4 不属于只读 MVP 的承诺范围。

## 2. A0：决策与运行基线

### 目标

在写代码前完成 DeepSeek 接入准备、数据告知与调用配额的落地设计，并补齐可复现运行说明。

### 工作项

- 已确认模型为 DeepSeek 官方 API 的 `deepseek-v4-flash`；确认 API 账号、可用地域与费用归属。
- 落实规格第 6 节的数据告知版本、弹窗文案、最小化字段与日志保留策略。
- 落实已确认的每日 20 次配额、1,000 字输入和 8 轮上下文限制，以及超额行为。
- 落实所有农场默认开放、OWNER 可关闭本农场 AI 的权限与交互口径。
- 为 API 增加不含真实密钥的 AI 环境变量样例；真实密钥仅放部署环境。
- 统一并更新本地启动文档。当前技术文档提到根目录 `README.md` 与 `docker-compose.yml`，仓库现状没有这两个文件，应先确认采用的 MySQL 启动方式并让文档与仓库一致。

### 验收

- 上述决策有记录且可供研发、测试使用。
- 新成员可根据仓库文档启动 API、数据库和小程序。
- 不提交模型密钥、访问令牌或真实对话数据。

### 当前配置基线（2026-09-02）

- 已确认使用 DeepSeek 官方 API 的 `deepseek-v4-flash`，并在 API Settings 与 `.env.example` 预留模型、超时、配额、上下文、工具调用上限、告知版本和用户隔离哈希密钥。
- `DEEPSEEK_API_KEY` 与 `AI_USER_ID_HASH_KEY` 为可选的服务端密钥：未配置时现有业务 API 仍能启动，未来 AI 接口在调用时拒绝请求。
- 仓库新增根目录运行说明，保留手动 Docker 启动 MySQL 的方式，不新增 Docker Compose。
- 公网 API 地址、HTTPS、微信请求域名白名单与实际 DeepSeek Key 均在部署／联调阶段配置，本地开发暂不预设。

## 3. A1：后端只读 AI 编排

### 目标

提供单个、受 JWT 保护的 AI 对话接口和最小工具白名单，不添加写入能力。

### 工作项

- 新增 AI Router、Request/Response Schema、AI Turn Service 和供应商调用模块；Router 只处理 HTTP，工具编排放在 Service。
- 新增 `Farm.ai_enabled`、对应 Schema／Service 更新和 Alembic migration；OWNER 能切换，所有农场默认开启。
- 增加当前农场预校验、输入与历史上下文上限、超时、稳定错误码、用户限流和调用日志。
- 用现有业务 Service 实现规格定义的只读工具；不从 AI 模块直接操作 ORM 或调用内部 HTTP。
- 在模型工具循环中限制工具数量、结果条数与字段；同名资源返回候选项而非猜测。
- 为模型客户端使用可控的 fake／stub，测试不依赖真实模型服务或真实密钥。

### 验收与测试

- 无 Token、无当前农场、非成员、农场 AI 已关闭、错误资源 ID、超额输入与模型超时均得到安全的预期错误。
- S1 至 S3 可由固定模型输出和固定工具结果覆盖。
- 验证同名地块、跨农场 ID、工具结果为空、工具调用超限与上游错误。
- 验证 AI 请求不产生 Farm、Plot、Production、FarmOperation 或 HarvestRecord 的写入。
- 运行 `uv run pytest`、`uv run ruff check .`、`uv run alembic check`。

### 完成记录（2026-09-02）

- 已新增 `POST /api/v1/ai/turn`、受控 DeepSeek 客户端、工具循环和 Pydantic 请求／响应 Schema；模型只能通过只读工具读取最小必要字段。
- 已新增 `farms.ai_enabled` 与 OWNER 可更新的 `aiEnabled`；所有已有和新建农场默认开启。
- 已新增不保存正文的 `ai_daily_turn_usages` 运行配额表；按用户和本地日期记录请求次数。历史 migration 的双 head 已通过新的 merge migration 收束。
- 已覆盖成员隔离、农场开关、候选选择、跨当前农场资源 ID、输入限制、配额、超时与工具上限；AI 测试使用 Fake Client，不请求真实 DeepSeek。
- 已验证：`uv run pytest`（67 passed）、`uv run ruff check .`、`uv run alembic check`。

## 4. A2：原生 AI Tab 对话页

### 目标

以现有 uni-app 技术栈交付非流式、原生的 AI 对话体验。

### 工作项

- 在 `pages.json` 注册 `pages/ai/index`，在原生 `tabBar` 增加第四项和成对图标资源。
- 新增 AI Service，复用现有 JWT 请求机制；不要修改现有业务接口的调用方式。
- 实现首次数据告知、消息列表、输入、发送中、失败重试、无当前农场、农场 AI 已关闭和候选项／对象引用跳转。
- 内存保存当前页面的会话；切换农场时清空，避免混用上下文。
- 仅渲染纯文本与原生结构化卡片；不引入 H5、Markdown HTML 渲染、SSE 或第三方聊天 UI 框架。

### 验收

- AI 作为第四个 Tab 可访问，并与现有首页、农场、我的 Tab 正常切换。
- 当前农场名称与实际查询范围一致；切换后不会显示旧农场的消息或引用。
- 网络、超时、401、限额和空结果状态清晰，401 沿用现有登录跳转行为。
- 前端业务数值继续使用 `formatNumber`，样式仅使用既有 design token。
- 运行 `pnpm exec vue-tsc --noEmit -p apps/miniapp/tsconfig.json` 与 `pnpm run miniapp:build`。

### 完成记录（2026-09-02）

- 已在既有 `pages/ai/index` 原生 Tab 页面实现消息流、输入、发送中、失败重试、候选选择和对象引用跳转；不使用 H5、Markdown HTML、SSE 或第三方聊天 UI。
- 页面使用与首页、农场 Tab 相同的 `PfPageHeader` Tab 变体，统一显示当前农场名称和小程序胶囊区域。
- 首次发送前使用本地“用户 ID + 告知版本”键展示并保存数据告知确认；确认层在页面内渲染，拒绝时不请求 AI API。
- 切换当前农场会清空当前页面展示，并取消旧请求结果对新农场页面的影响；不存在未隔离的本地聊天缓存。
- 已补齐前端 AI Service 与 `Farm.aiEnabled` 类型；后端对象引用参数已修正为既有详情页实际使用的 `plotId`、`productionId`、`operationId`、`harvestId`。
- 已验证：`pnpm exec vue-tsc --noEmit -p tsconfig.json`、`pnpm run build:mp-weixin`、`uv run pytest`（67 passed）、`uv run ruff check .`、`uv run alembic check`。

## 5. A2.5：持久化会话与对话管理

### 完成记录（2026-09-02）

- 新增 `ai_conversations`、`ai_messages` 和 Alembic migration。会话按用户与农场绑定，消息只保存用户／助手纯文本和已校验的对象引用／候选项；不保存 JWT、模型原始响应、工具参数或完整工具结果。
- `POST /api/v1/ai/turn` 改为只接收 `conversationId` 与新消息，服务端读取该窗口最近 8 轮上下文。已补充新建、列表、消息读取和删除窗口接口。
- 用户可在小程序创建新窗口、恢复历史窗口、查看并删除自己当前仍有 FarmMember 权限的全部窗口。被移出或主动退出农场时，在同一事务物理删除该用户在该农场的会话和消息。
- 已覆盖会话消息持久化、用户删除和成员移除清理的后端测试。
- AI Tab 顶部不再提供会话操作；新窗口入口收敛到输入栏发送按钮旁的“＋”。会话管理入口收敛到“我的 → AI 对话”。
- 初始对话在推荐问题上方提示“目前仅支持查询 · 新建和记录请使用原有功能”；首条消息出现后隐藏，不增加写入入口。
- 已验证：`uv run pytest`（73 passed）、`uv run ruff check .`、`uv run alembic check`、`pnpm exec vue-tsc --noEmit -p tsconfig.json`、`pnpm run build:mp-weixin`。

## 6. A3：联调、真机验证与试用

### 目标

验证模型输出不破坏业务边界，且微信小程序真实运行环境可用。

### 工作项

- 使用测试农场覆盖农业、林业、牧业、渔业、空闲地块、同地块多条 ACTIVE Production、重复名称地块和无记录场景。
- 使用两个隔离农场账号验证无法跨农场读取。
- 在微信开发者工具及至少一台真机验证登录、请求域名、超时、返回、Tab 切换和页面恢复。
- 记录匿名化的失败类型、工具调用成功率、平均延迟、人工重试率与配额消耗；不收集超出已确认范围的聊天正文。

### 验收

- 规格第 4 节场景与第 7 节成功标准全部通过。
- 未发现跨农场泄露、业务表意外写入、密钥泄露或不可恢复的重复请求。
- 试用结论明确：继续优化只读能力、进入 A4，或停止／调整产品方向。

## 7. A4：创建地块确认式写入试点（后续）

本阶段必须在独立规格确认后才可开始。设计记录见《[AI 写入操作设计记录](./03-ai-write-action-design.md)》。最低工作项：

- 新建待确认操作与执行审计的数据库模型、Schema、Service、Router 和 Alembic migration。
- 模型仅生成 `prepare_create_plot` 草稿；前端原生确认卡展示名称、类型、面积、单位与当前农场。
- 确认接口使用一次性操作 ID、过期时间和幂等键；执行前再次校验当前用户、FarmMember 角色、当前农场和 `CreatePlotRequest`。
- 覆盖 OWNER、ADMIN、MEMBER、过期草稿、二次确认、重复确认、切换农场和模型补问等测试。

## 8. 实施规则

- 每个阶段开始前复读本计划、AI 规格、技术设计及相关 MVP 文档。
- 任何新增持久化数据必须使用 Alembic migration；禁止改写历史 migration。
- 不因 AI 提前引入微服务、Redis、MQ、Celery、向量数据库或通用 Agent 框架。
- 每阶段完成后更新计划状态与验证结果，执行测试并停止等待确认。
