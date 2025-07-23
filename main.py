import os
import base64
import requests
import re
import asyncio
import functools
import time
import uuid
import traceback
import json as json_lib
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from io import BytesIO
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Union, Optional, Dict, Tuple, Any
from google import genai
from google.genai import types
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler

# 加载环境变量
load_dotenv()

# 高级日志配置
class StructuredLogger:
    def __init__(self, name, log_file="app.log"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # 清除现有的处理器
        for handler in self.logger.handlers:
            self.logger.removeHandler(handler)
        
        # 文件处理器 - 轮转日志
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 文件日志格式 - 清晰易读的分层格式
        class ReadableFileFormatter(logging.Formatter):
            def __init__(self):
                super().__init__()
                # 级别图标映射
                self.level_icons = {
                    'DEBUG': '🔍',
                    'INFO': '✅', 
                    'WARNING': '⚠️',
                    'ERROR': '🔴',
                    'CRITICAL': '💥'
                }
            
            def format(self, record):
                now = datetime.now()
                time_str = now.strftime("%H:%M:%S")
                date_str = now.strftime("%m-%d")
                
                # 获取级别图标
                icon = self.level_icons.get(record.levelname, '📝')
                
                # 获取简化的请求ID
                request_id = getattr(record, 'request_id', None)
                short_request_id = request_id[:8] if request_id and len(request_id) > 8 else request_id
                
                # 构建主要消息行
                main_line = f"[{date_str} {time_str}] {icon} {record.getMessage()}"
                if request_id:
                    main_line += f" (请求:{short_request_id})"
                
                # 构建详细信息行
                details = []
                
                # URL信息 (截断长URL)
                if hasattr(record, 'url'):
                    url = record.url
                    if len(url) > 70:
                        url = url[:35] + "..." + url[-32:]
                    details.append(f"URL: {url}")
                
                # 路径信息
                if hasattr(record, 'path'):
                    details.append(f"路径: {record.path}")
                
                # 状态码
                if hasattr(record, 'status'):
                    details.append(f"状态: {record.status}")
                
                # 耗时
                if hasattr(record, 'duration'):
                    details.append(f"耗时: {record.duration}")
                
                # 房间识别结果
                if hasattr(record, 'is_room'):
                    room_status = "房间" if record.is_room else "非房间"
                    details.append(f"识别: {room_status}")
                    
                if hasattr(record, 'room_type') and record.room_type:
                    details.append(f"类型: {record.room_type}")
                
                # 错误信息
                if hasattr(record, 'error_type'):
                    error_msg = record.error_type
                    if record.levelname == 'ERROR':
                        if 'timeout' in error_msg.lower() or 'connecttimeout' in error_msg.lower():
                            error_msg = "连接超时"
                        elif 'ssl' in error_msg.lower():
                            error_msg = "SSL证书错误"
                        elif 'notfound' in error_msg.lower() or '404' in str(record.getMessage()):
                            error_msg = "资源未找到"
                        elif 'network' in error_msg.lower():
                            error_msg = "网络错误"
                    details.append(f"错误: {error_msg}")
                
                # 客户端IP
                if hasattr(record, 'client_ip') and record.client_ip != 'unknown':
                    details.append(f"客户端: {record.client_ip}")
                
                # HTTP方法
                if hasattr(record, 'method'):
                    details.append(f"方法: {record.method}")
                
                # 数据大小
                if hasattr(record, 'data_size') and record.data_size:
                    if record.data_size > 1024*1024:
                        size_str = f"{record.data_size/(1024*1024):.1f}MB"
                    elif record.data_size > 1024:
                        size_str = f"{record.data_size/1024:.1f}KB"
                    else:
                        size_str = f"{record.data_size}字节"
                    details.append(f"大小: {size_str}")
                
                # 组装完整消息
                if details:
                    # 如果详细信息太多，分行显示
                    if len(details) > 3:
                        detail_lines = []
                        for detail in details:
                            detail_lines.append(f"    ├─ {detail}")
                        return main_line + "\n" + "\n".join(detail_lines)
                    else:
                        # 简单情况，放在一行
                        return main_line + f"\n    └─ {' | '.join(details)}"
                else:
                    return main_line
        
        # 备用JSON格式（用于程序解析）
        class BackupJSONFormatter(logging.Formatter):
            def format(self, record):
                now = datetime.now()
                log_entry = {
                    "时间": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "级别": record.levelname,
                    "日志器": record.name,
                    "消息": record.getMessage(),
                    "模块": record.module,
                    "函数": record.funcName,
                    "行号": record.lineno
                }
                
                # 添加额外的字段
                if hasattr(record, 'request_id'):
                    log_entry['请求ID'] = record.request_id
                if hasattr(record, 'url'):
                    log_entry['URL'] = record.url
                if hasattr(record, 'path'):
                    log_entry['路径'] = record.path
                if hasattr(record, 'duration'):
                    log_entry['耗时'] = record.duration
                if hasattr(record, 'status'):
                    log_entry['状态码'] = record.status
                if hasattr(record, 'error_type'):
                    log_entry['错误类型'] = record.error_type
                if hasattr(record, 'client_ip'):
                    log_entry['客户端IP'] = record.client_ip
                if hasattr(record, 'method'):
                    log_entry['HTTP方法'] = record.method
                if hasattr(record, 'is_room'):
                    log_entry['是否房间'] = "是" if record.is_room else "否"
                if hasattr(record, 'room_type'):
                    log_entry['房间类型'] = record.room_type
                if hasattr(record, 'data_size'):
                    log_entry['数据大小'] = f"{record.data_size}字节" if hasattr(record, 'data_size') else None
                if hasattr(record, 'stack_trace'):
                    log_entry['错误堆栈'] = record.stack_trace
                
                return json_lib.dumps(log_entry, ensure_ascii=False)
        
        # 分层日志格式 (用于控制台显示)
        class LayeredFormatter(logging.Formatter):
            def __init__(self):
                super().__init__()
                # 级别图标映射
                self.level_icons = {
                    'DEBUG': '🔍',
                    'INFO': '✅', 
                    'WARNING': '⚠️',
                    'ERROR': '🔴',
                    'CRITICAL': '💥'
                }
            
            def format(self, record):
                now = datetime.now()
                time_str = now.strftime("%H:%M:%S")
                
                # 获取级别图标
                icon = self.level_icons.get(record.levelname, '📝')
                
                # 获取简化的请求ID
                request_id = getattr(record, 'request_id', 'unknown')
                short_request_id = request_id[:8] if len(request_id) > 8 else request_id
                
                # 构建主要消息行
                main_line = f"[{time_str}] {icon} {record.getMessage()}"
                if request_id != 'unknown':
                    main_line += f" (请求: {short_request_id})"
                
                # 构建详细信息行
                details = []
                
                # URL信息 (截断长URL)
                if hasattr(record, 'url'):
                    url = record.url
                    if len(url) > 60:
                        url = url[:30] + "..." + url[-27:]
                    details.append(f"URL: {url}")
                
                # 路径信息
                if hasattr(record, 'path'):
                    details.append(f"路径: {record.path}")
                
                # 状态码
                if hasattr(record, 'status'):
                    details.append(f"状态: {record.status}")
                
                # 耗时
                if hasattr(record, 'duration'):
                    details.append(f"耗时: {record.duration}")
                
                # 房间识别结果
                if hasattr(record, 'is_room'):
                    room_status = "是房间" if record.is_room else "非房间"
                    details.append(f"识别: {room_status}")
                    
                if hasattr(record, 'room_type') and record.room_type:
                    details.append(f"类型: {record.room_type}")
                
                # 错误信息
                if hasattr(record, 'error_type'):
                    error_msg = record.error_type
                    if record.levelname == 'ERROR':
                        if 'timeout' in error_msg.lower() or 'connecttimeout' in error_msg.lower():
                            error_msg = "连接超时"
                        elif 'ssl' in error_msg.lower():
                            error_msg = "SSL证书错误"
                        elif 'notfound' in error_msg.lower() or '404' in str(record.getMessage()):
                            error_msg = "资源未找到"
                        elif 'network' in error_msg.lower():
                            error_msg = "网络错误"
                    details.append(f"错误: {error_msg}")
                
                # 客户端IP
                if hasattr(record, 'client_ip') and record.client_ip != 'unknown':
                    details.append(f"客户端: {record.client_ip}")
                
                # HTTP方法
                if hasattr(record, 'method'):
                    details.append(f"方法: {record.method}")
                
                # 数据大小
                if hasattr(record, 'data_size') and record.data_size:
                    if record.data_size > 1024*1024:
                        size_str = f"{record.data_size/(1024*1024):.1f}MB"
                    elif record.data_size > 1024:
                        size_str = f"{record.data_size/1024:.1f}KB"
                    else:
                        size_str = f"{record.data_size}字节"
                    details.append(f"大小: {size_str}")
                
                # 组装完整消息
                if details:
                    # 如果详细信息太多，分行显示
                    if len(details) > 2:
                        detail_lines = []
                        for detail in details:
                            detail_lines.append(f"         {detail}")
                        return main_line + "\n" + "\n".join(detail_lines)
                    else:
                        # 简单情况，放在一行
                        return main_line + "\n         " + " | ".join(details)
                else:
                    return main_line
        
        # 为文件使用易读格式
        file_handler.setFormatter(ReadableFileFormatter())
        console_handler.setFormatter(LayeredFormatter())
        
        # 额外创建一个JSON备份文件（供程序解析使用）
        json_handler = RotatingFileHandler(
            "app_backup.log", maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
        )
        json_handler.setLevel(logging.DEBUG)
        json_handler.setFormatter(BackupJSONFormatter())
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        self.logger.addHandler(json_handler)
    
    def debug(self, message, **kwargs):
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message, **kwargs):
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message, **kwargs):
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message, **kwargs):
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message, **kwargs):
        self._log(logging.CRITICAL, message, **kwargs)
    
    def _log(self, level, message, **kwargs):
        extra = {}
        for key, value in kwargs.items():
            extra[key] = value
        self.logger.log(level, message, extra=extra)

