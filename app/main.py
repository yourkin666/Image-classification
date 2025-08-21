from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .core.logging import logger
from .api.v1.router import api_router

# 初始化FastAPI应用
app = FastAPI(
    title=settings.APP_TITLE,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION
)

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含API路由
app.include_router(api_router)

# 记录服务配置
logger.info("房源图片分析系统启动成功")

@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    logger.info("应用启动，初始化资源...")

@app.on_event("shutdown")
async def shutdown_event_handler():
    """应用关闭时的清理"""
    logger.info("应用关闭，清理资源...")
    
    try:
        # 设置清理超时时间
        import asyncio
        
        # 清理异步处理器（设置超时）
        try:
            from .services.async_processor import async_processor
            # 使用 asyncio.wait_for 设置超时
            await asyncio.wait_for(
                asyncio.to_thread(async_processor.cleanup), 
                timeout=3.0
            )
        except asyncio.TimeoutError:
            logger.warning("异步处理器清理超时，强制跳过")
        except Exception as e:
            logger.error(f"异步处理器清理失败: {e}")
        
        # 关闭数据库连接池（设置超时）
        try:
            from .core.database import close_database_pool
            await asyncio.wait_for(close_database_pool(), timeout=2.0)
        except asyncio.TimeoutError:
            logger.warning("数据库连接池关闭超时，强制跳过")
        except Exception as e:
            logger.error(f"数据库连接池关闭失败: {e}")
        
        logger.info("资源清理完成")
    except Exception as e:
        logger.error(f"关闭事件处理失败: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host=settings.HOST, 
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower()
    ) 