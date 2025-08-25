"""
异步处理器
用于处理房源内容生成和数据库存储
"""
import asyncio
import logging
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from ..core.config import settings
from ..core.database import (
    init_database_pool,
    insert_room_analysis,
    update_room_analysis_status,
    get_room_analysis
)
from ..services.gemini_service import GeminiService
from ..utils.content_generator import ContentGenerator
from ..utils.content_formatter import ContentFormatter

logger = logging.getLogger(__name__)


class AsyncContentProcessor:
    """异步内容处理器"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=settings.ASYNC_MAX_WORKERS)
        self.max_retries = settings.ASYNC_MAX_RETRIES
        self.retry_delay = settings.ASYNC_RETRY_DELAY
        self.gemini_service = GeminiService()

    async def process_content_async(self, room_id: str, business_type: str, 
                                  image_urls: List[str], request_id: str) -> None:
        """异步处理内容生成和存储"""
        try:
            logger.info(f"开始异步处理: {room_id}, 请求ID: {request_id}")
            
            # 1. 创建初始记录
            existing_record = await get_room_analysis(room_id)
            if not existing_record:
                await insert_room_analysis(room_id, business_type, processing_status="pending")
                logger.info(f"创建初始记录: {room_id}")
            
            # 2. 更新状态为处理中
            await self.update_processing_status(room_id, "processing")

            # 3. 生成“特征JSON”内容（替换旧的自然语言描述方案）
            features_json = await self.generate_features_with_retry(image_urls, request_id)

            if not features_json:
                features_json = ContentGenerator.default_features()

            # 4. 存储到数据库（直接以JSON字符串存入content字段）
            import json as _json
            content_json = _json.dumps(features_json, ensure_ascii=False)
            await self.save_to_database_with_retry(room_id, business_type, content_json)

            # 5. 更新处理状态为完成
            await self.update_processing_status(room_id, "completed", content_json)

            logger.info(f"异步处理完成: {room_id}")

        except Exception as e:
            logger.error(f"异步处理失败: {room_id}, 错误: {e}")
            await self.update_processing_status(room_id, "failed", error=str(e))

    async def generate_content_with_retry(self, image_urls: List[str], 
                                        business_type: str, request_id: str) -> Optional[Dict[str, str]]:
        """（保留旧接口，未使用）"""
        for attempt in range(self.max_retries):
            try:
                logger.info(f"尝试生成内容 (第{attempt + 1}次): {request_id}")
                
                # 生成prompt
                prompt = ContentGenerator.generate_room_content_prompt(business_type)
                
                # 调用Gemini服务生成内容
                response = await self.gemini_service.generate_content_async(image_urls, prompt)
                
                if not response:
                    raise ValueError("Gemini服务返回空响应")

                # 解析AI响应
                content = ContentGenerator.parse_ai_response(response)
                
                if content:
                    # 验证生成的内容
                    validation = ContentGenerator.validate_generated_content(content)
                    if validation["is_valid"]:
                        logger.info(f"内容生成成功: {request_id}")
                        return content
                    else:
                        logger.warning(f"内容质量验证失败: {request_id}")
                        # 使用备用内容
                        content = ContentGenerator.generate_fallback_content(business_type)
                        return content
                else:
                    raise ValueError("AI响应解析失败")

            except Exception as e:
                logger.error(f"内容生成失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")

                if attempt == self.max_retries - 1:
                    # 最后一次尝试失败，使用备用内容
                    logger.info(f"使用备用内容: {request_id}")
                    return ContentGenerator.generate_fallback_content(business_type)
                else:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))

    async def generate_features_with_retry(self, image_urls: List[str], request_id: str) -> Optional[Dict[str, bool]]:
        """特征JSON生成带重试机制（支持本地联调绕过AI）"""
        import os as _os
        # 若强制要求使用Gemini，则不允许绕过
        if _os.getenv("DISABLE_GEMINI", "").lower() == "true":
            raise RuntimeError("DISABLE_GEMINI is not allowed when GEMINI usage is enforced.")
        if not self.gemini_service or not getattr(self.gemini_service, 'client', None):
            raise RuntimeError("Gemini client not initialized. Ensure GEMINI_API_KEY is set.")
        for attempt in range(self.max_retries):
            try:
                logger.info(f"尝试生成特征JSON (第{attempt + 1}次): {request_id}")

                prompt = ContentGenerator.generate_room_features_prompt()
                response = await self.gemini_service.generate_content_async(image_urls, prompt)

                if not response:
                    raise ValueError("Gemini服务返回空响应")

                features = ContentGenerator.parse_features_ai_response(response)
                if features:
                    return features
                else:
                    raise ValueError("特征JSON解析失败")

            except Exception as e:
                logger.error(f"特征JSON生成失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    return ContentGenerator.default_features()
                await asyncio.sleep(self.retry_delay * (attempt + 1))

    async def save_to_database_with_retry(self, room_id: str, business_type: str, 
                                        content: str) -> None:
        """数据库存储带重试机制"""
        for attempt in range(self.max_retries):
            try:
                logger.info(f"尝试存储到数据库 (第{attempt + 1}次): {room_id}")
                
                # 更新现有记录的内容
                await update_room_analysis_status(room_id, "completed", content)
                logger.info(f"更新记录内容: {room_id}")
                
                return

            except Exception as e:
                logger.error(f"数据库存储失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")

                if attempt == self.max_retries - 1:
                    raise
                else:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))

    async def update_processing_status(self, room_id: str, processing_status: str, 
                                     content: str = None, error: str = None) -> None:
        """更新处理状态"""
        try:
            if content:
                await update_room_analysis_status(room_id, processing_status, content)
            else:
                await update_room_analysis_status(room_id, processing_status)
            
            logger.info(f"状态更新: {room_id} -> {processing_status}")
            
        except Exception as e:
            logger.error(f"状态更新失败: {room_id}, 错误: {e}")

    async def get_processing_status(self, room_id: str) -> Optional[Dict[str, Any]]:
        """获取处理状态"""
        try:
            record = await get_room_analysis(room_id)
            if record:
                return {
                    "room_id": record["room_id"],
                    "business_type": record["business_type"],
                    "processing_status": record["processing_status"],
                    "content": ContentFormatter.parse_content_from_storage(record["content"]),
                    "created_at": record["created_at"],
                    "updated_at": record["updated_at"]
                }
            return None
        except Exception as e:
            logger.error(f"获取处理状态失败: {room_id}, 错误: {e}")
            return None

    def cleanup(self):
        """清理资源"""
        try:
            if hasattr(self, 'executor') and self.executor:
                logger.info("正在关闭线程池...")
                # 修复：ThreadPoolExecutor.shutdown() 不支持 timeout 参数
                self.executor.shutdown(wait=True)
                logger.info("线程池已关闭")
            
            # 清理Gemini服务
            if hasattr(self, 'gemini_service'):
                logger.info("正在清理Gemini服务...")
                # 这里可以添加Gemini服务的清理逻辑
                
            logger.info("异步处理器清理完成")
        except Exception as e:
            logger.error(f"异步处理器清理失败: {e}")


# 全局异步处理器实例
async_processor = AsyncContentProcessor() 