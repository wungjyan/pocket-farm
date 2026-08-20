# 核心业务规则

## 1. 创建农场

用户创建 Farm 时：

1. 创建 Farm。
2. 自动生成唯一 6 位 farmCode。
3. 创建当前用户对应的 FarmMember。
4. 角色设置为 OWNER。

上述操作必须在同一个数据库事务中完成。

---

## 2. 成员管理

第一阶段只添加已注册用户；通过唯一手机号查找用户。

手机号仅用于添加成员时的精确查找。农场成员列表和业务记录中的操作人展示 `nickname`，不公开完整手机号；昵称未设置时，前端使用脱敏手机号生成的兜底展示名。

MVP 支持成员列表、添加成员、修改角色、移除成员和主动退出农场。角色操作规则如下：

| 操作者 | 可以操作的成员 | 可以设置的角色 |
| --- | --- | --- |
| OWNER | 其他 OWNER、ADMIN、MEMBER | OWNER、ADMIN、MEMBER |
| ADMIN | ADMIN、MEMBER | ADMIN、MEMBER |
| MEMBER | 仅自己退出 | 无 |

约束：

- 一个 Farm 可以有多个 OWNER，但任意时刻必须至少保留一位 OWNER。
- ADMIN 不能操作 OWNER，也不能把成员提升为 OWNER。
- OWNER 可先将其他成员提升为 OWNER，再降级或退出；不单独提供“转移所有权”接口。
- ADMIN 和 MEMBER 可自行退出。OWNER 仅在 Farm 中仍有其他 OWNER 时可退出。
- 上述约束必须由后端在事务中校验，不能只依赖前端按钮状态。

---

## 3. 用户资料

MVP 仅支持用户修改自己的 `nickname`，不提供用户名、密码或手机号修改功能。手机号变更与账号合并留待正式短信认证方案单独设计。

---

## 4. 权限

OWNER：

- 编辑农场
- 管理成员
- 管理地块
- 开始种养
- 农事
- 收获
- 结束种养

ADMIN：

- 管理成员
- 管理地块
- 开始种养
- 农事
- 收获
- 结束种养

MEMBER：

- 查看
- 开始种养
- 农事
- 收获
- 结束种养

MVP 不做复杂权限配置。

---

## 5. 创建地块

必填：

name

建议填写：

type
area

`boundary` 选填。用户可以手动填写面积，也可以绘制 Polygon 后由前端计算建议面积；最终提交的 `area_value` 与 `area_unit` 是面积真值，用户可以修改建议值。

边界使用带 `coordinateSystem: "GCJ02"` 的 JSON 保存，不自动覆盖面积。地图功能不能阻塞创建地块。

---

## 6. 开始种养

“开始种养”创建一条 Production。

公共核心字段：

speciesId *
variety
plotId *
startedOn *

一个 Production 只能关联一个 Plot。创建表单始终显示地块必填项：首页进入时由用户选择，从地块详情进入时默认带入当前 `plotId`，但允许在同一 Farm 内重选。后端仍将 Plot 作为必填关联校验。

后端不强制绑定 PlotType 与 Industry；前端可按行业推荐地块类型，但用户仍可选择其他地块。

小程序创建流程分为两步：先在独立页面选择种类，再进入正式表单填写地块、选填品种和行业字段。正式表单只读展示已选种类，不支持中途更换；需要更换时返回种类选择页，未提交的表单内容不保留。

---

## 7. 农业 / 林业

农业和林业均使用 Species 的固定个体单位，不提供单位选择器。种植标准默认 `NORMAL`、种植方式默认 `TRANSPLANT`、作业方式默认 `MANUAL`；三项均为必填。

种植方式必须在时间字段前填写，并决定前端术语：

| PlantingMethod | 时间字段 | 数量字段 |
| --- | --- | --- |
| `TRANSPLANT` | 移栽时间 | 移栽数量 |
| `DIRECT_SEEDING` | 播种时间 | 播种数量 |

切换种植方式仅改变术语，不清空已填日期或数量。

农业必填：`speciesId`、`plotId`、种植标准、种植方式、移栽／播种时间、作业方式。移栽／播种数量、株间距、预计采收时间、预计亩产、品种与备注选填。预计亩产固定显示“公斤／亩”，仅保存 `expectedYieldPerMu` 数值。

林业必填：农业必填项加移栽／播种数量。林业不提供预计亩产。

株间距仅适用于农业和林业，选填，固定显示“厘米”，只保存 `plantSpacingCm` 数值。

---

## 8. 牧业

前端术语：

Plot → 栏舍
startedOn → 入栏时间
initialQuantity → 入栏数量

核心字段：

