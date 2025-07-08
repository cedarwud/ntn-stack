"""
決策管道
========

實現決策流程的管道模式，按順序處理決策階段。
"""

import asyncio
import time
from typing import List, Any, Dict, Optional, Callable
import structlog

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
    
    async def process(self, data: Any, context: Dict[str, Any] = None) -> Any:
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
                    self.processor(data, context or {}),
                    timeout=self.timeout
                )
            else:
                result = self.processor(data, context or {})
            
            execution_time = time.time() - start_time
            self.execution_count += 1
            self.total_execution_time += execution_time
            
            logger.debug(f"Pipeline stage '{self.name}' completed",
                        execution_time=execution_time)
            
            return result
            
        except asyncio.TimeoutError:
            self.error_count += 1
            logger.error(f"Pipeline stage '{self.name}' timeout",
                        timeout=self.timeout)
            raise PipelineTimeoutError(f"Stage '{self.name}' timed out after {self.timeout}s")
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Pipeline stage '{self.name}' failed",
                        error=str(e))
            raise PipelineStageError(f"Stage '{self.name}' failed: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取階段統計信息"""
        avg_execution_time = (self.total_execution_time / self.execution_count 
                             if self.execution_count > 0 else 0)
        
        return {
            "name": self.name,
            "execution_count": self.execution_count,
            "error_count": self.error_count,
            "average_execution_time": avg_execution_time,
            "total_execution_time": self.total_execution_time,
            "success_rate": ((self.execution_count - self.error_count) / self.execution_count 
                           if self.execution_count > 0 else 0)
        }

class DecisionPipeline:
    """
    決策管道主類
    
    按順序執行決策階段：事件處理 -> 候選篩選 -> 決策執行 -> 結果處理
    """
    
    def __init__(self, components: List[Any]):
        """
        初始化決策管道
        
        Args:
            components: 管道組件列表
        """
        self.stages: List[PipelineStage] = []
        self.is_running = False
        self.total_executions = 0
        self.total_failures = 0
        
        # 根據組件創建管道階段
        self._create_stages_from_components(components)
        
        logger.info("Decision pipeline initialized", 
                   stages=len(self.stages))
    
    def _create_stages_from_components(self, components: List[Any]):
        """從組件創建管道階段"""
        # 這裡簡化處理，實際應該根據組件類型創建相應的處理函數
        stage_configs = [
            ("event_processing", self._process_event_stage, 10.0),
            ("candidate_selection", self._select_candidates_stage, 15.0),
            ("rl_decision", self._make_decision_stage, 20.0),
            ("execution", self._execute_stage, 30.0)
        ]
        
        for name, processor, timeout in stage_configs:
            stage = PipelineStage(name, processor, timeout)
            self.stages.append(stage)
    
    async def process(self, initial_data: Any, 
                     context: Dict[str, Any] = None) -> Any:
        """
        處理完整的決策管道
        
        Args:
            initial_data: 初始輸入數據
            context: 處理上下文
            
        Returns:
            Any: 最終處理結果
        """
        start_time = time.time()
        context = context or {}
        
        try:
            self.is_running = True
            current_data = initial_data
            
            logger.info("Starting pipeline execution",
                       stages=len(self.stages))
            
            # 按順序執行所有階段
            for i, stage in enumerate(self.stages):
                logger.debug(f"Executing stage {i+1}/{len(self.stages)}: {stage.name}")
                
                # 更新上下文
                stage_context = context.copy()
                stage_context.update({
                    "stage_index": i,
                    "stage_name": stage.name,
                    "pipeline_start_time": start_time
                })
                
                # 執行階段
                current_data = await stage.process(current_data, stage_context)
                
                # 階段間數據驗證
                if current_data is None:
                    raise PipelineDataError(f"Stage '{stage.name}' returned None")
            
            execution_time = time.time() - start_time
            self.total_executions += 1
            
            logger.info("Pipeline execution completed",
                       execution_time=execution_time,
                       total_executions=self.total_executions)
            
            return current_data
            
        except Exception as e:
            self.total_failures += 1
            execution_time = time.time() - start_time
            
            logger.error("Pipeline execution failed",
                        error=str(e),
                        execution_time=execution_time,
                        total_failures=self.total_failures)
            raise
            
        finally:
            self.is_running = False
    
    async def _process_event_stage(self, data: Any, context: Dict[str, Any]):
        """事件處理階段 (占位符)"""
        # 實際實現會調用 EventProcessor
        await asyncio.sleep(0.01)  # 模擬處理時間
        return data
    
    async def _select_candidates_stage(self, data: Any, context: Dict[str, Any]):
        """候選篩選階段 (占位符)"""
        # 實際實現會調用 CandidateSelector
        await asyncio.sleep(0.02)  # 模擬處理時間
        return data
    
    async def _make_decision_stage(self, data: Any, context: Dict[str, Any]):
        """決策階段 (占位符)"""
        # 實際實現會調用 RLDecisionEngine
        await asyncio.sleep(0.05)  # 模擬處理時間
        return data
    
    async def _execute_stage(self, data: Any, context: Dict[str, Any]):
        """執行階段 (占位符)"""
        # 實際實現會調用 DecisionExecutor
        await asyncio.sleep(0.03)  # 模擬處理時間
        return data
    
    def add_stage(self, stage: PipelineStage, position: Optional[int] = None):
        """
        添加管道階段
        
        Args:
            stage: 要添加的階段
            position: 插入位置 (None表示追加到末尾)
        """
        if position is None:
            self.stages.append(stage)
        else:
            self.stages.insert(position, stage)
        
        logger.debug("Pipeline stage added",
                    stage_name=stage.name,
                    position=position or len(self.stages))
    
    def remove_stage(self, stage_name: str) -> bool:
        """
        移除管道階段
        
        Args:
            stage_name: 階段名稱
            
        Returns:
            bool: 是否成功移除
        """
        for i, stage in enumerate(self.stages):
            if stage.name == stage_name:
                del self.stages[i]
                logger.debug("Pipeline stage removed", stage_name=stage_name)
                return True
        return False
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """獲取管道統計信息"""
        stage_stats = [stage.get_stats() for stage in self.stages]
        
        return {
            "total_executions": self.total_executions,
            "total_failures": self.total_failures,
            "success_rate": ((self.total_executions - self.total_failures) / self.total_executions 
                           if self.total_executions > 0 else 0),
            "is_running": self.is_running,
            "stage_count": len(self.stages),
            "stage_stats": stage_stats
        }
    
    def reset_stats(self):
        """重置統計信息"""
        self.total_executions = 0
        self.total_failures = 0
        
        for stage in self.stages:
            stage.execution_count = 0
            stage.total_execution_time = 0.0
            stage.error_count = 0
        
        logger.info("Pipeline stats reset")

class PipelineError(Exception):
    """管道錯誤基類"""
    pass

class PipelineTimeoutError(PipelineError):
    """管道超時錯誤"""
    pass

class PipelineStageError(PipelineError):
    """管道階段錯誤"""
    pass

class PipelineDataError(PipelineError):
    """管道數據錯誤"""
    pass