from pydantic import BaseModel, Field
from typing import List, Optional, Union
from enum import Enum


class BusinessType(str, Enum):
    """业务类型枚举"""
    WHOLE_RENT = "whole_rent"      # 整租
    CENTRALIZED = "centralized"    # 集中式
    SHARED_RENT = "shared_rent"    # 合租


class ProcessingStatus(str, Enum):
    """处理状态枚举"""
    PENDING = "pending"                    # 等待处理
    PROCESSING = "processing"              # 处理中
    COMPLETED = "completed"                # 处理完成
    FAILED = "failed"                      # 处理失败


class AnalyzeRoomRequest(BaseModel):
    """房间分析请求模型"""
    roomId: str = Field(..., description="房间ID")
    business_type: BusinessType = Field(..., description="业务类型")
    url: Union[str, List[str]] = Field(..., description="图片地址，可以是单个URL或URL数组")


class AnalyzeResult(BaseModel):
    """单个图片分析结果"""
    url: str
    success: bool
    is_room: Optional[bool] = None
    error: Optional[str] = None


class RoomContent(BaseModel):
    """房源内容模型"""
    lighting_comfort: str = Field(..., description="采光与居住舒适度")
    decoration_quality: str = Field(..., description="装修品质与维护状况")
    space_layout: str = Field(..., description="空间感与布局")
    appliances_facilities: str = Field(..., description="电器与设施")


class AnalyzeRoomResponse(BaseModel):
    """房间分析响应模型 - 支持多图片结果"""
    success: bool
    results: Optional[List[AnalyzeResult]] = None  # 每张图片的具体结果
    error: Optional[str] = None


class ProcessingStatusResponse(BaseModel):
    """处理状态查询响应模型"""
    success: bool
    room_id: str
    business_type: str
    processing_status: ProcessingStatus
    content: Optional[dict] = Field(default=None, description="内容字段，已改为房间特征JSON结构")
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    error: Optional[str] = None
class RoomFeature(str, Enum):
    """房间特征枚举（用于参考）"""
    BALCONY = "阳台"
    PRIVATE_BATHROOM = "独卫"
    BAY_WINDOW = "飘窗"
    STUDIO = "开间"
    LOFT = "loft"
    TOILET = "马桶"
    SQUAT_TOILET = "蹲便"
    BUNK_BED = "上下铺"
    FINE_DECORATION = "精装"


class RoomFeatures(BaseModel):
    """房间特征模型（数据库content字段的新结构）"""
    阳台: bool = False
    独卫: bool = False
    飘窗: bool = False
    开间: bool = False
    loft: bool = False
    马桶: bool = False
    蹲便: bool = False
    上下铺: bool = False
    精装: bool = False



 