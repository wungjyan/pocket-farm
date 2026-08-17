# MVP 开发计划

开发必须按 Phase 推进。

不要一次实现全部系统。

每个 Phase 完成后：

编译 / 启动
→
执行测试
→
检查 migration
→
总结 API
→
总结修改
→
停止
→
等待确认

---

## Phase 0：工程初始化

目标：

建立可运行的前后端 Monorepo 基础结构。

后端完成：

- Python 3.12
- uv
- FastAPI
- SQLAlchemy 2.x
- aiomysql
- Alembic
- pydantic-settings
- MySQL Docker Compose
- pytest
- Ruff

建立：

app/main.py
app/core/
app/db/
app/api/
tests/

完成：

- Settings
- AsyncEngine
- async_sessionmaker
- AsyncSession Dependency
- Declarative Base
- Alembic 初始化
- 健康检查接口
- 基础异常结构

不要创建实际业务表。

验收：

API 可以启动。

GET /health

正常返回。

MySQL 可以连接。

Alembic 可以执行。

pytest 可以运行。

FastAPI 可以通过 AsyncSession 异步连接 MySQL。

数据库查询、commit、rollback 均通过 async / await 完成。

---

## Phase 1：Auth + User

完成：

- users
- User Model
- 唯一 `phone_number`
- JWT
- current user dependency
- 手机号验证码登录
- 获取当前用户
- 修改当前用户昵称

开发与测试环境：

- 仅接受格式正确的测试手机号。
- 验证码通过环境变量配置，默认可使用 `8888`。
- 测试登录开关在生产环境必须关闭。

MVP 不实现微信登录。正式环境接入短信服务时，仅替换验证码校验实现。

测试：

无 Token 不能访问受保护接口。

有效 Token 可以获得当前 User。

手机号格式错误或验证码错误不能登录。

同一手机号重复登录得到同一 User。

用户可以修改自己的昵称；手机号不作为成员列表的日常展示名称。

---

## Phase 2：Farm + FarmMember

完成：

farms
farm_members

功能：

- 创建 Farm
- farmCode
- 我的 Farm
- Farm Detail
- 编辑 Farm

- Members
- OWNER
- ADMIN
- MEMBER

- 添加成员
- 修改角色
- 移除成员
- 主动退出农场

关键事务：

Create Farm
+
Create OWNER FarmMember

必须原子完成。

测试：

创建用户自动成为 OWNER。

普通用户不能访问未加入 Farm。

farmCode UNIQUE。

FarmMember UNIQUE(farm_id, user_id)。

ADMIN 不能操作 OWNER 或提升 OWNER。

任何成员角色变更、移除或退出后，Farm 仍至少有一位 OWNER。

---

## Phase 3：Plot

完成：

plots

功能：

- 创建 Plot
- 编辑 Plot
- Plot List
- Plot Detail

实现：

PlotType
AreaUnit
area_value
area_m2
boundary JSON

boundary 使用 `GCJ02` 坐标系的 JSON，面积字段为真值，不由 boundary 自动覆盖。

地图 UI 暂时不必完成。

测试：

跨 Farm 不能访问 Plot。

---

## Phase 4：Species + Production

完成：

species
productions

初始化系统 Species。

使用 Alembic 数据 migration 初始化覆盖四行业的少量系统 Species；不提供 Species 管理接口。

实现：

Industry
ProductionStatus

PlantingStandard
PlantingMethod
WorkMethod

功能：

- Species 搜索
- 开始种养
- 当前种养
- 历史种养
- Production Detail

支持：

农业
林业
牧业
渔业

字段差异。

重点测试：

一个 Plot 可以先后存在多条 Production。

一个 Plot 可以有多个 ACTIVE Production。

每个 Production 只能属于一个 Plot。

PlotType 与 Industry 不做强绑定。

ACTIVE Production 的核心字段与删除规则遵循业务规则中的纠错约束。

---

## Phase 5：FarmOperation

完成：

farm_operations

实现：

OperationType

功能：

- 创建农事
- Plot 农事列表

规则：

plotId 必填。

productionId 必传但可为 null。

Operator 默认当前用户。

WorkMethod 默认 MANUAL。

测试：

没有 Production：

可以记农事。

一个 ACTIVE Production：

能够正确关联。

多个 ACTIVE Production：

必须明确选择 Production 或整个 Plot。

传入其他 Plot 的 productionId：

拒绝。

字段缺失返回 422。

进行中 Production 允许补录过去农事，但不得早于 startedOn 或晚于当前时间。

FarmOperation 的编辑、删除及 ENDED 锁定规则正确生效。

---

## Phase 6：HarvestRecord

完成：

harvest_records

功能：

- 农业采收
- 林业采收
- 渔业捕捞
- 牧业出栏

实现：

Production Harvest List
Plot Harvest List

测试：

一个 Production 可以创建多条 HarvestRecord。

Harvest 必须属于 Production。

不能为其他 Farm 的 Production 创建 Harvest。

数量单位及整数／小数校验正确。

