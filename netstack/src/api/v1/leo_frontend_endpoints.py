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

async def get_satellites_for_frontend(
    constellation: Optional[str] = Query(None, description="星座篩選 (starlink/oneweb)"),
    min_elevation: float = Query(5.0, description="最小仰角 (度)"),
    format: str = Query("enhanced", description="輸出格式 (basic/enhanced)")
) -> Dict[str, Any]:
    """
    獲取衛星數據，支援多種篩選和格式選項
    
    Returns:
        Dict: 前端格式的衛星數據，包含位置、可見性等信息
    """
    try:
        # 使用 /app/data 目錄而非 /tmp
        leo_output_dir = "/app/data/dynamic_pool_planning_outputs"
        
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
            "source": "LEO_F1_F2_F3_A1_System",
            "format": format,
            "satellites": filtered_satellites,
            "statistics": statistics
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"數據轉換失敗: {str(e)}")


@router.get("/dynamic-pools/summary")
async def get_dynamic_pool_summary() -> Dict[str, Any]:
    """
    獲取動態衛星池規劃摘要信息
    
    Returns:
        Dict: 動態池規劃的統計摘要
    """
    try:
        # Stage 6 輸出文件路徑
        stage6_output_path = Path("/app/data/dynamic_pool_planning_outputs/enhanced_dynamic_pools_output.json")
        
        # 如果主輸出路徑不存在，嘗試替代文件名
        if not stage6_output_path.exists():
            stage6_output_path = Path("/app/data/dynamic_pool_planning_outputs/enhanced_pools_with_3d.json")
        
        if not stage6_output_path.exists():
            raise HTTPException(
                status_code=404, 
                detail="動態衛星池數據不存在"
            )
        
        # 載入 Stage 6 輸出
        with open(stage6_output_path, 'r', encoding='utf-8') as f:
            stage6_data = json.load(f)
        
        # 提取關鍵統計信息
        summary = {
            "status": "success",
            "timestamp": stage6_data.get('metadata', {}).get('timestamp'),
            "processing_time_seconds": stage6_data.get('metadata', {}).get('processing_time_seconds'),
            "optimization_results": stage6_data.get('optimization_results', {}),
            "dynamic_satellite_pool": stage6_data.get('dynamic_satellite_pool', {}),
            "coverage_targets_met": stage6_data.get('coverage_targets_met', {}),
            "performance_metrics": stage6_data.get('performance_metrics', {}),
            "observer_coordinates": stage6_data.get('metadata', {}).get('observer_coordinates', {}),
            "current_3d_status": {
                "visible_count": stage6_data.get('frontend_3d_data', {}).get('current_visible_count', 0),
                "last_updated": stage6_data.get('frontend_3d_data', {}).get('timestamp'),
                "data_freshness": "real-time" if stage6_data.get('frontend_3d_data') else "unavailable"
            }
        }
        
        return summary
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"獲取動態池摘要失敗: {str(e)}"
        )

async def get_enhanced_satellites_data():
    """
    獲取增強版衛星數據（包含可見性分析和軌道數據）
    
    Returns:
        Dict: 增強版前端格式數據，包含 LEO 系統的詳細分析
    """
    try:
        # 使用 /app/data 目錄而非 /tmp
        leo_output_dir = "/app/data/dynamic_pool_planning_outputs"
        
        # 獲取基本衛星數據
        satellites = converter.convert_leo_to_frontend_format(leo_output_dir)
        
        # 讀取詳細的分析數據
        analysis_data = {}
        
        # 讀取最終報告
        final_report_path = Path(leo_output_dir) / "enhanced_dynamic_pools_output.json"
        if final_report_path.exists():
            with open(final_report_path, 'r') as f:
                analysis_data['final_report'] = json.load(f)
        
        # 讀取事件分析結果
        event_analysis_path = Path("/app/data/signal_analysis_outputs") / "signal_event_analysis_output.json"
        if event_analysis_path.exists():
            with open(event_analysis_path, 'r') as f:
                analysis_data['event_analysis'] = json.load(f)
        
        # 構建增強版響應
        enhanced_data = {
            "success": True,
            "source": "LEO_F1_F2_F3_A1_System_Enhanced",
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

async def get_leo_system_status():
    """
    獲取 LEO 系統狀態
    
    Returns:
        Dict: LEO 系統運行狀態和數據可用性
    """
    try:
        # 使用 /app/data 目錄而非 /tmp
        leo_output_dir = "/app/data/dynamic_pool_planning_outputs"
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
                "enhanced_dynamic_pools_output.json",
            ]
            
            # 檢查其他階段輸出
            stage_outputs = [
                ("/app/data/tle_calculation_outputs", "tle_calculation_output.json"),
                ("/app/data/intelligent_filtering_outputs", "intelligent_filtering_output.json"), 
                ("/app/data/signal_analysis_outputs", "signal_event_analysis_output.json"),
                ("/app/data/timeseries_preprocessing_outputs", "starlink_enhanced.json"),
                ("/app/data/data_integration_outputs", "data_integration_output.json")
            ]
            
            file_count = 0
            latest_time = None
            
            for file_name in expected_files:
                file_path = output_path / file_name
                if file_path.exists():
                    file_stat = file_path.stat()
                    status["data_files"][file_name] = {
                        "exists": True,
                        "size_mb": file_stat.st_size / (1024 * 1024),
                        "modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                    }
                    
                    file_time = datetime.fromtimestamp(file_stat.st_mtime)
                    if latest_time is None or file_time > latest_time:
                        latest_time = file_time
                    
                    file_count += 1
                else:
                    status["data_files"][file_name] = {"exists": False}
            
            # 檢查其他階段檔案
            for stage_dir, stage_file in stage_outputs:
                stage_path = Path(stage_dir) / stage_file
                if stage_path.exists():
                    file_stat = stage_path.stat()
                    status["data_files"][f"{stage_dir.split('/')[-1]}/{stage_file}"] = {
                        "exists": True,
                        "size_mb": file_stat.st_size / (1024 * 1024),
                        "modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                    }
                    file_count += 1
            
            # 設定狀態
            if latest_time:
                status["last_updated"] = latest_time.isoformat()
                
                # 檢查數據新鮮度
                time_diff = datetime.now() - latest_time
                if time_diff.total_seconds() < 3600:  # 1小時內
                    status["system_health"] = "excellent"
                elif time_diff.total_seconds() < 86400:  # 24小時內
                    status["system_health"] = "good"
                else:
                    status["system_health"] = "outdated"
            
            if file_count >= 3:
                status["data_completeness"] = "complete"
            elif file_count >= 1:
                status["data_completeness"] = "partial"
            else:
                status["data_completeness"] = "empty"
        
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"狀態檢查失敗: {str(e)}")

@router.post("/refresh", response_model=Dict[str, Any])
async def refresh_leo_data():
    """
    重新生成前端格式數據
    
    Returns:
        Dict: 數據刷新結果
    """
    try:
        leo_output_dir = "/app/data/leo_outputs"
        
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