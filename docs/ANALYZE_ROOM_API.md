## 房源图片分析 API（简版）

- POST `/analyze_room`
- 作用：识别图片是否为房间；若存在房间，后台异步生成“特征JSON”并入库。

请求体
```json
{
  "roomId": "string",
  "business_type": "whole_rent | centralized | shared_rent",
  "url": "string | string[]"
}
```

成功响应（示例）
```json
{
  "success": true,
  "results": [
    { "url": "https://...jpg", "success": true, "is_room": true, "error": null }
  ],
  "error": null
}
```

curl（单图）
```bash
curl -X POST 'http://127.0.0.1:8001/analyze_room' \
  -H 'Content-Type: application/json' \
  -d '{
    "roomId": "room_demo_001",
    "business_type": "whole_rent",
    "url": "https://picsum.photos/seed/101/640"
  }'
```

### 2) 状态查询
- GET `/status/{room_id}`
- 作用：查询异步处理结果；完成后 `content` 返回“特征JSON”。

成功响应（示例）
```json
{
  "success": true,
  "room_id": "room_demo_001",
  "business_type": "whole_rent",
  "processing_status": "completed",
  "content": {
    "阳台": false, "独卫": true, "飘窗": false, "开间": false, "loft": false,
    "马桶": true, "蹲便": false, "上下铺": false, "精装": true
  },
  "error": null
}
```

curl
```bash
curl -X GET 'http://127.0.0.1:8001/status/room_demo_001'
```

### 特征JSON 字段
`阳台`、`独卫`、`飘窗`、`开间`、`loft`、`马桶`、`蹲便`、`上下铺`、`精装`（默认 false，识别为 true）。

### 返回码
- 200：成功；400/422：参数错误；404：roomId 不存在；500：服务内部错误。

## 分析房间内容统一接口文档

- 接口地址: POST /analyze_room
- 说明: 触发“房间图片识别（不变）+ 内容生成阶段（已改造为特征JSON存储）”的流程。对外响应结构与改造前一致，仅内部 content 改为特征JSON存储。当前仅此一个对外接口。

### 认证
- 无（按实际部署增加鉴权方案）

### 请求头
- Content-Type: application/json

### 请求体
```json
{
  "rooms": [
    {
      "roomId": "1",
      "businessType": "whole_rent",
      "imageUrl": "http://example.com/image1.jpg"
    }
  ]
}
```

- rooms: 数组，至少1个、最多100个
  - roomId: string，业务侧房间ID
  - businessType: string，业务类型，取值：whole_rent | centralized | shared_rent
  - imageUrl: string，图片URL

### 成功响应（200）
```json
{
  "success": true,
  "results": [
    {
      "url": "http://example.com/image1.jpg",
      "success": true,
      "is_room": true,
      "error": null
    },
    {
      "url": "http://example.com/image2.jpg",
      "success": true,
      "is_room": false,
      "error": null
    }
  ]
}
```
- success: 是否处理成功
- results[i]: 每张图片的识别结果（识别阶段返回）。当任一图片识别为房间(is_room=true)时，后端会异步触发内容生成并入库（不影响此同步响应）。

说明：
- 对外响应结构与改造前一致。内部 content 已改为如下“特征JSON”结构存储（异步生成，不在本响应中返回）：
  ```json
  {
    "阳台": false,
    "独卫": false,
    "飘窗": false,
    "开间": false,
    "loft": false,
    "马桶": false,
    "蹲便": false,
    "上下铺": false,
    "精装": false
  }
  ```
- 特征JSON写入数据库表 `qft_ai_room_analysis.content`（text）。

### 失败响应（4xx/5xx）
```json
{
  "success": false,
  "results": [],
  "error": "错误信息"
}
```

### 示例
- 单个房间
```bash
curl -X POST "http://localhost/analyze_room" \
  -H "Content-Type: application/json" \
  -d '{
    "rooms": [
      {
        "roomId": "1",
        "businessType": "whole_rent",
        "imageUrl": "http://example.com/image1.jpg"
      }
    ]
  }'
```

- 批量房间
```bash
curl -X POST "http://localhost/analyze_room" \
  -H "Content-Type: application/json" \
  -d '{
    "rooms": [
      {"roomId": "1", "businessType": "whole_rent", "imageUrl": "http://example.com/image1.jpg"},
      {"roomId": "2", "businessType": "centralized", "imageUrl": "http://example.com/image2.jpg"},
      {"roomId": "3", "businessType": "shared_rent", "imageUrl": "http://example.com/image3.jpg"}
    ]
  }'
```

### 业务流说明
1) 网关调用 /analyze_room → 参数校验 → 进入识别阶段（不变）
2) 同步返回逐图片识别结果（success、is_room、error）
3) 若任一图片识别为房间，异步触发“内容生成阶段” → 生成特征JSON → 写入数据库

### 约束与建议
- 图片URL需可公网访问，建议HTTPS
- rooms上限建议≤100；图片大小与数量越多，整体处理耗时越长
- businessType 取值固定：whole_rent / centralized / shared_rent
- 查询接口不对外提供，如需状态可由调用方直接查询数据库（is_delete=0）或自建查询链路

### 变更兼容性
- 对外响应保持与改造前一致（success + results[逐图片]）
- 仅 content 的内部结构改为“特征JSON”并存表，旧逻辑不再生成自然语言描述
