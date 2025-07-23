import time
import uuid
import traceback
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from ....schemas.requests import AnalyzeRoomRequest, AnalyzeRoomResponse
from ....core.logging import logger
from ....services.image_service import process_batch_images

router = APIRouter()


@router.post("/analyze_room", response_model=AnalyzeRoomResponse)
async def analyze_room(request: AnalyzeRoomRequest, http_request: Request):
    """分析图片是否为房间"""
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

        # 处理图片
        results = await process_batch_images(urls, include_description, request_id)

        # 统计结果
        total_time = time.time() - start_time
        
        logger.info(
            f"Batch processing completed",
            request_id=request_id,
            total_images=len(urls),
            total_duration=f"{total_time:.3f}s"
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