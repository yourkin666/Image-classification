#!/usr/bin/env python3
"""
测试 prompt 优化功能
验证 include_description=false 时是否使用简化的 prompt
"""

import requests
import json
import time

def test_prompt_optimization():
    """测试 prompt 优化功能"""
    
    # 测试用的图片URL
    test_url = "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800"
    
    print("=== 测试 Prompt 优化功能 ===\n")
    
    # 测试1: 包含描述（完整prompt）
    print("1. 测试包含描述（include_description=True）")
    print("-" * 50)
    
    start_time = time.time()
    payload_with_desc = {
        "url": test_url,
        "include_description": True
    }
    
    try:
        response = requests.post("http://47.84.70.153/analyze_room", 
                               json=payload_with_desc, 
                               timeout=30)
        
        end_time = time.time()
        response_time_with_desc = end_time - start_time
        
        if response.status_code == 200:
            result = response.json()
            if result["success"] and result["results"]:
                item = result["results"][0]
                print(f"✅ 分析成功")
                print(f"⏱️  响应时间: {response_time_with_desc:.2f}秒")
                print(f"🏠 是否为房间: {'是' if item['is_room'] else '否'}")
                
                if "description" in item:
                    desc = item["description"]
                    print(f"📋 房间类型: {desc['room_type']}")
                    print(f"ℹ️  基本信息: {desc['basic_info']}")
                    print(f"✨ 特点: {desc['features']}")
                    print("✅ 正确：返回了完整的描述信息")
                else:
                    print("❌ 错误：应该包含描述信息")
            else:
                print(f"❌ 分析失败: {result.get('error', '未知错误')}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    print("\n" + "="*60 + "\n")
    
    # 测试2: 不包含描述（简化prompt）
    print("2. 测试不包含描述（include_description=False）")
    print("-" * 50)
    
    start_time = time.time()
    payload_without_desc = {
        "url": test_url,
        "include_description": False
    }
    
    try:
        response = requests.post("http://47.84.70.153/analyze_room", 
                               json=payload_without_desc, 
                               timeout=30)
        
        end_time = time.time()
        response_time_without_desc = end_time - start_time
        
        if response.status_code == 200:
            result = response.json()
            if result["success"] and result["results"]:
                item = result["results"][0]
                print(f"✅ 分析成功")
                print(f"⏱️  响应时间: {response_time_without_desc:.2f}秒")
                print(f"🏠 是否为房间: {'是' if item['is_room'] else '否'}")
                
                if "description" in item:
                    print("❌ 错误：不应该包含描述信息")
                    print(f"描述内容: {item['description']}")
                else:
                    print("✅ 正确：未包含描述信息")
                
                # 比较响应时间
                if response_time_without_desc < response_time_with_desc:
                    print(f"🚀 性能提升: 简化prompt比完整prompt快 {response_time_with_desc - response_time_without_desc:.2f}秒")
                else:
                    print(f"⚠️  性能对比: 简化prompt响应时间 {response_time_without_desc:.2f}秒 vs 完整prompt {response_time_with_desc:.2f}秒")
            else:
                print(f"❌ 分析失败: {result.get('error', '未知错误')}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    print("\n" + "="*60 + "\n")
    
    # 测试3: 批量测试性能差异
    print("3. 批量测试性能差异")
    print("-" * 50)
    
    multiple_urls = [
        test_url,
        "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=800",
        "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800"
    ]
    
    # 测试包含描述
    start_time = time.time()
    payload_batch_with_desc = {
        "url": multiple_urls,
        "include_description": True
    }
    
    try:
        response = requests.post("http://47.84.70.153/analyze_room", 
                               json=payload_batch_with_desc, 
                               timeout=60)
        end_time = time.time()
        batch_time_with_desc = end_time - start_time
        
        if response.status_code == 200:
            print(f"✅ 批量分析（包含描述）成功，耗时: {batch_time_with_desc:.2f}秒")
        else:
            print(f"❌ 批量分析（包含描述）失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 批量分析（包含描述）请求失败: {e}")
    
    # 测试不包含描述
    start_time = time.time()
    payload_batch_without_desc = {
        "url": multiple_urls,
        "include_description": False
    }
    
    try:
        response = requests.post("http://47.84.70.153/analyze_room", 
                               json=payload_batch_without_desc, 
                               timeout=60)
        end_time = time.time()
        batch_time_without_desc = end_time - start_time
        
        if response.status_code == 200:
            print(f"✅ 批量分析（不包含描述）成功，耗时: {batch_time_without_desc:.2f}秒")
            
            # 比较批量处理性能
            if batch_time_without_desc < batch_time_with_desc:
                improvement = ((batch_time_with_desc - batch_time_without_desc) / batch_time_with_desc) * 100
                print(f"🚀 批量处理性能提升: {improvement:.1f}%")
            else:
                print(f"⚠️  批量处理性能对比: 简化prompt {batch_time_without_desc:.2f}秒 vs 完整prompt {batch_time_with_desc:.2f}秒")
        else:
            print(f"❌ 批量分析（不包含描述）失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 批量分析（不包含描述）请求失败: {e}")

if __name__ == "__main__":
    test_prompt_optimization() 