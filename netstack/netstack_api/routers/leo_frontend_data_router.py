"""
LEO Frontend Data Router - P0.3 輸出格式對接
提供轉換後的前端立體圖數據 API 端點
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import structlog

# Import format converter
import sys
sys.path.append('/app/config')
sys.path.append('/app/src/leo_core')

try:
    from config.output_format_converter import (
        create_leo_to_frontend_converter,
        convert_phase1_to_frontend_format
    )
except ImportError:
    # Fallback for development environment
    sys.path.append('/home/sat/ntn-stack/netstack/config')
    from output_format_converter import (
        create_leo_to_frontend_converter,
        convert_phase1_to_frontend_format
    )

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/leo-frontend", tags=["LEO前端數據"])

class FrontendDataResponse(BaseModel):
    """前端數據響應模型"""
    success: bool
    data_source: str
    constellation: Optional[str]
    satellites_count: int
    timestamp: str
    metadata: Dict[str, Any]
    satellites: List[Dict[str, Any]]

class ConversionStatus(BaseModel):
    """轉換狀態響應模型"""
    available: bool
    last_conversion: Optional[str]
    phase1_report_available: bool
    conversion_error: Optional[str]

@router.get("/status", response_model=ConversionStatus)
async def get_conversion_status():
    """
    獲取 LEO 前端數據轉換狀態
    """
    try:
        # Check if F1→F2→F3→A1 final report exists
        final_report_paths = [
            "/app/data/leo_optimization_final_report.json",
            "/tmp/leo_temporary_outputs/leo_optimization_final_report.json"
        ]
        
        final_report_available = False
        final_report_path = None
        
        for path in final_report_paths:
            if os.path.exists(path):
                final_report_available = True
                final_report_path = path
                break
        
        last_conversion = None
        if final_report_path:
            stat = os.stat(final_report_path)
            last_conversion = datetime.fromtimestamp(stat.st_mtime).isoformat()
        
        return ConversionStatus(
            available=final_report_available,
            last_conversion=last_conversion,
            phase1_report_available=final_report_available,  # 保持兼容性
            conversion_error=None
        )
        
    except Exception as e:
        logger.error("Failed to get conversion status", error=str(e))
        return ConversionStatus(
            available=False,
            last_conversion=None,
            phase1_report_available=False,  # 保持兼容性
            conversion_error=str(e)
        )

@router.get("/data", response_model=FrontendDataResponse)
async def get_frontend_data(
    constellation: Optional[str] = Query(None, description="過濾特定星座 (starlink/oneweb)"),
    force_convert: bool = Query(False, description="強制重新轉換")
):
    """
    獲取前端立體圖數據
    P0.3: 核心端點 - 將 LEO Restructure 數據轉換為前端格式
    """
    try:
        # Find F1→F2→F3→A1 final report
        final_report_paths = [
            "/app/data/leo_optimization_final_report.json",
            "/tmp/leo_temporary_outputs/leo_optimization_final_report.json"
        ]
        
        final_report_path = None
        for path in final_report_paths:
            if os.path.exists(path):
                final_report_path = path
                break
        
        if not final_report_path:
            raise HTTPException(
                status_code=404,
                detail="LEO final report not found. Run F1→F2→F3→A1 LEO processing first."
            )
        
        # Load LEO final report
        with open(final_report_path, 'r', encoding='utf-8') as f:
            leo_final_report = json.load(f)
        
        # Convert to frontend format
        converter = create_leo_to_frontend_converter()
        frontend_data = converter.convert_phase1_report_to_frontend(leo_final_report)  # 使用同樣的轉換函數保持兼容性
        
        # Filter by constellation if specified
        if constellation:
            if constellation not in ['starlink', 'oneweb']:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid constellation. Use 'starlink' or 'oneweb'"
                )
            frontend_data = converter.convert_to_constellation_specific(frontend_data, constellation)
        
        # Validate format
        if not converter.validate_frontend_format(frontend_data):
            raise HTTPException(
                status_code=500,
                detail="Frontend format validation failed"
            )
        
        logger.info("Successfully served frontend data",
                   constellation=constellation,
                   satellites_count=len(frontend_data['satellites']))
        
        return FrontendDataResponse(
            success=True,
            data_source="leo_f1_f2_f3_a1_system",
            constellation=constellation,
            satellites_count=len(frontend_data['satellites']),
            timestamp=datetime.utcnow().isoformat(),
            metadata=frontend_data['metadata'],
            satellites=frontend_data['satellites']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get frontend data", error=str(e), constellation=constellation)
        raise HTTPException(status_code=500, detail=f"Data conversion error: {str(e)}")

@router.get("/constellations/{constellation}", response_model=FrontendDataResponse) 
async def get_constellation_data(constellation: str):
    """
    獲取特定星座的前端數據
    兼容舊版 API 端點
    """
    return await get_frontend_data(constellation=constellation)

@router.post("/convert")
async def convert_leo_to_frontend(
    force_convert: bool = Query(False, description="強制重新轉換"),
    save_files: bool = Query(True, description="保存轉換後的文件")
):
    """
    手動觸發 F1→F2→F3→A1 LEO 系統到前端格式轉換
    """
    try:
        # Find LEO final report
        final_report_paths = [
            "/app/data/leo_optimization_final_report.json",
            "/tmp/leo_temporary_outputs/leo_optimization_final_report.json"
        ]
        
        final_report_path = None
        for path in final_report_paths:
            if os.path.exists(path):
                final_report_path = path
                break
        
        if not final_report_path:
            raise HTTPException(
                status_code=404,
                detail="LEO final report not found"
            )
        
        results = {}
        
        if save_files:
            # Convert and save for both constellations
            output_dir = Path("/app/data")
            output_dir.mkdir(exist_ok=True)
            
            # Mixed constellation data
            mixed_output = output_dir / "leo_frontend_mixed.json"
            success = convert_phase1_to_frontend_format(
                final_report_path,
                str(mixed_output)
            )
            results["mixed_data"] = {
                "success": success,
                "output_path": str(mixed_output) if success else None
            }
            
            # Starlink specific
            starlink_output = output_dir / "leo_frontend_starlink.json"
            success = convert_phase1_to_frontend_format(
                final_report_path,
                str(starlink_output),
                constellation="starlink"
            )
            results["starlink_data"] = {
                "success": success,
                "output_path": str(starlink_output) if success else None
            }
            
            # OneWeb specific
            oneweb_output = output_dir / "leo_frontend_oneweb.json"
            success = convert_phase1_to_frontend_format(
                final_report_path,
                str(oneweb_output),
                constellation="oneweb"
            )
            results["oneweb_data"] = {
                "success": success,
                "output_path": str(oneweb_output) if success else None
            }
        
        logger.info("Manual conversion completed", results=results)
        
        return {
            "success": True,
            "message": "LEO F1→F2→F3→A1 to frontend conversion completed",
            "timestamp": datetime.utcnow().isoformat(),
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to convert LEO to frontend", error=str(e))
        raise HTTPException(status_code=500, detail=f"Conversion error: {str(e)}")

@router.get("/health")
async def frontend_data_health():
    """
    前端數據服務健康檢查
    """
    try:
        # Test converter creation
        converter = create_leo_to_frontend_converter()
        converter_ok = converter is not None
        
        # Check LEO final report data availability
        final_report_paths = [
            "/app/data/leo_optimization_final_report.json",
            "/tmp/leo_temporary_outputs/leo_optimization_final_report.json"
        ]
        
        final_report_available = any(os.path.exists(path) for path in final_report_paths)
        
        # Test conversion functionality
        conversion_ok = False
        if final_report_available and converter_ok:
            try:
                for path in final_report_paths:
                    if os.path.exists(path):
                        with open(path, 'r') as f:
                            test_data = json.load(f)
                        converter.convert_phase1_report_to_frontend(test_data)
                        conversion_ok = True
                        break
            except Exception:
                conversion_ok = False
        
        return {
            "status": "healthy" if all([converter_ok, final_report_available, conversion_ok]) else "degraded",
            "components": {
                "format_converter": "ok" if converter_ok else "error",
                "leo_final_data": "ok" if final_report_available else "missing",
                "conversion_functionality": "ok" if conversion_ok else "error"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Frontend data health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }