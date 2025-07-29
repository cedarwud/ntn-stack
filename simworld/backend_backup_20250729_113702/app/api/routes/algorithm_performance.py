"""
算法性能 API 路由
提供實際計算的算法性能數據，替代推算數據
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

from app.domains.interference.services.algorithm_performance_service import AlgorithmPerformanceService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/algorithm-performance", tags=["Algorithm Performance"])

# 服務實例
performance_service = AlgorithmPerformanceService()

@router.get("/four-way-comparison")
async def get_four_way_comparison() -> Dict[str, Any]:
    """
    獲取四種算法的實際性能比較
    替代 FourWayHandoverComparisonDashboard 中的推算數據
    """
    try:
        results = await performance_service.calculate_four_algorithm_comparison()
        
        # 轉換為前端需要的格式
        formatted_results = {
            "traditional_metrics": {
                "method_id": "traditional",
                "latency": results["algorithm_results"]["traditional"]["metrics"].latency,
                "success_rate": results["algorithm_results"]["traditional"]["metrics"].success_rate,
                "packet_loss": results["algorithm_results"]["traditional"]["metrics"].packet_loss,
                "throughput": results["algorithm_results"]["traditional"]["metrics"].throughput,
                "power_consumption": results["algorithm_results"]["traditional"]["calculated_metrics"].power_consumption,
                "prediction_accuracy": results["algorithm_results"]["traditional"]["calculated_metrics"].prediction_accuracy,
                "handover_frequency": results["algorithm_results"]["traditional"]["calculated_metrics"].handover_frequency,
                "signal_quality": results["algorithm_results"]["traditional"]["calculated_metrics"].signal_quality,
                "network_overhead": results["algorithm_results"]["traditional"]["calculated_metrics"].network_overhead,
                "user_satisfaction": results["algorithm_results"]["traditional"]["calculated_metrics"].user_satisfaction
            },
            "ntn_gs_metrics": {
                "method_id": "ntn_gs",
                "latency": results["algorithm_results"]["ntn_gs"]["metrics"].latency,
                "success_rate": results["algorithm_results"]["ntn_gs"]["metrics"].success_rate,
                "packet_loss": results["algorithm_results"]["ntn_gs"]["metrics"].packet_loss,
                "throughput": results["algorithm_results"]["ntn_gs"]["metrics"].throughput,
                "power_consumption": results["algorithm_results"]["ntn_gs"]["calculated_metrics"].power_consumption,
                "prediction_accuracy": results["algorithm_results"]["ntn_gs"]["calculated_metrics"].prediction_accuracy,
                "handover_frequency": results["algorithm_results"]["ntn_gs"]["calculated_metrics"].handover_frequency,
                "signal_quality": results["algorithm_results"]["ntn_gs"]["calculated_metrics"].signal_quality,
                "network_overhead": results["algorithm_results"]["ntn_gs"]["calculated_metrics"].network_overhead,
                "user_satisfaction": results["algorithm_results"]["ntn_gs"]["calculated_metrics"].user_satisfaction
            },
            "ntn_smn_metrics": {
                "method_id": "ntn_smn", 
                "latency": results["algorithm_results"]["ntn_smn"]["metrics"].latency,
                "success_rate": results["algorithm_results"]["ntn_smn"]["metrics"].success_rate,
                "packet_loss": results["algorithm_results"]["ntn_smn"]["metrics"].packet_loss,
                "throughput": results["algorithm_results"]["ntn_smn"]["metrics"].throughput,
                "power_consumption": results["algorithm_results"]["ntn_smn"]["calculated_metrics"].power_consumption,
                "prediction_accuracy": results["algorithm_results"]["ntn_smn"]["calculated_metrics"].prediction_accuracy,
                "handover_frequency": results["algorithm_results"]["ntn_smn"]["calculated_metrics"].handover_frequency,
                "signal_quality": results["algorithm_results"]["ntn_smn"]["calculated_metrics"].signal_quality,
                "network_overhead": results["algorithm_results"]["ntn_smn"]["calculated_metrics"].network_overhead,
                "user_satisfaction": results["algorithm_results"]["ntn_smn"]["calculated_metrics"].user_satisfaction
            },
            "ieee_infocom_2024_metrics": {
                "method_id": "ieee_infocom_2024",
                "latency": results["algorithm_results"]["ieee_infocom_2024"]["metrics"].latency,
                "success_rate": results["algorithm_results"]["ieee_infocom_2024"]["metrics"].success_rate,
                "packet_loss": results["algorithm_results"]["ieee_infocom_2024"]["metrics"].packet_loss,
                "throughput": results["algorithm_results"]["ieee_infocom_2024"]["metrics"].throughput,
                "power_consumption": results["algorithm_results"]["ieee_infocom_2024"]["calculated_metrics"].power_consumption,
                "prediction_accuracy": results["algorithm_results"]["ieee_infocom_2024"]["calculated_metrics"].prediction_accuracy,
                "handover_frequency": results["algorithm_results"]["ieee_infocom_2024"]["calculated_metrics"].handover_frequency,
                "signal_quality": results["algorithm_results"]["ieee_infocom_2024"]["calculated_metrics"].signal_quality,
                "network_overhead": results["algorithm_results"]["ieee_infocom_2024"]["calculated_metrics"].network_overhead,
                "user_satisfaction": results["algorithm_results"]["ieee_infocom_2024"]["calculated_metrics"].user_satisfaction
            },
            "improvement_vs_traditional": {
                "ntn_gs": {
                    "latency": ((results["algorithm_results"]["traditional"]["metrics"].latency - 
                               results["algorithm_results"]["ntn_gs"]["metrics"].latency) / 
                               results["algorithm_results"]["traditional"]["metrics"].latency) * 100,
                    "success_rate": ((results["algorithm_results"]["ntn_gs"]["metrics"].success_rate - 
                                    results["algorithm_results"]["traditional"]["metrics"].success_rate) / 
                                    results["algorithm_results"]["traditional"]["metrics"].success_rate) * 100
                },
                "ntn_smn": {
                    "latency": ((results["algorithm_results"]["traditional"]["metrics"].latency - 
                               results["algorithm_results"]["ntn_smn"]["metrics"].latency) / 
                               results["algorithm_results"]["traditional"]["metrics"].latency) * 100,
                    "success_rate": ((results["algorithm_results"]["ntn_smn"]["metrics"].success_rate - 
                                    results["algorithm_results"]["traditional"]["metrics"].success_rate) / 
                                    results["algorithm_results"]["traditional"]["metrics"].success_rate) * 100
                },
                "ieee_infocom_2024": {
                    "latency": ((results["algorithm_results"]["traditional"]["metrics"].latency - 
                               results["algorithm_results"]["ieee_infocom_2024"]["metrics"].latency) / 
                               results["algorithm_results"]["traditional"]["metrics"].latency) * 100,
                    "success_rate": ((results["algorithm_results"]["ieee_infocom_2024"]["metrics"].success_rate - 
                                    results["algorithm_results"]["traditional"]["metrics"].success_rate) / 
                                    results["algorithm_results"]["traditional"]["metrics"].success_rate) * 100
                }
            },
            "timestamp": results["timestamp"],
            "scenario_id": "actual_algorithm_calculation",
            "test_duration": len(performance_service.simulation_scenarios) * 10,  # 模擬測試時間
            "data_source": "actual_calculation"
        }
        
        return formatted_results
        
    except Exception as e:
        logger.error(f"四種算法比較計算失敗: {e}")
        raise HTTPException(status_code=500, detail=f"算法比較計算失敗: {str(e)}")

@router.get("/infocom-2024-detailed")
async def get_infocom_2024_detailed() -> Dict[str, Any]:
    """
    獲取 IEEE INFOCOM 2024 算法的詳細性能指標
    替代 ChartAnalysisDashboard 中的推算數據
    """
    try:
        detailed_metrics = await performance_service.get_ieee_infocom_2024_detailed_metrics()
        return detailed_metrics
        
    except Exception as e:
        logger.error(f"INFOCOM 2024 詳細指標計算失敗: {e}")
        raise HTTPException(status_code=500, detail=f"詳細指標計算失敗: {str(e)}")

@router.get("/latency-breakdown-comparison")
async def get_latency_breakdown_comparison() -> Dict[str, Any]:
    """
    獲取四種算法的延遲分解比較
    提供給 ChartAnalysisDashboard 的 handoverLatencyData
    """
    try:
        results = await performance_service.calculate_four_algorithm_comparison()
        
        # 提取延遲分解數據
        traditional_breakdown = results["algorithm_results"]["traditional"]["latency_breakdown"]
        ntn_gs_breakdown = results["algorithm_results"]["ntn_gs"]["latency_breakdown"]
        ntn_smn_breakdown = results["algorithm_results"]["ntn_smn"]["latency_breakdown"]
        infocom_breakdown = results["algorithm_results"]["ieee_infocom_2024"]["latency_breakdown"]
        
        return {
            "ntn_standard": [
                round(traditional_breakdown.preparation),
                round(traditional_breakdown.rrc_reconfig),
                round(traditional_breakdown.random_access),
                round(traditional_breakdown.ue_context),
                round(traditional_breakdown.path_switch)
            ],
            "ntn_standard_total": round(traditional_breakdown.total),
            "ntn_gs": [
                round(ntn_gs_breakdown.preparation),
                round(ntn_gs_breakdown.rrc_reconfig),
                round(ntn_gs_breakdown.random_access),
                round(ntn_gs_breakdown.ue_context),
                round(ntn_gs_breakdown.path_switch)
            ],
            "ntn_gs_total": round(ntn_gs_breakdown.total),
            "ntn_smn": [
                round(ntn_smn_breakdown.preparation),
                round(ntn_smn_breakdown.rrc_reconfig),
                round(ntn_smn_breakdown.random_access),
                round(ntn_smn_breakdown.ue_context),
                round(ntn_smn_breakdown.path_switch)
            ],
            "ntn_smn_total": round(ntn_smn_breakdown.total),
            "proposed": [
                round(infocom_breakdown.preparation),
                round(infocom_breakdown.rrc_reconfig),
                round(infocom_breakdown.random_access),
                round(infocom_breakdown.ue_context),
                round(infocom_breakdown.path_switch)
            ],
            "proposed_total": round(infocom_breakdown.total),
            "data_source": "actual_calculation",
            "timestamp": results["timestamp"]
        }
        
    except Exception as e:
        logger.error(f"延遲分解比較計算失敗: {e}")
        raise HTTPException(status_code=500, detail=f"延遲分解計算失敗: {str(e)}")

@router.get("/test-scenarios")
async def get_test_scenarios() -> Dict[str, Any]:
    """獲取測試情境資訊"""
    return {
        "scenario_count": len(performance_service.simulation_scenarios),
        "scenarios": performance_service.simulation_scenarios[:3],  # 只返回前3個作為示例
        "description": "基於不同網路條件、UE 位置和衛星配置的測試情境"
    }