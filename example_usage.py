#!/usr/bin/env python3
"""
使用示例：展示 analyze_room 接口的 include_description 参数功能
"""

import requests
import json

def example_usage():
    """展示如何使用新的 include_description 参数"""
    
    # 示例图片URL（请替换为实际的图片URL）
    image_url = "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800"
    
    print("=== Image Room Classification API 使用示例 ===\n")
    
    # 示例1: 包含详细描述（默认行为）
    print("1. 包含详细描述（include_description=True）")
    print("-" * 50)
    
    payload_with_desc = {
        "url": image_url,
        "include_description": True
    }
    
    try:
        response = requests.post("http://47.84.70.153/analyze_room", 
                               json=payload_with_desc, 
                               timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result["success"] and result["results"]:
                item = result["results"][0]
                print(f"✅ 分析成功")
                print(f"📸 图片URL: {item['url']}")
                print(f"🏠 是否为房间: {'是' if item['is_room'] else '否'}")
                
                if "description" in item:
                    desc = item["description"]
                    print(f"📋 房间类型: {desc['room_type']}")
                    print(f"ℹ️  基本信息: {desc['basic_info']}")
                    print(f"✨ 特点: {desc['features']}")
                else:
                    print("❌ 未包含描述信息")
            else:
                print(f"❌ 分析失败: {result.get('error', '未知错误')}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            print(f"错误信息: {response.text}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    print("\n" + "="*60 + "\n")
    
    # 示例2: 不包含详细描述（更快响应）
    print("2. 不包含详细描述（include_description=False）")
    print("-" * 50)
    
    payload_without_desc = {
        "url": image_url,
        "include_description": False
    }
    
    try:
        response = requests.post("http://47.84.70.153/analyze_room", 
                               json=payload_without_desc, 
                               timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result["success"] and result["results"]:
                item = result["results"][0]
                print(f"✅ 分析成功")
                print(f"📸 图片URL: {item['url']}")
                print(f"🏠 是否为房间: {'是' if item['is_room'] else '否'}")
                
                if "description" in item:
                    print("⚠️  警告：应该不包含描述信息，但返回了描述")
                else:
                    print("✅ 正确：未包含描述信息（响应更快）")
            else:
                print(f"❌ 分析失败: {result.get('error', '未知错误')}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            print(f"错误信息: {response.text}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    print("\n" + "="*60 + "\n")
    
    # 示例3: 批量处理（不包含描述以提高性能）
    print("3. 批量处理多张图片（不包含描述以提高性能）")
    print("-" * 50)
    
    multiple_urls = [
        image_url,
        "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=800",  # 另一个房间图片
        "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800"   # 户外图片
    ]
    
    payload_batch = {
        "url": multiple_urls,
        "include_description": False  # 批量处理时不包含描述以提高性能
    }
    
    try:
        response = requests.post("http://47.84.70.153/analyze_room", 
                               json=payload_batch, 
                               timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            if result["success"]:
                print(f"✅ 批量分析成功，共处理 {result['total']} 张图片")
                
                for i, item in enumerate(result["results"], 1):
                    print(f"\n📸 图片 {i}:")
                    print(f"   URL: {item['url']}")
                    
                    if item["success"]:
                        print(f"   🏠 是否为房间: {'是' if item['is_room'] else '否'}")
                        if "description" in item:
                            print("   ⚠️  包含描述信息（应该不包含）")
                        else:
                            print("   ✅ 不包含描述信息（符合预期）")
                    else:
                        print(f"   ❌ 分析失败: {item['error']}")
            else:
                print(f"❌ 批量分析失败: {result.get('error', '未知错误')}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            print(f"错误信息: {response.text}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

if __name__ == "__main__":
    example_usage() 