# AI Tab MVP 技术设计

> 状态：A0、A1、A2、A2.5 已完成。本文记录已实现的只读设计；模型使用 DeepSeek 官方 API 的 `deepseek-v4-flash`，调用细节仍限制在后端模块内。

## 1. A1 技术栈决策

### 结论

A1 **不引入 LangChain 或 LangGraph**。后端直接使用 DeepSeek 的 OpenAI 兼容接口，并在项目内实现一个边界明确的工具调用循环。

| 层次 | A1 方案 | 说明 |
| --- | --- | --- |
| 模型客户端 | Python `openai` SDK 的 `AsyncOpenAI` | 通过 `base_url=https://api.deepseek.com` 调用 `deepseek-v4-flash`；SDK 仅作为兼容协议客户端，不代表调用 OpenAI 模型。 |
| 对话编排 | 项目内轻量工具循环 | 发送消息 → 接收工具调用 → 校验参数 → 调用受限只读工具 → 回传结果；单轮最多 6 次工具调用。 |
| 工具参数与响应 | Pydantic Schema | 工具定义、参数校验和 API 响应均显式建模，禁止模型直接触碰数据库。 |
| 领域数据访问 | 复用现有 Service | 工具只调用已有的农场领域 Service，并保留 FarmMember 权限检查。 |
| 测试替身 | 可注入的 AI Client Fake | 单元测试不请求 DeepSeek；覆盖工具选择、参数错误、超限和上游失败。 |

不为此建立通用 Agent 框架、Provider 抽象、向量数据库或任务队列。模型供应商固定、工具数量有限时，这些抽象没有实际收益。

### 为什么 A1 不使用 LangChain / LangGraph

- LangChain 的集成生态适合需要同时组合大量模型、检索器和外部连接器的场景；A1 只有一个固定模型和少量内部只读工具。
- LangGraph 的重点是长运行、有状态、可持久化、可人工介入的 Agent 工作流；持久化聊天窗口只需普通的数据表和按轮读取，不需要工作流断点恢复或 Agent 状态机。
- 直接循环能把权限、脱敏、配额、工具白名单和错误处理放在可审计的业务代码中，符合当前项目保持简单、不要过早抽象的原则。

这些框架并不能替代本项目必须自行实施的农场成员鉴权、Farm AI 开关、数据告知、工具参数校验和每日配额。

### 未来重新评估的触发条件

以下需求真正出现且采用手工状态机明显变复杂时，再评估 LangGraph；不是提前引入的理由。

1. 一个 AI 操作需要跨多次请求恢复，且有可靠的草稿、审批、重试和断点续跑需求。
2. 出现多个有依赖关系的长耗时步骤，或需要并行的 Agent / 工具编排。
3. 已验证的写入操作扩展到多个领域，纯业务状态表和显式状态机不再能清晰表达流程。

即使进入“创建地块”的二次确认写入试点，也应先使用普通的草稿记录和显式确认接口；单一的准备 / 确认流程本身不足以引入 LangGraph。

## 2. 设计原则

- 后端承担模型调用、工具编排、权限验证、限流和错误收敛；小程序只发送用户问题并展示结构化结果。
- 复用现有 Service 的业务读取能力。AI 模块不得用 HTTP 回调本应用 API，也不得复制业务规则。
- 工具设计按业务意图而非 REST URL 组织，输入和输出均为最小的明确 Pydantic Schema。
- 会话与消息使用明确的 AI 专用数据表持久化；不保存模型原始响应、完整工具结果或工具调用参数。农场业务表仍不因 AI 对话发生写入。
- 不为未来多模型、多 Agent 或工作流平台预建通用抽象。用一个小型 `ai_client` 模块封装 DeepSeek 调用细节即可。

## 3. 请求链路

```text
pages/mine/index.vue → pages/ai/conversations.vue
  → GET /api/v1/ai/conversations → 打开／删除历史窗口
pages/ai/index.vue
  → 首次发送：POST /api/v1/ai/conversations
  → POST /api/v1/ai/turn
    → get_current_user + 会话所属 farm 的 FarmMember 校验
      → AI Turn Service
        → 模型请求 / 受控工具循环
          → 既有 Farm、Plot、Production、Operation、Harvest、Species Service
        → 回答与对象引用，并持久化本轮消息
  → 原生消息与对象入口渲染
```

