"""
信號品質緩存管理器

統一管理系統中所有信號品質計算結果的緩存，
避免在各階段重複計算相同的 RSRP 和信號品質指標。

作者: NTN Stack Team
版本: 1.0.0
創建日期: 2025-08-19
"""

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class SignalQualityEntry:
    """信號品質緩存條目"""
    satellite_id: str
    constellation: str
    elevation_deg: float
    rsrp_dbm: float
    snr_db: Optional[float] = None
    distance_km: Optional[float] = None
    calculation_timestamp: str = None
    calculation_method: str = "ITU-R_P.618_Ka_band"
    
    def __post_init__(self):
        if self.calculation_timestamp is None:
            self.calculation_timestamp = datetime.now(timezone.utc).isoformat()
    
    def get_cache_key(self) -> str:
        """生成緩存鍵值"""
        key_data = f"{self.satellite_id}_{self.constellation}_{self.elevation_deg:.1f}"
        return hashlib.md5(key_data.encode()).hexdigest()


@dataclass 
class SignalCalculationParams:
    """信號計算參數"""
    observer_lat: float
    observer_lon: float
    frequency_ghz: float = 12.0  # Ku頻段
    tx_power_dbm: float = 43.0   # 標準發射功率
    calculation_standard: str = "ITU-R_P.618_20GHz_Ka_band"


