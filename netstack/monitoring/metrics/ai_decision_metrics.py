# AI決策引擎 Prometheus 指標定義
# 階段8：系統監控與營運整合
# 根據 1.ai.md 規範實現核心監控指標

from prometheus_client import Counter, Histogram, Gauge, Enum, Info
from typing import Optional, Dict, Any
import time

# =============================================================================
# 1. AI決策系統核心指標
# =============================================================================

# 決策延遲 - 高精度時間桶
DECISION_LATENCY = Histogram(
    "ai_decision_latency_seconds",
    "AI決策延遲時間",
    buckets=[0.001, 0.005, 0.01, 0.015, 0.02, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
    labelnames=["algorithm", "decision_type", "component"],
)

# 決策成功率計數器
DECISIONS_TOTAL = Counter(
    "ntn_decisions_total",
    "總決策次數",
    labelnames=["algorithm", "decision_type", "result"],
)

DECISIONS_SUCCESS_TOTAL = Counter(
    "ntn_decisions_success_total",
    "成功決策次數",
    labelnames=["algorithm", "decision_type"],
)

DECISIONS_ERROR_TOTAL = Counter(
    "ntn_decisions_error_total",
    "失敗決策次數",
    labelnames=["algorithm", "decision_type", "error_category"],
)

# 衛星切換成功率
HANDOVER_SUCCESS_RATE = Gauge(
    "handover_success_rate",
    "衛星切換成功率",
    labelnames=["algorithm", "satellite_type"],
)

# 系統資源使用率
SYSTEM_CPU_USAGE = Gauge(
    "system_cpu_usage_percent", "CPU使用率百分比", labelnames=["component", "instance"]
)

SYSTEM_MEMORY_USAGE = Gauge(
    "system_memory_usage_percent",
    "內存使用率百分比",
    labelnames=["component", "instance"],
)

SYSTEM_GPU_UTILIZATION = Gauge(
    "system_gpu_utilization_percent",
    "GPU使用率百分比",
    labelnames=["gpu_id", "component"],
)

# API端點響應時間
HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP請求響應時間",
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    labelnames=["method", "endpoint", "status_code"],
)

# =============================================================================
# 2. RL訓練監控指標
# =============================================================================

# RL訓練進度
RL_TRAINING_PROGRESS = Gauge(
    "rl_training_progress_percent",
    "RL訓練進度百分比",
    labelnames=["algorithm", "environment"],
)

# RL訓練成功率
RL_TRAINING_SUCCESS_RATE = Gauge(
    "rl_training_success_rate", "RL訓練成功率", labelnames=["algorithm", "session_id"]
)

# 策略損失
POLICY_LOSS = Gauge(
    "rl_policy_loss", "RL策略損失函數值", labelnames=["algorithm", "epoch"]
)

# 訓練獎勵
TRAINING_REWARD = Gauge(
    "rl_training_reward", "RL訓練獎勵值", labelnames=["algorithm", "episode"]
)

# =============================================================================
# 3. 系統健康指標
# =============================================================================

# 系統健康分數
SYSTEM_HEALTH_SCORE = Gauge(
    "system_health_score", "系統健康分數 (0-100)", labelnames=["component", "subsystem"]
)

# 服務可用性
SERVICE_AVAILABILITY = Gauge(
    "service_availability_percent",
    "服務可用性百分比",
    labelnames=["service", "endpoint"],
)

# 數據庫連接
DATABASE_CONNECTIONS = Gauge(
    "database_connections_active",
    "活躍數據庫連接數",
    labelnames=["database", "pool_name"],
)

# 消息隊列指標
QUEUE_SIZE = Gauge(
    "queue_size_current", "當前隊列大小", labelnames=["queue_name", "consumer_group"]
)

# =============================================================================
# 4. 業務指標
# =============================================================================