模型供应商只能由 API 服务端访问。`ai_client` 使用 DeepSeek 官方 API、`https://api.deepseek.com` 与模型名 `deepseek-v4-flash`；小程序仅请求本项目已经配置的 API 域名，绝不接触供应商密钥或供应商 API。首版使用其 OpenAI 兼容的函数工具调用格式。

## 4. AI API 合约（提案）

### 4.1 请求

```http
POST /api/v1/ai/turn
Authorization: Bearer <current-user-jwt>
```

```json
{
  "conversationId": 12,
  "message": "1号大棚现在种了什么？"
}
```

- `conversationId` 必填、正整数；会话绑定创建者和农场，服务端每次检查创建者仍是该农场的 FarmMember。
- `message` 必填，去除首尾空白后限制长度。
- 历史上下文由服务端读取该窗口最近 8 轮；客户端不能提交或覆盖历史消息。
- 系统提示词、工具定义和工具结果由服务端生成，客户端不能传入。

具体字符与轮次上限在供应商预算确认时落入 Settings；建议首版保留最近 8 轮，且以服务器端上限为准。

### 4.3 会话管理接口

- `POST /api/v1/ai/conversations`：接收正整数 `farmId`，确认当前用户仍是该农场成员后创建空窗口，返回窗口 ID、农场名称、标题和时间；首次发送前才调用。
- `GET /api/v1/ai/conversations?page=&pageSize=`：返回当前用户在所有仍拥有 FarmMember 权限的农场中的窗口，按最近更新时间倒序分页。默认每页 20 条，最大 100 条。
- `GET /api/v1/ai/conversations/{conversationId}/messages?page=&pageSize=`：读取当前用户有权访问窗口的消息，按消息顺序返回。默认每页 50 条，最大 100 条。
- `DELETE /api/v1/ai/conversations/{conversationId}`：仅删除当前用户仍有 FarmMember 权限的自己的窗口，返回 `204`；关联消息随窗口删除。

会话列表、消息读取和删除均不能以客户端传入的农场 ID 绕过会话所属农场和 FarmMember 校验。

### 4.2 响应

```json
{
  "answer": "1号大棚当前有 2 批进行中的种养：黄瓜、生菜。",
  "references": [
    {
      "kind": "PLOT",
      "id": 31,
      "label": "1号大棚",
      "route": "/pages/plots/detail?plotId=31"
    }
  ],
  "needsSelection": false,
  "candidates": []
}
```

- `answer` 是纯文本，前端不得将其作为 HTML 执行。
- `references` 是服务端从实际工具结果构造的允许跳转对象，模型不能自行指定 route 或 ID。
- `needsSelection=true` 时，`candidates` 由服务端构造为同农场、用户可访问的候选项；用户选择后前端以明确 ID 发送下一轮问题。
- 模型不能直接生成 API 响应结构；AI Turn Service 必须在输出前校验并补充这些字段。

## 5. 工具白名单

初版工具均是只读且默认绑定一个已校验的 `farm_id`：

| 工具意图 | 可复用数据能力 | 结果上限 |
| --- | --- | --- |
| 查地块 | 农场地块摘要、名称匹配 | 20 条 |
| 读地块详情 | 地块聚合详情 | 1 个地块 |
| 查种养 | 农场级种养记录、状态/行业/种类筛选 | 20 条 |
| 查农事 | 农场级农事记录、类型筛选 | 20 条 |
| 查收获 | 农场级收获记录、行业/种类筛选 | 20 条 |
| 查最近动态 | 农场活动流 | 20 条 |
| 查种类/农事类型 | 系统只读选项 | 20 条 |

工具输入不接受任意 SQL、URL、字段名、分页大小或 Farm ID 覆盖。名称查询必须先返回候选项，只有唯一匹配或用户明确选择的 ID 才能读取详情。

模型每轮最多执行有限次数工具调用；超过次数时停止并要求用户缩小问题范围。每个工具响应只返回回答所需字段，不返回完整模型对象、手机号或审计字段。

## 6. 权限与数据流

