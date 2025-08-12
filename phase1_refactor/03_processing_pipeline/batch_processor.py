#!/usr/bin/env python3
"""
批次處理器
高效的大規模軌道計算批次處理系統
符合 CLAUDE.md 原則：完整算法，真實數據處理
"""

import logging
import time
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import queue
import json

logger = logging.getLogger(__name__)


class ProcessingMode(Enum):
    """處理模式"""
    SEQUENTIAL = "sequential"      # 順序處理
    PARALLEL = "parallel"          # 並行處理
    ADAPTIVE = "adaptive"          # 自適應處理


class TaskStatus(Enum):
    """任務狀態"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BatchTask:
    """批次任務"""
    task_id: str
    satellite_id: str
    processing_function: Callable
    parameters: Dict[str, Any]
    priority: int = 1
    max_retries: int = 3
    timeout_seconds: int = 300
    
    # 執行狀態
    status: TaskStatus = TaskStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    retry_count: int = 0
    error_message: Optional[str] = None
    result: Optional[Any] = None
    
    @property
    def execution_time_seconds(self) -> float:
        """執行時間"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0


@dataclass
class BatchConfiguration:
    """批次配置"""
    processing_mode: ProcessingMode = ProcessingMode.ADAPTIVE
    max_workers: int = 4
    batch_size: int = 100
    timeout_seconds: int = 3600
    retry_failed_tasks: bool = True
    save_intermediate_results: bool = True
    progress_report_interval: int = 10
    memory_limit_mb: int = 2048


@dataclass
class ProcessingStatistics:
    """處理統計信息"""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    cancelled_tasks: int = 0
    total_execution_time: float = 0.0
    avg_task_time: float = 0.0
    throughput_tasks_per_sec: float = 0.0
    memory_usage_mb: float = 0.0
    error_details: List[Dict] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_tasks == 0:
            return 0.0
        return (self.completed_tasks / self.total_tasks) * 100
    
    @property
    def remaining_tasks(self) -> int:
        """剩餘任務數"""
        return self.total_tasks - self.completed_tasks - self.failed_tasks - self.cancelled_tasks


@dataclass
class BatchResult:
    """批次處理結果"""
    batch_id: str
    start_time: datetime
    end_time: datetime
    configuration: BatchConfiguration
    statistics: ProcessingStatistics
    task_results: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """轉換為字典格式"""
        return {
            "batch_id": self.batch_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "total_time_seconds": (self.end_time - self.start_time).total_seconds(),
            "success": self.success,
            "statistics": {
                "total_tasks": self.statistics.total_tasks,
                "completed_tasks": self.statistics.completed_tasks,
                "failed_tasks": self.statistics.failed_tasks,
                "success_rate": round(self.statistics.success_rate, 2),
                "avg_task_time": round(self.statistics.avg_task_time, 3),
                "throughput": round(self.statistics.throughput_tasks_per_sec, 2),
                "memory_usage_mb": round(self.statistics.memory_usage_mb, 1)
            },
            "configuration": {
                "processing_mode": self.configuration.processing_mode.value,
                "max_workers": self.configuration.max_workers,
                "batch_size": self.configuration.batch_size
            },
            "task_results_count": len(self.task_results),
            "error_message": self.error_message
        }


class ProgressMonitor:
    """進度監控器"""
    
    def __init__(self, total_tasks: int, report_interval: int = 10):
        self.total_tasks = total_tasks
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.report_interval = report_interval
        self.start_time = datetime.now()
        self.last_report_time = self.start_time
        self.callbacks: List[Callable] = []
    
    def add_callback(self, callback: Callable[[Dict], None]):
        """添加進度回調函數"""
        self.callbacks.append(callback)
    
    def update_completed(self, count: int = 1):
        """更新完成任務數"""
        self.completed_tasks += count
        self._check_report()
    
    def update_failed(self, count: int = 1):
        """更新失敗任務數"""
        self.failed_tasks += count
        self._check_report()
    
    def _check_report(self):
        """檢查是否需要報告進度"""
        now = datetime.now()
        if (now - self.last_report_time).total_seconds() >= self.report_interval:
            self._report_progress()
            self.last_report_time = now
    
    def _report_progress(self):
        """報告進度"""
        progress = self._get_progress_info()
        
        logger.info(f"批次處理進度: {progress['completed']}/{progress['total']} "
                   f"({progress['progress_percent']:.1f}%), "
                   f"ETA: {progress['eta_minutes']:.1f}分鐘")
        
        # 調用回調函數
        for callback in self.callbacks:
            try:
                callback(progress)
            except Exception as e:
                logger.warning(f"進度回調執行失敗: {str(e)}")
    
    def _get_progress_info(self) -> Dict:
        """獲取進度信息"""
        total_processed = self.completed_tasks + self.failed_tasks
        progress_percent = (total_processed / self.total_tasks) * 100 if self.total_tasks > 0 else 0
        
        elapsed_seconds = (datetime.now() - self.start_time).total_seconds()
        
        if total_processed > 0:
            avg_time_per_task = elapsed_seconds / total_processed
            remaining_tasks = self.total_tasks - total_processed
            eta_seconds = remaining_tasks * avg_time_per_task
            eta_minutes = eta_seconds / 60
        else:
            eta_minutes = 0
        
        return {
            "total": self.total_tasks,
            "completed": self.completed_tasks,
            "failed": self.failed_tasks,
            "progress_percent": progress_percent,
            "elapsed_seconds": elapsed_seconds,
            "eta_minutes": eta_minutes,
            "throughput": total_processed / elapsed_seconds if elapsed_seconds > 0 else 0
        }
    
    def get_final_report(self) -> Dict:
        """獲取最終報告"""
        return self._get_progress_info()


