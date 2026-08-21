---
kind: error_handling
name: 前后端统一错误处理：AppException + ErrorCode + ApiResponse 信封与前端 ApiRequestError
category: error_handling
scope:
    - '**'
source_files:
    - apps/api/app/core/exceptions.py
    - apps/api/app/core/error_codes.py
    - apps/api/app/schemas/response.py
    - apps/api/app/main.py
    - apps/api/app/api/deps.py
    - apps/api/app/services/auth.py
    - apps/miniapp/src/services/http.ts
---

## 1. 总体方案

Pocket Farm 在 FastAPI 后端与 uni-app 小程序前端之间采用**统一的响应信封 + 领域错误码 + 全局异常处理器**的错误处理体系：

- 后端通过自定义 `AppException` 表达“预期内”的业务/认证/资源错误，并由全局异常处理器统一转换为标准 JSON 信封。
- 所有 API 响应（成功与失败）均使用 `ApiResponse[DataT]` 信封，包含 `success`、`data`、`error` 三个字段。
- 错误码集中在 `ErrorCode` StrEnum 中声明，保证机器可读且稳定。
- 前端 `http.ts` 解析后端信封，将业务错误包装为 `ApiRequestError` 并 reject Promise，网络层错误也统一转为该类型；401 自动清理本地 token。

## 2. 关键文件与职责

| 文件 | 职责 |
|---|---|
| `apps/api/app/core/error_codes.py` | 定义 `ErrorCode` StrEnum（`BUSINESS_CONFLICT`、`DATABASE_UNAVAILABLE`、`FORBIDDEN`、`INTERNAL_SERVER_ERROR`、`HTTP_ERROR`、`NOT_FOUND`、`UNAUTHORIZED`、`VALIDATION_ERROR`），作为全系统稳定的错误标识 |
| `apps/api/app/schemas/response.py` | 定义 `ErrorDetail` 与泛型 `ApiResponse[DataT]`，提供 `success_response` / `error_response` 两个构造器，是所有 API 响应的唯一信封 |
| `apps/api/app/core/exceptions.py` | 定义 `AppException`（携带 `status_code`、`code`、`message`、`details`），并注册四个全局异常处理器：`AppException`、`RequestValidationError`、`StarletteHTTPException`、兜底 `Exception` |
| `apps/api/app/main.py` | 在 `create_application()` 中调用 `register_exception_handlers(app)`，确保应用启动即挂载全部处理器 |
| `apps/api/app/api/deps.py` | 认证依赖 `get_current_user`，缺失/无效 token 时抛出 `AppException(status_code=401, code=ErrorCode.UNAUTHORIZED, ...)`；DB session 依赖在异常时执行 rollback |
| `apps/api/app/services/auth.py` | 登录流程捕获 SQLAlchemy `IntegrityError`，回滚后转抛 `AppException(code=ErrorCode.BUSINESS_CONFLICT, status_code=409)` |
| `apps/miniapp/src/services/http.ts` | 封装 `uni.request`，解析后端 `ApiEnvelope<T>`，成功路径 resolve(data)，业务错误 reject(`ApiRequestError`)，网络失败 reject(`ApiRequestError`)，401 自动 `clearAuthToken()` |

## 3. 架构与约定

### 后端异常分层

1. **业务/认证/资源错误**：在 service / dependency 层直接 `raise AppException(status_code=..., code=ErrorCode.XXX, message=...)`。例如 `deps.get_current_user` 对无 token、JWT 解析失败、用户不存在等场景统一返回 `UNAUTHORIZED`；`auth.login_with_verification_code` 对并发创建用户返回 `BUSINESS_CONFLICT`。
2. **请求校验错误**：FastAPI 的 `RequestValidationError` 由 `request_validation_exception_handler` 拦截，固定返回 422 + `ErrorCode.VALIDATION_ERROR`，并将 Pydantic 校验错误序列化为 `details`。
3. **HTTP 异常**：任意 `StarletteHTTPException` 被 `http_exception_handler` 捕获，映射为 `ErrorCode.HTTP_ERROR`，保留原始 `status_code` 与 `detail`。
4. **未捕获异常**：兜底 `Exception` 处理器返回 500 + `INTERNAL_SERVER_ERROR`，不泄露堆栈给客户端。
5. **数据库会话**：`get_db_session` 在 `yield` 期间捕获任何异常并 `session.rollback()` 后再抛出，避免脏连接泄漏。

### 响应信封

- 成功：`ApiResponse.success_response(data)` → `{ success: true, data: ..., error: null }`
- 失败：`ApiResponse.error_response(code, message, details?)` → `{ success: false, data: null, error: { code, message, details? } }`

所有异常处理器都通过 `ApiResponse.error_response` 输出，保证客户端只需检查 `envelope.success` 即可区分成功与失败。

### 前端错误处理

- `http.ts` 的 `request<T>()` 是唯一的 HTTP 入口。
- 成功分支：`2xx` 且 `envelope.success === true` 且 `data !== null` 时 resolve(data)；`204 No Content` 直接 resolve(undefined)。
- 业务错误：reject `ApiRequestError(message, code, statusCode, details)`，其中 `code` 优先取后端 `error.code`，否则退化为 `HTTP_状态码`。
- 网络错误：`fail` 回调 reject `ApiRequestError(error.errMsg || "网络连接失败")`。
- 鉴权失效：收到 `401` 时调用 `clearAuthToken()`，后续请求不再带过期 token。

## 4. 约定与约束

- **所有可预期的 API 错误必须通过 `AppException` 抛出**，而不是在 endpoint 中手动构造 `JSONResponse`——由全局处理器统一收敛。
- **错误码必须来自 `ErrorCode`**，新增错误需先在枚举中声明，禁止随意使用字符串码。
- **所有 API 响应必须使用 `ApiResponse` 信封**，禁止直接返回裸 dict/pydantic model。
- **数据库操作必须在 try/except 中捕获并 rollback**，如 `auth.py` 对 `IntegrityError` 的处理模式。
- **前端只依赖 `http.ts` 发起请求**，页面/组件不应直接使用 `uni.request`，从而保证错误统一包装。
- **401 自动登出**：前端对 401 无条件清除本地 token，由业务层引导重新登录。
- **未捕获异常对外隐藏细节**：兜底处理器仅返回通用 `Internal server error.`，不暴露内部堆栈或敏感信息。

## 5. 覆盖范围说明

- 后端：完整的异常类、错误码枚举、全局处理器、响应信封、服务层/依赖层使用模式均已实现。
- 前端：统一的 HTTP 封装、错误信封解析、`ApiRequestError` 类型已实现；但当前代码库中尚未发现业务组件对 `ApiRequestError` 的 catch 消费逻辑（可能由更高层路由或页面级 guard 处理）。
- 文档站（VitePress）不涉及运行时错误处理。