进行中 Production 允许补录过去收获，但不得早于 startedOn 或晚于当前时间。

HarvestRecord 的编辑、删除及 ENDED 锁定规则正确生效。

---

## Phase 7：结束种养

实现：

POST /productions/{id}/end

参数：

endedOn

规则：

ACTIVE
→
ENDED

测试：

0 Harvest：

允许结束。

多次 Harvest：

允许结束。

ENDED：

不能重复结束。

Harvest 不自动结束 Production。

endedOn 不早于 startedOn、关联农事或收获的业务日期，且不能晚于今天。

---

## Phase 8：地块完整详情

完成 Plot 聚合 API / 前端页面。

地块详情：

基本信息

种养：
- 当前
- 历史

农事

收获

重点：

这里只做聚合展示。

不要改变底层数据归属关系。

---

## Phase 9：小程序完整联调

### 农业

创建 Farm
→
创建大棚
→
开始黄瓜种植

普通
移栽
人工

→
施肥
→
灌溉
→
采收 100kg
→
采收 80kg
→
结束种植

验证：

完整历史正确。

---

### 渔业

创建鱼塘
→
青鱼投苗
→
换水
→
投料
→
捕捞
→
再次捕捞
→
结束养殖

---

### 牧业

创建栏舍
→
育肥猪入栏
→
喂料
→
消毒
→
出栏
→
结束养殖

---

### 空闲地块

创建 Plot
→
没有 Production
→
翻耕

必须成功。

---

### 多轮种植

1号大棚

Production A：
黄瓜
→
结束

Production B：
黄瓜
→
ACTIVE

A 和 B 的数据：

完全独立。

---

### 同时多种

1号地块：

Production A 黄瓜 ACTIVE
Production B 生菜 ACTIVE

创建农事时：

可以选择 A。

可以选择 B。

可以选择整个地块。

---

## 测试重点

必须重点覆盖：

- Farm 数据隔离
- FarmMember 权限
- FarmMember 唯一
- farmCode 唯一

- Plot 归属验证

- 一个 Plot 多个 Production
- 一个 Plot 多个 ACTIVE Production

- FarmOperation.productionId 可空
- FarmOperation 必须属于 Plot

- HarvestRecord 必须属于 Production
- Production 可以多次 Harvest

- 未 Harvest 允许结束
- 重复结束禁止

- Operator 必须属于 Farm

- 可预测 ID 不能造成越权

- OWNER 至少保留一位
- ADMIN 不能操作 OWNER
- 生产、农事、收获的时间边界
- 数量单位与整数／小数约束
- 分页与默认排序

---

## Codex 开发规则

1. 每次只开发当前 Phase。
2. 不提前实现后续需求。
3. 每个 Phase 结束后停止。
4. 不擅自增加产品模块。
5. 不提前引入 Redis、Celery、MQ。
6. 不做微服务。
7. 不做复杂 DDD。
8. 不建立 GenericRepository。
9. 不建立 BaseService 体系。
10. 不滥用设计模式。
11. 不直接返回 SQLAlchemy Model。
12. Request / Response 使用 Pydantic。
13. AsyncSession 生命周期由 FastAPI Dependency 管理。每个请求使用独立 AsyncSession。不要跨并发任务共享 AsyncSession。
14. 事务边界由 Service 控制。
15. 不创建全局 Session。
16. 数据库结构必须使用 Alembic。
17. Alembic autogenerate 后必须检查 migration 内容。
18. 不修改已执行 migration。
19. 不使用 UUID。
20. 不使用 Snowflake ID。
21. Farm 权限不能依靠 ID 难猜。
22. 不信任客户端传入的 farmId。
23. SQLAlchemy relationship 不要无脑配置 cascade。
24. 不为了少写代码创建复杂 ORM magic。
25. 不把所有 Model relationship 都默认 eager load。
26. 查询列表时注意 N+1。
27. 不把日期保存成字符串。
28. 不直接保存中文枚举。
29. 不给所有 Decimal 无脑设置 6 位精度。
30. 重要 Service 必须编写测试。
31. 有业务歧义先问。
32. 新增生产依赖前说明用途。
33. 一次不要修改大量与任务无关文件。
34. 优先标准、普通、容易读懂的 Python 写法。
35. 我正在学习 FastAPI 和 SQLAlchemy，关键实现不要故意使用复杂技巧。
36. 完成任务后说明：
   - 修改文件
   - migration
   - API
   - 测试结果
   - 尚未解决问题

---

## 当前第一次任务

现在不要实现任何业务模块。

首先：

1. 阅读全部 docs。
2. 总结你对领域模型的理解。
3. 给出 Phase 0 的目录结构。
4. 列出准备安装的 Python 依赖及用途。
5. 说明 SQLAlchemy Session 管理方式。
6. 说明 Alembic 配置方案。
7. 说明 Settings / 环境变量设计。
8. 给出 Phase 0 准备创建的文件。
9. 列出目前仍需确认的问题。

完成分析以后停止。

等待确认后，再开始 Phase 0。