speciesId *
plotId *
startedOn *
initialQuantity *

保留：

variety
entryAgeDays
remark

entryAgeDays：

必填，表示入栏日龄。

牧业不展示也不保存 `workMethod`。入栏数量必填，单位由 Species 固定单位自动带出，例如猪、牛、羊为“头”，鸡、鸭为“羽”。

内部如需要生产编号：

由系统自动生成。

不要让用户填写批次号。

---

## 9. 渔业

前端术语：

Plot → 养殖地块
startedOn → 养殖时间
initialQuantity → 养殖数量

核心字段：

speciesId *
plotId *
startedOn *
initialQuantity *
workMethod *

保留：

variety
initialQuantity
workMethod
remark

养殖数量必填，单位由 Species 固定单位自动带出。作业方式必填，前端默认 `MANUAL`。

---

## 10. 行业术语

后端保持统一模型。

前端根据 Industry 展示术语。

AGRICULTURE：

开始种植
采收
结束种植

FORESTRY：

开始种植
采收
结束种植

LIVESTOCK：

开始养殖
出栏
结束养殖

FISHERY：

开始养殖
捕捞
结束养殖

不要为了文字差异建立四套重复 API 和数据库表。

---

## 11. 农事

FarmOperation 首先属于 Plot。

因此：

没有 Production
也允许记农事。

例如：

翻耕
清沟
消毒
灌溉
清塘

---

## 12. 农事基础信息

MVP 农事表单统一为：

operationTypeId *
plotId *

workMethod
operatedAt
operator
remark

默认：

workMethod = MANUAL
operatedAt = 当前时间
operator = 当前用户

`operator` 表示实际执行农事的 Farm 成员。前端默认选择当前用户，但允许改选当前 Farm 的其他有效成员。请求中的 `operatorId` 必须由后端校验其对应用户存在且属于当前 Farm；不允许仅依赖前端的成员选择列表。

系统另行保存 `createdBy`：它表示在系统中创建记录的用户，必须由后端从 JWT 获取，前端不能传入、指定或修改。创建时：

```text
createdBy = current_user.id
```

编辑时保留原始 `createdBy` 与 `createdAt`，不因编辑人变化而更新。MVP 暂不增加 `updatedBy` 或完整审计日志。

照片可以后续增加。

不要让文件上传阻塞第一版。

---

## 13. 农事暂不关联农资

例如施肥：

MVP 只记录：

施肥这个行为。

暂时不要继续要求：

- 肥料
- 农资
- 数量
- 浓度
- 库存

同理不要为不同 OperationType 动态生成复杂表单。

---

## 14. FarmOperation 自动关联 Production

创建农事的 `productionId` 必传但允许为 `null`；字段缺失时返回 `422`，后端不根据缺失字段猜测业务含义。关联具体种养是选填的追溯能力，默认记录整个地块。

| 地块当前状态 | 前端行为 | 请求中的 `productionId` |
| --- | --- | --- |
| 没有 ACTIVE Production | 记录整个地块 | `null` |
| 有一条或多条 ACTIVE Production | 默认记录整个地块；用户可按带开始日期、品种和初始数量的批次卡片选择具体种养 | 对应 ID 或 `null` |

后端必须校验非空 `productionId` 确实属于当前 Plot。

农事类型由系统 `OperationType` 数据表维护。创建或改选时只能使用 `ACTIVE` 类型；下架后不影响既有农事记录的展示和编辑（编辑时可保留原类型，但不可切换到其他下架类型）。

---

## 15. 收获

HarvestRecord 必须属于具体 Production。

不能只针对 Plot 创建收获记录。

---

## 16. 收获术语

AGRICULTURE：
采收

FORESTRY：
采收

FISHERY：
捕捞

LIVESTOCK：
出栏

牧业 MVP 暂时只处理“出栏”。

暂不处理：

- 鸡蛋
- 牛奶
- 羊毛
- 羽毛
- 肉类

等其他过程产出。

---

## 17. 收获字段

核心：

productionId *
quantity *

默认：

workMethod = MANUAL
harvestedAt = 当前时间
operator = 当前用户

`operator` 表示实际执行采收、捕捞或出栏的 Farm 成员。前端默认当前用户，但允许改选当前 Farm 的其他有效成员；后端必须验证该成员归属于当前 Farm。

HarvestRecord 同样保存 `createdBy`，由后端根据 JWT 自动写入，前端不可传入或修改；编辑时保留原始 `createdBy` 与 `createdAt`。

选填：

productName
grade
remark

productName 可以默认 Species.name。

grade：

不能自动默认“特等品”等业务事实。

数量字段和单位按行业固定：

