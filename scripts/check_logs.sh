#!/bin/bash
# 图片分析服务日志查看工具

echo "🔍 图片分析服务日志查看工具"
echo "=================================="

case "$1" in
    "error" | "错误")
        echo "📋 最近的错误日志:"
        echo "----------------"
        grep "🔴" app.log | tail -10
        ;;
    "success" | "成功")
        echo "📋 最近成功的处理:"
        echo "----------------"
        grep "Image processing completed successfully" app.log | tail -5
        ;;
    "request" | "请求")
        if [ -z "$2" ]; then
            echo "❌ 请提供请求ID，例如: ./check_logs.sh request 40368fdf"
            exit 1
        fi
        echo "📋 请求 $2 的完整流程:"
        echo "--------------------"
        grep "$2" app.log
        ;;
    "live" | "实时")
        echo "📋 实时监控日志 (Ctrl+C 退出):"
        echo "----------------------------"
        tail -f app.log
        ;;
    "stats" | "统计")
        echo "📊 今日统计:"
        echo "----------"
        today=$(date +"%m-%d")
        echo "🔍 总请求数: $(grep -c "Starting batch image analysis request" app.log)"
        echo "✅ 成功处理: $(grep -c "Image processing completed successfully" app.log)"
        echo "🔴 处理失败: $(grep -c "Image download failed" app.log)"
        echo "⚠️  JSON解析警告: $(grep -c "not valid JSON format" app.log)"
        ;;
    "health" | "健康")
        echo "📋 健康检查记录:"
        echo "--------------"
        grep "Health check completed" app.log | tail -5
        ;;
    *)
        echo "📖 使用方法:"
        echo "  ./check_logs.sh error     - 查看错误日志"
        echo "  ./check_logs.sh success   - 查看成功记录"
        echo "  ./check_logs.sh request <ID> - 查看特定请求"
        echo "  ./check_logs.sh live      - 实时监控"
        echo "  ./check_logs.sh stats     - 查看统计信息"
        echo "  ./check_logs.sh health    - 查看健康检查"
        echo ""
        echo "📋 最近10条日志:"
        echo "-------------"
        tail -10 app.log
        ;;
esac 