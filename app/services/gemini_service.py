import base64
import time
import json
import traceback
from google import genai
from google.genai import types
from ..core.logging import logger
from ..core.config import settings
from ..utils.decorators import monitor_performance
from ..utils.url_utils import ensure_valid_mime_type_for_gemini


@monitor_performance("Gemini Image Analysis")
def analyze_image_with_gemini(image_data, mime_type, include_description=True, url=None, request_id='unknown'):
    """使用Gemini AI分析图片"""
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
        
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
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