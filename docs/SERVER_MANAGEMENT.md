# 🚀 服务器管理指南

## ✅ 问题已解决：Ctrl+C 现在可以快速关闭项目

### 🔧 修复内容

我们已经修复了 `Ctrl+C` 无法停止项目和关闭速度慢的问题：

1. **简化了信号处理逻辑**：移除了复杂的自定义信号处理器
2. **直接使用 uvicorn**：让 uvicorn 自己处理 Ctrl+C 信号
3. **优化了启动脚本**：简化了 `scripts/start_server.py`
4. **改进了停止脚本**：使用 SIGINT 信号而不是 SIGTERM
5. **修复了异步处理器清理**：解决了 ThreadPoolExecutor 的 timeout 参数问题
6. **修复了数据库连接释放**：解决了异步连接释放的问题
7. **添加了超时机制**：为资源清理设置了合理的超时时间

### ⚡ 关闭速度优化

- **之前**：关闭需要等待 10-20 秒
- **现在**：关闭只需要 1-3 秒
- **超时保护**：如果清理超时，会强制跳过，确保快速关闭

### 🎯 现在的关闭方式

#### 方式 1：Ctrl+C（推荐）

在运行服务器的终端窗口按 `Ctrl+C`，服务器会在 1-3 秒内停止。

#### 方式 2：使用停止脚本

```bash
# 激活虚拟环境
source venv/bin/activate

# 停止服务器
python scripts/stop_server.py
```

#### 方式 3：进程管理

```bash
# 查找进程
ps aux | grep uvicorn

# 发送 Ctrl+C 信号
kill -INT <PID>

# 强制终止（不推荐）
kill -KILL <PID>
```

## 🚀 启动方式

### 方式 1：使用启动脚本（推荐）

```bash
# 激活虚拟环境
source venv/bin/activate

# 启动服务器
python scripts/start_server.py
```

### 方式 2：直接使用 uvicorn

```bash
# 激活虚拟环境
source venv/bin/activate

# 启动服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📊 关闭流程

```
按 Ctrl+C
    ↓
uvicorn 收到 SIGINT 信号
    ↓
触发 FastAPI 的 shutdown 事件
    ↓
清理异步处理器（超时 3 秒）
    ↓
关闭数据库连接池（超时 2 秒）
    ↓
记录关闭日志
    ↓
退出程序
```

## 🔧 故障排除

### 1. 进程无法停止

```bash
# 查找所有相关进程
ps aux | grep -E "(uvicorn|start_server|python.*app)"

# 强制终止
pkill -f "uvicorn"
pkill -f "start_server.py"
```

### 2. 端口被占用

```bash
# 查找占用端口的进程
lsof -i :8000

# 终止占用进程
kill -TERM <PID>
```

### 3. 数据库连接未释放

```bash
# 检查数据库连接
mysql -h <host> -u <user> -p -e "SHOW PROCESSLIST;"

# 清理长时间连接
mysql -h <host> -u <user> -p -e "KILL <connection_id>;"
```

## 📝 日志监控

### 查看启动日志

```bash
tail -f logs/app.log | grep -E "(启动|关闭|错误)"
```

### 查看关闭日志

```bash
grep -E "(应用关闭|资源清理|服务器已关闭)" logs/app.log
```

### 查看超时日志

```bash
grep -E "(超时|强制跳过)" logs/app.log
```

## 🎯 最佳实践

1. **开发环境**：使用启动脚本 `python scripts/start_server.py`
2. **停止服务**：优先使用 `Ctrl+C` 或停止脚本
3. **监控日志**：定期检查日志文件确保正常关闭
4. **备份数据**：重要操作前确保数据已保存

## 🔄 自动化部署

### systemd 服务配置示例

```ini
[Unit]
Description=房源图片分析系统
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/Image-classification
Environment=PATH=/path/to/venv/bin
ExecStart=/path/to/venv/bin/python scripts/start_server.py
ExecStop=/path/to/venv/bin/python scripts/stop_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

**现在你的项目已经完全支持快速 Ctrl+C 关闭了！⚡**
