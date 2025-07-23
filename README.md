# Image Room Classification Service

使用 Gemini AI 分析图片是否为房间并识别房间类型的 FastAPI 服务。

## 🏗️ 项目结构

```
Image-classification/
├── app/                          # 应用主目录
│   ├── __init__.py
│   ├── main.py                   # FastAPI应用入口
│   ├── api/                      # API路由层
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py         # 路由汇总
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── analyze.py    # 图像分析接口

│   ├── core/                     # 核心配置和基础设施
│   │   ├── __init__.py
│   │   ├── config.py             # 配置管理
│   │   ├── logging.py            # 日志配置
│   │   └── middleware.py         # 中间件
│   ├── services/                 # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── image_service.py      # 图像处理服务
│   │   └── gemini_service.py     # Gemini AI服务
│   ├── utils/                    # 工具函数
│   │   ├── __init__.py
│   │   ├── decorators.py         # 性能监控装饰器
│   │   ├── image_utils.py        # 图像工具
│   │   └── url_utils.py          # URL处理工具
│   └── schemas/                  # 数据模型
│       ├── __init__.py
│       └── requests.py           # 请求/响应模型
├── tests/                        # 测试目录
│   └── __init__.py
├── scripts/                      # 脚本目录
│   ├── start_service.sh          # 启动服务脚本
│   ├── stop_service.sh           # 停止服务脚本
│   └── check_logs.sh             # 日志检查脚本
├── logs/                         # 日志目录
├── docs/                         # 文档目录
├── .env.example                  # 环境变量示例
├── .gitignore
├── requirements.txt
├── ecosystem.config.js           # PM2配置
└── README.md
```

## 🚀 Production Deployment with Nginx

服务配置了 nginx 反向代理，运行在 80 端口。

### 服务管理

```bash
# 启动服务
./scripts/start_service.sh

# 停止服务
./scripts/stop_service.sh

# 检查日志
./scripts/check_logs.sh
```

### 服务 URLs

- **主服务**: http://localhost (port 80)
- **API 文档**: http://localhost/docs
- **开发环境**: http://localhost:8000 (直接运行)

## 🎯 Features

- 🏠 使用 Gemini 2.0 Flash Lite AI 模型进行图像分析
- 📥 支持从 URLs 下载图片
- 🔍 准确判断图片是否为房间
- 🚀 RESTful API 接口
- 📊 结构化日志记录

- 🏗️ 模块化架构设计
- ⚡ 异步并发处理
- 📋 详细的房间描述和分类

## 📦 Installation

### 1. 克隆项目

```bash
git clone <repository-url>
cd Image-classification
```

### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，设置你的 Gemini API 密钥：

```bash
# 从 https://aistudio.google.com/app/apikey 获取API密钥
GEMINI_API_KEY=your_gemini_api_key_here
```

## 🚀 Quick Start

### 开发环境运行

```bash
# 激活虚拟环境
source venv/bin/activate

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 生产环境运行

```bash
# 使用PM2启动服务
./scripts/start_service.sh
```

服务将在 `http://localhost` (nginx 代理) 或 `http://localhost:8000` (直接访问) 启动

## 📚 API Usage

### 1. 分析图片是否为房间

**接口:** `POST /analyze_room`

**请求格式:**

**单张图片:**

```json
{
  "url": "https://example.com/image.jpg",
  "include_description": true
}
```

**多张图片 (批量处理):**

```json
{
  "url": [
    "https://example.com/image1.jpg",
    "https://example.com/image2.jpg",
    "https://example.com/image3.jpg"
  ],
  "include_description": false
}
```

**参数说明:**

- `url` (必填): 图片 URL 或 URL 数组
- `include_description` (可选): 是否包含详细描述，默认为 `true`
  - `true`: 返回房间类型和详细描述 (较慢但信息丰富)
  - `false`: 仅返回是否为房间 (较快)

**响应格式:**

```json
{
  "success": true,
  "total": 1,
  "processing_time": "2.345s",
  "results": [
    {
      "url": "https://example.com/image.jpg",
      "success": true,
      "is_room": true,
      "description": {
        "room_type": "客厅",
        "basic_info": "现代开放式客厅，采用中性色调和自然采光",
        "features": "大型落地窗提供充足自然光线和城市景观"
      }
    }
  ]
}
```



## 📋 Examples

### 使用 curl

```bash
# 分析单张图片 (包含描述)
curl -X POST http://localhost:8000/analyze_room \
  -H "Content-Type: application/json" \
  -d '{"url": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800", "include_description": true}'

# 快速分析 (不包含描述)
curl -X POST http://localhost:8000/analyze_room \
  -H "Content-Type: application/json" \
  -d '{"url": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800", "include_description": false}'

# 批量分析多张图片
curl -X POST http://localhost:8000/analyze_room \
  -H "Content-Type: application/json" \
  -d '{"url": ["https://example.com/image1.jpg", "https://example.com/image2.jpg"], "include_description": false}'


```

### 使用 Python

