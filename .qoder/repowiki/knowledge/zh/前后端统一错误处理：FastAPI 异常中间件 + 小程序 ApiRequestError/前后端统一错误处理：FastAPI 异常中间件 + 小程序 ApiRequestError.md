---
kind: error_handling
name: 前后端统一错误处理：FastAPI 异常中间件 + 小程序 ApiRequestError
category: error_handling
scope:
    - '**'
source_files:
    - apps/api/app/core/error_codes.py
    - apps/api/app/core/exceptions.py
    - apps/api/app/schemas/response.py
    - apps/api/app/main.py
    - apps/miniapp/src/services/http.ts
---

## 1. 整体方案

本仓库在后端（FastAPI）与前端（uni-app 小程序）分别实现了统一的错误处理体系，并通过一致的响应信封 `ApiResponse` / `ApiEnvelope` 在两端对齐。

- **后端**：自定义 `AppException` 作为业务/领域异常的基类，配合 `ErrorCode` 枚举，通过 FastAPI 的 `add_exception_handler` 注册全局异常处理器，将任意异常统一序列化为 `{ success, data, error }` 结构返回。
- **前端**：封装 `uni.request` 为 `request()`，把后端返回的 envelope 中的 `error` 包装成 `ApiRequestError`（携带 `code`、`statusCode`、`details`），由调用方按 code 分支处理。

## 2. 关键文件

| 文件 | 职责 |
|---|---|
| `apps/api/app/core/error_codes.py` | 定义 `ErrorCode` StrEnum（`BUSINESS_CONFLICT`、`DATABASE_UNAVAILABLE`、`FORBIDDEN`、`INTERNAL_SERVER_ERROR`、`HTTP_ERROR`、`NOT_FOUND`、`UNAUTHORIZED`、`VALIDATION_ERROR`） |
| `apps/api/app/core/exceptions.py` | 定义 `AppException` 及四个全局异常处理器：`app_exception_handler`、`request_validation_exception_handler`、`http_exception_handler`、`unhandled_exception_handler`；提供 `register_exception_handlers(app)` |
| `apps/api/app/schemas/response.py` | 定义 `ErrorDetail` 与 `ApiResponse[DataT]`，提供 `success_response` / `error_response` 工厂方法 |
| `apps/api/app/main.py` | 在 `create_application()` 中调用 `register_exception_handlers(app)`，确保所有路由共享同一套错误处理 |
| `apps/miniapp/src/services/http.ts` | 定义 `ApiEnvelope`、`ApiErrorPayload`、`ApiRequestError`，集中处理 401 登出、204 无内容、成功 envelope 与失败 envelope |

## 3. 架构与约定

### 后端（FastAPI）

1. **抛出异常**：业务层（`services/*`）、依赖注入（`api/deps.py`）、健康检查等位置直接 `raise AppException(status_code=..., code=ErrorCode.X, message=..., details=...)`。例如认证失败抛 `UNAUTHORIZED`，并发写入冲突抛 `BUSINESS_CONFLICT`。
2. **全局处理器映射**：
   - `AppException` → 原样使用其 `status_code` + `code` + `message` + `details` 构造 `ApiResponse.error_response(...)`。
   - `RequestValidationError` → 固定 422，code 为 `VALIDATION_ERROR`，`details` 为 Pydantic 校验错误列表。
   - `StarletteHTTPException` → 使用其 `status_code`，code 固定为 `HTTP_ERROR`，`detail` 为字符串时放入 `message`，否则放入 `details`。
   - 兜底 `Exception` → 500，code 为 `INTERNAL_SERVER_ERROR`，不泄露堆栈。
3. **响应信封**：所有响应（含错误）均遵循 `ApiResponse` 结构：`success: bool`、`data: T | null`、`error: ErrorDetail | null`。成功路径由业务代码显式返回 `ApiResponse.success_response(data)`。

### 前端（uni-app）

1. **统一请求入口**：所有业务 service（`auth.ts`、`farm.ts`、`harvest.ts` 等）通过 `request<T>({ url, method, data })` 发起 HTTP 请求，自动附加 `Authorization: Bearer <token>`。
2. **错误分类**：
   - 网络层失败（`fail` 回调）→ 抛出 `ApiRequestError("网络连接失败")`。
   - 401 → 先 `clearAuthToken()` 再走 envelope 错误分支。
   - 204 → 直接 resolve `undefined`。
   - 2xx 且 `envelope.success === true` 且 `data !== null` → 正常 resolve。
   - 其他情况 → 从 `envelope.error` 构造 `ApiRequestError(message, code, statusCode, details)`。
3. **错误码映射**：前端保留后端返回的 `code`（如 `UNAUTHORIZED`、`BUSINESS_CONFLICT`），并在网络失败时回退为 `REQUEST_FAILED`，HTTP 错误时回退为 `HTTP_{statusCode}`。

## 4. 约束与规则

- 业务异常必须通过 `AppException` 抛出，禁止在 handler/service 中直接返回 `JSONResponse` 或 `Response`，以保证错误被统一序列化。
- 新增错误类型应在 `ErrorCode` 中声明，而不是散落的字符串字面量。
- 所有 API 响应必须使用 `ApiResponse.success_response` / `ApiResponse.error_response` 构造，保证 `success/data/error` 三字段稳定。
- 前端不得绕过 `request()` 直接调用 `uni.request`，以确保 401 清理 token、错误包装逻辑一致生效。
- 未捕获异常不会暴露内部细节给客户端，统一降级为 `INTERNAL_SERVER_ERROR`。

## 5. 覆盖范围说明

该错误处理体系主要覆盖 API 服务与小程序之间的 HTTP 通信。文档站（VitePress）与 Alembic 迁移脚本未涉及此模式，因此本卡片仅对 `apps/api` 与 `apps/miniapp` 有效。