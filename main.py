import os
import base64
import requests
import re
import asyncio
import functools
import time
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

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="图片房间分类服务",
              description="使用Gemini AI分析图片是否为房间并识别房间类型", version="1.0.0")

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
    raise ValueError("请设置环境变量 GEMINI_API_KEY")

# 并行处理配置
DOWNLOAD_TIMEOUT = int(os.getenv("DOWNLOAD_TIMEOUT", "15"))  # 下载超时时间(秒)
MAX_CONCURRENT_DOWNLOADS = int(
    os.getenv("MAX_CONCURRENT_DOWNLOADS", "5"))  # 最大并发下载数
MAX_CONCURRENT_ANALYSIS = int(
    os.getenv("MAX_CONCURRENT_ANALYSIS", "3"))  # 最大并发分析数

# 创建下载信号量和分析信号量，用于控制并发
download_semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)
analysis_semaphore = asyncio.Semaphore(MAX_CONCURRENT_ANALYSIS)

# 全局会话对象，重用HTTP连接
session = requests.Session()
session.verify = False  # 禁用SSL验证（仅用于测试）
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
})

# ----------------- 业务逻辑函数 -----------------


def extract_image_url_from_google_search(google_url):
    try:
        parsed = urlparse(google_url)
        query_params = parse_qs(parsed.query)
        if 'imgurl' in query_params:
            return query_params['imgurl'][0]
        if 'imgurl=' in google_url:
            match = re.search(r'imgurl=([^&]+)', google_url)
            if match:
                return match.group(1)
        return None
    except Exception as e:
        logger.error(f"提取图片URL失败: {str(e)}")
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


def download_image(url):
    try:
        start_time = time.time()
        response = session.get(url, timeout=DOWNLOAD_TIMEOUT)
        response.raise_for_status()
        content_type = response.headers.get('content-type', '').lower()

        # 检查是否为HTML页面
        if 'text/html' in content_type:
            raise Exception(
                "URL返回的是HTML页面，不是图片文件。请使用直接的图片URL，而不是Google搜索页面URL")

        # 使用更智能的MIME类型检查
        if not is_valid_image_mime_type(content_type, url):
            # 如果MIME类型不匹配，但URL看起来像图片，给出警告但继续处理
            if is_likely_image_url(url):
                logger.warning(
                    f"MIME类型 {content_type} 不是标准图片类型，但URL似乎是图片，尝试继续处理")
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
                raise Exception(f"不支持的MIME类型: {content_type}")

        image_data = base64.b64encode(response.content).decode('utf-8')
        download_time = time.time() - start_time
        logger.info(f"图片下载完成，用时: {download_time:.2f}秒, URL: {url}")
        return image_data, content_type
    except requests.exceptions.SSLError as e:
        logger.error(f"SSL连接错误: {str(e)}")
        raise Exception(f"SSL连接失败，请检查图片URL是否正确")
    except requests.exceptions.Timeout as e:
        logger.error(f"下载超时: {str(e)}")
        raise Exception(f"下载超时，请检查图片URL是否可访问或增加超时设置")
    except requests.exceptions.RequestException as e:
        logger.error(f"网络请求错误: {str(e)}")
        raise Exception(f"网络请求失败: {str(e)}")
    except Exception as e:
        logger.error(f"下载图片失败: {str(e)}")
        raise Exception(f"无法下载图片: {str(e)}")


def ensure_valid_mime_type_for_gemini(mime_type, url=None):
    """确保MIME类型是Gemini API支持的格式"""
    # Gemini API支持的图片MIME类型
    supported_types = [
        'image/jpeg', 'image/jpg', 'image/png', 'image/gif',
        'image/webp', 'image/bmp', 'image/tiff'
    ]

    mime_type = mime_type.lower()

    # 如果已经是支持的类型，直接返回
    if mime_type in supported_types:
        return mime_type

    # 如果是 application/octet-stream 或其他二进制类型，根据URL推断
    if mime_type in ['application/octet-stream', 'application/binary', 'binary/octet-stream']:
        if url:
            if url.lower().endswith(('.jpg', '.jpeg')):
                return 'image/jpeg'
            elif url.lower().endswith('.png'):
                return 'image/png'
            elif url.lower().endswith('.gif'):
                return 'image/gif'
            elif url.lower().endswith('.webp'):
                return 'image/webp'
            elif url.lower().endswith('.bmp'):
                return 'image/bmp'
            elif url.lower().endswith(('.tiff', '.tif')):
                return 'image/tiff'
        # 默认返回 jpeg
        return 'image/jpeg'

    # 如果是其他 image/ 类型，尝试映射到支持的类型
    if mime_type.startswith('image/'):
        if 'jpeg' in mime_type or 'jpg' in mime_type:
            return 'image/jpeg'
        elif 'png' in mime_type:
            return 'image/png'
        elif 'gif' in mime_type:
            return 'image/gif'
        elif 'webp' in mime_type:
            return 'image/webp'
        elif 'bmp' in mime_type:
            return 'image/bmp'
        elif 'tiff' in mime_type or 'tif' in mime_type:
            return 'image/tiff'

    # 默认返回 jpeg
    return 'image/jpeg'