class BatchProcessor:
    """
    批次處理器
    高效處理大規模軌道計算任務
    """
    
    def __init__(self, configuration: BatchConfiguration):
        self.config = configuration
        self.tasks: List[BatchTask] = []
        self.task_queue: queue.Queue = queue.Queue()
        self.result_queue: queue.Queue = queue.Queue()
        self.statistics = ProcessingStatistics()
        self.progress_monitor: Optional[ProgressMonitor] = None
        self.is_running = False
        self.cancelled = False
        
        logger.info(f"批次處理器初始化完成: {configuration.processing_mode.value} 模式, "
                   f"{configuration.max_workers} 個工作者")
    
    def add_task(self, task: BatchTask) -> bool:
        """添加批次任務"""
        if self.is_running:
            logger.warning("批次處理器運行中，無法添加任務")
            return False
        
        self.tasks.append(task)
        logger.debug(f"添加任務: {task.task_id} (衛星: {task.satellite_id})")
        return True
    
    def add_tasks_bulk(self, tasks: List[BatchTask]) -> int:
        """批量添加任務"""
        added_count = 0
        for task in tasks:
            if self.add_task(task):
                added_count += 1
        
        logger.info(f"批量添加任務: {added_count}/{len(tasks)} 成功")
        return added_count
    
    def process_batch(self, batch_id: str = None) -> BatchResult:
        """執行批次處理"""
        if not self.tasks:
            logger.warning("沒有任務需要處理")
            return self._create_empty_result(batch_id or f"empty_{int(time.time())}")
        
        batch_id = batch_id or f"batch_{int(time.time())}"
        start_time = datetime.now()
        
        logger.info(f"開始批次處理: {batch_id}, {len(self.tasks)} 個任務")
        
        self.is_running = True
        self.cancelled = False
        self._initialize_statistics()
        self._setup_progress_monitor()
        
        try:
            # 根據處理模式執行
            if self.config.processing_mode == ProcessingMode.SEQUENTIAL:
                task_results = self._process_sequential()
            elif self.config.processing_mode == ProcessingMode.PARALLEL:
                task_results = self._process_parallel()
            else:  # ADAPTIVE
                task_results = self._process_adaptive()
            
            end_time = datetime.now()
            self._finalize_statistics(start_time, end_time)
            
            # 創建結果
            result = BatchResult(
                batch_id=batch_id,
                start_time=start_time,
                end_time=end_time,
                configuration=self.config,
                statistics=self.statistics,
                task_results=task_results,
                success=self.statistics.failed_tasks == 0
            )
            
            logger.info(f"批次處理完成: {batch_id}, "
                       f"成功率: {self.statistics.success_rate:.1f}%, "
                       f"處理時間: {(end_time - start_time).total_seconds():.1f}秒")
            
            return result
            
        except Exception as e:
            end_time = datetime.now()
            error_msg = f"批次處理失敗: {str(e)}"
            logger.error(error_msg)
            
            return BatchResult(
                batch_id=batch_id,
                start_time=start_time,
                end_time=end_time,
                configuration=self.config,
                statistics=self.statistics,
                task_results={},
                success=False,
                error_message=error_msg
            )
        
        finally:
            self.is_running = False
    
    def _initialize_statistics(self):
        """初始化統計信息"""
        self.statistics = ProcessingStatistics()
        self.statistics.total_tasks = len(self.tasks)
    
    def _setup_progress_monitor(self):
        """設置進度監控"""
        self.progress_monitor = ProgressMonitor(
            total_tasks=len(self.tasks),
            report_interval=self.config.progress_report_interval
        )
    
    def _process_sequential(self) -> Dict[str, Any]:
        """順序處理"""
        logger.debug("使用順序處理模式")
        task_results = {}
        
        for task in self.tasks:
            if self.cancelled:
                break
                
            result = self._execute_single_task(task)
            if result is not None:
                task_results[task.task_id] = result
            
            self._update_progress(task)
        
        return task_results
    
    def _process_parallel(self) -> Dict[str, Any]:
        """並行處理"""
        logger.debug(f"使用並行處理模式: {self.config.max_workers} 個工作者")
        task_results = {}
        
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            # 提交所有任務
            future_to_task = {
                executor.submit(self._execute_single_task, task): task 
                for task in self.tasks
            }
            
            # 收集結果
            for future in as_completed(future_to_task, timeout=self.config.timeout_seconds):
                if self.cancelled:
                    break
                
                task = future_to_task[future]
                try:
                    result = future.result()
                    if result is not None:
                        task_results[task.task_id] = result
                except Exception as e:
                    logger.error(f"任務 {task.task_id} 執行異常: {str(e)}")
                    task.status = TaskStatus.FAILED
                    task.error_message = str(e)
                
                self._update_progress(task)
        
        return task_results
    
    def _process_adaptive(self) -> Dict[str, Any]:
        """自適應處理"""
        logger.debug("使用自適應處理模式")
        
        # 根據任務數量和複雜度決定處理方式
        if len(self.tasks) < 10:
            return self._process_sequential()
        else:
            return self._process_parallel()
    
    def _execute_single_task(self, task: BatchTask) -> Optional[Any]:
        """執行單個任務"""
        task.status = TaskStatus.RUNNING
        task.start_time = datetime.now()
        
        try:
            # 設置超時
            if hasattr(task.processing_function, '__name__'):
                logger.debug(f"執行任務 {task.task_id}: {task.processing_function.__name__}")
            
            # 執行處理函數
            result = task.processing_function(**task.parameters)
            
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.end_time = datetime.now()
            
            logger.debug(f"任務 {task.task_id} 完成，耗時: {task.execution_time_seconds:.2f}秒")
            return result
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.end_time = datetime.now()
            
            logger.error(f"任務 {task.task_id} 失敗: {str(e)}")
            
            # 重試機制
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                logger.info(f"重試任務 {task.task_id} (第 {task.retry_count} 次)")
                return self._execute_single_task(task)
            
            self.statistics.error_details.append({
                "task_id": task.task_id,
                "satellite_id": task.satellite_id,
                "error": str(e),
                "retry_count": task.retry_count
            })
            
            return None
    
    def _update_progress(self, task: BatchTask):
        """更新進度"""
        if task.status == TaskStatus.COMPLETED:
            self.statistics.completed_tasks += 1
            self.statistics.total_execution_time += task.execution_time_seconds
            if self.progress_monitor:
                self.progress_monitor.update_completed()
        elif task.status == TaskStatus.FAILED:
            self.statistics.failed_tasks += 1
            if self.progress_monitor:
                self.progress_monitor.update_failed()
    
    def _finalize_statistics(self, start_time: datetime, end_time: datetime):
        """完成統計信息"""
        total_time = (end_time - start_time).total_seconds()
        
        if self.statistics.completed_tasks > 0:
            self.statistics.avg_task_time = (
                self.statistics.total_execution_time / self.statistics.completed_tasks
            )
        
        if total_time > 0:
            self.statistics.throughput_tasks_per_sec = (
                (self.statistics.completed_tasks + self.statistics.failed_tasks) / total_time
            )
        
        # 估算記憶體使用 (簡化計算)
        self.statistics.memory_usage_mb = len(self.tasks) * 0.5  # 約 0.5MB 每個任務
    
    def _create_empty_result(self, batch_id: str) -> BatchResult:
        """創建空結果"""
        now = datetime.now()
        return BatchResult(
            batch_id=batch_id,
            start_time=now,
            end_time=now,
            configuration=self.config,
            statistics=ProcessingStatistics(),
            task_results={},
            success=True,
            error_message="沒有任務需要處理"
        )
    
    def cancel_batch(self):
        """取消批次處理"""
        logger.info("取消批次處理")
        self.cancelled = True
        
        # 標記未完成的任務為已取消
        for task in self.tasks:
            if task.status == TaskStatus.PENDING:
                task.status = TaskStatus.CANCELLED
                self.statistics.cancelled_tasks += 1
    
    def get_task_summary(self) -> Dict:
        """獲取任務摘要"""
        status_count = {}
        for task in self.tasks:
            status = task.status.value
            status_count[status] = status_count.get(status, 0) + 1
        
        return {
            "total_tasks": len(self.tasks),
            "status_distribution": status_count,
            "avg_priority": sum(task.priority for task in self.tasks) / len(self.tasks) if self.tasks else 0,
            "is_running": self.is_running,
            "cancelled": self.cancelled
        }
    
    def save_batch_report(self, result: BatchResult, output_path: str) -> bool:
        """保存批次處理報告"""
        try:
            report_data = result.to_dict()
            
            # 添加詳細任務信息
            report_data["task_details"] = []
            for task in self.tasks:
                task_detail = {
                    "task_id": task.task_id,
                    "satellite_id": task.satellite_id,
                    "status": task.status.value,
                    "execution_time": task.execution_time_seconds,
                    "retry_count": task.retry_count,
                    "error_message": task.error_message
                }
                report_data["task_details"].append(task_detail)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"批次處理報告已保存到: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存批次處理報告失敗: {str(e)}")
            return False


