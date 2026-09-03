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

服务器部署文件位于 [`deploy/`](./deploy/)。该配置使用独立的 API 与 MySQL 容器：MySQL 不映射宿主机端口，API 仅绑定到 `127.0.0.1:8887`，由宿主机 Nginx 为 `farm.wungjyan.com` 提供 HTTPS 反向代理。

服务器已导入 API 镜像与 `mysql:8.4` 镜像时，使用
[`deploy/docker-compose.server.yml`](./deploy/docker-compose.server.yml)。它不包含构建上下文，不要求服务器保存项目源码，也不会拉取镜像。当前默认 API 镜像是 `wungjyan/pocket-farm-api:20260902-1`；升级镜像时，通过 `API_IMAGE` 指定新 tag。

```bash
cd deploy
cp mysql.env.example mysql.env
cp api.env.example api.env
# 编辑两个文件，填入不同的随机数据库密码与 JWT 密钥；按需填写 AI 密钥。
# 正式环境必须保持 TEST_LOGIN_ENABLED=false。

docker compose -f docker-compose.server.yml up -d mysql
docker compose -f docker-compose.server.yml --profile migration run --rm migrate
docker compose -f docker-compose.server.yml up -d api
```

本地构建或服务器允许构建 API 时，使用 [`deploy/docker-compose.yml`](./deploy/docker-compose.yml)：

```bash
cd deploy
cp mysql.env.example mysql.env
cp api.env.example api.env
# 编辑两个文件，填入不同的随机数据库密码与 JWT 密钥；按需填写 AI 密钥。
# 正式环境必须保持 TEST_LOGIN_ENABLED=false。

docker compose build
docker compose up -d mysql
docker compose --profile migration run --rm migrate
docker compose up -d api
```

首次部署或每次升级后，确认 `https://farm.wungjyan.com/health` 返回成功。将
[`deploy/nginx/farm.wungjyan.com.conf.example`](./deploy/nginx/farm.wungjyan.com.conf.example)
复制到宿主机 Nginx 配置后，按服务器实际证书路径修改并执行 `nginx -t`、重载 Nginx。

若服务器不适合构建镜像，可在本机为 x86_64 服务器构建并导出镜像：

```bash
./scripts/build-api-image-linux-amd64.sh
scp artifacts/pocket-farm-api-<tag>-linux-amd64.tar.gz <server>:/path/to/deploy/
scp artifacts/pocket-farm-api-<tag>-linux-amd64.tar.gz.sha256 <server>:/path/to/deploy/
```

将 `deploy/` 目录中的 Compose 配置和两个环境文件一并放到服务器。导入镜像后，使用相同的 `<tag>` 启动，不在服务器构建 API：

```bash
cd /path/to/deploy
sha256sum -c pocket-farm-api-<tag>-linux-amd64.tar.gz.sha256
docker load -i pocket-farm-api-<tag>-linux-amd64.tar.gz

docker compose -f docker-compose.server.yml up -d mysql
API_IMAGE=pocket-farm-api:<tag> docker compose -f docker-compose.server.yml --profile migration run --rm migrate
API_IMAGE=pocket-farm-api:<tag> docker compose -f docker-compose.server.yml up -d api
```

生产环境必须保持 `TEST_LOGIN_ENABLED=false`。仅在有网络访问控制的临时测试环境中，才可将其改为 `true` 并设置非默认的 `TEST_LOGIN_CODE`；测试结束后立即关闭。小程序正式测试包还需要将 `VITE_API_BASE_URL` 设置为 `https://farm.wungjyan.com/api/v1`，并在微信小程序后台配置 `https://farm.wungjyan.com` 为 request 合法域名。

## 文档

- [MVP 项目总览](./docs/mvp/00-project-overview.md)
- [小程序重构计划](./docs/refactor/00-miniapp-refactor-plan.md)
- [AI Tab MVP 规格](./docs/ai/00-ai-tab-mvp-spec.md)
- [AI Tab 技术设计](./docs/ai/01-ai-tab-technical-design.md)
- [AI Tab 交付计划](./docs/ai/02-ai-tab-delivery-plan.md)
- [AI 写入操作设计记录（暂不实现）](./docs/ai/03-ai-write-action-design.md)
