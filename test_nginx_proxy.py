#!/usr/bin/env python3
"""
测试nginx反向代理和Flask应用
"""

import requests
import json
import time

def test_endpoints():
    """测试所有端点"""
    base_url = "http://localhost"
    
    print("🔍 测试nginx反向代理和Flask应用...")
    print("=" * 50)
    
    # 测试主页
    print("1. 测试主页 (GET /)")
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 主页正常 - 服务: {data.get('service', 'N/A')}")
        else:
            print(f"❌ 主页错误 - 状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ 主页测试失败: {e}")
    
    print()
    
    # 测试健康检查
    print("2. 测试健康检查 (GET /health)")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 健康检查正常 - 状态: {data.get('status', 'N/A')}")
        else:
            print(f"❌ 健康检查错误 - 状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ 健康检查测试失败: {e}")
    
    print()
    
    # 测试分析端点（使用示例图片）
    print("3. 测试房间分析 (POST /analyze_room)")
    test_url = "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=800"
    payload = {
        "url": test_url,
        "include_description": True
    }
    
    try:
        response = requests.post(
            f"{base_url}/analyze_room", 
            json=payload, 
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                result = data['results'][0]
                print(f"✅ 房间分析正常")
                print(f"   图片URL: {result.get('url', 'N/A')}")
                print(f"   是否为房间: {result.get('is_room', 'N/A')}")
                if 'description' in result:
                    desc = result['description']
                    print(f"   房间类型: {desc.get('room_type', 'N/A')}")
                    print(f"   基本信息: {desc.get('basic_info', 'N/A')}")
            else:
                print(f"❌ 房间分析失败: {data.get('error', '未知错误')}")
        else:
            print(f"❌ 房间分析错误 - 状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ 房间分析测试失败: {e}")
    
    print()
    print("=" * 50)
    print("🎉 测试完成！")
    print(f"📝 服务地址: {base_url}")
    print(f"🔍 健康检查: {base_url}/health")
    print(f"📊 API文档: {base_url}/")

if __name__ == "__main__":
    test_endpoints() 