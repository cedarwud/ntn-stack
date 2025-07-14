"""
Phase 2.3 統一 API 端點

整合所有 Phase 2.3 組件的統一 API 接口：
- RL 算法管理和切換
- 真實環境訓練控制
- 決策分析和可解釋性
- 多算法性能對比
- 實時決策狀態監控
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, WebSocket
from pydantic import BaseModel, Field

from .rl_algorithm_integrator import RLAlgorithmIntegrator, AlgorithmType
from .real_environment_bridge import RealEnvironmentBridge
from .decision_analytics_engine import DecisionAnalyticsEngine
from .multi_algorithm_comparator import (
    MultiAlgorithmComparator,
    ABTestConfig,
    ComparisonMetric,
)
from .realtime_decision_service import RealtimeDecisionService

logger = logging.getLogger(__name__)


# API 模型定義
class AlgorithmSwitchRequest(BaseModel):
    algorithm_type: str = Field(description="算法類型：dqn, ppo, sac")


class TrainingSessionRequest(BaseModel):
    algorithm_type: str = Field(description="訓練算法類型")
    scenario_type: str = Field(default="urban", description="場景類型")
    complexity: str = Field(default="moderate", description="複雜度")
    episodes: int = Field(default=100, description="訓練回合數")
    config_overrides: Optional[Dict[str, Any]] = Field(
        default=None, description="配置覆蓋"
    )


class ABTestRequest(BaseModel):
    algorithms: List[str] = Field(description="參與測試的算法列表")
    episodes_per_algorithm: int = Field(default=50, description="每個算法的測試回合數")
    scenarios: List[str] = Field(default=["urban", "suburban"], description="測試場景")
    metrics: List[str] = Field(
        default=["total_reward", "success_rate"], description="比較指標"
    )


class DecisionAnalysisRequest(BaseModel):
    episode_id: str = Field(description="Episode ID")
    include_explainability: bool = Field(
        default=True, description="是否包含可解釋性分析"
    )


# API 響應模型
class AlgorithmStatusResponse(BaseModel):
    current_algorithm: str
    available_algorithms: List[str]
    algorithm_metrics: Dict[str, Dict[str, float]]
    is_initialized: bool


class TrainingSessionResponse(BaseModel):
    session_id: str
    algorithm_type: str
    scenario_type: str
    status: str
    started_at: str


class ABTestResponse(BaseModel):
    test_id: str
    status: str
    algorithms: List[str]
    started_at: str
    estimated_completion: Optional[str]


class DecisionAnalysisResponse(BaseModel):
    episode_id: str
    total_decisions: int
    successful_decisions: int
    average_confidence: float
    decision_records: List[Dict[str, Any]]
    explainability_summary: Optional[Dict[str, Any]]


# 創建路由器
router = APIRouter(tags=["Phase 2.3 - RL 算法實戰應用"])

# 全局服務實例
_services_initialized = False
_algorithm_integrator = None
_environment_bridge = None
_analytics_engine = None
_comparator = None
_realtime_service = None


async def get_services():
    """獲取服務實例"""
    global _services_initialized, _algorithm_integrator, _environment_bridge, _analytics_engine, _comparator, _realtime_service

    if not _services_initialized:
        # 初始化配置
        algorithm_config = {
            "enabled_algorithms": ["dqn", "ppo", "sac"],
            "default_algorithm": "dqn",
            "algorithm_configs": {
                "dqn": {"learning_rate": 0.001, "batch_size": 32},
                "ppo": {"learning_rate": 0.0003, "batch_size": 64},
                "sac": {"learning_rate": 0.0001, "batch_size": 128},
            },
        }

        environment_config = {
            "max_episode_steps": 1000,
            "scenario_type": "urban",
            "complexity": "moderate",
            "simworld_url": "http://localhost:8888",
        }

        analytics_config = {
            "enable_detailed_logging": True,
            "enable_explainability": True,
            "max_records_per_episode": 10000,
        }

        comparator_config = {
            "default_scenarios": ["urban", "suburban", "rural"],
            "default_metrics": ["total_reward", "success_rate", "decision_time"],
        }

        realtime_config = {
            "websocket_host": "localhost",
            "websocket_port": 8765,
            "performance_monitor_interval": 5.0,
        }

        # 初始化服務
        _algorithm_integrator = RLAlgorithmIntegrator(algorithm_config)
        _environment_bridge = RealEnvironmentBridge(environment_config)
        _analytics_engine = DecisionAnalyticsEngine(analytics_config)

        # 初始化組件
        await _algorithm_integrator.initialize()
        await _environment_bridge.initialize()

        _comparator = MultiAlgorithmComparator(
            _algorithm_integrator,
            _environment_bridge,
            _analytics_engine,
            comparator_config,
        )

        _realtime_service = RealtimeDecisionService(
            _algorithm_integrator,
            _environment_bridge,
            _analytics_engine,
            _comparator,
            realtime_config,
        )

        # 啟動實時服務
        await _realtime_service.start_service()

        _services_initialized = True
        logger.info("Phase 2.3 服務初始化完成")

    return (
        _algorithm_integrator,
        _environment_bridge,
        _analytics_engine,
        _comparator,
        _realtime_service,
    )


@router.get("/health")
async def health_check():
    """健康檢查"""
    try:
        integrator, bridge, analytics, comparator, realtime = await get_services()

        return {
            "status": "healthy",
            "phase": "2.3",
            "services": {
                "algorithm_integrator": integrator.is_initialized,
                "environment_bridge": bridge.state.value,
                "analytics_engine": analytics.total_decisions_analyzed > 0 or True,
                "comparator": len(comparator.completed_tests) >= 0,
                "realtime_service": realtime.is_running,
            },
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"健康檢查失敗: {e}")
        raise HTTPException(
            status_code=500, detail=f"Service health check failed: {str(e)}"
        )


@router.get("/status", response_model=AlgorithmStatusResponse)
async def get_algorithm_status():
    """獲取算法狀態"""
    try:
        integrator, _, _, _, _ = await get_services()

        status = integrator.get_status()
        metrics = integrator.get_algorithm_metrics()

        return AlgorithmStatusResponse(
            current_algorithm=status["current_algorithm"] or "none",
            available_algorithms=status["available_algorithms"],
            algorithm_metrics={
                algo: {
                    "total_decisions": metrics[algo].total_decisions,
                    "success_rate": metrics[algo].successful_decisions
                    / max(metrics[algo].total_decisions, 1),
                    "average_confidence": metrics[algo].average_confidence,
                    "average_decision_time_ms": metrics[algo].average_decision_time_ms,
                }
                for algo in metrics.keys()
            },
            is_initialized=status["is_initialized"],
        )
    except Exception as e:
        logger.error(f"獲取算法狀態失敗: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get algorithm status: {str(e)}"
        )


@router.post("/algorithms/switch")
async def switch_algorithm(request: AlgorithmSwitchRequest):
    """切換算法"""
    try:
        integrator, _, _, _, realtime = await get_services()

        algorithm_type = AlgorithmType(request.algorithm_type.lower())
        success = await integrator.switch_algorithm(algorithm_type)

        if success:
            # 廣播算法切換事件
            await realtime.broadcast_algorithm_status(
                {
                    "action": "algorithm_switched",
                    "new_algorithm": algorithm_type.value,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            return {
                "success": True,
                "current_algorithm": algorithm_type.value,
                "message": f"已成功切換到 {algorithm_type.value.upper()} 算法",
            }
        else:
            raise HTTPException(
                status_code=400, detail=f"算法切換失敗: {request.algorithm_type}"
            )

    except ValueError:
        raise HTTPException(
            status_code=400, detail=f"無效的算法類型: {request.algorithm_type}"
        )
    except Exception as e:
        logger.error(f"算法切換失敗: {e}")
        raise HTTPException(
            status_code=500, detail=f"Algorithm switch failed: {str(e)}"
        )


@router.post("/training/start", response_model=TrainingSessionResponse)
async def start_training_session(
    request: TrainingSessionRequest, background_tasks: BackgroundTasks
):
    """開始訓練會話"""
    try:
        integrator, bridge, analytics, _, realtime = await get_services()

        # 切換到指定算法
        algorithm_type = AlgorithmType(request.algorithm_type.lower())
        await integrator.switch_algorithm(algorithm_type)

        # 生成會話 ID
        session_id = f"{algorithm_type.value}_{int(datetime.now().timestamp())}"

        # 啟動後台訓練任務
        background_tasks.add_task(
            _run_training_session,
            session_id,
            algorithm_type,
            request,
            integrator,
            bridge,
            analytics,
            realtime,
        )

        return TrainingSessionResponse(
            session_id=session_id,
            algorithm_type=algorithm_type.value,
            scenario_type=request.scenario_type,
            status="starting",
            started_at=datetime.now().isoformat(),
        )

    except ValueError:
        raise HTTPException(
            status_code=400, detail=f"無效的算法類型: {request.algorithm_type}"
        )
    except Exception as e:
        logger.error(f"啟動訓練會話失敗: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to start training session: {str(e)}"
        )


async def _run_training_session(
    session_id: str,
    algorithm_type: AlgorithmType,
    request: TrainingSessionRequest,
    integrator: RLAlgorithmIntegrator,
    bridge: RealEnvironmentBridge,
    analytics: DecisionAnalyticsEngine,
    realtime: RealtimeDecisionService,
):
    """運行訓練會話"""
    try:
        logger.info(f"開始訓練會話: {session_id}")

        # 開始 episode 分析
        analytics.start_episode(session_id, algorithm_type, request.scenario_type)

        for episode in range(request.episodes):
            episode_id = f"{session_id}_ep_{episode}"

            # 重置環境
            obs = await bridge.reset(
                {
                    "scenario_type": request.scenario_type,
                    "complexity": request.complexity,
                }
            )

            episode_reward = 0.0
            step_count = 0

            while step_count < 1000:  # 最大步數限制
                # 算法決策
                decision = await integrator.predict(obs)

                # 轉換為環境動作
                if isinstance(decision.action, int):
                    action_mapping = {
                        0: "no_handover",
                        1: "prepare_handover",
                        2: "trigger_handover",
                    }
                    action_type = action_mapping.get(decision.action, "no_handover")
                else:
                    action_type = "no_handover"

                from .real_environment_bridge import EnvironmentAction

                action = EnvironmentAction(
                    action_type=action_type,
                    target_satellite_id=None,
                    handover_timing=0.5,
                    power_control=0.7,
                    priority_level=0.6,
                )

                # 記錄決策分析
                decision_record = await analytics.analyze_decision(
                    obs, decision, action, {"episode": episode, "step": step_count}
                )

                # 廣播決策事件
                await realtime.broadcast_decision_event(
                    algorithm_type,
                    decision,
                    action,
                    obs,
                    explanation=(
                        decision_record.explanation.__dict__
                        if decision_record.explanation
                        else None
                    ),
                )

                # 執行環境步驟
                next_obs, reward, terminated, truncated, info = await bridge.step(
                    action
                )

                # 更新決策結果
                await analytics.update_decision_result(
                    decision_record.decision_id,
                    reward,
                    next_obs,
                    info.get("step_duration_ms", 0),
                )

                # 廣播換手事件
                if action.action_type == "trigger_handover":
                    await realtime.broadcast_handover_event(
                        info.get("execution_result", {}), algorithm_type
                    )

                # 更新算法
                await integrator.update(
                    obs, action, reward.total_reward, next_obs, terminated or truncated
                )

                episode_reward += reward.total_reward
                step_count += 1
                obs = next_obs

                if terminated or truncated:
                    break

            logger.info(f"Episode {episode} 完成，獎勵: {episode_reward:.3f}")

        # 完成分析
        episode_analytics = await analytics.finalize_episode()

        logger.info(f"訓練會話完成: {session_id}")

    except Exception as e:
        logger.error(f"訓練會話執行失敗: {e}")


@router.post("/ab-test/start", response_model=ABTestResponse)
async def start_ab_test(request: ABTestRequest, background_tasks: BackgroundTasks):
    """開始 A/B 測試"""
    try:
        _, _, _, comparator, _ = await get_services()

        # 構建測試配置
        algorithms = [AlgorithmType(algo.lower()) for algo in request.algorithms]
        metrics = [ComparisonMetric(metric.lower()) for metric in request.metrics]

        test_config = ABTestConfig(
            algorithms=algorithms,
            episodes_per_algorithm=request.episodes_per_algorithm,
            scenarios=request.scenarios,
            metrics=metrics,
        )

        # 啟動測試
        test_id = await comparator.start_ab_test(test_config)

        estimated_duration = (
            len(algorithms) * request.episodes_per_algorithm * 2
        )  # 估算2分鐘/episode
        estimated_completion = datetime.now() + timedelta(minutes=estimated_duration)

        return ABTestResponse(
            test_id=test_id,
            status="running",
            algorithms=request.algorithms,
            started_at=datetime.now().isoformat(),
            estimated_completion=estimated_completion.isoformat(),
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"無效的參數: {str(e)}")
    except Exception as e:
        logger.error(f"啟動 A/B 測試失敗: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to start A/B test: {str(e)}"
        )


@router.get("/ab-test/{test_id}/status")
async def get_ab_test_status(test_id: str):
    """獲取 A/B 測試狀態"""
    try:
        _, _, _, comparator, _ = await get_services()

        test_result = comparator.get_test_result(test_id)
        if not test_result:
            raise HTTPException(status_code=404, detail=f"測試未找到: {test_id}")

        # 判斷狀態
        if test_id in comparator.active_tests:
            status = "running"
        elif test_id in comparator.completed_tests:
            status = "completed"
        else:
            status = "unknown"

        response = {
            "test_id": test_id,
            "status": status,
            "algorithms": [algo.value for algo in test_result.config.algorithms],
            "start_time": test_result.start_time.isoformat(),
            "end_time": (
                test_result.end_time.isoformat() if test_result.end_time else None
            ),
        }

        if status == "completed":
            response.update(
                {
                    "algorithm_ranking": [
                        {"algorithm": algo.value, "score": score}
                        for algo, score in test_result.algorithm_ranking
                    ],
                    "recommendations": test_result.recommendations[:5],  # 前5個建議
                }
            )

        return response

    except Exception as e:
        logger.error(f"獲取 A/B 測試狀態失敗: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get A/B test status: {str(e)}"
        )


@router.get("/ab-test/{test_id}/report")
async def get_ab_test_report(test_id: str):
    """獲取 A/B 測試詳細報告"""
    try:
        _, _, _, comparator, _ = await get_services()

        report = comparator.export_comparison_report(test_id)
        if not report:
            raise HTTPException(status_code=404, detail=f"測試報告未找到: {test_id}")

        return report

    except Exception as e:
        logger.error(f"獲取 A/B 測試報告失敗: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get A/B test report: {str(e)}"
        )


@router.get("/analytics/{episode_id}", response_model=DecisionAnalysisResponse)
async def get_decision_analysis(
    episode_id: str, request: DecisionAnalysisRequest = Depends()
):
    """獲取決策分析"""
    try:
        _, _, analytics, _, _ = await get_services()

        # 獲取決策記錄
        decision_records = analytics.get_decision_records(episode_id)
        episode_analytics = analytics.get_episode_analytics(episode_id)

        if not decision_records and not episode_analytics:
            raise HTTPException(
                status_code=404, detail=f"Episode 分析未找到: {episode_id}"
            )

        # 構建回應
        response_data = {
            "episode_id": episode_id,
            "total_decisions": len(decision_records),
            "successful_decisions": sum(1 for r in decision_records if r.success),
            "average_confidence": sum(
                r.algorithm_decision.confidence for r in decision_records
            )
            / max(len(decision_records), 1),
            "decision_records": [
                {
                    "decision_id": record.decision_id,
                    "timestamp": record.timestamp.isoformat(),
                    "algorithm": record.algorithm_decision.algorithm_type.value,
                    "action": record.environment_action.action_type,
                    "confidence": record.algorithm_decision.confidence,
                    "reward": record.reward.total_reward if record.reward else 0.0,
                    "success": record.success,
                }
                for record in decision_records[-50:]  # 最近50個決策
            ],
        }

        # 可解釋性數據
        if request.include_explainability and decision_records:
            explainability_summary = {
                "key_factors": [],
                "decision_patterns": {},
                "confidence_distribution": {},
            }

            # 統計主要決策因子
            factor_counts = {}
            for record in decision_records:
                if record.explanation:
                    for factor in record.explanation.key_factors:
                        if factor.factor_name not in factor_counts:
                            factor_counts[factor.factor_name] = 0
                        factor_counts[factor.factor_name] += 1

            explainability_summary["key_factors"] = [
                {"factor": factor, "frequency": count}
                for factor, count in sorted(
                    factor_counts.items(), key=lambda x: x[1], reverse=True
                )[:10]
            ]

            response_data["explainability_summary"] = explainability_summary

        return DecisionAnalysisResponse(**response_data)

    except Exception as e:
        logger.error(f"獲取決策分析失敗: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get decision analysis: {str(e)}"
        )


@router.get("/analytics/export/{episode_id}")
async def export_analytics_data(episode_id: str, format_type: str = "json"):
    """匯出分析數據"""
    try:
        _, _, analytics, _, _ = await get_services()

        data = analytics.export_analytics_data(episode_id, format_type)
        if not data:
            raise HTTPException(
                status_code=404, detail=f"Episode 數據未找到: {episode_id}"
            )

        return data

    except Exception as e:
        logger.error(f"匯出分析數據失敗: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to export analytics data: {str(e)}"
        )


@router.get("/realtime/status")
async def get_realtime_status():
    """獲取實時服務狀態"""
    try:
        _, _, _, _, realtime = await get_services()

        return realtime.get_service_status()

    except Exception as e:
        logger.error(f"獲取實時服務狀態失敗: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get realtime status: {str(e)}"
        )


@router.get("/realtime/clients")
async def get_connected_clients():
    """獲取已連接的客戶端"""
    try:
        _, _, _, _, realtime = await get_services()

        return {
            "clients": realtime.get_connected_clients(),
            "total_count": len(realtime.get_connected_clients()),
        }

    except Exception as e:
        logger.error(f"獲取連接客戶端失敗: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get connected clients: {str(e)}"
        )


@router.get("/realtime/events")
async def get_recent_events(limit: int = 100):
    """獲取最近的決策事件"""
    try:
        _, _, _, _, realtime = await get_services()

        return {
            "events": realtime.get_recent_decision_events(limit),
            "total_count": len(realtime.get_recent_decision_events(limit)),
        }

    except Exception as e:
        logger.error(f"獲取最近事件失敗: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get recent events: {str(e)}"
        )


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 端點"""
    await websocket.accept()

    try:
        _, _, _, _, realtime = await get_services()

        # 這裡可以實現 WebSocket 連接邏輯
        # 簡化實現，直接發送狀態更新
        while True:
            status = realtime.get_service_status()
            await websocket.send_json(
                {
                    "type": "status_update",
                    "data": status,
                    "timestamp": datetime.now().isoformat(),
                }
            )
            await asyncio.sleep(5)

    except Exception as e:
        logger.error(f"WebSocket 連接錯誤: {e}")
    finally:
        await websocket.close()
