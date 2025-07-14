"""
Phase 2.3 RL 算法實戰應用 API 端點

提供完整的 RL 算法實戰應用功能，包括：
- 多算法並行訓練管理
- 實時決策推送和監控
- A/B 測試和性能對比
- 統計分析和實驗管理
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
import json

from ..core.algorithm_integrator import RLAlgorithmIntegrator
from ..core.decision_analytics_engine import DecisionAnalyticsEngine
from ..core.real_time_decision_service import RealTimeDecisionService
from ..core.training_orchestrator import TrainingOrchestrator
from ..core.performance_analyzer import PerformanceAnalyzer
from ..implementations.simplified_postgresql_repository import SimplifiedPostgreSQLRepository
from ..scenarios.handover_scenario_generator import RealTimeHandoverScenarioGenerator
from ...simworld_tle_bridge_service import SimWorldTLEBridgeService
from ..environments.leo_satellite_environment import LEOSatelliteEnvironment

logger = logging.getLogger(__name__)

# 創建路由器
router = APIRouter(tags=["Phase 2.3 - RL 算法實戰應用"])

# 全局服務實例
_services_initialized = False
_algorithm_integrator = None
_decision_analytics = None
_real_time_service = None
_training_orchestrator = None
_performance_analyzer = None
_scenario_generator = None
_repository = None

# WebSocket 連接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket 連接建立，目前連接數: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket 連接斷開，目前連接數: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"發送個人消息失敗: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"廣播消息失敗: {e}")
                disconnected.append(connection)
        
        # 清理斷開的連接
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

# API 模型定義
class MultiAlgorithmTrainingRequest(BaseModel):
    algorithms: List[str] = Field(description="要並行訓練的算法列表")
    experiment_name: str = Field(description="實驗名稱")
    total_episodes: int = Field(default=100, description="每個算法的訓練回合數")
    scenario_type: str = Field(default="urban", description="場景類型")
    researcher_id: str = Field(default="system", description="研究員 ID")
    research_notes: Optional[str] = Field(default=None, description="研究筆記")
    enable_realtime_streaming: bool = Field(default=True, description="啟用實時串流")

class ABTestRequest(BaseModel):
    algorithm_a: str = Field(description="算法 A")
    algorithm_b: str = Field(description="算法 B")
    test_scenarios: List[str] = Field(description="測試場景列表")
    episodes_per_algorithm: int = Field(default=50, description="每個算法的測試回合數")
    significance_level: float = Field(default=0.05, description="統計顯著性水平")

class PerformanceComparisonRequest(BaseModel):
    session_ids: List[int] = Field(description="要比較的會話 ID 列表")
    metrics: List[str] = Field(description="比較的指標列表")
    statistical_tests: bool = Field(default=True, description="是否進行統計檢驗")

class RealTimeDecisionRequest(BaseModel):
    algorithm: str = Field(description="使用的算法")
    current_state: Dict[str, Any] = Field(description="當前狀態")
    scenario_context: Optional[Dict[str, Any]] = Field(default=None, description="場景上下文")

# 響應模型
class MultiAlgorithmTrainingResponse(BaseModel):
    experiment_id: str
    session_ids: List[int]
    algorithms: List[str]
    status: str
    estimated_completion_time: datetime
    realtime_stream_url: Optional[str]

class ABTestResponse(BaseModel):
    test_id: str
    algorithm_a_session_id: int
    algorithm_b_session_id: int
    test_scenarios: List[str]
    status: str
    preliminary_results: Optional[Dict[str, Any]]

class PerformanceComparisonResponse(BaseModel):
    comparison_id: str
    algorithms: List[str]
    metrics_summary: Dict[str, Any]
    statistical_results: Optional[Dict[str, Any]]
    recommendations: List[str]

class RealTimeDecisionResponse(BaseModel):
    decision: Dict[str, Any]
    confidence: float
    explanation: Dict[str, Any]
    execution_time_ms: float
    timestamp: datetime

async def get_services():
    """獲取服務實例"""
    global _services_initialized, _algorithm_integrator, _decision_analytics, _real_time_service
    global _training_orchestrator, _performance_analyzer, _scenario_generator, _repository

    if not _services_initialized:
        # 初始化基礎服務
        tle_bridge = SimWorldTLEBridgeService()
        leo_env = LEOSatelliteEnvironment({
            "simworld_url": "http://localhost:8888",
            "max_satellites": 6,
            "scenario": "urban",
            "fallback_enabled": True,
        })

        # 初始化 Phase 2.3 服務
        _repository = SimplifiedPostgreSQLRepository()
        _algorithm_integrator = RLAlgorithmIntegrator()
        _decision_analytics = DecisionAnalyticsEngine()
        _real_time_service = RealTimeDecisionService()
        _training_orchestrator = TrainingOrchestrator()
        _performance_analyzer = PerformanceAnalyzer()
        _scenario_generator = RealTimeHandoverScenarioGenerator(
            tle_bridge_service=tle_bridge, leo_environment=leo_env
        )

        _services_initialized = True
        logger.info("Phase 2.3 服務初始化完成")

    return {
        "repository": _repository,
        "integrator": _algorithm_integrator,
        "analytics": _decision_analytics,
        "realtime": _real_time_service,
        "orchestrator": _training_orchestrator,
        "analyzer": _performance_analyzer,
        "scenario_generator": _scenario_generator
    }

@router.post("/training/multi-algorithm", response_model=MultiAlgorithmTrainingResponse)
async def start_multi_algorithm_training(
    request: MultiAlgorithmTrainingRequest,
    background_tasks: BackgroundTasks
):
    """
    啟動多算法並行訓練
    
    支持同時訓練多個 RL 算法，並提供實時性能比較
    """
    try:
        services = await get_services()
        
        # 驗證算法列表
        available_algorithms = ["dqn", "ppo", "sac"]
        invalid_algorithms = [alg for alg in request.algorithms if alg not in available_algorithms]
        if invalid_algorithms:
            raise HTTPException(
                status_code=400, 
                detail=f"不支援的算法: {invalid_algorithms}。可用算法: {available_algorithms}"
            )

        # 創建實驗 ID
        experiment_id = f"multi_alg_{int(datetime.now().timestamp())}"
        
        # 為每個算法創建訓練會話
        session_ids = []
        for algorithm in request.algorithms:
            session_id = await services["orchestrator"].create_training_session(
                algorithm=algorithm,
                experiment_name=f"{request.experiment_name}_{algorithm}",
                total_episodes=request.total_episodes,
                scenario_type=request.scenario_type,
                researcher_id=request.researcher_id,
                research_notes=request.research_notes
            )
            session_ids.append(session_id)

        # 啟動並行訓練
        background_tasks.add_task(
            _run_parallel_training,
            experiment_id,
            session_ids,
            request.algorithms,
            request.enable_realtime_streaming
        )

        # 計算預估完成時間
        estimated_time = datetime.now() + timedelta(
            seconds=request.total_episodes * len(request.algorithms) * 2  # 每回合約2秒
        )

        realtime_url = f"ws://localhost:8080/api/v1/rl/phase-2-3/ws/training/{experiment_id}" if request.enable_realtime_streaming else None

        return MultiAlgorithmTrainingResponse(
            experiment_id=experiment_id,
            session_ids=session_ids,
            algorithms=request.algorithms,
            status="started",
            estimated_completion_time=estimated_time,
            realtime_stream_url=realtime_url
        )

    except Exception as e:
        logger.error(f"多算法並行訓練啟動失敗: {e}")
        raise HTTPException(status_code=500, detail=f"訓練啟動失敗: {str(e)}")

@router.post("/testing/ab-test", response_model=ABTestResponse)
async def start_ab_test(request: ABTestRequest, background_tasks: BackgroundTasks):
    """
    啟動 A/B 測試
    
    比較兩個算法在相同場景下的性能表現
    """
    try:
        services = await get_services()
        
        # 創建測試 ID
        test_id = f"ab_test_{int(datetime.now().timestamp())}"
        
        # 為兩個算法分別創建測試會話
        session_a = await services["orchestrator"].create_training_session(
            algorithm=request.algorithm_a,
            experiment_name=f"ABTest_{test_id}_A",
            total_episodes=request.episodes_per_algorithm,
            scenario_type="ab_test",
            research_notes=f"A/B 測試 - 算法 A: {request.algorithm_a}"
        )
        
        session_b = await services["orchestrator"].create_training_session(
            algorithm=request.algorithm_b,
            experiment_name=f"ABTest_{test_id}_B",
            total_episodes=request.episodes_per_algorithm,
            scenario_type="ab_test",
            research_notes=f"A/B 測試 - 算法 B: {request.algorithm_b}"
        )

        # 啟動 A/B 測試
        background_tasks.add_task(
            _run_ab_test,
            test_id,
            session_a,
            session_b,
            request.test_scenarios,
            request.significance_level
        )

        return ABTestResponse(
            test_id=test_id,
            algorithm_a_session_id=session_a,
            algorithm_b_session_id=session_b,
            test_scenarios=request.test_scenarios,
            status="started",
            preliminary_results=None
        )

    except Exception as e:
        logger.error(f"A/B 測試啟動失敗: {e}")
        raise HTTPException(status_code=500, detail=f"A/B 測試啟動失敗: {str(e)}")

@router.post("/analysis/performance-comparison", response_model=PerformanceComparisonResponse)
async def compare_performance(request: PerformanceComparisonRequest):
    """
    性能比較分析
    
    對多個訓練會話進行詳細的性能比較和統計分析
    """
    try:
        services = await get_services()
        
        # 獲取會話數據
        sessions_data = {}
        for session_id in request.session_ids:
            session_data = await services["repository"].get_experiment_session(session_id)
            if session_data:
                sessions_data[session_id] = session_data
            else:
                raise HTTPException(status_code=404, detail=f"會話 {session_id} 不存在")

        # 執行性能分析
        comparison_id = f"comparison_{int(datetime.now().timestamp())}"
        analysis_results = await services["analyzer"].compare_algorithms(
            sessions_data=sessions_data,
            metrics=request.metrics,
            statistical_tests=request.statistical_tests
        )

        # 生成建議
        recommendations = await services["analyzer"].generate_recommendations(analysis_results)

        return PerformanceComparisonResponse(
            comparison_id=comparison_id,
            algorithms=[session["algorithm_type"] for session in sessions_data.values()],
            metrics_summary=analysis_results.get("summary", {}),
            statistical_results=analysis_results.get("statistical_tests", {}) if request.statistical_tests else None,
            recommendations=recommendations
        )

    except Exception as e:
        logger.error(f"性能比較分析失敗: {e}")
        raise HTTPException(status_code=500, detail=f"分析失敗: {str(e)}")

@router.post("/decision/realtime", response_model=RealTimeDecisionResponse)
async def make_realtime_decision(request: RealTimeDecisionRequest):
    """
    實時決策執行
    
    使用指定算法對當前狀態進行即時決策，並返回解釋
    """
    try:
        services = await get_services()
        
        start_time = datetime.now()
        
        # 執行實時決策
        decision_result = await services["realtime"].make_decision(
            algorithm=request.algorithm,
            current_state=request.current_state,
            scenario_context=request.scenario_context
        )
        
        # 生成決策解釋
        explanation = await services["analytics"].explain_decision(
            decision=decision_result,
            algorithm=request.algorithm,
            state=request.current_state
        )
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds() * 1000

        # 廣播決策結果到 WebSocket 連接
        await manager.broadcast(json.dumps({
            "type": "realtime_decision",
            "algorithm": request.algorithm,
            "decision": decision_result,
            "execution_time_ms": execution_time,
            "timestamp": end_time.isoformat()
        }))

        return RealTimeDecisionResponse(
            decision=decision_result,
            confidence=decision_result.get("confidence", 0.0),
            explanation=explanation,
            execution_time_ms=execution_time,
            timestamp=end_time
        )

    except Exception as e:
        logger.error(f"實時決策執行失敗: {e}")
        raise HTTPException(status_code=500, detail=f"決策失敗: {str(e)}")

@router.websocket("/ws/training/{experiment_id}")
async def websocket_training_stream(websocket: WebSocket, experiment_id: str):
    """
    訓練過程實時串流
    
    提供訓練進度、性能指標和決策過程的實時更新
    """
    await manager.connect(websocket)
    try:
        # 發送連接確認
        await manager.send_personal_message(
            json.dumps({
                "type": "connection_established",
                "experiment_id": experiment_id,
                "timestamp": datetime.now().isoformat()
            }),
            websocket
        )
        
        # 保持連接並等待斷開
        while True:
            try:
                data = await websocket.receive_text()
                # 處理客戶端消息（如果需要）
                message = json.loads(data)
                if message.get("type") == "ping":
                    await manager.send_personal_message(
                        json.dumps({"type": "pong", "timestamp": datetime.now().isoformat()}),
                        websocket
                    )
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket 處理消息錯誤: {e}")
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)

@router.get("/status")
async def get_phase23_status():
    """
    獲取 Phase 2.3 系統狀態
    
    返回所有服務組件的運行狀態和統計信息
    """
    try:
        services = await get_services()
        
        # 收集各服務的統計信息
        active_connections = len(manager.active_connections)
        
        # 獲取訓練會話統計
        session_stats = await services["orchestrator"].get_session_statistics()
        
        status = {
            "phase": "2.3",
            "status": "operational",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "algorithm_integrator": {"active": True, "algorithms_available": 3},
                "decision_analytics": {"active": True, "analytics_engine": "operational"},
                "real_time_service": {"active": True, "active_connections": active_connections},
                "training_orchestrator": {"active": True, **session_stats},
                "performance_analyzer": {"active": True, "analysis_engine": "operational"},
                "scenario_generator": {"active": True, "phase_22_integration": "complete"}
            },
            "capabilities": {
                "multi_algorithm_training": True,
                "ab_testing": True,
                "real_time_decisions": True,
                "performance_comparison": True,
                "websocket_streaming": True,
                "statistical_analysis": True
            },
            "websocket_connections": active_connections
        }
        
        return status

    except Exception as e:
        logger.error(f"獲取 Phase 2.3 狀態失敗: {e}")
        return {
            "phase": "2.3",
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

# 健康檢查端點
@router.get("/health")
async def health_check():
    """Phase 2.3 服務健康檢查"""
    return {
        "status": "healthy",
        "phase": "2.3",
        "timestamp": datetime.now().isoformat(),
        "capabilities": [
            "multi_algorithm_training",
            "ab_testing", 
            "real_time_decisions",
            "performance_comparison",
            "websocket_streaming"
        ]
    }

# 後台任務函數
async def _run_parallel_training(experiment_id: str, session_ids: List[int], algorithms: List[str], enable_streaming: bool):
    """執行並行訓練的後台任務"""
    try:
        services = await get_services()
        
        # 創建並行訓練任務
        tasks = []
        for i, (session_id, algorithm) in enumerate(zip(session_ids, algorithms)):
            task = asyncio.create_task(
                services["orchestrator"].run_training_session(session_id, algorithm, enable_streaming)
            )
            tasks.append(task)
        
        # 等待所有訓練完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 廣播完成消息
        if enable_streaming:
            await manager.broadcast(json.dumps({
                "type": "experiment_completed",
                "experiment_id": experiment_id,
                "session_ids": session_ids,
                "algorithms": algorithms,
                "results": [str(r) if isinstance(r, Exception) else "completed" for r in results],
                "timestamp": datetime.now().isoformat()
            }))
            
        logger.info(f"並行訓練實驗 {experiment_id} 完成")
        
    except Exception as e:
        logger.error(f"並行訓練執行失敗: {e}")
        if enable_streaming:
            await manager.broadcast(json.dumps({
                "type": "experiment_error",
                "experiment_id": experiment_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }))

async def _run_ab_test(test_id: str, session_a: int, session_b: int, scenarios: List[str], significance_level: float):
    """執行 A/B 測試的後台任務"""
    try:
        services = await get_services()
        
        # 並行執行兩個算法的測試
        results_a, results_b = await asyncio.gather(
            services["orchestrator"].run_training_session(session_a, "algorithm_a", False),
            services["orchestrator"].run_training_session(session_b, "algorithm_b", False)
        )
        
        # 執行統計分析
        statistical_results = await services["analyzer"].perform_ab_test_analysis(
            results_a, results_b, significance_level
        )
        
        # 廣播 A/B 測試結果
        await manager.broadcast(json.dumps({
            "type": "ab_test_completed",
            "test_id": test_id,
            "session_a": session_a,
            "session_b": session_b,
            "statistical_results": statistical_results,
            "timestamp": datetime.now().isoformat()
        }))
        
        logger.info(f"A/B 測試 {test_id} 完成")
        
    except Exception as e:
        logger.error(f"A/B 測試執行失敗: {e}")
        await manager.broadcast(json.dumps({
            "type": "ab_test_error",
            "test_id": test_id,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }))