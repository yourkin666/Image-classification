# 🏠 房源分析接口 API 文档

## 📋 接口信息

**接口**: `POST /analyze_room`  
**地址**: http://localhost:8000  
**功能**: 分析图片是否为房间，异步生成房源内容

---

## 📥 请求参数

### 请求格式

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

| 类型值        | 描述       | 适用场景           | 内容风格特点                     |
| ------------- | ---------- | ------------------ | -------------------------------- |
| `whole_rent`  | 整租       | 适合家庭或长期居住 | 注重空间感、舒适度、家庭生活便利 |
| `centralized` | 集中式公寓 | 适合年轻白领       | 强调现代化、智能化、社交便利     |
| `shared_rent` | 合租       | 适合预算有限的租客 | 突出性价比、基础功能、实用性     |

---

## 📤 响应格式

### 成功响应

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

### 错误响应

```json
{
  "success": false,
  "error": "错误信息",
  "error_type": "错误类型",
  "request_id": "请求唯一标识"
}
```

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
      "https://example.com/image2.jpg",
      "https://example.com/image3.jpg"
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
    },
    {
      "url": "https://example.com/image3.jpg",
      "success": true,
      "is_room": true,
      "error": null
    }
  ]
}
```


## 🔄 处理流程

### 1. 房间识别阶段

- **处理时间**: 2-3 秒
- **返回内容**: 每张图片是否为房间的判断结果
- **处理方式**: 同步处理，立即返回结果

### 2. 内容生成阶段

- **处理时间**: 10-15 秒
- **返回内容**: 四大维度房源内容
- **处理方式**: 异步处理，需要查询状态获取结果

## ⚠️ 错误处理

### 常见错误类型

| 错误类型           | HTTP 状态码 | 描述            | 解决方案                |
| ------------------ | ----------- | --------------- | ----------------------- |
| `ValidationError`  | 400         | 参数验证失败    | 检查必填字段和格式      |
| `RequestException` | 400         | 图片下载失败    | 检查图片 URL 是否可访问 |
| `JSONDecodeError`  | 500         | AI 响应解析失败 | 系统会自动重试          |
| `TimeoutError`     | 500         | 请求超时        | 检查网络连接            |

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

## 📊 房间识别规则

### 房间定义

房间定义为建筑物内部空间，用于人类居住或活动。

### 支持的房间类型

- **居住空间**: 客厅、卧室、书房
- **功能空间**: 厨房、卫生间、餐厅
- **过渡空间**: 阳台、走廊、玄关
- **其他空间**: 衣帽间、储物间等

### 识别标准

- 具有明确的室内空间特征
- 包含居住或活动所需的基础设施
- 具有合理的空间布局和功能分区

---

## 📝 使用注意事项

### 1. 图片要求

- **格式支持**: JPG, PNG, WEBP, GIF 等常见格式
- **URL 要求**: 图片 URL 必须可直接访问
- **图片质量**: 建议分辨率不低于 640x480
- **内容要求**: 图片应清晰展示房间内部空间

### 2. 批量处理

- **数量限制**: 建议单次请求不超过 10 张图片
- **处理顺序**: 图片按数组顺序处理
- **错误处理**: 单个图片失败不影响其他图片处理
- **并发处理**: 支持多张图片并发分析

### 3. 业务类型选择

- **整租 (whole_rent)**: 适合家庭居住，注重空间感和舒适度
- **集中式公寓 (centralized)**: 适合年轻白领，强调现代化和便利性
- **合租 (shared_rent)**: 适合预算有限，突出实用性和性价比

### 4. 异步处理

- **立即返回**: 房间识别结果立即返回
- **后台处理**: 内容生成在后台异步进行
- **状态查询**: 需要通过状态查询接口获取最终内容
- **数据存储**: 处理结果存储在数据库中，支持重复查询

---

## 🔗 相关接口

- **状态查询**: `GET /status/{room_id}` - 查询处理状态和生成内容
- **完整文档**: [API_DOCUMENTATION.md](../API_DOCUMENTATION.md) - 查看完整 API 文档
