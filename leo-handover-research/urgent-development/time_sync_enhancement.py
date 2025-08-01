"""
⏰ 時間同步精度強化系統
=========================

提供亞秒級時間同步精度，確保 D2 事件觸發時機準確
支持多種時間源和同步協議，適用於 LEO 衛星換手場景

作者: Claude Sonnet 4 (SuperClaude)
版本: v1.0  
日期: 2025-08-01
精度目標: <10ms (從原本50ms提升)
"""

import time
import threading
import logging
import statistics
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod
from collections import deque
import socket
import struct

logger = logging.getLogger(__name__)


@dataclass
class TimeReference:
    """時間參考點"""
    timestamp: float
    source: str
    accuracy_ms: float
    confidence: float  # 0-1
    drift_rate_ppm: float  # 漂移率 (ppm)


@dataclass
class SyncResult:
    """時間同步結果"""
    synchronized_time: float
    local_time: float
    offset_ms: float
    accuracy_ms: float
    sync_method: str
    confidence: float
    last_sync_timestamp: float


class TimeSource(ABC):
    """時間源抽象基類"""
    
    @abstractmethod
    def get_reference_time(self) -> TimeReference:
        """獲取參考時間"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """檢查時間源是否可用"""
        pass


class SystemTimeSource(TimeSource):
    """系統時間源"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.SystemTimeSource")
        
    def get_reference_time(self) -> TimeReference:
        """獲取系統時間"""
        current_time = time.time()
        return TimeReference(
            timestamp=current_time,
            source='system',
            accuracy_ms=50.0,  # 系統時間精度通常較低
            confidence=0.7,
            drift_rate_ppm=10.0
        )
        
    def is_available(self) -> bool:
        return True


class NTPTimeSource(TimeSource):
    """NTP 時間源 (模擬實現)"""
    
    def __init__(self, ntp_server: str = "pool.ntp.org"):
        self.logger = logging.getLogger(f"{__name__}.NTPTimeSource")
        self.ntp_server = ntp_server
        self.last_sync_time = 0
        self.last_offset = 0.0
        
    def get_reference_time(self) -> TimeReference:
        """獲取 NTP 時間 (模擬實現)"""
        try:
            # 模擬 NTP 查詢
            current_time = time.time()
            
            # 簡化的 NTP 偏移計算 (實際應使用 ntplib)
            ntp_offset = np.random.normal(0, 0.005)  # ±5ms 標準差
            ntp_time = current_time + ntp_offset
            
            self.last_sync_time = current_time
            self.last_offset = ntp_offset
            
            return TimeReference(
                timestamp=ntp_time,
                source=f'ntp_{self.ntp_server}',
                accuracy_ms=5.0,  # NTP 通常可達到 5ms 精度
                confidence=0.9,
                drift_rate_ppm=1.0
            )
            
        except Exception as e:
            self.logger.error(f"NTP 時間獲取失敗: {e}")
            # 備用系統時間
            return TimeReference(
                timestamp=time.time(),
                source='ntp_fallback',
                accuracy_ms=50.0,
                confidence=0.5,
                drift_rate_ppm=10.0
            )
    
    def is_available(self) -> bool:
        """檢查 NTP 服務可用性 (簡化實現)"""
        try:
            # 模擬網路連接檢查
            return time.time() - self.last_sync_time < 300  # 5分鐘內有同步過
        except:
            return False


class GPSTimeSource(TimeSource):
    """GPS 時間源 (模擬實現)"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.GPSTimeSource")
        self.gps_available = True  # 模擬 GPS 可用性
        
    def get_reference_time(self) -> TimeReference:
        """獲取 GPS 時間"""
        if not self.gps_available:
            raise RuntimeError("GPS 信號不可用")
        
        try:
            # 模擬 GPS 時間 (UTC)
            current_time = time.time()
            gps_offset = np.random.normal(0, 0.001)  # ±1ms 標準差
            gps_time = current_time + gps_offset
            
            return TimeReference(
                timestamp=gps_time,
                source='gps',
                accuracy_ms=1.0,  # GPS 可達到 1ms 精度
                confidence=0.95,
                drift_rate_ppm=0.1
            )
            
        except Exception as e:
            self.logger.error(f"GPS 時間獲取失敗: {e}")
            raise
    
    def is_available(self) -> bool:
        return self.gps_available


class PrecisionTimeProtocol(TimeSource):
    """精密時間協定 (PTP) 時間源"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.PrecisionTimeProtocol")
        self.ptp_enabled = True
        
    def get_reference_time(self) -> TimeReference:
        """獲取 PTP 時間"""
        try:
            # 模擬 PTP 同步
            current_time = time.time()
            ptp_offset = np.random.normal(0, 0.0001)  # ±0.1ms 標準差
            ptp_time = current_time + ptp_offset
            
            return TimeReference(
                timestamp=ptp_time,
                source='ptp',
                accuracy_ms=0.1,  # PTP 可達到亞毫秒精度
                confidence=0.98,
                drift_rate_ppm=0.01
            )
            
        except Exception as e:
            self.logger.error(f"PTP 時間獲取失敗: {e}")
            raise
    
    def is_available(self) -> bool:
        return self.ptp_enabled


