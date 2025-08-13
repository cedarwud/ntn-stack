#!/usr/bin/env python3
"""
Phase 2.5 衛星數據池準備器
專注於建構時數據池準備，移除智能篩選邏輯

版本: v1.0.0
建立日期: 2025-08-10
目標: 準備充足且多樣化的衛星數據池
"""

import logging
import random
import math
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime

from unified_satellite_config import (
    UnifiedSatelliteConfig,
    ConstellationConfig,
    get_unified_config
)

logger = logging.getLogger(__name__)

class SatelliteDataPoolBuilder:
    """建構階段：準備充足的衛星數據池
    
    職責：
    1. 基礎數據有效性檢查 (TLE 格式、軌道合理性)
    2. 多樣性採樣確保衛星池的空間和時間分布
    3. 為每個星座準備充足的候選衛星
    
    不包含：
    - 智能篩選邏輯 (移至運行時選擇器)
    - 仰角計算和可見性判斷
    - 換手適用性評分
    """
    
    def __init__(self, config: Optional[UnifiedSatelliteConfig] = None):
        """
        初始化數據池準備器
        
        Args:
            config: 統一配置實例，None 時使用默認配置
        """
        self.config = config or get_unified_config()
        
        # 驗證配置
        validation_result = self.config.validate()
        if not validation_result.is_valid:
            raise ValueError(f"配置驗證失敗: {validation_result.errors}")
        
        logger.info(f"衛星數據池準備器初始化完成")
        logger.info(f"  配置版本: {self.config.version}")
        logger.info(f"  星座數量: {len(self.config.constellations)}")
        
        for name, constellation in self.config.constellations.items():
            logger.info(f"  {name}: 目標衛星池 {constellation.total_satellites} 顆")
    
    def build_satellite_pools_phase1_only(self, raw_satellite_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        """階段一專用：僅進行基本TLE有效性驗證，不做智能篩選
        
        ⚠️ 重要：此方法已修復為符合文檔要求的全量處理
        
        階段一職責：
        1. ✅ TLE格式基本驗證（移除損壞數據）
        2. ✅ 保留所有有效衛星進行SGP4計算
        3. ❌ 不做任何數量限制或智能篩選（移至階段二）
        
        Args:
            raw_satellite_data: 原始衛星數據 {constellation_name: [satellite_data]}
            
        Returns:
            有效衛星池 {constellation_name: [all_valid_satellites]} - 全量數據
        """
        pools = {}
        
        logger.info("🚀 開始階段一衛星池建構（全量處理模式）...")
        
        for constellation_name in raw_satellite_data.keys():
            raw_satellites = raw_satellite_data[constellation_name]
            logger.info(f"📡 處理 {constellation_name}: {len(raw_satellites)} 顆原始衛星")
            
            # 🔥 關鍵修復：僅進行基本TLE格式驗證，不做智能篩選
            valid_satellites = self._basic_tle_validation_only(raw_satellites, constellation_name)
            
            pools[constellation_name] = valid_satellites
            logger.info(f"  ✅ 階段一完成: {len(valid_satellites)} 顆有效衛星（保留全量進入SGP4計算）")
        
        # 總結統計
        total_valid_satellites = sum(len(pool) for pool in pools.values())
        total_raw_satellites = sum(len(satellites) for satellites in raw_satellite_data.values())
        
        logger.info(f"🎯 階段一全量處理完成:")
        logger.info(f"  原始衛星: {total_raw_satellites} 顆")
        logger.info(f"  有效衛星: {total_valid_satellites} 顆")
        logger.info(f"  有效率: {total_valid_satellites/total_raw_satellites*100:.1f}%")
        logger.info(f"  ⚠️  智能篩選將在階段二執行")
        
        return pools

    def _basic_tle_validation_only(self, satellites: List[Dict[str, Any]], constellation: str) -> List[Dict[str, Any]]:
        """階段一專用：僅進行基本TLE格式驗證
        
        檢查項目：
        1. ✅ TLE格式驗證（必要）
        2. ❌ 移除軌道參數範圍檢查（過於嚴格）
        3. ❌ 移除覆蓋潛力預判（屬於階段二智能篩選）
        """
        valid_satellites = []
        
        for satellite in satellites:
            try:
                # 僅檢查TLE格式有效性
                if self._validate_tle_format(satellite):
                    valid_satellites.append(satellite)
                    
            except Exception as e:
                logger.debug(f"TLE格式無效，跳過: {e}")
                continue
        
        success_rate = len(valid_satellites) / len(satellites) * 100 if satellites else 0
        logger.info(f"  {constellation} 基本格式驗證: {success_rate:.1f}% 通過")
        
        return valid_satellites

    # 保留原方法作為階段二使用（重命名）
    def build_satellite_pools_stage2_intelligent(self, phase1_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        """階段二專用：智能衛星篩選（從階段一移動過來）
        
        這個方法包含了原本錯誤放在階段一的智能篩選邏輯：
        1. 軌道參數合理性檢查
        2. 覆蓋潛力評估  
        3. 多樣性採樣
        4. 數量限制到目標配置
        
        應該被階段二的智能篩選系統調用
        """
        pools = {}
        
        logger.info("🎯 開始階段二智能篩選...")
        
        for constellation_name, constellation_config in self.config.constellations.items():
            if constellation_name not in phase1_data:
                logger.warning(f"未找到 {constellation_name} 的階段一數據，跳過")
                continue
            
            phase1_satellites = phase1_data[constellation_name]
            logger.info(f"🔍 階段二處理 {constellation_name}: {len(phase1_satellites)} 顆階段一衛星")
            
            # 智能篩選：軌道參數和覆蓋性檢查
            suitable_satellites = self._basic_filter_satellites(phase1_satellites, constellation_name)
            logger.info(f"  智能篩選後: {len(suitable_satellites)} 顆適合衛星")
            
            if len(suitable_satellites) == 0:
                logger.error(f"  {constellation_name}: 沒有適合的換手候選衛星！")
                pools[constellation_name] = []
                continue
            
            # 多樣性採樣到目標數量
            target_pool_size = constellation_config.total_satellites
            selected_pool = self._diverse_sampling(suitable_satellites, target_pool_size, constellation_name)
            
            pools[constellation_name] = selected_pool
            logger.info(f"  🎯 最終篩選結果: {len(selected_pool)} 顆高品質候選衛星")
        
        # 統計總結
        total_selected = sum(len(pool) for pool in pools.values())
        total_input = sum(len(satellites) for satellites in phase1_data.values())
        logger.info(f"✅ 階段二智能篩選完成: {total_input} → {total_selected} 顆衛星")
        
        return pools
    
    def build_satellite_pools(self, raw_satellite_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        """🔧 修復：統一入口方法，根據階段選擇正確的處理邏輯
        
        ⚠️ 重要：這個方法現在默認調用 Phase 1 全量處理
        如需 Stage 2 智能篩選，請直接調用 build_satellite_pools_stage2_intelligent()
        """
        logger.info("⚠️ 調用了通用 build_satellite_pools 方法，默認使用 Phase 1 全量處理")
        return self.build_satellite_pools_phase1_only(raw_satellite_data)
    
    def _basic_filter_satellites(self, satellites: List[Dict[str, Any]], constellation: str) -> List[Dict[str, Any]]:
        """基礎篩選 - 只檢查數據有效性，不做智能選擇
        
        檢查項目：
        1. TLE 格式驗證
        2. 軌道參數合理性檢查  
        3. 基本覆蓋範圍檢查
        """
        valid_satellites = []
        
        for satellite in satellites:
            try:
                # TLE 格式檢查
                if not self._validate_tle_format(satellite):
                    continue
                
                # 軌道參數檢查
                if not self._validate_orbital_parameters(satellite, constellation):
                    continue
                
                # 基本覆蓋檢查 (確保軌道能覆蓋觀測點)
                if not self._validate_coverage_potential(satellite):
                    continue
                
                valid_satellites.append(satellite)
                
            except Exception as e:
                logger.debug(f"衛星數據驗證失敗: {e}")
                continue
        
        success_rate = len(valid_satellites) / len(satellites) * 100 if satellites else 0
        logger.info(f"  {constellation} 基礎篩選成功率: {success_rate:.1f}%")
        
        return valid_satellites
    
    def _validate_tle_format(self, satellite: Dict[str, Any]) -> bool:
        """驗證 TLE 格式"""
        try:
            line1 = satellite.get('line1', '')
            line2 = satellite.get('line2', '')
            
            # 檢查行格式
            if not (line1.startswith('1 ') and line2.startswith('2 ')):
                return False
            
            # 檢查行長度
            if not (len(line1) >= 69 and len(line2) >= 69):
                return False
            
            # 檢查 NORAD ID 一致性
            norad_id1 = int(line1[2:7].strip())
            norad_id2 = int(line2[2:7].strip())
            
            if norad_id1 != norad_id2:
                return False
            
            # 檢查衛星名稱
            name = satellite.get('name', '')
            if not name or len(name.strip()) == 0:
                return False
            
            return True
            
        except (ValueError, IndexError, TypeError):
            return False
    
    def _validate_orbital_parameters(self, satellite: Dict[str, Any], constellation: str) -> bool:
        """驗證軌道參數合理性"""
        try:
            line2 = satellite.get('line2', '')
            
            # 提取軌道參數
            inclination = float(line2[8:16].strip())      # 軌道傾角
            eccentricity = float(f"0.{line2[26:33].strip()}")  # 偏心率
            mean_motion = float(line2[52:63].strip())     # 平均運動
            
            # 檢查軌道傾角 (0-180度)
            if not (0 <= inclination <= 180):
                return False
            
            # 檢查偏心率 (LEO 衛星應該接近圓軌道)
            if eccentricity > 0.1:  # 偏心率過高
                return False
            
            # 檢查平均運動 (LEO 衛星典型值)
            if not (10 < mean_motion < 20):  # 大約對應 550-1200km 高度
                return False
            
            # 星座特定檢查
            if constellation.lower() == 'starlink':
                # Starlink 軌道特性檢查
                if not (50 < inclination < 100):  # Starlink 主要傾角範圍
                    return False
                if not (14.5 < mean_motion < 16.0):  # Starlink 高度範圍
                    return False
            
            elif constellation.lower() == 'oneweb':
                # OneWeb 軌道特性檢查
                if not (80 < inclination < 90):  # OneWeb 極地軌道
                    return False
                if not (12.5 < mean_motion < 14.5):  # OneWeb 高度範圍
                    return False
            
            return True
            
        except (ValueError, IndexError):
            return False
    
    def _validate_coverage_potential(self, satellite: Dict[str, Any]) -> bool:
        """驗證基本覆蓋可能性 (不計算具體仰角)"""
        try:
            line2 = satellite.get('line2', '')
            inclination = float(line2[8:16].strip())
            
            # 觀測點緯度
            observer_lat = abs(self.config.observer.latitude)
            
            # 軌道能否覆蓋觀測點 (簡單幾何檢查)
            if inclination < observer_lat:
                return False  # 軌道傾角小於觀測點緯度，無法覆蓋
            
            return True
            
        except (ValueError, IndexError):
            return False
    
    def _diverse_sampling(self, satellites: List[Dict[str, Any]], target_count: int, constellation: str) -> List[Dict[str, Any]]:
        """多樣性採樣 - 確保衛星池的多樣性
        
        採樣策略：
        1. 軌道平面分散：盡可能選擇不同軌道平面的衛星
        2. 相位角分散：同一軌道平面內選擇不同相位的衛星
        3. 隨機採樣：在滿足分散性的前提下隨機選擇
        """
        if len(satellites) <= target_count:
            logger.info(f"  {constellation}: 衛星數量不足目標，返回所有有效衛星 ({len(satellites)} 顆)")
            return satellites[:]
        
        logger.info(f"  {constellation}: 從 {len(satellites)} 顆中採樣 {target_count} 顆")
        
        # 根據星座類型選擇採樣策略
        constellation_config = self.config.get_constellation_config(constellation)
        if not constellation_config:
            # 回退到簡單隨機採樣
            return self._simple_random_sampling(satellites, target_count)
        
        method = constellation_config.pool_selection_method
        
        if method == "diverse_orbital_sampling":
            return self._orbital_plane_sampling(satellites, target_count, constellation)
        elif method == "polar_coverage_sampling":
            return self._polar_coverage_sampling(satellites, target_count, constellation)
        else:
            return self._simple_random_sampling(satellites, target_count)
    
    def _orbital_plane_sampling(self, satellites: List[Dict[str, Any]], target_count: int, constellation: str) -> List[Dict[str, Any]]:
        """軌道平面分散採樣 (適用於 Starlink)"""
        try:
            # 按 RAAN (升交點赤經) 分組
            raan_groups = {}
            
            for satellite in satellites:
                line2 = satellite.get('line2', '')
                if len(line2) >= 25:
                    try:
                        raan = float(line2[17:25].strip())
                        # 將 RAAN 分組 (每 10 度一組)
                        raan_group = int(raan // 10) * 10
                        
                        if raan_group not in raan_groups:
                            raan_groups[raan_group] = []
                        raan_groups[raan_group].append(satellite)
                        
                    except ValueError:
                        continue
            
            if not raan_groups:
                return self._simple_random_sampling(satellites, target_count)
            
            # 從每個軌道平面組中選擇衛星
            selected = []
            group_keys = list(raan_groups.keys())
            satellites_per_group = max(1, target_count // len(group_keys))
            
            for group_key in group_keys:
                group_satellites = raan_groups[group_key]
                # 從每組中隨機選擇
                sample_size = min(satellites_per_group, len(group_satellites))
                selected.extend(random.sample(group_satellites, sample_size))
                
                if len(selected) >= target_count:
                    break
            
            # 如果還需要更多衛星，從剩餘衛星中補充
            if len(selected) < target_count:
                remaining_satellites = [s for s in satellites if s not in selected]
                needed = target_count - len(selected)
                if remaining_satellites and needed > 0:
                    additional = random.sample(remaining_satellites, 
                                             min(needed, len(remaining_satellites)))
                    selected.extend(additional)
            
            # 確保不超過目標數量
            if len(selected) > target_count:
                selected = selected[:target_count]
            
            logger.info(f"    軌道平面分散採樣: {len(raan_groups)} 個軌道組, 選擇 {len(selected)} 顆")
            return selected
            
        except Exception as e:
            logger.warning(f"軌道平面採樣失敗: {e}, 回退到隨機採樣")
            return self._simple_random_sampling(satellites, target_count)
    
    def _polar_coverage_sampling(self, satellites: List[Dict[str, Any]], target_count: int, constellation: str) -> List[Dict[str, Any]]:
        """極地覆蓋採樣 (適用於 OneWeb)"""
        try:
            # OneWeb 是極地軌道，重點是相位分散
            # 按平近點角 (Mean Anomaly) 分組來實現相位分散
            ma_groups = {}
            
            for satellite in satellites:
                line2 = satellite.get('line2', '')
                if len(line2) >= 69:
                    try:
                        mean_anomaly = float(line2[43:51].strip())
                        # 將平近點角分組 (每 30 度一組)
                        ma_group = int(mean_anomaly // 30) * 30
                        
                        if ma_group not in ma_groups:
                            ma_groups[ma_group] = []
                        ma_groups[ma_group].append(satellite)
                        
                    except ValueError:
                        continue
            
            if not ma_groups:
                return self._simple_random_sampling(satellites, target_count)
            
            # 從每個相位組中選擇衛星
            selected = []
            group_keys = list(ma_groups.keys())
            satellites_per_group = max(1, target_count // len(group_keys))
            
            for group_key in group_keys:
                group_satellites = ma_groups[group_key]
                sample_size = min(satellites_per_group, len(group_satellites))
                selected.extend(random.sample(group_satellites, sample_size))
                
                if len(selected) >= target_count:
                    break
            
            # 補充到目標數量
            if len(selected) < target_count:
                remaining_satellites = [s for s in satellites if s not in selected]
                needed = target_count - len(selected)
                if remaining_satellites and needed > 0:
                    additional = random.sample(remaining_satellites,
                                             min(needed, len(remaining_satellites)))
                    selected.extend(additional)
            
            # 確保不超過目標數量
            if len(selected) > target_count:
                selected = selected[:target_count]
            
            logger.info(f"    極地覆蓋採樣: {len(ma_groups)} 個相位組, 選擇 {len(selected)} 顆")
            return selected
            
        except Exception as e:
            logger.warning(f"極地覆蓋採樣失敗: {e}, 回退到隨機採樣")
            return self._simple_random_sampling(satellites, target_count)
    
    def _simple_random_sampling(self, satellites: List[Dict[str, Any]], target_count: int) -> List[Dict[str, Any]]:
        """簡單隨機採樣 (回退方法)"""
        sample_size = min(target_count, len(satellites))
        selected = random.sample(satellites, sample_size)
        logger.info(f"    隨機採樣: 選擇 {len(selected)} 顆衛星")
        return selected
    
    def get_pool_statistics(self, pools: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """獲取衛星池統計信息"""
        stats = {
            "total_constellations": len(pools),
            "total_satellites": sum(len(pool) for pool in pools.values()),
            "constellations": {}
        }
        
        for constellation_name, pool in pools.items():
            constellation_config = self.config.get_constellation_config(constellation_name)
            target_size = constellation_config.total_satellites if constellation_config else 0
            
            stats["constellations"][constellation_name] = {
                "pool_size": len(pool),
                "target_size": target_size,
                "completion_rate": len(pool) / target_size * 100 if target_size > 0 else 0,
                "satellites": [sat.get('name', 'unknown') for sat in pool[:5]]  # 前5顆衛星名稱
            }
        
        return stats


def create_satellite_data_pool_builder(config: Optional[UnifiedSatelliteConfig] = None) -> SatelliteDataPoolBuilder:
    """創建衛星數據池準備器的便利函數"""
    return SatelliteDataPoolBuilder(config)


if __name__ == "__main__":
    """數據池準備器測試腳本"""
    import json
    
    # 設置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("Phase 2.5 衛星數據池準備器測試")
    print("=" * 60)
    
    # 創建數據池準備器
    builder = create_satellite_data_pool_builder()
    
    # 模擬原始衛星數據
    mock_raw_data = {
        "starlink": [
            {
                "name": f"STARLINK-{1000+i}",
                "norad_id": 50000 + i,
                "line1": f"1 {50000+i:05d}U 21001A   21001.00000000  .00001000  00000-0  10000-4 0  999{i%10}",
                "line2": f"2 {50000+i:05d}  53.2000 100.0000 0001000  90.0000 270.0000 15.50000000    1{i%10}",
                "tle_date": "20250810"
            }
            for i in range(800)  # 模擬 800 顆 Starlink 衛星
        ],
        "oneweb": [
            {
                "name": f"ONEWEB-{100+i:04d}",
                "norad_id": 60000 + i,
                "line1": f"1 {60000+i:05d}U 21001A   21001.00000000  .00001000  00000-0  10000-4 0  999{i%10}",
                "line2": f"2 {60000+i:05d}  87.4000 {i*6%360:03d}.0000 0001000  {i*10%360:03d}.0000 {i*15%360:03d}.0000 13.50000000    1{i%10}",
                "tle_date": "20250810"
            }
            for i in range(200)  # 模擬 200 顆 OneWeb 衛星
        ]
    }
    
    print(f"模擬數據:")
    print(f"  Starlink: {len(mock_raw_data['starlink'])} 顆原始衛星")
    print(f"  OneWeb: {len(mock_raw_data['oneweb'])} 顆原始衛星")
    
    # 建構衛星池 - 修復：使用正確的 Phase 1 方法
    print(f"\n開始建構衛星數據池...")
    pools = builder.build_satellite_pools_phase1_only(mock_raw_data)
    
    # 獲取統計信息
    stats = builder.get_pool_statistics(pools)
    
    print(f"\n建構結果:")
    print(f"  總星座數: {stats['total_constellations']}")
    print(f"  總衛星數: {stats['total_satellites']}")
    
    for constellation, constellation_stats in stats["constellations"].items():
        print(f"\n  {constellation.upper()}:")
        print(f"    衛星池大小: {constellation_stats['pool_size']} 顆")
        print(f"    目標大小: {constellation_stats['target_size']} 顆")
        print(f"    完成率: {constellation_stats['completion_rate']:.1f}%")
        print(f"    範例衛星: {', '.join(constellation_stats['satellites'])}")
    
    print(f"\n" + "=" * 60)
    print("數據池準備器測試完成")
    print("=" * 60)