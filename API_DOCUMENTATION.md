# 🏠 房源分析接口 API 文档

## 📋 接口信息

**接口**: `POST /analyze_room`  
**地址**: http://localhost:8000  
**功能**: 分析图片是否为房间，生成房源内容

---

## 📥 请求参数

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

- `whole_rent` - 整租 (适合家庭或长期居住)
- `centralized` - 集中式公寓 (适合年轻白领)
- `shared_rent` - 合租 (适合预算有限的租客)

---

## 📤 响应格式

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

## 🧪 使用示例

"url": ["https://i.epochtimes.com/assets/uploads/2023/12/id14128363-shutterstock_2276643691.jpg",
"https://www.google.com/imgres?q=%E6%88%BF%E9%97%B4&imgurl=https%3A%2F%2Fi.epochtimes.com%2Fassets%2Fuploads%2F2023%2F12%2Fid14128361-shutterstock_2082456313.jpg&imgrefurl=https%3A%2F%2Fwww.epochtimes.com%2Fgb%2F23%2F12%2F2%2Fn14128315.htm&docid=XL3-w2_x4rYuOM&tbnid=RhbSHXa0DUru9M&vet=12ahUKEwixtumj9buOAxVnsFYBHd2lH04QM3oECHwQAA..i&w=4000&h=2666&hcb=2&ved=2ahUKEwixtumj9buOAxVnsFYBHd2lH04QM3oECHwQAA",
"https://www.google.com/imgres?q=%E6%88%BF%E9%97%B4&imgurl=https%3A%2F%2Fwy-static.wenxiaobai.com%2Faigc-online%2Fdelogo_17f296e9-e55b-06ef-e405-11ac562d74d6.webp%3FratioWH%3D1.6100178890877%26type%3Dopt&imgrefurl=https%3A%2F%2Fwww.wenxiaobai.com%2Fapi%2Fexpends%2Fdetail%3Farticle%3D47d7274e-0c44-4a47-a147-0fc498211ccd&docid=FcXUzqaKZ3EB8M&tbnid=r_3zCyDNAcB8-M&vet=12ahUKEwixtumj9buOAxVnsFYBHd2lH04QM3oECFsQAA..i&w=900&h=559&hcb=2&ved=2ahUKEwixtumj9buOAxVnsFYBHd2lH04QM3oECFsQAA"
]

### 1. 分析单张图片

```bash
curl -X POST "http://localhost:8000/analyze_room" \
  -H "Content-Type: application/json" \
  -d '{
    "roomId": "room_001",
    "business_type": "whole_rent",
    "url": "https://i.epochtimes.com/assets/uploads/2023/12/id14128363-shutterstock_2276643691.jpg"
  }'
```

**响应示例：**

```json
{
  "success": true,
  "results": [
    {
      "url": "https://i.epochtimes.com/assets/uploads/2023/12/id14128363-shutterstock_2276643691.jpg",
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
    "roomId": "room_0223302",
    "business_type": "centralized",
    "url":["https://i.epochtimes.com/assets/uploads/2023/12/id14128363-shutterstock_2276643691.jpg",
        "https://www.google.com/imgres?q=%E6%88%BF%E9%97%B4&imgurl=https%3A%2F%2Fi.epochtimes.com%2Fassets%2Fuploads%2F2023%2F12%2Fid14128361-shutterstock_2082456313.jpg&imgrefurl=https%3A%2F%2Fwww.epochtimes.com%2Fgb%2F23%2F12%2F2%2Fn14128315.htm&docid=XL3-w2_x4rYuOM&tbnid=RhbSHXa0DUru9M&vet=12ahUKEwixtumj9buOAxVnsFYBHd2lH04QM3oECHwQAA..i&w=4000&h=2666&hcb=2&ved=2ahUKEwixtumj9buOAxVnsFYBHd2lH04QM3oECHwQAA",
        "https://www.google.com/imgres?q=%E6%88%BF%E9%97%B4&imgurl=https%3A%2F%2Fwy-static.wenxiaobai.com%2Faigc-online%2Fdelogo_17f296e9-e55b-06ef-e405-11ac562d74d6.webp%3FratioWH%3D1.6100178890877%26type%3Dopt&imgrefurl=https%3A%2F%2Fwww.wenxiaobai.com%2Fapi%2Fexpends%2Fdetail%3Farticle%3D47d7274e-0c44-4a47-a147-0fc498211ccd&docid=FcXUzqaKZ3EB8M&tbnid=r_3zCyDNAcB8-M&vet=12ahUKEwixtumj9buOAxVnsFYBHd2lH04QM3oECFsQAA..i&w=900&h=559&hcb=2&ved=2ahUKEwixtumj9buOAxVnsFYBHd2lH04QM3oECFsQAA"
        ]
  }'
```

