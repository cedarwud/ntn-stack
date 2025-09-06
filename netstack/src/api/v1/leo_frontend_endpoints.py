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
            "source": "LEO_F1_F2_F3_A1_System",
            "format": format,
            "satellites": filtered_satellites,
            "statistics": statistics
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"數據轉換失敗: {str(e)}")


@router.get("/satellites")
async def get_satellites_endpoint(
    constellation: Optional[str] = Query(None, description="星座篩選 (starlink/oneweb)"),
    min_elevation: float = Query(5.0, description="最小仰角 (度)"),
    format: str = Query("enhanced", description="輸出格式 (basic/enhanced)")
) -> Dict[str, Any]:
    """獲取衛星數據API端點（支持多階段回退）"""
    return await get_satellites_for_frontend(constellation, min_elevation, format)

@router.get("/satellites/enhanced")
async def get_enhanced_satellites_endpoint() -> Dict[str, Any]:
    """獲取增強版衛星數據API端點（支持多階段回退）"""
    return await get_enhanced_satellites_data()

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
        final_report_path = Path(leo_output_dir) / "enhanced_dynamic_pools_output.json"
        if final_report_path.exists():
            with open(final_report_path, 'r') as f:
                analysis_data['final_report'] = json.load(f)
        
        # 讀取事件分析結果
        event_analysis_path = Path("/app/data/signal_analysis_outputs") / "signal_event_analysis_output.json"
        if event_analysis_path.exists():
            with open(event_analysis_path, 'r') as f:
                analysis_data['event_analysis'] = json.load(f)
        
        # 獲取數據源信息
        best_stage_num, best_stage_info = stage_manager.get_best_available_stage()
        
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
            (3, "~1200 顆信號分析"),
            (4, "~1200 顆時間序列"),
            (5, "~1200 顆數據整合"),
            (6, "260-330 顆最終優化")
        ]
        
        for stage_num, expected_desc in expected_flow:
            stage_info = all_stages.get(stage_num)
            if stage_info:
                actual_count = stage_info.satellite_count
                status_icon = {
                    "success": "✅",
                    "partial": "⚠️", 
                    "failed": "❌",
                    "missing": "❌"
                }.get(stage_info.status.value, "❓")
                
                data_flow.append({
                    "stage": stage_num,
                    "expected": expected_desc,
                    "actual": f"{actual_count} 顆衛星",
                    "status": stage_info.status.value,
                    "status_icon": status_icon,
                    "is_healthy": stage_info.status.value in ["success", "partial"]
                })
        
        # @docs 合規性檢查
        docs_compliance = {
            "stage_2_target": {"expected": "1150-1400", "actual": all_stages[2].satellite_count if 2 in all_stages else 0},
            "stage_6_target": {"expected": "260-330", "actual": all_stages[6].satellite_count if 6 in all_stages else 0},
            "retention_rate": {
                "stage_2": round((all_stages[2].satellite_count / 8791 * 100), 1) if 2 in all_stages and all_stages[2].satellite_count > 0 else 0,
                "expected_stage_2": "12-15%"
            }
        }
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_stages": 6,
                "successful_stages": successful_stages,
                "best_available_stage": best_stage_num,
                "best_available_data": {
                    "stage_name": best_stage_info.stage_name,
                    "satellite_count": best_stage_info.satellite_count,
                    "status": best_stage_info.status.value
                },
                "overall_health": "healthy" if successful_stages >= 3 else "degraded" if successful_stages >= 1 else "critical"
            },
            "stages": stages_status,
            "data_flow_analysis": data_flow,
            "docs_compliance": docs_compliance,
            "recommendations": _generate_stage_recommendations(all_stages)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"階段狀態檢查失敗: {str(e)}")

@router.get("/stage/{stage_number}", response_model=Dict[str, Any])
async def get_stage_data(
    stage_number: int = Path(..., ge=1, le=6, description="階段編號 (1-6)"),
    include_samples: bool = Query(False, description="是否包含衛星樣本數據"),
    sample_count: int = Query(10, description="樣本數量")
) -> Dict[str, Any]:
    """
    獲取特定階段的詳細數據
    
    Args:
        stage_number: 階段編號 (1-6)
        include_samples: 是否包含衛星樣本數據
        sample_count: 樣本數量
        
    Returns:
        Dict: 特定階段的詳細信息和可選的樣本數據
    """
    try:
        from shared_core.stage_data_manager import StageDataManager
        
        # 初始化階段管理器
        stage_manager = StageDataManager()
        
        # 獲取特定階段信息
        stage_info = stage_manager.get_stage_info(stage_number)
        
        response = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "stage_info": {
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
        }
        
        # 如果請求包含樣本數據且階段可用
        if include_samples and stage_info.status.value in ["success", "partial"]:
            try:
                # 載入階段數據
                stage_data = stage_manager.load_stage_data(stage_number)
                
                # 轉換為統一格式並取樣本
                unified_data = stage_manager._convert_to_unified_format(stage_data, stage_number)
                samples = unified_data[:sample_count] if unified_data else []
                
                response["samples"] = {
                    "count": len(samples),
                    "total_available": len(unified_data),
                    "data": samples
                }
                
            except Exception as e:
                response["samples"] = {
                    "error": f"樣本數據載入失敗: {str(e)}"
                }
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"階段 {stage_number} 數據獲取失敗: {str(e)}")

def _generate_stage_recommendations(stages_status: Dict[int, Any]) -> List[Dict[str, str]]:
    """生成階段狀態改進建議"""
    recommendations = []
    
    # 檢查各階段並生成建議
    for stage_num in range(1, 7):
        if stage_num not in stages_status:
            continue
            
        stage_info = stages_status[stage_num]
        status = stage_info.status.value
        sat_count = stage_info.satellite_count
        
        if status == "missing":
            recommendations.append({
                "priority": "high",
                "stage": f"Stage {stage_num}",
                "issue": f"{stage_info.stage_name} 數據缺失",
                "suggestion": f"運行 Stage {stage_num} 處理器生成數據"
            })
        elif status == "failed":
            recommendations.append({
                "priority": "high", 
                "stage": f"Stage {stage_num}",
                "issue": f"{stage_info.stage_name} 處理失敗",
                "suggestion": "檢查錯誤日誌並修復問題"
            })
        elif status == "partial":
            recommendations.append({
                "priority": "medium",
                "stage": f"Stage {stage_num}",
                "issue": f"衛星數量偏低 ({sat_count} 顆)",
                "suggestion": "檢查篩選參數或輸入數據質量"
            })
    
    # 數據流連續性檢查
    successful_stages = [num for num, info in stages_status.items() if info.status.value in ["success", "partial"]]
    if successful_stages:
        max_stage = max(successful_stages)
        if max_stage < 6:
            recommendations.append({
                "priority": "medium",
                "stage": f"Stage {max_stage+1}-6",
                "issue": f"數據流在 Stage {max_stage} 後中斷",
                "suggestion": f"修復 Stage {max_stage+1} 以恢復完整流程"
            })
    
    # @docs 合規性建議
    if 6 in stages_status:
        stage6_count = stages_status[6].satellite_count
        if stage6_count > 0 and (stage6_count < 260 or stage6_count > 330):
            recommendations.append({
                "priority": "medium",
                "stage": "Stage 6",
                "issue": f"最終衛星數量 ({stage6_count}) 不符合 @docs 標準 (260-330)",
                "suggestion": "調整模擬退火算法參數"
            })
    
    return recommendations

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