# 创建全局日志器
logger = StructuredLogger(__name__)

# 请求跟踪中间件
class RequestTrackingMiddleware:
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # 生成唯一请求ID
            request_id = str(uuid.uuid4())
            start_time = time.time()
            
            # 获取基本请求信息
            method = scope.get("method", "UNKNOWN")
            path = scope.get("path", "unknown")
            client_info = scope.get("client", ("unknown", 0))
            client_ip = client_info[0] if client_info else "unknown"
            
            # 记录请求开始
            logger.info(
                f"Request started: {method} {path}",
                request_id=request_id,
                path=path,
                method=method,
                client_ip=client_ip
            )
            
            # 将request_id添加到scope中，以便在路由中使用
            scope["request_id"] = request_id
            
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    # 记录响应状态
                    status_code = message["status"]
                    duration = time.time() - start_time
                    
                    logger.info(
                        f"Request completed: {method} {path} - Status: {status_code}",
                        request_id=request_id,
                        path=path,
                        status=status_code,
                        duration=f"{duration:.3f}s"
                    )
                
                await send(message)
            
            try:
                await self.app(scope, receive, send_wrapper)
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Request failed: {method} {path} - Error: {str(e)}",
                    request_id=request_id,
                    path=path,
                    error_type=type(e).__name__,
                    duration=f"{duration:.3f}s",
                    stack_trace=traceback.format_exc()
                )
                raise
        else:
            await self.app(scope, receive, send)