# 候選衛星篩選時間
CANDIDATE_SELECTION_DURATION = Histogram(
    "candidate_selection_duration_seconds",
    "候選衛星篩選耗時",
    buckets=[0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1],
    labelnames=["selection_strategy", "candidate_count"],
)

# 換手延遲
HANDOVER_DELAY = Histogram(
    "handover_delay_milliseconds",
    "衛星換手延遲時間(毫秒)",
    buckets=[1, 5, 10, 20, 50, 100, 200, 500, 1000],
    labelnames=["from_satellite", "to_satellite", "algorithm"],
)

# 信號中斷時間
SIGNAL_DROP_TIME = Histogram(
    "signal_drop_time_milliseconds",
    "信號中斷時間(毫秒)",
    buckets=[0, 1, 5, 10, 25, 50, 100, 200],
    labelnames=["satellite_id", "cause"],
)

# 能效指標
ENERGY_EFFICIENCY = Gauge(
    "energy_efficiency_ratio",
    "能效比 (0-1)",
    labelnames=["algorithm", "optimization_type"],
)

# =============================================================================
# 5. 可視化與前端整合指標
# =============================================================================

# WebSocket連接數
WEBSOCKET_CONNECTIONS = Gauge(
    "websocket_connections_active",
    "活躍WebSocket連接數",
    labelnames=["endpoint", "client_type"],
)

# 可視化同步延遲
VISUALIZATION_SYNC_LATENCY = Histogram(
    "visualization_sync_latency_seconds",
    "可視化同步延遲",
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0],
    labelnames=["visualization_type", "data_type"],
)

# 動畫幀率
ANIMATION_FPS = Gauge(
    "animation_fps", "動畫幀率", labelnames=["animation_type", "quality_level"]
)

# 3D渲染性能
RENDERING_PERFORMANCE = Histogram(
    "rendering_performance_milliseconds",
    "3D渲染性能(毫秒)",
    buckets=[5, 10, 16.67, 33.33, 50, 100, 200],  # 16.67ms = 60fps
    labelnames=["renderer", "scene_complexity"],
)

# =============================================================================
# 6. 系統狀態枚舉指標
# =============================================================================

# AI決策引擎狀態
AI_DECISION_ENGINE_STATE = Enum(
    "ai_decision_engine_state",
    "AI決策引擎當前狀態",
    labelnames=["instance"],
    states=["initializing", "active", "training", "error", "maintenance"],
)

# RL訓練狀態
RL_TRAINING_STATE = Enum(
    "rl_training_state",
    "RL訓練當前狀態",
    labelnames=["algorithm", "session_id"],
    states=["idle", "training", "evaluating", "converged", "failed"],
)

# =============================================================================
# 7. 信息型指標
# =============================================================================

# 系統版本信息
SYSTEM_INFO = Info("ntn_stack_build_info", "NTN Stack系統構建信息")

# AI模型信息
AI_MODEL_INFO = Info(
    "ai_model_info", "AI模型信息", labelnames=["model_type", "version"]
)

# =============================================================================
# 8. 便利函數與上下文管理器
# =============================================================================


class DecisionLatencyTimer:
    """決策延遲計時器上下文管理器"""

    def __init__(
        self, algorithm: str, decision_type: str, component: str = "decision-engine"
    ):
        self.algorithm = algorithm
        self.decision_type = decision_type
        self.component = component
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            latency = time.time() - self.start_time
            DECISION_LATENCY.labels(
                algorithm=self.algorithm,
                decision_type=self.decision_type,
                component=self.component,
            ).observe(latency)


def record_decision_result(
    algorithm: str,
    decision_type: str,
    success: bool,
    error_category: Optional[str] = None,
):
    """記錄決策結果的便利函數"""
    result = "success" if success else "error"

    # 總決策計數
    DECISIONS_TOTAL.labels(
        algorithm=algorithm, decision_type=decision_type, result=result
    ).inc()

    if success:
        DECISIONS_SUCCESS_TOTAL.labels(
            algorithm=algorithm, decision_type=decision_type
        ).inc()
    else:
        DECISIONS_ERROR_TOTAL.labels(
            algorithm=algorithm,
            decision_type=decision_type,
            error_category=error_category or "unknown",
        ).inc()