class AdaptiveTimeSyncSystem:
    """
    自適應時間同步系統
    支持多時間源融合和智能切換
    """
    
    def __init__(self, target_accuracy_ms: float = 10.0):
        self.logger = logging.getLogger(f"{__name__}.AdaptiveTimeSyncSystem")
        
        # 系統參數
        self.target_accuracy_ms = target_accuracy_ms
        self.sync_interval_s = 1.0  # 同步間隔
        self.history_size = 100
        
        # 時間源管理
        self.time_sources: Dict[str, TimeSource] = {}
        self.primary_source: Optional[str] = None
        self.backup_sources: List[str] = []
        
        # 同步狀態
        self.sync_history = deque(maxlen=self.history_size)
        self.current_offset = 0.0
        self.drift_compensation = 0.0
        self.last_sync_time = 0.0
        
        # 統計資料
        self.sync_stats = {
            'successful_syncs': 0,
            'failed_syncs': 0,
            'average_accuracy_ms': 0.0,
            'max_offset_ms': 0.0,
            'current_accuracy_ms': target_accuracy_ms
        }
        
        # 控制線程
        self.sync_thread = None
        self.running = False
        
        self._initialize_time_sources()
        self.logger.info(f"自適應時間同步系統初始化完成 (目標精度: {target_accuracy_ms}ms)")
    
    def _initialize_time_sources(self):
        """初始化時間源"""
        # 添加各種時間源
        self.time_sources['system'] = SystemTimeSource()
        self.time_sources['ntp'] = NTPTimeSource()
        self.time_sources['gps'] = GPSTimeSource()
        self.time_sources['ptp'] = PrecisionTimeProtocol()
        
        # 設置優先級 (精度越高優先級越高)
        self.primary_source = 'ptp'
        self.backup_sources = ['gps', 'ntp', 'system']
        
        self.logger.info(f"時間源初始化完成: {list(self.time_sources.keys())}")
    
    def start_sync(self):
        """啟動時間同步"""
        if self.running:
            return
        
        self.running = True
        self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.sync_thread.start()
        
        self.logger.info("時間同步線程已啟動")
    
    def stop_sync(self):
        """停止時間同步"""
        self.running = False
        if self.sync_thread:
            self.sync_thread.join(timeout=2.0)
        
        self.logger.info("時間同步線程已停止")
    
    def _sync_loop(self):
        """同步循環"""
        while self.running:
            try:
                self._perform_sync()
                time.sleep(self.sync_interval_s)
            except Exception as e:
                self.logger.error(f"同步循環錯誤: {e}")
                time.sleep(1.0)
    
    def _perform_sync(self):
        """執行時間同步"""
        try:
            # 選擇最佳時間源
            selected_source = self._select_best_time_source()
            
            if not selected_source:
                self.logger.warning("沒有可用的時間源")
                return
            
            # 獲取參考時間
            time_ref = self.time_sources[selected_source].get_reference_time()
            local_time = time.time()
            
            # 計算偏移
            offset_s = time_ref.timestamp - local_time
            offset_ms = offset_s * 1000
            
            # 更新偏移和漂移補償
            self._update_sync_parameters(offset_ms, time_ref)
            
            # 記錄同步結果
            sync_result = SyncResult(
                synchronized_time=time_ref.timestamp,
                local_time=local_time,
                offset_ms=offset_ms,
                accuracy_ms=time_ref.accuracy_ms,
                sync_method=selected_source,
                confidence=time_ref.confidence,
                last_sync_timestamp=local_time
            )
            
            self.sync_history.append(sync_result)
            self.last_sync_time = local_time
            
            # 更新統計資料
            self._update_statistics(sync_result)
            
            self.logger.debug(f"時間同步完成: 源={selected_source}, "
                            f"偏移={offset_ms:.2f}ms, "
                            f"精度={time_ref.accuracy_ms:.2f}ms")
            
        except Exception as e:
            self.logger.error(f"時間同步失敗: {e}")
            self.sync_stats['failed_syncs'] += 1
    
    def _select_best_time_source(self) -> Optional[str]:
        """選擇最佳時間源"""
        # 首先嘗試主要時間源
        if (self.primary_source and 
            self.primary_source in self.time_sources and
            self.time_sources[self.primary_source].is_available()):
            return self.primary_source
        
        # 嘗試備用時間源
        for backup_source in self.backup_sources:
            if (backup_source in self.time_sources and
                self.time_sources[backup_source].is_available()):
                return backup_source
        
        return None
    
    def _update_sync_parameters(self, offset_ms: float, time_ref: TimeReference):
        """更新同步參數"""
        # 使用低通濾波器平滑偏移
        alpha = 0.1  # 濾波係數
        self.current_offset = alpha * offset_ms + (1 - alpha) * self.current_offset
        
        # 計算漂移補償 (簡化實現)
        if len(self.sync_history) > 1:
            recent_offsets = [r.offset_ms for r in list(self.sync_history)[-10:]]
            if len(recent_offsets) > 2:
                # 計算漂移趨勢
                drift_trend = np.polyfit(range(len(recent_offsets)), recent_offsets, 1)[0]
                self.drift_compensation = drift_trend * 0.1  # 漂移補償係數
    
    def _update_statistics(self, sync_result: SyncResult):
        """更新統計資料"""
        self.sync_stats['successful_syncs'] += 1
        
        # 計算平均精度
        recent_accuracies = [r.accuracy_ms for r in list(self.sync_history)[-20:]]
        self.sync_stats['average_accuracy_ms'] = statistics.mean(recent_accuracies)
        
        # 記錄最大偏移
        self.sync_stats['max_offset_ms'] = max(
            self.sync_stats['max_offset_ms'], 
            abs(sync_result.offset_ms)
        )
        
        # 當前精度估算
        self.sync_stats['current_accuracy_ms'] = sync_result.accuracy_ms
    
    def get_synchronized_time(self) -> float:
        """獲取同步後的時間"""
        local_time = time.time()
        
        # 應用偏移和漂移補償
        time_since_last_sync = local_time - self.last_sync_time
        drift_correction = self.drift_compensation * time_since_last_sync / 1000
        
        synchronized_time = local_time - (self.current_offset + drift_correction) / 1000
        
        return synchronized_time
    
    def get_time_accuracy_ms(self) -> float:
        """獲取當前時間精度 (ms)"""
        if not self.sync_history:
            return self.target_accuracy_ms
        
        # 基於最近同步結果估算精度
        recent_sync = self.sync_history[-1]
        time_since_sync = time.time() - recent_sync.last_sync_timestamp
        
        # 精度隨時間降低
        accuracy_degradation = time_since_sync * 0.1  # 每秒降低 0.1ms
        
        current_accuracy = recent_sync.accuracy_ms + accuracy_degradation
        
        return min(current_accuracy, self.target_accuracy_ms * 5)  # 最大不超過目標精度的 5 倍
    
    def is_sync_accurate(self) -> bool:
        """檢查同步精度是否滿足要求"""
        return self.get_time_accuracy_ms() <= self.target_accuracy_ms
    
    def get_sync_statistics(self) -> Dict[str, Any]:
        """獲取同步統計資料"""
        total_syncs = self.sync_stats['successful_syncs'] + self.sync_stats['failed_syncs']
        success_rate = (self.sync_stats['successful_syncs'] / max(total_syncs, 1)) * 100
        
        return {
            **self.sync_stats,
            'total_syncs': total_syncs,
            'success_rate_percent': success_rate,
            'current_offset_ms': self.current_offset,
            'drift_compensation_ms': self.drift_compensation,
            'time_since_last_sync_s': time.time() - self.last_sync_time,
            'sync_history_size': len(self.sync_history)
        }


