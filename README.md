# 房源图片分析系统

基于 Gemini AI 的智能房源图片分析系统，支持房间识别和内容生成。

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
│   │           └── analyze.py    # 图像分析接口
│   ├── core/                     # 核心配置和基础设施
│   │   ├── __init__.py
│   │   ├── config.py             # 配置管理
│   │   ├── database.py           # 数据库配置
│   │   └── logging.py            # 日志配置
│   ├── services/                 # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── image_service.py      # 图像处理服务
│   │   ├── gemini_service.py     # Gemini AI服务
│   │   └── async_processor.py    # 异步处理器
│   ├── utils/                    # 工具函数
│   │   ├── __init__.py
│   │   ├── image_utils.py        # 图像工具
│   │   ├── url_utils.py          # URL处理工具
│   │   ├── content_generator.py  # 内容生成工具
│   │   └── content_formatter.py  # 内容格式化工具
│   └── schemas/                  # 数据模型
│       ├── __init__.py
│       └── requests.py           # 请求/响应模型
├── database/                     # 数据库相关
│   └── init.sql                  # 数据库初始化脚本
├── tests/                        # 测试目录
│   └── __init__.py
├── scripts/                      # 脚本目录
│   └── init_database.py          # 数据库初始化脚本
├── logs/                         # 日志目录
├── .env.example                  # 环境变量示例
├── .gitignore
├── requirements.txt
└── README.md
```

## 🎯 核心功能

- 🏠 使用 Gemini 2.0 Flash Lite AI 模型进行图像分析
- 📥 支持从 URLs 下载图片
- 🔍 准确判断图片是否为房间
- 🚀 RESTful API 接口
- 📊 结构化日志记录
- 🏗️ 模块化架构设计
- ⚡ 异步并发处理
- 📋 四大维度房源内容生成
- 💾 MySQL 数据库存储
- 🔄 异步内容处理架构
- 📈 处理状态跟踪

### 业务支持

- 🏘️ 整租房 (whole_rent)
- 🏢 集中式公寓 (centralized)
- 🏠 合租房 (shared_rent)

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

### 5. 初始化数据库

```bash
python scripts/init_database.py
```

## 🚀 Quick Start

### 开发环境运行

```bash
# 激活虚拟环境
source venv/bin/activate

# 方式1: 使用启动脚本（推荐）
python scripts/start_server.py

# 方式2: 直接使用uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 停止服务器

```bash
# 方式1: 使用停止脚本（推荐）
python scripts/stop_server.py

# 方式2: 在运行窗口按 Ctrl+C
# 现在支持优雅关闭，会正确清理资源
```

服务将在 `http://localhost:8000` 启动

### 优雅关闭特性

- ✅ 支持 `Ctrl+C` 优雅关闭
- ✅ 自动清理数据库连接池
- ✅ 自动关闭异步处理器
- ✅ 等待正在进行的任务完成
- ✅ 详细的关闭日志记录

## 📚 API Usage

### 1. 房源分析接口

**接口:** `POST /analyze_room`

**请求格式:**

```json
{
  "roomId": "room_001",
  "business_type": "whole_rent",
  "url": "https://example.com/image.jpg"
}
```

**批量处理:**

```json
{
  "roomId": "room_002",
  "business_type": "centralized",
  "url": ["https://example.com/image1.jpg", "https://example.com/image2.jpg"]
}
```

**参数说明:**

- `roomId` (必填): 房间 ID
- `business_type` (必填): 业务类型 (whole_rent/centralized/shared_rent)
- `url` (必填): 图片 URL 或 URL 数组

**响应格式:**

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

### 2. 处理状态查询接口

**接口:** `GET /status/{room_id}`

**响应格式:**

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
  "created_at": "2025-08-21T14:32:10",
  "updated_at": "2025-08-21T14:43:11"
}
```

## 🏠 房间定义

房间定义为建筑物内部空间，用于人类居住或活动。

### 支持的房间类型

- 客厅、卧室、厨房、卫生间
- 书房、餐厅、阳台、走廊
- 其他居住空间

## ⚙️ Configuration

### 环境变量配置

```bash
# Gemini API配置
GEMINI_API_KEY=your_gemini_api_key_here

# 数据库配置
DB_HOST=rm-m5el7ur6zifx6ankzvo.mysql.rds.aliyuncs.com
DB_PORT=3306
DB_NAME=qft_ai_test
DB_USER=qft_ai_test
DB_PASSWORD=uJOLj2K09
DB_CHARSET=utf8mb4

# 服务器配置
APP_HOST=0.0.0.0
APP_PORT=8000
APP_DEBUG=true
APP_LOG_LEVEL=INFO
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

## 🌟 Features

### 批量处理

- 支持单次请求分析多张图片
- 并发处理提高效率
- 独立错误处理，单个失败不影响其他图片

### 异步处理

- 快速返回房间识别结果
- 后台异步生成详细内容
- 支持状态查询和进度跟踪

### 内容生成

- 四大维度房源内容分析
- 根据业务类型定制内容
- 智能内容质量验证
- 备用内容机制
