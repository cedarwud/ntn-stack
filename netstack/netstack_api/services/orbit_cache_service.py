"""
軌道計算緩存服務
完成 Phase 4.2 要求：提供高效的軌道計算緩存機制

功能特點：
- 智能緩存策略，減少重複計算
- 基於時間和位置的緩存鍵
- 自動過期和清理機制
- 記憶體和磁盤雙層緩存
- 緩存命中率統計
"""

import hashlib
import json
import time
import threading
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple, Any, List
from dataclasses import dataclass, asdict
import pickle
import os
from pathlib import Path

@dataclass
class CacheEntry:
    """緩存條目"""
    data: Any
    timestamp: float
    access_count: int
    last_access: float
    ttl: float  # 生存時間 (秒)
    
    def is_expired(self) -> bool:
        """檢查是否過期"""
        return time.time() - self.timestamp > self.ttl
    
    def is_stale(self, staleness_threshold: float = 300) -> bool:
        """檢查是否陳舊 (5分鐘)"""
        return time.time() - self.timestamp > staleness_threshold

@dataclass
class CacheStats:
    """緩存統計"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_entries: int = 0
    memory_usage_bytes: int = 0
    
    @property
    def hit_rate(self) -> float:
        """命中率"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

class OrbitCacheService:
    """軌道計算緩存服務"""
    
    def __init__(self, 
                 max_memory_entries: int = 1000,
                 default_ttl: float = 3600,  # 1小時
                 cache_dir: str = "/tmp/orbit_cache",
                 enable_disk_cache: bool = True):
        """
        初始化緩存服務
        
        Args:
            max_memory_entries: 記憶體緩存最大條目數
            default_ttl: 預設生存時間 (秒)
            cache_dir: 磁盤緩存目錄
            enable_disk_cache: 是否啟用磁盤緩存
        """
        self.max_memory_entries = max_memory_entries
        self.default_ttl = default_ttl
        self.cache_dir = Path(cache_dir)
        self.enable_disk_cache = enable_disk_cache
        
        # 記憶體緩存
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.access_order: List[str] = []  # LRU 順序
        
        # 統計資訊
        self.stats = CacheStats()
        
        # 執行緒鎖
        self.lock = threading.RLock()
        
        # 初始化磁盤緩存目錄
        if self.enable_disk_cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 啟動清理執行緒
        self.cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self.cleanup_thread.start()
    
    def _generate_cache_key(self, tle_line1: str, tle_line2: str, 
                           prediction_time: datetime, precision: int = 60) -> str:
        """
        生成緩存鍵
        
        Args:
            tle_line1: TLE 第一行
            tle_line2: TLE 第二行
            prediction_time: 預測時間
            precision: 時間精度 (秒)，用於時間量化
            
        Returns:
            str: 緩存鍵
        """
        # 時間量化到指定精度
        timestamp = prediction_time.timestamp()
        quantized_timestamp = int(timestamp // precision) * precision
        
        # 組合所有參數
        key_data = {
            'tle1': tle_line1.strip(),
            'tle2': tle_line2.strip(),
            'time': quantized_timestamp,
            'precision': precision
        }
        
        # 生成 MD5 雜湊
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, tle_line1: str, tle_line2: str, 
            prediction_time: datetime, precision: int = 60) -> Optional[Dict]:
        """
        從緩存獲取軌道計算結果
        
        Args:
            tle_line1: TLE 第一行
            tle_line2: TLE 第二行
            prediction_time: 預測時間
            precision: 時間精度 (秒)
            
        Returns:
            Optional[Dict]: 緩存的軌道計算結果，如果不存在則返回 None
        """
        cache_key = self._generate_cache_key(tle_line1, tle_line2, prediction_time, precision)
        
        with self.lock:
            # 首先檢查記憶體緩存
            if cache_key in self.memory_cache:
                entry = self.memory_cache[cache_key]
                
                if not entry.is_expired():
                    # 更新存取統計
                    entry.access_count += 1
                    entry.last_access = time.time()
                    
                    # 更新 LRU 順序
                    if cache_key in self.access_order:
                        self.access_order.remove(cache_key)
                    self.access_order.append(cache_key)
                    
                    self.stats.hits += 1
                    return entry.data
                else:
                    # 過期條目，移除
                    del self.memory_cache[cache_key]
                    if cache_key in self.access_order:
                        self.access_order.remove(cache_key)
            
            # 檢查磁盤緩存
            if self.enable_disk_cache:
                disk_result = self._get_from_disk(cache_key)
                if disk_result is not None:
                    # 將磁盤緩存載入記憶體
                    self._put_memory(cache_key, disk_result, self.default_ttl)
                    self.stats.hits += 1
                    return disk_result
            
            self.stats.misses += 1
            return None
    
    def put(self, tle_line1: str, tle_line2: str, 
            prediction_time: datetime, result: Dict, 
            ttl: Optional[float] = None, precision: int = 60) -> None:
        """
        將軌道計算結果存入緩存
        
        Args:
            tle_line1: TLE 第一行
            tle_line2: TLE 第二行
            prediction_time: 預測時間
            result: 軌道計算結果
            ttl: 生存時間 (秒)，如果為 None 則使用預設值
            precision: 時間精度 (秒)
        """
        cache_key = self._generate_cache_key(tle_line1, tle_line2, prediction_time, precision)
        ttl = ttl or self.default_ttl
        
        with self.lock:
            # 存入記憶體緩存
            self._put_memory(cache_key, result, ttl)
            
            # 存入磁盤緩存
            if self.enable_disk_cache:
                self._put_disk(cache_key, result, ttl)
    
    def _put_memory(self, cache_key: str, data: Any, ttl: float) -> None:
        """存入記憶體緩存"""
        current_time = time.time()
        
        # 檢查是否需要清理空間
        if len(self.memory_cache) >= self.max_memory_entries:
            self._evict_lru()
        
        # 創建緩存條目
        entry = CacheEntry(
            data=data,
            timestamp=current_time,
            access_count=1,
            last_access=current_time,
            ttl=ttl
        )
        
        self.memory_cache[cache_key] = entry
        
        # 更新 LRU 順序
        if cache_key in self.access_order:
            self.access_order.remove(cache_key)
        self.access_order.append(cache_key)
        
        # 更新統計
        self.stats.total_entries = len(self.memory_cache)
    
    def _put_disk(self, cache_key: str, data: Any, ttl: float) -> None:
        """存入磁盤緩存"""
        try:
            cache_file = self.cache_dir / f"{cache_key}.cache"
            
            cache_data = {
                'data': data,
                'timestamp': time.time(),
                'ttl': ttl
            }
            
            with open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
                
        except Exception as e:
            print(f"磁盤緩存寫入失敗: {e}")
    
    def _get_from_disk(self, cache_key: str) -> Optional[Any]:
        """從磁盤緩存獲取"""
        try:
            cache_file = self.cache_dir / f"{cache_key}.cache"
            
            if not cache_file.exists():
                return None
            
            with open(cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            
            # 檢查是否過期
            if time.time() - cache_data['timestamp'] > cache_data['ttl']:
                # 刪除過期文件
                cache_file.unlink()
                return None
            
            return cache_data['data']
            
        except Exception as e:
            print(f"磁盤緩存讀取失敗: {e}")
            return None
    
    def _evict_lru(self) -> None:
        """清除最少使用的緩存條目"""
        if not self.access_order:
            return
        
        # 移除最舊的條目
        oldest_key = self.access_order.pop(0)
        if oldest_key in self.memory_cache:
            del self.memory_cache[oldest_key]
            self.stats.evictions += 1
    
    def _cleanup_worker(self) -> None:
        """清理工作執行緒"""
        while True:
            try:
                time.sleep(300)  # 每 5 分鐘清理一次
                self._cleanup_expired()
            except Exception as e:
                print(f"緩存清理錯誤: {e}")
    
    def _cleanup_expired(self) -> None:
        """清理過期的緩存條目"""
        with self.lock:
            # 清理記憶體緩存
            expired_keys = [
                key for key, entry in self.memory_cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self.memory_cache[key]
                if key in self.access_order:
                    self.access_order.remove(key)
            
            # 清理磁盤緩存
            if self.enable_disk_cache:
                self._cleanup_disk_cache()
            
            # 更新統計
            self.stats.total_entries = len(self.memory_cache)
    
    def _cleanup_disk_cache(self) -> None:
        """清理磁盤緩存"""
        try:
            for cache_file in self.cache_dir.glob("*.cache"):
                try:
                    with open(cache_file, 'rb') as f:
                        cache_data = pickle.load(f)
                    
                    # 檢查是否過期
                    if time.time() - cache_data['timestamp'] > cache_data['ttl']:
                        cache_file.unlink()
                        
                except Exception:
                    # 如果文件損壞，直接刪除
                    cache_file.unlink()
                    
        except Exception as e:
            print(f"磁盤緩存清理錯誤: {e}")
    
    def invalidate(self, tle_line1: str, tle_line2: str, 
                   prediction_time: Optional[datetime] = None) -> None:
        """
        使緩存失效
        
        Args:
            tle_line1: TLE 第一行
            tle_line2: TLE 第二行
            prediction_time: 預測時間，如果為 None 則清除所有相關緩存
        """
        with self.lock:
            if prediction_time is not None:
                # 清除特定時間的緩存
                cache_key = self._generate_cache_key(tle_line1, tle_line2, prediction_time)
                
                if cache_key in self.memory_cache:
                    del self.memory_cache[cache_key]
                    if cache_key in self.access_order:
                        self.access_order.remove(cache_key)
                
                if self.enable_disk_cache:
                    cache_file = self.cache_dir / f"{cache_key}.cache"
                    if cache_file.exists():
                        cache_file.unlink()
            else:
                # 清除所有相關緩存 (基於 TLE)
                tle_hash = hashlib.md5(f"{tle_line1}{tle_line2}".encode()).hexdigest()[:8]
                
                # 清除記憶體緩存
                keys_to_remove = [
                    key for key in self.memory_cache.keys()
                    if tle_hash in key
                ]
                
                for key in keys_to_remove:
                    del self.memory_cache[key]
                    if key in self.access_order:
                        self.access_order.remove(key)
                
                # 清除磁盤緩存
                if self.enable_disk_cache:
                    for cache_file in self.cache_dir.glob(f"*{tle_hash}*.cache"):
                        cache_file.unlink()
    
    def clear_all(self) -> None:
        """清除所有緩存"""
        with self.lock:
            self.memory_cache.clear()
            self.access_order.clear()
            
            if self.enable_disk_cache:
                for cache_file in self.cache_dir.glob("*.cache"):
                    cache_file.unlink()
            
            # 重置統計
            self.stats = CacheStats()
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取緩存統計資訊"""
        with self.lock:
            # 計算記憶體使用量
            memory_usage = sum(
                len(pickle.dumps(entry.data)) 
                for entry in self.memory_cache.values()
            )
            
            self.stats.memory_usage_bytes = memory_usage
            self.stats.total_entries = len(self.memory_cache)
            
            return {
                'hit_rate': self.stats.hit_rate,
                'hits': self.stats.hits,
                'misses': self.stats.misses,
                'evictions': self.stats.evictions,
                'total_entries': self.stats.total_entries,
                'memory_usage_mb': memory_usage / 1024 / 1024,
                'cache_efficiency': self._calculate_efficiency()
            }
    
    def _calculate_efficiency(self) -> float:
        """計算緩存效率"""
        if not self.memory_cache:
            return 0.0
        
        # 基於存取頻率和命中率計算效率
        total_accesses = sum(entry.access_count for entry in self.memory_cache.values())
        avg_accesses = total_accesses / len(self.memory_cache)
        
        # 效率 = 命中率 * 平均存取次數權重
        efficiency = self.stats.hit_rate * min(1.0, avg_accesses / 10.0)
        return efficiency

# 全局緩存實例
_orbit_cache_instance = None

def get_orbit_cache() -> OrbitCacheService:
    """獲取全局軌道緩存實例"""
    global _orbit_cache_instance
    if _orbit_cache_instance is None:
        _orbit_cache_instance = OrbitCacheService()
    return _orbit_cache_instance

# 使用示例
if __name__ == "__main__":
    # 創建緩存服務
    cache = OrbitCacheService()
    
    # 模擬軌道計算結果
    tle1 = "1 25544U 98067A   21001.00000000  .00002182  00000-0  40768-4 0  9990"
    tle2 = "2 25544  51.6461 339.2911 0002829  86.3372 273.9164 15.48919103123456"
    prediction_time = datetime.now(timezone.utc)
    
    result = {
        'latitude': 25.0,
        'longitude': 121.0,
        'altitude': 408.0,
        'velocity': {'x': 7.5, 'y': 0.0, 'z': 0.0}
    }
    
    # 存入緩存
    cache.put(tle1, tle2, prediction_time, result)
    
    # 從緩存獲取
    cached_result = cache.get(tle1, tle2, prediction_time)
    print(f"緩存結果: {cached_result}")
    
    # 獲取統計資訊
    stats = cache.get_stats()
    print(f"緩存統計: {stats}")
