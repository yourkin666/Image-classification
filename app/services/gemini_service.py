import base64
import time
import json
import traceback
import asyncio
from typing import List, Optional
from google import genai
from google.genai import types
from ..core.logging import logger
from ..core.config import settings
from ..utils.url_utils import ensure_valid_mime_type_for_gemini


def analyze_image_with_gemini(image_data, mime_type, url=None, request_id='unknown'):
    """使用Gemini AI分析图片是否为房间"""
    try:
        logger.info(
            f"Starting Gemini image analysis",
            request_id=request_id,
            url=url,
            mime_type=mime_type,
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
        
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        model = "gemini-2.0-flash-lite"
        
        logger.debug(
            f"Using Gemini model: {model}",
            request_id=request_id,
            model=model
        )
        
        # 简化的prompt，只判断是否为房间
        system_prompt = """Analyze the image and determine if it shows a room.

Definition:
A "room" is defined as an interior space within a building, intended for human occupancy or activity.

Rules:
1. Analyze the content of the image carefully.
2. Determine if the image matches the definition of a "room".
3. You MUST return ONLY a valid JSON object in the following format:
{
    "is_room": true/false
}

IMPORTANT: Return ONLY the JSON object, no other text or explanation."""
        
        logger.debug("Using basic room analysis prompt", request_id=request_id)
        
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
            response_text=result_text
        )
        
        # 解析JSON响应
        try:
            result_json = json.loads(result_text)
            is_room = result_json.get('is_room', False)
            
            logger.info(
                f"Successfully parsed Gemini response",
                request_id=request_id,
                is_room=is_room
            )
            
            return is_room
            
        except json.JSONDecodeError as e:
            logger.debug(
                f"Failed to parse JSON response from Gemini, using fallback parsing",
                request_id=request_id,
                response_text=result_text,
                error=str(e)
            )
            # 如果JSON解析失败，尝试从文本中推断
            if 'true' in result_text.lower():
                return True
            elif 'false' in result_text.lower():
                return False
            else:
                # 默认返回False
                return False
                
    except Exception as e:
        logger.error(
            f"Gemini image analysis failed",
            request_id=request_id,
            url=url,
            error_type=type(e).__name__,
            error_message=str(e),
            stack_trace=traceback.format_exc()
        )
        raise


class GeminiService:
    """Gemini AI服务类"""
    
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = "gemini-2.0-flash-lite"
    
    async def generate_content_async(self, image_urls: List[str], prompt: str) -> Optional[str]:
        """异步生成内容"""
        try:
            logger.info(f"开始异步内容生成: {len(image_urls)} 张图片")
            
            if not image_urls:
                raise ValueError("没有提供图片URL")
            
            # 准备所有图片数据
            parts = [types.Part.from_text(text=prompt)]
            
            import requests
            
            for i, image_url in enumerate(image_urls):
                try:
                    logger.info(f"下载第{i+1}张图片: {image_url}")
                    response = requests.get(image_url, timeout=30)
                    response.raise_for_status()
                    
                    mime_type = response.headers.get('content-type', 'image/jpeg')
                    logger.info(f"图片{i+1}下载成功, 大小: {len(response.content)} 字节")
                    
                    # 添加图片到parts
                    parts.append(
                        types.Part.from_bytes(
                            mime_type=mime_type,
                            data=response.content
                        )
                    )
                    
                except Exception as e:
                    logger.warning(f"图片{i+1}下载失败: {image_url}, 错误: {e}")
                    continue
            
            if len(parts) == 1:  # 只有prompt，没有图片
                raise ValueError("没有成功下载任何图片")
            
            logger.info(f"成功准备 {len(parts)-1} 张图片用于分析")
            
            # 调用Gemini API
            content = types.Content(
                role="user",
                parts=parts,
            )
            
            logger.info(f"发送内容生成请求，包含 {len(parts)-1} 张图片")
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=content,
            )
            
            result_text = response.text.strip() if response.text else ""
            logger.info(f"内容生成完成, 响应长度: {len(result_text)}")
            
            return result_text
            
        except Exception as e:
            logger.error(f"内容生成失败: {e}")
            return None 