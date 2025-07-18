#!/bin/bash

# 图片房间分类服务启动脚本（PM2版）

echo "🚀 启动图片房间分类服务..."

# 检查nginx状态
if ! systemctl is-active --quiet nginx; then
    echo "📦 启动nginx服务..."
    systemctl start nginx
    systemctl enable nginx
else
    echo "✅ nginx服务已运行"
fi

# 检查PM2是否安装
if ! command -v pm2 &> /dev/null; then
    echo "❌ PM2未安装，请先安装PM2: npm install -g pm2"
    exit 1
fi

# 启动FastAPI应用
echo "⚡ 使用PM2启动FastAPI应用..."
cd /root/Image-classification
# 使用PM2启动应用
pm2 start ecosystem.config.js
sleep 3

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 2

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
    echo "   FastAPI: $(pm2 status image-classification-api | grep -q 'online' && echo 'running' || echo 'stopped')"
    echo ""
    echo "💡 PM2管理命令:"
    echo "   - 查看状态: pm2 status"
    echo "   - 查看日志: pm2 logs"
    echo "   - 重启服务: pm2 restart image-classification-api"
    echo "   - 停止服务: pm2 stop image-classification-api"
else
    echo "❌ 服务启动失败，请检查日志"
    echo "📋 nginx日志: journalctl -u nginx -f"
    echo "📋 PM2日志: pm2 logs"
fi 