#!/bin/bash

# 图片房间分类服务启动脚本（FastAPI版）

echo "🚀 启动图片房间分类服务..."

# 检查nginx状态
if ! systemctl is-active --quiet nginx; then
    echo "📦 启动nginx服务..."
    systemctl start nginx
    systemctl enable nginx
else
    echo "✅ nginx服务已运行"
fi

# 检查FastAPI应用是否运行
if pgrep -f "uvicorn main:app" > /dev/null; then
    echo "✅ FastAPI应用已运行"
else
    echo "⚡ 启动FastAPI应用..."
    cd /root/Image-classification
    nohup uvicorn main:app --host 0.0.0.0 --port 5000 --log-level info > fastapi.log 2>&1 &
    sleep 3
fi

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 5

# 测试服务
echo "🔍 测试服务状态..."
if curl -s http://localhost/health > /dev/null; then
    echo "✅ 服务启动成功!"
    echo "📍 服务地址: http://localhost"
    echo "🔍 健康检查: http://localhost/health"
    echo "📝 API文档: http://localhost/"
    echo ""
    echo "📊 服务状态:"
    echo "   nginx: $(systemctl is-active nginx)"
    echo "   FastAPI: $(pgrep -f 'uvicorn main:app' > /dev/null && echo 'running' || echo 'stopped')"
else
    echo "❌ 服务启动失败，请检查日志"
    echo "📋 nginx日志: journalctl -u nginx -f"
    echo "📋 FastAPI日志: tail -f /root/Image-classification/fastapi.log"
fi 