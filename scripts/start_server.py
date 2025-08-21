#!/usr/bin/env python3
"""
启动脚本 - 简化版本，直接使用uvicorn
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import settings
from app.core.logging import logger

if __name__ == "__main__":
    # 确保日志目录存在
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 直接使用uvicorn启动，让uvicorn自己处理信号
    import uvicorn
    
    logger.info(f"启动服务器: {settings.HOST}:{settings.PORT}")
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower(),
        reload=False,  # 生产环境关闭热重载
        access_log=True,
        use_colors=True
    ) 