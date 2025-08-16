"""
LEO 前端整合 API 端點
Phase 1 Week 4: 前端數據格式相容性
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
import json
from pathlib import Path
from datetime import datetime

from .leo_data_converter import LEODataConverter

router = APIRouter(prefix="/api/v1/leo-frontend", tags=["leo-frontend"])

# 全域轉換器實例
converter = LEODataConverter()

@router.get("/satellites", response_model=Dict[str, Any])
async def get_satellites_for_frontend(
    format: str = Query("current", description="數據格式: current|historical|enhanced"),
    constellation: Optional[str] = Query(None, description="星座篩選: starlink|oneweb"),
    min_elevation: float = Query(10.0, description="最小仰角篩選")
) -> Dict[str, Any]:
    """
    獲取前端格式的衛星數據
    
    Returns:
        Dict: 包含衛星列表和統計信息的前端格式數據
    """
    try:
        # 使用最新的 LEO 輸出數據
        leo_output_dir = "/tmp/phase1_outputs"
        
        # 檢查數據是否存在
        output_path = Path(leo_output_dir)
        if not output_path.exists():
            raise HTTPException(
                status_code=404, 
                detail="LEO系統數據不存在，請先運行 LEO 系統生成數據"
            )
        
        # 轉換數據
        satellites = converter.convert_leo_to_frontend_format(leo_output_dir)
        
        # 應用篩選
        filtered_satellites = []
        for sat in satellites:
            # 星座篩選
            if constellation and sat['constellation'].lower() != constellation.lower():
                continue
            
            # 仰角篩選
            if sat['elevation_deg'] < min_elevation:
                continue
            
            filtered_satellites.append(sat)
        
        # 計算統計信息
        statistics = {
            "total_satellites": len(filtered_satellites),
            "starlink_count": len([s for s in filtered_satellites if s['constellation'] == 'STARLINK']),
            "oneweb_count": len([s for s in filtered_satellites if s['constellation'] == 'ONEWEB']),
            "avg_elevation": sum(s['elevation_deg'] for s in filtered_satellites) / len(filtered_satellites) if filtered_satellites else 0,
            "max_elevation": max(s['elevation_deg'] for s in filtered_satellites) if filtered_satellites else 0,
            "min_elevation_filter": min_elevation,
            "constellation_filter": constellation,
            "generated_at": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "source": "LEO_Phase1_System",
            "format": format,
            "satellites": filtered_satellites,
            "statistics": statistics
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"數據轉換失敗: {str(e)}")

@router.get("/satellites/enhanced", response_model=Dict[str, Any])
async def get_enhanced_satellites_data():
    """
    獲取增強版衛星數據（包含可見性分析和軌道數據）
    
    Returns:
        Dict: 增強版前端格式數據，包含 LEO 系統的詳細分析
    """
    try:
        leo_output_dir = "/tmp/phase1_outputs"
        
        # 獲取基本衛星數據
        satellites = converter.convert_leo_to_frontend_format(leo_output_dir)
        
        # 讀取詳細的分析數據
        analysis_data = {}
        
        # 讀取最終報告
        final_report_path = Path(leo_output_dir) / "phase1_final_report.json"
        if final_report_path.exists():
            with open(final_report_path, 'r') as f:
                analysis_data['final_report'] = json.load(f)
        
        # 讀取事件分析結果
        event_analysis_path = Path(leo_output_dir) / "handover_event_analysis_results.json"
        if event_analysis_path.exists():
            with open(event_analysis_path, 'r') as f:
                analysis_data['event_analysis'] = json.load(f)
        
        # 構建增強版響應
        enhanced_data = {
            "success": True,
            "source": "LEO_Phase1_System_Enhanced",
            "satellites": satellites,
            "leo_analysis": analysis_data,
            "statistics": {
                "total_satellites": len(satellites),
                "starlink_count": len([s for s in satellites if s['constellation'] == 'STARLINK']),
                "oneweb_count": len([s for s in satellites if s['constellation'] == 'ONEWEB']),
                "avg_elevation": sum(s['elevation_deg'] for s in satellites) / len(satellites) if satellites else 0,
                "max_elevation": max(s['elevation_deg'] for s in satellites) if satellites else 0,
                "total_visible_time": sum(s.get('leo_visible_time_minutes', 0) for s in satellites),
                "avg_score": sum(s.get('leo_total_score', 0) for s in satellites) / len(satellites) if satellites else 0
            },
            "capabilities": {
                "real_orbit_calculation": True,
                "visibility_analysis": True,
                "handover_events": True,
                "signal_quality": True,
                "dynamic_optimization": True
            }
        }
        
        return enhanced_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"增強數據獲取失敗: {str(e)}")

@router.get("/status", response_model=Dict[str, Any])
async def get_leo_system_status():
    """
    獲取 LEO 系統狀態
    
    Returns:
        Dict: LEO 系統運行狀態和數據可用性
    """
    try:
        leo_output_dir = "/tmp/phase1_outputs"
        output_path = Path(leo_output_dir)
        
        status = {
            "leo_system_available": output_path.exists(),
            "data_files": {},
            "last_updated": None,
            "system_health": "unknown"
        }
        
        if output_path.exists():
            # 檢查各種數據檔案
            expected_files = [
                "phase1_final_report.json",
                "tle_loading_and_orbit_calculation_results.json", 
                "satellite_filtering_and_candidate_selection_results.json",
                "handover_event_analysis_results.json",
                "dynamic_satellite_pool_optimization_results.json"
            ]
            
            for filename in expected_files:
                file_path = output_path / filename
                status["data_files"][filename] = {
                    "exists": file_path.exists(),
                    "size_mb": file_path.stat().st_size / 1024 / 1024 if file_path.exists() else 0,
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat() if file_path.exists() else None
                }
            
            # 獲取最後更新時間
            if status["data_files"]["phase1_final_report.json"]["exists"]:
                status["last_updated"] = status["data_files"]["phase1_final_report.json"]["modified"]
                status["system_health"] = "healthy"
            else:
                status["system_health"] = "incomplete"
        else:
            status["system_health"] = "offline"
        
        return {
            "success": True,
            "status": status,
            "frontend_compatibility": True,
            "recommended_action": "ready" if status["system_health"] == "healthy" else "run_leo_system"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "status": {"system_health": "error"},
            "frontend_compatibility": False,
            "recommended_action": "check_system"
        }

@router.post("/refresh", response_model=Dict[str, Any])
async def refresh_leo_data():
    """
    重新生成前端格式數據
    
    Returns:
        Dict: 數據刷新結果
    """
    try:
        leo_output_dir = "/tmp/phase1_outputs"
        
        # 重新轉換數據
        output_file = converter.save_frontend_format(leo_output_dir)
        
        # 獲取更新後的統計
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        return {
            "success": True,
            "message": "前端數據已刷新",
            "output_file": output_file,
            "statistics": data['statistics'],
            "refreshed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"數據刷新失敗: {str(e)}")

# 包含路由到主應用
def include_leo_frontend_router(app):
    """將 LEO 前端路由添加到主應用"""
    app.include_router(router)
    print("✅ LEO 前端整合 API 端點已註冊")