app = FastAPI(title="图片房间分类服务",
              description="使用Gemini AI分析图片是否为房间并识别房间类型", version="1.0.0")

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

# Gemini API密钥 - 从环境变量读取
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.critical("Missing GEMINI_API_KEY environment variable")
    raise ValueError("请设置环境变量 GEMINI_API_KEY")

# 并行处理配置
DOWNLOAD_TIMEOUT = int(os.getenv("DOWNLOAD_TIMEOUT", "15"))  # 下载超时时间(秒)
MAX_CONCURRENT_DOWNLOADS = int(
    os.getenv("MAX_CONCURRENT_DOWNLOADS", "5"))  # 最大并发下载数
MAX_CONCURRENT_ANALYSIS = int(
    os.getenv("MAX_CONCURRENT_ANALYSIS", "3"))  # 最大并发分析数

logger.info(
    "Service configuration loaded",
    download_timeout=DOWNLOAD_TIMEOUT,
    max_concurrent_downloads=MAX_CONCURRENT_DOWNLOADS,
    max_concurrent_analysis=MAX_CONCURRENT_ANALYSIS
)

# 创建下载信号量和分析信号量，用于控制并发
download_semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)
analysis_semaphore = asyncio.Semaphore(MAX_CONCURRENT_ANALYSIS)

# 全局会话对象，重用HTTP连接
session = requests.Session()
session.verify = False  # 禁用SSL验证（仅用于测试）
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
})

# 性能监控装饰器
def monitor_performance(operation_name):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            # 更智能地获取request_id
            request_id = kwargs.get('request_id', 'unknown')
            if request_id == 'unknown' and len(args) > 0:
                # 尝试从参数中找到request_id
                for arg in args:
                    if isinstance(arg, str) and len(arg) == 36 and '-' in arg:
                        request_id = arg
                        break
            
            logger.debug(
                f"开始 {operation_name}",
                request_id=request_id
            )
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.info(
                    f"{operation_name} 完成",
                    request_id=request_id,
                    耗时=f"{duration:.3f}s"
                )
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                
                logger.error(
                    f"{operation_name} 失败: {str(e)}",
                    request_id=request_id,
                    error_type=type(e).__name__,
                    耗时=f"{duration:.3f}s",
                    stack_trace=traceback.format_exc()
                )
                raise
        return wrapper
    return decorator