def update_system_health(component: str, subsystem: str, health_score: float):
    """更新系統健康分數"""
    SYSTEM_HEALTH_SCORE.labels(component=component, subsystem=subsystem).set(
        max(0, min(100, health_score))
    )  # 確保在0-100範圍內


def record_handover_performance(
    from_sat: str, to_sat: str, algorithm: str, delay_ms: float, success: bool
):
    """記錄換手性能指標"""
    # 記錄延遲
    HANDOVER_DELAY.labels(
        from_satellite=from_sat, to_satellite=to_sat, algorithm=algorithm
    ).observe(delay_ms)

    # 記錄決策結果
    record_decision_result(algorithm, "handover", success)


# =============================================================================
# 6. 新增系統整合指標
# =============================================================================

# 算法切換指標
ALGORITHM_SWITCH_TOTAL = Counter(
    "algorithm_switch_total",
    "算法切換總次數",
    labelnames=["from_algorithm", "to_algorithm", "trigger_reason"],
)

# 訓練會話指標
TRAINING_SESSION_START = Counter(
    "training_session_start_total",
    "訓練會話開始次數",
    labelnames=["algorithm", "session_type"],
)

# RL互動指標
RL_EPISODES_TOTAL = Counter(
    "rl_episodes_total", "RL回合總數", labelnames=["algorithm", "environment"]
)

RL_ACTIONS_TOTAL = Counter(
    "rl_actions_total", "RL動作總數", labelnames=["algorithm", "action_type"]
)

# 模型相關指標
MODEL_PARAMETERS_TOTAL = Gauge(
    "model_parameters_total", "模型參數數量", labelnames=["algorithm", "model_type"]
)

MODEL_MEMORY_USAGE_BYTES = Gauge(
    "model_memory_usage_bytes", "模型內存使用量", labelnames=["algorithm", "device"]
)

# 網路拓撲指標
SATELLITE_UTILIZATION_RATIO = Gauge(
    "satellite_utilization_ratio",
    "衛星使用率",
    labelnames=["satellite_id", "satellite_type"],
)

SIGNAL_STRENGTH_DBM = Gauge(
    "signal_strength_dbm",
    "信號強度(dBm)",
    labelnames=["satellite_id", "ground_station"],
)

SIGNAL_NOISE_RATIO_DB = Gauge(
    "signal_noise_ratio_db", "信噪比(dB)", labelnames=["satellite_id", "frequency_band"]
)

# 性能基準指標
THROUGHPUT_MBPS = Gauge(
    "throughput_mbps", "吞吐量(Mbps)", labelnames=["algorithm", "scenario"]
)

POWER_CONSUMPTION_WATTS = Gauge(
    "power_consumption_watts", "功耗(W)", labelnames=["component", "algorithm"]
)

# =============================================================================
# 7. 高級功能函數
# =============================================================================


def record_algorithm_switch(from_algo: str, to_algo: str, reason: str):
    """記錄算法切換事件"""
    ALGORITHM_SWITCH_TOTAL.labels(
        from_algorithm=from_algo, to_algorithm=to_algo, trigger_reason=reason
    ).inc()


def record_training_session(algorithm: str, session_type: str = "normal"):
    """記錄訓練會話開始"""
    TRAINING_SESSION_START.labels(algorithm=algorithm, session_type=session_type).inc()


def record_rl_interaction(algorithm: str, environment: str, action_type: str):
    """記錄RL環境互動"""
    RL_EPISODES_TOTAL.labels(algorithm=algorithm, environment=environment).inc()

    RL_ACTIONS_TOTAL.labels(algorithm=algorithm, action_type=action_type).inc()


