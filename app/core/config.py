import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Settings:
    # Gemini API配置
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")
    
    # 并行处理配置
    DOWNLOAD_TIMEOUT: int = int(os.getenv("DOWNLOAD_TIMEOUT", "15"))
    MAX_CONCURRENT_DOWNLOADS: int = int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "5"))
    MAX_CONCURRENT_ANALYSIS: int = int(os.getenv("MAX_CONCURRENT_ANALYSIS", "3"))
    
    # 应用配置
    APP_TITLE: str = "图片房间分类服务"
    APP_DESCRIPTION: str = "使用Gemini AI分析图片是否为房间并识别房间类型"
    APP_VERSION: str = "1.0.0"
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 5000
    
    # 日志配置
    LOG_FILE: str = "logs/app.log"
    LOG_BACKUP_FILE: str = "logs/app_backup.log"
    LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5
    
# 创建全局配置实例
settings = Settings()

# 验证配置
if not settings.GEMINI_API_KEY:
    raise ValueError("请设置环境变量 GEMINI_API_KEY") 