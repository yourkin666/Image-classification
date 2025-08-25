#!/usr/bin/env python3
"""
数据库初始化脚本
用于创建数据库表和初始数据
"""
import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import init_database_pool, close_database_pool, execute_query


async def create_tables():
    """创建数据库表"""
    print("🏗️ 开始创建数据库表...")
    
    # 房源分析结果表
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS `qft_ai_room_analysis` (
      `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
      `room_id` varchar(64) NOT NULL COMMENT '房间ID',
      `business_type` enum('whole_rent','centralized','shared_rent') NOT NULL COMMENT '业务类型',
      `content` text COMMENT '生成的房源内容(JSON格式，最大64KB)',
      `processing_status` enum('pending','processing','completed','failed') DEFAULT 'pending' COMMENT '处理状态',
      `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
      `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
      PRIMARY KEY (`id`),
      UNIQUE KEY `uk_room_id` (`room_id`),
      KEY `idx_business_type` (`business_type`),
      KEY `idx_processing_status` (`processing_status`),
      KEY `idx_created_at` (`created_at`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='房源分析结果表';
    """
    
    try:
        await execute_query(create_table_sql)
        print("✅ 表 qft_ai_room_analysis 创建成功")
        return True
    except Exception as e:
        print(f"❌ 创建表失败: {e}")
        return False


async def check_table_exists():
    """检查表是否存在"""
    try:
        result = await execute_query("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = 'qft_ai_test' 
            AND TABLE_NAME = 'qft_ai_room_analysis'
        """)
        return bool(result)
    except Exception as e:
        print(f"❌ 检查表存在失败: {e}")
        return False


async def show_table_info():
    """显示表信息"""
    try:
        # 获取表结构
        columns = await execute_query("""
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_COMMENT
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = 'qft_ai_test' 
            AND TABLE_NAME = 'qft_ai_room_analysis'
            ORDER BY ORDINAL_POSITION
        """)
        
        print("\n📊 表结构信息:")
        print(f"{'字段名':<20} {'类型':<15} {'允许空':<8} {'默认值':<15} {'注释'}")
        print("-" * 80)
        for row in columns:
            print(f"{row[0]:<20} {row[1]:<15} {row[2]:<8} {str(row[3]):<15} {row[4]}")
        
        # 获取索引信息
        indexes = await execute_query("""
            SELECT INDEX_NAME, COLUMN_NAME, NON_UNIQUE
            FROM INFORMATION_SCHEMA.STATISTICS 
            WHERE TABLE_SCHEMA = 'qft_ai_test' 
            AND TABLE_NAME = 'qft_ai_room_analysis'
            ORDER BY INDEX_NAME, SEQ_IN_INDEX
        """)
        
        print("\n🔍 索引信息:")
        print(f"{'索引名':<20} {'字段名':<20} {'是否唯一':<8}")
        print("-" * 50)
        for row in indexes:
            unique = "唯一" if row[2] == 0 else "普通"
            print(f"{row[0]:<20} {row[1]:<20} {unique:<8}")
            
    except Exception as e:
        print(f"❌ 获取表信息失败: {e}")


async def insert_sample_data():
    """插入示例数据"""
    print("\n📝 插入示例数据...")
    
    sample_data = [
        {
            "room_id": "sample_room_001",
            "business_type": "whole_rent",
            "content": '{"lighting_comfort": "采光充足，南北通透，居住舒适度高", "decoration_quality": "精装修，墙面整洁，维护良好", "space_layout": "空间布局合理，功能分区明确", "appliances_facilities": "图片中可见的家具电器有限"}',
            "processing_status": "completed"
        },
        {
            "room_id": "sample_room_002", 
            "business_type": "centralized",
            "content": '{"lighting_comfort": "采光良好，通风顺畅", "decoration_quality": "标准化装修，品质可靠", "space_layout": "空间紧凑实用，布局合理", "appliances_facilities": "图片中可见的家具电器有限"}',
            "processing_status": "completed"
        },
        {
            "room_id": "sample_room_003",
            "business_type": "shared_rent", 
            "content": '{"lighting_comfort": "采光适中，通风良好", "decoration_quality": "装修简洁实用，维护到位", "space_layout": "共享空间设计合理，私密性好", "appliances_facilities": "图片中可见的家具电器有限"}',
            "processing_status": "completed"
        }
    ]
    
    try:
        for data in sample_data:
            # 先删除已存在的数据
            await execute_query("DELETE FROM qft_ai_room_analysis WHERE room_id = %s", (data["room_id"],))
            
            # 插入新数据
            await execute_query("""
                INSERT INTO qft_ai_room_analysis 
                (room_id, business_type, content, processing_status) 
                VALUES (%s, %s, %s, %s)
            """, (data["room_id"], data["business_type"], data["content"], data["processing_status"]))
            
            print(f"✅ 插入示例数据: {data['room_id']}")
        
        print("✅ 所有示例数据插入完成")
        return True
        
    except Exception as e:
        print(f"❌ 插入示例数据失败: {e}")
        return False


async def show_data_count():
    """显示数据统计"""
    try:
        # 总记录数
        total = await execute_query("SELECT COUNT(*) FROM qft_ai_room_analysis")
        print(f"\n📊 数据统计:")
        print(f"总记录数: {total[0][0]}")
        
        # 按业务类型统计
        business_stats = await execute_query("""
            SELECT business_type, COUNT(*) as count
            FROM qft_ai_room_analysis 
            GROUP BY business_type
        """)
        
        print("按业务类型统计:")
        for row in business_stats:
            print(f"  {row[0]}: {row[1]} 条")
        
        # 按处理状态统计
        status_stats = await execute_query("""
            SELECT processing_status, COUNT(*) as count
            FROM qft_ai_room_analysis 
            GROUP BY processing_status
        """)
        
        print("按处理状态统计:")
        for row in status_stats:
            print(f"  {row[0]}: {row[1]} 条")
            
    except Exception as e:
        print(f"❌ 获取数据统计失败: {e}")


async def main():
    """主函数"""
    print("🚀 数据库初始化工具")
    print("=" * 50)
    
    try:
        # 初始化数据库连接
        await init_database_pool()
        print("✅ 数据库连接成功")
        
        # 检查表是否存在
        table_exists = await check_table_exists()
        
        if not table_exists:
            # 创建表
            success = await create_tables()
            if not success:
                print("❌ 表创建失败")
                return
        else:
            print("✅ 表已存在")
        
        # 显示表信息
        await show_table_info()
        
        # 询问是否插入示例数据
        print("\n❓ 是否插入示例数据？(y/n): ", end="")
        choice = input().strip().lower()
        
        if choice in ['y', 'yes', '是']:
            await insert_sample_data()
            await show_data_count()
        
        print("\n🎉 数据库初始化完成！")
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
    finally:
        await close_database_pool()
        print("🔌 数据库连接已关闭")


if __name__ == "__main__":
    asyncio.run(main()) 