# 异步性能监控装饰器
def monitor_async_performance(operation_name):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            # 更智能地获取request_id
            request_id = kwargs.get('request_id', 'unknown')
            if request_id == 'unknown' and len(args) > 0:
                # 尝试从参数中找到request_id
                for arg in args:
                    if isinstance(arg, str) and len(arg) == 36 and '-' in arg:
                        request_id = arg
                        break
            
            logger.debug(
                f"开始 {operation_name}",
                request_id=request_id
            )
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.info(
                    f"{operation_name} 完成",
                    request_id=request_id,
                    耗时=f"{duration:.3f}s"
                )
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                
                logger.error(
                    f"{operation_name} 失败: {str(e)}",
                    request_id=request_id,
                    error_type=type(e).__name__,
                    耗时=f"{duration:.3f}s",
                    stack_trace=traceback.format_exc()
                )
                raise
        return wrapper
    return decorator

# ----------------- 业务逻辑函数 -----------------

def extract_image_url_from_google_search(google_url, request_id='unknown'):
    try:
        logger.debug(
            f"Extracting image URL from Google search URL: {google_url}",
            request_id=request_id,
            url=google_url
        )
        
        parsed = urlparse(google_url)
        query_params = parse_qs(parsed.query)
        if 'imgurl' in query_params:
            extracted_url = query_params['imgurl'][0]
            logger.info(
                f"Successfully extracted image URL from query params: {extracted_url}",
                request_id=request_id,
                original_url=google_url,
                extracted_url=extracted_url
            )
            return extracted_url
            
        if 'imgurl=' in google_url:
            match = re.search(r'imgurl=([^&]+)', google_url)
            if match:
                extracted_url = match.group(1)
                logger.info(
                    f"Successfully extracted image URL using regex: {extracted_url}",
                    request_id=request_id,
                    original_url=google_url,
                    extracted_url=extracted_url
                )
                return extracted_url
        
        logger.warning(
            f"Could not extract image URL from Google search URL",
            request_id=request_id,
            url=google_url
        )
        return None
    except Exception as e:
        logger.error(
            f"Error extracting image URL from Google search URL: {str(e)}",
            request_id=request_id,
            url=google_url,
            error_type=type(e).__name__,
            stack_trace=traceback.format_exc()
        )
        return None

def is_likely_image_url(url):
    """根据URL扩展名判断是否可能为图片"""
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif',
                        '.bmp', '.webp', '.tiff', '.tif')
    return any(url.lower().endswith(ext) for ext in image_extensions)

def is_valid_image_mime_type(content_type, url):
    """检查MIME类型或URL扩展名是否表示图片"""
    content_type = content_type.lower()

    # 标准图片MIME类型
    if content_type.startswith('image/'):
        return True

    # 允许 application/octet-stream，但需要URL看起来像图片
    if content_type == 'application/octet-stream' and is_likely_image_url(url):
        return True

    # 其他可能的二进制类型，如果URL看起来像图片
    binary_types = ['application/binary',
                    'binary/octet-stream', 'application/unknown']
    if content_type in binary_types and is_likely_image_url(url):
        return True

    return False

@monitor_performance("Image Download")
def download_image(url, request_id='unknown'):
    try:
        logger.info(
            f"Starting image download",
            request_id=request_id,
            url=url,
            timeout=DOWNLOAD_TIMEOUT
        )
        
        start_time = time.time()
        response = session.get(url, timeout=DOWNLOAD_TIMEOUT)
        response.raise_for_status()
        
        content_type = response.headers.get('content-type', '').lower()
        content_length = response.headers.get('content-length', 'unknown')
        
        logger.debug(
            f"Received response",
            request_id=request_id,
            url=url,
            status_code=response.status_code,
            content_type=content_type,
            content_length=content_length
        )

        # 检查是否为HTML页面
        if 'text/html' in content_type:
            error_msg = "URL返回的是HTML页面，不是图片文件。请使用直接的图片URL，而不是Google搜索页面URL"
            logger.error(
                error_msg,
                request_id=request_id,
                url=url,
                content_type=content_type
            )
            raise Exception(error_msg)

        # 使用更智能的MIME类型检查
        if not is_valid_image_mime_type(content_type, url):
            # 如果MIME类型不匹配，但URL看起来像图片，给出警告但继续处理
            if is_likely_image_url(url):
                logger.warning(
                    f"MIME type {content_type} is not standard image type, but URL appears to be image, attempting to continue",
                    request_id=request_id,
                    url=url,
                    content_type=content_type
                )
                # 为 application/octet-stream 设置默认图片类型
                if content_type == 'application/octet-stream':
                    if url.lower().endswith(('.jpg', '.jpeg')):
                        content_type = 'image/jpeg'
                    elif url.lower().endswith('.png'):
                        content_type = 'image/png'
                    elif url.lower().endswith('.gif'):
                        content_type = 'image/gif'
                    elif url.lower().endswith('.webp'):
                        content_type = 'image/webp'
                    else:
                        content_type = 'image/jpeg'  # 默认为jpeg
            else:
                error_msg = f"不支持的MIME类型: {content_type}"
                logger.error(
                    error_msg,
                    request_id=request_id,
                    url=url,
                    content_type=content_type
                )
                raise Exception(error_msg)

        image_data = base64.b64encode(response.content).decode('utf-8')
        download_time = time.time() - start_time
        
        logger.info(
            f"Image download completed successfully",
            request_id=request_id,
            url=url,
            duration=f"{download_time:.3f}s",
            content_type=content_type,
            data_size=len(response.content)
        )
        
        return image_data, content_type
        
    except requests.exceptions.SSLError as e:
        error_msg = f"SSL连接失败，请检查图片URL是否正确"
        logger.error(
            f"SSL connection error: {str(e)}",
            request_id=request_id,
            url=url,
            error_type=type(e).__name__,
            stack_trace=traceback.format_exc()
        )
        raise Exception(error_msg)
    except requests.exceptions.Timeout as e:
        error_msg = f"下载超时，请检查图片URL是否可访问或增加超时设置"
        logger.error(
            f"Download timeout: {str(e)}",
            request_id=request_id,
            url=url,
            timeout=DOWNLOAD_TIMEOUT,
            error_type=type(e).__name__
        )
        raise Exception(error_msg)
    except requests.exceptions.RequestException as e:
        error_msg = f"网络请求失败: {str(e)}"
        logger.error(
            f"Network request error: {str(e)}",
            request_id=request_id,
            url=url,
            error_type=type(e).__name__,
            stack_trace=traceback.format_exc()
        )
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"无法下载图片: {str(e)}"
        logger.error(
            f"Image download failed: {str(e)}",
            request_id=request_id,
            url=url,
            error_type=type(e).__name__,
            stack_trace=traceback.format_exc()
        )
        raise Exception(error_msg)


