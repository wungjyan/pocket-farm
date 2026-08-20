# API 与安全设计

## 1. API 前缀

统一：

/api/v1

---

## 2. REST 风格

合理使用：

GET
POST
PATCH
DELETE

不要所有接口都使用 POST。

---

## 3. 认证

API 使用 Bearer JWT 表达：

已经登录的应用用户身份。

JWT 至少包含：

user id
expire time

不要把完整权限列表塞进 JWT。

权限应根据数据库当前 FarmMember 数据判断。

---

## 4. 登录方式

MVP 使用手机号验证码登录。

1. 小程序提交 `phoneNumber` 与 `verificationCode`。
2. 后端校验手机号格式和验证码。
3. 按手机号查询或创建 User。
4. 后端签发自己的 JWT。

开发与测试环境的验证码由环境变量控制，可固定为 `8888`。此测试模式必须在生产环境关闭；生产环境接入真实短信验证码服务时，只替换验证码校验实现，不改变 User、FarmMember 或成员添加方式。

MVP 不实现微信登录，也不依赖微信获取手机号。

---

## 5. 当前用户

提供统一依赖：

get_current_user

业务 Router 不自行解析 JWT。

---

## 6. 权限核心原则

资源访问逻辑：

Resource
→
Farm
→
FarmMember
→
Current User
→
Role

所有业务资源最终必须解析出所属 Farm。

---

## 7. 不信任前端 farmId

假设：

POST /farms/1/plots

不能因为前端传：

farmId = 1

就认为用户属于 Farm 1。

必须查询：

FarmMember

确认当前用户有权限。

---

## 8. Plot 权限

访问：

/plots/{plotId}

流程：

Plot
→ farm_id
→ FarmMember

检查当前 User。

---

## 9. Production 权限

访问：

/productions/{productionId}

流程：

Production
→ Plot
→ Farm
→ FarmMember

不能：

根据 Production ID 查到以后直接返回。

---

## 10. FarmOperation 权限

FarmOperation
→ Plot
→ Farm
→ FarmMember

如果 FarmOperation.production_id 不为空：

还需要验证 Production 确实属于同一个 Plot。

`operator_id` 还必须满足：对应 User 存在，且是该 Farm 的有效 FarmMember。`created_by` 不接受客户端传入，由后端从当前 JWT 写入；创建和编辑接口都不得允许客户端覆盖它。

---

## 11. HarvestRecord 权限

HarvestRecord
→ Production
→ Plot
→ Farm
→ FarmMember

`operator_id` 必须属于 Production 所属 Farm 的有效 FarmMember。`created_by` 始终由后端从当前 JWT 获取，客户端不可指定或修改。

---

## 12. 参考 API

### Auth

POST /api/v1/auth/login
GET  /api/v1/users/me
PATCH /api/v1/users/me

`POST /api/v1/auth/login` 的 Request：

```json
{
  "phoneNumber": "13800000001",
  "verificationCode": "8888"
}
```

`PATCH /api/v1/users/me` 仅允许更新昵称：

```json
{
  "nickname": "张三"
}
```

`phoneNumber` 是登录和成员查找字段，不在用户资料更新接口中开放，也不应作为农场成员列表的展示字段。

---

### Farm

GET  /api/v1/farms
POST /api/v1/farms

GET   /api/v1/farms/{farmId}
PATCH /api/v1/farms/{farmId}

---

### Member

GET  /api/v1/farms/{farmId}/members
POST /api/v1/farms/{farmId}/members

PATCH  /api/v1/farms/{farmId}/members/{memberId}
DELETE /api/v1/farms/{farmId}/members/{memberId}
DELETE /api/v1/farms/{farmId}/members/me

---

### Plot

GET  /api/v1/farms/{farmId}/plots
POST /api/v1/farms/{farmId}/plots

GET   /api/v1/plots/{plotId}
GET   /api/v1/plots/{plotId}/detail
PATCH /api/v1/plots/{plotId}

---

### Species

GET /api/v1/species

支持：

industry
keyword

等筛选。

---

### Production

GET  /api/v1/plots/{plotId}/productions
POST /api/v1/plots/{plotId}/productions

GET /api/v1/productions/{productionId}
PATCH /api/v1/productions/{productionId}
DELETE /api/v1/productions/{productionId}

POST /api/v1/productions/{productionId}/end

---

### Operation

GET  /api/v1/operation-types
GET  /api/v1/plots/{plotId}/operations
POST /api/v1/plots/{plotId}/operations
PATCH  /api/v1/operations/{operationId}
DELETE /api/v1/operations/{operationId}

