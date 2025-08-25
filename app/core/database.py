"""
数据库配置和连接管理
"""
import aiomysql
import logging
from typing import Optional, Dict, Any, List
from .config import settings
import ssl

logger = logging.getLogger(__name__)
# 业务类型映射：DB改为tinyint(1:集中 centralized, 2:整租 whole_rent, 3:合租 shared_rent)
BUSINESS_TYPE_TO_CODE = {
    "centralized": 1,
    "whole_rent": 2,
    "shared_rent": 3,
}

CODE_TO_BUSINESS_TYPE = {v: k for k, v in BUSINESS_TYPE_TO_CODE.items()}


# 数据库连接池
_pool = None

# 数据库配置
DATABASE_CONFIG = {
    "host": settings.DB_HOST,
    "port": settings.DB_PORT,
    "db": settings.DB_NAME,
    "user": settings.DB_USER,
    "password": settings.DB_PASSWORD,
    "charset": settings.DB_CHARSET,
    "autocommit": True,
    "minsize": 1,
    "maxsize": settings.DB_POOL_SIZE,
    "pool_recycle": settings.DB_POOL_RECYCLE
}

# SSL 配置（可选）
if settings.DB_SSL_ENABLED:
    ssl_ctx = ssl.create_default_context(cafile=settings.DB_SSL_CA or None)
    if not settings.DB_SSL_VERIFY:
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
    if settings.DB_SSL_CERT and settings.DB_SSL_KEY:
        ssl_ctx.load_cert_chain(certfile=settings.DB_SSL_CERT, keyfile=settings.DB_SSL_KEY)
    DATABASE_CONFIG["ssl"] = ssl_ctx


async def init_database_pool():
    """初始化数据库连接池"""
    global _pool
    if _pool is None:
        try:
            _pool = await aiomysql.create_pool(**DATABASE_CONFIG)
            logger.info("数据库连接池初始化成功")
        except Exception as e:
            logger.error(f"数据库连接池初始化失败: {e}")
            raise


async def close_database_pool():
    """关闭数据库连接池"""
    global _pool
    if _pool:
        try:
            logger.info("正在关闭数据库连接池...")
            _pool.close()
            # 设置等待关闭的超时时间
            import asyncio
            await asyncio.wait_for(_pool.wait_closed(), timeout=2.0)
            _pool = None
            logger.info("数据库连接池已关闭")
        except asyncio.TimeoutError:
            logger.warning("数据库连接池关闭超时，强制关闭")
            _pool = None
        except Exception as e:
            logger.error(f"关闭数据库连接池失败: {e}")
            _pool = None


async def get_connection():
    """获取数据库连接"""
    if _pool is None:
        await init_database_pool()
    return await _pool.acquire()


async def release_connection(conn):
    """释放数据库连接"""
    if _pool:
        _pool.release(conn)


async def execute_query(query: str, params: tuple = None) -> List[tuple]:
    """执行查询操作"""
    conn = await get_connection()
    try:
        async with conn.cursor() as cursor:
            await cursor.execute(query, params)
            result = await cursor.fetchall()
            return result
    finally:
        await release_connection(conn)


async def execute_insert(query: str, params: tuple) -> int:
    """执行插入操作"""
    conn = await get_connection()
    try:
        async with conn.cursor() as cursor:
            await cursor.execute(query, params)
            return cursor.lastrowid
    finally:
        await release_connection(conn)


async def execute_update(query: str, params: tuple) -> int:
    """执行更新操作"""
    conn = await get_connection()
    try:
        async with conn.cursor() as cursor:
            await cursor.execute(query, params)
            return cursor.rowcount
    finally:
        await release_connection(conn)


# 房源分析相关的数据库操作
def _normalize_business_type_to_code(business_type) -> int:
    """将传入的业务类型(可能为枚举/字符串/数字)规范化为数据库 tinyint 代码。"""
    # 已是合法代码
    if isinstance(business_type, int):
        return business_type if business_type in CODE_TO_BUSINESS_TYPE else None
    # Pydantic Enum 或一般 Enum
    bt = getattr(business_type, "value", business_type)
    if bt is None:
        return None
    bt_str = str(bt).strip().lower()
    return BUSINESS_TYPE_TO_CODE.get(bt_str)


async def insert_room_analysis(room_id: str, business_type, content: str = None, 
                              processing_status: str = "pending") -> int:
    """插入房源分析记录"""
    # 兼容：支持传入 Enum/字符串/数字，统一映射为tinyint
    bt_code = _normalize_business_type_to_code(business_type)
    if bt_code is None:
        raise ValueError(f"Invalid business_type: {business_type}")
    query = """
    INSERT INTO qft_ai_room_analysis 
    (room_id, business_type, content, processing_status) 
    VALUES (%s, %s, %s, %s)
    """
    params = (room_id, bt_code, content, processing_status)
    return await execute_insert(query, params)


async def update_room_analysis_status(room_id: str, processing_status: str, 
                                    content: str = None, error_message: str = None) -> int:
    """更新房源分析状态"""
    if content:
        query = """
        UPDATE qft_ai_room_analysis 
        SET processing_status = %s, content = %s, updated_at = CURRENT_TIMESTAMP
        WHERE room_id = %s
        """
        params = (processing_status, content, room_id)
    else:
        query = """
        UPDATE qft_ai_room_analysis 
        SET processing_status = %s, updated_at = CURRENT_TIMESTAMP
        WHERE room_id = %s
        """
        params = (processing_status, room_id)
    
    return await execute_update(query, params)


async def get_room_analysis(room_id: str) -> Optional[Dict[str, Any]]:
    """获取房源分析记录"""
    query = """
    SELECT id, room_id, business_type, content, processing_status, 
           created_at, updated_at
    FROM qft_ai_room_analysis 
    WHERE room_id = %s
    """
    result = await execute_query(query, (room_id,))
    
    if result:
        row = result[0]
        # 将tinyint业务类型还原为字符串，保持对上层接口兼容
        try:
            _bt = CODE_TO_BUSINESS_TYPE.get(int(row[2])) if row[2] is not None else None
        except Exception:
            _bt = row[2]
        return {
            "id": row[0],
            "room_id": row[1],
            "business_type": _bt,
            "content": row[3],
            "processing_status": row[4],
            "created_at": row[5],
            "updated_at": row[6]
        }
    return None 