def ensure_valid_mime_type_for_gemini(mime_type, url=None, request_id='unknown'):
    """确保MIME类型是Gemini API支持的格式"""
    logger.debug(
        f"Validating MIME type for Gemini API",
        request_id=request_id,
        original_mime_type=mime_type,
        url=url
    )
    
    # Gemini API支持的图片MIME类型
    supported_types = [
        'image/jpeg', 'image/jpg', 'image/png', 'image/gif',
        'image/webp', 'image/bmp', 'image/tiff'
    ]

    mime_type = mime_type.lower()

    # 如果已经是支持的类型，直接返回
    if mime_type in supported_types:
        logger.debug(
            f"MIME type is already supported",
            request_id=request_id,
            mime_type=mime_type
        )
        return mime_type

    # 如果是 application/octet-stream 或其他二进制类型，根据URL推断
    if mime_type in ['application/octet-stream', 'application/binary', 'binary/octet-stream']:
        if url:
            if url.lower().endswith(('.jpg', '.jpeg')):
                converted_type = 'image/jpeg'
            elif url.lower().endswith('.png'):
                converted_type = 'image/png'
            elif url.lower().endswith('.gif'):
                converted_type = 'image/gif'
            elif url.lower().endswith('.webp'):
                converted_type = 'image/webp'
            elif url.lower().endswith('.bmp'):
                converted_type = 'image/bmp'
            elif url.lower().endswith(('.tiff', '.tif')):
                converted_type = 'image/tiff'
            else:
                converted_type = 'image/jpeg'  # 默认为jpeg
        else:
            converted_type = 'image/jpeg'  # 默认返回 jpeg
            
        logger.info(
            f"Converted binary MIME type based on URL extension",
            request_id=request_id,
            original_mime_type=mime_type,
            converted_mime_type=converted_type,
            url=url
        )
        return converted_type

    # 如果是其他 image/ 类型，尝试映射到支持的类型
    if mime_type.startswith('image/'):
        if 'jpeg' in mime_type or 'jpg' in mime_type:
            converted_type = 'image/jpeg'
        elif 'png' in mime_type:
            converted_type = 'image/png'
        elif 'gif' in mime_type:
            converted_type = 'image/gif'
        elif 'webp' in mime_type:
            converted_type = 'image/webp'
        elif 'bmp' in mime_type:
            converted_type = 'image/bmp'
        elif 'tiff' in mime_type or 'tif' in mime_type:
            converted_type = 'image/tiff'
        else:
            converted_type = 'image/jpeg'  # 默认返回 jpeg
            
        logger.info(
            f"Mapped image MIME type to supported format",
            request_id=request_id,
            original_mime_type=mime_type,
            converted_mime_type=converted_type
        )
        return converted_type

    # 默认返回 jpeg
    logger.warning(
        f"Unknown MIME type, defaulting to image/jpeg",
        request_id=request_id,
        original_mime_type=mime_type
    )
    return 'image/jpeg'


