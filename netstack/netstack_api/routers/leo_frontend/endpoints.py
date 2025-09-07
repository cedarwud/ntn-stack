"""
LEO 前端整合 API 端點
Phase 1 Week 4: 前端數據格式相容性
Phase 2: 多階段數據管理與回退機制
整合到 netstack_api 路由器結構中
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
import json
from pathlib import Path
from datetime import datetime
import sys

# 添加路徑以導入共享核心模組
sys.path.insert(0, '/app/src')

from ...src.api.v1.leo_data_converter import LEODataConverter

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
        # 🚀 使用新的多階段數據管理器
        from shared_core.stage_data_manager import StageDataManager
        
        # 初始化數據管理器
        stage_manager = StageDataManager()
        
        # 獲取統一格式的衛星數據
        satellites = stage_manager.get_unified_satellite_data()
        
        if not satellites:
            # 獲取階段狀態信息提供更詳細的錯誤
            stage_num, stage_info = stage_manager.get_best_available_stage()
            raise HTTPException(
                status_code=404, 
                detail=f"沒有可用的衛星數據。最佳階段 Stage {stage_num} 狀態: {stage_info.status.value}"
            )
        
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
        
        # 獲取數據源信息
        best_stage_num, best_stage_info = stage_manager.get_best_available_stage()
        
        # 計算統計信息
        statistics = {
            "total_satellites": len(filtered_satellites),
            "starlink_count": len([s for s in filtered_satellites if s['constellation'] == 'STARLINK']),
            "oneweb_count": len([s for s in filtered_satellites if s['constellation'] == 'ONEWEB']),
            "avg_elevation": sum(s['elevation_deg'] for s in filtered_satellites) / len(filtered_satellites) if filtered_satellites else 0,
            "max_elevation": max(s['elevation_deg'] for s in filtered_satellites) if filtered_satellites else 0,
            "min_elevation_filter": min_elevation,
            "constellation_filter": constellation,
            "data_source_stage": best_stage_num,
            "data_source_name": best_stage_info.stage_name,
            "data_source_status": best_stage_info.status.value,
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
        # 🚀 使用新的多階段數據管理器
        from shared_core.stage_data_manager import StageDataManager
        
        # 初始化數據管理器
        stage_manager = StageDataManager()
        
        # 獲取統一格式的衛星數據
        satellites = stage_manager.get_unified_satellite_data()
        
        if not satellites:
            stage_num, stage_info = stage_manager.get_best_available_stage()
            raise HTTPException(
                status_code=404, 
                detail=f"沒有可用的衛星數據。最佳階段 Stage {stage_num} 狀態: {stage_info.status.value}"
            )
        
        # 讀取詳細的分析數據
        analysis_data = {}
        
        # 讀取最終報告
        final_report_path = Path(leo_output_dir) / "leo_optimization_final_report.json"
        if final_report_path.exists():
            with open(final_report_path, 'r') as f:
                analysis_data['final_report'] = json.load(f)
        
        # 讀取事件分析結果
        event_analysis_path = Path(leo_output_dir) / "handover_event_analysis_results.json"
        if event_analysis_path.exists():
            with open(event_analysis_path, 'r') as f:
                analysis_data['event_analysis'] = json.load(f)
        
        # 獲取數據源信息
        best_stage_num, best_stage_info = stage_manager.get_best_available_stage()
        
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
                "avg_score": sum(s.get('leo_total_score', 0) for s in satellites) / len(satellites) if satellites else 0,
                "data_source_stage": best_stage_num,
                "data_source_name": best_stage_info.stage_name,
                "data_source_status": best_stage_info.status.value
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

@router.get("/stages-status", response_model=Dict[str, Any])
async def get_stages_status() -> Dict[str, Any]:
    """
    獲取六階段處理狀態詳情
    
    Returns:
        Dict: 包含所有階段狀態信息的詳細報告
    """
    try:
        from shared_core.stage_data_manager import StageDataManager
        
        # 初始化階段管理器
        stage_manager = StageDataManager()
        
        # 獲取所有階段狀態
        all_stages = stage_manager.get_all_stages_status()
        
        # 轉換為API響應格式
        stages_status = {}
        total_satellites = 0
        successful_stages = 0
        
        for stage_num, stage_info in all_stages.items():
            stages_status[f"stage_{stage_num}"] = {
                "stage_number": stage_info.stage_number,
                "stage_name": stage_info.stage_name,
                "status": stage_info.status.value,
                "satellite_count": stage_info.satellite_count,
                "file_size_mb": round(stage_info.file_size_mb, 2),
                "file_path": stage_info.file_path,
                "processing_time": stage_info.processing_time.isoformat() if stage_info.processing_time else None,
                "data_quality": stage_info.data_quality,
                "error_message": stage_info.error_message
            }
            
            if stage_info.status.value in ["success", "partial"]:
                successful_stages += 1
                if stage_info.satellite_count > total_satellites:
                    total_satellites = stage_info.satellite_count
        
        # 獲取最佳可用階段
        best_stage_num, best_stage_info = stage_manager.get_best_available_stage()
        
        # 數據流分析
        data_flow = []
        expected_flow = [
            (1, "8791 顆衛星載入"),
            (2, "~1200 顆高質量篩選"),
            (3, "~800 顆信號分析"),
            (4, "~600 顆時序預處理"),
            (5, "~400 顆整合準備"),
            (6, "260-330 顆最終優化")
        ]
        
        for stage_num, expected_desc in expected_flow:
            stage_info = all_stages.get(stage_num)
            if stage_info:
                data_flow.append({
                    "stage": stage_num,
                    "expected": expected_desc,
                    "actual": f"{stage_info.satellite_count} 顆衛星",
                    "status": stage_info.status.value,
                    "health": "healthy" if stage_info.status.value == "success" else "needs_attention"
                })
        
        # @docs 合規性檢查
        stage_6_info = all_stages.get(6)
        docs_compliance = {
            "stage_6_target_met": False,
            "final_satellite_count": stage_6_info.satellite_count if stage_6_info else 0,
            "target_range": "260-330 顆衛星",
            "compliance_status": "unknown"
        }
        
        if stage_6_info and 260 <= stage_6_info.satellite_count <= 330:
            docs_compliance.update({
                "stage_6_target_met": True,
                "compliance_status": "compliant"
            })
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "pipeline_health": {
                "total_stages": len(all_stages),
                "successful_stages": successful_stages,
                "overall_status": "healthy" if successful_stages >= 3 else "degraded",
                "best_available_stage": best_stage_num
            },
            "stages_detail": stages_status,
            "data_flow_analysis": data_flow,
            "docs_compliance": docs_compliance,
            "recommendations": _generate_recommendations(all_stages, best_stage_num)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"階段狀態檢查失敗: {str(e)}")

@router.get("/stage/{stage_number}", response_model=Dict[str, Any])
async def get_single_stage_status(stage_number: int) -> Dict[str, Any]:
    """
    獲取單一階段的詳細狀態
    
    Args:
        stage_number: 階段編號 (1-6)
        
    Returns:
        Dict: 單一階段的詳細狀態信息
    """
    if stage_number < 1 or stage_number > 6:
        raise HTTPException(status_code=400, detail="階段編號必須在 1-6 之間")
    
    try:
        from shared_core.stage_data_manager import StageDataManager
        
        stage_manager = StageDataManager()
        stage_info = stage_manager.get_stage_info(stage_number)
        
        # 構建詳細響應
        return {
            "success": True,
            "stage_number": stage_info.stage_number,
            "stage_name": stage_info.stage_name,
            "status": stage_info.status.value,
            "satellite_count": stage_info.satellite_count,
            "file_path": stage_info.file_path,
            "file_size_mb": round(stage_info.file_size_mb, 2),
            "processing_time": stage_info.processing_time.isoformat() if stage_info.processing_time else None,
            "data_quality": stage_info.data_quality,
            "error_message": stage_info.error_message,
            "stage_analysis": _analyze_single_stage(stage_info),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"階段狀態檢查失敗: {str(e)}")

def _generate_recommendations(all_stages: Dict, best_stage_num: int) -> List[str]:
    """生成階段修復建議"""
    recommendations = []
    
    if best_stage_num < 6:
        recommendations.append(f"目前使用 Stage {best_stage_num} 數據，建議修復後續階段以獲得更好效果")
    
    # 檢查各階段問題
    for stage_num in range(1, 7):
        stage_info = all_stages.get(stage_num)
        if stage_info and stage_info.status.value == "failed":
            recommendations.append(f"Stage {stage_num} 處理失敗，請檢查: {stage_info.error_message}")
        elif stage_info and stage_info.status.value == "missing":
            recommendations.append(f"Stage {stage_num} 數據缺失，請重新運行該階段")
    
    if not recommendations:
        recommendations.append("所有階段運行正常，系統狀態良好")
    
    return recommendations

def _analyze_single_stage(stage_info) -> Dict[str, Any]:
    """分析單一階段的詳細信息"""
    analysis = {
        "health_score": 0,
        "performance_metrics": {},
        "data_completeness": stage_info.data_quality.get("data_completeness", 0.0),
        "issues": [],
        "suggestions": []
    }
    
    # 健康評分
    if stage_info.status.value == "success":
        analysis["health_score"] = 100
    elif stage_info.status.value == "partial":
        analysis["health_score"] = 70
    elif stage_info.status.value == "failed":
        analysis["health_score"] = 0
    else:
        analysis["health_score"] = 0
    
    # 性能指標
    analysis["performance_metrics"] = {
        "satellite_density": stage_info.satellite_count / 100,  # 每100顆衛星的密度
        "file_efficiency": stage_info.file_size_mb / max(stage_info.satellite_count, 1),  # MB per satellite
        "has_position_data": stage_info.data_quality.get("has_position_data", False),
        "has_elevation_data": stage_info.data_quality.get("has_elevation_data", False)
    }
    
    return analysis

async def get_leo_system_status():
    """
    獲取 LEO 系統狀態
    
    Returns:
        Dict: LEO 系統運行狀態和數據可用性
    """
    try:
        leo_output_dir = "/app/data"
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
                "leo_optimization_final_report.json",
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
            if status["data_files"]["leo_optimization_final_report.json"]["exists"]:
                status["last_updated"] = status["data_files"]["leo_optimization_final_report.json"]["modified"]
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
        leo_output_dir = "/app/data"
        
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

# 為了保持向後兼容，也導出 include_leo_frontend_router 函數
def include_leo_frontend_router(app):
    """將 LEO 前端路由添加到主應用"""
    app.include_router(router)
    print("✅ LEO 前端整合 API 端點已註冊")