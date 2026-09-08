# Pocket Farm

掌上农场是一个面向微信小程序的轻量生产管理 MVP。核心业务围绕农场、地块和一次种养生命周期展开。产品与研发规格位于 [`docs/`](./docs/)。

## 本地运行

依赖：Node.js、pnpm、Python 3.12、uv、Docker 和可访问的 MySQL 8。

本地开发使用手动启动的 MySQL 容器；数据库需要暴露给 `apps/api/.env` 中的 `DATABASE_URL`。如果尚未创建容器，可以根据自己的密码与数据库名执行类似命令：

```bash
docker run --name pocket-farm-mysql \
  -e MYSQL_ROOT_PASSWORD=<your-password> \
  -e MYSQL_DATABASE=pocket_farm \
  -p 3306:3306 \
  -d mysql:8.0
```

后端：

```bash
cd apps/api
cp .env.example .env
uv sync
uv run alembic upgrade head
cd ../..
pnpm api:dev
```

小程序：

```bash
pnpm install
cp apps/miniapp/.env.example apps/miniapp/.env.local
pnpm miniapp:dev
```

使用微信开发者工具导入 `apps/miniapp/dist/dev/mp-weixin/`。本机调试可保持 `VITE_API_BASE_URL` 指向本机；真机调试时改为局域网可访问的 API 地址。

## 验证命令

```bash
cd apps/api
uv run pytest
uv run ruff check .
uv run alembic check

cd ../..
pnpm --dir apps/miniapp exec vue-tsc --noEmit -p tsconfig.json
pnpm miniapp:build
pnpm docs:build
```

## AI Tab 本地配置

AI Tab 计划使用 DeepSeek 官方 API 的 `deepseek-v4-flash`。配置项已列在 [`apps/api/.env.example`](./apps/api/.env.example) 中。

- 本地开发 AI 功能前，在 `apps/api/.env` 填入 `DEEPSEEK_API_KEY` 和一个随机的 `AI_USER_ID_HASH_KEY`。
- 不要提交 `.env`、API Key 或用户对话内容。
- API Key 未配置时，后续 AI 接口会拒绝 AI 请求，但其他业务 API 可正常运行。
- 部署阶段再确定公网 API 地址、HTTPS 和微信小程序请求域名白名单；当前本地开发不预设生产域名。

## Docker 部署

服务器部署文件位于 [`deploy/`](./deploy/)。三份 Compose 配置分别覆盖以下场景：

| 配置 | API 镜像 | MySQL | 适用场景 |
| --- | --- | --- | --- |
| [`docker-compose.yml`](./deploy/docker-compose.yml) | 从 `apps/api` 构建 | Compose 创建 | 本地构建，或服务器保留项目源码 |
| [`docker-compose.server.yml`](./deploy/docker-compose.server.yml) | 使用服务器已有镜像 | Compose 创建 | 服务器只保存部署文件和已导入镜像 |
| [`docker-compose.external-db.yml`](./deploy/docker-compose.external-db.yml) | 使用服务器已有镜像 | 连接已有数据库 | 数据库由云服务或其他主机维护 |

三种配置都从 `api.env` 读取 API 配置，并将 API 绑定到宿主机的 `127.0.0.1:8887`。正式环境应由宿主机 Nginx 提供 HTTPS 反向代理。

### 公共准备

```bash
cd deploy
cp api.env.example api.env
```

编辑 `api.env`，至少设置 `DATABASE_URL` 和随机的 `JWT_SECRET_KEY`，按需填写 AI 配置。不要提交实际环境文件；正式环境必须保持 `TEST_LOGIN_ENABLED=false`。

如需覆盖 Compose 中的默认 API 镜像，在命令前设置 `API_IMAGE`：

```bash
API_IMAGE=pocket-farm-api:<tag> docker compose -f <compose-file> up -d api
```

### 方式一：本地构建 API，并部署 MySQL

使用 [`deploy/docker-compose.yml`](./deploy/docker-compose.yml)。复制数据库环境变量，并保证 `api.env` 的数据库密码与 `mysql.env` 中的 `MYSQL_PASSWORD` 相同；连接主机保持为 `mysql`。

