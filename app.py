import os
import base64
import requests
import re
from urllib.parse import urlparse, parse_qs
from io import BytesIO
from flask import Flask, request, jsonify
from google import genai
from google.genai import types
from dotenv import load_dotenv
import logging

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 配置Gemini API密钥
GEMINI_API_KEY = "AIzaSyCpZZmlwgbyPjIp6XQNCQIN7R8LzCl3-3g"


def extract_image_url_from_google_search(google_url):
    """
    从Google图片搜索URL中提取实际的图片URL
    """
    try:
        # 解析URL参数
        parsed = urlparse(google_url)
        query_params = parse_qs(parsed.query)

        # 提取imgurl参数
        if 'imgurl' in query_params:
            return query_params['imgurl'][0]

        # 如果没有imgurl参数，尝试从URL中提取
        if 'imgurl=' in google_url:
            match = re.search(r'imgurl=([^&]+)', google_url)
            if match:
                return match.group(1)

        return None
    except Exception as e:
        logger.error(f"提取图片URL失败: {str(e)}")
        return None


def download_image(url):
    """
    从URL下载图片并返回base64编码
    """
    try:
        # 添加SSL验证选项和重试机制
        session = requests.Session()
        session.verify = False  # 禁用SSL验证（仅用于测试）

        # 设置请求头，模拟浏览器
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = session.get(url, timeout=30, headers=headers)
        response.raise_for_status()

        # 检查Content-Type
        content_type = response.headers.get('content-type', '').lower()
        if 'text/html' in content_type:
            raise Exception(
                f"URL返回的是HTML页面，不是图片文件。请使用直接的图片URL，而不是Google搜索页面URL")

        if not content_type.startswith('image/'):
            raise Exception(f"不支持的MIME类型: {content_type}")

        # 将图片转换为base64
        image_data = base64.b64encode(response.content).decode('utf-8')
        return image_data, content_type

    except requests.exceptions.SSLError as e:
        logger.error(f"SSL连接错误: {str(e)}")
        raise Exception(f"SSL连接失败，请检查图片URL是否正确")
    except requests.exceptions.RequestException as e:
        logger.error(f"网络请求错误: {str(e)}")
        raise Exception(f"网络请求失败: {str(e)}")
    except Exception as e:
        logger.error(f"下载图片失败: {str(e)}")
        raise Exception(f"无法下载图片: {str(e)}")


