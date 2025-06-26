"""API v1 路由模組"""

from .ue import router as ue_router
from .handover import router as handover_router

# 導出所有路由器
__all__ = ["ue_router", "handover_router"]