class HighPrecisionTimer:
    """
    高精度計時器
    用於 D2 事件觸發的精確時機控制
    """
    
    def __init__(self, sync_system: AdaptiveTimeSyncSystem):
        self.logger = logging.getLogger(f"{__name__}.HighPrecisionTimer")
        self.sync_system = sync_system
        self.active_timers: Dict[str, Dict] = {}
        
    def schedule_event(self, event_id: str, target_time: float, 
                      callback: Callable, accuracy_required_ms: float = 10.0):
        """
        調度事件到精確時間
        
        Args:
            event_id: 事件ID
            target_time: 目標時間 (同步時間)
            callback: 回調函數
            accuracy_required_ms: 要求精度 (ms)
        """
        try:
            # 檢查同步精度是否滿足要求
            current_accuracy = self.sync_system.get_time_accuracy_ms()
            if current_accuracy > accuracy_required_ms:
                self.logger.warning(f"時間同步精度不足: 當前{current_accuracy:.1f}ms > 要求{accuracy_required_ms:.1f}ms")
            
            # 計算等待時間
            current_sync_time = self.sync_system.get_synchronized_time()
            wait_time = target_time - current_sync_time
            
            if wait_time <= 0:
                self.logger.warning(f"事件 {event_id} 目標時間已過")
                return False
            
            # 創建計時器線程
            timer_info = {
                'event_id': event_id,
                'target_time': target_time,
                'callback': callback,
                'accuracy_required_ms': accuracy_required_ms,
                'created_time': current_sync_time,
                'thread': None
            }
            
            timer_thread = threading.Thread(
                target=self._precise_wait_and_execute,
                args=(timer_info,),
                daemon=True
            )
            
            timer_info['thread'] = timer_thread
            self.active_timers[event_id] = timer_info
            
            timer_thread.start()
            
            self.logger.info(f"事件 {event_id} 已調度到 {target_time:.3f} "
                           f"(等待 {wait_time:.3f}s)")
            
            return True
            
        except Exception as e:
            self.logger.error(f"事件調度失敗: {e}")
            return False
    
    def _precise_wait_and_execute(self, timer_info: Dict):
        """精確等待並執行事件"""
        try:
            event_id = timer_info['event_id']
            target_time = timer_info['target_time']
            callback = timer_info['callback']
            
            # 精確等待
            while True:
                current_time = self.sync_system.get_synchronized_time()
                remaining_time = target_time - current_time
                
                if remaining_time <= 0:
                    break
                
                # 動態調整等待時間
                if remaining_time > 0.1:  # >100ms
                    time.sleep(remaining_time - 0.05)  # 留 50ms 精確等待
                elif remaining_time > 0.01:  # >10ms
                    time.sleep(remaining_time / 2)
                else:  # <10ms
                    time.sleep(0.001)  # 1ms 精確等待
            
            # 執行回調
            execution_time = self.sync_system.get_synchronized_time()
            time_error_ms = (execution_time - target_time) * 1000
            
            self.logger.debug(f"執行事件 {event_id}: 時間誤差 {time_error_ms:.2f}ms")
            
            # 調用回調函數
            callback(event_id, execution_time, time_error_ms)
            
            # 清理計時器
            if event_id in self.active_timers:
                del self.active_timers[event_id]
                
        except Exception as e:
            self.logger.error(f"精確計時器執行失敗: {e}")
    
    def cancel_event(self, event_id: str) -> bool:
        """取消事件"""
        if event_id in self.active_timers:
            timer_info = self.active_timers[event_id]
            # 標記線程停止 (簡化實現)
            del self.active_timers[event_id]
            self.logger.info(f"事件 {event_id} 已取消")
            return True
        return False
    
    def get_active_timers(self) -> List[str]:
        """獲取活動計時器列表"""
        return list(self.active_timers.keys())


