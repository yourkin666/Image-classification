import asyncio
import functools
import uuid
import time
from ..core.logging import logger
from ..core.config import settings
from ..utils.image_utils import download_image
from ..utils.url_utils import extract_image_url_from_google_search
from .gemini_service import analyze_image_with_gemini


# 创建下载信号量和分析信号量，用于控制并发
download_semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_DOWNLOADS)
analysis_semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_ANALYSIS)


async def process_image(image_url, request_id='unknown'):
    """处理单个图片的异步函数"""
    try:
        logger.info(
            f"Starting image processing",
            request_id=request_id,
            url=image_url
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
                download_result = await loop.run_in_executor(
                    None,
                    functools.partial(download_image, actual_image_url, request_id)
                )
                image_data = download_result['image_data']
                mime_type = download_result['mime_type']
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
                is_room = await loop.run_in_executor(
                    None,
                    functools.partial(
                        analyze_image_with_gemini,
                        image_data,
                        mime_type,
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
            is_room=is_room
        )
        
        result_item = {
            'url': image_url,
            'success': True,
            'is_room': is_room
        }

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


async def process_batch_images(urls, request_id):
    """批处理多个图片"""
    try:
        logger.info(
            f"Starting parallel processing of {len(urls)} images",
            request_id=request_id,
            urls_count=len(urls)
        )
        
        # 创建任务列表
        tasks = [process_image(url, request_id) for url in urls]
        
        # 并发执行所有任务
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    f"Task {i} failed with exception",
                    request_id=request_id,
                    url=urls[i],
                    error_type=type(result).__name__,
                    error_message=str(result)
                )
                processed_results.append({
                    'url': urls[i],
                    'success': False,
                    'error': str(result)
                })
            else:
                processed_results.append(result)
        
        logger.info(
            f"Batch processing completed",
            request_id=request_id,
            total_images=len(urls),
            successful_results=sum(1 for r in processed_results if r['success'])
        )
        
        return processed_results
        
    except Exception as e:
        logger.error(
            f"Batch processing failed",
            request_id=request_id,
            error_type=type(e).__name__,
            error_message=str(e)
        )
        # 返回所有失败的结果
        return [{
            'url': url,
            'success': False,
            'error': str(e)
        } for url in urls] 