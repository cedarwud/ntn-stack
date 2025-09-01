"""
LEO Configuration Router - P0.2 配置系統統一
提供 LEO Restructure 配置管理 API 端點
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import structlog

# Import LEO unified configuration system
import sys
sys.path.append('/app/config')
# sys.path.append('/app/src/leo_core')  # 已移除過時的 leo_core 系統

try:
    from config.leo_config import (
        create_default_config,
        create_netstack_compatible_config,
        create_unified_config_manager,
        LEOConfigManager
    )
except ImportError:
    # Fallback for development environment
    sys.path.append('/home/sat/ntn-stack/netstack/config')
    from leo_config import (
        create_default_config,
        create_netstack_compatible_config,
        create_unified_config_manager,
        LEOConfigManager
    )

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/leo-config", tags=["LEO配置系統"])

class ConfigResponse(BaseModel):
    """配置響應模型"""
    config_type: str
    timestamp: str
    config: Dict[str, Any]

class ConfigModeRequest(BaseModel):
    """配置模式請求模型"""
    ultra_fast: bool = False
    fast: bool = False
    production: bool = True

@router.get("/default", response_model=ConfigResponse)
async def get_default_config():
    """
    獲取 LEO Restructure 預設配置
    P0.2: 統一配置系統的核心端點
    """
    try:
        config = create_default_config()
        
        return ConfigResponse(
            config_type="leo_restructure_default",
            timestamp=str(datetime.utcnow().isoformat()),
            config=config
        )
    
    except Exception as e:
        logger.error("Failed to get default LEO config", error=str(e))
        raise HTTPException(status_code=500, detail=f"Configuration error: {str(e)}")

@router.get("/netstack-compatible", response_model=ConfigResponse)
async def get_netstack_compatible_config():
    """
    獲取 NetStack 兼容格式配置
    P0.3: 用於輸出格式對接
    """
    try:
        config = create_netstack_compatible_config()
        
        return ConfigResponse(
            config_type="netstack_compatible",
            timestamp=str(datetime.utcnow().isoformat()),
            config=config
        )
    
    except Exception as e:
        logger.error("Failed to get NetStack compatible config", error=str(e))
        raise HTTPException(status_code=500, detail=f"Configuration error: {str(e)}")

@router.post("/mode", response_model=ConfigResponse)
async def set_config_mode(mode_request: ConfigModeRequest):
    """
    設置配置運行模式
    支援 ultra-fast, fast, production 模式
    """
    try:
        manager = create_unified_config_manager(
            ultra_fast=mode_request.ultra_fast,
            fast=mode_request.fast,
            production=mode_request.production
        )
        
        config = manager.get_leo_restructure_format()
        
        mode_name = "production"
        if mode_request.ultra_fast:
            mode_name = "ultra_fast"
        elif mode_request.fast:
            mode_name = "fast"
        
        logger.info("LEO config mode updated", mode=mode_name)
        
        return ConfigResponse(
            config_type=f"leo_restructure_{mode_name}",
            timestamp=str(datetime.utcnow().isoformat()),
            config=config
        )
    
    except Exception as e:
        logger.error("Failed to set config mode", error=str(e), mode=mode_request)
        raise HTTPException(status_code=500, detail=f"Mode configuration error: {str(e)}")

@router.get("/elevation-thresholds")
async def get_elevation_thresholds():
    """
    獲取分層仰角門檻配置
    基於 docs/satellite_handover_standards.md
    """
    try:
        manager = LEOConfigManager()
        netstack_format = manager.get_legacy_netstack_format()
        
        return {
            "elevation_thresholds": netstack_format["elevation_thresholds"],
            "environmental_factors": manager.config.elevation_thresholds.environmental_factors,
            "description": "分層仰角門檻配置 - 基於 ITU-R 和 3GPP NTN 標準"
        }
    
    except Exception as e:
        logger.error("Failed to get elevation thresholds", error=str(e))
        raise HTTPException(status_code=500, detail=f"Elevation threshold error: {str(e)}")

@router.get("/health")
async def config_health_check():
    """
    配置系統健康檢查
    """
    try:
        # Test both config formats
        leo_config = create_default_config()
        netstack_config = create_netstack_compatible_config()
        
        return {
            "status": "healthy",
            "leo_config_available": bool(leo_config),
            "netstack_compat_available": bool(netstack_config),
            "config_components": {
                "tle_loader": "tle_loader" in leo_config,
                "satellite_filter": "satellite_filter" in leo_config,
                "event_processor": "event_processor" in leo_config,
                "optimizer": "optimizer" in leo_config
            }
        }
    
    except Exception as e:
        logger.error("LEO config health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e)
        }

# Import datetime for timestamps
from datetime import datetime