"""
房源内容格式化工具
"""
import json
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class ContentFormatter:
    """房源内容格式化器"""
    
    @staticmethod
    def format_content_for_storage(content: Dict[str, str]) -> str:
        """格式化内容用于数据库存储"""
        try:
            return json.dumps(content, ensure_ascii=False, separators=(',', ':'))
        except Exception as e:
            logger.error(f"格式化内容失败: {e}")
            return "{}"
    
    @staticmethod
    def parse_content_from_storage(content_str: str) -> Optional[Dict[str, str]]:
        """从数据库存储格式解析内容"""
        if not content_str:
            return None
        
        try:
            return json.loads(content_str)
        except json.JSONDecodeError as e:
            logger.error(f"解析存储内容失败: {e}")
            return None
        except Exception as e:
            logger.error(f"解析内容失败: {e}")
            return None
    
    @staticmethod
    def validate_content(content: Dict[str, str]) -> bool:
        """验证内容格式"""
        required_fields = ["lighting_comfort", "decoration_quality", "space_layout", "appliances_facilities"]
        
        # 检查必需字段
        if not all(field in content for field in required_fields):
            return False
        
        # 检查字段内容
        if not all(content.get(field, "").strip() for field in required_fields):
            return False
        
        return True 