def update_satellite_metrics(
    satellite_id: str,
    satellite_type: str,
    utilization: float,
    signal_strength: float,
    signal_noise_ratio: float,
):
    """更新衛星相關指標"""
    SATELLITE_UTILIZATION_RATIO.labels(
        satellite_id=satellite_id, satellite_type=satellite_type
    ).set(utilization)

    SIGNAL_STRENGTH_DBM.labels(satellite_id=satellite_id, ground_station="default").set(
        signal_strength
    )

    SIGNAL_NOISE_RATIO_DB.labels(
        satellite_id=satellite_id, frequency_band="ku_band"
    ).set(signal_noise_ratio)


def update_model_metrics(
    algorithm: str,
    model_type: str,
    param_count: int,
    memory_usage: int,
    device: str = "gpu",
):
    """更新模型相關指標"""
    MODEL_PARAMETERS_TOTAL.labels(algorithm=algorithm, model_type=model_type).set(
        param_count
    )

    MODEL_MEMORY_USAGE_BYTES.labels(algorithm=algorithm, device=device).set(
        memory_usage
    )


def update_performance_metrics(
    algorithm: str,
    scenario: str,
    throughput: float,
    power_consumption: float,
    component: str = "ai_engine",
):
    """更新性能基準指標"""
    THROUGHPUT_MBPS.labels(algorithm=algorithm, scenario=scenario).set(throughput)

    POWER_CONSUMPTION_WATTS.labels(component=component, algorithm=algorithm).set(
        power_consumption
    )


# =============================================================================
# 8. 指標收集和導出功能
# =============================================================================


def get_all_metrics() -> Dict[str, Any]:
    """獲取所有註冊的指標"""
    from prometheus_client import CollectorRegistry, generate_latest
    from prometheus_client.core import REGISTRY

    return {
        "decision_latency": DECISION_LATENCY,
        "decisions_total": DECISIONS_TOTAL,
        "decisions_success": DECISIONS_SUCCESS_TOTAL,
        "decisions_error": DECISIONS_ERROR_TOTAL,
        "handover_success_rate": HANDOVER_SUCCESS_RATE,
        "system_cpu_usage": SYSTEM_CPU_USAGE,
        "system_memory_usage": SYSTEM_MEMORY_USAGE,
        "system_gpu_utilization": SYSTEM_GPU_UTILIZATION,
        "http_request_duration": HTTP_REQUEST_DURATION,
        "rl_training_progress": RL_TRAINING_PROGRESS,
        "rl_training_success_rate": RL_TRAINING_SUCCESS_RATE,
        "policy_loss": POLICY_LOSS,
        "training_reward": TRAINING_REWARD,
        "system_health_score": SYSTEM_HEALTH_SCORE,
        "service_availability": SERVICE_AVAILABILITY,
        "database_connections": DATABASE_CONNECTIONS,
        "queue_size": QUEUE_SIZE,
        "candidate_selection_duration": CANDIDATE_SELECTION_DURATION,
        "handover_delay": HANDOVER_DELAY,
        "signal_drop_time": SIGNAL_DROP_TIME,
        "energy_efficiency": ENERGY_EFFICIENCY,
        "websocket_connections": WEBSOCKET_CONNECTIONS,
        "visualization_sync_latency": VISUALIZATION_SYNC_LATENCY,
        "animation_fps": ANIMATION_FPS,
        "rendering_performance": RENDERING_PERFORMANCE,
    }


def export_metrics_to_prometheus() -> str:
    """導出所有指標為Prometheus格式"""
    from prometheus_client import generate_latest
    from prometheus_client.core import REGISTRY

    return generate_latest(REGISTRY).decode("utf-8")


def clear_all_metrics():
    """清空所有指標（主要用於測試）"""
    from prometheus_client.core import REGISTRY

    collectors = list(REGISTRY._collector_to_names.keys())
    for collector in collectors:
        try:
            REGISTRY.unregister(collector)
        except KeyError:
            pass


