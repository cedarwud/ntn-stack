"""
四場景測試驗證環境 API 路由
提供城市移動、高速公路、偏遠地區、緊急救援場景的測試API
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from ..services.scenario_test_environment import (
    scenario_test_environment,
    TestScenarioType,
    ScenarioEnvironment,
    ScenarioTestResult
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scenario-test", tags=["scenario_test"])

# Request/Response 模型
class ScenarioTestRequest(BaseModel):
    """場景測試請求"""
    scenario_id: str = Field(..., description="場景ID")
    test_duration_override: Optional[float] = Field(None, ge=0.1, le=48.0, description="測試時長覆蓋(小時)")
    handover_algorithm: str = Field("ieee_infocom_2024", description="換手算法")

class BatchScenarioTestRequest(BaseModel):
    """批量場景測試請求"""
    scenario_ids: List[str] = Field(..., min_items=1, description="場景ID列表")
    test_duration_override: Optional[float] = Field(None, ge=0.1, le=48.0, description="測試時長覆蓋(小時)")
    algorithms: List[str] = Field(["ieee_infocom_2024", "traditional"], description="換手算法列表")

class ScenarioComparisonRequest(BaseModel):
    """場景對比請求"""
    scenario_ids: List[str] = Field(..., min_items=2, description="要對比的場景ID列表")
    algorithm: str = Field("ieee_infocom_2024", description="使用的換手算法")

class ScenarioTestResponse(BaseModel):
    """場景測試響應"""
    test_id: str
    scenario_id: str
    message: str
    estimated_completion_time: str
    test_parameters: Dict[str, Any]

class BatchTestResponse(BaseModel):
    """批量測試響應"""
    batch_id: str
    submitted_tests: List[str]
    total_tests: int
    estimated_completion_time: str

class ScenarioResultsResponse(BaseModel):
    """場景結果響應"""
    scenario_id: str
    test_results: List[Dict[str, Any]]
    summary_statistics: Dict[str, Any]
    performance_trends: Dict[str, Any]

class ScenarioComparisonResponse(BaseModel):
    """場景對比響應"""
    comparison_summary: Dict[str, Any]
    scenario_rankings: List[Dict[str, Any]]
    performance_matrix: Dict[str, Dict[str, float]]
    recommendations: List[str]

@router.get("/available-scenarios")
async def get_available_scenarios():
    """
    獲取可用的測試場景列表
    """
    try:
        scenarios = []
        
        for scenario_id, scenario in scenario_test_environment.scenarios.items():
            scenario_info = {
                "scenario_id": scenario_id,
                "scenario_type": scenario.scenario_type.value,
                "description": scenario.terrain_type,
                "duration_hours": scenario.duration_hours,
                "user_density": scenario.user_density,
                "interference_level": scenario.interference_level,
                "building_density": scenario.building_density,
                "mobility_patterns": scenario.mobility_patterns,
                "simulation_area": {
                    "lat_range": [scenario.simulation_area[0], scenario.simulation_area[1]],
                    "lon_range": [scenario.simulation_area[2], scenario.simulation_area[3]]
                },
                "weather_conditions": scenario.weather_conditions
            }
            scenarios.append(scenario_info)
        
        scenario_types_info = {
            "urban_mobility": {
                "name": "城市移動場景",
                "description": "高密度建築物環境，多種移動模式",
                "key_challenges": ["建築物遮蔽", "高用戶密度", "電磁干擾"]
            },
            "highway_mobility": {
                "name": "高速公路場景", 
                "description": "高速線性移動，開闊環境",
                "key_challenges": ["高速移動", "都卜勒效應", "快速換手需求"]
            },
            "rural_coverage": {
                "name": "偏遠地區場景",
                "description": "稀疏衛星覆蓋，地形復雜",
                "key_challenges": ["稀疏覆蓋", "地形阻礙", "長距離通訊"]
            },
            "emergency_response": {
                "name": "緊急救援場景",
                "description": "災害環境，UAV密集作業",
                "key_challenges": ["高干擾環境", "優先級排程", "快速部署需求"]
            }
        }
        
        logger.info(f"獲取可用場景列表, 共 {len(scenarios)} 個場景")
        
        return {
            "scenarios": scenarios,
            "scenario_types": scenario_types_info,
            "total_scenarios": len(scenarios),
            "supported_algorithms": ["ieee_infocom_2024", "traditional", "load_balancing"]
        }
        
    except Exception as e:
        logger.error(f"獲取場景列表失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取場景列表失敗: {str(e)}")

@router.post("/run-test", response_model=ScenarioTestResponse)
async def run_scenario_test(
    request: ScenarioTestRequest,
    background_tasks: BackgroundTasks
):
    """
    運行單個場景測試
    
    支持的場景類型:
    - urban_mobility_taipei: 台北城市移動場景
    - highway_mobility_freeway: 高速公路場景  
    - rural_coverage_mountain: 山區偏遠地區場景
    - emergency_response_disaster: 緊急救援場景
    """
    try:
        # 驗證場景是否存在
        if request.scenario_id not in scenario_test_environment.scenarios:
            raise HTTPException(
                status_code=404, 
                detail=f"場景不存在: {request.scenario_id}"
            )
        
        scenario = scenario_test_environment.scenarios[request.scenario_id]
        
        # 在背景運行測試
        background_tasks.add_task(
            scenario_test_environment.run_scenario_test,
            scenario_id=request.scenario_id,
            test_duration_override=request.test_duration_override,
            handover_algorithm=request.handover_algorithm
        )
        
        # 生成測試ID
        test_id = f"test_{request.scenario_id}_{int(datetime.now().timestamp())}"
        
        # 計算預估完成時間
        test_duration = request.test_duration_override or scenario.duration_hours
        estimated_minutes = max(1, int(test_duration * 2))  # 實際時間的2倍
        completion_time = (datetime.now().replace(microsecond=0) + 
                          datetime.timedelta(minutes=estimated_minutes))
        
        logger.info(f"開始場景測試: {test_id}, 場景: {request.scenario_id}, 算法: {request.handover_algorithm}")
        
        return ScenarioTestResponse(
            test_id=test_id,
            scenario_id=request.scenario_id,
            message=f"場景測試已開始執行: {scenario.scenario_type.value}",
            estimated_completion_time=completion_time.isoformat(),
            test_parameters={
                "scenario_type": scenario.scenario_type.value,
                "test_duration_hours": test_duration,
                "handover_algorithm": request.handover_algorithm,
                "total_ues": len(scenario_test_environment.ue_configurations.get(request.scenario_id, [])),
                "total_satellites": len(scenario_test_environment.satellite_configurations.get(request.scenario_id, []))
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"啟動場景測試失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"啟動場景測試失敗: {str(e)}")

@router.post("/run-batch-tests", response_model=BatchTestResponse)
async def run_batch_scenario_tests(
    request: BatchScenarioTestRequest,
    background_tasks: BackgroundTasks
):
    """
    批量運行多場景測試
    
    支持多場景、多算法的批量測試
    """
    try:
        # 驗證所有場景是否存在
        for scenario_id in request.scenario_ids:
            if scenario_id not in scenario_test_environment.scenarios:
                raise HTTPException(
                    status_code=404,
                    detail=f"場景不存在: {scenario_id}"
                )
        
        batch_id = f"batch_{int(datetime.now().timestamp())}"
        submitted_tests = []
        
        # 為每個場景和算法組合提交測試
        for scenario_id in request.scenario_ids:
            for algorithm in request.algorithms:
                # 在背景運行測試
                background_tasks.add_task(
                    scenario_test_environment.run_scenario_test,
                    scenario_id=scenario_id,
                    test_duration_override=request.test_duration_override,
                    handover_algorithm=algorithm
                )
                
                test_id = f"test_{scenario_id}_{algorithm}_{int(datetime.now().timestamp())}"
                submitted_tests.append(test_id)
        
        total_tests = len(request.scenario_ids) * len(request.algorithms)
        
        # 計算批量測試完成時間
        max_duration = max(
            scenario_test_environment.scenarios[sid].duration_hours 
            for sid in request.scenario_ids
        )
        test_duration = request.test_duration_override or max_duration
        estimated_minutes = max(5, int(test_duration * 3))  # 批量測試需要更長時間
        completion_time = (datetime.now().replace(microsecond=0) + 
                          datetime.timedelta(minutes=estimated_minutes))
        
        logger.info(f"開始批量場景測試: {batch_id}, 總測試數: {total_tests}")
        
        return BatchTestResponse(
            batch_id=batch_id,
            submitted_tests=submitted_tests,
            total_tests=total_tests,
            estimated_completion_time=completion_time.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"啟動批量測試失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"啟動批量測試失敗: {str(e)}")

@router.get("/results/{scenario_id}", response_model=ScenarioResultsResponse)
async def get_scenario_test_results(scenario_id: str):
    """
    獲取指定場景的測試結果
    """
    try:
        # 驗證場景是否存在
        if scenario_id not in scenario_test_environment.scenarios:
            raise HTTPException(status_code=404, detail=f"場景不存在: {scenario_id}")
        
        # 獲取測試結果
        test_results = await scenario_test_environment.get_scenario_test_results(scenario_id)
        
        if not test_results:
            return ScenarioResultsResponse(
                scenario_id=scenario_id,
                test_results=[],
                summary_statistics={
                    "total_tests": 0,
                    "message": "尚無測試結果"
                },
                performance_trends={}
            )
        
        # 計算摘要統計
        total_tests = len(test_results)
        total_handovers = sum(result["total_handovers"] for result in test_results)
        avg_success_rate = sum(result["success_rate"] for result in test_results) / total_tests
        avg_latency = sum(result["average_latency"] for result in test_results) / total_tests
        avg_prediction_accuracy = sum(result["prediction_accuracy"] for result in test_results) / total_tests
        
        summary_stats = {
            "total_tests": total_tests,
            "total_handovers": total_handovers,
            "average_success_rate": round(avg_success_rate, 2),
            "average_latency": round(avg_latency, 2),
            "average_prediction_accuracy": round(avg_prediction_accuracy, 2),
            "latest_test_time": test_results[-1]["test_start_time"] if test_results else None,
            "validation_pass_rate": round(
                sum(result["validation_passed"] / result["validation_total"] 
                    for result in test_results if result["validation_total"] > 0) / 
                max(1, len([r for r in test_results if r["validation_total"] > 0])) * 100, 2
            )
        }
        
        # 計算性能趨勢
        if len(test_results) >= 2:
            recent_results = test_results[-5:]  # 最近5次測試
            early_results = test_results[:5]    # 最早5次測試
            
            recent_avg_success = sum(r["success_rate"] for r in recent_results) / len(recent_results)
            early_avg_success = sum(r["success_rate"] for r in early_results) / len(early_results)
            
            recent_avg_latency = sum(r["average_latency"] for r in recent_results) / len(recent_results)
            early_avg_latency = sum(r["average_latency"] for r in early_results) / len(early_results)
            
            performance_trends = {
                "success_rate_trend": round(recent_avg_success - early_avg_success, 2),
                "latency_trend": round(recent_avg_latency - early_avg_latency, 2),
                "improvement_direction": "improving" if recent_avg_success > early_avg_success and recent_avg_latency < early_avg_latency else "stable"
            }
        else:
            performance_trends = {
                "success_rate_trend": 0.0,
                "latency_trend": 0.0,
                "improvement_direction": "insufficient_data"
            }
        
        logger.info(f"獲取場景測試結果: {scenario_id}, 共 {total_tests} 個測試")
        
        return ScenarioResultsResponse(
            scenario_id=scenario_id,
            test_results=test_results,
            summary_statistics=summary_stats,
            performance_trends=performance_trends
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取測試結果失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取測試結果失敗: {str(e)}")

@router.post("/compare-scenarios", response_model=ScenarioComparisonResponse)
async def compare_scenario_performance(request: ScenarioComparisonRequest):
    """
    比較多個場景的性能表現
    
    提供跨場景的性能對比分析
    """
    try:
        # 驗證所有場景是否存在
        for scenario_id in request.scenario_ids:
            if scenario_id not in scenario_test_environment.scenarios:
                raise HTTPException(
                    status_code=404,
                    detail=f"場景不存在: {scenario_id}"
                )
        
        comparison_data = {}
        scenario_rankings = []
        performance_matrix = {}
        
        # 收集每個場景的性能數據
        for scenario_id in request.scenario_ids:
            test_results = await scenario_test_environment.get_scenario_test_results(scenario_id)
            scenario = scenario_test_environment.scenarios[scenario_id]
            
            if test_results:
                # 計算平均性能指標
                avg_success_rate = sum(r["success_rate"] for r in test_results) / len(test_results)
                avg_latency = sum(r["average_latency"] for r in test_results) / len(test_results)
                avg_prediction_accuracy = sum(r["prediction_accuracy"] for r in test_results) / len(test_results)
                
                # 計算綜合性能分數
                performance_score = (
                    avg_success_rate * 0.4 +           # 成功率權重40%
                    (200 - avg_latency) / 2 * 0.3 +    # 延遲權重30% (越低越好)
                    avg_prediction_accuracy * 0.3       # 預測精度權重30%
                )
                
                comparison_data[scenario_id] = {
                    "scenario_type": scenario.scenario_type.value,
                    "test_count": len(test_results),
                    "avg_success_rate": round(avg_success_rate, 2),
                    "avg_latency": round(avg_latency, 2),
                    "avg_prediction_accuracy": round(avg_prediction_accuracy, 2),
                    "performance_score": round(performance_score, 2),
                    "environment_complexity": {
                        "building_density": scenario.building_density,
                        "interference_level": scenario.interference_level,
                        "user_density": scenario.user_density
                    }
                }
                
                performance_matrix[scenario_id] = {
                    "success_rate": avg_success_rate,
                    "latency": avg_latency,
                    "prediction_accuracy": avg_prediction_accuracy,
                    "performance_score": performance_score
                }
            else:
                comparison_data[scenario_id] = {
                    "scenario_type": scenario.scenario_type.value,
                    "test_count": 0,
                    "message": "無測試數據"
                }
                performance_matrix[scenario_id] = {
                    "success_rate": 0,
                    "latency": 999,
                    "prediction_accuracy": 0,
                    "performance_score": 0
                }
        
        # 性能排名
        ranked_scenarios = sorted(
            [(sid, data) for sid, data in comparison_data.items() if "performance_score" in data],
            key=lambda x: x[1]["performance_score"],
            reverse=True
        )
        
        for i, (scenario_id, data) in enumerate(ranked_scenarios):
            scenario_rankings.append({
                "rank": i + 1,
                "scenario_id": scenario_id,
                "scenario_type": data["scenario_type"],
                "performance_score": data["performance_score"],
                "strengths": _identify_scenario_strengths(data),
                "weaknesses": _identify_scenario_weaknesses(data)
            })
        
        # 生成建議
        recommendations = _generate_comparison_recommendations(comparison_data, ranked_scenarios)
        
        comparison_summary = {
            "comparison_timestamp": datetime.now().isoformat(),
            "algorithm_used": request.algorithm,
            "total_scenarios": len(request.scenario_ids),
            "scenarios_with_data": len([d for d in comparison_data.values() if "performance_score" in d]),
            "best_performing_scenario": ranked_scenarios[0][0] if ranked_scenarios else None,
            "performance_spread": {
                "max_score": ranked_scenarios[0][1]["performance_score"] if ranked_scenarios else 0,
                "min_score": ranked_scenarios[-1][1]["performance_score"] if ranked_scenarios else 0,
                "score_range": ranked_scenarios[0][1]["performance_score"] - ranked_scenarios[-1][1]["performance_score"] if len(ranked_scenarios) > 1 else 0
            }
        }
        
        logger.info(f"完成場景性能比較, 比較場景: {request.scenario_ids}")
        
        return ScenarioComparisonResponse(
            comparison_summary=comparison_summary,
            scenario_rankings=scenario_rankings,
            performance_matrix=performance_matrix,
            recommendations=recommendations
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"場景性能比較失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"場景性能比較失敗: {str(e)}")

@router.get("/summary")
async def get_all_scenarios_summary():
    """
    獲取所有場景的摘要信息
    """
    try:
        summary = await scenario_test_environment.get_scenario_summary()
        
        # 添加詳細的場景描述
        for scenario_info in summary["scenarios"]:
            scenario_id = scenario_info["scenario_id"]
            scenario = scenario_test_environment.scenarios[scenario_id]
            
            scenario_info.update({
                "description": _get_scenario_description(scenario.scenario_type.value),
                "key_features": _get_scenario_key_features(scenario),
                "recommended_use_cases": _get_scenario_use_cases(scenario.scenario_type.value)
            })
        
        # 添加整體建議
        overall_recommendations = _generate_overall_recommendations(summary)
        summary["recommendations"] = overall_recommendations
        
        logger.info(f"獲取場景摘要, 共 {summary['total_scenarios']} 個場景")
        
        return summary
        
    except Exception as e:
        logger.error(f"獲取場景摘要失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取場景摘要失敗: {str(e)}")

@router.get("/health")
async def health_check():
    """
    服務健康檢查
    """
    try:
        scenario_count = len(scenario_test_environment.scenarios)
        total_tests = sum(
            len(results) for results in scenario_test_environment.test_results.values()
        )
        
        return {
            "status": "healthy",
            "service": "ScenarioTestEnvironment",
            "timestamp": datetime.now().isoformat(),
            "statistics": {
                "total_scenarios": scenario_count,
                "total_tests_completed": total_tests,
                "predefined_scenarios": [
                    "urban_mobility_taipei",
                    "highway_mobility_freeway", 
                    "rural_coverage_mountain",
                    "emergency_response_disaster"
                ],
                "service_uptime": "running"
            }
        }
        
    except Exception as e:
        logger.error(f"健康檢查失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"服務健康檢查失敗: {str(e)}")

# 輔助函數
def _identify_scenario_strengths(data: Dict[str, Any]) -> List[str]:
    """識別場景優勢"""
    strengths = []
    
    if data["avg_success_rate"] > 90:
        strengths.append("高成功率")
    if data["avg_latency"] < 60:
        strengths.append("低延遲")
    if data["avg_prediction_accuracy"] > 90:
        strengths.append("高預測精度")
    
    return strengths

def _identify_scenario_weaknesses(data: Dict[str, Any]) -> List[str]:
    """識別場景弱點"""
    weaknesses = []
    
    if data["avg_success_rate"] < 80:
        weaknesses.append("成功率偏低")
    if data["avg_latency"] > 100:
        weaknesses.append("延遲較高")
    if data["avg_prediction_accuracy"] < 80:
        weaknesses.append("預測精度不足")
    
    return weaknesses

def _generate_comparison_recommendations(
    comparison_data: Dict[str, Any], 
    ranked_scenarios: List[Tuple[str, Dict[str, Any]]]
) -> List[str]:
    """生成比較建議"""
    recommendations = []
    
    if not ranked_scenarios:
        return ["需要更多測試數據進行有效比較"]
    
    best_scenario = ranked_scenarios[0]
    worst_scenario = ranked_scenarios[-1] if len(ranked_scenarios) > 1 else None
    
    # 基於最佳場景的建議
    if "urban" in best_scenario[0]:
        recommendations.append("城市移動場景表現最佳，建議優先優化城市部署策略")
    elif "highway" in best_scenario[0]:
        recommendations.append("高速移動場景表現優異，適合車聯網應用")
    elif "rural" in best_scenario[0]:
        recommendations.append("偏遠地區覆蓋效果良好，可擴展到更多偏遠區域")
    elif "emergency" in best_scenario[0]:
        recommendations.append("緊急救援場景性能優秀，建議加強災害應對能力")
    
    # 基於性能差異的建議
    if worst_scenario and best_scenario[1]["performance_score"] - worst_scenario[1]["performance_score"] > 20:
        recommendations.append("不同場景間性能差異顯著，建議針對性優化")
    
    # 基於具體指標的建議
    avg_success_rates = [data["avg_success_rate"] for data in comparison_data.values() if "avg_success_rate" in data]
    if avg_success_rates and min(avg_success_rates) < 85:
        recommendations.append("部分場景成功率較低，建議加強算法適應性")
    
    avg_latencies = [data["avg_latency"] for data in comparison_data.values() if "avg_latency" in data]
    if avg_latencies and max(avg_latencies) > 100:
        recommendations.append("部分場景延遲較高，建議優化換手觸發機制")
    
    return recommendations

def _get_scenario_description(scenario_type: str) -> str:
    """獲取場景描述"""
    descriptions = {
        "urban_mobility": "模擬城市高密度環境下的移動通訊場景，包含建築物遮蔽、電磁干擾等挑戰",
        "highway_mobility": "模擬高速公路環境下的高速移動通訊場景，重點測試快速換手能力",
        "rural_coverage": "模擬偏遠山區的稀疏覆蓋通訊場景，測試低密度衛星網路性能",
        "emergency_response": "模擬災害救援環境下的緊急通訊場景，測試高干擾環境下的通訊可靠性"
    }
    return descriptions.get(scenario_type, "未知場景類型")

def _get_scenario_key_features(scenario: ScenarioEnvironment) -> List[str]:
    """獲取場景關鍵特徵"""
    features = []
    
    if scenario.building_density > 0.5:
        features.append("高建築物密度")
    if scenario.interference_level > 0.5:
        features.append("高干擾環境")
    if scenario.user_density > 500:
        features.append("高用戶密度")
    if "uav" in scenario.mobility_patterns:
        features.append("UAV支援")
    if scenario.weather_conditions.get("precipitation", 0) > 0.5:
        features.append("惡劣天氣")
    
    return features

def _get_scenario_use_cases(scenario_type: str) -> List[str]:
    """獲取場景適用案例"""
    use_cases = {
        "urban_mobility": ["智慧城市", "車聯網", "物聯網部署", "行動寬頻服務"],
        "highway_mobility": ["高速公路通訊", "車聯網", "物流追蹤", "交通管理"],
        "rural_coverage": ["偏遠地區通訊", "農業物聯網", "環境監測", "緊急通訊"],
        "emergency_response": ["災害救援", "應急通訊", "UAV作業", "危機管理"]
    }
    return use_cases.get(scenario_type, ["通用通訊場景"])

def _generate_overall_recommendations(summary: Dict[str, Any]) -> List[str]:
    """生成整體建議"""
    recommendations = []
    
    if summary["overall_statistics"]["total_tests"] == 0:
        recommendations.append("建議開始進行場景測試以獲得性能基準")
    elif summary["overall_statistics"]["overall_success_rate"] < 85:
        recommendations.append("整體成功率偏低，建議優化換手算法")
    
    if summary["overall_statistics"]["average_latency"] > 80:
        recommendations.append("平均延遲較高，建議加強預測算法優化")
    
    tested_scenarios = len([s for s in summary["scenarios"] if s["test_count"] > 0])
    if tested_scenarios < len(summary["scenarios"]):
        recommendations.append(f"建議完成所有 {len(summary['scenarios'])} 個場景的測試以獲得完整評估")
    
    return recommendations