import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Settings:
    # Gemini API配置
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")
    
    # 数据库配置
    DB_HOST: str = os.getenv("DB_HOST", "rm-m5el7ur6zifx6ankzvo.mysql.rds.aliyuncs.com")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_NAME: str = os.getenv("DB_NAME", "qft_ai_test")
    DB_USER: str = os.getenv("DB_USER", "qft_ai_test")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "uJOLj2K09")
    DB_CHARSET: str = os.getenv("DB_CHARSET", "utf8mb4")
    
    # 数据库连接池配置
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "10"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "3600"))
    
    # 并行处理配置
    DOWNLOAD_TIMEOUT: int = int(os.getenv("DOWNLOAD_TIMEOUT", "15"))
    MAX_CONCURRENT_DOWNLOADS: int = int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "5"))
    MAX_CONCURRENT_ANALYSIS: int = int(os.getenv("MAX_CONCURRENT_ANALYSIS", "3"))
    
    # 异步处理配置
    ASYNC_MAX_WORKERS: int = int(os.getenv("ASYNC_MAX_WORKERS", "5"))
    ASYNC_MAX_RETRIES: int = int(os.getenv("ASYNC_MAX_RETRIES", "3"))
    ASYNC_RETRY_DELAY: int = int(os.getenv("ASYNC_RETRY_DELAY", "5"))
    
    # 应用配置
    APP_TITLE: str = "房源图片分析系统"
    APP_DESCRIPTION: str = "使用Gemini AI分析房源图片并生成房源内容"
    APP_VERSION: str = "2.0.0"
    
    # 服务器配置
    HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("APP_PORT", "8000"))
    DEBUG: bool = os.getenv("APP_DEBUG", "true").lower() == "true"
    LOG_LEVEL: str = os.getenv("APP_LOG_LEVEL", "INFO")
    
    # 日志配置
    LOG_FILE: str = "logs/app.log"
    LOG_BACKUP_FILE: str = "logs/app_backup.log"
    LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5


# 全局配置实例
settings = Settings() 