@monitor_performance("Gemini Image Analysis")
def analyze_image_with_gemini(image_data, mime_type, include_description=True, url=None, request_id='unknown'):
    try:
        logger.info(
            f"Starting Gemini image analysis",
            request_id=request_id,
            url=url,
            mime_type=mime_type,
            include_description=include_description,
            data_size=len(image_data) if image_data else 0
        )
        
        start_time = time.time()
        # 确保MIME类型是Gemini API支持的格式
        safe_mime_type = ensure_valid_mime_type_for_gemini(mime_type, url, request_id)
        if safe_mime_type != mime_type:
            logger.info(
                f"MIME type converted for Gemini API compatibility",
                request_id=request_id,
                original_mime_type=mime_type,
                converted_mime_type=safe_mime_type
            )

        logger.debug(
            f"Initializing Gemini client",
            request_id=request_id
        )
        
        client = genai.Client(api_key=GEMINI_API_KEY)
        model = "gemini-2.0-flash-lite"
        
        logger.debug(
            f"Using Gemini model: {model}",
            request_id=request_id,
            model=model
        )
        
        if include_description:
            system_prompt = """Analyze the provided image and determine if it is a room, then provide a structured description.\n\nDefinition:\nA \"room\" is defined as an interior space within a building, intended for human occupancy or activity.\n\nRoom Types:\n[\"客厅\", \"家庭室\", \"餐厅\", \"厨房\", \"主卧室\", \"卧室\", \"客房\", \"卫生间\", \"浴室\", \"书房\", \"家庭办公室\", \"洗衣房\", \"储藏室\", \"食品储藏间\", \"玄关\", \"门厅\", \"走廊\", \"阳台\", \"地下室\", \"阁楼\", \"健身房\", \"家庭影院\", \"游戏室\", \"娱乐室\", \"其他\"]\n\nRules:\n1. Analyze the content of the image carefully.\n2. Determine if the image matches the definition of a \"room\".\n3. If it's a room, identify the room type from the list above.\n4. You MUST return ONLY a valid JSON object in the following format:\n{\n    \"is_room\": true/false,\n    \"room_type\": \"房型名称（从列表中选一个）\",\n    \"basic_info\": \"基本信息：精炼描述整体风格与布局\",\n    \"features\": \"特点：用最精炼的语言一句话描述最显著特点\"\n}\n\nDescription Guidelines:\n- room_type: 必须从提供的房型列表中选择一个，如果不匹配任何类型则选择\"其他\"\n- basic_info: 侧重整体风格与布局，用精炼语言描述\n- features: 用一句话描述最显著的特点\n\nIMPORTANT: Return ONLY the JSON object, no other text or explanation."""
            logger.debug("Using detailed analysis prompt", request_id=request_id)
        else:
            system_prompt = """Analyze the provided image and determine if it is a room.\n\nDefinition:\nA \"room\" is defined as an interior space within a building, intended for human occupancy or activity.\n\nRules:\n1. Analyze the content of the image carefully.\n2. Determine if the image matches the definition of a \"room\".\n3. You MUST return ONLY a valid JSON object in the following format:\n{\n    \"is_room\": true/false\n}\n\nIMPORTANT: Return ONLY the JSON object, no other text or explanation."""
            logger.debug("Using basic analysis prompt", request_id=request_id)
        logger.debug(
            f"Preparing API request content",
            request_id=request_id,
            mime_type=safe_mime_type,
            image_data_length=len(image_data)
        )
        
        content = types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(
                    mime_type=safe_mime_type,
                    data=base64.b64decode(image_data)
                ),
            ],
        )
        generate_content_config = types.GenerateContentConfig(
            system_instruction=[
                types.Part.from_text(text=system_prompt),
            ],
            response_mime_type="text/plain",
        )
        
        logger.info(
            f"Sending request to Gemini API",
            request_id=request_id,
            model=model
        )
        
        api_start_time = time.time()
        response = client.models.generate_content(
            model=model,
            contents=content,
            config=generate_content_config,
        )
        api_duration = time.time() - api_start_time
        
        logger.info(
            f"Received response from Gemini API",
            request_id=request_id,
            api_duration=f"{api_duration:.3f}s"
        )
        
        result_text = response.text.strip() if response.text else ""
        
        logger.debug(
            f"Raw Gemini response",
            request_id=request_id,
            response_length=len(result_text),
            response_preview=result_text[:200] + "..." if len(result_text) > 200 else result_text
        )
        
        try:
            import json
            result_json = json.loads(result_text)
            if 'is_room' not in result_json:
                raise ValueError("JSON格式不完整")
            is_room = result_json['is_room']
            if include_description:
                room_type = result_json.get('room_type', '其他')
                basic_info = result_json.get('basic_info', '')
                features = result_json.get('features', '')
                description = {
                    'room_type': room_type,
                    'basic_info': basic_info,
                    'features': features
                }
            else:
                description = {}
            analysis_time = time.time() - start_time
            
            logger.info(
                f"Successfully parsed Gemini response as JSON",
                request_id=request_id,
                is_room=is_room,
                room_type=room_type if include_description else None,
                analysis_duration=f"{analysis_time:.3f}s"
            )
            
            return is_room, description
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(
                f"Gemini response is not valid JSON format, attempting alternative parsing",
                request_id=request_id,
                error_type=type(e).__name__,
                raw_response=result_text[:500] + "..." if len(result_text) > 500 else result_text
            )
            
            result_text_lower = result_text.lower()
            is_room = False
            if 'true' in result_text_lower or '是房间' in result_text or '房间' in result_text:
                is_room = True
                
            try:
                if '```json' in result_text:
                    logger.debug(
                        f"Attempting to extract JSON from code block",
                        request_id=request_id
                    )
                    json_start = result_text.find('```json') + 7
                    json_end = result_text.find('```', json_start)
                    if json_end != -1:
                        json_content = result_text[json_start:json_end].strip()
                        json_obj = json.loads(json_content)
                        room_type = json_obj.get('room_type', '其他')
                        basic_info = json_obj.get('basic_info', '')
                        features = json_obj.get('features', '')
                        if 'is_room' in json_obj:
                            is_room = json_obj['is_room']
                        description = {
                            'room_type': room_type,
                            'basic_info': basic_info,
                            'features': features
                        }
                        analysis_time = time.time() - start_time
                        
                        logger.info(
                            f"Successfully extracted JSON from code block",
                            request_id=request_id,
                            is_room=is_room,
                            room_type=room_type,
                            analysis_duration=f"{analysis_time:.3f}s"
                        )
                        
                        return is_room, description
            except Exception as parse_error:
                logger.warning(
                    f"Failed to parse JSON from code block",
                    request_id=request_id,
                    error_type=type(parse_error).__name__,
                    error_message=str(parse_error)
                )
                
            if include_description:
                description = {
                    'room_type': '其他' if is_room else '',
                    'basic_info': result_text[:100] + "..." if len(result_text) > 100 else result_text,
                    'features': '图片分析成功，但无法提取详细特点'
                }
            else:
                description = {}
            analysis_time = time.time() - start_time
            
            logger.info(
                f"Completed analysis with fallback parsing",
                request_id=request_id,
                is_room=is_room,
                analysis_duration=f"{analysis_time:.3f}s",
                parsing_method="fallback"
            )
            
            return is_room, description
    except Exception as e:
        logger.error(
            f"Gemini analysis failed with exception",
            request_id=request_id,
            error_type=type(e).__name__,
            error_message=str(e),
            stack_trace=traceback.format_exc()
        )
        raise Exception(f"图片分析失败: {str(e)}")

