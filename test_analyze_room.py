#!/usr/bin/env python3
"""
测试 analyze_room 接口的 include_description 参数功能
"""

import requests
import json

def test_analyze_room():
    """测试 analyze_room 接口"""
    
    # 测试用的图片URL（请替换为实际的图片URL）
    test_url = "https://example.com/test-room.jpg"
    
    # 测试1: 包含描述（默认行为）
    print("=== 测试1: 包含描述（include_description=True）===")
    payload1 = {
        "url": test_url,
        "include_description": True
    }
    
    try:
        response1 = requests.post("http://47.84.70.153/analyze_room", 
                                json=payload1, 
                                timeout=30)
        print(f"状态码: {response1.status_code}")
        if response1.status_code == 200:
            result1 = response1.json()
            print("返回结果包含description字段:", "description" in result1["results"][0])
            print("结果预览:", json.dumps(result1, indent=2, ensure_ascii=False)[:500] + "...")
        else:
            print("错误响应:", response1.text)
    except Exception as e:
        print(f"请求失败: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # 测试2: 不包含描述
    print("=== 测试2: 不包含描述（include_description=False）===")
    payload2 = {
        "url": test_url,
        "include_description": False
    }
    
    try:
        response2 = requests.post("http://47.84.70.153/analyze_room", 
                                json=payload2, 
                                timeout=30)
        print(f"状态码: {response2.status_code}")
        if response2.status_code == 200:
            result2 = response2.json()
            print("返回结果包含description字段:", "description" in result2["results"][0])
            print("结果预览:", json.dumps(result2, indent=2, ensure_ascii=False)[:500] + "...")
        else:
            print("错误响应:", response2.text)
    except Exception as e:
        print(f"请求失败: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # 测试3: 不指定参数（应该默认为True）
    print("=== 测试3: 不指定include_description参数（默认值）===")
    payload3 = {
        "url": test_url
    }
    
    try:
        response3 = requests.post("http://47.84.70.153/analyze_room", 
                                json=payload3, 
                                timeout=30)
        print(f"状态码: {response3.status_code}")
        if response3.status_code == 200:
            result3 = response3.json()
            print("返回结果包含description字段:", "description" in result3["results"][0])
            print("结果预览:", json.dumps(result3, indent=2, ensure_ascii=False)[:500] + "...")
        else:
            print("错误响应:", response3.text)
    except Exception as e:
        print(f"请求失败: {e}")

if __name__ == "__main__":
    test_analyze_room() 