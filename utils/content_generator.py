#!/usr/bin/env python3
"""
房源内容生成工具
基于四大维度生成租客关心的房源内容
"""

import json
from typing import Dict, Optional
from ..core.logging import logger


class ContentGenerator:
    """房源内容生成器"""
    
    # 内容长度限制配置
    MAX_CONTENT_LENGTH = 2 * 1024  # 2KB总长度限制
    MAX_DIMENSION_LENGTH = 100     # 每个维度最大100字符
    MAX_JSON_LENGTH = 1 * 1024     # JSON格式最大1KB
    
    @staticmethod
    def generate_room_content_prompt(business_type: str) -> str:
        """生成针对不同业务类型的内容生成prompt"""
        
        base_prompt = """分析房源图片，从以下四个维度生成租客关心的房源内容：

1. 采光与居住舒适度 (非常正面的信息)
   - 自然采光情况
   - 通风条件
   - 居住舒适度评估
   - 朝向优势

2. 装修品质与维护状况 (总体正面)
   - 装修风格和品质
   - 墙面、地面、天花板状况
   - 维护保养情况
   - 整体美观度

3. 空间感与布局 (有利的推断)
   - 空间大小和比例
   - 功能布局合理性
   - 储物空间设计
   - 动线规划

4. 电器与设施 (信息有限)
   - 基础电器配置
   - 生活设施完善度
   - 智能化程度
   - 便利性评估

要求：
- 每个维度用1-2句话描述，总长度不超过100字符
- 保持积极正面的语调
- 突出房源优势
- 语言简洁明了
- 适合租客阅读
- 如果某个维度信息不足，可以合理推断
- 严格控制字数，避免冗长描述

请按以下JSON格式返回：
{
    "lighting_comfort": "采光与居住舒适度描述(不超过100字符)",
    "decoration_quality": "装修品质与维护状况描述(不超过100字符)", 
    "space_layout": "空间感与布局描述(不超过100字符)",
    "appliances_facilities": "电器与设施描述(不超过100字符)"
}"""
        
        # 根据业务类型调整prompt
        business_prompts = {
            "whole_rent": base_prompt + "\n\n重点关注：整租房的完整性和私密性，适合家庭或长期居住",
            "centralized": base_prompt + "\n\n重点关注：集中式公寓的标准化和便利性，适合年轻白领",
            "shared_rent": base_prompt + "\n\n重点关注：合租房的共享空间和性价比，适合预算有限的租客"
        }
        
        return business_prompts.get(business_type, base_prompt)
    
    @staticmethod
    def validate_content_length(content_dict: Dict[str, str]) -> bool:
        """验证内容长度是否符合限制"""
        try:
            # 检查每个维度的长度
            for key, value in content_dict.items():
                if len(value) > ContentGenerator.MAX_DIMENSION_LENGTH:
                    logger.warning(f"维度 {key} 内容过长: {len(value)} 字符")
                    return False
            
            # 检查JSON总长度
            content_json = json.dumps(content_dict, ensure_ascii=False, separators=(',', ':'))
            if len(content_json.encode('utf-8')) > ContentGenerator.MAX_JSON_LENGTH:
                logger.warning(f"JSON内容过长: {len(content_json)} 字节")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"内容长度验证失败: {e}")
            return False
    
    @staticmethod
    def truncate_content(content_dict: Dict[str, str]) -> Dict[str, str]:
        """截断过长的内容"""
        truncated = {}
        for key, value in content_dict.items():
            if len(value) > ContentGenerator.MAX_DIMENSION_LENGTH:
                # 截断到最大长度，保留完整句子
                truncated_value = value[:ContentGenerator.MAX_DIMENSION_LENGTH-3] + "..."
                truncated[key] = truncated_value
                logger.info(f"截断维度 {key} 内容: {len(value)} -> {len(truncated_value)} 字符")
            else:
                truncated[key] = value
        return truncated
    
    @staticmethod
    def parse_content_response(response_text: str) -> Optional[Dict[str, str]]:
        """解析AI返回的内容响应"""
        try:
            # 尝试直接解析JSON
            if response_text.strip().startswith('{'):
                content_dict = json.loads(response_text)
            # 尝试提取JSON代码块
            elif '```json' in response_text:
                start = response_text.find('```json') + 7
                end = response_text.find('```', start)
                if end != -1:
                    json_content = response_text[start:end].strip()
                    content_dict = json.loads(json_content)
                else:
                    raise ValueError("JSON代码块格式不完整")
            else:
                # 尝试提取JSON部分
                import re
                json_pattern = r'\{[^{}]*"lighting_comfort"[^{}]*"decoration_quality"[^{}]*"space_layout"[^{}]*"appliances_facilities"[^{}]*\}'
                matches = re.findall(json_pattern, response_text, re.DOTALL)
                if matches:
                    content_dict = json.loads(matches[0])
                else:
                    logger.warning(f"无法解析内容响应: {response_text[:200]}...")
                    return None
            
            # 验证内容长度
            if not ContentGenerator.validate_content_length(content_dict):
                # 如果内容过长，进行截断
                content_dict = ContentGenerator.truncate_content(content_dict)
            
            return content_dict
            
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"解析内容响应失败: {e}")
            return None
    
    @staticmethod
    def generate_fallback_content(business_type: str) -> Dict[str, str]:
        """生成降级内容（当AI生成失败时使用）"""
        
        fallback_contents = {
            "whole_rent": {
                "lighting_comfort": "房间采光良好，通风条件优越，居住舒适度较高",
                "decoration_quality": "装修风格现代，维护状况良好，整体美观大方",
                "space_layout": "空间布局合理，功能分区明确，储物空间充足",
                "appliances_facilities": "图片中可见的家具电器有限"
            },
            "centralized": {
                "lighting_comfort": "公寓采光充足，通风良好，居住环境舒适",
                "decoration_quality": "标准化装修，品质可靠，维护状况良好",
                "space_layout": "空间利用合理，布局紧凑实用，功能齐全",
                "appliances_facilities": "图片中可见的家具电器有限"
            },
            "shared_rent": {
                "lighting_comfort": "房间采光适中，通风条件良好，居住舒适",
                "decoration_quality": "装修简洁实用，维护状况良好，性价比高",
                "space_layout": "空间布局紧凑，功能分区合理，储物空间充足",
                "appliances_facilities": "图片中可见的家具电器有限"
            }
        }
        
        return fallback_contents.get(business_type, fallback_contents["whole_rent"])


