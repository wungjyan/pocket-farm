# 技术架构与工程规范

## 1. Monorepo

项目采用一个 Git 仓库：

pocket-farm/
├── apps/
│   ├── api/
│   └── miniapp/
├── docs/
├── docker-compose.yml
└── README.md

前后端分别使用自己的依赖管理系统。

---

## 2. 小程序

技术栈：

- uni-app
- Vue 3
- TypeScript
- Pinia
- Vite

目标平台：

微信小程序

第一阶段只保证微信小程序正常使用。

---

## 3. 后端

技术栈：

- Python 3.12
- FastAPI
- SQLAlchemy 2.x ORM
- aiomysql
- Alembic
- MySQL 8.0
- Pydantic 2
- pydantic-settings
- PyJWT
- pwdlib
- uv
- pytest
- httpx
- Ruff

MVP 统一使用 SQLAlchemy asyncio。

使用：

- create_async_engine
- AsyncSession
- async_sessionmaker

MySQL 异步驱动使用 aiomysql。

数据库连接格式：

mysql+aiomysql://...

API、Service 和数据库访问链路统一使用 async / await，
不要在异步请求中混入同步 SQLAlchemy Session。

原因不是否定异步方案，而是当前项目首先追求：

- 容易理解
- 容易调试
- 事务边界清晰
- 降低学习复杂度

未来出现明确的异步数据库需求时再评估。

---

## 4. 不使用 SQLModel

本项目明确使用：

SQLAlchemy ORM
+
Pydantic Schema

分别承担：

数据库模型
+
API 输入输出模型

不要为了减少代码引入 SQLModel。

---

## 5. API 目录

建议：

apps/api/
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   ├── deps.py
│   │   └── v1/
│   │       ├── router.py
│   │       └── endpoints/
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── exceptions.py
│   │   └── error_codes.py
│   │
│   ├── db/
│   │   ├── base.py
│   │   └── session.py
│   │
│   ├── models/
│   ├── schemas/
│   ├── services/
│   └── repositories/
│
├── alembic/
├── tests/
├── pyproject.toml
└── alembic.ini

`repositories/` 不是强制层。

只有查询逻辑明显复杂或需要复用时再创建 Repository。

不要建立 GenericRepository。

简单查询允许由 Service 使用 SQLAlchemy Session 完成。

---

## 6. 层职责

### API / Router

负责：

- HTTP 参数
- Depends
- Request Schema
- Response Schema
- HTTP 状态码

不要写复杂业务逻辑。

---

### Service

负责：

- 业务规则
- 权限验证
- 事务
- 多表操作
- 状态变化

Service 是主要业务层。

---

### Model

SQLAlchemy ORM Model。

只描述：

- 表结构
- 字段
- relationship
- 数据库约束

不要把大量业务逻辑塞进 ORM Model。

---

### Schema

Pydantic Model。

区分：

- Create
- Update
- Response

例如：

CreateFarmRequest
UpdateFarmRequest
FarmResponse

不要直接把 SQLAlchemy Model 返回给 API。

---

## 7. SQLAlchemy 规范

使用 SQLAlchemy 2.x Typed Declarative 风格。

Base 使用：

DeclarativeBase

字段使用：

Mapped
mapped_column

建立统一 Base，并配置 constraint naming convention，方便 Alembic migration。

Session：

每个 Request 获取独立 AsyncSession。

使用 FastAPI Dependency 管理 AsyncSession 生命周期。

推荐：

async_sessionmaker(
    engine,
    expire_on_commit=False
)

不要创建全局 AsyncSession。

不要在多个并发 task 之间共享同一个 AsyncSession。

异步 ORM 查询原则：

- 避免依赖 relationship 隐式 lazy loading
- 需要关联数据时明确使用 selectinload / joinedload
- 避免产生隐式数据库 IO
- 列表接口注意 N+1 查询

不要使用全局 Session。

事务由 Service 控制。

---

## 8. 配置

使用：

pydantic-settings

配置至少包括：

APP_NAME
DEBUG
API_V1_PREFIX
DATABASE_URL
JWT_SECRET_KEY
JWT_ALGORITHM
JWT_EXPIRE_MINUTES
APP_TIMEZONE

开发／测试环境额外配置：

TEST_LOGIN_ENABLED
TEST_LOGIN_CODE

敏感信息：

- 数据库密码
- JWT Secret
- 第三方密钥

只能从环境变量获取。

不要提交真实 `.env`。

提供：

.env.example

`TEST_LOGIN_ENABLED` 必须在生产环境设为 `false`。测试环境仅校验手机号格式与固定验证码；生产环境不保留固定验证码登录。

---

## 9. 数据库

使用 MySQL 8.0 与 `utf8mb4`。本地开发通过仓库根目录的 `docker-compose.yml` 启动：