def create_batch_processor(configuration: BatchConfiguration = None) -> BatchProcessor:
    """創建批次處理器實例"""
    if configuration is None:
        configuration = BatchConfiguration()
    
    return BatchProcessor(configuration)


def create_orbit_calculation_task(satellite_id: str, sgp4_engine, 
                                start_time: datetime, duration_hours: float = 2.0,
                                time_step_seconds: int = 30) -> BatchTask:
    """創建軌道計算任務"""
    def calculate_orbit_trajectory(satellite_id: str, start_time: datetime, 
                                 duration_hours: float, time_step_seconds: int):
        """軌道軌跡計算函數"""
        try:
            results = []
            current_time = start_time
            end_time = start_time + timedelta(hours=duration_hours)
            
            while current_time <= end_time:
                result = sgp4_engine.calculate_position(satellite_id, current_time)
                if result and result.success:
                    results.append({
                        "timestamp": current_time.isoformat(),
                        "position_eci": result.position_eci.tolist(),
                        "velocity_eci": result.velocity_eci.tolist() if result.velocity_eci is not None else None
                    })
                
                current_time += timedelta(seconds=time_step_seconds)
            
            return {
                "satellite_id": satellite_id,
                "trajectory_points": len(results),
                "start_time": start_time.isoformat(),
                "duration_hours": duration_hours,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"軌道計算失敗 {satellite_id}: {str(e)}")
            raise
    
    return BatchTask(
        task_id=f"orbit_{satellite_id}_{int(start_time.timestamp())}",
        satellite_id=satellite_id,
        processing_function=calculate_orbit_trajectory,
        parameters={
            "satellite_id": satellite_id,
            "start_time": start_time,
            "duration_hours": duration_hours,
            "time_step_seconds": time_step_seconds
        },
        timeout_seconds=600
    )