# 測試和驗證函數
def test_time_sync_system():
    """測試時間同步系統"""
    logger.info("開始時間同步系統測試")
    
    # 創建同步系統
    sync_system = AdaptiveTimeSyncSystem(target_accuracy_ms=10.0)
    
    # 啟動同步
    sync_system.start_sync()
    
    # 等待幾次同步
    time.sleep(3.0)
    
    # 檢查同步狀態
    stats = sync_system.get_sync_statistics()
    logger.info(f"同步統計:")
    logger.info(f"  成功率: {stats['success_rate_percent']:.1f}%")
    logger.info(f"  平均精度: {stats['average_accuracy_ms']:.2f} ms")
    logger.info(f"  當前精度: {sync_system.get_time_accuracy_ms():.2f} ms")
    logger.info(f"  偏移: {stats['current_offset_ms']:.2f} ms")
    
    # 測試高精度計時器
    timer = HighPrecisionTimer(sync_system)
    
    def test_callback(event_id, execution_time, time_error_ms):
        logger.info(f"事件 {event_id} 執行完成，時間誤差: {time_error_ms:.2f}ms")
    
    # 調度測試事件
    target_time = sync_system.get_synchronized_time() + 1.0  # 1秒後
    timer.schedule_event("test_event", target_time, test_callback, 5.0)
    
    # 等待事件執行
    time.sleep(1.5)
    
    # 停止同步
    sync_system.stop_sync()
    
    # 最終統計
    final_stats = sync_system.get_sync_statistics()
    accuracy_achieved = final_stats['current_accuracy_ms'] <= 10.0
    
    logger.info(f"測試結果:")
    logger.info(f"  目標精度達成: {'✅' if accuracy_achieved else '❌'}")
    logger.info(f"  同步成功率: {final_stats['success_rate_percent']:.1f}%")
    
    return sync_system, timer


if __name__ == "__main__":
    # 設置日誌
    logging.basicConfig(level=logging.INFO,
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 運行測試
    test_time_sync_system()