def analyze_image_with_gemini(image_data, mime_type, include_description=True, url=None):
    try:
        start_time = time.time()
        # 确保MIME类型是Gemini API支持的格式
        safe_mime_type = ensure_valid_mime_type_for_gemini(mime_type, url)
        if safe_mime_type != mime_type:
            logger.info(
                f"将MIME类型从 {mime_type} 转换为 {safe_mime_type} 以兼容Gemini API")

        client = genai.Client(api_key=GEMINI_API_KEY)
        model = "gemini-2.0-flash-lite"
        if include_description:
            system_prompt = """Analyze the provided image and determine if it is a room, then provide a structured description.\n\nDefinition:\nA \"room\" is defined as an interior space within a building, intended for human occupancy or activity.\n\nRoom Types:\n[\"客厅\", \"家庭室\", \"餐厅\", \"厨房\", \"主卧室\", \"卧室\", \"客房\", \"卫生间\", \"浴室\", \"书房\", \"家庭办公室\", \"洗衣房\", \"储藏室\", \"食品储藏间\", \"玄关\", \"门厅\", \"走廊\", \"阳台\", \"地下室\", \"阁楼\", \"健身房\", \"家庭影院\", \"游戏室\", \"娱乐室\", \"其他\"]\n\nRules:\n1. Analyze the content of the image carefully.\n2. Determine if the image matches the definition of a \"room\".\n3. If it's a room, identify the room type from the list above.\n4. You MUST return ONLY a valid JSON object in the following format:\n{\n    \"is_room\": true/false,\n    \"room_type\": \"房型名称（从列表中选一个）\",\n    \"basic_info\": \"基本信息：精炼描述整体风格与布局\",\n    \"features\": \"特点：用最精炼的语言一句话描述最显著特点\"\n}\n\nDescription Guidelines:\n- room_type: 必须从提供的房型列表中选择一个，如果不匹配任何类型则选择\"其他\"\n- basic_info: 侧重整体风格与布局，用精炼语言描述\n- features: 用一句话描述最显著的特点\n\nIMPORTANT: Return ONLY the JSON object, no other text or explanation."""
        else:
            system_prompt = """Analyze the provided image and determine if it is a room.\n\nDefinition:\nA \"room\" is defined as an interior space within a building, intended for human occupancy or activity.\n\nRules:\n1. Analyze the content of the image carefully.\n2. Determine if the image matches the definition of a \"room\".\n3. You MUST return ONLY a valid JSON object in the following format:\n{\n    \"is_room\": true/false\n}\n\nIMPORTANT: Return ONLY the JSON object, no other text or explanation."""
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
        response = client.models.generate_content(
            model=model,
            contents=content,
            config=generate_content_config,
        )
        result_text = response.text.strip() if response.text else ""
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
            logger.info(f"图片分析完成，用时: {analysis_time:.2f}秒")
            return is_room, description
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Gemini返回的不是有效JSON格式: {result_text}")
            result_text_lower = result_text.lower()
            is_room = False
            if 'true' in result_text_lower or '是房间' in result_text or '房间' in result_text:
                is_room = True
            try:
                if '```json' in result_text:
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
                        logger.info(f"图片分析完成(从代码块解析)，用时: {analysis_time:.2f}秒")
                        return is_room, description
            except:
                pass
            if include_description:
                description = {
                    'room_type': '其他' if is_room else '',
                    'basic_info': result_text[:100] + "..." if len(result_text) > 100 else result_text,
                    'features': '图片分析成功，但无法提取详细特点'
                }
            else:
                description = {}
            analysis_time = time.time() - start_time
            logger.info(f"图片分析完成(非标准格式)，用时: {analysis_time:.2f}秒")
            return is_room, description
    except Exception as e:
        logger.error(f"Gemini分析失败: {str(e)}")
        raise Exception(f"图片分析失败: {str(e)}")