```bash
cp mysql.env.example mysql.env
# 编辑 mysql.env 和 api.env。

docker compose build
docker compose up -d mysql
docker compose --profile migration run --rm migrate
docker compose up -d api
```

### 方式二：使用已有镜像，并部署 MySQL

使用 [`deploy/docker-compose.server.yml`](./deploy/docker-compose.server.yml)。服务器需要提前导入 API 镜像和 `mysql:8.4` 镜像；该配置不会构建或拉取镜像，也不要求服务器保存项目源码。

```bash
cp mysql.env.example mysql.env
# 编辑 mysql.env 和 api.env。

docker compose -f docker-compose.server.yml up -d mysql
docker compose -f docker-compose.server.yml --profile migration run --rm migrate
docker compose -f docker-compose.server.yml up -d api
```

### 方式三：使用已有镜像，并连接外部 MySQL

使用 [`deploy/docker-compose.external-db.yml`](./deploy/docker-compose.external-db.yml)。该配置只包含 `api` 和一次性 `migrate` 服务，不会创建 MySQL 容器或数据卷，也不需要 `mysql.env`。

将 `api.env` 中的 `DATABASE_URL` 改为已有数据库的实际地址：

```env
DATABASE_URL=mysql+aiomysql://<user>:<password>@<database-host>:3306/<database-name>?charset=utf8mb4
```

确认数据库已创建、账号权限正确，并允许 API 所在服务器访问。若 MySQL 运行在 Docker 宿主机上，容器内的 `127.0.0.1` 并不指向宿主机，应使用容器可访问的宿主机地址。

```bash
docker compose -f docker-compose.external-db.yml --profile migration run --rm migrate
docker compose -f docker-compose.external-db.yml up -d api
```

无论使用哪种方式，都应先成功执行迁移，再启动或升级 API。

### 离线导入 API 镜像

若服务器不适合构建镜像，可在本机为 x86_64 服务器构建并导出镜像：

```bash
./scripts/build-api-image-linux-amd64.sh
scp artifacts/pocket-farm-api-<tag>-linux-amd64.tar.gz <server>:/path/to/deploy/
scp artifacts/pocket-farm-api-<tag>-linux-amd64.tar.gz.sha256 <server>:/path/to/deploy/
```

将所选 Compose 配置、`api.env` 以及方式二需要的 `mysql.env` 放到服务器。导入镜像后，使用相同的 `<tag>` 启动，不在服务器构建 API：

```bash
cd /path/to/deploy
sha256sum -c pocket-farm-api-<tag>-linux-amd64.tar.gz.sha256
docker load -i pocket-farm-api-<tag>-linux-amd64.tar.gz
```

导入后，在方式二或方式三的命令前设置相同的镜像 tag，例如：

```bash
API_IMAGE=pocket-farm-api:<tag> docker compose -f docker-compose.external-db.yml --profile migration run --rm migrate
API_IMAGE=pocket-farm-api:<tag> docker compose -f docker-compose.external-db.yml up -d api
```

### Nginx 与部署检查

将 [`deploy/nginx/farm.wungjyan.com.conf.example`](./deploy/nginx/farm.wungjyan.com.conf.example) 复制到宿主机 Nginx 配置，按实际域名与证书路径修改。执行 `nginx -t` 并重载 Nginx 后，确认公网 `/health` 接口返回成功。

生产环境必须保持 `TEST_LOGIN_ENABLED=false`。仅在有网络访问控制的临时测试环境中，才可将其改为 `true` 并设置非默认的 `TEST_LOGIN_CODE`；测试结束后立即关闭。小程序正式测试包还需要将 `VITE_API_BASE_URL` 设置为实际 HTTPS API 地址，并在微信小程序后台将对应域名配置为 request 合法域名。

## 文档

- [MVP 项目总览](./docs/mvp/00-project-overview.md)
- [小程序重构计划](./docs/refactor/00-miniapp-refactor-plan.md)
- [AI Tab MVP 规格](./docs/ai/00-ai-tab-mvp-spec.md)
- [AI Tab 技术设计](./docs/ai/01-ai-tab-technical-design.md)
- [AI Tab 交付计划](./docs/ai/02-ai-tab-delivery-plan.md)
- [AI 写入操作设计记录（暂不实现）](./docs/ai/03-ai-write-action-design.md)