**响应示例：**

```json
{
  "success": true,
  "results": [
    {
      "url": "https://i.epochtimes.com/assets/uploads/2023/12/id14128363-shutterstock_2276643691.jpg",
      "success": true,
      "is_room": true,
      "error": null
    },
    {
      "url": "https://www.google.com/imgres?q=%E6%88%BF%E9%97%B4&imgurl=https%3A%2F%2Fi.epochtimes.com%2Fassets%2Fuploads%2F2023%2F12%2Fid14128361-shutterstock_2082456313.jpg&imgrefurl=https%3A%2F%2Fwww.epochtimes.com%2Fgb%2F23%2F12%2F2%2Fn14128315.htm&docid=XL3-w2_x4rYuOM&tbnid=RhbSHXa0DUru9M&vet=12ahUKEwixtumj9buOAxVnsFYBHd2lH04QM3oECHwQAA..i&w=4000&h=2666&hcb=2&ved=2ahUKEwixtumj9buOAxVnsFYBHd2lH04QM3oECHwQAA",
      "success": true,
      "is_room": false,
      "error": null
    },
    {
      "url": "https://www.google.com/imgres?q=%E6%88%BF%E9%97%B4&imgurl=https%3A%2F%2Fwy-static.wenxiaobai.com%2Faigc-online%2Fdelogo_17f296e9-e55b-06ef-e405-11ac562d74d6.webp%3FratioWH%3D1.6100178890877%26type%3Dopt&imgrefurl=https%3A%2F%2Fwww.wenxiaobai.com%2Fapi%2Fexpends%2Fdetail%3Farticle%3D47d7274e-0c44-4a47-a147-0fc498211ccd&docid=FcXUzqaKZ3EB8M&tbnid=r_3zCyDNAcB8-M&vet=12ahUKEwixtumj9buOAxVnsFYBHd2lH04QM3oECFsQAA..i&w=900&h=559&hcb=2&ved=2ahUKEwixtumj9buOAxVnsFYBHd2lH04QM3oECFsQAA",
      "success": true,
      "is_room": true,
      "error": null
    }
  ]
}
```

---

## 📊 生成的内容

如果识别为房间，会异步生成四大维度内容：

```json
{
  "lighting_comfort": "采光与居住舒适度",
  "decoration_quality": "装修品质与维护状况",
  "space_layout": "空间感与布局",
  "appliances_facilities": "电器与设施"
}
```

### 内容字段说明

| 字段名                  | 描述               | 内容范围                                     |
| ----------------------- | ------------------ | -------------------------------------------- |
| `lighting_comfort`      | 采光与居住舒适度   | 自然采光、通风条件、舒适度评估、朝向优势     |
| `decoration_quality`    | 装修品质与维护状况 | 装修风格、墙面地面状况、维护保养、整体美观度 |
| `space_layout`          | 空间感与布局       | 空间大小、功能布局、储物空间、动线规划       |
| `appliances_facilities` | 电器与设施         | 基础电器、生活设施、智能化程度、便利性       |

---

## 🔄 处理流程

1. **立即返回**: 房间识别结果 (2-3 秒)
2. **异步处理**: 生成房源内容 (10-15 秒)
3. **状态查询**: `GET /status/{room_id}` 获取最终结果

---

## ⚠️ 错误响应

```json
{
  "success": false,
  "error": "错误信息",
  "error_type": "错误类型"
}
```

### 常见错误类型

| 错误类型           | 描述            | 解决方案                |
| ------------------ | --------------- | ----------------------- |
| `ValidationError`  | 参数验证失败    | 检查必填字段和格式      |
| `RequestException` | 图片下载失败    | 检查图片 URL 是否可访问 |
| `JSONDecodeError`  | AI 响应解析失败 | 系统会自动重试          |
| `TimeoutError`     | 请求超时        | 检查网络连接            |

---
