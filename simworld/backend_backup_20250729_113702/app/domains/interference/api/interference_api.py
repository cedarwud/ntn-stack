"""
干擾模擬與 AI-RAN 控制 API

提供干擾模擬和抗干擾決策的 REST API 端點
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse

from ..models.interference_models import (
    InterferenceSimulationRequest,
    InterferenceSimulationResponse,
    AIRANControlRequest,
    AIRANControlResponse,
    JammerType,
    InterferenceEnvironment,
    InterferenceDetectionResult,
    InterferenceMetrics,
    JammerSource,
    InterferencePattern,
)
from ..services.interference_simulation_service import InterferenceSimulationService
from ..services.ai_ran_service import AIRANService
from ..services.ai_ran_service_integrated import (
    AIRANServiceIntegrated,
    get_ai_ran_service_integrated,
)

logger = logging.getLogger(__name__)

# 創建路由器
router = APIRouter(prefix="/interference", tags=["干擾模擬與抗干擾"])

# 服務實例（在實際應用中應通過依賴注入）
interference_service = InterferenceSimulationService()
ai_ran_service = AIRANService()  # 保留原服務作為後備
# 整合服務將通過依賴注入獲取


@router.post("/simulate", response_model=InterferenceSimulationResponse)
async def simulate_interference(
    request: InterferenceSimulationRequest, background_tasks: BackgroundTasks
):
    """
    執行干擾模擬

    使用 Sionna 進行 GPU 加速的多類型干擾源模擬，
    支持寬帶噪聲、掃頻、智能干擾等多種干擾場景。
    """
    try:
        logger.info(f"收到干擾模擬請求: {request.request_id}")

        # 執行干擾模擬
        response = await interference_service.simulate_interference(request)

        # 在背景更新歷史數據
        if response.success:
            background_tasks.add_task(_update_simulation_history, request, response)

        return response

    except Exception as e:
        logger.error(f"干擾模擬API失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"模擬失敗: {str(e)}")


@router.post("/ai-ran/control", response_model=AIRANControlResponse)
async def ai_ran_control(
    request: AIRANControlRequest, background_tasks: BackgroundTasks
):
    """
    AI-RAN 抗干擾控制 (原版)

    基於本地 DQN 的抗干擾決策，保留作為後備系統。
    """
    try:
        logger.info(f"收到 AI-RAN 控制請求 (原版): {request.request_id}")

        # 執行 AI-RAN 決策
        response = await ai_ran_service.make_anti_jamming_decision(request)

        # 在背景訓練 AI 模型
        if response.success and ai_ran_service.ai_available:
            background_tasks.add_task(_train_ai_model, request, response)

        return response

    except Exception as e:
        logger.error(f"AI-RAN 控制API失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"控制失敗: {str(e)}")


@router.post("/ai-ran/control-integrated", response_model=AIRANControlResponse)
async def ai_ran_control_integrated(
    request: AIRANControlRequest, background_tasks: BackgroundTasks
):
    """
    AI-RAN 抗干擾控制 (NetStack 整合版)

    基於 NetStack RL 系統的智能抗干擾決策，支持：
    - 多算法支援 (DQN/PPO/SAC)
    - NetStack PostgreSQL 資料庫整合
    - 統一的會話管理和持久化
    - 毫秒級實時決策響應
    - 自動降級到本地模式
    """
    try:
        logger.info(f"收到 AI-RAN 控制請求 (整合版): {request.request_id}")

        # 獲取整合服務
        integrated_service = await get_ai_ran_service_integrated()

        # 執行 NetStack 整合決策
        response = await integrated_service.make_anti_jamming_decision(request)

        # 記錄使用的系統模式
        system_status = getattr(response, "system_status", {}) or {}
        logger.info(f"決策完成，模式: {system_status.get('decision_mode', 'unknown')}")

        return response

    except Exception as e:
        logger.error(f"AI-RAN 整合控制API失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"整合控制失敗: {str(e)}")


@router.post("/scenario/create")
async def create_jammer_scenario(
    scenario_name: str,
    jammer_configs: List[Dict[str, Any]],
    environment_bounds: Dict[str, float],
    duration_sec: float = 60.0,
):
    """
    創建干擾場景

    快速創建包含多個干擾源的測試場景
    """
    try:
        environment = await interference_service.create_jammer_scenario(
            scenario_name, jammer_configs, environment_bounds, duration_sec
        )

        return {
            "success": True,
            "message": f"干擾場景 '{scenario_name}' 創建成功",
            "environment": environment.dict(),
            "jammer_count": len(environment.jammer_sources),
        }

    except Exception as e:
        logger.error(f"創建干擾場景失敗: {e}")
        raise HTTPException(status_code=500, detail=f"場景創建失敗: {str(e)}")


@router.get("/scenarios/presets")
async def get_preset_scenarios():
    """
    獲取預設干擾場景

    返回常用的干擾測試場景配置
    """
    presets = {
        "urban_broadband_interference": {
            "name": "都市寬帶干擾",
            "description": "模擬都市環境中的寬帶噪聲干擾",
            "jammer_configs": [
                {
                    "type": "broadband_noise",
                    "position": [500, 0, 10],
                    "power_dbm": 30,
                    "frequency_band": {"center_freq_mhz": 2150, "bandwidth_mhz": 50},
                }
            ],
            "environment_bounds": {
                "min_x": -1000,
                "max_x": 1000,
                "min_y": -1000,
                "max_y": 1000,
                "min_z": 0,
                "max_z": 100,
            },
        },
        "military_sweep_jamming": {
            "name": "軍用掃頻干擾",
            "description": "模擬軍事環境中的掃頻干擾攻擊",
            "jammer_configs": [
                {
                    "type": "sweep_jammer",
                    "position": [800, 300, 20],
                    "power_dbm": 40,
                    "frequency_band": {"center_freq_mhz": 2150, "bandwidth_mhz": 100},
                    "sweep_rate_mhz_per_sec": 2000,
                }
            ],
            "environment_bounds": {
                "min_x": -2000,
                "max_x": 2000,
                "min_y": -2000,
                "max_y": 2000,
                "min_z": 0,
                "max_z": 200,
            },
        },
        "smart_adaptive_jamming": {
            "name": "智能自適應干擾",
            "description": "模擬AI驅動的智能干擾攻擊",
            "jammer_configs": [
                {
                    "type": "smart_jammer",
                    "position": [1000, -500, 30],
                    "power_dbm": 35,
                    "frequency_band": {"center_freq_mhz": 2150, "bandwidth_mhz": 20},
                    "learning_enabled": True,
                    "target_protocols": ["5G-NR", "LTE"],
                }
            ],
            "environment_bounds": {
                "min_x": -1500,
                "max_x": 1500,
                "min_y": -1500,
                "max_y": 1500,
                "min_z": 0,
                "max_z": 150,
            },
        },
    }

    return {"success": True, "presets": presets, "count": len(presets)}


@router.get("/jammers/active")
async def get_active_jammers():
    """獲取活躍的干擾源"""
    try:
        active_jammers = await interference_service.get_active_jammers()

        return {
            "success": True,
            "active_jammers": active_jammers,
            "count": len(active_jammers),
        }

    except Exception as e:
        logger.error(f"獲取活躍干擾源失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取失敗: {str(e)}")


@router.post("/jammers/{jammer_id}/activate")
async def activate_jammer(jammer_id: str, jammer_config: Dict[str, Any]):
    """啟用干擾源"""
    try:
        await interference_service.add_active_jammer(jammer_id, jammer_config)

        return {
            "success": True,
            "message": f"干擾源 {jammer_id} 已啟用",
            "jammer_id": jammer_id,
        }

    except Exception as e:
        logger.error(f"啟用干擾源失敗: {e}")
        raise HTTPException(status_code=500, detail=f"啟用失敗: {str(e)}")


@router.delete("/jammers/{jammer_id}")
async def deactivate_jammer(jammer_id: str):
    """停用干擾源"""
    try:
        await interference_service.remove_active_jammer(jammer_id)

        return {
            "success": True,
            "message": f"干擾源 {jammer_id} 已停用",
            "jammer_id": jammer_id,
        }

    except Exception as e:
        logger.error(f"停用干擾源失敗: {e}")
        raise HTTPException(status_code=500, detail=f"停用失敗: {str(e)}")


@router.get("/ai-ran/models")
async def get_ai_ran_models():
    """獲取可用的 AI-RAN 模型"""
    models = {
        "DQN": {
            "name": "Deep Q-Network",
            "description": "基於深度Q網路的頻率選擇算法",
            "suitable_for": ["頻率跳變", "通道選擇"],
            "response_time_ms": 1.0,
        },
        "DDPG": {
            "name": "Deep Deterministic Policy Gradient",
            "description": "基於深度確定性政策梯度的連續控制",
            "suitable_for": ["功率控制", "波束成形"],
            "response_time_ms": 2.0,
        },
        "Heuristic": {
            "name": "啟發式算法",
            "description": "基於規則的快速響應機制",
            "suitable_for": ["緊急響應", "後備決策"],
            "response_time_ms": 0.1,
        },
    }

    return {
        "success": True,
        "available_models": models,
        "current_model": "DQN" if ai_ran_service.ai_available else "Heuristic",
        "ai_available": ai_ran_service.ai_available,
    }


@router.get("/ai-ran/netstack/status")
async def get_netstack_rl_status():
    """
    獲取 NetStack RL 系統狀態

    返回 NetStack RL 系統的連接狀態、可用算法、當前訓練會話等信息
    """
    try:
        integrated_service = await get_ai_ran_service_integrated()

        # 獲取 NetStack 客戶端
        if integrated_service.netstack_client:
            # 檢查連接狀態
            health_ok = await integrated_service.netstack_client.health_check()

            # 獲取可用算法
            algorithms = (
                await integrated_service.netstack_client.get_available_algorithms()
            )

            # 獲取訓練狀態
            training_status = await integrated_service.get_training_status()

            return {
                "success": True,
                "netstack_available": integrated_service.is_netstack_available,
                "connection_healthy": health_ok,
                "available_algorithms": algorithms,
                "preferred_algorithm": integrated_service.preferred_algorithm,
                "current_session": integrated_service.current_training_session,
                "training_status": training_status,
                "last_health_check": (
                    integrated_service.netstack_client.last_health_check.isoformat()
                    if integrated_service.netstack_client.last_health_check
                    else None
                ),
            }
        else:
            return {
                "success": False,
                "error": "NetStack RL 客戶端未初始化",
                "netstack_available": False,
            }

    except Exception as e:
        logger.error(f"獲取 NetStack RL 狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=f"狀態獲取失敗: {str(e)}")


@router.post("/ai-ran/netstack/training/pause")
async def pause_netstack_training():
    """暫停 NetStack RL 訓練"""
    try:
        integrated_service = await get_ai_ran_service_integrated()
        success = await integrated_service.pause_training()

        if success:
            return {
                "success": True,
                "message": "訓練已暫停",
                "session_id": integrated_service.current_training_session,
            }
        else:
            return {
                "success": False,
                "message": "暫停訓練失敗",
                "session_id": integrated_service.current_training_session,
            }

    except Exception as e:
        logger.error(f"暫停訓練失敗: {e}")
        raise HTTPException(status_code=500, detail=f"暫停失敗: {str(e)}")


@router.post("/ai-ran/netstack/training/resume")
async def resume_netstack_training():
    """恢復 NetStack RL 訓練"""
    try:
        integrated_service = await get_ai_ran_service_integrated()
        success = await integrated_service.resume_training()

        if success:
            return {
                "success": True,
                "message": "訓練已恢復",
                "session_id": integrated_service.current_training_session,
            }
        else:
            return {
                "success": False,
                "message": "恢復訓練失敗",
                "session_id": integrated_service.current_training_session,
            }

    except Exception as e:
        logger.error(f"恢復訓練失敗: {e}")
        raise HTTPException(status_code=500, detail=f"恢復失敗: {str(e)}")


@router.post("/ai-ran/netstack/training/stop")
async def stop_netstack_training():
    """停止 NetStack RL 訓練"""
    try:
        integrated_service = await get_ai_ran_service_integrated()
        success = await integrated_service.stop_training()

        if success:
            return {
                "success": True,
                "message": "訓練已停止",
                "previous_session_id": integrated_service.current_training_session,
            }
        else:
            return {
                "success": False,
                "message": "停止訓練失敗",
                "session_id": integrated_service.current_training_session,
            }

    except Exception as e:
        logger.error(f"停止訓練失敗: {e}")
        raise HTTPException(status_code=500, detail=f"停止失敗: {str(e)}")


@router.post("/ai-ran/netstack/training/restart")
async def restart_netstack_training(
    algorithm: str = Query(default="dqn", description="要使用的算法 (dqn/ppo/sac)")
):
    """重新啟動 NetStack RL 訓練會話"""
    try:
        integrated_service = await get_ai_ran_service_integrated()

        # 停止當前會話
        if integrated_service.current_training_session:
            await integrated_service.stop_training()

        # 更新首選算法
        integrated_service.preferred_algorithm = algorithm

        # 啟動新會話
        session_id = await integrated_service._ensure_training_session()

        if session_id:
            return {
                "success": True,
                "message": f"訓練會話已重新啟動，使用算法: {algorithm}",
                "session_id": session_id,
                "algorithm": algorithm,
            }
        else:
            return {
                "success": False,
                "message": "重新啟動訓練會話失敗",
                "algorithm": algorithm,
            }

    except Exception as e:
        logger.error(f"重新啟動訓練失敗: {e}")
        raise HTTPException(status_code=500, detail=f"重新啟動失敗: {str(e)}")


@router.get("/metrics")
async def get_interference_metrics(
    time_window_sec: float = Query(default=3600.0, description="時間窗口（秒）")
):
    """獲取干擾系統指標"""
    try:
        metrics = await interference_service.get_simulation_metrics(time_window_sec)

        return {
            "success": True,
            "metrics": metrics.dict(),
            "service_status": {
                "interference_simulation": interference_service.get_service_status(),
                "ai_ran": getattr(ai_ran_service, "get_service_status", lambda: {})(),
            },
        }

    except Exception as e:
        logger.error(f"獲取指標失敗: {e}")
        raise HTTPException(status_code=500, detail=f"指標獲取失敗: {str(e)}")


@router.post("/quick-test")
async def quick_interference_test():
    """
    快速干擾測試

    運行預設的干擾場景，用於系統功能驗證
    """
    try:
        # 創建簡單的測試場景
        test_environment = InterferenceEnvironment(
            environment_id="quick_test",
            name="快速測試場景",
            area_bounds={
                "min_x": -500,
                "max_x": 500,
                "min_y": -500,
                "max_y": 500,
                "min_z": 0,
                "max_z": 50,
            },
            jammer_sources=[
                JammerSource(
                    jammer_id="test_jammer",
                    jammer_type=JammerType.BROADBAND_NOISE,
                    position=(200, 0, 10),
                    power_dbm=25,
                    frequency_band={"center_freq_mhz": 2150, "bandwidth_mhz": 20},
                    pattern=InterferencePattern.CONTINUOUS,
                )
            ],
            simulation_duration_sec=10.0,
        )

        # 創建測試請求
        test_request = InterferenceSimulationRequest(
            request_id="quick_test_001",
            environment=test_environment,
            victim_positions=[(0, 0, 1.5), (100, 100, 1.5)],
            victim_frequency_mhz=2150,
            victim_bandwidth_mhz=20,
            simulation_time_step_ms=10.0,
        )

        # 執行模擬
        simulation_result = await interference_service.simulate_interference(
            test_request
        )

        # 如果檢測到干擾，測試 AI-RAN 響應
        ai_ran_result = None
        if simulation_result.success and simulation_result.detection_results:
            ai_ran_request = AIRANControlRequest(
                request_id="quick_test_ai_ran",
                scenario_description="快速測試干擾響應",
                current_interference_state=simulation_result.detection_results[
                    :3
                ],  # 取前3個結果
                current_network_performance={"throughput_mbps": 50, "latency_ms": 10},
                available_frequencies_mhz=[2140, 2160, 2180],
                power_constraints_dbm={"max": 30, "min": 10},
                latency_requirements_ms=1.0,
            )

            ai_ran_result = await ai_ran_service.make_anti_jamming_decision(
                ai_ran_request
            )

        return {
            "success": True,
            "message": "快速測試完成",
            "test_results": {
                "interference_simulation": {
                    "success": simulation_result.success,
                    "detections": len(simulation_result.detection_results),
                    "affected_victims": simulation_result.affected_victim_count,
                    "processing_time_ms": simulation_result.processing_time_ms,
                },
                "ai_ran_response": (
                    {
                        "success": ai_ran_result.success if ai_ran_result else False,
                        "decision_type": (
                            ai_ran_result.ai_decision.decision_type.value
                            if ai_ran_result and ai_ran_result.success
                            else None
                        ),
                        "decision_time_ms": (
                            ai_ran_result.decision_time_ms if ai_ran_result else 0
                        ),
                    }
                    if ai_ran_result
                    else None
                ),
            },
        }

    except Exception as e:
        logger.error(f"快速測試失敗: {e}")
        raise HTTPException(status_code=500, detail=f"測試失敗: {str(e)}")


@router.delete("/cache/clear")
async def clear_simulation_cache():
    """清理模擬快取"""
    try:
        await interference_service.clear_simulation_cache()

        return {"success": True, "message": "模擬快取已清理"}

    except Exception as e:
        logger.error(f"清理快取失敗: {e}")
        raise HTTPException(status_code=500, detail=f"清理失敗: {str(e)}")


# ===== 背景任務 =====


async def _update_simulation_history(
    request: InterferenceSimulationRequest, response: InterferenceSimulationResponse
):
    """更新模擬歷史（背景任務）"""
    try:
        # 這裡可以實現數據庫存儲、統計分析等
        logger.info(f"模擬歷史已更新: {response.simulation_id}")
    except Exception as e:
        logger.error(f"更新模擬歷史失敗: {e}")


async def _train_ai_model(request: AIRANControlRequest, response: AIRANControlResponse):
    """訓練AI模型（背景任務）"""
    try:
        # 這裡可以實現增量學習、模型優化等
        logger.info(f"AI模型訓練任務已提交: {response.control_id}")
    except Exception as e:
        logger.error(f"AI模型訓練失敗: {e}")


# 導出路由器
__all__ = ["router"]
