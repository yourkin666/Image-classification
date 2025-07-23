import asyncio
import functools
import uuid
import time
from ..core.logging import logger
from ..core.config import settings
from ..utils.image_utils import download_image
from ..utils.url_utils import extract_image_url_from_google_search
from ..utils.decorators import monitor_async_performance
from .gemini_service import analyze_image_with_gemini


# 创建下载信号量和分析信号量，用于控制并发
download_semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_DOWNLOADS)
analysis_semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_ANALYSIS)


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
            error_message=str(e)
        )
        return {
            'url': image_url,
            'success': False,
            'error': str(e)
        }


async def process_batch_images(urls, include_description, request_id):
    """批处理多个图片"""
    logger.info(
        f"Starting parallel processing of {len(urls)} images",
        request_id=request_id,
        max_concurrent_downloads=settings.MAX_CONCURRENT_DOWNLOADS,
        max_concurrent_analysis=settings.MAX_CONCURRENT_ANALYSIS
    )

    # 并行处理所有图片
    tasks = [process_image(url, include_description, request_id) for url in urls]
    results = await asyncio.gather(*tasks)

    # 记录失败的URL
    failed_urls = [result for result in results if not result.get('success', False)]
    if failed_urls:
        logger.warning(
            f"Some images failed to process",
            request_id=request_id,
            failed_count=len(failed_urls),
            failed_urls=[r.get('url', 'unknown') for r in failed_urls[:5]]  # 只记录前5个
        )

    return results 