# ----------------- FastAPI接口 -----------------


class AnalyzeRoomRequest(BaseModel):
    url: Union[str, List[str]]
    include_description: Optional[bool] = True













@monitor_async_performance("Process Single Image")
async def process_image(image_url, include_description, request_id='unknown'):
    """处理单个图片的异步函数"""
    try:
        logger.info(
            f"Starting image processing",
            request_id=request_id,
            url=image_url,
            include_description=include_description
        )
        
        if not image_url:
            error_msg = '图片URL不能为空'
            logger.error(
                error_msg,
                request_id=request_id,
                url=image_url
            )
            return {
                'url': image_url,
                'success': False,
                'error': error_msg
            }

        actual_image_url = image_url
        if 'google.com/imgres' in image_url:
            logger.debug(
                f"Detected Google search URL, extracting actual image URL",
                request_id=request_id,
                google_url=image_url
            )
            
            extracted_url = extract_image_url_from_google_search(image_url, request_id)
            if extracted_url:
                actual_image_url = extracted_url
                logger.info(
                    f"Successfully extracted actual image URL from Google search",
                    request_id=request_id,
                    original_url=image_url,
                    extracted_url=actual_image_url
                )
            else:
                error_msg = '无法从Google搜索URL中提取图片URL'
                logger.error(
                    error_msg,
                    request_id=request_id,
                    google_url=image_url
                )
                return {
                    'url': image_url,
                    'success': False,
                    'error': error_msg
                }

        logger.info(
            f"Starting image processing workflow",
            request_id=request_id,
            final_url=actual_image_url
        )
        
        # 下载图片(使用信号量控制并发)
        async with download_semaphore:
            logger.debug(
                f"Acquired download semaphore",
                request_id=request_id,
                url=actual_image_url
            )
            
            try:
                # 在异步环境中调用同步函数
                loop = asyncio.get_event_loop()
                image_data, mime_type = await loop.run_in_executor(
                    None,
                    functools.partial(download_image, actual_image_url, request_id)
                )
            except Exception as e:
                logger.error(
                    f"Image download failed",
                    request_id=request_id,
                    url=actual_image_url,
                    error_type=type(e).__name__,
                    error_message=str(e)
                )
                return {
                    'url': image_url,
                    'success': False,
                    'error': str(e)
                }

        # 分析图片(使用信号量控制并发)
        async with analysis_semaphore:
            logger.debug(
                f"Acquired analysis semaphore",
                request_id=request_id,
                url=actual_image_url
            )
            
            try:
                # 在异步环境中调用同步函数
                is_room, description = await loop.run_in_executor(
                    None,
                    functools.partial(
                        analyze_image_with_gemini,
                        image_data,
                        mime_type,
                        include_description,
                        actual_image_url,
                        request_id
                    )
                )
            except Exception as e:
                logger.error(
                    f"Image analysis failed",
                    request_id=request_id,
                    url=actual_image_url,
                    error_type=type(e).__name__,
                    error_message=str(e)
                )
                return {
                    'url': image_url,
                    'success': False,
                    'error': str(e)
                }

        logger.info(
            f"Image processing completed successfully",
            request_id=request_id,
            url=actual_image_url,
            is_room=is_room,
            room_type=description.get('room_type', None) if include_description else None
        )
        
        result_item = {
            'url': image_url,
            'actual_url': actual_image_url if actual_image_url != image_url else None,
            'success': True,
            'is_room': is_room
        }

        if include_description:
            result_item['description'] = description

        return result_item
    except Exception as e:
        logger.error(
            f"Unexpected error during image processing",
            request_id=request_id,
            url=image_url,
            error_type=type(e).__name__,
            error_message=str(e),
            stack_trace=traceback.format_exc()
        )
        return {
            'url': image_url,
            'success': False,
            'error': str(e)
        }


