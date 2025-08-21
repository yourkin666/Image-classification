# 🏠 房源分析接口 API 文档

## 📋 接口概览

基于 Gemini AI 的智能房源图片分析系统，支持房间识别和四大维度内容生成。

**服务地址**: http://localhost:8000  
**API 版本**: v1

---

## 🔍 接口列表

### 1. 房源分析接口

- **接口**: `POST /analyze_room`
- **功能**: 分析图片是否为房间，异步生成房源内容

### 2. 处理状态查询接口

- **接口**: `GET /status/{room_id}`
- **功能**: 查询异步处理状态和生成的内容

---

## 📥 房源分析接口

### 请求参数

```json
{
  "roomId": "房间ID",
  "business_type": "业务类型",
  "url": "图片URL或URL数组"
}
```

### 字段说明

| 字段名          | 类型               | 必填 | 描述                         | 示例值                            |
| --------------- | ------------------ | ---- | ---------------------------- | --------------------------------- |
| `roomId`        | string             | ✅   | 房间唯一标识符，用于后续查询 | `"room_001"`                      |
| `business_type` | string             | ✅   | 业务类型，影响生成内容的风格 | `"whole_rent"`                    |
| `url`           | string \| string[] | ✅   | 图片 URL，支持单张或批量分析 | `"https://example.com/image.jpg"` |

### 业务类型

| 类型值        | 描述       | 适用场景           |
| ------------- | ---------- | ------------------ |
| `whole_rent`  | 整租       | 适合家庭或长期居住 |
| `centralized` | 集中式公寓 | 适合年轻白领       |
| `shared_rent` | 合租       | 适合预算有限的租客 |

### 响应格式

```json
{
  "success": true,
  "results": [
    {
      "url": "https://example.com/image1.jpg",
      "success": true,
      "is_room": true,
      "error": null
    },
    {
      "url": "https://example.com/image2.jpg",
      "success": true,
      "is_room": false,
      "error": null
    }
  ]
}
```

### 响应字段说明

| 字段名    | 类型    | 描述                   | 示例值     |
| --------- | ------- | ---------------------- | ---------- |
| `success` | boolean | 请求是否成功           | `true`     |
| `results` | array   | 每张图片的具体检测结果 | 见下方说明 |

### results 数组字段说明

| 字段名    | 类型            | 描述                 | 示例值                            |
| --------- | --------------- | -------------------- | --------------------------------- |
| `url`     | string          | 原始图片 URL         | `"https://example.com/image.jpg"` |
| `success` | boolean         | 该图片处理是否成功   | `true`                            |
| `is_room` | boolean \| null | 该图片是否识别为房间 | `true`                            |
| `error`   | string \| null  | 处理错误信息         | `null`                            |

---

## 📊 处理状态查询接口

### 请求格式

```bash
GET /status/{room_id}
```

### 路径参数

| 参数名    | 类型   | 必填 | 描述    | 示例值       |
| --------- | ------ | ---- | ------- | ------------ |
| `room_id` | string | ✅   | 房间 ID | `"room_001"` |

### 响应格式

```json
{
  "success": true,
  "room_id": "room_001",
  "business_type": "whole_rent",
  "processing_status": "completed",
  "content": {
    "lighting_comfort": "阳光充足,视野开阔,居住舒适度极佳",
    "decoration_quality": "装修品质上乘,维护良好,整体美观大气",
    "space_layout": "空间宽敞,布局合理,功能分区明确",
    "appliances_facilities": "电器设施齐全,生活便利,智能化程度高"
  },
  "created_at": "2025-01-21T14:32:10",
  "updated_at": "2025-01-21T14:43:11"
}
```

### 响应字段说明

| 字段名              | 类型    | 描述                     | 示例值                  |
| ------------------- | ------- | ------------------------ | ----------------------- |
| `success`           | boolean | 请求是否成功             | `true`                  |
| `room_id`           | string  | 房间 ID                  | `"room_001"`            |
| `business_type`     | string  | 业务类型                 | `"whole_rent"`          |
| `processing_status` | string  | 处理状态                 | `"completed"`           |
| `content`           | object  | 生成的内容（完成时返回） | 见下方说明              |
| `created_at`        | string  | 创建时间                 | `"2025-01-21T14:32:10"` |
| `updated_at`        | string  | 更新时间                 | `"2025-01-21T14:43:11"` |

### 处理状态说明

