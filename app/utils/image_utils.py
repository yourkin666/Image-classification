import base64
import time
import requests
import traceback
from ..core.logging import logger
from ..core.config import settings
from .url_utils import is_valid_image_mime_type, is_likely_image_url
from ..utils.decorators import monitor_performance


# 全局会话对象，重用HTTP连接
session = requests.Session()
session.verify = False  # 禁用SSL验证（仅用于测试）
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
})


@monitor_performance("Image Download")
def download_image(url, request_id='unknown'):
    """下载图片并返回base64编码的数据和MIME类型"""
    try:
        logger.info(
            f"Starting image download",
            request_id=request_id,
            url=url,
            timeout=settings.DOWNLOAD_TIMEOUT
        )
        
        start_time = time.time()
        response = session.get(url, timeout=settings.DOWNLOAD_TIMEOUT)
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
            timeout=settings.DOWNLOAD_TIMEOUT,
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