"""
🎭 算法生態系統 API 路由 - 重構後的簡化版本

提供統一的多算法管理和換手決策 API。
重構後導入並使用模組化的組件。
"""

import logging

# 導入重構後的路由器
from .algorithm_ecosystem import router

logger = logging.getLogger(__name__)

# 導出路由器供主應用使用
__all__ = ["router"]

logger.info("算法生態系統路由器已載入（重構版本）")