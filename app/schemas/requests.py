from pydantic import BaseModel
from typing import List, Union, Optional, Dict, Any


class AnalyzeRoomRequest(BaseModel):
    """房间分析请求模型"""
    url: Union[str, List[str]]
    include_description: Optional[bool] = True


class RoomDescription(BaseModel):
    """房间描述模型"""
    room_type: str
    basic_info: str
    features: str


class AnalyzeResult(BaseModel):
    """单个图片分析结果模型"""
    url: str
    actual_url: Optional[str] = None
    success: bool
    is_room: Optional[bool] = None
    description: Optional[RoomDescription] = None
    error: Optional[str] = None


class AnalyzeRoomResponse(BaseModel):
    """房间分析响应模型"""
    success: bool
    total: Optional[int] = None
    processing_time: Optional[str] = None
    results: Optional[List[AnalyzeResult]] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    request_id: Optional[str] = None


 