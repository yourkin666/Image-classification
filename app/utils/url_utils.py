import re
from urllib.parse import urlparse, parse_qs
from ..core.logging import logger


def extract_image_url_from_google_search(google_url, request_id='unknown'):
    """从Google搜索URL中提取图片URL"""
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
            error_type=type(e).__name__
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