# 产品与物模型 CRUD 接口文档

> 智慧农业环境监控平台 · F2 产品管理 / F3 物模型
> 后端：Flask + Flask-SQLAlchemy + Flask-JWT-Extended
> 代码位置：`app/api/product.py`（`product_bp`，URL 前缀 `/api/products`）

---

## 1. 通用说明

- **Base URL**：`http://<host>:5000`
- **认证**：所有接口需在请求头携带 JWT：
  ```
  Authorization: Bearer <access_token>
  ```
  获取方式见《需求清单初稿》F1：先 `POST /api/auth/register` 注册，再 `POST /api/auth/login` 取 `access_token`。
- **Content-Type**：`application/json`（POST/PUT 请求）
- **时间格式**：ISO 8601 字符串
- **统一响应**：成功返回 JSON 数据；失败返回 `{"msg": "错误信息"}` 及对应状态码。

### 错误码速查
| 状态码 | 含义 |
|--------|------|
| 400 | 参数缺失 / 格式错误 |
| 401 | 未携带 / 过期 / 非法的 JWT |
| 404 | 资源不存在（产品 / 属性 / 服务 / 事件 ID 错误） |
| 409 | 冲突（如 `product_key` / `identifier` 已存在） |
| 500 | 服务器内部错误 |

---

## 2. 产品（Product）接口

### 2.1 产品列表 `GET /api/products`
查询参数：`page`(默认1)、`per_page`(默认20，最大100)、`keyword`(按名称/标识模糊搜)。

响应 200：
```json
{
  "items": [
    {"id":1,"product_key":"env_ctrl","product_name":"智能环境测控仪",
     "description":"...","protocol":"MQTT","created_at":"...","updated_at":"..."}
  ],
  "total": 1, "page": 1, "per_page": 20, "pages": 1
}
```

### 2.2 创建产品 `POST /api/products`
请求体：
```json
{
  "product_key": "env_ctrl",
  "product_name": "智能环境测控仪",
  "description": "集数据采集与设备控制于一体的农业物联网终端",
  "protocol": "MQTT",
  "thing_model": { "note": "完整物模型快照，可在此直接写入" }
}
```
响应 201：`{"msg":"创建成功","product":{...}}` ；`product_key` 重复返回 409。

### 2.3 产品详情 `GET /api/products/<pid>`
响应 200：返回产品全部字段 + `thing_model` + `properties`/`services`/`events` 数组（含完整物模型）。

### 2.4 更新产品 `PUT /api/products/<pid>`
请求体（仅传需改字段）：
```json
{ "product_name": "智能环境测控仪-改", "thing_model": {"k":"v"} }
```
响应 200：`{"msg":"更新成功","product":{...}}`。

### 2.5 删除产品 `DELETE /api/products/<pid>`
响应 200：`{"msg":"删除成功"}`。**级联删除**该产品的全部属性 / 服务 / 事件定义。

---

## 3. 物模型聚合 `GET /api/products/<pid>/thing-model`

前端一次加载用。响应 200：
```json
{
  "product_key": "env_ctrl",
  "product_name": "智能环境测控仪",
  "thing_model": { "...": "..." },
  "properties": [ {"id":1,"identifier":"air_temperature",...} ],
  "services":   [ {"id":1,"identifier":"set_fan",...} ],
  "events":     [ {"id":1,"identifier":"temp_alarm",...} ]
}
```

---

## 4. 物模型-属性（Property）接口

路径前缀：`/api/products/<pid>/properties`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 列出该产品全部属性 |
| POST | `/` | 新增属性 |
| PUT | `/<tid>` | 更新某属性 |
| DELETE | `/<tid>` | 删除某属性 |

**POST 请求体**：
```json
{ "property_name":"空气温度", "identifier":"air_temperature",
  "data_type":"float", "unit":"°C", "access_mode":"r", "description":"传感器采集上报" }
```
- 必填：`property_name`、`identifier`、`data_type`；缺则返回 400。
- `identifier` 同一产品内唯一，重复返回 409。
- `access_mode` 取值 `r` / `rw`。
- 响应 201：`{"msg":"创建成功","property":{...}}`。

**PUT 请求体**（部分更新）：`{"unit":"lx"}` 等。

---

## 5. 物模型-服务（Service）接口

路径前缀：`/api/products/<pid>/services`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 列出服务 |
| POST | `/` | 新增服务 |
| PUT | `/<tid>` | 更新服务 |
| DELETE | `/<tid>` | 删除服务 |

**POST 请求体**：
```json
{ "service_name":"风机控制", "identifier":"set_fan",
  "input_params":{"fan_state":"bool"}, "output_params":{"result":"string"},
  "description":"远程开/关风机" }
```
- 必填：`service_name`、`identifier`。

---

## 6. 物模型-事件（Event）接口

路径前缀：`/api/products/<pid>/events`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 列出事件 |
| POST | `/` | 新增事件 |
| PUT | `/<tid>` | 更新事件 |
| DELETE | `/<tid>` | 删除事件 |

**POST 请求体**：
```json
{ "event_name":"温度超限告警", "identifier":"temp_alarm",
  "trigger_position":"设备端",
  "output_params":{"temperature":"float","threshold":"float","timestamp":"string"},
  "trigger_condition":"温度 > 本地存储阈值" }
```
- 必填：`event_name`、`identifier`。

---

## 7. 调用示例（curl）

```bash
# 1) 登录拿 token
TOKEN=$(curl -s -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"apitest","password":"apitest123"}' | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# 2) 创建产品
curl -s -X POST http://127.0.0.1:5000/api/products \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"product_key":"env_ctrl","product_name":"智能环境测控仪","protocol":"MQTT"}'

# 3) 给产品加一个属性
curl -s -X POST http://127.0.0.1:5000/api/products/1/properties \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"property_name":"空气温度","identifier":"air_temperature","data_type":"float","unit":"°C","access_mode":"r"}'

# 4) 一次加载完整物模型
curl -s http://127.0.0.1:5000/api/products/1/thing-model \
  -H "Authorization: Bearer $TOKEN"
```

---

## 8. 实现要点与约定

- **模型层**：`app/models/product.py` 中 `Product` 与 `ProductProperty/Service/Event` 通过 `relationship(cascade="all, delete-orphan")` 关联，删除产品自动级联清理物模型。
- **双写一致性**：更新物模型时，若同时维护 `thing_model` JSON 与关系表，请保证两边一致（建议在服务层封装统一的"保存物模型"方法，后续可加校验）。
- **鉴权**：当前所有接口均 `@jwt_required()`；F9 RBAC 角色校验可在本蓝图层叠加（如限制仅 `admin` 可写）。
- **分页**：列表接口统一返回 `items/total/page/per_page/pages` 结构，便于前端分页组件对接。