```python
import requests

# 分析单张图片
response = requests.post('http://localhost:8000/analyze_room',
                        json={'url': 'https://example.com/image.jpg'})
result = response.json()
print(f"是否为房间: {result['results'][0]['is_room']}")

# 批量分析
urls = [
    "https://example.com/image1.jpg",
    "https://example.com/image2.jpg",
    "https://example.com/image3.jpg"
]
response = requests.post('http://localhost:8000/analyze_room',
                        json={'url': urls, 'include_description': True})
result = response.json()

for i, item in enumerate(result['results']):
    if item['success']:
        print(f"图片 {i+1}: {'房间' if item['is_room'] else '非房间'}")
        if item['is_room']:
            desc = item['description']
            print(f"  房间类型: {desc['room_type']}")
            print(f"  基本信息: {desc['basic_info']}")
            print(f"  特点: {desc['features']}")
    else:
        print(f"图片 {i+1}: 分析失败 - {item['error']}")
```

## 🏠 房间定义和类型

### 房间定义

房间定义为建筑物内部空间，用于人类居住或活动。

### 支持的房间类型

- 客厅 (Living Room)
- 家庭室 (Family Room)
- 餐厅 (Dining Room)
- 厨房 (Kitchen)
- 主卧室 (Master Bedroom)
- 卧室 (Bedroom)
- 客房 (Guest Room)
- 卫生间 (Bathroom)
- 浴室 (Bathroom)
- 书房 (Study)
- 家庭办公室 (Home Office)
- 洗衣房 (Laundry Room)
- 储藏室 (Storage Room)
- 食品储藏间 (Pantry)
- 玄关 (Entrance)
- 门厅 (Foyer)
- 走廊 (Corridor)
- 阳台 (Balcony)
- 地下室 (Basement)
- 阁楼 (Attic)
- 健身房 (Gym)
- 家庭影院 (Home Theater)
- 游戏室 (Game Room)
- 娱乐室 (Entertainment Room)
- 其他 (Other)

## ⚙️ Configuration

### 环境变量

| 变量名                     | 默认值 | 说明                   |
| -------------------------- | ------ | ---------------------- |
| `GEMINI_API_KEY`           | -      | Gemini API 密钥 (必填) |
| `DOWNLOAD_TIMEOUT`         | 15     | 图片下载超时时间(秒)   |
| `MAX_CONCURRENT_DOWNLOADS` | 5      | 最大并发下载数         |
| `MAX_CONCURRENT_ANALYSIS`  | 3      | 最大并发分析数         |

### 性能调优

- 并发下载: 控制同时下载的图片数量
- 并发分析: 控制同时进行 AI 分析的图片数量
- 下载超时: 防止网络慢导致的长时间等待

## 🔍 Logging

### 日志文件

- `app.log`: 主要日志文件 (易读格式)
- `app_backup.log`: JSON 格式日志 (程序解析用)
- `logs/out.log`: PM2 标准输出日志
- `logs/error.log`: PM2 错误日志

### 日志管理

```bash
# 查看实时日志
./scripts/check_logs.sh live

# 查看错误日志
./scripts/check_logs.sh error

# 查看成功记录
./scripts/check_logs.sh success

# 查看统计信息
./scripts/check_logs.sh stats

# 查看特定请求
./scripts/check_logs.sh request <request_id>
```

## 🛠️ Development

### 项目特点

- **模块化设计**: 代码按功能分层组织
- **异步处理**: 支持高并发图片处理
- **配置管理**: 集中的配置管理系统
- **结构化日志**: 详细的日志记录和监控
- **错误处理**: 完善的错误处理和恢复机制
- **性能监控**: 内置性能监控装饰器

### 添加新功能

1. **新的 API 端点**: 在 `app/api/v1/endpoints/` 添加新文件
2. **业务逻辑**: 在 `app/services/` 添加服务模块
3. **工具函数**: 在 `app/utils/` 添加工具模块
4. **数据模型**: 在 `app/schemas/` 添加数据模型

### 测试

```bash


# 测试图片分析 (需要有效的图片URL)
curl -X POST http://localhost:8000/analyze_room \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/test-image.jpg"}'
```

## 📝 Error Handling

服务返回详细的错误信息：

```json
{
  "success": false,
  "error": "错误描述",
  "error_type": "异常类型",
  "request_id": "请求唯一标识"
}
```

常见错误:

- 缺少图片 URL 参数
- 图片 URL 为空
- 图片下载失败
- AI 分析失败
- SSL 连接错误
- 不支持的 MIME 类型

## 🌟 Features

### Google 图片搜索支持

- 自动从 Google 图片搜索 URL 提取实际图片 URL
- 处理 SSL 证书问题
- 智能 MIME 类型验证

### 批量处理

- 支持单次请求分析多张图片
- 并发处理提高效率
- 独立错误处理，单个失败不影响其他图片

### 结构化描述

每个房间图片分析返回:

- **room_type**: 具体房间分类
- **basic_info**: 整体风格和布局描述
- **features**: 最显著特点的一句话描述

## 📄 License

[添加您的许可证信息]

---

🏠 **图片房间分类服务** - 让 AI 帮您识别和分类房间图片！
