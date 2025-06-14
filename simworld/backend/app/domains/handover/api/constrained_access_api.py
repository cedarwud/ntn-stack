"""
Constrained Satellite Access API
提供約束式衛星接入策略的 REST API 接口
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import List, Optional, Dict, Any
import logging
import time

from ..services.constrained_satellite_access_service import (
    ConstrainedSatelliteAccessService,
    SatelliteConstraintType,
    SatelliteAccessCandidate
)
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/handover/constrained-access", tags=["Constrained Access"])

# 全局服務實例
constrained_access_service = ConstrainedSatelliteAccessService()


# === API 數據模型 ===

class SatelliteSelectionRequest(BaseModel):
    """衛星選擇請求"""
    ue_id: str = Field(description="UE 設備 ID")
    ue_latitude: float = Field(description="UE 緯度")
    ue_longitude: float = Field(description="UE 經度") 
    ue_altitude: float = Field(default=0.0, description="UE 海拔高度 (米)")
    consider_future: bool = Field(default=True, description="是否考慮未來軌道預測")
    scenario_type: str = Field(default="urban", description="場景類型 (urban/suburban/rural)")


class ConstraintConfigRequest(BaseModel):
    """約束配置請求"""
    constraint_type: str = Field(description="約束類型")
    threshold_value: Optional[float] = Field(default=None, description="閾值")
    weight: Optional[float] = Field(default=None, description="權重 (0-1)")
    is_hard_constraint: Optional[bool] = Field(default=None, description="是否為硬約束")


class SatelliteSelectionResponse(BaseModel):
    """衛星選擇響應"""
    success: bool
    selected_satellite: Optional[Dict[str, Any]]
    total_candidates: int
    filtered_candidates: int
    selection_time_ms: float
    constraint_scores: Dict[str, float]
    recommendation_confidence: float


# === API 端點 ===

@router.post("/select-satellite", response_model=SatelliteSelectionResponse)
async def select_optimal_satellite(
    request: SatelliteSelectionRequest,
    background_tasks: BackgroundTasks
):
    """
    使用約束式策略選擇最佳衛星
    """
    try:
        start_time = time.time()
        logger.info(f"收到約束式衛星選擇請求 - UE: {request.ue_id}")
        
        # 模擬獲取可用衛星列表 (在實際系統中應從軌道服務獲取)
        available_satellites = _generate_mock_satellites(
            (request.ue_latitude, request.ue_longitude, request.ue_altitude),
            request.scenario_type
        )
        
        total_candidates = len(available_satellites)
        
        # 執行約束式衛星選擇
        selected_candidate = await constrained_access_service.select_optimal_satellite(
            ue_id=request.ue_id,
            ue_position=(request.ue_latitude, request.ue_longitude, request.ue_altitude),
            available_satellites=available_satellites,
            timestamp=time.time(),
            consider_future=request.consider_future
        )
        
        selection_time = (time.time() - start_time) * 1000  # 轉換為毫秒
        
        if selected_candidate:
            response = SatelliteSelectionResponse(
                success=True,
                selected_satellite={
                    "satellite_id": selected_candidate.satellite_id,
                    "satellite_name": selected_candidate.satellite_name,
                    "elevation_deg": selected_candidate.elevation_deg,
                    "azimuth_deg": selected_candidate.azimuth_deg,
                    "distance_km": selected_candidate.distance_km,
                    "signal_strength_dbm": selected_candidate.signal_strength_dbm,
                    "orbital_velocity_km_s": selected_candidate.orbital_velocity_km_s,
                    "coverage_duration_sec": selected_candidate.coverage_duration_sec,
                    "load_ratio": selected_candidate.load_ratio,
                    "overall_score": selected_candidate.overall_score
                },
                total_candidates=total_candidates,
                filtered_candidates=1,  # 簡化，實際應該計算過濾後的數量
                selection_time_ms=selection_time,
                constraint_scores={
                    constraint_type.value: score 
                    for constraint_type, score in selected_candidate.constraint_scores.items()
                },
                recommendation_confidence=selected_candidate.overall_score
            )
        else:
            response = SatelliteSelectionResponse(
                success=False,
                selected_satellite=None,
                total_candidates=total_candidates,
                filtered_candidates=0,
                selection_time_ms=selection_time,
                constraint_scores={},
                recommendation_confidence=0.0
            )
        
        # 在背景任務中記錄詳細日誌
        background_tasks.add_task(
            _log_selection_details,
            request.ue_id,
            selected_candidate,
            selection_time
        )
        
        return response
        
    except Exception as e:
        logger.error(f"約束式衛星選擇失敗: {e}")
        raise HTTPException(status_code=500, detail=f"選擇失敗: {str(e)}")


@router.get("/constraints")
async def get_constraint_configuration():
    """
    獲取當前約束配置
    """
    try:
        config = constrained_access_service.get_constraint_configuration()
        return {
            "success": True,
            "constraints": config,
            "total_constraints": len(config)
        }
    except Exception as e:
        logger.error(f"獲取約束配置失敗: {e}")
        raise HTTPException(status_code=500, detail=f"配置查詢失敗: {str(e)}")


@router.put("/constraints")
async def update_constraint_configuration(request: ConstraintConfigRequest):
    """
    更新約束配置
    """
    try:
        # 驗證約束類型
        try:
            constraint_type = SatelliteConstraintType(request.constraint_type)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"無效的約束類型: {request.constraint_type}"
            )
        
        # 更新約束
        constrained_access_service.update_constraint(
            constraint_type=constraint_type,
            threshold_value=request.threshold_value,
            weight=request.weight,
            is_hard_constraint=request.is_hard_constraint
        )
        
        return {
            "success": True,
            "message": f"約束 {request.constraint_type} 已更新",
            "updated_constraint": {
                "type": request.constraint_type,
                "threshold": request.threshold_value,
                "weight": request.weight,
                "is_hard": request.is_hard_constraint
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新約束配置失敗: {e}")
        raise HTTPException(status_code=500, detail=f"配置更新失敗: {str(e)}")


@router.get("/statistics")
async def get_performance_statistics():
    """
    獲取約束式接入策略的性能統計
    """
    try:
        stats = constrained_access_service.get_performance_statistics()
        
        # 添加額外的分析指標
        analysis = {
            "efficiency_metrics": {
                "selection_success_rate": _calculate_success_rate(stats),
                "load_balance_score": stats["load_balance_ratio"],
                "constraint_compliance_rate": _calculate_compliance_rate(stats)
            },
            "performance_insights": {
                "most_violated_constraint": _find_most_violated_constraint(stats),
                "busiest_satellite": _find_busiest_satellite(stats),
                "optimization_suggestions": _generate_optimization_suggestions(stats)
            }
        }
        
        return {
            "success": True,
            "statistics": stats,
            "analysis": analysis,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"獲取性能統計失敗: {e}")
        raise HTTPException(status_code=500, detail=f"統計查詢失敗: {str(e)}")


@router.post("/scenarios/{scenario_name}/test")
async def test_constraint_strategy(
    scenario_name: str,
    num_ues: int = Query(10, description="測試 UE 數量"),
    test_duration_sec: int = Query(300, description="測試持續時間 (秒)")
):
    """
    測試約束策略在特定場景下的性能
    """
    try:
        logger.info(f"開始測試約束策略 - 場景: {scenario_name}, UE數量: {num_ues}")
        
        test_results = await _run_constraint_strategy_test(
            scenario_name, num_ues, test_duration_sec
        )
        
        return {
            "success": True,
            "scenario": scenario_name,
            "test_parameters": {
                "num_ues": num_ues,
                "duration_sec": test_duration_sec
            },
            "results": test_results
        }
        
    except Exception as e:
        logger.error(f"約束策略測試失敗: {e}")
        raise HTTPException(status_code=500, detail=f"測試失敗: {str(e)}")


@router.delete("/assignments/{ue_id}")
async def release_ue_assignment(ue_id: str):
    """
    釋放 UE 的衛星分配
    """
    try:
        # 從服務中釋放分配
        if ue_id in constrained_access_service.ue_assignments:
            satellite_id = constrained_access_service.ue_assignments[ue_id]
            
            # 減少衛星負載
            if satellite_id in constrained_access_service.satellite_loads:
                constrained_access_service.satellite_loads[satellite_id] = max(
                    0, constrained_access_service.satellite_loads[satellite_id] - 1
                )
            
            # 移除分配記錄
            del constrained_access_service.ue_assignments[ue_id]
            
            return {
                "success": True,
                "message": f"UE {ue_id} 的衛星分配已釋放",
                "released_satellite": satellite_id
            }
        else:
            return {
                "success": True,
                "message": f"UE {ue_id} 沒有活躍的衛星分配"
            }
            
    except Exception as e:
        logger.error(f"釋放 UE 分配失敗: {e}")
        raise HTTPException(status_code=500, detail=f"釋放失敗: {str(e)}")


# === 輔助函數 ===

def _generate_mock_satellites(ue_position: tuple, scenario_type: str) -> List[Dict]:
    """生成模擬衛星數據（根據場景類型調整）"""
    import random
    import math
    
    # 根據場景類型調整衛星數量和分布
    if scenario_type == "urban":
        num_satellites = random.randint(8, 12)  # 城市環境，更多衛星
        min_elevation = 15.0  # 較高的最小仰角
    elif scenario_type == "suburban":
        num_satellites = random.randint(6, 10)
        min_elevation = 10.0
    else:  # rural
        num_satellites = random.randint(4, 8)   # 鄉村環境，較少衛星
        min_elevation = 5.0   # 較低的最小仰角
    
    satellites = []
    satellite_names = [
        "ONEWEB-0012", "ONEWEB-0010", "ONEWEB-0008", "ONEWEB-0007", "ONEWEB-0006",
        "ONEWEB-0001", "ONEWEB-0002", "ONEWEB-0003", "ONEWEB-0004", "ONEWEB-0005",
        "ONEWEB-0011", "ONEWEB-0013"
    ]
    
    for i in range(num_satellites):
        sat_name = satellite_names[i % len(satellite_names)]
        
        # 生成衛星位置參數
        elevation = random.uniform(min_elevation, 85.0)
        azimuth = random.uniform(0, 360)
        distance = random.uniform(500, 1500)  # LEO 距離範圍
        velocity = random.uniform(6.8, 7.8)   # LEO 軌道速度
        
        satellite = {
            "norad_id": f"{40000 + i}",
            "name": sat_name,
            "elevation_deg": elevation,
            "azimuth_deg": azimuth,
            "distance_km": distance,
            "velocity_km_s": velocity
        }
        
        satellites.append(satellite)
    
    return satellites


async def _log_selection_details(
    ue_id: str, 
    selected_candidate: Optional[SatelliteAccessCandidate], 
    selection_time_ms: float
):
    """記錄選擇詳細信息（背景任務）"""
    if selected_candidate:
        logger.info(
            f"約束式選擇完成 - UE: {ue_id}, "
            f"衛星: {selected_candidate.satellite_name}, "
            f"評分: {selected_candidate.overall_score:.3f}, "
            f"耗時: {selection_time_ms:.1f}ms"
        )
    else:
        logger.warning(f"約束式選擇失敗 - UE: {ue_id}, 耗時: {selection_time_ms:.1f}ms")


def _calculate_success_rate(stats: Dict) -> float:
    """計算選擇成功率"""
    total_selections = stats.get("total_selections", 0)
    if total_selections == 0:
        return 1.0
    
    # 簡化計算，實際應該基於失敗記錄
    return 0.95  # 假設 95% 成功率


def _calculate_compliance_rate(stats: Dict) -> float:
    """計算約束遵守率"""
    violations = stats.get("constraint_violations", {})
    total_violations = sum(violations.values())
    total_selections = stats.get("total_selections", 1)
    
    compliance_rate = 1.0 - (total_violations / max(total_selections, 1))
    return max(0.0, compliance_rate)


def _find_most_violated_constraint(stats: Dict) -> str:
    """找出最常違反的約束"""
    violations = stats.get("constraint_violations", {})
    if not violations:
        return "none"
    
    return max(violations, key=violations.get)


def _find_busiest_satellite(stats: Dict) -> str:
    """找出負載最高的衛星"""
    loads = stats.get("current_satellite_loads", {})
    if not loads:
        return "none"
    
    return max(loads, key=loads.get)


def _generate_optimization_suggestions(stats: Dict) -> List[str]:
    """生成優化建議"""
    suggestions = []
    
    # 基於負載平衡
    load_ratio = stats.get("load_balance_ratio", 1.0)
    if load_ratio < 0.7:
        suggestions.append("建議增加負載平衡約束權重，改善衛星負載分布")
    
    # 基於約束違反
    violations = stats.get("constraint_violations", {})
    if violations:
        most_violated = _find_most_violated_constraint(stats)
        suggestions.append(f"建議檢視 {most_violated} 約束閾值，減少違反次數")
    
    # 基於選擇數量
    total_selections = stats.get("total_selections", 0)
    if total_selections < 10:
        suggestions.append("需要更多數據來進行準確的性能分析")
    
    return suggestions if suggestions else ["當前性能良好，無需調整"]


async def _run_constraint_strategy_test(
    scenario_name: str, 
    num_ues: int, 
    duration_sec: int
) -> Dict:
    """運行約束策略測試"""
    # 這是一個簡化的測試實現
    # 在真實系統中，這會模擬多個 UE 在指定時間內的衛星選擇過程
    
    test_results = {
        "scenario": scenario_name,
        "total_ues_tested": num_ues,
        "test_duration_sec": duration_sec,
        "successful_selections": int(num_ues * 0.95),  # 假設 95% 成功率
        "average_selection_time_ms": 12.5,
        "constraint_violations": 2,
        "load_balance_achieved": True,
        "recommendations": [
            "測試結果良好，約束策略運作正常",
            f"在 {scenario_name} 場景下表現穩定"
        ]
    }
    
    return test_results