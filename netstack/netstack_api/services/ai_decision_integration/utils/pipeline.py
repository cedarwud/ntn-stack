"""
決策管道
========

實現決策流程的管道模式，按順序處理決策階段。
"""

import asyncio
import time
from typing import List, Any, Dict, Optional, Callable
import structlog
from collections import defaultdict, deque
import uuid

logger = structlog.get_logger(__name__)


class PipelineStage:
    """管道階段基類"""

    def __init__(self, name: str, processor: Callable, timeout: float = 30.0):
        """
        初始化管道階段

        Args:
            name: 階段名稱
            processor: 處理函數
            timeout: 超時時間 (秒)
        """
        self.name = name
        self.processor = processor
        self.timeout = timeout
        self.execution_count = 0
        self.total_execution_time = 0.0
        self.error_count = 0

    async def process(self, data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        處理數據

        Args:
            data: 輸入數據
            context: 處理上下文

        Returns:
            Any: 處理結果
        """
        start_time = time.time()

        try:
            if asyncio.iscoroutinefunction(self.processor):
                result = await asyncio.wait_for(
                    self.processor(data, context or {}), timeout=self.timeout
                )
            else:
                result = self.processor(data, context or {})

            execution_time = time.time() - start_time
            self.execution_count += 1
            self.total_execution_time += execution_time

            logger.debug(
                f"Pipeline stage '{self.name}' completed", execution_time=execution_time
            )

            return result

        except asyncio.TimeoutError:
            self.error_count += 1
            logger.error(f"Pipeline stage '{self.name}' timeout", timeout=self.timeout)
            raise PipelineTimeoutError(
                f"Stage '{self.name}' timed out after {self.timeout}s"
            )

        except Exception as e:
            self.error_count += 1
            logger.error(f"Pipeline stage '{self.name}' failed", error=str(e))
            raise PipelineStageError(f"Stage '{self.name}' failed: {str(e)}")

    def get_stats(self) -> Dict[str, Any]:
        """獲取階段統計信息"""
        avg_execution_time = (
            self.total_execution_time / self.execution_count
            if self.execution_count > 0
            else 0
        )

        return {
            "name": self.name,
            "execution_count": self.execution_count,
            "error_count": self.error_count,
            "average_execution_time": avg_execution_time,
            "total_execution_time": self.total_execution_time,
            "success_rate": (
                (self.execution_count - self.error_count) / self.execution_count
                if self.execution_count > 0
                else 0
            ),
        }


"""
決策管道主類 - 階段5優化版本

按順序執行決策階段，提供完整的性能監控和錯誤處理：
- 事件處理 -> 候選篩選 -> 決策執行 -> 結果處理
- 支援並行執行和回退機制
- 完整的監控和指標收集
"""


class DecisionPipeline:
    def __init__(self, components: Optional[List[Any]] = None):
        """
        初始化決策管道 - 階段5優化版本

        Args:
            components: 管道組件列表 (可選)
        """
        self.stages: List[PipelineStage] = []
        self.is_running = False
        self.total_executions = 0
        self.total_failures = 0

        # 性能監控
        self.stage_metrics: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "total_time": 0.0,
            "execution_count": 0,
            "error_count": 0,
            "avg_time": 0.0,
            "success_rate": 0.0
        })

        # 錯誤處理
        self.error_handlers: Dict[str, Callable] = {}
        self.retry_config = {
            "max_retries": 3,
            "retry_delay": 1.0,
            "exponential_backoff": True
        }

        # 管道狀態
        self.last_execution_context: Optional[Dict[str, Any]] = None
        self.execution_history: deque = deque(maxlen=100)

        # 如果提供了組件，則從組件創建基礎階段
        if components:
            self._create_stages_from_components(components)

        logger.info("Decision pipeline initialized (Stage 5 optimized)", 
                   stages=len(self.stages))

    def _create_stages_from_components(self, components: List[Any]):
        """從組件創建管道階段 - 保留向後兼容性"""
        # 基礎階段配置
        stage_configs = [
            ("event_processing", self._process_event_stage, 10.0),
            ("candidate_selection", self._select_candidates_stage, 15.0),
            ("rl_decision", self._make_decision_stage, 20.0),
            ("execution", self._execute_stage, 30.0),
        ]

        for name, processor, timeout in stage_configs:
            stage = PipelineStage(name, processor, timeout)
            self.stages.append(stage)

    async def process(self, initial_data: Any, 
                     context: Optional[Dict[str, Any]] = None) -> Any:
        """
        處理完整的決策管道 - 階段5優化版本

        Args:
            initial_data: 初始輸入數據
            context: 處理上下文

        Returns:
            Any: 最終處理結果
        """
        start_time = time.time()
        execution_id = str(uuid.uuid4())
        context = context or {}
        context["execution_id"] = execution_id

        # 記錄執行開始
        execution_record = {
            "execution_id": execution_id,
            "start_time": start_time,
            "initial_data": initial_data,
            "context": context.copy(),
            "stages_completed": [],
            "status": "running",
        }

        try:
            self.is_running = True
            current_data = initial_data

            logger.info(
                "Starting pipeline execution (Stage 5 optimized)",
                execution_id=execution_id,
                stages=len(self.stages),
            )

            # 按順序執行所有階段
            for i, stage in enumerate(self.stages):
                stage_start_time = time.time()

                logger.debug(
                    f"Executing stage {i+1}/{len(self.stages)}: {stage.name}",
                    execution_id=execution_id,
                )

                # 更新階段上下文
                stage_context = context.copy()
                stage_context.update(
                    {
                        "stage_index": i,
                        "stage_name": stage.name,
                        "pipeline_start_time": start_time,
                        "execution_id": execution_id,
                        "previous_stages": execution_record["stages_completed"],
                    }
                )

                # 執行階段 (支援重試機制)
                try:
                    current_data = await self._execute_stage_with_retry(
                        stage, current_data, stage_context
                    )

                    # 記錄階段完成
                    stage_duration = time.time() - stage_start_time
                    execution_record["stages_completed"].append(
                        {
                            "stage_name": stage.name,
                            "duration": stage_duration,
                            "success": True,
                        }
                    )

                    # 更新階段指標
                    self._update_stage_metrics(stage.name, stage_duration, True)

                except Exception as stage_error:
                    stage_duration = time.time() - stage_start_time
                    execution_record["stages_completed"].append(
                        {
                            "stage_name": stage.name,
                            "duration": stage_duration,
                            "success": False,
                            "error": str(stage_error),
                        }
                    )

                    # 更新階段指標
                    self._update_stage_metrics(stage.name, stage_duration, False)

                    # 檢查是否有錯誤處理器
                    if stage.name in self.error_handlers:
                        logger.warning(
                            f"Stage {stage.name} failed, attempting recovery",
                            execution_id=execution_id,
                            error=str(stage_error),
                        )

                        current_data = await self.error_handlers[stage.name](
                            stage_error, current_data, stage_context
                        )
                    else:
                        raise

                # 階段間數據驗證
                if current_data is None:
                    raise PipelineDataError(f"Stage '{stage.name}' returned None")

            # 執行成功
            execution_time = time.time() - start_time
            execution_record.update(
                {
                    "status": "completed",
                    "execution_time": execution_time,
                    "success": True,
                }
            )

            self.total_executions += 1
            self.execution_history.append(execution_record)

            logger.info(
                "Pipeline execution completed (Stage 5 optimized)",
                execution_id=execution_id,
                execution_time=execution_time,
                total_executions=self.total_executions,
            )

            return current_data

        except Exception as e:
            # 執行失敗
            execution_time = time.time() - start_time
            execution_record.update(
                {
                    "status": "failed",
                    "execution_time": execution_time,
                    "error": str(e),
                    "success": False,
                }
            )

            self.total_failures += 1
            self.execution_history.append(execution_record)

            logger.error(
                "Pipeline execution failed",
                execution_id=execution_id,
                error=str(e),
                execution_time=execution_time,
                total_failures=self.total_failures,
            )
            raise PipelineError(f"Pipeline failed at stage: {execution_record['stages_completed'][-1]['stage_name'] if execution_record['stages_completed'] else 'unknown'}") from e

        finally:
            self.is_running = False
            self.last_execution_context = context

    async def _execute_stage_with_retry(self, stage: PipelineStage, 
                                       data: Any, context: Dict[str, Any]) -> Any:
        """使用重試機制執行管道階段"""
        retries = 0
        last_exception: Optional[Exception] = None
        
        while retries <= self.retry_config["max_retries"]:
            try:
                return await stage.process(data, context)
            except Exception as e:
                last_exception = e
                retries += 1

                if retries > self.retry_config["max_retries"]:
                    break

                delay = self.retry_config["retry_delay"]
                if self.retry_config["exponential_backoff"]:
                    delay *= 2 ** (retries - 1)

                logger.warning(
                    f"Stage {stage.name} failed. Retrying in {delay}s...",
                    retry_count=retries,
                    max_retries=self.retry_config["max_retries"],
                )

                await asyncio.sleep(delay)
        
        if last_exception is not None:
            raise last_exception
        
        # This part should be unreachable, but as a safeguard:
        raise PipelineError(f"Retry logic failed for stage {stage.name} without a specific exception.")

    def _update_stage_metrics(self, stage_name: str, duration: float, success: bool):
        """更新階段指標"""
        metrics = self.stage_metrics[stage_name]
        metrics["total_time"] += duration
        metrics["execution_count"] += 1

        if not success:
            metrics["error_count"] += 1

        metrics["avg_time"] = metrics["total_time"] / metrics["execution_count"]
        metrics["success_rate"] = (
            (metrics["execution_count"] - metrics["error_count"]) / metrics["execution_count"]
        )

    def add_error_handler(self, stage_name: str, handler: Callable):
        """添加錯誤處理器"""
        self.error_handlers[stage_name] = handler

    def set_retry_config(self, max_retries: int, retry_delay: float, 
                        exponential_backoff: bool = True):
        """設置重試配置"""
        self.retry_config["max_retries"] = max_retries
        self.retry_config["retry_delay"] = retry_delay
        self.retry_config["exponential_backoff"] = exponential_backoff

    def add_stage(self, stage: PipelineStage, position: Optional[int] = None):
        """
        添加一個新的階段到管道

        Args:
            stage: PipelineStage 對象
            position: 插入位置 (可選)
        """
        if position is None:
            self.stages.append(stage)
        else:
            self.stages.insert(position, stage)

    def remove_stage(self, stage_name: str) -> bool:
        """
        從管道中移除一個階段

        Args:
            stage_name: 要移除的階段名稱

        Returns:
            bool: 如果成功移除返回 True, 否則 False
        """
        initial_len = len(self.stages)
        self.stages = [s for s in self.stages if s.name != stage_name]
        return len(self.stages) < initial_len

    def get_pipeline_stats(self) -> Dict[str, Any]:
        """
        獲取管道的整體統計數據

        Returns:
            Dict[str, Any]: 統計數據字典
        """
        total_time = sum(m["total_time"] for m in self.stage_metrics.values())
        total_executions = self.total_executions
        total_failures = self.total_failures

        success_rate = (
            (total_executions - total_failures) / total_executions
            if total_executions > 0
            else 0
        )

        stage_stats = {stage.name: stage.get_stats() for stage in self.stages}
        
        return {
            "is_running": self.is_running,
            "total_executions": total_executions,
            "total_failures": total_failures,
            "success_rate": success_rate,
            "total_processing_time": total_time,
            "average_execution_time": total_time / total_executions if total_executions > 0 else 0,
            "stage_metrics": self.stage_metrics,
            "stage_details": stage_stats,
            "execution_history_count": len(self.execution_history),
        }

    def get_execution_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """獲取最近的執行歷史"""
        return list(self.execution_history)[-limit:]

    def reset_stats(self):
        """重置所有統計數據"""
        self.total_executions = 0
        self.total_failures = 0
        self.stage_metrics.clear()

        for stage in self.stages:
            stage.execution_count = 0
            stage.total_execution_time = 0
            stage.error_count = 0

        logger.info("Pipeline statistics have been reset.")

    async def validate_pipeline(self) -> Dict[str, Any]:
        """
        驗證管道配置和階段處理器

        Returns:
            Dict[str, Any]: 驗證結果
        """
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "stage_count": len(self.stages),
        }

        if not self.stages:
            validation_results["valid"] = False
            validation_results["errors"].append("Pipeline has no stages.")

        stage_names = set()
        for stage in self.stages:
            if stage.name in stage_names:
                validation_results["valid"] = False
                validation_results["errors"].append(f"Duplicate stage name found: {stage.name}")
            stage_names.add(stage.name)
            
            if not callable(stage.processor):
                validation_results["valid"] = False
                validation_results["errors"].append(f"Processor for stage '{stage.name}' is not callable.")

        return validation_results

    async def _process_event_stage(self, data: Any, context: Dict[str, Any]):
        """事件處理階段"""
        if "components" not in context or "event_processor" not in context["components"]:
            raise PipelineDataError("Event processor not found in context")
        return await context["components"]["event_processor"].process_event(data["event_type"], data["event_data"])

    async def _select_candidates_stage(self, data: Any, context: Dict[str, Any]):
        """候選篩選階段"""
        if "components" not in context or "candidate_selector" not in context["components"]:
            raise PipelineDataError("Candidate selector not found in context")
        return await context["components"]["candidate_selector"].score_candidates(
            await context["components"]["candidate_selector"].select_candidates(
                data, context.get("satellite_pool", [])
            )
        )

    async def _make_decision_stage(self, data: Any, context: Dict[str, Any]):
        """RL決策階段"""
        if "components" not in context or "decision_engine" not in context["components"]:
            raise PipelineDataError("Decision engine not found in context")
        return await context["components"]["decision_engine"].make_decision(data, context.get("network_conditions", {}))

    async def _execute_stage(self, data: Any, context: Dict[str, Any]):
        """決策執行階段"""
        if "components" not in context or "executor" not in context["components"]:
            raise PipelineDataError("Executor not found in context")
        return await context["components"]["executor"].execute_decision(data)


class PipelineError(Exception):
    """管道基礎異常"""

    pass


class PipelineTimeoutError(PipelineError):
    """管道超時異常"""

    pass


class PipelineStageError(PipelineError):
    """管道階段錯誤"""

    pass


class PipelineDataError(PipelineError):
    """管道數據錯誤"""

    pass