class ContentFormatter:
    """内容格式化工具"""
    
    @staticmethod
    def format_content_for_display(content_dict: Dict[str, str]) -> str:
        """将JSON内容格式化为可读文本"""
        sections = [
            f"🌟 采光与居住舒适度：{content_dict.get('lighting_comfort', '信息不足')}",
            f"🏠 装修品质与维护状况：{content_dict.get('decoration_quality', '信息不足')}",
            f"📐 空间感与布局：{content_dict.get('space_layout', '信息不足')}",
            f"🔌 电器与设施：{content_dict.get('appliances_facilities', '信息不足')}"
        ]
        return "\n".join(sections)
    
    @staticmethod
    def format_content_for_storage(content_dict: Dict[str, str]) -> str:
        """将内容格式化为存储格式（压缩JSON）"""
        return json.dumps(content_dict, ensure_ascii=False, separators=(',', ':'))
    
    @staticmethod
    def format_content_for_api(content_dict: Dict[str, str]) -> Dict[str, str]:
        """将内容格式化为API响应格式"""
        return {
            "content": content_dict,
            "formatted_content": ContentFormatter.format_content_for_display(content_dict)
        }
    
    @staticmethod
    def validate_content(content_dict: Dict[str, str]) -> bool:
        """验证内容格式是否正确"""
        required_keys = ["lighting_comfort", "decoration_quality", "space_layout", "appliances_facilities"]
        
        # 检查必需字段
        for key in required_keys:
            if key not in content_dict:
                logger.error(f"缺少必需字段: {key}")
                return False
            
            if not content_dict[key] or not content_dict[key].strip():
                logger.error(f"字段内容为空: {key}")
                return False
        
        # 检查内容长度
        return ContentGenerator.validate_content_length(content_dict)


# 使用示例
if __name__ == "__main__":
    # 测试内容生成
    generator = ContentGenerator()
    prompt = generator.generate_room_content_prompt("whole_rent")
    print("生成的Prompt:")
    print(prompt)
    
    # 测试内容格式化
    test_content = {
        "lighting_comfort": "房间采光充足，南北通透，居住舒适度很高",
        "decoration_quality": "装修风格现代简约，维护状况良好，整体美观大方",
        "space_layout": "空间布局合理，功能分区明确，储物空间充足",
        "appliances_facilities": "基础电器配置完善，生活设施齐全，便利性良好"
    }
    
    # 测试长度验证
    is_valid = ContentGenerator.validate_content_length(test_content)
    print(f"\n内容长度验证: {'通过' if is_valid else '不通过'}")
    
    formatter = ContentFormatter()
    formatted_text = formatter.format_content_for_display(test_content)
    print("\n格式化后的内容:")
    print(formatted_text) 