class SignalQualityCache:
    """
    信號品質緩存管理器
    
    負責管理信號品質計算結果的緩存，避免重複計算：
    1. Stage3 計算後存入緩存
    2. Stage5/6 需要時從緩存讀取
    3. 支援多種緩存策略 (記憶體、檔案、混合)
    """
    
    def __init__(self, cache_dir: str = "/app/data/signal_cache", 
                 cache_size_limit: int = 10000):
        """
        初始化信號品質緩存
        
        Args:
            cache_dir: 緩存檔案存儲目錄
            cache_size_limit: 記憶體緩存條目數量限制
        """
        self.cache_dir = Path(cache_dir)
        # 🚫 移除自動創建目錄 - signal_cache 功能未被使用
        # self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.cache_size_limit = cache_size_limit
        
        # 記憶體緩存 (快速存取)
        self._memory_cache: Dict[str, SignalQualityEntry] = {}
        
        # 緩存統計
        self._cache_stats = {
            "hits": 0,
            "misses": 0,
            "writes": 0,
            "cache_creation_time": datetime.now(timezone.utc).isoformat()
        }
        
        # 🚫 移除載入已存在緩存的邏輯 - 避免不必要的文件操作
        # self._load_existing_cache()
        
        logger.info("⚠️ 信號品質緩存管理器初始化 (未啟用模式)")
        logger.info(f"  緩存目錄: {self.cache_dir} (不會自動創建)")
        logger.info(f"  記憶體緩存限制: {self.cache_size_limit} 條目")
        logger.info(f"  現有緩存條目: {len(self._memory_cache)} 個 (未載入)")
    
    def get_cached_rsrp(self, satellite_id: str, constellation: str, 
                       elevation_deg: float) -> Optional[float]:
        """
        從緩存獲取 RSRP 值
        
        Args:
            satellite_id: 衛星ID
            constellation: 星座名稱
            elevation_deg: 仰角 (度)
        
        Returns:
            RSRP 值 (dBm) 或 None (如果未緩存)
        """
        cache_key = self._generate_cache_key(satellite_id, constellation, elevation_deg)
        
        # 優先從記憶體緩存查找
        if cache_key in self._memory_cache:
            self._cache_stats["hits"] += 1
            entry = self._memory_cache[cache_key]
            logger.debug(f"緩存命中: {satellite_id} @ {elevation_deg}° = {entry.rsrp_dbm} dBm")
            return entry.rsrp_dbm
        
        # 從檔案緩存查找
        file_cached_entry = self._load_from_file_cache(cache_key)
        if file_cached_entry:
            # 載入到記憶體緩存
            self._memory_cache[cache_key] = file_cached_entry
            self._cache_stats["hits"] += 1
            logger.debug(f"檔案緩存命中: {satellite_id} @ {elevation_deg}° = {file_cached_entry.rsrp_dbm} dBm")
            return file_cached_entry.rsrp_dbm
        
        # 緩存未命中
        self._cache_stats["misses"] += 1
        logger.debug(f"緩存未命中: {satellite_id} @ {elevation_deg}°")
        return None
    
    def cache_rsrp_calculation(self, satellite_id: str, constellation: str,
                              elevation_deg: float, rsrp_dbm: float,
                              distance_km: Optional[float] = None,
                              snr_db: Optional[float] = None) -> None:
        """
        緩存 RSRP 計算結果
        
        Args:
            satellite_id: 衛星ID
            constellation: 星座名稱
            elevation_deg: 仰角 (度)
            rsrp_dbm: RSRP 值 (dBm)
            distance_km: 距離 (公里)
            snr_db: 信噪比 (dB)
        """
        entry = SignalQualityEntry(
            satellite_id=satellite_id,
            constellation=constellation,
            elevation_deg=elevation_deg,
            rsrp_dbm=rsrp_dbm,
            distance_km=distance_km,
            snr_db=snr_db
        )
        
        cache_key = entry.get_cache_key()
        
        # 存入記憶體緩存
        self._memory_cache[cache_key] = entry
        self._cache_stats["writes"] += 1
        
        # 檢查記憶體緩存大小限制
        if len(self._memory_cache) > self.cache_size_limit:
            self._evict_oldest_entries()
        
        # 異步存入檔案緩存
        self._save_to_file_cache(cache_key, entry)
        
        logger.debug(f"緩存寫入: {satellite_id} @ {elevation_deg}° = {rsrp_dbm} dBm")
    
    def batch_cache_satellite_signals(self, satellite_data: Dict[str, Any], 
                                     calculation_params: SignalCalculationParams) -> Dict[str, Any]:
        """
        批次緩存衛星信號計算結果 (用於 Stage3 完成後的批次存儲)
        
        Args:
            satellite_data: 包含信號計算結果的衛星數據
            calculation_params: 計算參數
        
        Returns:
            緩存統計結果
        """
        cached_count = 0
        skipped_count = 0
        
        logger.info("📦 開始批次緩存衛星信號計算結果")
        
        for constellation, data in satellite_data.get('constellations', {}).items():
            satellites = data.get('satellites', [])
            
            for satellite in satellites:
                satellite_id = satellite.get('satellite_id')
                if not satellite_id:
                    continue
                
                # 緩存多個仰角的信號數據
                signal_quality = satellite.get('signal_quality', {})
                rsrp_by_elevation = signal_quality.get('rsrp_by_elevation', {})
                
                for elev_key, rsrp_value in rsrp_by_elevation.items():
                    # 解析仰角值 (格式: "elev_5deg" -> 5.0)
                    try:
                        elevation = float(elev_key.replace('elev_', '').replace('deg', ''))
                        
                        # 檢查是否已緩存
                        existing_rsrp = self.get_cached_rsrp(satellite_id, constellation, elevation)
                        if existing_rsrp is None:
                            # 緩存新的計算結果
                            self.cache_rsrp_calculation(
                                satellite_id=satellite_id,
                                constellation=constellation,
                                elevation_deg=elevation,
                                rsrp_dbm=rsrp_value,
                                distance_km=satellite.get('range_km'),
                                snr_db=signal_quality.get('snr_estimate_db')
                            )
                            cached_count += 1
                        else:
                            skipped_count += 1
                    except (ValueError, TypeError) as e:
                        logger.warning(f"無法解析仰角鍵值 {elev_key}: {e}")
                        continue
        
        result = {
            "cached_entries": cached_count,
            "skipped_entries": skipped_count,
            "total_cache_size": len(self._memory_cache),
            "cache_hit_rate": self._calculate_hit_rate()
        }
        
        logger.info(f"✅ 批次緩存完成: {cached_count} 新增, {skipped_count} 跳過")
        return result
    
    def get_cached_satellite_signals(self, satellite_id: str, constellation: str,
                                   elevation_angles: List[float]) -> Dict[str, Optional[float]]:
        """
        批次獲取衛星在多個仰角的緩存信號數據
        
        Args:
            satellite_id: 衛星ID
            constellation: 星座名稱
            elevation_angles: 仰角列表
        
        Returns:
            仰角與 RSRP 的映射字典
        """
        results = {}
        
        for elevation in elevation_angles:
            rsrp = self.get_cached_rsrp(satellite_id, constellation, elevation)
            results[f"elev_{int(elevation)}deg"] = rsrp
        
        return results
    
    def clear_cache(self, older_than_hours: Optional[int] = None) -> Dict[str, int]:
        """
        清理緩存
        
        Args:
            older_than_hours: 清理超過指定小時的緩存，None表示清理全部
        
        Returns:
            清理統計結果
        """
        if older_than_hours is None:
            # 清理全部
            memory_cleared = len(self._memory_cache)
            self._memory_cache.clear()
            
            # 清理檔案緩存
            file_cleared = 0
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
                file_cleared += 1
            
            logger.info(f"🗑️ 清理全部緩存: 記憶體 {memory_cleared} 個, 檔案 {file_cleared} 個")
            
        else:
            # 清理過期緩存
            cutoff_time = datetime.now(timezone.utc).timestamp() - (older_than_hours * 3600)
            memory_cleared = 0
            file_cleared = 0
            
            # 清理記憶體緩存
            keys_to_remove = []
            for key, entry in self._memory_cache.items():
                entry_time = datetime.fromisoformat(entry.calculation_timestamp.replace('Z', '+00:00')).timestamp()
                if entry_time < cutoff_time:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self._memory_cache[key]
                memory_cleared += 1
            
            # 清理檔案緩存
            for cache_file in self.cache_dir.glob("*.json"):
                if cache_file.stat().st_mtime < cutoff_time:
                    cache_file.unlink()
                    file_cleared += 1
            
            logger.info(f"🗑️ 清理過期緩存 ({older_than_hours}小時): 記憶體 {memory_cleared} 個, 檔案 {file_cleared} 個")
        
        return {
            "memory_cleared": memory_cleared,
            "file_cleared": file_cleared,
            "remaining_memory_entries": len(self._memory_cache)
        }
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """獲取緩存統計信息"""
        return {
            **self._cache_stats,
            "memory_cache_size": len(self._memory_cache),
            "file_cache_directory": str(self.cache_dir),
            "cache_hit_rate": self._calculate_hit_rate(),
            "memory_usage_estimate_mb": len(self._memory_cache) * 0.001,  # 粗略估算
        }
    
    def _generate_cache_key(self, satellite_id: str, constellation: str, elevation_deg: float) -> str:
        """生成緩存鍵值"""
        key_data = f"{satellite_id}_{constellation}_{elevation_deg:.1f}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _load_existing_cache(self) -> None:
        """載入現有的檔案緩存到記憶體"""
        cache_files = list(self.cache_dir.glob("*.json"))
        loaded_count = 0
        
        for cache_file in cache_files:
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                
                entry = SignalQualityEntry(**data)
                cache_key = entry.get_cache_key()
                self._memory_cache[cache_key] = entry
                loaded_count += 1
                
                # 檢查記憶體限制
                if len(self._memory_cache) >= self.cache_size_limit:
                    break
                    
            except Exception as e:
                logger.warning(f"載入緩存檔案失敗 {cache_file}: {e}")
        
        if loaded_count > 0:
            logger.info(f"📂 載入現有緩存: {loaded_count} 個條目")
    
    def _save_to_file_cache(self, cache_key: str, entry: SignalQualityEntry) -> None:
        """保存緩存條目到檔案"""
        try:
            cache_file = self.cache_dir / f"{cache_key}.json"
            with open(cache_file, 'w') as f:
                json.dump(asdict(entry), f, indent=2)
        except Exception as e:
            logger.warning(f"保存緩存檔案失敗 {cache_key}: {e}")
    
    def _load_from_file_cache(self, cache_key: str) -> Optional[SignalQualityEntry]:
        """從檔案載入緩存條目"""
        try:
            cache_file = self.cache_dir / f"{cache_key}.json"
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                return SignalQualityEntry(**data)
        except Exception as e:
            logger.warning(f"載入緩存檔案失敗 {cache_key}: {e}")
        
        return None
    
    def _evict_oldest_entries(self) -> None:
        """移除最舊的緩存條目 (LRU策略)"""
        if len(self._memory_cache) <= self.cache_size_limit:
            return
        
        # 簡單的FIFO策略：移除10%的條目
        entries_to_remove = len(self._memory_cache) - int(self.cache_size_limit * 0.9)
        keys_to_remove = list(self._memory_cache.keys())[:entries_to_remove]
        
        for key in keys_to_remove:
            del self._memory_cache[key]
        
        logger.debug(f"🗑️ 緩存清理: 移除 {len(keys_to_remove)} 個舊條目")
    
    def _calculate_hit_rate(self) -> float:
        """計算緩存命中率"""
        total_requests = self._cache_stats["hits"] + self._cache_stats["misses"]
        if total_requests == 0:
            return 0.0
        return self._cache_stats["hits"] / total_requests