| 状态值       | 描述     | 说明                 |
| ------------ | -------- | -------------------- |
| `pending`    | 等待处理 | 任务已创建，等待处理 |
| `processing` | 处理中   | 正在生成内容         |
| `completed`  | 处理完成 | 内容生成完成         |
| `failed`     | 处理失败 | 内容生成失败         |

### content 字段说明

| 字段名                  | 描述               | 内容范围                                     |
| ----------------------- | ------------------ | -------------------------------------------- |
| `lighting_comfort`      | 采光与居住舒适度   | 自然采光、通风条件、舒适度评估、朝向优势     |
| `decoration_quality`    | 装修品质与维护状况 | 装修风格、墙面地面状况、维护保养、整体美观度 |
| `space_layout`          | 空间感与布局       | 空间大小、功能布局、储物空间、动线规划       |
| `appliances_facilities` | 电器与设施         | 基础电器、生活设施、智能化程度、便利性       |

---

## 🧪 使用示例

### 1. 分析单张图片

```bash
curl -X POST "http://localhost:8000/analyze_room" \
  -H "Content-Type: application/json" \
  -d '{
    "roomId": "room_001",
    "business_type": "whole_rent",
    "url": "https://example.com/image.jpg"
  }'
```

**响应示例：**

```json
{
  "success": true,
  "results": [
    {
      "url": "https://example.com/image.jpg",
      "success": true,
      "is_room": true,
      "error": null
    }
  ]
}
```

### 2. 批量分析

```bash
curl -X POST "http://localhost:8000/analyze_room" \
  -H "Content-Type: application/json" \
  -d '{
    "roomId": "room_002",
    "business_type": "centralized",
    "url": [
      "https://example.com/image1.jpg",
      "https://example.com/image2.jpg"
    ]
  }'
```

**响应示例：**

```json
{
  "success": true,
  "results": [
    {
      "url": "https://example.com/image1.jpg",
      "success": true,
      "is_room": true,
      "error": null
    },
    {
      "url": "https://example.com/image2.jpg",
      "success": true,
      "is_room": false,
      "error": null
    }
  ]
}
```

### 3. 查询处理状态

```bash
curl -X GET "http://localhost:8000/status/room_001"
```

**响应示例：**

```json
{
  "success": true,
  "room_id": "room_001",
  "business_type": "whole_rent",
  "processing_status": "completed",
  "content": {
    "lighting_comfort": "阳光充足,视野开阔,居住舒适度极佳",
    "decoration_quality": "装修品质上乘,维护良好,整体美观大气",
    "space_layout": "空间宽敞,布局合理,功能分区明确",
    "appliances_facilities": "电器设施齐全,生活便利,智能化程度高"
  },
  "created_at": "2025-01-21T14:32:10",
  "updated_at": "2025-01-21T14:43:11"
}
```

---

## 🔄 处理流程

1. **立即返回**: 房间识别结果 (2-3 秒)
2. **异步处理**: 生成房源内容 (10-15 秒)
3. **状态查询**: `GET /status/{room_id}` 获取最终结果

### 完整使用流程

```bash
# 1. 提交分析请求
POST /analyze_room

# 2. 轮询查询状态（可选）
GET /status/{room_id}

# 3. 获取最终结果
GET /status/{room_id}
```

---

## ⚠️ 错误处理

### 错误响应格式

```json
{
  "success": false,
  "error": "错误信息",
  "error_type": "错误类型",
  "request_id": "请求唯一标识"
}
```

### 常见错误类型

| 错误类型           | HTTP 状态码 | 描述            | 解决方案                |
| ------------------ | ----------- | --------------- | ----------------------- |
| `ValidationError`  | 400         | 参数验证失败    | 检查必填字段和格式      |
| `RequestException` | 400         | 图片下载失败    | 检查图片 URL 是否可访问 |
| `JSONDecodeError`  | 500         | AI 响应解析失败 | 系统会自动重试          |
| `TimeoutError`     | 500         | 请求超时        | 检查网络连接            |
| `NotFound`         | 404         | 房间 ID 不存在  | 检查房间 ID 是否正确    |

### 错误示例

```json
{
  "success": false,
  "error": "URL参数必须是字符串或数组",
  "error_type": "ValidationError",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

## 📝 注意事项

1. **图片格式**: 支持常见的图片格式 (JPG, PNG, WEBP 等)
2. **URL 要求**: 图片 URL 必须可直接访问
3. **批量限制**: 建议单次请求不超过 10 张图片
4. **异步处理**: 内容生成是异步的，需要查询状态获取结果
5. **数据存储**: 处理结果会存储在数据库中，支持重复查询
