"""
Migration Orchestrator
======================

階段6遷移流程自動化協調器
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import structlog

from .feature_flag_manager import get_feature_flag_manager, FeatureStatus
from .api_proxy import get_api_proxy

logger = structlog.get_logger(__name__)

class MigrationPhase(Enum):
    """遷移階段"""
    PREPARATION = "preparation"
    GRADUAL_ROLLOUT = "gradual_rollout"
    FULL_DEPLOYMENT = "full_deployment"
    VALIDATION = "validation"
    CLEANUP = "cleanup"

@dataclass
class MigrationPlan:
    """遷移計劃"""
    phase: MigrationPhase
    steps: List[str]
    success_criteria: List[str]
    rollback_triggers: List[str]
    estimated_duration: timedelta
    
@dataclass
class MigrationResult:
    """遷移結果"""
    success: bool
    phase: MigrationPhase
    completed_steps: List[str]
    failed_steps: List[str]
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = None
    duration: timedelta = None

class MigrationOrchestrator:
    """遷移協調器"""
    
    def __init__(self):
        self.feature_manager = get_feature_flag_manager()
        self.api_proxy = get_api_proxy()
        self.migration_plans = self._create_migration_plans()
        self.current_phase = MigrationPhase.PREPARATION
        
    def _create_migration_plans(self) -> Dict[MigrationPhase, MigrationPlan]:
        """創建遷移計劃"""
        return {
            MigrationPhase.PREPARATION: MigrationPlan(
                phase=MigrationPhase.PREPARATION,
                steps=[
                    "validate_system_health",
                    "backup_current_system",
                    "verify_new_system_readiness",
                    "prepare_monitoring"
                ],
                success_criteria=[
                    "all_tests_pass",
                    "system_health_good",
                    "backup_complete"
                ],
                rollback_triggers=[
                    "critical_test_failure",
                    "system_instability"
                ],
                estimated_duration=timedelta(hours=2)
            ),
            
            MigrationPhase.GRADUAL_ROLLOUT: MigrationPlan(
                phase=MigrationPhase.GRADUAL_ROLLOUT,
                steps=[
                    "enable_event_processor",
                    "monitor_event_processing",
                    "enable_candidate_selector",
                    "monitor_candidate_selection",
                    "enable_rl_engine",
                    "monitor_rl_decisions",
                    "enable_executor",
                    "monitor_execution"
                ],
                success_criteria=[
                    "error_rate_below_threshold",
                    "performance_maintained",
                    "user_satisfaction_stable"
                ],
                rollback_triggers=[
                    "error_rate_spike",
                    "performance_degradation",
                    "user_complaints"
                ],
                estimated_duration=timedelta(days=2)
            ),
            
            MigrationPhase.FULL_DEPLOYMENT: MigrationPlan(
                phase=MigrationPhase.FULL_DEPLOYMENT,
                steps=[
                    "enable_api_proxy",
                    "route_traffic_to_new_system",
                    "monitor_full_system",
                    "validate_integration"
                ],
                success_criteria=[
                    "100_percent_traffic_success",
                    "performance_improved",
                    "zero_critical_errors"
                ],
                rollback_triggers=[
                    "system_failure",
                    "data_corruption",
                    "business_impact"
                ],
                estimated_duration=timedelta(days=1)
            ),
            
            MigrationPhase.VALIDATION: MigrationPlan(
                phase=MigrationPhase.VALIDATION,
                steps=[
                    "run_comprehensive_tests",
                    "validate_business_metrics",
                    "verify_performance_gains",
                    "collect_user_feedback"
                ],
                success_criteria=[
                    "all_tests_pass",
                    "business_metrics_improved",
                    "performance_targets_met"
                ],
                rollback_triggers=[
                    "validation_failure",
                    "business_metrics_decline"
                ],
                estimated_duration=timedelta(days=3)
            ),
            
            MigrationPhase.CLEANUP: MigrationPlan(
                phase=MigrationPhase.CLEANUP,
                steps=[
                    "disable_old_system",
                    "remove_old_code",
                    "update_documentation",
                    "final_validation"
                ],
                success_criteria=[
                    "old_system_removed",
                    "documentation_updated",
                    "system_clean"
                ],
                rollback_triggers=[
                    "unexpected_dependencies"
                ],
                estimated_duration=timedelta(days=1)
            )
        }
    
    async def execute_full_migration(self) -> List[MigrationResult]:
        """執行完整遷移流程"""
        logger.info("Starting full migration process")
        
        results = []
        
        for phase in MigrationPhase:
            logger.info(f"Starting migration phase: {phase.value}")
            
            result = await self.execute_phase(phase)
            results.append(result)
            
            if not result.success:
                logger.error(f"Migration phase failed: {phase.value}", error=result.error_message)
                
                # 執行回滾
                await self.rollback_to_phase(phase)
                break
            
            logger.info(f"Migration phase completed: {phase.value}")
            self.current_phase = phase
        
        return results
    
    async def execute_phase(self, phase: MigrationPhase) -> MigrationResult:
        """執行特定遷移階段"""
        start_time = datetime.utcnow()
        plan = self.migration_plans[phase]
        
        completed_steps = []
        failed_steps = []
        
        try:
            for step in plan.steps:
                logger.info(f"Executing step: {step}")
                
                success = await self._execute_step(step)
                
                if success:
                    completed_steps.append(step)
                    logger.info(f"Step completed: {step}")
                else:
                    failed_steps.append(step)
                    logger.error(f"Step failed: {step}")
                    
                    # 檢查是否觸發回滾
                    if await self._should_rollback(phase, step):
                        raise Exception(f"Rollback triggered by step failure: {step}")
                
                # 檢查成功標準
                if not await self._check_success_criteria(phase):
                    raise Exception(f"Success criteria not met after step: {step}")
            
            # 收集指標
            metrics = await self._collect_metrics(phase)
            
            duration = datetime.utcnow() - start_time
            
            return MigrationResult(
                success=True,
                phase=phase,
                completed_steps=completed_steps,
                failed_steps=failed_steps,
                metrics=metrics,
                duration=duration
            )
            
        except Exception as e:
            duration = datetime.utcnow() - start_time
            
            return MigrationResult(
                success=False,
                phase=phase,
                completed_steps=completed_steps,
                failed_steps=failed_steps,
                error_message=str(e),
                duration=duration
            )
    
    async def _execute_step(self, step: str) -> bool:
        """執行單個遷移步驟"""
        try:
            if step == "validate_system_health":
                return await self._validate_system_health()
            elif step == "backup_current_system":
                return await self._backup_current_system()
            elif step == "verify_new_system_readiness":
                return await self._verify_new_system_readiness()
            elif step == "prepare_monitoring":
                return await self._prepare_monitoring()
            elif step == "enable_event_processor":
                return await self._enable_event_processor()
            elif step == "monitor_event_processing":
                return await self._monitor_event_processing()
            elif step == "enable_candidate_selector":
                return await self._enable_candidate_selector()
            elif step == "monitor_candidate_selection":
                return await self._monitor_candidate_selection()
            elif step == "enable_rl_engine":
                return await self._enable_rl_engine()
            elif step == "monitor_rl_decisions":
                return await self._monitor_rl_decisions()
            elif step == "enable_executor":
                return await self._enable_executor()
            elif step == "monitor_execution":
                return await self._monitor_execution()
            elif step == "enable_api_proxy":
                return await self._enable_api_proxy()
            elif step == "route_traffic_to_new_system":
                return await self._route_traffic_to_new_system()
            elif step == "monitor_full_system":
                return await self._monitor_full_system()
            elif step == "validate_integration":
                return await self._validate_integration()
            elif step == "run_comprehensive_tests":
                return await self._run_comprehensive_tests()
            elif step == "validate_business_metrics":
                return await self._validate_business_metrics()
            elif step == "verify_performance_gains":
                return await self._verify_performance_gains()
            elif step == "collect_user_feedback":
                return await self._collect_user_feedback()
            elif step == "disable_old_system":
                return await self._disable_old_system()
            elif step == "remove_old_code":
                return await self._remove_old_code()
            elif step == "update_documentation":
                return await self._update_documentation()
            elif step == "final_validation":
                return await self._final_validation()
            else:
                logger.warning(f"Unknown step: {step}")
                return False
                
        except Exception as e:
            logger.error(f"Step execution failed: {step}", error=str(e))
            return False
    
    async def _validate_system_health(self) -> bool:
        """驗證系統健康狀態"""
        try:
            health = await self.api_proxy.health_check()
            return health.get("proxy_healthy", False)
        except Exception as e:
            logger.error("System health validation failed", error=str(e))
            return False
    
    async def _backup_current_system(self) -> bool:
        """備份當前系統"""
        # 實際實現中應該備份配置、數據等
        logger.info("Backing up current system")
        return True
    
    async def _verify_new_system_readiness(self) -> bool:
        """驗證新系統就緒狀態"""
        try:
            # 檢查新系統組件
            from ..orchestrator import DecisionOrchestrator
            from ..config.di_container import create_default_container
            
            container = create_default_container(use_mocks=False)
            orchestrator = DecisionOrchestrator(container)
            
            status = orchestrator.get_service_status()
            return status.get("healthy", False)
            
        except Exception as e:
            logger.error("New system readiness check failed", error=str(e))
            return False
    
    async def _prepare_monitoring(self) -> bool:
        """準備監控"""
        # 實際實現中應該設置監控、告警等
        logger.info("Preparing monitoring systems")
        return True
    
    async def _enable_event_processor(self) -> bool:
        """啟用事件處理器"""
        return await self.feature_manager.enable_feature("use_new_event_processor", 100.0, "orchestrator")
    
    async def _monitor_event_processing(self) -> bool:
        """監控事件處理"""
        # 實際實現中應該檢查事件處理指標
        await asyncio.sleep(10)  # 模擬監控時間
        return True
    
    async def _enable_candidate_selector(self) -> bool:
        """啟用候選篩選器"""
        return await self.feature_manager.enable_feature("use_new_candidate_selector", 100.0, "orchestrator")
    
    async def _monitor_candidate_selection(self) -> bool:
        """監控候選篩選"""
        await asyncio.sleep(10)
        return True
    
    async def _enable_rl_engine(self) -> bool:
        """啟用RL引擎"""
        return await self.feature_manager.enable_feature("use_new_rl_engine", 100.0, "orchestrator")
    
    async def _monitor_rl_decisions(self) -> bool:
        """監控RL決策"""
        await asyncio.sleep(10)
        return True
    
    async def _enable_executor(self) -> bool:
        """啟用執行器"""
        return await self.feature_manager.enable_feature("use_new_executor", 100.0, "orchestrator")
    
    async def _monitor_execution(self) -> bool:
        """監控執行"""
        await asyncio.sleep(10)
        return True
    
    async def _enable_api_proxy(self) -> bool:
        """啟用API代理"""
        return await self.feature_manager.enable_feature("enable_new_api_proxy", 100.0, "orchestrator")
    
    async def _route_traffic_to_new_system(self) -> bool:
        """路由流量到新系統"""
        # 實際實現中應該配置負載均衡器等
        logger.info("Routing traffic to new system")
        return True
    
    async def _monitor_full_system(self) -> bool:
        """監控完整系統"""
        await asyncio.sleep(30)  # 更長的監控時間
        return True
    
    async def _validate_integration(self) -> bool:
        """驗證整合"""
        # 運行整合測試
        try:
            test_data = {
                "context": {
                    "system_metrics": {
                        "latency_ms": 45.0,
                        "throughput_mbps": 75.0,
                        "coverage_percentage": 82.0
                    },
                    "network_state": {"active_connections": 1000},
                    "interference_data": {},
                    "optimization_objectives": []
                }
            }
            
            # 模擬請求
            mock_request = type('MockRequest', (), {
                'headers': {},
                'client': type('MockClient', (), {'host': '127.0.0.1'})()
            })()
            
            result = await self.api_proxy.proxy_comprehensive_decision(test_data, mock_request)
            return result.get("success", False)
            
        except Exception as e:
            logger.error("Integration validation failed", error=str(e))
            return False
    
    async def _run_comprehensive_tests(self) -> bool:
        """運行綜合測試"""
        # 實際實現中應該運行完整的測試套件
        logger.info("Running comprehensive tests")
        return True
    
    async def _validate_business_metrics(self) -> bool:
        """驗證業務指標"""
        # 實際實現中應該檢查KPI等業務指標
        logger.info("Validating business metrics")
        return True
    
    async def _verify_performance_gains(self) -> bool:
        """驗證性能提升"""
        # 實際實現中應該比較性能指標
        logger.info("Verifying performance gains")
        return True
    
    async def _collect_user_feedback(self) -> bool:
        """收集用戶反饋"""
        # 實際實現中應該收集用戶反饋
        logger.info("Collecting user feedback")
        return True
    
    async def _disable_old_system(self) -> bool:
        """禁用舊系統"""
        # 實際實現中應該禁用舊系統組件
        logger.info("Disabling old system")
        return True
    
    async def _remove_old_code(self) -> bool:
        """移除舊代碼"""
        # 實際實現中應該移除舊代碼文件
        logger.info("Removing old code")
        return True
    
    async def _update_documentation(self) -> bool:
        """更新文檔"""
        # 實際實現中應該更新系統文檔
        logger.info("Updating documentation")
        return True
    
    async def _final_validation(self) -> bool:
        """最終驗證"""
        # 實際實現中應該進行最終的系統驗證
        logger.info("Performing final validation")
        return True
    
    async def _should_rollback(self, phase: MigrationPhase, step: str) -> bool:
        """檢查是否應該回滾"""
        plan = self.migration_plans[phase]
        
        # 檢查回滾觸發器
        for trigger in plan.rollback_triggers:
            if await self._check_rollback_trigger(trigger):
                logger.warning(f"Rollback trigger activated: {trigger}")
                return True
        
        return False
    
    async def _check_rollback_trigger(self, trigger: str) -> bool:
        """檢查回滾觸發器"""
        # 實際實現中應該檢查具體的觸發條件
        return False
    
    async def _check_success_criteria(self, phase: MigrationPhase) -> bool:
        """檢查成功標準"""
        plan = self.migration_plans[phase]
        
        for criterion in plan.success_criteria:
            if not await self._check_success_criterion(criterion):
                logger.warning(f"Success criterion not met: {criterion}")
                return False
        
        return True
    
    async def _check_success_criterion(self, criterion: str) -> bool:
        """檢查成功標準"""
        # 實際實現中應該檢查具體的成功標準
        return True
    
    async def _collect_metrics(self, phase: MigrationPhase) -> Dict[str, Any]:
        """收集指標"""
        metrics = {
            "phase": phase.value,
            "timestamp": datetime.utcnow().isoformat(),
            "proxy_metrics": self.api_proxy._get_metrics_summary(),
            "feature_flags": self.feature_manager.get_migration_status()["feature_flags"]
        }
        
        return metrics
    
    async def rollback_to_phase(self, target_phase: MigrationPhase):
        """回滾到指定階段"""
        logger.warning(f"Rolling back to phase: {target_phase.value}")
        
        # 回滾所有特性開關
        manager = self.feature_manager
        
        features_to_rollback = [
            "use_new_event_processor",
            "use_new_candidate_selector",
            "use_new_rl_engine", 
            "use_new_executor",
            "enable_new_api_proxy"
        ]
        
        for feature in features_to_rollback:
            await manager.rollback_feature(feature, "orchestrator_rollback")
        
        self.current_phase = target_phase
        logger.info(f"Rollback completed to phase: {target_phase.value}")
    
    def get_migration_status(self) -> Dict[str, Any]:
        """獲取遷移狀態"""
        return {
            "current_phase": self.current_phase.value,
            "migration_plans": {
                phase.value: {
                    "steps": plan.steps,
                    "success_criteria": plan.success_criteria,
                    "estimated_duration": str(plan.estimated_duration)
                }
                for phase, plan in self.migration_plans.items()
            },
            "feature_flags": self.feature_manager.get_migration_status()["feature_flags"],
            "proxy_metrics": self.api_proxy._get_metrics_summary()
        }

# 全局實例
_migration_orchestrator = None

def get_migration_orchestrator() -> MigrationOrchestrator:
    """獲取遷移協調器實例"""
    global _migration_orchestrator
    if _migration_orchestrator is None:
        _migration_orchestrator = MigrationOrchestrator()
    return _migration_orchestrator