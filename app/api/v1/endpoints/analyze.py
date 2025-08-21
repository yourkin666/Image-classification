import time
import uuid
import traceback
import asyncio
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from ....schemas.requests import (
    AnalyzeRoomRequest, 
    AnalyzeRoomResponse, 
    ProcessingStatusResponse
)
from ....core.logging import logger
from ....services.image_service import process_batch_images
from ....services.async_processor import async_processor
from ....core.database import init_database_pool, close_database_pool

router = APIRouter()


@router.post("/analyze_room", response_model=AnalyzeRoomResponse)
async def analyze_room(request: AnalyzeRoomRequest, http_request: Request):
    """分析图片是否为房间"""
    request_id = str(uuid.uuid4())
    
    try:
        start_time = time.time()
        roomId = request.roomId
        business_type = request.business_type
        urls = request.url
        
        logger.info(
            f"Starting room analysis request",
            request_id=request_id,
            roomId=roomId,
            business_type=business_type,
            urls_count=len(urls) if isinstance(urls, list) else 1
        )

        # 参数验证
        if isinstance(urls, str):
            urls = [urls]
        if not urls or not isinstance(urls, list):
            error_msg = 'URL参数必须是字符串或数组'
            logger.error(error_msg, request_id=request_id)
            return JSONResponse(status_code=400, content={
                'success': False,
                'error': error_msg
            })

        # 验证URL不能为空
        empty_urls = [i for i, url in enumerate(urls) if not url or not str(url).strip()]
        if empty_urls:
            error_msg = f'URL数组中的第{empty_urls}个位置包含空URL'
            logger.error(error_msg, request_id=request_id)
            return JSONResponse(status_code=400, content={
                'success': False,
                'error': error_msg
            })

        # 1. 房间识别
        room_results = await process_batch_images(urls, request_id)

        # 2. 检查是否有房间（用于异步处理判断）
        has_room = any(result.get('is_room', False) for result in room_results)

        # 3. 返回详细的结果，包含每张图片的检测结果
        response = {
            'success': True,
            'results': room_results  # 每张图片的具体结果
        }

        # 4. 如果有房间，启动异步内容处理
        if has_room:
            task = asyncio.create_task(
                start_content_processing(
                    roomId,
                    business_type,
                    urls,
                    request_id
                )
            )
            task.add_done_callback(lambda t: logger.error(f"异步任务失败: {t.exception()}") if t.exception() else None)

        return response
    except Exception as e:
        total_time = time.time() - start_time
        logger.error(
            f"Room analysis failed",
            request_id=request_id,
            error_type=type(e).__name__,
            error_message=str(e)
        )
        return JSONResponse(status_code=500, content={
            'success': False,
            'request_id': request_id,
            'error': str(e),
            'error_type': type(e).__name__,
            'results': []  # 错误时返回空的结果数组
        })


async def start_content_processing(room_id: str, business_type: str, 
                                 image_urls: list, request_id: str):
    """启动异步内容处理"""
    try:
        await init_database_pool()
        await async_processor.process_content_async(
            room_id=room_id,
            business_type=business_type,
            image_urls=image_urls,
            request_id=request_id
        )
    except Exception as e:
        logger.error(f"启动异步内容处理失败: {room_id}, 错误: {e}")


@router.get("/status/{room_id}", response_model=ProcessingStatusResponse)
async def get_processing_status(room_id: str):
    """获取处理状态"""
    try:
        await init_database_pool()
        status_data = await async_processor.get_processing_status(room_id)
        
        if not status_data:
            raise HTTPException(status_code=404, detail="房间ID不存在")
        
        # 构建响应数据，确保content字段格式正确
        response_data = {
            'success': True,
            'room_id': status_data['room_id'],
            'business_type': status_data['business_type'],
            'processing_status': status_data['processing_status'],
            'created_at': status_data['created_at'].isoformat() if status_data['created_at'] else None,
            'updated_at': status_data['updated_at'].isoformat() if status_data['updated_at'] else None
        }
        
        # 处理content字段
        if status_data['content'] and isinstance(status_data['content'], dict):
            response_data['content'] = status_data['content']
        else:
            response_data['content'] = None
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取处理状态失败: {room_id}, 错误: {e}")
        raise HTTPException(status_code=500, detail=f"获取处理状态失败: {str(e)}")


@router.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库连接池"""
    try:
        await init_database_pool()
        logger.info("数据库连接池初始化成功")
    except Exception as e:
        logger.error(f"数据库连接池初始化失败: {e}")


@router.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    try:
        await close_database_pool()
        async_processor.cleanup()
        logger.info("资源清理完成")
    except Exception as e:
        logger.error(f"资源清理失败: {e}") 