| 行业 | 前端字段名 | 保存单位 | 数值规则 |
| --- | --- | --- | --- |
| 农业 | 采收重量 | `KG` | 允许小数 |
| 渔业 | 捕捞重量 | `KG` | 允许小数 |
| 林业 | 采收数量 | Species.`individual_unit` | 必须为整数 |
| 牧业 | 出栏数量 | Species.`individual_unit` | 必须为整数 |

`unit` 由后端根据 Production 对应的 Species 自动派生，客户端不能在创建或编辑请求中传入。创建时保存为 HarvestRecord 的历史快照，之后允许修改 `quantity`，但不允许修改 `unit`。可保存的单位代码为 `KG`、`HEAD`、`FEATHER`、`PIECE`、`PLANT`、`TAIL`；MVP 不做单位换算。

---

## 18. 收获次数

一次 Production 可以多次 Harvest。

例如：

08-20 100kg
08-25 120kg
09-01 80kg

三次必须是三条 HarvestRecord。

---

## 19. 收获不会结束种养

创建 HarvestRecord 后：

Production.status 仍然保持 ACTIVE。

除非用户明确执行：

结束种养。

---

## 20. 结束种养

结束操作只需要：

endedOn

默认：

今天。

成功后：

Production.status = ENDED
Production.endedOn = endedOn

不要创建 EndRecord 表。

`endedOn` 不能晚于今天，必须满足：

- `endedOn >= startedOn`；
- `endedOn` 不早于该 Production 已有关联农事和收获的业务日期。

---

## 21. 未收获也可以结束

允许：

开始种养
→
0 次 Harvest
→
结束

例如：

- 种植失败
- 作物清除
- 养殖中止

都属于合法业务。

---

## 22. 多次收获后结束

同样允许：

开始
→
Harvest A
→
Harvest B
→
Harvest C
→
结束

---

## 23. 是否已收获

不要保存：

is_harvested

是否采收通过：

是否存在 HarvestRecord

动态判断。

---

## 24. 已结束 Production

ENDED Production：

不能：

- 再次结束
- 新增正常 Harvest

对于是否允许补录历史记录：

MVP 默认不允许。

如果未来出现补录需求，再单独设计。

Production 结束后，其关联 FarmOperation 和 HarvestRecord 同时锁定，均不能新增、修改或删除。

---

## 25. Production WorkMethod 独立

例如：

开始种植：
MECHANICAL

施肥：
MANUAL

采收：
MECHANICAL

完全合法。

不要让 Production.workMethod 自动影响后续记录。

---

## 26. 同地块重复生产

例如：

1号大棚
Production A
黄瓜
已结束

之后：

Production B
黄瓜
ACTIVE

必须允许。

A 和 B 的：

FarmOperation
HarvestRecord

不能混淆。

---

## 27. 同地块多 ACTIVE Production

例如：

1号地块

Production A：
黄瓜

Production B：
生菜

都可以是 ACTIVE。

系统所有业务都必须正确处理该情况。

---

## 28. 时间校验与补录

进行中的 Production 允许补录过去数据，但所有时间都不得晚于当前时间。MVP 默认业务时区为 `Asia/Shanghai`。

| 记录 | 校验规则 |
| --- | --- |
| Production.startedOn | 不能晚于今天 |
| Production.endedOn | 不能晚于今天，且满足第 20 节约束 |
| 关联 Production 的 FarmOperation.operatedAt | 不早于 `startedOn`，不晚于当前时间 |
| HarvestRecord.harvestedAt | 不早于 `startedOn`，不晚于当前时间 |
| 纯地块 FarmOperation.operatedAt | 不晚于当前时间 |

API 的 datetime 使用带时区的 ISO 8601 格式。后端转换为 UTC 保存，返回时携带时区偏移。

---

## 29. 纠错与删除

MVP 支持有限纠错，不做审计日志、软删除或历史版本。

| 资源 | 允许的纠错规则 |
| --- | --- |
| Farm、Plot | 正常支持编辑 |
| ACTIVE Production | 可编辑普通字段；仅当没有关联农事和收获时，才可修改 `plotId`、`speciesId`、`startedOn` |
| ACTIVE Production 删除 | 仅在没有关联农事和收获时允许删除；有记录后只能结束 |
| FarmOperation | 可编辑、删除；关联 ENDED Production 时锁定 |
| HarvestRecord | 在 Production ACTIVE 时可编辑、删除；Production ENDED 后锁定 |

编辑 FarmOperation 和 HarvestRecord 不修改其原始 `created_at`；允许修改 `operator_id`，但必须重新校验新操作人属于资源所属 Farm。审计时间字段只更新 `updated_at`。
