"""
決策執行器實現
==============

負責執行決策，包括驗證、執行、監控和回滾功能。
"""

import time
import uuid
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import deque
from dataclasses import asdict

from ..interfaces.executor import (
    DecisionExecutorInterface,
    ExecutionResult,
    ExecutionContext,
    ExecutionStatus,
    ExecutionError,
    ExecutionTimeoutError,
    ExecutionValidationError,
)
from ..interfaces.decision_engine import Decision

logger = logging.getLogger(__name__)


class DecisionExecutor(DecisionExecutorInterface):
    """
    決策執行器實現

    提供完整的決策執行生命週期管理：
    - 決策驗證
    - 異步執行
    - 實時監控
    - 錯誤處理
    - 回滾機制
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化決策執行器

        Args:
            config: 配置參數
        """
        self.config = config or {}
        self.logger = logger.bind(component="decision_executor")

        # 執行歷史和狀態管理
        self.execution_history = deque(maxlen=1000)
        self.active_executions = {}  # execution_id -> execution_info
        self.rollback_data = {}  # execution_id -> rollback_info

        # 性能統計
        self.total_executions = 0
        self.successful_executions = 0
        self.failed_executions = 0
        self.avg_execution_time = 0.0

        # 資源使用統計
        self.resource_usage = {
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
            "active_executions": 0,
            "queue_length": 0,
        }

        # 配置參數
        self.default_timeout = self.config.get("default_timeout", 30.0)
        self.max_concurrent_executions = self.config.get("max_concurrent", 10)
        self.retry_enabled = self.config.get("retry_enabled", True)
        self.rollback_enabled = self.config.get("rollback_enabled", True)

        self.logger.info(
            "決策執行器初始化完成",
            max_concurrent=self.max_concurrent_executions,
            default_timeout=self.default_timeout,
        )

    def execute_decision(
        self, decision: Decision, context: Optional[ExecutionContext] = None
    ) -> ExecutionResult:
        """
        執行決策

        Args:
            decision: 要執行的決策
            context: 執行上下文

        Returns:
            ExecutionResult: 執行結果
        """
        # 創建執行上下文
        if context is None:
            context = ExecutionContext(
                execution_id=str(uuid.uuid4()),
                timestamp=time.time(),
                timeout_seconds=self.default_timeout,
            )

        execution_start_time = time.time()

        self.logger.info(
            "開始執行決策",
            execution_id=context.execution_id,
            decision=decision.selected_satellite,
            algorithm=decision.algorithm_used,
        )

        try:
            # 1. 檢查並發限制
            if len(self.active_executions) >= self.max_concurrent_executions:
                raise ExecutionError("達到最大並發執行數限制")

            # 2. 驗證決策
            if not self.validate_decision(decision):
                raise ExecutionValidationError(
                    f"決策驗證失敗: {decision.selected_satellite}"
                )

            # 3. 準備執行環境
            self._prepare_execution_environment(decision, context)

            # 4. 執行決策
            execution_result = self._execute_decision_impl(decision, context)

            # 5. 後處理
            execution_time = (time.time() - execution_start_time) * 1000
            self._update_statistics(True, execution_time)

            # 6. 記錄執行歷史
            self._record_execution_history(execution_result)

            self.logger.info(
                "決策執行成功",
                execution_id=context.execution_id,
                execution_time=execution_time,
            )

            return execution_result

        except ExecutionTimeoutError as e:
            execution_time = (time.time() - execution_start_time) * 1000
            self._update_statistics(False, execution_time)

            result = ExecutionResult(
                success=False,
                execution_time=execution_time,
                performance_metrics={},
                status=ExecutionStatus.TIMEOUT,
                decision=decision,
                error_message=str(e),
                execution_id=context.execution_id,
            )

            self._record_execution_history(result)
            self.logger.error(
                "決策執行超時", execution_id=context.execution_id, error=str(e)
            )
            return result

        except Exception as e:
            execution_time = (time.time() - execution_start_time) * 1000
            self._update_statistics(False, execution_time)

            result = ExecutionResult(
                success=False,
                execution_time=execution_time,
                performance_metrics={},
                status=ExecutionStatus.FAILED,
                decision=decision,
                error_message=str(e),
                execution_id=context.execution_id,
            )

            self._record_execution_history(result)
            self.logger.error(
                "決策執行失敗", execution_id=context.execution_id, error=str(e)
            )
            return result

        finally:
            # 清理執行狀態
            self._cleanup_execution(context.execution_id)

    def rollback_decision(self, execution_id: str) -> bool:
        """
        回滾決策

        Args:
            execution_id: 執行ID

        Returns:
            bool: 是否成功回滾
        """
        if not self.rollback_enabled:
            self.logger.warning("回滾功能已禁用", execution_id=execution_id)
            return False

        try:
            self.logger.info("開始回滾決策", execution_id=execution_id)

            # 檢查回滾數據
            if execution_id not in self.rollback_data:
                self.logger.error("未找到回滾數據", execution_id=execution_id)
                return False

            rollback_info = self.rollback_data[execution_id]

            # 執行回滾操作
            success = self._execute_rollback(rollback_info)

            if success:
                # 清理回滾數據
                del self.rollback_data[execution_id]
                self.logger.info("決策回滾成功", execution_id=execution_id)
            else:
                self.logger.error("決策回滾失敗", execution_id=execution_id)

            return success

        except Exception as e:
            self.logger.error("回滾操作異常", execution_id=execution_id, error=str(e))
            return False

    def monitor_execution(self, execution_id: str) -> Dict[str, Any]:
        """
        監控決策執行狀態

        Args:
            execution_id: 執行ID

        Returns:
            Dict[str, Any]: 執行狀態信息
        """
        if execution_id in self.active_executions:
            execution_info = self.active_executions[execution_id]
            current_time = time.time()
            elapsed_time = current_time - execution_info["start_time"]

            return {
                "execution_id": execution_id,
                "status": execution_info["status"],
                "elapsed_time": elapsed_time,
                "progress": execution_info.get("progress", 0.0),
                "stage": execution_info.get("current_stage", "unknown"),
                "estimated_remaining_time": execution_info.get(
                    "estimated_remaining", 0.0
                ),
                "is_active": True,
            }
        else:
            # 查找歷史記錄
            for result in self.execution_history:
                if result.execution_id == execution_id:
                    return {
                        "execution_id": execution_id,
                        "status": result.status.value,
                        "success": result.success,
                        "execution_time": result.execution_time,
                        "error_message": result.error_message,
                        "is_active": False,
                        "is_completed": True,
                    }

            return {
                "execution_id": execution_id,
                "status": "not_found",
                "is_active": False,
                "is_completed": False,
            }

    def get_execution_history(self, limit: int = 100) -> List[ExecutionResult]:
        """
        獲取執行歷史

        Args:
            limit: 返回記錄數限制

        Returns:
            List[ExecutionResult]: 執行歷史列表
        """
        return list(self.execution_history)[-limit:]

    def cancel_execution(self, execution_id: str) -> bool:
        """
        取消執行

        Args:
            execution_id: 執行ID

        Returns:
            bool: 是否成功取消
        """
        if execution_id not in self.active_executions:
            self.logger.warning("執行不存在或已完成", execution_id=execution_id)
            return False

        try:
            execution_info = self.active_executions[execution_id]
            execution_info["status"] = ExecutionStatus.CANCELLED
            execution_info["cancelled"] = True

            # 如果支持，取消實際執行
            if "cancel_function" in execution_info:
                execution_info["cancel_function"]()

            self.logger.info("執行已取消", execution_id=execution_id)
            return True

        except Exception as e:
            self.logger.error("取消執行失敗", execution_id=execution_id, error=str(e))
            return False

    def validate_decision(self, decision: Decision) -> bool:
        """
        驗證決策的可執行性

        Args:
            decision: 要驗證的決策

        Returns:
            bool: 是否可執行
        """
        try:
            # 基本驗證
            if not decision.selected_satellite:
                self.logger.warning("決策缺少目標衛星")
                return False

            if decision.confidence < 0.1:
                self.logger.warning("決策置信度過低", confidence=decision.confidence)
                return False

            # 驗證執行計劃
            execution_plan = decision.execution_plan
            if not execution_plan:
                self.logger.warning("決策缺少執行計劃")
                return False

            # 驗證換手類型
            handover_type = execution_plan.get("handover_type")
            if handover_type not in ["A4", "A3", "D1", "D2", "T1"]:
                self.logger.warning("不支持的換手類型", handover_type=handover_type)
                return False

            # 驗證時間參數
            preparation_time = execution_plan.get("preparation_time", 0)
            if preparation_time < 0:
                self.logger.warning("準備時間不能為負數")
                return False

            return True

        except Exception as e:
            self.logger.error("決策驗證異常", error=str(e))
            return False

    def estimate_execution_time(self, decision: Decision) -> float:
        """
        估計執行時間

        Args:
            decision: 決策

        Returns:
            float: 預估執行時間 (毫秒)
        """
        execution_plan = decision.execution_plan

        # 基礎時間成本
        base_time = 1000.0  # 1秒基礎時間

        # 根據換手類型調整
        handover_type = execution_plan.get("handover_type", "A4")
        type_multipliers = {
            "A4": 1.0,  # 標準換手
            "A3": 1.2,  # 跨頻段換手
            "D1": 0.8,  # 緊急換手
            "D2": 1.5,  # 複雜換手
            "T1": 1.3,  # 定時換手
        }

        base_time *= type_multipliers.get(handover_type, 1.0)

        # 根據置信度調整 (置信度低可能需要更多驗證時間)
        confidence_factor = 1.0 + (1.0 - decision.confidence) * 0.5
        base_time *= confidence_factor

        # 根據歷史平均時間調整
        if self.avg_execution_time > 0:
            historical_factor = 0.7
            base_time = (
                base_time * (1 - historical_factor)
                + self.avg_execution_time * historical_factor
            )

        return base_time

    def get_resource_usage(self) -> Dict[str, float]:
        """
        獲取資源使用情況

        Returns:
            Dict[str, float]: 資源使用統計
        """
        self.resource_usage.update(
            {
                "active_executions": len(self.active_executions),
                "total_executions": self.total_executions,
                "success_rate": (
                    self.successful_executions / self.total_executions
                    if self.total_executions > 0
                    else 0.0
                ),
                "avg_execution_time": self.avg_execution_time,
            }
        )

        return self.resource_usage.copy()

    # 私有方法實現
    def _prepare_execution_environment(
        self, decision: Decision, context: ExecutionContext
    ):
        """準備執行環境"""
        execution_info = {
            "execution_id": context.execution_id,
            "decision": decision,
            "context": context,
            "start_time": time.time(),
            "status": ExecutionStatus.RUNNING,
            "progress": 0.0,
            "current_stage": "preparation",
        }

        self.active_executions[context.execution_id] = execution_info

        # 準備回滾數據
        if self.rollback_enabled:
            self.rollback_data[context.execution_id] = {
                "original_state": self._capture_current_state(decision),
                "rollback_plan": self._create_rollback_plan(decision),
                "timestamp": time.time(),
            }

    def _execute_decision_impl(
        self, decision: Decision, context: ExecutionContext
    ) -> ExecutionResult:
        """實際執行決策的核心邏輯"""
        execution_info = self.active_executions[context.execution_id]
        start_time = time.time()

        try:
            # 階段1: 準備階段
            execution_info["current_stage"] = "preparation"
            execution_info["progress"] = 0.1
            self._execute_preparation_phase(decision, context)

            # 階段2: 換手執行
            execution_info["current_stage"] = "handover_execution"
            execution_info["progress"] = 0.4
            handover_result = self._execute_handover_phase(decision, context)

            # 階段3: 驗證階段
            execution_info["current_stage"] = "verification"
            execution_info["progress"] = 0.8
            verification_result = self._execute_verification_phase(
                decision, context, handover_result
            )

            # 階段4: 完成階段
            execution_info["current_stage"] = "completion"
            execution_info["progress"] = 1.0
            performance_metrics = self._calculate_performance_metrics(
                decision, handover_result, verification_result
            )

            execution_time = (time.time() - start_time) * 1000

            return ExecutionResult(
                success=True,
                execution_time=execution_time,
                performance_metrics=performance_metrics,
                status=ExecutionStatus.SUCCESS,
                decision=decision,
                execution_id=context.execution_id,
                rollback_data=self.rollback_data.get(context.execution_id),
            )

        except asyncio.TimeoutError:
            raise ExecutionTimeoutError(f"執行超時: {context.timeout_seconds}秒")
        except Exception as e:
            raise ExecutionError(f"執行失敗: {str(e)}")

    def _execute_preparation_phase(self, decision: Decision, context: ExecutionContext):
        """執行準備階段"""
        # 模擬準備工作
        time.sleep(0.1)  # 100ms準備時間

        # 檢查目標衛星可用性
        target_satellite = decision.selected_satellite
        if not self._check_satellite_availability(target_satellite):
            raise ExecutionError(f"目標衛星不可用: {target_satellite}")

        # 預留資源
        self._reserve_resources(decision)

    def _execute_handover_phase(
        self, decision: Decision, context: ExecutionContext
    ) -> Dict[str, Any]:
        """執行換手階段"""
        handover_type = decision.execution_plan.get("handover_type", "A4")

        # 模擬換手執行
        execution_time = decision.execution_plan.get("execution_time", 2000) / 1000.0
        time.sleep(min(execution_time, 1.0))  # 最多睡眠1秒

        # 模擬換手結果
        handover_result = {
            "handover_type": handover_type,
            "target_satellite": decision.selected_satellite,
            "success": True,
            "signal_quality": 0.85,
            "handover_time": execution_time * 1000,
            "packet_loss": 0.02,
        }

        return handover_result

    def _execute_verification_phase(
        self,
        decision: Decision,
        context: ExecutionContext,
        handover_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """執行驗證階段"""
        # 模擬驗證工作
        time.sleep(0.05)  # 50ms驗證時間

        # 驗證連接質量
        signal_quality = handover_result.get("signal_quality", 0.0)
        if signal_quality < 0.5:
            raise ExecutionError("換手後信號質量不達標")

        verification_result = {
            "connection_verified": True,
            "signal_quality": signal_quality,
            "latency": 20.0,  # ms
            "throughput": 150.0,  # Mbps
            "verification_time": 50.0,  # ms
        }

        return verification_result

    def _calculate_performance_metrics(
        self,
        decision: Decision,
        handover_result: Dict[str, Any],
        verification_result: Dict[str, Any],
    ) -> Dict[str, float]:
        """計算性能指標"""
        return {
            "handover_success_rate": 1.0 if handover_result.get("success") else 0.0,
            "signal_quality": verification_result.get("signal_quality", 0.0),
            "latency": verification_result.get("latency", 0.0),
            "throughput": verification_result.get("throughput", 0.0),
            "packet_loss_rate": handover_result.get("packet_loss", 0.0),
            "total_handover_time": handover_result.get("handover_time", 0.0),
            "verification_time": verification_result.get("verification_time", 0.0),
        }

    def _check_satellite_availability(self, satellite_id: str) -> bool:
        """檢查衛星可用性"""
        # 簡化實現 - 實際應該檢查衛星狀態
        return satellite_id != "UNAVAILABLE"

    def _reserve_resources(self, decision: Decision):
        """預留資源"""
        # 簡化實現 - 實際應該預留網路資源
        pass

    def _capture_current_state(self, decision: Decision) -> Dict[str, Any]:
        """捕獲當前狀態用於回滾"""
        return {
            "current_satellite": "previous_satellite",  # 實際應該獲取當前衛星
            "network_config": {},
            "timestamp": time.time(),
        }

    def _create_rollback_plan(self, decision: Decision) -> Dict[str, Any]:
        """創建回滾計劃"""
        return {
            "rollback_type": "revert_handover",
            "target_satellite": "previous_satellite",
            "estimated_time": 1000.0,  # ms
        }

    def _execute_rollback(self, rollback_info: Dict[str, Any]) -> bool:
        """執行回滾操作"""
        try:
            # 模擬回滾操作
            time.sleep(0.5)  # 500ms回滾時間
            return True
        except Exception as e:
            self.logger.error("回滾執行失敗", error=str(e))
            return False

    def _cleanup_execution(self, execution_id: str):
        """清理執行狀態"""
        if execution_id in self.active_executions:
            del self.active_executions[execution_id]

    def _update_statistics(self, success: bool, execution_time: float):
        """更新統計信息"""
        self.total_executions += 1

        if success:
            self.successful_executions += 1
        else:
            self.failed_executions += 1

        # 更新平均執行時間
        current_avg = self.avg_execution_time
        self.avg_execution_time = (
            current_avg * (self.total_executions - 1) + execution_time
        ) / self.total_executions

    def _record_execution_history(self, result: ExecutionResult):
        """記錄執行歷史"""
        self.execution_history.append(result)
