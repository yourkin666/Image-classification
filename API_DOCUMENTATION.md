# 图片房间分类服务 API 文档

## 概述

图片房间分类服务是一个基于Gemini AI的API，用于分析图片是否为房间并识别房间类型。该服务可以接受图片URL，并返回关于图片内容的结构化分析结果。

- **版本**：1.0.0
- **基础URL**：`http://47.236.238.112`
- **服务描述**：使用Gemini AI分析图片是否为房间并识别房间类型

## API 端点

### 1. 健康检查

检查服务的运行状态。

**请求**：
- **方法**：`GET`
- **路径**：`/health`

**响应**：
```json
{
    "status": "healthy",
    "service": "image-room-classifier"
}
```

**状态码**：
- `200 OK`：服务正常运行

### 2. 分析房间

分析图片是否为房间，并可选择性地返回详细描述。

**请求**：
- **方法**：`POST`
- **路径**：`/analyze_room`
- **内容类型**：`application/json`

**请求参数**：

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|------|------|
| url | string 或 string[] | 是 | - | 图片URL或图片URL数组 |
| include_description | boolean | 否 | true | 是否在结果中包含详细描述 |

**请求体示例**：
```json
{
    "url": "https://example.com/image.jpg",
    "include_description": true
}
```

或者批量处理多个图片：
```json
{
    "url": [
        "https://example.com/image1.jpg",
        "https://example.com/image2.jpg"
    ],
    "include_description": true
}
```

**响应**：
```json
{
    "success": true,
    "total": 1,
    "processing_time": "1.25秒",
    "results": [
        {
            "url": "https://example.com/image.jpg",
            "actual_url": null,
            "success": true,
            "is_room": true,
            "description": {
                "room_type": "客厅",
                "basic_info": "现代风格的客厅，宽敞明亮，采用开放式布局",
                "features": "配有舒适的沙发、茶几和电视墙，整体色调温馨"
            }
        }
    ]
}
```

**响应字段说明**：

| 字段名 | 类型 | 描述 |
|------|------|------|
| success | boolean | 整体请求是否成功 |
| total | integer | 处理的图片数量 |
| processing_time | string | 总处理时间 |
| results | array | 结果数组，每个图片一个结果对象 |

**结果对象字段**：

| 字段名 | 类型 | 描述 |
|------|------|------|
| url | string | 原始请求URL |
| actual_url | string | 实际处理的URL（如果从Google图片搜索中提取） |
| success | boolean | 此图片处理是否成功 |
| is_room | boolean | 图片是否为房间 |
| description | object | 房间描述（当include_description=true时） |

**描述对象字段**：

| 字段名 | 类型 | 描述 |
|------|------|------|
| room_type | string | 房间类型，可能的值："客厅", "家庭室", "餐厅", "厨房", "主卧室", "卧室", "客房", "卫生间", "浴室", "书房", "家庭办公室", "洗衣房", "储藏室", "食品储藏间", "玄关", "门厅", "走廊", "阳台", "地下室", "阁楼", "健身房", "家庭影院", "游戏室", "娱乐室", "其他" |
| basic_info | string | 房间基本信息描述 |
| features | string | 房间的显著特点 |

**错误响应示例**：
```json
{
    "success": false,
    "error": "URL参数必须是字符串或数组"
}
```

或者单个图片处理失败：
```json
{
    "success": true,
    "total": 1,
    "processing_time": "0.50秒",
    "results": [
        {
            "url": "https://invalid-url.com/image.jpg",
            "success": false,
            "error": "网络请求失败: 404 Client Error: Not Found"
        }
    ]
}
```

**状态码**：
- `200 OK`：请求处理成功（即使某些图片处理失败）
- `400 Bad Request`：请求参数错误
- `500 Internal Server Error`：服务器内部错误

## 使用示例

### curl 示例

**1. 健康检查**：
```bash
curl -X GET http://47.236.238.112/health
```

**2. 分析单张图片**：
```bash
curl -X POST \
  http://47.236.238.112/analyze_room \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/image.jpg",
    "include_description": true
  }'
```

**3. 批量分析多张图片**：
```bash
curl -X POST \
  http://47.236.238.112/analyze_room \
  -H "Content-Type: application/json" \
  -d '{
    "url": [
      "https://example.com/image1.jpg",
      "https://example.com/image2.jpg"
    ],
    "include_description": true
  }'
```

### Python 示例

```python
import requests
import json

# 分析单张图片
def analyze_single_image(url):
    api_url = "http://47.236.238.112/analyze_room"
    payload = {
        "url": url,
        "include_description": True
    }
    
    response = requests.post(api_url, json=payload)
    return response.json()

# 分析多张图片
def analyze_multiple_images(urls):
    api_url = "http://47.236.238.112/analyze_room"
    payload = {
        "url": urls,
        "include_description": True
    }
    
    response = requests.post(api_url, json=payload)
    return response.json()

# 使用示例
single_result = analyze_single_image("https://example.com/image.jpg")
print(json.dumps(single_result, indent=2, ensure_ascii=False))

multiple_results = analyze_multiple_images([
    "https://example.com/image1.jpg",
    "https://example.com/image2.jpg"
])
print(json.dumps(multiple_results, indent=2, ensure_ascii=False))
```

## 限制和注意事项

1. **并发限制**：
   - 服务配置了最大并发下载数和最大并发分析数
   - 默认最大并发下载数：5
   - 默认最大并发分析数：3

2. **超时设置**：
   - 下载超时时间默认为15秒

3. **支持的图片格式**：
   - JPEG/JPG
   - PNG
   - GIF
   - WebP
   - BMP
   - TIFF

4. **URL要求**：
   - 必须是公网可访问的有效图片URL
   - 支持从Google图片搜索URL中提取实际图片URL

5. **响应时间**：
   - 图片处理时间与图片大小、复杂度和服务器负载有关
   - 批量处理多张图片时，处理是并行的，但受并发限制

## 错误码和故障排除

| 错误描述 | 可能原因 | 解决方案 |
|---------|---------|---------|
| URL参数必须是字符串或数组 | 传递了无效的URL格式 | 检查请求参数格式 |
| 图片URL不能为空 | URL参数为空 | 提供有效的图片URL |
| 网络请求失败 | 图片URL无法访问或超时 | 检查URL是否有效并可公网访问 |
| 无法从Google搜索URL中提取图片URL | Google搜索URL格式不正确 | 使用直接的图片URL |
| 不支持的MIME类型 | 图片格式不受支持 | 使用支持的图片格式 |
| 图片分析失败 | AI分析过程出错 | 尝试不同的图片或稍后重试 |

## API变更历史

### 版本1.0.0
- 初始版本
- 支持分析单张和多张图片
- 支持房间类型识别和描述 