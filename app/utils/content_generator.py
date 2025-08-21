"""
房源内容生成工具
"""
import json
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class ContentGenerator:
    """房源内容生成器"""
    
    @staticmethod
    def generate_room_content_prompt(business_type: str) -> str:
        """生成房源内容生成的prompt"""
        base_prompt = """仔细分析所有房源图片，从以下四个维度生成具体、实际的房源描述：

重要：这是同一套房源的多张图片，请综合分析所有图片信息，生成一个连贯、完整的房源描述，避免信息重复或冲突。

1. 采光与居住舒适度
   - 综合分析所有房间的采光情况（如：客厅大落地窗朝南采光充足、卧室小窗朝北光线柔和等）
   - 整体通风条件（如：客厅阳台通风好、卧室窗户可开启、整体空气流通等）
   - 居住舒适度（如：温度适宜、湿度适中、环境安静等）

2. 装修品质与维护状况
   - 整体装修风格（如：现代简约风格、欧式古典、中式传统、北欧清新等）
   - 墙面、地面、天花板材质和状况（如：白墙干净、木地板保养好、吊顶简洁等）
   - 家具品质和保养情况（如：家具崭新、略有磨损、保养良好等）
   - 整体美观度和细节处理（如：装修精致、细节到位、整体协调等）

3. 空间感与布局
   - 整体空间布局（如：客厅宽敞明亮、卧室私密安静、厨房功能齐全等）
   - 功能区域划分（如：客厅开放、卧室独立、厨房半开放、卫生间干湿分离等）
   - 储物空间设计（如：衣柜充足、储物柜合理、收纳空间大等）
   - 动线规划和空间利用率（如：动线流畅、空间利用充分、布局合理等）

4. 电器与设施（重要：必须综合识别所有图片中的可见物品）
   - 仔细识别所有图片中的家具：床、沙发、桌椅、衣柜、书柜、茶几、电视柜、床头柜、梳妆台、餐桌、餐椅、书桌、办公椅等
   - 仔细识别所有图片中的电器：空调、电视、冰箱、洗衣机、热水器、微波炉、电饭煲、电磁炉、油烟机、电风扇、加湿器、空气净化器等
   - 仔细识别所有图片中的生活设施：厨房设备（灶台、水槽、橱柜）、卫浴设施（马桶、淋浴、浴缸、洗手台）、照明设备（吊灯、台灯、壁灯、吸顶灯）、窗帘、地毯、装饰画等
   - 仔细识别所有图片中的智能化设备：智能门锁、智能家电、网络设备、监控设备等
   - 重要：必须在appliances_facilities字段中列出所有图片中可见的具体家具电器名称，避免重复

要求：
- 每个维度用1-2句话描述，总长度不超过100字符
- 语言要具体实际，避免虚泛描述，使用具体的形容词和名词
- 重点描述可见的具体物品和设施，不要使用"设施完善"、"配置齐全"等虚泛词汇
- 综合分析所有图片信息，生成连贯、不突兀的描述
- 严格控制字数，避免冗长描述
- 对于appliances_facilities字段，必须仔细识别所有图片中可见的具体家具电器，并列出名称，避免重复

appliances_facilities字段格式要求：
- 综合所有图片看到的家具电器：appliances_facilities: "配备床、衣柜、沙发、电视、空调、冰箱等完整家具电器"
- 如果看到客厅和卧室的不同设施：appliances_facilities: "配备沙发、茶几、电视、床、衣柜、空调、热水器等生活家具电器"
- 如果看到办公区域：appliances_facilities: "配备书桌、书柜、电脑、床、衣柜、空调等办公生活家具电器"
- 如果看不到具体物品：appliances_facilities: "图片中可见的家具电器有限"

禁止使用的虚泛词汇：
- 设施完善、配置齐全、生活便利、便捷舒适
- 满足需求、基础电器、生活设施、设备齐全
- 配置完善、设施齐全、生活便利、满足日常需求

必须使用的具体词汇：
- 家具：床、沙发、桌子、椅子、衣柜、书柜、茶几、电视柜、床头柜、梳妆台、餐桌、餐椅、书桌、办公椅
- 电器：空调、电视、冰箱、洗衣机、热水器、微波炉、电饭煲、电磁炉、油烟机、电风扇、加湿器、空气净化器
- 设施：厨房设备、卫浴设施、照明设备、窗帘、地毯、装饰画

请按以下JSON格式返回：
{
    "lighting_comfort": "采光与居住舒适度描述(不超过100字符)",
    "decoration_quality": "装修品质与维护状况描述(不超过100字符)",
    "space_layout": "空间感与布局描述(不超过100字符)",
    "appliances_facilities": "具体列出所有图片中的家具电器设施(不超过100字符)"
}

重要提醒：请综合分析所有图片，在appliances_facilities字段中列出您能看到的家具电器，如床、沙发、桌子、椅子、衣柜、空调、电视等。如果图片中看不到具体物品，请说明"图片中可见的家具电器有限"。

最终要求：appliances_facilities字段必须包含具体的家具电器名称，不能使用任何虚泛描述。综合分析所有图片信息，生成连贯、完整的房源描述。
"""

        # 根据业务类型调整prompt
        business_prompts = {
            "whole_rent": base_prompt + "\n\n重点关注：整租房的完整性和私密性，适合家庭或长期居住。综合分析所有房间图片，电器设施要完整齐全，必须仔细识别并列出所有图片中可见的家具电器。",
            "centralized": base_prompt + "\n\n重点关注：集中式公寓的标准化和便利性，适合年轻白领。综合分析所有房间图片，设施配置要现代化，必须仔细识别并列出所有图片中可见的家具电器。",
            "shared_rent": base_prompt + "\n\n重点关注：合租房的共享空间和性价比，适合预算有限的租客。综合分析所有房间图片，基础设施要齐全，必须仔细识别并列出所有图片中可见的家具电器。"
        }

        return business_prompts.get(business_type, base_prompt)

    @staticmethod
    def parse_ai_response(response_text: str) -> Optional[Dict[str, str]]:
        """解析AI响应内容"""
        try:
            # 尝试直接解析JSON
            if response_text.strip().startswith('{') and response_text.strip().endswith('}'):
                content_dict = json.loads(response_text)
            else:
                # 尝试提取JSON部分
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = response_text[start_idx:end_idx]
                    content_dict = json.loads(json_str)
                else:
                    logger.error("无法在响应中找到JSON格式内容")
                    return None

            # 验证内容结构
            required_fields = ["lighting_comfort", "decoration_quality", "space_layout", "appliances_facilities"]
            if not all(field in content_dict for field in required_fields):
                logger.error("内容结构验证失败")
                return None

            # 清理和标准化内容
            for field in required_fields:
                if field in content_dict:
                    content_dict[field] = str(content_dict[field]).strip()
                    # 截断超长内容
                    if len(content_dict[field]) > 100:
                        content_dict[field] = content_dict[field][:97] + "..."

            return content_dict

        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            return None
        except Exception as e:
            logger.error(f"内容解析失败: {e}")
            return None

    @staticmethod
    def validate_generated_content(content: Dict[str, str]) -> Dict[str, any]:
        """验证生成的内容质量"""
        required_fields = ["lighting_comfort", "decoration_quality", "space_layout", "appliances_facilities"]
        
        # 检查必需字段
        missing_fields = [field for field in required_fields if field not in content]
        if missing_fields:
            return {
                "is_valid": False,
                "issues": f"缺少必需字段: {missing_fields}"
            }
        
        # 检查字段内容
        empty_fields = [field for field in required_fields if not content.get(field, "").strip()]
        if empty_fields:
            return {
                "is_valid": False,
                "issues": f"字段内容为空: {empty_fields}"
            }
        
        return {
            "is_valid": True,
            "issues": []
        }

    @staticmethod
    def generate_fallback_content(business_type: str) -> Dict[str, str]:
        """生成备用内容"""
        fallback_content = {
            "lighting_comfort": "房间采光充足，通风条件良好，居住环境舒适宜人",
            "decoration_quality": "装修风格现代简约，墙面地面保养良好，整体美观协调",
            "space_layout": "空间布局合理，功能分区明确，储物空间设计充足",
            "appliances_facilities": "配备床、衣柜、桌椅等基础家具，空调、热水器等生活电器"
        }
        
        # 根据业务类型调整
        if business_type == "whole_rent":
            fallback_content["space_layout"] = "空间宽敞明亮，布局合理流畅，适合家庭生活需求"
            fallback_content["appliances_facilities"] = "配备床、沙发、电视、冰箱、洗衣机等完整家具电器"
        elif business_type == "centralized":
            fallback_content["appliances_facilities"] = "配备床、衣柜、空调、热水器等标准化基础设备"
        elif business_type == "shared_rent":
            fallback_content["space_layout"] = "共享空间设计合理，性价比高，适合合租生活"
            fallback_content["appliances_facilities"] = "配备床、衣柜、空调等基础家具电器"
        
        return fallback_content 