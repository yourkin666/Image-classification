# 房源图片分析系统

基于 Gemini AI 的智能房源图片分析系统，支持房间识别和内容生成。

## 🎯 核心功能

- 🏠 使用 Gemini 2.0 Flash Lite AI 模型进行图像分析
- 📥 支持从 URLs 下载图片
- 🔍 准确判断图片是否为房间
- 📋 四大维度房源内容生成（采光舒适度、装修品质、空间布局、电器设施）
- 💾 MySQL 数据库存储
- 🔄 异步内容处理架构
- 📈 处理状态跟踪

### 支持的业务类型

- 🏘️ 整租房 (whole_rent)
- 🏢 集中式公寓 (centralized)
- 🏠 合租房 (shared_rent)

## 🚀 快速开始

### 1. 安装依赖

```bash
git clone <repository-url>
cd Image-classification
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 2. 配置环境

```bash
cp .env.example .env
# 编辑 .env 文件，设置 Gemini API 密钥
# 从 https://aistudio.google.com/app/apikey 获取
```

### 3. 初始化数据库

```bash
python scripts/init_database.py
```

### 4. 启动服务

```bash
python scripts/start_server.py
# 服务将在 http://localhost:8000 启动
```

## 📚 API 使用

### 房源分析接口

```bash
POST /analyze_room
```

**请求示例：**

```json
{
  "roomId": "room_001",
  "business_type": "whole_rent",
  "url": "https://example.com/image.jpg"
}
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

### 处理状态查询

```bash
GET /status/{room_id}
```

## 🏗️ 项目结构

```
Image-classification/
├── app/                          # 应用主目录
│   ├── main.py                   # FastAPI应用入口
│   ├── api/v1/endpoints/         # API接口
│   ├── core/                     # 核心配置
│   ├── services/                 # 业务逻辑
│   ├── utils/                    # 工具函数
│   └── schemas/                  # 数据模型
├── database/                     # 数据库相关
├── scripts/                      # 启动脚本
└── tests/                        # 测试目录
```

## ⚙️ 配置说明

主要环境变量：

- `GEMINI_API_KEY`: Gemini API 密钥
- `DB_HOST`, `DB_PORT`, `DB_NAME`: 数据库配置
- `APP_HOST`, `APP_PORT`: 服务器配置

## 🌟 特性

- **批量处理**: 支持单次请求分析多张图片
- **异步处理**: 快速返回房间识别结果，后台异步生成详细内容
- **智能内容**: 根据业务类型定制四大维度房源内容
- **状态跟踪**: 支持处理状态查询和进度跟踪
- **优雅关闭**: 支持 Ctrl+C 优雅关闭，自动清理资源

## 📖 更多文档

- [API 文档](API_DOCUMENTATION.md)
- [服务器管理](docs/SERVER_MANAGEMENT.md)
