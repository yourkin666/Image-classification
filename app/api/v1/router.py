from fastapi import APIRouter
from .endpoints import analyze

api_router = APIRouter()

# 包含所有端点路由
api_router.include_router(analyze.router, tags=["图像分析"]) 