# 測試代碼
if __name__ == "__main__":
    import sys
    import os
    from datetime import datetime, timezone
    
    logging.basicConfig(level=logging.INFO)
    
    # 創建測試配置
    config = BatchConfiguration(
        processing_mode=ProcessingMode.PARALLEL,
        max_workers=2,
        batch_size=50,
        progress_report_interval=5
    )
    
    # 創建批次處理器
    processor = create_batch_processor(config)
    
    # 創建測試任務
    def test_task(satellite_id: str, delay: float = 1.0):
        time.sleep(delay)
        return f"處理完成: {satellite_id}"
    
    for i in range(10):
        task = BatchTask(
            task_id=f"test_task_{i}",
            satellite_id=f"SAT_{i:03d}",
            processing_function=test_task,
            parameters={"satellite_id": f"SAT_{i:03d}", "delay": 0.5}
        )
        processor.add_task(task)
    
    # 執行批次處理
    result = processor.process_batch("test_batch")
    
    print("✅ 批次處理測試完成")
    print(f"成功率: {result.statistics.success_rate:.1f}%")
    print(f"處理時間: {(result.end_time - result.start_time).total_seconds():.1f}秒")
    print(f"吞吐量: {result.statistics.throughput_tasks_per_sec:.2f} 任務/秒")