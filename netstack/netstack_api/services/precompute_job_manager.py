#!/usr/bin/env python3
"""
預計算作業管理器 - Phase 2 核心組件

管理衛星軌道預計算作業的完整生命週期，包括作業創建、進度追蹤、
錯誤處理和資源管理。支援並發作業和長時間運行的計算任務。
"""

import asyncio
import structlog
import uuid
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, List, Any, Tuple
from enum import Enum
from dataclasses import dataclass, asdict

from .precompute_satellite_history import SatelliteHistoryPrecomputer, ObserverPosition
from .batch_processor import HistoryBatchProcessor
from .tle_data_manager import TLEDataManager

logger = structlog.get_logger(__name__)


class JobStatus(Enum):
    """作業狀態枚舉"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


@dataclass
class JobConfig:
    """作業配置"""
    constellation: str
    start_time: datetime
    end_time: datetime
    observer_coords: Tuple[float, float, float]  # 緯度, 經度, 海拔
    time_step_seconds: int = 30
    batch_size: int = 1000
    priority: int = 1  # 1=高, 2=中, 3=低
    retry_count: int = 3


@dataclass
class JobInfo:
    """作業信息"""
    job_id: str
    config: JobConfig
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    progress: float = 0.0
    total_calculations: int = 0
    processed_records: int = 0
    failed_records: int = 0
    estimated_duration_minutes: float = 0.0
    actual_duration_seconds: float = 0.0
    error_message: Optional[str] = None
    retry_attempts: int = 0
    resource_usage: Dict[str, Any] = None


class ResourceMonitor:
    """資源監控器"""
    
    def __init__(self):
        self.active_jobs = 0
        self.peak_memory_mb = 0
        self.total_cpu_time = 0.0
    
    def start_job(self) -> None:
        """開始作業時調用"""
        self.active_jobs += 1
    
    def end_job(self, duration: float) -> None:
        """結束作業時調用"""
        self.active_jobs = max(0, self.active_jobs - 1)
        self.total_cpu_time += duration
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取資源統計"""
        return {
            "active_jobs": self.active_jobs,
            "peak_memory_mb": self.peak_memory_mb,
            "total_cpu_time": self.total_cpu_time
        }