1. Router 使用现有 `get_current_user`。
2. AI Turn Service 先确认会话创建者仍是其绑定农场的 FarmMember，再检查 `Farm.ai_enabled`。
3. 所有工具调用均向既有 Service 显式传入该 `user_id` 和 `farm_id`／资源 ID。
4. Service 原有的 FarmMember、资源所属关系和状态校验继续生效。
5. 会话列表、消息读取和删除同样检查会话创建者与当前 FarmMember；成员退出或被移出时同步删除该用户在此农场的会话。
6. 经最小化后的工具结果才可以作为模型上下文；回答与引用再次通过 Schema 校验后返回。

因此模型即使给出错误 ID、尝试跨农场查询或产生提示注入内容，也无法扩大当前用户权限。

调用 DeepSeek 时，使用服务端生成的非个人信息 `user_id` 标识，例如以服务端密钥计算的稳定 HMAC 值；不得传入手机号、昵称或本项目的原始用户 ID。该标识仅用于供应商侧的安全、缓存和调度隔离。

## 7. 农场级 AI 开关

- 在 `farms` 表新增非空布尔字段 `ai_enabled`，新的和历史农场均默认 `true`；使用新的 Alembic migration。
- `FarmResponse` 新增 `aiEnabled`，OWNER 通过现有农场编辑权限将其切换为开／关；ADMIN、MEMBER 没有切换权限。
- AI Turn Service 在任意模型请求与工具调用之前检查该值。关闭时返回稳定业务错误码 `AI_NOT_ENABLED`，且绝不向 DeepSeek 发送用户输入。
- AI Tab 在关闭状态只展示简洁状态和 OWNER 设置入口；不得因为前端隐藏而省略后端检查。

## 8. 失败、限流与可观测性

- API 为模型超时、供应商不可用、限额耗尽和工具异常定义稳定的应用错误码；前端展示统一重试状态。
- 服务端设置连接、读取和总请求超时，并在客户端取消或页面离开时停止等待。
- MVP 至少记录请求关联 ID、用户 ID、农场 ID、模型配置标识、工具名、耗时、成功／失败与用量；默认不记录完整消息正文和完整工具结果。
- 以用户 ID 为维度实施服务端限流与日配额。限流数据可以先使用数据库／进程内的简单实现，具体实现与部署形态一并确认；不因为 AI 提前引入 Redis、MQ 或 Celery。
- 已确认只读 MVP 配额：每用户每天 20 次；单次问题最多 1,000 个字符；服务端至多接受最近 8 轮对话历史。超额时返回稳定错误码并提示次日再试。

## 9. 小程序设计

- 在原生 `tabBar` 中增加第四项 `pages/ai/index` 及两张本地 PNG 图标。
- 页面复用 `.pf-page`、`.pf-page-content`、设计 token 与现有 HTTP 认证机制。
- 消息列表使用页面滚动或 `scroll-view`，输入区作为独立同级区域；新消息完成后滚动到末尾，但用户上滑查看历史时不强制拉回底部。
- 初始对话在推荐问题上方显示低权重的“目前仅支持查询 · 新建和记录请使用原有功能”，首条消息出现后隐藏；它不是卡片、弹窗或写入入口。
- 发送期间禁用重复发送和输入栏的“＋”新对话按钮，显示等待状态；不在首版实现取消或分块流式渲染。
- 候选项、对象引用和未来的确认草稿均为原生可点击行／按钮，不嵌在 AI 输出的富文本内。
- 在首次模型请求前显示页面内数据告知确认层，以用户 ID 加告知版本作为本地确认键；未确认时不请求后端 AI 接口。
- 新对话入口放在 AI Tab 输入栏的发送按钮旁；AI 页顶部不放会话操作。会话管理入口放在“我的 → AI 对话”。切换农场时不混用窗口；打开其他农场的历史窗口时先切换服务端当前农场。

## 10. 写入试点的扩展点（不实现）

写入阶段新增的不是“可写工具”，而是 `prepare_create_plot`：它只生成并校验草稿。用户确认后由独立的确认 API 调用既有 `create_plot` Service。

届时新增 `ai_pending_actions` 与 `ai_action_audits` 表或等价的明确持久化模型，分别保存短时效待确认参数与不可变执行审计。两者均使用新的 Alembic migration；操作执行时以当前 JWT 和角色再次授权。

完整流程、幂等与测试边界见《[AI 写入操作设计记录](./03-ai-write-action-design.md)》。该记录不构成 A4 的实现授权。