# 全局實例 (單例模式)
_global_signal_cache = None

def get_signal_quality_cache() -> SignalQualityCache:
    """獲取全局信號品質緩存實例"""
    global _global_signal_cache
    if _global_signal_cache is None:
        # 🔧 修復：智能檢測環境，使用正確的路徑
        import os
        if os.path.exists("/app"):
            # 容器內環境
            cache_dir = "/app/data/signal_cache"
        else:
            # 主機環境
            cache_dir = "/home/sat/ntn-stack/data/signal_cache"
        
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir, exist_ok=True)
        _global_signal_cache = SignalQualityCache(cache_dir=cache_dir)
    return _global_signal_cache


# 便捷函數
def get_cached_rsrp(satellite_id: str, constellation: str, elevation_deg: float) -> Optional[float]:
    """快速獲取緩存的 RSRP 值"""
    return get_signal_quality_cache().get_cached_rsrp(satellite_id, constellation, elevation_deg)

def cache_rsrp_result(satellite_id: str, constellation: str, elevation_deg: float, rsrp_dbm: float) -> None:
    """快速緩存 RSRP 結果"""
    get_signal_quality_cache().cache_rsrp_calculation(satellite_id, constellation, elevation_deg, rsrp_dbm)


if __name__ == "__main__":
    # 測試信號品質緩存
    cache = get_signal_quality_cache()
    
    print("🧪 測試信號品質緩存管理器")
    print("=" * 50)
    
    # 測試緩存寫入
    cache.cache_rsrp_calculation("STARLINK-1234", "starlink", 15.0, -85.5, distance_km=1200.5)
    cache.cache_rsrp_calculation("ONEWEB-5678", "oneweb", 20.0, -78.2, distance_km=950.0)
    
    # 測試緩存讀取
    rsrp1 = cache.get_cached_rsrp("STARLINK-1234", "starlink", 15.0)
    rsrp2 = cache.get_cached_rsrp("ONEWEB-5678", "oneweb", 20.0)
    rsrp3 = cache.get_cached_rsrp("UNKNOWN-9999", "starlink", 10.0)  # 應該返回 None
    
    print(f"Starlink-1234 @ 15°: {rsrp1} dBm")
    print(f"OneWeb-5678 @ 20°: {rsrp2} dBm")
    print(f"Unknown-9999 @ 10°: {rsrp3}")
    
    # 測試批次獲取
    batch_results = cache.get_cached_satellite_signals("STARLINK-1234", "starlink", [10.0, 15.0, 30.0])
    print(f"批次查詢結果: {batch_results}")
    
    # 測試統計
    stats = cache.get_cache_statistics()
    print(f"緩存統計: 命中率 {stats['cache_hit_rate']:.2%}, 條目數 {stats['memory_cache_size']}")
    
    print("\n✅ 信號品質緩存管理器測試完成")