class PrecomputeJobManager:
    """
    預計算作業管理器
    
    功能：
    1. 作業創建和調度
    2. 進度追蹤和狀態管理
    3. 錯誤處理和重試機制
    4. 資源監控和限制
    5. 作業優先級管理
    """
    
    def __init__(self, max_concurrent_jobs: int = 2, db_url: Optional[str] = None):
        """
        初始化作業管理器
        
        Args:
            max_concurrent_jobs: 最大並發作業數
            db_url: 數據庫連接字符串
        """
        self.max_concurrent_jobs = max_concurrent_jobs
        self.db_url = db_url or os.getenv('SATELLITE_DATABASE_URL', 'postgresql://netstack_user:netstack_password@netstack-postgres:5432/netstack_db')
        self.logger = structlog.get_logger(__name__)
        
        # 作業存儲
        self.active_jobs: Dict[str, JobInfo] = {}
        self.job_tasks: Dict[str, asyncio.Task] = {}
        self.job_queue: List[str] = []  # 等待隊列
        
        # 組件
        self.tle_manager = TLEDataManager()
        self.resource_monitor = ResourceMonitor()
        
        # 控制標誌
        self._shutdown = False
        self._queue_task: Optional[asyncio.Task] = None
        
        self.logger.info(
            "預計算作業管理器初始化完成",
            max_concurrent_jobs=max_concurrent_jobs
        )
    
    async def initialize(self) -> bool:
        """
        初始化管理器
        
        Returns:
            是否初始化成功
        """
        try:
            # 初始化 TLE 管理器
            await self.tle_manager.initialize_default_sources()
            
            # 啟動作業隊列處理器
            self._queue_task = asyncio.create_task(self._process_job_queue())
            
            self.logger.info("作業管理器初始化成功")
            return True
            
        except Exception as e:
            self.logger.error("作業管理器初始化失敗", error=str(e))
            return False
    
    async def create_precompute_job(
        self,
        constellation: str,
        start_time: datetime,
        end_time: datetime,
        observer_coords: Tuple[float, float, float],
        time_step_seconds: int = 30,
        priority: int = 1
    ) -> str:
        """
        創建預計算作業
        
        Args:
            constellation: 星座名稱
            start_time: 開始時間
            end_time: 結束時間  
            observer_coords: 觀測者坐標 (緯度, 經度, 海拔)
            time_step_seconds: 時間步長
            priority: 優先級 (1=高, 2=中, 3=低)
            
        Returns:
            作業 ID
        """
        # 生成作業 ID
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        job_id = f"precompute_{constellation}_{timestamp}_{uuid.uuid4().hex[:8]}"
        
        # 估算計算量
        duration_seconds = (end_time - start_time).total_seconds()
        total_timepoints = int(duration_seconds / time_step_seconds)
        estimated_duration_minutes = max(1, total_timepoints / 1000)  # 估算：1000 個時間點/分鐘
        
        # 創建作業配置
        config = JobConfig(
            constellation=constellation,
            start_time=start_time,
            end_time=end_time,
            observer_coords=observer_coords,
            time_step_seconds=time_step_seconds,
            priority=priority
        )
        
        # 創建作業信息
        job_info = JobInfo(
            job_id=job_id,
            config=config,
            status=JobStatus.PENDING,
            created_at=datetime.now(timezone.utc),
            total_calculations=total_timepoints,
            estimated_duration_minutes=estimated_duration_minutes
        )
        
        # 存儲作業
        self.active_jobs[job_id] = job_info
        
        # 添加到隊列
        self._add_to_queue(job_id)
        
        self.logger.info(
            "預計算作業已創建",
            job_id=job_id,
            constellation=constellation,
            total_calculations=total_timepoints,
            estimated_duration=f"{estimated_duration_minutes:.1f}分鐘"
        )
        
        return job_id
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        獲取作業狀態
        
        Args:
            job_id: 作業 ID
            
        Returns:
            作業狀態字典或 None
        """
        if job_id not in self.active_jobs:
            return None
        
        job = self.active_jobs[job_id]
        
        # 轉換為可序列化的字典
        status_dict = {
            "job_id": job.job_id,
            "status": job.status.value,
            "progress": job.progress,
            "created_at": job.created_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "failed_at": job.failed_at.isoformat() if job.failed_at else None,
            "total_calculations": job.total_calculations,
            "processed_records": job.processed_records,
            "failed_records": job.failed_records,
            "estimated_duration_minutes": job.estimated_duration_minutes,
            "actual_duration_seconds": job.actual_duration_seconds,
            "error_message": job.error_message,
            "retry_attempts": job.retry_attempts,
            "config": {
                "constellation": job.config.constellation,
                "start_time": job.config.start_time.isoformat(),
                "end_time": job.config.end_time.isoformat(),
                "observer_coords": job.config.observer_coords,
                "time_step_seconds": job.config.time_step_seconds,
                "priority": job.config.priority
            }
        }
        
        return status_dict
    
    async def cancel_job(self, job_id: str) -> bool:
        """
        取消作業
        
        Args:
            job_id: 作業 ID
            
        Returns:
            是否成功取消
        """
        if job_id not in self.active_jobs:
            return False
        
        job = self.active_jobs[job_id]
        
        if job.status in [JobStatus.PENDING, JobStatus.RUNNING, JobStatus.PAUSED]:
            # 取消任務
            if job_id in self.job_tasks:
                self.job_tasks[job_id].cancel()
                del self.job_tasks[job_id]
            
            # 從隊列移除
            if job_id in self.job_queue:
                self.job_queue.remove(job_id)
            
            # 更新狀態
            job.status = JobStatus.CANCELLED
            job.failed_at = datetime.now(timezone.utc)
            
            self.logger.info(f"作業已取消", job_id=job_id)
            return True
        
        return False
    
    async def pause_job(self, job_id: str) -> bool:
        """暫停作業"""
        if job_id not in self.active_jobs:
            return False
        
        job = self.active_jobs[job_id]
        if job.status == JobStatus.RUNNING:
            job.status = JobStatus.PAUSED
            self.logger.info(f"作業已暫停", job_id=job_id)
            return True
        
        return False
    
    async def resume_job(self, job_id: str) -> bool:
        """恢復作業"""
        if job_id not in self.active_jobs:
            return False
        
        job = self.active_jobs[job_id]
        if job.status == JobStatus.PAUSED:
            job.status = JobStatus.PENDING
            self._add_to_queue(job_id)
            self.logger.info(f"作業已恢復", job_id=job_id)
            return True
        
        return False
    
    async def get_all_jobs(self) -> List[Dict[str, Any]]:
        """獲取所有作業狀態"""
        jobs = []
        for job_id in self.active_jobs:
            job_status = await self.get_job_status(job_id)
            if job_status:
                jobs.append(job_status)
        
        # 按創建時間排序
        jobs.sort(key=lambda x: x["created_at"], reverse=True)
        return jobs
    
    async def get_system_status(self) -> Dict[str, Any]:
        """獲取系統狀態"""
        active_count = len([j for j in self.active_jobs.values() if j.status == JobStatus.RUNNING])
        pending_count = len([j for j in self.active_jobs.values() if j.status == JobStatus.PENDING])
        completed_count = len([j for j in self.active_jobs.values() if j.status == JobStatus.COMPLETED])
        failed_count = len([j for j in self.active_jobs.values() if j.status == JobStatus.FAILED])
        
        return {
            "active_jobs": active_count,
            "pending_jobs": pending_count,
            "completed_jobs": completed_count,
            "failed_jobs": failed_count,
            "total_jobs": len(self.active_jobs),
            "max_concurrent": self.max_concurrent_jobs,
            "queue_length": len(self.job_queue),
            "resource_stats": self.resource_monitor.get_stats()
        }
    
    def _add_to_queue(self, job_id: str) -> None:
        """添加作業到隊列（按優先級排序）"""
        if job_id in self.job_queue:
            return
        
        job = self.active_jobs[job_id]
        
        # 按優先級插入（優先級數字越小越優先）
        inserted = False
        for i, queued_id in enumerate(self.job_queue):
            queued_job = self.active_jobs[queued_id]
            if job.config.priority < queued_job.config.priority:
                self.job_queue.insert(i, job_id)
                inserted = True
                break
        
        if not inserted:
            self.job_queue.append(job_id)
    
    async def _process_job_queue(self) -> None:
        """處理作業隊列"""
        while not self._shutdown:
            try:
                # 檢查是否可以啟動新作業
                running_count = len([t for t in self.job_tasks.values() if not t.done()])
                
                if running_count < self.max_concurrent_jobs and self.job_queue:
                    job_id = self.job_queue.pop(0)
                    
                    if job_id in self.active_jobs:
                        job = self.active_jobs[job_id]
                        
                        if job.status == JobStatus.PENDING:
                            # 啟動作業
                            task = asyncio.create_task(self._execute_precompute_job(job_id))
                            self.job_tasks[job_id] = task
                
                # 清理完成的任務
                completed_tasks = [job_id for job_id, task in self.job_tasks.items() if task.done()]
                for job_id in completed_tasks:
                    del self.job_tasks[job_id]
                
                await asyncio.sleep(1)  # 每秒檢查一次
                
            except Exception as e:
                self.logger.error("作業隊列處理異常", error=str(e))
                await asyncio.sleep(5)
    
    async def _execute_precompute_job(self, job_id: str) -> None:
        """
        執行預計算作業
        
        Args:
            job_id: 作業 ID
        """
        job = self.active_jobs[job_id]
        
        try:
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now(timezone.utc)
            
            self.resource_monitor.start_job()
            
            self.logger.info(f"開始執行預計算作業", job_id=job_id)
            
            # 下載 TLE 數據
            tle_data = await self.tle_manager.get_constellation_satellites(job.config.constellation)
            
            if not tle_data:
                # 嘗試更新 TLE 數據
                await self.tle_manager.force_update_all()
                tle_data = await self.tle_manager.get_constellation_satellites(job.config.constellation)
            
            if not tle_data:
                raise Exception(f"無法獲取 {job.config.constellation} 星座的 TLE 數據")
            
            # 轉換 TLE 數據格式
            tle_data_dict = [asdict(tle) for tle in tle_data]
            
            # 創建預計算器
            precomputer = SatelliteHistoryPrecomputer(
                tle_data=tle_data_dict,
                observer_coords=job.config.observer_coords,
                time_range=(job.config.start_time, job.config.end_time)
            )
            
            # 分批計算以便更新進度
            batch_duration = timedelta(hours=1)  # 每次計算 1 小時的數據
            current_time = job.config.start_time
            all_results = []
            
            while current_time < job.config.end_time and job.status == JobStatus.RUNNING:
                batch_end = min(current_time + batch_duration, job.config.end_time)
                
                # 計算當前批次
                batch_precomputer = SatelliteHistoryPrecomputer(
                    tle_data=tle_data_dict,
                    observer_coords=job.config.observer_coords,
                    time_range=(current_time, batch_end)
                )
                
                batch_results = batch_precomputer.compute_history(job.config.time_step_seconds)
                all_results.extend(batch_results)
                
                # 更新進度
                progress = (current_time - job.config.start_time).total_seconds() / (job.config.end_time - job.config.start_time).total_seconds()
                job.progress = min(progress * 100, 100.0)
                
                self.logger.info(f"作業進度", job_id=job_id, progress=f"{job.progress:.1f}%")
                
                current_time = batch_end
            
            if job.status != JobStatus.RUNNING:
                return  # 作業被取消或暫停
            
            # 存儲結果
            processor = HistoryBatchProcessor(self.db_url)
            await processor.initialize()
            
            try:
                store_result = await processor.process_and_store(all_results)
                job.processed_records = store_result.get("processed", 0)
                job.failed_records = store_result.get("failed", 0)
                
            finally:
                await processor.close()
            
            # 作業完成
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now(timezone.utc)
            job.progress = 100.0
            job.actual_duration_seconds = (job.completed_at - job.started_at).total_seconds()
            
            self.logger.info(
                "預計算作業完成",
                job_id=job_id,
                processed_records=job.processed_records,
                failed_records=job.failed_records,
                duration=f"{job.actual_duration_seconds:.1f}s"
            )
            
        except asyncio.CancelledError:
            job.status = JobStatus.CANCELLED
            self.logger.info(f"作業被取消", job_id=job_id)
            
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.failed_at = datetime.now(timezone.utc)
            job.retry_attempts += 1
            
            self.logger.error(f"預計算作業失敗", job_id=job_id, error=str(e))
            
            # 重試邏輯
            if job.retry_attempts < job.config.retry_count:
                job.status = JobStatus.PENDING
                self._add_to_queue(job_id)
                self.logger.info(f"作業將重試", job_id=job_id, retry_attempt=job.retry_attempts)
        
        finally:
            if job.started_at:
                duration = (datetime.now(timezone.utc) - job.started_at).total_seconds()
                self.resource_monitor.end_job(duration)
    
    def cleanup_completed_jobs(self, max_age_hours: int = 24) -> int:
        """
        清理完成的作業記錄
        
        Args:
            max_age_hours: 最大保留時間（小時）
            
        Returns:
            清理的作業數量
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        
        jobs_to_remove = []
        for job_id, job in self.active_jobs.items():
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                job_time = job.completed_at or job.failed_at or job.created_at
                if job_time < cutoff_time:
                    jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            del self.active_jobs[job_id]
            if job_id in self.job_tasks:
                del self.job_tasks[job_id]
        
        if jobs_to_remove:
            self.logger.info(f"清理了 {len(jobs_to_remove)} 個過期作業記錄")
        
        return len(jobs_to_remove)
    
    async def shutdown(self) -> None:
        """關閉作業管理器"""
        self._shutdown = True
        
        # 取消所有運行中的作業
        for job_id in list(self.job_tasks.keys()):
            await self.cancel_job(job_id)
        
        # 停止隊列處理器
        if self._queue_task:
            self._queue_task.cancel()
            try:
                await self._queue_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("預計算作業管理器已關閉")


# 全域作業管理器實例
job_manager = PrecomputeJobManager()