# =============================================================================
# 9. 監控數據模擬器（用於測試和演示）
# =============================================================================

import random
import threading
import time


class MetricsSimulator:
    """指標數據模擬器 - 用於測試和演示"""

    def __init__(self):
        self.running = False
        self.thread = None

    def start(self):
        """開始模擬數據生成"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._simulate_metrics)
            self.thread.daemon = True
            self.thread.start()

    def stop(self):
        """停止模擬數據生成"""
        self.running = False
        if self.thread:
            self.thread.join()

    def _simulate_metrics(self):
        """模擬指標數據生成主循環"""
        algorithms = ["dqn", "ppo", "sac"]
        satellites = ["sat_001", "sat_002", "sat_003", "sat_004"]

        while self.running:
            try:
                # 模擬決策延遲
                for algo in algorithms:
                    latency = random.uniform(0.005, 0.025)  # 5-25ms
                    with DecisionLatencyTimer(algo, "handover"):
                        time.sleep(latency)

                # 模擬決策成功率
                for algo in algorithms:
                    success = random.choice([True, True, True, False])  # 75%成功率
                    record_decision_result(algo, "handover", success)

                # 模擬系統資源
                for component in ["ai_engine", "rl_trainer", "decision_executor"]:
                    SYSTEM_CPU_USAGE.labels(component=component, instance="main").set(
                        random.uniform(20, 80)
                    )
                    SYSTEM_MEMORY_USAGE.labels(
                        component=component, instance="main"
                    ).set(random.uniform(30, 70))

                # 模擬RL訓練進度
                for algo in algorithms:
                    progress = min(100, random.uniform(0, 100))
                    RL_TRAINING_PROGRESS.labels(
                        algorithm=algo, environment="satellite_env"
                    ).set(progress)

                    reward = random.uniform(-10, 100)
                    TRAINING_REWARD.labels(algorithm=algo, episode="current").set(
                        reward
                    )

                # 模擬衛星指標
                for sat in satellites:
                    update_satellite_metrics(
                        satellite_id=sat,
                        satellite_type="leo",
                        utilization=random.uniform(0.3, 0.9),
                        signal_strength=random.uniform(-80, -40),
                        signal_noise_ratio=random.uniform(10, 30),
                    )

                # 模擬切換性能
                for algo in algorithms:
                    success_rate = random.uniform(0.85, 0.98)
                    HANDOVER_SUCCESS_RATE.labels(
                        algorithm=algo, satellite_type="leo"
                    ).set(success_rate)

                time.sleep(5)  # 每5秒更新一次

            except Exception as e:
                print(f"Metrics simulation error: {e}")
                time.sleep(1)


# 全局模擬器實例
_simulator = MetricsSimulator()


def start_metrics_simulation():
    """啟動指標模擬（用於開發和測試）"""
    _simulator.start()


def stop_metrics_simulation():
    """停止指標模擬"""
    _simulator.stop()


# =============================================================================
# 9. 初始化系統信息
# =============================================================================


def initialize_system_metrics():
    """初始化系統信息指標"""
    import os
    from datetime import datetime

    # 設置系統構建信息
    SYSTEM_INFO.info(
        {
            "version": os.getenv("NTN_STACK_VERSION", "dev"),
            "build_date": datetime.now().isoformat(),
            "git_commit": os.getenv("GIT_COMMIT", "unknown"),
            "environment": os.getenv("ENVIRONMENT", "development"),
        }
    )

    # 初始化決策引擎狀態
    AI_DECISION_ENGINE_STATE.labels(instance="main").state("initializing")

    # 設置初始健康分數
    for component in [
        "decision-engine",
        "rl-trainer",
        "candidate-selector",
        "visualizer",
    ]:
        update_system_health(component, "core", 100.0)


# 在模塊導入時初始化
initialize_system_metrics()
