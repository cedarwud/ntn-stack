"""
Phase 3 Stage 8: Canary 漸進式部署實現
從 1% 流量開始的 Canary 部署策略，實現即時性能監控和問題識別
"""
import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Tuple
import yaml
from pathlib import Path

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CanaryStage(Enum):
    """Canary 部署階段"""
    PREPARING = "preparing"
    CANARY_1_PERCENT = "canary_1_percent"
    CANARY_5_PERCENT = "canary_5_percent"
    CANARY_10_PERCENT = "canary_10_percent"
    CANARY_25_PERCENT = "canary_25_percent"
    CANARY_50_PERCENT = "canary_50_percent"
    CANARY_75_PERCENT = "canary_75_percent"
    FULL_DEPLOYMENT = "full_deployment"
    COMPLETED = "completed"
    ROLLING_BACK = "rolling_back"
    FAILED = "failed"

class CanaryDecision(Enum):
    """Canary 決策"""
    CONTINUE = "continue"      # 繼續下一階段
    HOLD = "hold"             # 保持當前階段
    ROLLBACK = "rollback"     # 回滾部署

@dataclass
class CanaryMetrics:
    """Canary 階段指標"""
    stage: CanaryStage
    traffic_percentage: float
    success_rate: float = 0.0
    error_rate: float = 0.0
    response_time_ms: float = 0.0
    handover_latency_ms: float = 0.0
    handover_success_rate: float = 0.0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    throughput_rps: float = 0.0
    user_sessions: int = 0
    business_impact_score: float = 0.0  # 業務影響評分
    
@dataclass
class CanaryThresholds:
    """Canary 閾值配置"""
    max_error_rate: float = 0.001        # 最大錯誤率 0.1%
    max_response_time_ms: float = 100.0  # 最大響應時間 100ms
    max_handover_latency_ms: float = 50.0 # 最大 handover 延遲 50ms
    min_handover_success_rate: float = 0.995  # 最小 handover 成功率 99.5%
    max_cpu_usage: float = 0.8           # 最大 CPU 使用率 80%
    max_memory_usage: float = 0.8        # 最大記憶體使用率 80%
    min_success_rate: float = 0.999      # 最小成功率 99.9%
    max_business_impact: float = 0.1     # 最大業務影響 10%

@dataclass
class CanaryStageConfig:
    """Canary 階段配置"""
    stage: CanaryStage
    traffic_percentage: float
    duration_minutes: int
    min_requests: int = 100      # 最小請求數要求
    auto_promote: bool = True    # 自動晉升到下一階段
    rollback_on_failure: bool = True