```bash
docker compose up -d mysql
```

默认连接地址：

```text
mysql+aiomysql://pocket_farm:pocket_farm@127.0.0.1:3306/pocket_farm?charset=utf8mb4
```

Compose 中的数据库名、账号和密码都可通过同名环境变量覆盖；数据持久化在命名卷 `mysql_data` 中。

数据库字段：

snake_case

Python：

snake_case

---

## 10. 数据库迁移

所有 Schema 修改必须使用 Alembic。

开发流程：

修改 SQLAlchemy Model
→
生成 migration
→
人工检查 migration
→
执行 migration

禁止：

直接手工修改正式数据库
然后不留下 migration。

不要修改已经执行过的历史 migration。

需要变更时创建新 revision。

---

## 11. 主键

MVP 不使用 UUID。

所有主要业务表：

BIGINT UNSIGNED AUTO_INCREMENT

Python：

int

SQLAlchemy：

BigInteger
autoincrement=True

不要：

UUID
Snowflake
NanoID

除非未来出现明确业务理由。

---

## 12. ID 与安全

类似：

/plots/123
/productions/586

是允许的。

ID 是否可猜测与安全无关。

安全依靠 FarmMember 权限验证。

---

## 13. farmCode

Farm 除内部 id 外提供：

farm_code

规则：

- 6 位数字
- 100000 ~ 999999
- 后端创建 Farm 时自动生成
- 用户不可填写
- UNIQUE
- 碰撞后重新生成

例如：

id = 138
farm_code = 583921

id 用于数据库关联。

farmCode 用于：

- 用户展示
- 搜索
- 后续邀请场景

不要使用 farmCode 作为主键。

---

## 14. 枚举存储

Python 使用 Enum / StrEnum 表达业务枚举。

数据库保存稳定英文代码。

例如：

MANUAL
MECHANICAL
ACTIVE
ENDED

不要直接保存：

人工
机械
进行中
已结束

为了便于未来扩展：

数据库优先使用 VARCHAR 保存枚举代码。

不要默认使用 MySQL ENUM 类型。

---

## 15. 时间

业务日期：

Python：
date

MySQL：
DATE

例如：

Production.started_on
Production.ended_on
expected_harvest_on

具体操作时间：

Python：
datetime

MySQL：
DATETIME

例如：

FarmOperation.operated_at
HarvestRecord.harvested_at
created_at
updated_at

不要把日期时间保存为字符串。

API 的 `datetime` 使用带时区的 ISO 8601 字符串，例如 `2026-08-14T16:30:00+08:00`。后端将其转换为 UTC 后保存到 MySQL `DATETIME`；MVP 的默认业务时区为 `Asia/Shanghai`。业务日期字段继续使用 `DATE`，不携带时区。

---

## 16. 数值

不要所有字段统一使用 6 位小数。

根据业务设计合理精度。

面积可以保留：

area_value
area_unit
area_m2

其中：

area_value：
保留用户填写数值

area_unit：
亩 / 平方米 / 公顷对应的稳定代码

area_m2：
后端计算得到的标准平方米值

不要存三份不同单位的面积。

数量单位固定为 `KG`、`TON`、`HEAD`、`PIECE`、`PLANT`、`TAIL`，不接受任意字符串。`HEAD`、`PIECE`、`PLANT` 与 `TAIL` 必须是整数；`KG` 与 `TON` 可以为小数。MVP 不提供 `KG` 与 `TON` 的自动换算。

预计产量仅表示总产量，沿用上述数量单位；不实现 `KG_PER_MU`、`TON_PER_MU` 等单位面积产量单位。

API 返回时不要人为补大量尾随 0。

---

## 17. Plot boundary

第一阶段使用：

MySQL JSON

保存带 `coordinateSystem: "GCJ02"` 的 Polygon JSON，`boundary` 可以为空。它是辅助空间信息，不等同于标准 WGS84 GeoJSON，也不自动覆盖用户确认的面积。

不要为了 MVP 地块轮廓直接引入 GIS 服务或 PostGIS。

---

## 18. 依赖管理

使用 uv。

依赖通过：

pyproject.toml

管理。

不要同时维护：

requirements.txt
Pipfile
Poetry

多套依赖系统。

---

## 19. 代码质量

使用 Ruff：

- lint
- format

测试：

pytest

API 测试：

httpx

不要求第一阶段搭建复杂 CI/CD。

---

## 20. 暂不引入

MVP 不需要：

- Redis
- Celery
- RabbitMQ
- Kafka
- Elasticsearch
- SQLModel
- Django
- 微服务
- DDD 框架
- Dependency Injector 第三方框架

优先使用 FastAPI 原生 Depends 和普通 Python 代码。
