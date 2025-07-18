#!/bin/bash

# 图片房间分类服务停止脚本（PM2版）

echo "🛑 停止图片房间分类服务..."

# 检查PM2是否安装
if ! command -v pm2 &> /dev/null; then
    echo "❌ PM2未安装，但仍将尝试关闭可能运行的FastAPI进程"
    if pgrep -f "uvicorn main:app" > /dev/null; then
        pkill -f "uvicorn main:app"
        echo "✅ FastAPI进程已停止"
    else
        echo "✅ Flask应用未运行"
    fi
else
    # 使用PM2停止FastAPI应用
    if pm2 list | grep -q "image-classification-api"; then
        echo "⏳ 停止FastAPI应用..."
        pm2 stop image-classification-api
        echo "✅ FastAPI应用已停止"
    else
        echo "✅ FastAPI应用未在PM2中运行"
    fi
fi

echo "🎉 服务停止完成！"
echo "💡 提示: nginx服务保持运行，如需完全停止请运行: systemctl stop nginx" 