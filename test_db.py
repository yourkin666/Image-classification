#!/usr/bin/env python3
"""
数据库连接测试脚本
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import init_database_pool, get_room_analysis, close_database_pool
from app.core.logging import logger

async def test_database():
    """测试数据库连接和查询"""
    try:
        print("正在初始化数据库连接池...")
        await init_database_pool()
        print("数据库连接池初始化成功")
        
        # 测试查询
        print("正在测试查询...")
        result = await get_room_analysis("test_room_014")
        if result:
            print(f"查询成功: {result}")
        else:
            print("查询结果为空")
            
    except Exception as e:
        print(f"数据库测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await close_database_pool()
        print("数据库连接已关闭")

if __name__ == "__main__":
    asyncio.run(test_database()) 