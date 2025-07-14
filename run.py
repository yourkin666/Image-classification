#!/usr/bin/env python3
"""
图片房间分类服务启动脚本
"""

import sys
import os

def check_dependencies():
    """检查依赖是否安装"""
    try:
        import flask
        import google.genai
        import requests
        print("✅ 所有依赖已安装")
        return True
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        return False

def main():
    """主函数"""
    print("🚀 启动图片房间分类服务...")
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 启动服务
    try:
        from app import app
        print("✅ 服务启动成功!")
        print("📍 服务地址: http://localhost:5000")
        print("🔍 健康检查: http://localhost:5000/health")
        print("📝 API文档: 查看 README.md")
        print("\n按 Ctrl+C 停止服务")
        
        app.run(debug=True, host='0.0.0.0', port=5000)
        
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 