# Pocket Farm

掌上农场是一个面向微信小程序的轻量生产管理 MVP。核心业务围绕农场、地块和一次种养生命周期展开。产品与研发规格位于 [`docs/`](./docs/)。

## 本地运行

依赖：Node.js、pnpm、Python 3.12、uv、Docker 和可访问的 MySQL 8。

本仓库不维护 Docker Compose 文件。本地开发使用手动启动的 MySQL 容器；数据库需要暴露给 `apps/api/.env` 中的 `DATABASE_URL`。如果尚未创建容器，可以根据自己的密码与数据库名执行类似命令：

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

## 文档

- [MVP 项目总览](./docs/mvp/00-project-overview.md)
- [小程序重构计划](./docs/refactor/00-miniapp-refactor-plan.md)
- [AI Tab MVP 规格](./docs/ai/00-ai-tab-mvp-spec.md)
- [AI Tab 技术设计](./docs/ai/01-ai-tab-technical-design.md)
- [AI Tab 交付计划](./docs/ai/02-ai-tab-delivery-plan.md)
- [AI 写入操作设计记录（暂不实现）](./docs/ai/03-ai-write-action-design.md)