def analyze_image_with_gemini(image_data, mime_type, include_description=True):
    """
    使用Gemini大模型分析图片是否为房间并描述内容
    Args:
        image_data: base64编码的图片数据
        mime_type: 图片的MIME类型
        include_description: 是否包含详细描述，默认为True
    """
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        model = "gemini-2.5-pro"

        # 根据是否包含描述选择不同的系统提示词
        if include_description:
            # 完整的系统提示词 - 要求返回JSON格式
            system_prompt = """Analyze the provided image and determine if it is a room, then provide a structured description.

Definition:
A "room" is defined as an interior space within a building, intended for human occupancy or activity.

Room Types:
["客厅", "家庭室", "餐厅", "厨房", "主卧室", "卧室", "客房", "卫生间", "浴室", "书房", "家庭办公室", "洗衣房", "储藏室", "食品储藏间", "玄关", "门厅", "走廊", "阳台", "地下室", "阁楼", "健身房", "家庭影院", "游戏室", "娱乐室", "其他"]

Rules:
1. Analyze the content of the image carefully.
2. Determine if the image matches the definition of a "room".
3. If it's a room, identify the room type from the list above.
4. You MUST return ONLY a valid JSON object in the following format:
{
    "is_room": true/false,
    "room_type": "房型名称（从列表中选一个）",
    "basic_info": "基本信息：精炼描述整体风格与布局",
    "features": "特点：用最精炼的语言一句话描述最显著特点"
}

Description Guidelines:
- room_type: 必须从提供的房型列表中选择一个，如果不匹配任何类型则选择"其他"
- basic_info: 侧重整体风格与布局，用精炼语言描述
- features: 用一句话描述最显著的特点

IMPORTANT: Return ONLY the JSON object, no other text or explanation."""
        else:
            # 简化的系统提示词 - 只判断是否为房间
            system_prompt = """Analyze the provided image and determine if it is a room.

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

        # 创建内容
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_bytes(
                        mime_type=mime_type,
                        data=base64.b64decode(image_data)
                    ),
                ],
            ),
        ]

        # 配置生成参数
        generate_content_config = types.GenerateContentConfig(
            system_instruction=[
                types.Part.from_text(text=system_prompt),
            ],
            response_mime_type="text/plain",
        )

        # 调用Gemini API
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=generate_content_config,
        )

        result_text = response.text.strip()

        # 尝试解析JSON响应
        try:
            import json
            result_json = json.loads(result_text)

            # 验证JSON格式
            if 'is_room' not in result_json:
                raise ValueError("JSON格式不完整")

            # 提取is_room字段
            is_room = result_json['is_room']

            if include_description:
                # 提取详细描述字段
                room_type = result_json.get('room_type', '其他')
                basic_info = result_json.get('basic_info', '')
                features = result_json.get('features', '')

                # 构建结构化描述
                description = {
                    'room_type': room_type,
                    'basic_info': basic_info,
                    'features': features
                }
            else:
                # 不包含描述时，返回空的结构
                description = {}

            return is_room, description

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Gemini返回的不是有效JSON格式: {result_text}")

            # 尝试从文本中提取信息
            result_text_lower = result_text.lower()

            # 判断是否为房间
            is_room = False
            if 'true' in result_text_lower or '是房间' in result_text or '房间' in result_text:
                is_room = True

            # 尝试从文本中提取结构化信息
            try:
                # 查找JSON格式的内容
                if '```json' in result_text:
                    json_start = result_text.find('```json') + 7
                    json_end = result_text.find('```', json_start)
                    if json_end != -1:
                        json_content = result_text[json_start:json_end].strip()
                        json_obj = json.loads(json_content)

                        # 提取结构化信息
                        room_type = json_obj.get('room_type', '其他')
                        basic_info = json_obj.get('basic_info', '')
                        features = json_obj.get('features', '')

                        # 更新is_room状态
                        if 'is_room' in json_obj:
                            is_room = json_obj['is_room']

                        description = {
                            'room_type': room_type,
                            'basic_info': basic_info,
                            'features': features
                        }
                        return is_room, description
            except:
                pass

            # 如果无法解析，返回默认结构
            if include_description:
                description = {
                    'room_type': '其他' if is_room else '',
                    'basic_info': result_text[:100] + "..." if len(result_text) > 100 else result_text,
                    'features': '图片分析成功，但无法提取详细特点'
                }
            else:
                description = {}

            return is_room, description

    except Exception as e:
        logger.error(f"Gemini分析失败: {str(e)}")
        raise Exception(f"图片分析失败: {str(e)}")


@app.route('/analyze_room', methods=['POST'])
def analyze_room():
    """
    分析图片是否为房间的API端点
    支持单个URL或URL数组
    参数:
    - url: 图片URL或URL数组
    - include_description: 是否包含详细描述，默认为True
    """
    try:
        # 获取请求数据
        data = request.get_json()

        if not data or 'url' not in data:
            return jsonify({
                'success': False,
                'error': '缺少图片URL参数'
            }), 400

        urls = data['url']
        # 获取是否包含描述的开关，默认为True
        include_description = data.get('include_description', True)

        # 处理单个URL的情况
        if isinstance(urls, str):
            urls = [urls]

        # 验证URL数组
        if not urls or not isinstance(urls, list):
            return jsonify({
                'success': False,
                'error': 'URL参数必须是字符串或数组'
            }), 400

        results = []

        for i, image_url in enumerate(urls):
            try:
                if not image_url:
                    results.append({
                        'url': image_url,
                        'success': False,
                        'error': '图片URL不能为空'
                    })
                    continue

                # 检查是否是Google图片搜索URL
                actual_image_url = image_url
                if 'google.com/imgres' in image_url:
                    extracted_url = extract_image_url_from_google_search(
                        image_url)
                    if extracted_url:
                        actual_image_url = extracted_url
                        logger.info(
                            f"从Google搜索URL提取到实际图片URL: {actual_image_url}")
                    else:
                        results.append({
                            'url': image_url,
                            'success': False,
                            'error': '无法从Google搜索URL中提取图片URL'
                        })
                        continue

                logger.info(f"开始分析第{i+1}张图片: {actual_image_url}")

                # 下载图片
                image_data, mime_type = download_image(actual_image_url)

                # 使用Gemini分析
                is_room, description = analyze_image_with_gemini(
                    image_data, mime_type, include_description)

                logger.info(
                    f"第{i+1}张图片分析完成，结果: {'是房间' if is_room else '不是房间'}")

                # 构建返回结果
                result_item = {
                    'url': image_url,
                    'actual_url': actual_image_url if actual_image_url != image_url else None,
                    'success': True,
                    'is_room': is_room
                }

                # 根据开关决定是否包含描述
                if include_description:
                    result_item['description'] = description

                results.append(result_item)

            except Exception as e:
                logger.error(f"处理第{i+1}张图片时发生错误: {str(e)}")
                results.append({
                    'url': image_url,
                    'success': False,
                    'error': str(e)
                })

        return jsonify({
            'success': True,
            'total': len(urls),
            'results': results
        })

    except Exception as e:
        logger.error(f"处理请求时发生错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """
    健康检查端点
    """
    return jsonify({
        'status': 'healthy',
        'service': 'image-room-classifier'
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