class CanaryDeploymentManager:
    """Canary 漸進式部署管理器"""
    
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.current_stage = CanaryStage.PREPARING
        self.canary_metrics = CanaryMetrics(stage=self.current_stage, traffic_percentage=0.0)
        self.thresholds = CanaryThresholds()
        self.deployment_start_time = None
        self.stage_start_time = None
        self.metrics_history: List[CanaryMetrics] = []
        self.decision_callbacks: List[Callable] = []
        self.is_running = False
        
        # Canary 階段配置
        self.canary_stages = self._initialize_canary_stages()
        
    def _load_config(self) -> Dict[str, Any]:
        """載入配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"載入配置失敗: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """獲取預設配置"""
        return {
            "canary": {
                "stages": [
                    {"traffic_percentage": 1, "duration_minutes": 10},
                    {"traffic_percentage": 5, "duration_minutes": 15}, 
                    {"traffic_percentage": 10, "duration_minutes": 20},
                    {"traffic_percentage": 25, "duration_minutes": 30},
                    {"traffic_percentage": 50, "duration_minutes": 30},
                    {"traffic_percentage": 75, "duration_minutes": 20},
                    {"traffic_percentage": 100, "duration_minutes": 10}
                ],
                "thresholds": {
                    "error_rate": 0.001,
                    "response_time_ms": 100.0,
                    "handover_latency_ms": 50.0,
                    "handover_success_rate": 0.995
                },
                "monitoring": {
                    "check_interval": 30,
                    "min_observation_period": 300
                }
            }
        }
    
    def _initialize_canary_stages(self) -> List[CanaryStageConfig]:
        """初始化 Canary 階段配置"""
        stages_config = self.config.get("canary", {}).get("stages", [])
        
        stage_mappings = [
            (CanaryStage.CANARY_1_PERCENT, 1),
            (CanaryStage.CANARY_5_PERCENT, 5),
            (CanaryStage.CANARY_10_PERCENT, 10),
            (CanaryStage.CANARY_25_PERCENT, 25),
            (CanaryStage.CANARY_50_PERCENT, 50),
            (CanaryStage.CANARY_75_PERCENT, 75),
            (CanaryStage.FULL_DEPLOYMENT, 100)
        ]
        
        canary_stages = []
        
        for i, (stage_enum, default_percentage) in enumerate(stage_mappings):
            if i < len(stages_config):
                stage_config = stages_config[i]
                percentage = stage_config.get("traffic_percentage", default_percentage)
                duration = stage_config.get("duration_minutes", 15)
            else:
                percentage = default_percentage
                duration = 15
            
            canary_stages.append(CanaryStageConfig(
                stage=stage_enum,
                traffic_percentage=percentage,
                duration_minutes=duration,
                min_requests=max(100, int(percentage * 10)),  # 根據流量比例調整最小請求數
                auto_promote=True,
                rollback_on_failure=True
            ))
        
        logger.info(f"初始化 {len(canary_stages)} 個 Canary 階段")
        return canary_stages
    
    async def deploy_canary(self, version: str, services: Optional[List[str]] = None) -> bool:
        """執行 Canary 漸進式部署"""
        try:
            self.deployment_start_time = datetime.now()
            self.is_running = True
            
            logger.info(f"🕯️ 開始 Canary 漸進式部署 - 版本: {version}")
            
            # Phase 1: 準備 Canary 環境
            if not await self._prepare_canary_environment(version, services):
                logger.error("❌ Canary 環境準備失敗")
                return False
            
            # Phase 2: 執行 Canary 階段
            for stage_config in self.canary_stages:
                if not await self._execute_canary_stage(stage_config):
                    logger.error(f"❌ Canary 階段 {stage_config.stage.value} 失敗")
                    await self._rollback_canary()
                    return False
            
            # Phase 3: 完成部署
            await self._complete_canary_deployment()
            
            logger.info("🎉 Canary 漸進式部署成功完成！")
            return True
            
        except Exception as e:
            logger.error(f"❌ Canary 部署過程中發生錯誤: {e}")
            await self._handle_canary_failure(e)
            return False
        
        finally:
            self.is_running = False
    
    async def _prepare_canary_environment(self, version: str, services: Optional[List[str]]) -> bool:
        """準備 Canary 環境"""
        self.current_stage = CanaryStage.PREPARING
        logger.info("🔧 準備 Canary 環境...")
        
        try:
            # 部署 Canary 版本到隔離環境
            await self._deploy_canary_version(version, services)
            
            # 配置流量路由規則
            await self._configure_traffic_routing()
            
            # 初始化監控
            await self._initialize_canary_monitoring()
            
            # 預熱 Canary 環境
            await self._warmup_canary_environment()
            
            logger.info("✅ Canary 環境準備完成")
            return True
            
        except Exception as e:
            logger.error(f"Canary 環境準備失敗: {e}")
            return False
    
    async def _execute_canary_stage(self, stage_config: CanaryStageConfig) -> bool:
        """執行 Canary 階段"""
        self.current_stage = stage_config.stage
        self.stage_start_time = datetime.now()
        
        logger.info(f"🚀 執行 Canary 階段: {stage_config.stage.value} ({stage_config.traffic_percentage}% 流量)")
        
        try:
            # 調整流量分配
            await self._adjust_traffic_percentage(stage_config.traffic_percentage)
            
            # 監控階段執行
            decision = await self._monitor_canary_stage(stage_config)
            
            if decision == CanaryDecision.CONTINUE:
                logger.info(f"✅ Canary 階段 {stage_config.stage.value} 完成，繼續下一階段")
                return True
            elif decision == CanaryDecision.ROLLBACK:
                logger.error(f"❌ Canary 階段 {stage_config.stage.value} 觸發回滾")
                return False
            else:  # HOLD
                logger.warning(f"⏸️ Canary 階段 {stage_config.stage.value} 暫停")
                # 在實際實現中，這裡可能需要人工干預
                return False
                
        except Exception as e:
            logger.error(f"Canary 階段 {stage_config.stage.value} 執行失敗: {e}")
            return False
    
    async def _monitor_canary_stage(self, stage_config: CanaryStageConfig) -> CanaryDecision:
        """監控 Canary 階段"""
        monitoring_config = self.config.get("canary", {}).get("monitoring", {})
        check_interval = monitoring_config.get("check_interval", 30)
        min_observation_period = monitoring_config.get("min_observation_period", 300)
        
        stage_duration = stage_config.duration_minutes * 60  # 轉換為秒
        observation_start = time.time()
        
        logger.info(f"📊 開始監控 Canary 階段 - 持續時間: {stage_config.duration_minutes}分鐘")
        
        while time.time() - observation_start < stage_duration:
            # 收集當前階段指標
            current_metrics = await self._collect_canary_metrics(stage_config)
            self.canary_metrics = current_metrics
            self.metrics_history.append(current_metrics)
            
            # 分析指標並做出決策
            decision = await self._analyze_canary_metrics(current_metrics, stage_config)
            
            if decision == CanaryDecision.ROLLBACK:
                logger.error("🚨 檢測到嚴重問題，觸發回滾")
                return CanaryDecision.ROLLBACK
            
            # 檢查是否滿足最小觀察期要求
            elapsed_time = time.time() - observation_start
            if elapsed_time >= min_observation_period:
                # 如果指標穩定且良好，可以提前晉升
                if (decision == CanaryDecision.CONTINUE and 
                    stage_config.auto_promote and 
                    await self._check_early_promotion_criteria(current_metrics)):
                    logger.info(f"📈 指標穩定良好，提前完成階段 {stage_config.stage.value}")
                    return CanaryDecision.CONTINUE
            
            # 記錄當前狀態
            logger.info(f"🔍 階段監控 - 流量: {current_metrics.traffic_percentage}%, "
                       f"錯誤率: {current_metrics.error_rate:.4f}, "
                       f"響應時間: {current_metrics.response_time_ms:.1f}ms, "
                       f"Handover成功率: {current_metrics.handover_success_rate:.3f}")
            
            await asyncio.sleep(check_interval)
        
        # 階段時間結束，進行最終評估
        final_decision = await self._make_final_stage_decision(stage_config)
        return final_decision
    
    async def _collect_canary_metrics(self, stage_config: CanaryStageConfig) -> CanaryMetrics:
        """收集 Canary 指標"""
        # 模擬指標收集
        await asyncio.sleep(1)
        
        import random
        
        # 根據階段調整指標（模擬真實場景）
        traffic_percentage = stage_config.traffic_percentage
        
        # 基礎成功率 (Canary 版本可能略有差異)
        base_success_rate = 0.999 if traffic_percentage < 50 else 0.9985
        success_rate = base_success_rate + random.uniform(-0.0005, 0.0005)
        
        # 錯誤率 (滿足 <0.1% SLA)
        base_error_rate = 0.0005 if traffic_percentage < 25 else 0.0008
        error_rate = max(0, base_error_rate + random.uniform(-0.0002, 0.0003))
        
        # 響應時間 (隨著流量增加可能略微上升)
        base_response_time = 45 + (traffic_percentage / 100) * 15
        response_time_ms = base_response_time + random.uniform(-10, 15)
        
        # Handover 指標 (滿足 SLA 要求)
        handover_latency_ms = 35 + random.uniform(0, 10)  # 35-45ms
        handover_success_rate = 0.996 + random.uniform(0, 0.003)  # 99.6-99.9%
        
        # 資源使用率
        cpu_usage = 0.4 + (traffic_percentage / 100) * 0.3 + random.uniform(-0.1, 0.1)
        memory_usage = 0.5 + (traffic_percentage / 100) * 0.2 + random.uniform(-0.05, 0.1)
        
        # 吞吐量
        throughput_rps = traffic_percentage * 10 + random.uniform(-50, 100)
        
        # 用戶會話數
        user_sessions = int(traffic_percentage * 50 + random.uniform(0, 100))
        
        # 業務影響評分 (0-1, 越低越好)
        business_impact_score = max(0, error_rate * 10 + max(0, response_time_ms - 80) / 1000)
        
        metrics = CanaryMetrics(
            stage=stage_config.stage,
            traffic_percentage=traffic_percentage,
            success_rate=success_rate,
            error_rate=error_rate,
            response_time_ms=response_time_ms,
            handover_latency_ms=handover_latency_ms,
            handover_success_rate=handover_success_rate,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            throughput_rps=throughput_rps,
            user_sessions=user_sessions,
            business_impact_score=business_impact_score
        )
        
        return metrics
    
    async def _analyze_canary_metrics(self, metrics: CanaryMetrics, stage_config: CanaryStageConfig) -> CanaryDecision:
        """分析 Canary 指標並做出決策"""
        
        # 檢查嚴重錯誤條件 (立即回滾)
        critical_issues = []
        
        if metrics.error_rate > self.thresholds.max_error_rate:
            critical_issues.append(f"錯誤率 {metrics.error_rate:.4f} 超過閾值 {self.thresholds.max_error_rate}")
        
        if metrics.handover_latency_ms > self.thresholds.max_handover_latency_ms:
            critical_issues.append(f"Handover 延遲 {metrics.handover_latency_ms:.1f}ms 超過 SLA 閾值")
        
        if metrics.handover_success_rate < self.thresholds.min_handover_success_rate:
            critical_issues.append(f"Handover 成功率 {metrics.handover_success_rate:.3f} 低於 SLA 閾值")
        
        if metrics.response_time_ms > self.thresholds.max_response_time_ms:
            critical_issues.append(f"響應時間 {metrics.response_time_ms:.1f}ms 超過閾值")
        
        if critical_issues:
            logger.error("🚨 檢測到嚴重問題:")
            for issue in critical_issues:
                logger.error(f"  - {issue}")
            return CanaryDecision.ROLLBACK
        
        # 檢查警告條件
        warning_issues = []
        
        if metrics.cpu_usage > self.thresholds.max_cpu_usage:
            warning_issues.append(f"CPU 使用率 {metrics.cpu_usage:.2f} 超過閾值")
        
        if metrics.memory_usage > self.thresholds.max_memory_usage:
            warning_issues.append(f"記憶體使用率 {metrics.memory_usage:.2f} 超過閾值")
        
        if metrics.business_impact_score > self.thresholds.max_business_impact:
            warning_issues.append(f"業務影響評分 {metrics.business_impact_score:.3f} 過高")
        
        if warning_issues:
            logger.warning("⚠️ 檢測到警告問題:")
            for issue in warning_issues:
                logger.warning(f"  - {issue}")
            
            # 根據問題嚴重程度決定是否暫停
            if len(warning_issues) >= 2:
                return CanaryDecision.HOLD
        
        # 一切正常，可以繼續
        return CanaryDecision.CONTINUE
    
    async def _check_early_promotion_criteria(self, metrics: CanaryMetrics) -> bool:
        """檢查提前晉升條件"""
        # 檢查指標是否遠優於閾值
        if (metrics.error_rate < self.thresholds.max_error_rate * 0.5 and
            metrics.response_time_ms < self.thresholds.max_response_time_ms * 0.8 and
            metrics.handover_latency_ms < self.thresholds.max_handover_latency_ms * 0.8 and
            metrics.handover_success_rate > self.thresholds.min_handover_success_rate + 0.001):
            
            # 檢查歷史穩定性
            if len(self.metrics_history) >= 3:
                recent_metrics = self.metrics_history[-3:]
                error_rates = [m.error_rate for m in recent_metrics]
                response_times = [m.response_time_ms for m in recent_metrics]
                
                # 檢查指標穩定性
                error_rate_variance = max(error_rates) - min(error_rates)
                response_time_variance = max(response_times) - min(response_times)
                
                if error_rate_variance < 0.0001 and response_time_variance < 10:
                    return True
        
        return False
    
    async def _make_final_stage_decision(self, stage_config: CanaryStageConfig) -> CanaryDecision:
        """做出最終階段決策"""
        # 分析整個階段的指標
        stage_metrics = [m for m in self.metrics_history if m.stage == stage_config.stage]
        
        if not stage_metrics:
            logger.error("沒有收集到階段指標")
            return CanaryDecision.ROLLBACK
        
        # 計算平均指標
        avg_error_rate = sum(m.error_rate for m in stage_metrics) / len(stage_metrics)
        avg_response_time = sum(m.response_time_ms for m in stage_metrics) / len(stage_metrics)
        avg_handover_latency = sum(m.handover_latency_ms for m in stage_metrics) / len(stage_metrics)
        avg_handover_success_rate = sum(m.handover_success_rate for m in stage_metrics) / len(stage_metrics)
        
        # 檢查 SLA 合規性
        sla_violations = []
        
        if avg_error_rate > self.thresholds.max_error_rate:
            sla_violations.append(f"平均錯誤率 {avg_error_rate:.4f} 超過閾值")
        
        if avg_handover_latency > self.thresholds.max_handover_latency_ms:
            sla_violations.append(f"平均 Handover 延遲 {avg_handover_latency:.1f}ms 超過 SLA")
        
        if avg_handover_success_rate < self.thresholds.min_handover_success_rate:
            sla_violations.append(f"平均 Handover 成功率 {avg_handover_success_rate:.3f} 低於 SLA")
        
        if sla_violations:
            logger.error(f"🚨 階段 {stage_config.stage.value} SLA 違規:")
            for violation in sla_violations:
                logger.error(f"  - {violation}")
            return CanaryDecision.ROLLBACK
        
        logger.info(f"✅ 階段 {stage_config.stage.value} 指標良好:")
        logger.info(f"  - 平均錯誤率: {avg_error_rate:.4f}")
        logger.info(f"  - 平均響應時間: {avg_response_time:.1f}ms")
        logger.info(f"  - 平均 Handover 延遲: {avg_handover_latency:.1f}ms")
        logger.info(f"  - 平均 Handover 成功率: {avg_handover_success_rate:.3f}")
        
        return CanaryDecision.CONTINUE
    
    # 輔助方法實現
    async def _deploy_canary_version(self, version: str, services: Optional[List[str]]):
        """部署 Canary 版本"""
        logger.info(f"部署 Canary 版本 {version}")
        services_to_deploy = services or ["netstack", "simworld", "frontend"]
        
        for service in services_to_deploy:
            logger.info(f"  - 部署 {service}:{version} 到 Canary 環境")
            await asyncio.sleep(2)  # 模擬部署時間
    
    async def _configure_traffic_routing(self):
        """配置流量路由"""
        logger.info("配置流量路由規則")
        await asyncio.sleep(1)
    
    async def _initialize_canary_monitoring(self):
        """初始化 Canary 監控"""
        logger.info("初始化 Canary 監控系統")
        await asyncio.sleep(1)
    
    async def _warmup_canary_environment(self):
        """預熱 Canary 環境"""
        logger.info("預熱 Canary 環境")
        # 發送測試請求來預熱服務
        await asyncio.sleep(3)
    
    async def _adjust_traffic_percentage(self, percentage: float):
        """調整流量分配比例"""
        logger.info(f"調整流量分配 - Canary: {percentage}%, Stable: {100-percentage}%")
        # 更新負載均衡器配置
        await asyncio.sleep(2)
    
    async def _complete_canary_deployment(self):
        """完成 Canary 部署"""
        self.current_stage = CanaryStage.COMPLETED
        logger.info("🎉 Canary 部署完成，切換到 100% 新版本")
        
        # 記錄部署成功
        deployment_duration = (datetime.now() - self.deployment_start_time).total_seconds()
        
        success_record = {
            "deployment_type": "canary",
            "start_time": self.deployment_start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "duration_seconds": deployment_duration,
            "stages_completed": len([m for m in self.metrics_history]),
            "final_sla_compliance": True,
            "average_error_rate": sum(m.error_rate for m in self.metrics_history) / len(self.metrics_history),
            "average_handover_latency": sum(m.handover_latency_ms for m in self.metrics_history) / len(self.metrics_history)
        }
        
        logger.info(f"Canary 部署記錄: {json.dumps(success_record, ensure_ascii=False, indent=2)}")
    
    async def _rollback_canary(self):
        """回滾 Canary 部署"""
        self.current_stage = CanaryStage.ROLLING_BACK
        logger.warning("🔄 執行 Canary 回滾")
        
        # 將流量切回穩定版本
        await self._adjust_traffic_percentage(0)
        
        # 停止 Canary 環境
        await self._stop_canary_environment()
        
        self.current_stage = CanaryStage.FAILED
        logger.info("✅ Canary 回滾完成")
    
    async def _stop_canary_environment(self):
        """停止 Canary 環境"""
        logger.info("停止 Canary 環境")
        await asyncio.sleep(2)
    
    async def _handle_canary_failure(self, error: Exception):
        """處理 Canary 失敗"""
        self.current_stage = CanaryStage.FAILED
        logger.error(f"Canary 部署失敗: {error}")
        
        # 確保回滾到穩定狀態
        await self._rollback_canary()
    
    def get_deployment_status(self) -> Dict[str, Any]:
        """獲取部署狀態"""
        return {
            "current_stage": self.current_stage.value,
            "is_running": self.is_running,
            "current_metrics": self.canary_metrics.__dict__ if self.canary_metrics else None,
            "total_stages": len(self.canary_stages),
            "completed_stages": len(set(m.stage for m in self.metrics_history)),
            "deployment_duration": (
                (datetime.now() - self.deployment_start_time).total_seconds()
                if self.deployment_start_time else 0
            )
        }

# 使用示例
async def main():
    """Canary 部署示例"""
    
    # 創建 Canary 配置
    config = {
        "canary": {
            "stages": [
                {"traffic_percentage": 1, "duration_minutes": 5},   # 1% - 5分鐘
                {"traffic_percentage": 5, "duration_minutes": 10},  # 5% - 10分鐘
                {"traffic_percentage": 10, "duration_minutes": 10}, # 10% - 10分鐘
                {"traffic_percentage": 25, "duration_minutes": 15}, # 25% - 15分鐘
                {"traffic_percentage": 50, "duration_minutes": 15}, # 50% - 15分鐘
                {"traffic_percentage": 75, "duration_minutes": 10}, # 75% - 10分鐘
                {"traffic_percentage": 100, "duration_minutes": 5}  # 100% - 5分鐘
            ],
            "thresholds": {
                "error_rate": 0.001,
                "response_time_ms": 100.0,
                "handover_latency_ms": 50.0,
                "handover_success_rate": 0.995
            },
            "monitoring": {
                "check_interval": 15,      # 15秒檢查一次
                "min_observation_period": 120  # 最小觀察期 2分鐘
            }
        }
    }
    
    config_path = "/tmp/canary_config.yaml"
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
    
    # 初始化 Canary 部署管理器
    canary_manager = CanaryDeploymentManager(config_path)
    
    # 執行 Canary 部署
    print("🕯️ 開始 Canary 漸進式部署...")
    success = await canary_manager.deploy_canary("v2.1.0", ["netstack", "simworld"])
    
    if success:
        print("🎉 Canary 部署成功！")
        
        # 顯示部署狀態
        status = canary_manager.get_deployment_status()
        print(f"部署狀態: {json.dumps(status, ensure_ascii=False, indent=2)}")
        
        # 顯示最終指標
        if canary_manager.metrics_history:
            final_metrics = canary_manager.metrics_history[-1]
            print(f"\n最終指標:")
            print(f"  - 錯誤率: {final_metrics.error_rate:.4f} < 0.001 ✅")
            print(f"  - Handover 延遲: {final_metrics.handover_latency_ms:.1f}ms < 50ms ✅")
            print(f"  - Handover 成功率: {final_metrics.handover_success_rate:.3f} > 0.995 ✅")
            print(f"  - 響應時間: {final_metrics.response_time_ms:.1f}ms < 100ms ✅")
    else:
        print("❌ Canary 部署失敗")

if __name__ == "__main__":
    asyncio.run(main())