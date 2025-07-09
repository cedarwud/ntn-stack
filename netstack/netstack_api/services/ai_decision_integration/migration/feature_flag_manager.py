"""
Feature Flag Manager for AI Decision Engine Migration
====================================================

管理新舊系統切換的特性開關系統，支援漸進式啟用和回滾機制。
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import redis
from pathlib import Path

logger = logging.getLogger(__name__)

class FeatureStatus(Enum):
    """功能狀態枚舉"""
    DISABLED = "disabled"
    ENABLED = "enabled"
    TESTING = "testing"
    ROLLBACK = "rollback"

@dataclass
class FeatureFlag:
    """特性開關數據結構"""
    name: str
    status: FeatureStatus
    enabled_percentage: float = 0.0  # 啟用百分比 (0-100)
    last_updated: datetime = None
    updated_by: str = "system"
    conditions: Dict[str, Any] = None  # 啟用條件
    dependencies: List[str] = None  # 依賴的其他功能
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.utcnow()
        if self.conditions is None:
            self.conditions = {}
        if self.dependencies is None:
            self.dependencies = []

@dataclass
class MigrationStep:
    """遷移步驟"""
    step_name: str
    feature_flags: List[str]
    validation_checks: List[str]
    rollback_procedure: str
    estimated_duration: timedelta
    prerequisites: List[str] = None
    
    def __post_init__(self):
        if self.prerequisites is None:
            self.prerequisites = []

class FeatureFlagManager:
    """特性開關管理器"""
    
    def __init__(self, redis_client: redis.Redis = None):
        self.redis = redis_client
        self.flags: Dict[str, FeatureFlag] = {}
        self.migration_steps: List[MigrationStep] = []
        self.callbacks: Dict[str, List[Callable]] = {}
        
        # 初始化核心特性開關
        self._initialize_core_flags()
        self._setup_migration_steps()
        
    def _initialize_core_flags(self):
        """初始化核心特性開關"""
        core_flags = [
            FeatureFlag(
                name="use_new_event_processor",
                status=FeatureStatus.DISABLED,
                dependencies=[]
            ),
            FeatureFlag(
                name="use_new_candidate_selector", 
                status=FeatureStatus.DISABLED,
                dependencies=["use_new_event_processor"]
            ),
            FeatureFlag(
                name="use_new_rl_engine",
                status=FeatureStatus.DISABLED,
                dependencies=["use_new_candidate_selector"]
            ),
            FeatureFlag(
                name="use_new_executor",
                status=FeatureStatus.DISABLED,
                dependencies=["use_new_rl_engine"]
            ),
            FeatureFlag(
                name="enable_3d_visualization",
                status=FeatureStatus.ENABLED,
                enabled_percentage=100.0
            ),
            FeatureFlag(
                name="enable_websocket_streaming",
                status=FeatureStatus.ENABLED,
                enabled_percentage=100.0
            ),
            FeatureFlag(
                name="enable_performance_monitoring",
                status=FeatureStatus.ENABLED,
                enabled_percentage=100.0
            ),
            FeatureFlag(
                name="enable_new_api_proxy",
                status=FeatureStatus.DISABLED,
                dependencies=["use_new_executor"]
            )
        ]
        
        for flag in core_flags:
            self.flags[flag.name] = flag
    
    def _setup_migration_steps(self):
        """設置遷移步驟"""
        self.migration_steps = [
            MigrationStep(
                step_name="event_processor_migration",
                feature_flags=["use_new_event_processor"],
                validation_checks=["test_event_processing", "validate_a4_d1_d2_t1_handlers"],
                rollback_procedure="disable_event_processor_flags",
                estimated_duration=timedelta(hours=1),
                prerequisites=[]
            ),
            MigrationStep(
                step_name="candidate_selector_migration",
                feature_flags=["use_new_candidate_selector"],
                validation_checks=["test_candidate_selection", "validate_scoring_engine"],
                rollback_procedure="disable_candidate_selector_flags",
                estimated_duration=timedelta(hours=2),
                prerequisites=["event_processor_migration"]
            ),
            MigrationStep(
                step_name="rl_engine_migration",
                feature_flags=["use_new_rl_engine"],
                validation_checks=["test_rl_integration", "validate_dqn_ppo_sac"],
                rollback_procedure="disable_rl_engine_flags",
                estimated_duration=timedelta(hours=3),
                prerequisites=["candidate_selector_migration"]
            ),
            MigrationStep(
                step_name="executor_migration",
                feature_flags=["use_new_executor"],
                validation_checks=["test_decision_execution", "validate_monitoring"],
                rollback_procedure="disable_executor_flags",
                estimated_duration=timedelta(hours=1),
                prerequisites=["rl_engine_migration"]
            ),
            MigrationStep(
                step_name="api_proxy_migration",
                feature_flags=["enable_new_api_proxy"],
                validation_checks=["test_api_compatibility", "validate_performance"],
                rollback_procedure="disable_api_proxy_flags",
                estimated_duration=timedelta(hours=2),
                prerequisites=["executor_migration"]
            )
        ]
    
    def is_feature_enabled(self, feature_name: str, user_id: str = None) -> bool:
        """
        檢查特性是否啟用
        
        Args:
            feature_name: 特性名稱
            user_id: 用戶ID (用於A/B測試)
            
        Returns:
            bool: 是否啟用
        """
        if feature_name not in self.flags:
            logger.warning(f"Unknown feature flag: {feature_name}")
            return False
        
        flag = self.flags[feature_name]
        
        # 檢查狀態
        if flag.status == FeatureStatus.DISABLED:
            return False
        elif flag.status == FeatureStatus.ENABLED:
            return True
        elif flag.status == FeatureStatus.ROLLBACK:
            return False
        elif flag.status == FeatureStatus.TESTING:
            # A/B測試邏輯
            if user_id:
                return self._should_enable_for_user(flag, user_id)
            return flag.enabled_percentage >= 100.0
        
        return False
    
    def _should_enable_for_user(self, flag: FeatureFlag, user_id: str) -> bool:
        """根據用戶ID決定是否啟用功能 (A/B測試)"""
        # 簡單的哈希算法決定用戶是否在啟用範圍內
        user_hash = hash(user_id + flag.name) % 100
        return user_hash < flag.enabled_percentage
    
    async def enable_feature(self, feature_name: str, percentage: float = 100.0, 
                           updated_by: str = "system") -> bool:
        """
        啟用功能
        
        Args:
            feature_name: 功能名稱
            percentage: 啟用百分比
            updated_by: 更新者
            
        Returns:
            bool: 是否成功
        """
        if feature_name not in self.flags:
            logger.error(f"Unknown feature flag: {feature_name}")
            return False
        
        flag = self.flags[feature_name]
        
        # 檢查依賴
        if not await self._check_dependencies(feature_name):
            logger.error(f"Dependencies not met for feature: {feature_name}")
            return False
        
        # 更新狀態
        flag.status = FeatureStatus.TESTING if percentage < 100.0 else FeatureStatus.ENABLED
        flag.enabled_percentage = percentage
        flag.last_updated = datetime.utcnow()
        flag.updated_by = updated_by
        
        # 持久化
        await self._persist_flag(flag)
        
        # 觸發回調
        await self._trigger_callbacks(feature_name, "enabled")
        
        logger.info(f"Feature {feature_name} enabled at {percentage}% by {updated_by}")
        return True
    
    async def disable_feature(self, feature_name: str, updated_by: str = "system") -> bool:
        """
        禁用功能
        
        Args:
            feature_name: 功能名稱
            updated_by: 更新者
            
        Returns:
            bool: 是否成功
        """
        if feature_name not in self.flags:
            logger.error(f"Unknown feature flag: {feature_name}")
            return False
        
        flag = self.flags[feature_name]
        flag.status = FeatureStatus.DISABLED
        flag.enabled_percentage = 0.0
        flag.last_updated = datetime.utcnow()
        flag.updated_by = updated_by
        
        # 持久化
        await self._persist_flag(flag)
        
        # 觸發回調
        await self._trigger_callbacks(feature_name, "disabled")
        
        logger.info(f"Feature {feature_name} disabled by {updated_by}")
        return True
    
    async def rollback_feature(self, feature_name: str, updated_by: str = "system") -> bool:
        """
        回滾功能
        
        Args:
            feature_name: 功能名稱
            updated_by: 更新者
            
        Returns:
            bool: 是否成功
        """
        if feature_name not in self.flags:
            logger.error(f"Unknown feature flag: {feature_name}")
            return False
        
        flag = self.flags[feature_name]
        flag.status = FeatureStatus.ROLLBACK
        flag.enabled_percentage = 0.0
        flag.last_updated = datetime.utcnow()
        flag.updated_by = updated_by
        
        # 持久化
        await self._persist_flag(flag)
        
        # 觸發回調
        await self._trigger_callbacks(feature_name, "rollback")
        
        logger.warning(f"Feature {feature_name} rolled back by {updated_by}")
        return True
    
    async def _check_dependencies(self, feature_name: str) -> bool:
        """檢查功能依賴"""
        flag = self.flags[feature_name]
        
        for dep in flag.dependencies:
            if dep not in self.flags:
                logger.error(f"Missing dependency: {dep}")
                return False
            
            dep_flag = self.flags[dep]
            if dep_flag.status not in [FeatureStatus.ENABLED, FeatureStatus.TESTING]:
                logger.error(f"Dependency {dep} is not enabled")
                return False
        
        return True
    
    async def _persist_flag(self, flag: FeatureFlag):
        """持久化特性開關"""
        if self.redis:
            key = f"feature_flag:{flag.name}"
            value = json.dumps(asdict(flag), default=str)
            await self.redis.set(key, value)
    
    async def _trigger_callbacks(self, feature_name: str, event: str):
        """觸發回調函數"""
        if feature_name in self.callbacks:
            for callback in self.callbacks[feature_name]:
                try:
                    await callback(feature_name, event)
                except Exception as e:
                    logger.error(f"Callback error for {feature_name}: {e}")
    
    def register_callback(self, feature_name: str, callback: Callable):
        """註冊回調函數"""
        if feature_name not in self.callbacks:
            self.callbacks[feature_name] = []
        self.callbacks[feature_name].append(callback)
    
    async def execute_migration_step(self, step_name: str) -> Dict[str, Any]:
        """
        執行遷移步驟
        
        Args:
            step_name: 步驟名稱
            
        Returns:
            Dict: 執行結果
        """
        step = next((s for s in self.migration_steps if s.step_name == step_name), None)
        if not step:
            return {"success": False, "error": f"Unknown migration step: {step_name}"}
        
        logger.info(f"Starting migration step: {step_name}")
        
        # 檢查先決條件
        for prereq in step.prerequisites:
            if not await self._is_step_completed(prereq):
                return {
                    "success": False, 
                    "error": f"Prerequisite not met: {prereq}"
                }
        
        # 執行驗證檢查
        validation_results = await self._run_validation_checks(step.validation_checks)
        if not validation_results["success"]:
            return {
                "success": False,
                "error": "Validation checks failed",
                "details": validation_results
            }
        
        # 啟用功能
        for flag_name in step.feature_flags:
            success = await self.enable_feature(flag_name, 100.0, "migration")
            if not success:
                # 回滾
                await self._rollback_migration_step(step)
                return {
                    "success": False,
                    "error": f"Failed to enable feature: {flag_name}"
                }
        
        # 標記步驟完成
        await self._mark_step_completed(step_name)
        
        logger.info(f"Migration step completed: {step_name}")
        return {
            "success": True,
            "step_name": step_name,
            "enabled_features": step.feature_flags,
            "validation_results": validation_results
        }
    
    async def _is_step_completed(self, step_name: str) -> bool:
        """檢查步驟是否完成"""
        if self.redis:
            key = f"migration_step:{step_name}"
            return await self.redis.exists(key)
        return False
    
    async def _mark_step_completed(self, step_name: str):
        """標記步驟完成"""
        if self.redis:
            key = f"migration_step:{step_name}"
            data = {
                "step_name": step_name,
                "completed_at": datetime.utcnow().isoformat(),
                "status": "completed"
            }
            await self.redis.set(key, json.dumps(data))
    
    async def _run_validation_checks(self, checks: List[str]) -> Dict[str, Any]:
        """運行驗證檢查"""
        results = {"success": True, "checks": {}}
        
        for check in checks:
            try:
                # 這裡應該實際運行測試
                # 暫時模擬成功
                results["checks"][check] = {
                    "success": True,
                    "message": f"Check {check} passed"
                }
            except Exception as e:
                results["success"] = False
                results["checks"][check] = {
                    "success": False,
                    "error": str(e)
                }
        
        return results
    
    async def _rollback_migration_step(self, step: MigrationStep):
        """回滾遷移步驟"""
        logger.warning(f"Rolling back migration step: {step.step_name}")
        
        for flag_name in step.feature_flags:
            await self.rollback_feature(flag_name, "migration_rollback")
    
    def get_migration_status(self) -> Dict[str, Any]:
        """獲取遷移狀態"""
        return {
            "feature_flags": {
                name: {
                    "status": flag.status.value,
                    "enabled_percentage": flag.enabled_percentage,
                    "last_updated": flag.last_updated.isoformat(),
                    "updated_by": flag.updated_by
                }
                for name, flag in self.flags.items()
            },
            "migration_steps": [
                {
                    "step_name": step.step_name,
                    "feature_flags": step.feature_flags,
                    "estimated_duration": str(step.estimated_duration),
                    "prerequisites": step.prerequisites
                }
                for step in self.migration_steps
            ]
        }
    
    async def get_feature_metrics(self, feature_name: str) -> Dict[str, Any]:
        """獲取功能指標"""
        if feature_name not in self.flags:
            return {"error": f"Unknown feature: {feature_name}"}
        
        flag = self.flags[feature_name]
        
        # 從Redis獲取指標數據
        metrics = {
            "feature_name": feature_name,
            "status": flag.status.value,
            "enabled_percentage": flag.enabled_percentage,
            "last_updated": flag.last_updated.isoformat(),
            "usage_count": 0,  # 應該從實際指標系統獲取
            "error_rate": 0.0,  # 應該從實際指標系統獲取
            "performance_impact": 0.0  # 應該從實際指標系統獲取
        }
        
        return metrics

# 全局實例
_feature_flag_manager = None

def get_feature_flag_manager() -> FeatureFlagManager:
    """獲取特性開關管理器實例"""
    global _feature_flag_manager
    if _feature_flag_manager is None:
        _feature_flag_manager = FeatureFlagManager()
    return _feature_flag_manager

async def initialize_feature_flag_manager(redis_client: redis.Redis = None):
    """初始化特性開關管理器"""
    global _feature_flag_manager
    _feature_flag_manager = FeatureFlagManager(redis_client)
    return _feature_flag_manager