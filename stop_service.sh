#!/bin/bash

# 图片房间分类服务停止脚本

echo "🛑 停止图片房间分类服务..."

# 停止Flask应用
if pgrep -f "python3 run.py" > /dev/null; then
    echo "🐍 停止Flask应用..."
    pkill -f "python3 run.py"
    sleep 2
    echo "✅ Flask应用已停止"
else
    echo "✅ Flask应用未运行"
fi

# 停止nginx（可选，注释掉以保持nginx运行）
# echo "📦 停止nginx服务..."
# systemctl stop nginx
# echo "✅ nginx服务已停止"

echo "🎉 服务停止完成！"
echo "💡 提示: nginx服务保持运行，如需完全停止请运行: systemctl stop nginx" 