@app.post("/analyze_room")
async def analyze_room(request: AnalyzeRoomRequest, http_request: Request):
    # 生成request_id
    request_id = str(uuid.uuid4())
    
    try:
        start_time = time.time()
        urls = request.url
        include_description = request.include_description
        
        logger.info(
            f"Starting batch image analysis request",
            request_id=request_id,
            urls_count=len(urls) if isinstance(urls, list) else 1,
            include_description=include_description,
            raw_urls=urls if isinstance(urls, list) else [urls]
        )

        # 参数验证
        if isinstance(urls, str):
            urls = [urls]
        if not urls or not isinstance(urls, list):
            error_msg = 'URL参数必须是字符串或数组'
            logger.error(
                error_msg,
                request_id=request_id,
                received_urls=urls,
                urls_type=type(urls).__name__
            )
            return JSONResponse(status_code=400, content={
                'success': False,
                'error': error_msg
            })

        # 验证URL不能为空
        empty_urls = [i for i, url in enumerate(urls) if not url or not str(url).strip()]
        if empty_urls:
            error_msg = f'URL数组中的第{empty_urls}个位置包含空URL'
            logger.error(
                error_msg,
                request_id=request_id,
                empty_url_indices=empty_urls,
                total_urls=len(urls)
            )
            return JSONResponse(status_code=400, content={
                'success': False,
                'error': error_msg
            })

        logger.info(
            f"Starting parallel processing of {len(urls)} images",
            request_id=request_id,
            max_concurrent_downloads=MAX_CONCURRENT_DOWNLOADS,
            max_concurrent_analysis=MAX_CONCURRENT_ANALYSIS
        )

        # 并行处理所有图片
        tasks = [process_image(url, include_description, request_id) for url in urls]
        results = await asyncio.gather(*tasks)

        # 统计结果
        total_time = time.time() - start_time
        
        logger.info(
            f"Batch processing completed",
            request_id=request_id,
            total_images=len(urls),
            total_duration=f"{total_time:.3f}s"
        )

        # 记录失败的URL
        failed_urls = [result for result in results if not result.get('success', False)]
        if failed_urls:
            logger.warning(
                f"Some images failed to process",
                request_id=request_id,
                failed_count=len(failed_urls),
                failed_urls=[r.get('url', 'unknown') for r in failed_urls[:5]]  # 只记录前5个
            )



        return {
            'success': True,
            'total': len(urls),
            'processing_time': f"{total_time:.3f}s",
            'results': results
        }
    except Exception as e:
        total_time = time.time() - start_time
        logger.error(
            f"Batch processing failed with exception",
            request_id=request_id,
            error_type=type(e).__name__,
            error_message=str(e),
            duration=f"{total_time:.3f}s",
            stack_trace=traceback.format_exc()
        )
        return JSONResponse(status_code=500, content={
            'success': False,
            'request_id': request_id,
            'error': str(e),
            'error_type': type(e).__name__
        })