# ----------------- FastAPI接口 -----------------


class AnalyzeRoomRequest(BaseModel):
    url: Union[str, List[str]]
    include_description: Optional[bool] = True


@app.get("/")
def index():
    return {
        'service': '图片房间分类服务',
        'version': '1.0.0',
        'description': '使用Gemini AI分析图片是否为房间并识别房间类型',
        'endpoints': {
            'POST /analyze_room': {
                'description': '分析图片是否为房间',
                'parameters': {
                    'url': '图片URL或URL数组（字符串或数组）',
                    'include_description': '是否包含详细描述（布尔值，默认true）'
                },
                'example': {
                    'url': 'https://example.com/image.jpg',
                    'include_description': True
                }
            },
            'GET /health': {
                'description': '健康检查',
                'response': {
                    'status': 'healthy',
                    'service': 'image-room-classifier'
                }
            }
        },
        'usage': '发送POST请求到 /analyze_room 端点，包含图片URL进行分析'
    }


@app.get("/health")
async def health():
    return {
        'status': 'healthy',
        'service': 'image-room-classifier'
    }


async def process_image(image_url, include_description):
    """处理单个图片的异步函数"""
    try:
        if not image_url:
            return {
                'url': image_url,
                'success': False,
                'error': '图片URL不能为空'
            }

        actual_image_url = image_url
        if 'google.com/imgres' in image_url:
            extracted_url = extract_image_url_from_google_search(image_url)
            if extracted_url:
                actual_image_url = extracted_url
                logger.info(f"从Google搜索URL提取到实际图片URL: {actual_image_url}")
            else:
                return {
                    'url': image_url,
                    'success': False,
                    'error': '无法从Google搜索URL中提取图片URL'
                }

        logger.info(f"开始处理图片: {actual_image_url}")
        # 下载图片(使用信号量控制并发)
        async with download_semaphore:
            try:
                # 在异步环境中调用同步函数
                loop = asyncio.get_event_loop()
                image_data, mime_type = await loop.run_in_executor(
                    None,
                    functools.partial(download_image, actual_image_url)
                )
            except Exception as e:
                return {
                    'url': image_url,
                    'success': False,
                    'error': str(e)
                }

        # 分析图片(使用信号量控制并发)
        async with analysis_semaphore:
            try:
                # 在异步环境中调用同步函数
                is_room, description = await loop.run_in_executor(
                    None,
                    functools.partial(
                        analyze_image_with_gemini,
                        image_data,
                        mime_type,
                        include_description,
                        actual_image_url
                    )
                )
            except Exception as e:
                return {
                    'url': image_url,
                    'success': False,
                    'error': str(e)
                }

        logger.info(f"图片分析完成，结果: {'是房间' if is_room else '不是房间'}")
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
        logger.error(f"处理图片时发生错误: {str(e)}")
        return {
            'url': image_url,
            'success': False,
            'error': str(e)
        }


@app.post("/analyze_room")
async def analyze_room(request: AnalyzeRoomRequest):
    try:
        start_time = time.time()
        urls = request.url
        include_description = request.include_description

        if isinstance(urls, str):
            urls = [urls]
        if not urls or not isinstance(urls, list):
            return JSONResponse(status_code=400, content={
                'success': False,
                'error': 'URL参数必须是字符串或数组'
            })

        # 并行处理所有图片
        tasks = [process_image(url, include_description) for url in urls]
        results = await asyncio.gather(*tasks)

        total_time = time.time() - start_time
        logger.info(
            f"批量处理完成 {len(urls)} 张图片，总用时: {total_time:.2f}秒，平均每张: {total_time/len(urls):.2f}秒")

        return {
            'success': True,
            'total': len(urls),
            'processing_time': f"{total_time:.2f}秒",
            'results': results
        }
    except Exception as e:
        logger.error(f"处理请求时发生错误: {str(e)}")
        return JSONResponse(status_code=500, content={
            'success': False,
            'error': str(e)
        })
