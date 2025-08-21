#!/usr/bin/env python3
"""
状态查询功能测试脚本
"""
import asyncio
import requests
import time
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import init_database_pool, close_database_pool, get_room_analysis
from app.services.async_processor import async_processor

BASE_URL = "http://localhost:8000"

def test_direct_database_query():
    """直接测试数据库查询"""
    print("=== 直接数据库查询测试 ===")
    
    async def test_db():
        try:
            await init_database_pool()
            
            # 测试查询存在的记录
            test_room_ids = ["test_room_001", "test_room_002", "test_room_003"]
            
            for room_id in test_room_ids:
                print(f"查询房间: {room_id}")
                record = await get_room_analysis(room_id)
                if record:
                    print(f"✓ 找到记录: {room_id}")
                    print(f"  状态: {record['processing_status']}")
                    print(f"  内容: {record['content'][:100] if record['content'] else 'None'}...")
                else:
                    print(f"✗ 未找到记录: {room_id}")
                    
            await close_database_pool()
            
        except Exception as e:
            print(f"✗ 数据库查询失败: {e}")
            
    asyncio.run(test_db())

def test_async_processor_status():
    """测试异步处理器的状态查询"""
    print("\n=== 异步处理器状态查询测试 ===")
    
    async def test_processor():
        try:
            await init_database_pool()
            
            test_room_ids = ["test_room_001", "test_room_002", "test_room_003"]
            
            for room_id in test_room_ids:
                print(f"查询房间状态: {room_id}")
                try:
                    status = await async_processor.get_processing_status(room_id)
                    if status:
                        print(f"✓ 状态查询成功: {room_id}")
                        print(f"  状态: {status['processing_status']}")
                        print(f"  业务类型: {status['business_type']}")
                        if status['content']:
                            print(f"  内容字段: {list(status['content'].keys())}")
                    else:
                        print(f"✗ 状态查询返回None: {room_id}")
                except Exception as e:
                    print(f"✗ 状态查询异常: {room_id}, 错误: {e}")
                    
            await close_database_pool()
            
        except Exception as e:
            print(f"✗ 异步处理器测试失败: {e}")
            
    asyncio.run(test_processor())

def test_api_status_endpoint():
    """测试API状态端点"""
    print("\n=== API状态端点测试 ===")
    
    test_room_ids = ["test_room_001", "test_room_002", "test_room_003"]
    
    for room_id in test_room_ids:
        print(f"API查询房间: {room_id}")
        try:
            response = requests.get(f"{BASE_URL}/status/{room_id}", timeout=10)
            print(f"  状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"  响应: {result}")
            elif response.status_code == 404:
                print(f"  房间不存在: {room_id}")
            else:
                print(f"  错误响应: {response.text}")
                
        except Exception as e:
            print(f"✗ API请求异常: {e}")

def test_content_parsing():
    """测试内容解析"""
    print("\n=== 内容解析测试 ===")
    
    from app.utils.content_formatter import ContentFormatter
    
    # 测试正常内容
    test_content = {
        "lighting_comfort": "阳光充足,视野开阔",
        "decoration_quality": "装修品质上乘",
        "space_layout": "空间宽敞,布局合理",
        "appliances_facilities": "电器设施齐全"
    }
    
    # 格式化
    formatted = ContentFormatter.format_content_for_storage(test_content)
    print(f"格式化结果: {formatted}")
    
    # 解析
    parsed = ContentFormatter.parse_content_from_storage(formatted)
    print(f"解析结果: {parsed}")
    
    # 验证
    is_valid = ContentFormatter.validate_content(parsed)
    print(f"验证结果: {is_valid}")
    
    # 测试空内容
    empty_parsed = ContentFormatter.parse_content_from_storage("")
    print(f"空内容解析: {empty_parsed}")
    
    # 测试无效JSON
    invalid_parsed = ContentFormatter.parse_content_from_storage("{invalid json}")
    print(f"无效JSON解析: {invalid_parsed}")

if __name__ == "__main__":
    print("🔍 开始状态查询功能诊断")
    
    # 1. 直接数据库查询
    test_direct_database_query()
    
    # 2. 异步处理器状态查询
    test_async_processor_status()
    
    # 3. API状态端点测试
    test_api_status_endpoint()
    
    # 4. 内容解析测试
    test_content_parsing()
    
    print("\n🎯 诊断完成") 