---

### Harvest

GET  /api/v1/productions/{productionId}/harvests
POST /api/v1/productions/{productionId}/harvests
PATCH  /api/v1/harvests/{harvestId}
DELETE /api/v1/harvests/{harvestId}

地块聚合：

GET /api/v1/plots/{plotId}/harvests

---

### 操作人和记录人的 API 字段约束

FarmOperation 与 HarvestRecord 的创建请求可以传入 `operatorId`；未传入时由后端默认使用当前登录用户。传入后必须验证该用户属于资源所属 Farm 的有效 FarmMember。

HarvestRecord 的创建和编辑请求均不接受 `unit`。服务端根据 Production 对应 Species 派生单位：农业、渔业使用 `KG`，林业、牧业使用 Species.`individual_unit`；创建后单位作为历史快照，不允许通过 PATCH 修改。

FarmOperation 的创建请求必须传入 `operationTypeId`；该 ID 必须指向状态为 `ACTIVE` 的系统农事类型。农事类型列表仅返回 `ACTIVE` 记录，且不包含农场私有数据。

编辑请求仅在需要变更实际执行人时传入 `operatorId`，同样执行 FarmMember 校验。

`createdBy`、`createdAt` 属于服务端维护字段：

- 不接受客户端在创建或编辑请求中传入
- 创建时由 JWT 当前用户写入 `createdBy`
- 编辑时保持原始 `createdBy` 与 `createdAt`
- 响应可以返回记录人信息，供详情页在操作人与记录人不同时展示

---

## 13. Response

所有接口统一使用简单稳定的响应 envelope：

```json
{
  "success": true,
  "data": {},
  "error": null
}
```

成功响应将业务结果放在 `data`；错误响应将 `success` 设为 `false`，将 `data` 置为 `null`，并在 `error` 中返回错误信息。避免出现 `data.data` 等多层重复包装。

列表接口的分页结果放在 `data` 中：

```json
{
  "items": [],
  "page": 1,
  "pageSize": 20,
  "total": 0
}
```

所有列表都使用 `page`、`pageSize` 查询参数：默认 `page=1`、`pageSize=20`，最大 `pageSize=100`。

默认排序：Farm 与 Plot 按 `createdAt DESC`；Production 按 ACTIVE 优先、同状态按 `startedOn DESC`；FarmOperation 按 `operatedAt DESC`；HarvestRecord 按 `harvestedAt DESC`。

---

## 14. Error Response

错误 envelope 统一，例如：

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "PRODUCTION_ALREADY_ENDED",
    "message": "该种养已经结束",
    "details": null
  }
}
```

至少区分：

VALIDATION_ERROR
UNAUTHORIZED
FORBIDDEN
NOT_FOUND
BUSINESS_CONFLICT
INTERNAL_SERVER_ERROR

不要向客户端返回：

- Stack Trace
- SQL
- 数据库密码
- Python 异常内部信息

---

## 15. HTTP 状态码

合理使用：

200
201
204
400
401
403
404
409
422
500

业务状态冲突，例如：

重复结束 Production

适合返回：

409 Conflict

资源不存在，或当前用户根本不是资源所属 Farm 的成员时，统一返回 `404 NOT_FOUND`，避免泄露资源是否存在。用户已经是 Farm 成员、但角色不具备该操作权限时返回 `403 FORBIDDEN`；未登录或 Token 无效时返回 `401 UNAUTHORIZED`。

---

## 16. Schema

不要接收任意 dict。

所有 Request：

使用明确 Pydantic Schema。

例如：

CreateFarmRequest
CreatePlotRequest
StartProductionRequest
CreateOperationRequest
CreateHarvestRequest
EndProductionRequest
UpdateCurrentUserRequest

---

## 17. 更新接口

PATCH Request：

只允许更新明确开放字段。

不要简单：

把 Request 中所有字段直接 setattr 到 SQLAlchemy Model。

更新与删除的可用范围由业务规则限制：ENDED Production 及其关联记录不可修改；Production 的核心归属字段仅能在不存在关联农事和收获时修改；有记录的 Production 不可删除。

所有 datetime Request 字段必须是带时区的 ISO 8601 字符串。`productionId` 是创建农事时必传、但允许为 `null` 的字段；缺失时由 Pydantic 返回 `422 VALIDATION_ERROR`。

---

## 18. 数据越权测试

必须覆盖：

用户 A：

属于 Farm 1

用户 B：

属于 Farm 2

用户 A 即使知道：

Farm 2 的 plotId
productionId
harvestId

也不能读取或修改。

自增 ID 可预测不应该产生越权。
