from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .core.logging import logger
from .core.middleware import RequestTrackingMiddleware
from .api.v1.router import api_router

# 初始化FastAPI应用
app = FastAPI(
    title=settings.APP_TITLE,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION
)

# 添加请求跟踪中间件 - 暂时禁用，基本功能已工作
# app.middleware("http")(RequestTrackingMiddleware)

# 允许跨域（如有需要可调整）
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
logger.info(
    "Service configuration loaded",
    download_timeout=settings.DOWNLOAD_TIMEOUT,
    max_concurrent_downloads=settings.MAX_CONCURRENT_DOWNLOADS,
    max_concurrent_analysis=settings.MAX_CONCURRENT_ANALYSIS
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT) 