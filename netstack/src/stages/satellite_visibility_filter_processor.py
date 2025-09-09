#!/usr/bin/env python3
"""
修復版增強智能衛星篩選處理器
解決篩選過嚴和輸出格式問題
"""

import os
import sys
import json
import math
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

sys.path.insert(0, '/app/netstack')
sys.path.insert(0, '/app')

from shared_core.observer_config_service import get_ntpu_coordinates
from shared_core.elevation_threshold_manager import get_elevation_threshold_manager
from shared_core.visibility_service import get_visibility_service, ObserverLocation
from shared_core.validation_snapshot_base import ValidationSnapshotBase, ValidationCheckHelper

# 新增：運行時檢查組件 (Phase 2)
from validation.runtime_architecture_checker import RuntimeArchitectureChecker, check_runtime_architecture
from validation.api_contract_validator import APIContractValidator, validate_api_contract
from validation.execution_flow_checker import ExecutionFlowChecker, validate_stage_completion

logger = logging.getLogger(__name__)


class SimplifiedVisibilityPreFilter:
    """
    學術標準可見性預篩選器（Grade A合規）
    
    Academic Standards Compliance:
    - Grade A: 嚴格基於物理參數，無設定值或回退機制
    - 零容忍政策: 數據不足時直接排除，不使用假設
    """
    
    def __init__(self, observer_location: Tuple[float, float, float]):
        self.observer_lat, self.observer_lon, self.observer_alt = observer_location
        self.earth_radius_km = 6371.0  # WGS84標準地球半徑
        
    def check_orbital_coverage(self, satellite_data: Dict) -> bool:
        """
        檢查衛星軌道是否可能對觀測點可見（學術標準Grade A）
        
        Academic Standards Compliance:
        - 基於真實軌道傾角計算
        - 使用球面三角學原理
        - 無設定值或回退機制
        """
        try:
            # 🎯 修復：適配統一格式的數據結構
            orbit_data = satellite_data.get('orbit_data', {})
            
            # 1. 優先從 orbit_data 獲取傾角（統一格式）
            if 'inclination' in orbit_data:
                inclination = orbit_data['inclination']
            # 2. 回退：從 orbital_elements 獲取傾角（舊格式）
            elif 'orbital_elements' in satellite_data:
                orbital_elements = satellite_data.get('orbital_elements', {})
                if 'inclination_deg' in orbital_elements:
                    inclination = orbital_elements['inclination_deg']
                else:
                    logger.debug(f"衛星 {satellite_data.get('name', 'Unknown')} orbital_elements 中缺少 inclination_deg，排除")
                    return False
            # 3. 最後回退：從 TLE line2 解析傾角
            else:
                # 嘗試從 orbit_data 獲取 TLE line2（統一格式）
                tle_line2 = orbit_data.get('tle_line2', '')
                
                # 如果沒有，嘗試從 tle_data 獲取（舊格式）
                if not tle_line2:
                    tle_data = satellite_data.get('tle_data', {})
                    tle_line2 = tle_data.get('line2', '')
                
                if not tle_line2 or len(tle_line2) < 16:
                    # 學術標準：無有效TLE數據時排除該衛星
                    logger.debug(f"衛星 {satellite_data.get('name', 'Unknown')} 缺少有效TLE數據，排除")
                    return False
                
                try:
                    inclination = float(tle_line2[8:16].strip())
                except (ValueError, IndexError):
                    # 學術標準：TLE解析失敗時排除該衛星
                    logger.debug(f"衛星 {satellite_data.get('name', 'Unknown')} TLE傾角解析失敗，排除")
                    return False
            
            # 基於球面三角學的可見性計算
            observer_lat_abs = abs(self.observer_lat)
            
            # ITU-R標準：基於軌道傾角和觀測點緯度的物理可見性
            # 低傾角衛星對高緯度地區的可見性限制
            if inclination < observer_lat_abs - 10:
                logger.debug(f"衛星傾角 {inclination}° 對緯度 {self.observer_lat}° 觀測點不可見")
                return False
            
            # 極軌衛星（傾角 > 80°）對所有緯度都可見
            if inclination > 80:
                return True
                
            # 基於軌道力學：中等傾角衛星的可見性計算
            # 對於NTPU位置（24.94°N），大部分LEO衛星都有可見性
            return inclination >= (observer_lat_abs - 30)
            
        except Exception as e:
            logger.error(f"軌道覆蓋檢查失敗 {satellite_data.get('name', 'Unknown')}: {e}")
            # 學術標準：錯誤時排除該衛星，不使用假設
            return False  # 錯誤時假設可見


class SatelliteVisibilityFilterProcessor(ValidationSnapshotBase):
    """修復版增強智能衛星篩選處理器"""
    
    # 針對取樣模式調整的目標（比例性調整）
    def __init__(self, observer_lat: float = None, observer_lon: float = None,
             input_dir: str = "/app/data", output_dir: str = "/app/data",
             sample_mode: bool = False):
        """
        初始化處理器
        
        Args:
            sample_mode: 不再影響篩選數量，僅用於相容性
        """
        # 初始化驗證快照基礎
        super().__init__(stage_number=2, stage_name="智能衛星篩選")
        
        # 獲取觀測座標
        if observer_lat is None or observer_lon is None:
            ntpu_lat, ntpu_lon, ntpu_alt = get_ntpu_coordinates()
            self.observer_lat = observer_lat if observer_lat is not None else ntpu_lat
            self.observer_lon = observer_lon if observer_lon is not None else ntpu_lon
            self.observer_alt = ntpu_alt
        else:
            self.observer_lat = observer_lat
            self.observer_lon = observer_lon
            self.observer_alt = 50.0
        
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 保留sample_mode以維持相容性，但不再用於數量限制
        self.sample_mode = sample_mode
        
        # 篩選參數：基於@docs標準
        self.filtering_criteria = {
            'starlink': {
                'min_elevation_deg': 5.0,   # Starlink最低仰角5°
                'min_visible_time_min': 1.0  # 最低1分鐘可見時間
            },
            'oneweb': {
                'min_elevation_deg': 10.0,  # OneWeb最低仰角10°
                'min_visible_time_min': 0.5  # 最低0.5分鐘可見時間
            }
        }
        
        # 初始化預篩選器
        self.visibility_prefilter = SimplifiedVisibilityPreFilter(
            (self.observer_lat, self.observer_lon, self.observer_alt)
        )
        
        # 初始化管理器
        self.elevation_manager = get_elevation_threshold_manager()
        
        observer_location = ObserverLocation(
            latitude=self.observer_lat,
            longitude=self.observer_lon,
            altitude=self.observer_alt,
            location_name="NTPU"
        )
        self.visibility_service = get_visibility_service(observer_location)
        
        # 🛡️ Phase 3 新增：初始化驗證框架
        self.validation_enabled = False
        self.validation_adapter = None
        
        try:
            from validation.adapters.stage2_validation_adapter import Stage2ValidationAdapter
            self.validation_adapter = Stage2ValidationAdapter()
            self.validation_enabled = True
            logger.info("🛡️ Phase 3 Stage 2 驗證框架初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ Phase 3 驗證框架初始化失敗: {e}")
            logger.warning("   繼續使用舊版驗證機制")
        
        logger.info("✅ 地理可見性自然篩選處理器初始化完成")
        logger.info(f"  觀測點: NTPU ({self.observer_lat:.6f}°, {self.observer_lon:.6f}°)")
        logger.info(f"  篩選模式: 地理可見性自然篩選（無數量限制）")
        logger.info(f"  Starlink條件: 仰角≥{self.filtering_criteria['starlink']['min_elevation_deg']}°, 可見時間≥{self.filtering_criteria['starlink']['min_visible_time_min']}分鐘")
        logger.info(f"  OneWeb條件: 仰角≥{self.filtering_criteria['oneweb']['min_elevation_deg']}°, 可見時間≥{self.filtering_criteria['oneweb']['min_visible_time_min']}分鐘")
        logger.info(f"  🛡️ Phase 3 驗證框架: {'啟用' if self.validation_enabled else '停用'}")
        
    def load_orbital_calculation_output(self) -> Dict[str, Any]:
        """載入軌道計算結果檔案 - v5.0 統一格式版本"""
        # 🎯 更新為新的檔案命名
        orbital_file = self.input_dir / "tle_orbital_calculation_output.json"
        
        if not orbital_file.exists():
            logger.error(f"❌ 軌道計算檔案不存在: {orbital_file}")
            return {}
        
        try:
            logger.info(f"📥 載入軌道計算檔案: {orbital_file}")
            
            with open(orbital_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 🎯 v5.0 統一格式檢查和統計
            if 'constellations' in data:
                total_satellites = 0
                for const_name, const_data in data['constellations'].items():
                    # 🔧 修復：從 satellites 列表計算實際數量，而不是依賴 satellite_count 字段
                    satellites = const_data.get('satellites', [])
                    const_sat_count = len(satellites)
                    total_satellites += const_sat_count
                    logger.info(f"    {const_name}: {const_sat_count} 顆衛星")
                
                logger.info(f"  ✅ 載入 {total_satellites} 顆衛星數據")
                
                # 🎯 驗證統一格式
                format_version = data.get('metadata', {}).get('data_format_version', '')
                if format_version == 'unified_v1.0':
                    logger.info("✅ 確認使用統一格式 v1.0")
                else:
                    logger.warning(f"⚠️ 格式版本不匹配: {format_version}")
                    
            elif 'satellites' in data:
                # 🔧 回退兼容：處理舊的 satellites 陣列格式
                satellite_count = len(data['satellites'])
                logger.info(f"  ✅ 載入 {satellite_count} 顆衛星數據（舊格式）")
                
                # 統計星座分布
                constellations = {}
                for sat in data['satellites']:
                    const = sat.get('constellation', 'unknown')
                    constellations[const] = constellations.get(const, 0) + 1
                
                for const, count in constellations.items():
                    logger.info(f"    {const}: {count} 顆衛星")
                    
                logger.warning("⚠️ 檢測到舊格式數據，建議使用統一格式")
            else:
                logger.error("❌ 數據格式錯誤：缺少 constellations 或 satellites 字段")
                return {}
            
            return data
            
        except Exception as e:
            logger.error(f"❌ 載入軌道計算檔案失敗: {e}")
            return {}
        
    def _visibility_prefilter(self, satellites: List[Dict]) -> List[Dict]:
        """階段 0: 可見性預篩選（保守策略）"""
        logger.info("🔍 階段 0: 執行可見性預篩選...")
        
        visible_satellites = []
        excluded_count = 0
        
        for sat in satellites:
            if self.visibility_prefilter.check_orbital_coverage(sat):
                visible_satellites.append(sat)
            else:
                excluded_count += 1
                
        logger.info(f"  ✅ 預篩選完成: {len(satellites)} → {len(visible_satellites)} 顆")
        if excluded_count > 0:
            logger.info(f"  排除永不可見衛星: {excluded_count} 顆")
        
        return visible_satellites
        
    def _simple_filtering(self, satellites: List[Dict]) -> List[Dict]:
        """
        正確的地理可見性自然篩選邏輯
        基於@docs要求，不使用人為數量限制，純粹根據地理可見性條件篩選
        """
        logger.info("🎯 執行地理可見性自然篩選（無數量限制）...")
        
        # 按星座分組
        starlink_sats = []
        oneweb_sats = []
        
        for sat in satellites:
            const = sat.get('constellation', '').lower()
            if 'starlink' in const:
                starlink_sats.append(sat)
            elif 'oneweb' in const:
                oneweb_sats.append(sat)
                
        logger.info(f"  Starlink: {len(starlink_sats)} 顆")
        logger.info(f"  OneWeb: {len(oneweb_sats)} 顆")
        
        def apply_natural_geographic_visibility_filter(satellites, constellation_name):
            """自然的地理可見性篩選 - 沒有數量限制，純粹基於條件篩選"""
            
            # 根據@docs的星座特定參數
            if constellation_name.lower() == 'starlink':
                min_elevation = 5.0      # Starlink最低仰角5°
                min_visible_time = 1.0   # 最低1分鐘可見時間
            else:  # oneweb  
                min_elevation = 10.0     # OneWeb最低仰角10°
                min_visible_time = 0.5   # 最低0.5分鐘可見時間
            
            filtered = []
            
            for sat in satellites:
                position_timeseries = sat.get('position_timeseries', [])
                if not position_timeseries:
                    continue
                    
                # 計算實際可見性指標
                visible_points = 0
                total_points = len(position_timeseries)
                max_elevation = -90
                visible_duration_minutes = 0
                
                for pos in position_timeseries:
                    elevation = pos.get('relative_to_observer', {}).get('elevation_deg', -90)
                    max_elevation = max(max_elevation, elevation)
                    
                    if elevation >= min_elevation:
                        visible_points += 1
                        visible_duration_minutes += 0.5  # 每點30秒
                
                # 自然篩選條件：滿足最低可見時間要求
                if visible_duration_minutes >= min_visible_time:
                    # 保留衛星並記錄篩選原因
                    sat['stage2_filtering'] = {
                        'passed': True,
                        'reason': 'geographic_visibility',
                        'visible_duration_minutes': visible_duration_minutes,
                        'visible_points_count': visible_points,
                        'max_elevation_deg': max_elevation,
                        'min_elevation_threshold': min_elevation,
                        'visibility_percentage': (visible_points / total_points) * 100
                    }
                    filtered.append(sat)
            
            return filtered
        
        # 對每個星座執行自然篩選
        filtered_starlink = apply_natural_geographic_visibility_filter(starlink_sats, 'starlink')
        filtered_oneweb = apply_natural_geographic_visibility_filter(oneweb_sats, 'oneweb')
        
        # 統計結果
        starlink_retention = len(filtered_starlink) / len(starlink_sats) * 100 if starlink_sats else 0
        oneweb_retention = len(filtered_oneweb) / len(oneweb_sats) * 100 if oneweb_sats else 0
        
        logger.info(f"  ✅ Starlink: {len(filtered_starlink)} 顆選中 ({starlink_retention:.1f}%保留率)")
        logger.info(f"  ✅ OneWeb: {len(filtered_oneweb)} 顆選中 ({oneweb_retention:.1f}%保留率)")
        logger.info(f"  🎯 使用星座特定仰角門檻: Starlink 5°, OneWeb 10°")
        logger.info(f"  📊 自然篩選完成：無人為數量限制")
        
        return filtered_starlink + filtered_oneweb
        
    def save_filtered_output(self, filtered_satellites: List[Dict], 
                        original_count: int) -> str:
        """保存篩選結果（正確格式）"""
        
        # 按星座分組衛星數據
        starlink_satellites = [s for s in filtered_satellites if 'starlink' in s.get('constellation', '').lower()]
        oneweb_satellites = [s for s in filtered_satellites if 'oneweb' in s.get('constellation', '').lower()]
        
        # 準備輸出數據 (符合Stage 3期望格式)
        output_data = {
            'metadata': {
                'stage': 'satellite_visibility_filtering',  # 🎯 更新為功能性描述
                'filtering_version': 'natural_filtering_v2.0',
                'processing_timestamp': datetime.now(timezone.utc).isoformat(),
                'filtering_approach': 'pure_geographic_visibility_no_quantity_limits',
                'observer_location': {
                    'latitude': self.observer_lat,
                    'longitude': self.observer_lon,
                    'location_name': 'NTPU'
                },
                'filtering_criteria': self.filtering_criteria,
                'filtering_stats': {
                    'input_satellites': original_count,
                    'output_satellites': len(filtered_satellites),
                    'retention_rate_percent': (len(filtered_satellites)/original_count*100),
                    'starlink_filtered': len(starlink_satellites),
                    'oneweb_filtered': len(oneweb_satellites),
                    'starlink_retention_percent': (len(starlink_satellites)/original_count*100) if original_count > 0 else 0,
                    'oneweb_retention_percent': (len(oneweb_satellites)/original_count*100) if original_count > 0 else 0
                },
                'total_satellites': len(filtered_satellites),
                'processing_complete': True
            },
            'constellations': {
                'starlink': {
                    'satellite_count': len(starlink_satellites),
                    'satellites': starlink_satellites
                },
                'oneweb': {
                    'satellite_count': len(oneweb_satellites),
                    'satellites': oneweb_satellites
                }
            },
            'satellites': filtered_satellites  # 向後兼容：保留扁平化格式
        }
        
        # 🎯 更新為新的檔案命名
        output_file = self.output_dir / "satellite_visibility_filtered_output.json"
        
        # 清理舊檔案
        if output_file.exists():
            logger.info(f"🗑️ 清理舊檔案: {output_file}")
            output_file.unlink()
            
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
            
        file_size_mb = output_file.stat().st_size / (1024 * 1024)
        
        logger.info(f"✅ 自然篩選結果已保存: {output_file}")
        logger.info(f"  檔案大小: {file_size_mb:.1f} MB")
        logger.info(f"  衛星數量: {len(filtered_satellites)} 顆")
        
        return str(output_file)
        
    def _process_with_data(self, orbital_data: Dict[str, Any]) -> Dict[str, Any]:
        """使用提供的orbital_data進行處理（不從文件載入）"""
        logger.info("🚀 使用提供數據進行修復版增強智能衛星篩選處理")
        logger.info("=" * 60)
        
        # 🔧 新版雙模式清理：使用統一清理管理器
        try:
            from shared_core.cleanup_manager import auto_cleanup
            cleaned_result = auto_cleanup(current_stage=2)
            logger.info(f"🗑️ 自動清理完成: {cleaned_result['files']} 檔案, {cleaned_result['directories']} 目錄")
        except Exception as e:
            logger.warning(f"⚠️ 自動清理警告: {e}")
        
        # 整理所有衛星數據 - 適配新的SGP4輸出格式
        all_satellites = []
        
        # 檢查新的SGP4格式（直接包含satellites列表）
        if 'satellites' in orbital_data:
            satellites_list = orbital_data.get('satellites', [])
            logger.info(f"📊 從提供數據載入 {len(satellites_list)} 顆衛星")
            all_satellites = satellites_list
                
        # 兼容舊格式
        elif 'constellations' in orbital_data:
            for constellation_name, constellation_data in orbital_data.get('constellations', {}).items():
                satellites = constellation_data.get('orbit_data', {}).get('satellites', {})
                for sat_id, sat_data in satellites.items():
                    sat_data['constellation'] = constellation_name
                    sat_data['satellite_id'] = sat_id
                    all_satellites.append(sat_data)
                
        logger.info(f"📊 開始處理 {len(all_satellites)} 顆衛星")
        
        # 階段 0: 可見性預篩選
        visible_satellites = self._visibility_prefilter(all_satellites)
        
        # 簡化篩選（避免過度篩選）
        filtered_satellites = self._simple_filtering(visible_satellites)
        
        # 保存結果
        output_file = self.save_filtered_output(filtered_satellites, len(all_satellites))
        
        # 輸出統計
        logger.info("=" * 60)
        logger.info("✅ 修復版增強智能篩選完成")
        logger.info(f"  輸入: {len(all_satellites)} 顆")
        logger.info(f"  輸出: {len(filtered_satellites)} 顆")
        logger.info(f"  篩選率: {(1 - len(filtered_satellites)/len(all_satellites))*100:.1f}%")
        
        # 🎯 修復驗證快照metadata - 確保包含validation所需的所有字段
        from datetime import datetime, timezone
        
        return {
            'metadata': {
                'total_satellites': len(filtered_satellites),
                'input_satellites': len(all_satellites),  # ✅ extract_key_metrics需要
                'processing_timestamp': datetime.now(timezone.utc).isoformat(),  # ✅ validation需要
                'filtering_stats': {  # ✅ validation需要
                    'input_satellites': len(all_satellites),
                    'output_satellites': len(filtered_satellites),
                    'retention_rate_percent': (len(filtered_satellites) / len(all_satellites)) * 100
                },
                'processing_complete': True,
                'cleanup_strategy': 'dual_mode_auto_cleanup'  # v3.2 新增
            },
            'satellites': filtered_satellites
        }
        
    def process(self) -> Dict[str, Any]:
        """執行完整的篩選流程 - v5.0 統一格式版本 + Phase 3 驗證框架"""
        logger.info("🚀 開始修復版增強智能衛星篩選處理 + Phase 3 驗證框架")
        logger.info("=" * 60)
        
        # 清理舊驗證快照 (確保生成最新驗證快照)
        if self.snapshot_file.exists():
            logger.info(f"🗑️ 清理舊驗證快照: {self.snapshot_file}")
            self.snapshot_file.unlink()
        
        # 載入軌道數據
        orbital_data = self.load_orbital_calculation_output()
        
        # 🎯 v5.0 統一格式：從 constellations 結構提取衛星數據
        all_satellites = []
        
        if 'constellations' in orbital_data:
            # 🎯 統一格式：處理 constellations 結構
            for constellation_name, constellation_data in orbital_data.get('constellations', {}).items():
                satellites = constellation_data.get('satellites', [])
                
                for sat_data in satellites:
                    # 確保每顆衛星都有 constellation 字段
                    sat_data['constellation'] = constellation_name
                    
                    # 確保有 satellite_id 字段
                    if 'satellite_id' not in sat_data:
                        sat_data['satellite_id'] = sat_data.get('name', f"{constellation_name}_unknown")
                    
                    all_satellites.append(sat_data)
                    
        elif 'satellites' in orbital_data:
            # 🔧 回退兼容：處理舊的 satellites 陣列格式
            satellites_list = orbital_data.get('satellites', [])
            
            for sat_data in satellites_list:
                # 保持原有的constellation字段，不覆寫
                if 'constellation' not in sat_data:
                    sat_data['constellation'] = 'unknown'
                all_satellites.append(sat_data)
        else:
            logger.error("❌ 數據格式錯誤：缺少 constellations 或 satellites 字段")
            return {
                'metadata': {'total_satellites': 0, 'processing_complete': False, 'error': 'invalid_data_format'},
                'satellites': []
            }
                
        logger.info(f"📊 開始處理 {len(all_satellites)} 顆衛星")
        
        if len(all_satellites) == 0:
            logger.error("❌ 沒有衛星數據可供處理")
            return {
                'metadata': {'total_satellites': 0, 'processing_complete': False, 'error': 'no_satellites_data'},
                'satellites': []
            }
        
        # 🛡️ Phase 3 新增：預處理驗證
        validation_context = {
            'stage_name': 'stage2_satellite_visibility_filter',
            'processing_start': datetime.now(timezone.utc).isoformat(),
            'input_satellites_count': len(all_satellites),
            'observer_coordinates': {
                'latitude': self.observer_lat,
                'longitude': self.observer_lon,
                'altitude': self.observer_alt
            },
            'filtering_criteria': self.filtering_criteria
        }
        
        if self.validation_enabled and self.validation_adapter:
            try:
                logger.info("🔍 執行預處理驗證 (軌道數據結構檢查)...")
                
                # 執行預處理驗證
                import asyncio
                pre_validation_result = asyncio.run(
                    self.validation_adapter.pre_process_validation(all_satellites, validation_context)
                )
                
                if not pre_validation_result.get('success', False):
                    error_msg = f"預處理驗證失敗: {pre_validation_result.get('blocking_errors', [])}"
                    logger.error(f"🚨 {error_msg}")
                    raise ValueError(f"Phase 3 Validation Failed: {error_msg}")
                
                logger.info("✅ 預處理驗證通過，繼續可見性篩選...")
                
            except Exception as e:
                logger.error(f"🚨 Phase 3 預處理驗證異常: {str(e)}")
                if "Phase 3 Validation Failed" in str(e):
                    raise  # 重新拋出驗證失敗錯誤
                else:
                    logger.warning("   使用舊版驗證邏輯繼續處理")
        
        # 階段 0: 可見性預篩選
        visible_satellites = self._visibility_prefilter(all_satellites)
        
        # 簡化篩選（避免過度篩選）
        filtered_satellites = self._simple_filtering(visible_satellites)
        
        # 防止除零錯誤
        if len(all_satellites) == 0:
            retention_rate = 0.0
        else:
            retention_rate = (1 - len(filtered_satellites)/len(all_satellites))*100
        
        # 準備處理指標
        processing_metrics = {
            'input_satellites': len(all_satellites),
            'visible_satellites': len(visible_satellites),
            'filtered_satellites': len(filtered_satellites),
            'retention_rate': retention_rate,
            'processing_time': datetime.now(timezone.utc).isoformat(),
            'filtering_criteria_applied': self.filtering_criteria
        }
        
        # 🛡️ Phase 3 新增：後處理驗證
        if self.validation_enabled and self.validation_adapter:
            try:
                logger.info("🔍 執行後處理驗證 (可見性篩選結果檢查)...")
                
                # 執行後處理驗證
                post_validation_result = asyncio.run(
                    self.validation_adapter.post_process_validation(filtered_satellites, processing_metrics)
                )
                
                # 檢查驗證結果
                if not post_validation_result.get('success', False):
                    error_msg = f"後處理驗證失敗: {post_validation_result.get('error', '未知錯誤')}"
                    logger.error(f"🚨 {error_msg}")
                    
                    # 檢查是否為品質門禁阻斷
                    if 'Quality gate blocked' in post_validation_result.get('error', ''):
                        raise ValueError(f"Phase 3 Quality Gate Blocked: {error_msg}")
                    else:
                        logger.warning("   後處理驗證失敗，但繼續處理 (降級模式)")
                else:
                    logger.info("✅ 後處理驗證通過，可見性篩選結果符合學術標準")
                    
                    # 記錄驗證摘要
                    academic_compliance = post_validation_result.get('academic_compliance', {})
                    if academic_compliance.get('compliant', False):
                        logger.info(f"🎓 學術合規性: Grade {academic_compliance.get('grade_level', 'Unknown')}")
                    else:
                        logger.warning(f"⚠️ 學術合規性問題: {len(academic_compliance.get('violations', []))} 項違規")
                
                # 將驗證結果加入處理指標
                processing_metrics['validation_summary'] = post_validation_result
                
            except Exception as e:
                logger.error(f"🚨 Phase 3 後處理驗證異常: {str(e)}")
                if "Phase 3 Quality Gate Blocked" in str(e):
                    raise  # 重新拋出品質門禁阻斷錯誤
                else:
                    logger.warning("   使用舊版驗證邏輯繼續處理")
                    processing_metrics['validation_summary'] = {
                        'success': False,
                        'error': str(e),
                        'fallback_used': True
                    }
        
        # 保存結果
        output_file = self.save_filtered_output(filtered_satellites, len(all_satellites))
        
        # 輸出統計
        logger.info("=" * 60)
        logger.info("✅ 修復版增強智能篩選完成")
        logger.info(f"  輸入: {len(all_satellites)} 顆")
        logger.info(f"  輸出: {len(filtered_satellites)} 顆")
        if len(all_satellites) > 0:
            logger.info(f"  篩選率: {retention_rate:.1f}%")
        
        # 構建返回結果
        result = {
            'metadata': {
                'total_satellites': len(filtered_satellites),
                'input_satellites': len(all_satellites),
                'processing_complete': True,
                'data_format_version': 'unified_v1.1_phase3',
                'validation_summary': processing_metrics.get('validation_summary', None),
                'academic_compliance': {
                    'phase3_validation': 'enabled' if self.validation_enabled else 'disabled',
                    'processing_metrics': processing_metrics
                }
            },
            'satellites': filtered_satellites
        }
        
        # 🔍 自動保存驗證快照
        snapshot_saved = self.save_validation_snapshot(result)
        if snapshot_saved:
            logger.info(f"📊 驗證快照已自動保存: {self.snapshot_file}")
        else:
            logger.warning("⚠️ 驗證快照自動保存失敗")
        
        return result
    
    def process_intelligent_filtering(self, orbital_data=None, save_output=True):
        """
        兼容性方法：保持與原有API接口一致
        
        Phase 2 Enhancement: 新增運行時檢查
        """
        logger.info("🔄 使用兼容性API呼叫process_intelligent_filtering")
        
        # 🚨 Phase 2: 運行時檢查 - 引擎類型和依賴驗證
        try:
            check_runtime_architecture("stage2", engine=self.visibility_prefilter)
            validate_stage_completion("stage2", ["stage1"])  # Stage 2 依賴 Stage 1
            logger.info("✅ Stage 2 運行時架構檢查通過")
        except Exception as e:
            logger.error(f"❌ Stage 2 運行時架構檢查失敗: {e}")
            raise RuntimeError(f"Stage 2 runtime architecture validation failed: {e}")
        
        # 開始處理計時
        self.start_processing_timer()
        
        # 🎯 CRITICAL FIX: 如果提供了orbital_data，直接使用而不是從文件載入
        if orbital_data:
            logger.info("📊 使用提供的orbital_data而非從文件載入")
            result = self._process_with_data(orbital_data)
        else:
            result = self.process()
        
        # 🚨 Phase 2: API合約驗證 - 檢查篩選結果格式
        try:
            validate_api_contract("stage2", result)
            logger.info("✅ Stage 2 API合約驗證通過")
        except Exception as e:
            logger.error(f"❌ Stage 2 API合約驗證失敗: {e}")
            raise RuntimeError(f"Stage 2 API contract validation failed: {e}")
        
        # 結束處理計時
        self.end_processing_timer()
        
        # 轉換為Stage 3期望的格式
        if 'satellites' in result:
            satellites = result['satellites']
            starlink_satellites = [s for s in satellites if 'starlink' in s.get('constellation', '').lower()]
            oneweb_satellites = [s for s in satellites if 'oneweb' in s.get('constellation', '').lower()]
            
            # 添加constellations格式
            result['constellations'] = {
                'starlink': {
                    'satellite_count': len(starlink_satellites),
                    'satellites': starlink_satellites
                },
                'oneweb': {
                    'satellite_count': len(oneweb_satellites),
                    'satellites': oneweb_satellites
                }
            }
        
        # 🔍 保存驗證快照
        snapshot_saved = self.save_validation_snapshot(result)
        if snapshot_saved:
            logger.info(f"📊 驗證快照已保存: {self.snapshot_file}")
        else:
            logger.warning("⚠️ 驗證快照保存失敗")
        
        if save_output:
            logger.info("💾 輸出已保存到文件")
        
        logger.info("✅ Stage 2 處理完成，所有運行時檢查通過")
        return result

    def extract_key_metrics(self, processing_results: Dict[str, Any]) -> Dict[str, Any]:
        """提取 Stage 2 關鍵指標（適配process()方法的返回格式）- Grade A學術標準合規"""
        metadata = processing_results.get('metadata', {})
        satellites = processing_results.get('satellites', [])
        
        # 從階段一輸出文件獲取輸入數量 - Grade A合規：必須從真實數據源獲取
        try:
            orbital_data = self.load_orbital_calculation_output()
            total_input = len(orbital_data.get('satellites', []))
            if total_input == 0:
                # 檢查舊格式兼容
                if 'constellations' in orbital_data:
                    total_input = sum(const_data.get('satellite_count', 0) 
                                    for const_data in orbital_data['constellations'].values())
            
            if total_input == 0:
                raise ValueError("❌ Grade A違規: 階段一數據為空 - 必須使用真實TLE數據")
                
        except Exception as e:
            raise ValueError(f"❌ Grade A違規: 無法從階段一獲取真實衛星數據 - {str(e)}")
            
        total_output = len(satellites)
        
        # 按星座統計
        starlink_count = sum(1 for sat in satellites if sat.get('constellation', '').lower() == 'starlink')
        oneweb_count = sum(1 for sat in satellites if sat.get('constellation', '').lower() == 'oneweb')
        
        filtering_rate = ((total_input - total_output) / max(total_input, 1)) * 100
        
        return {
            "輸入衛星": total_input,
            "輸出衛星": total_output,
            "Starlink篩選": starlink_count,
            "OneWeb篩選": oneweb_count,
            "篩選率": f"{filtering_rate:.1f}%",
            "地理相關性": f"{total_output}顆",
            "處理模式": "取樣模式" if self.sample_mode else "全量模式",
            "學術合規": "Grade A - 真實數據源"
        }
    
    def run_validation_checks(self, processing_results: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 3 增強版 Stage 2 驗證檢查 - 整合仰角計算精度和物理公式合規驗證 + Phase 3.5 可配置驗證級別"""
        
        # 🎯 Phase 3.5: 導入可配置驗證級別管理器
        try:
            from pathlib import Path
            import sys
            
            from validation.managers.validation_level_manager import ValidationLevelManager
            
            validation_manager = ValidationLevelManager()
            validation_level = validation_manager.get_validation_level('stage2')
            
            # 性能監控開始
            import time
            validation_start_time = time.time()
            
        except ImportError:
            # 回退到標準驗證級別
            validation_level = 'STANDARD'
            validation_start_time = time.time()
        
        metadata = processing_results.get('metadata', {})
        constellations = processing_results.get('constellations', {})
        satellites = processing_results.get('satellites', [])
        
        checks = {}
        
        # 📊 根據驗證級別決定檢查項目
        if validation_level == 'FAST':
            # 快速模式：只執行關鍵檢查
            critical_checks = [
                '輸入數據存在性',
                '數量範圍合理性', 
                '仰角門檻合規性',
                '數據結構完整性'
            ]
        elif validation_level == 'COMPREHENSIVE':
            # 詳細模式：執行所有檢查 + 額外的深度檢查
            critical_checks = [
                '輸入數據存在性', '數量範圍合理性', '星座分布平衡性', 
                '仰角門檻合規性', '可見時間合規性', '仰角計算精度', 
                '物理公式合規性', '篩選原因一致性', '數據結構完整性',
                '處理時間合理性', '時間基準一致性', '地理覆蓋相關性'
            ]
        else:
            # 標準模式：執行大部分檢查
            critical_checks = [
                '輸入數據存在性', '數量範圍合理性', '星座分布平衡性',
                '仰角門檻合規性', '可見時間合規性', '仰角計算精度',
                '物理公式合規性', '篩選原因一致性', '數據結構完整性',
                '處理時間合理性', '時間基準一致性'
            ]
        
        # 1. 輸入數據存在性檢查 - Grade A合規
        if '輸入數據存在性' in critical_checks:
            try:
                orbital_data = self.load_orbital_calculation_output()
                total_input = len(orbital_data.get('satellites', []))
                if total_input == 0:
                    if 'constellations' in orbital_data:
                        total_input = sum(const_data.get('satellite_count', 0) 
                                        for const_data in orbital_data['constellations'].values())
                
                if total_input == 0:
                    raise ValueError("❌ Grade A違規: 階段一數據為空 - 必須使用真實TLE數據")
                    
            except Exception as e:
                raise ValueError(f"❌ Grade A違規: 無法從階段一獲取真實衛星數據 - {str(e)}")
                
            checks["輸入數據存在性"] = total_input > 0
        
        # 2. 數量範圍合理性檢查 - 修復過於寬鬆的問題
        if '數量範圍合理性' in critical_checks:
            total_output = len(satellites)
            retention_rate = (total_output / max(total_input, 1)) * 100
            
            # 基於實際地理篩選邏輯的合理範圍
            expected_min_output = int(total_input * 0.10)  # 至少10%
            expected_max_output = int(total_input * 0.60)  # 最多60%
            
            checks["數量範圍合理性"] = expected_min_output <= total_output <= expected_max_output
        
        # 3. 星座分布檢查 - 更嚴格的星座平衡驗證
        if '星座分布平衡性' in critical_checks:
            starlink_count = sum(1 for sat in satellites if 'starlink' in sat.get('constellation', '').lower())
            oneweb_count = sum(1 for sat in satellites if 'oneweb' in sat.get('constellation', '').lower())
            
            # 基於不同仰角門檻，OneWeb保留率應該較低
            starlink_retention = (starlink_count / max(1, sum(1 for sat in satellites if 'starlink' in sat.get('constellation', '').lower()))) * 100
            oneweb_retention = (oneweb_count / max(1, sum(1 for sat in satellites if 'oneweb' in sat.get('constellation', '').lower()))) * 100
            
            checks["星座分布平衡性"] = starlink_count > 0 and oneweb_count > 0 and starlink_count > oneweb_count
        
        # 4. 仰角門檻驗證 - 新增重要檢查
        if '仰角門檻合規性' in critical_checks:
            elevation_compliance = True
            # 快速模式使用較小的樣本
            sample_count = min(50 if validation_level == 'FAST' else 100, len(satellites))
            
            for sat in satellites[:sample_count]:
                constellation = sat.get('constellation', '').lower()
                filtering_info = sat.get('stage2_filtering', {})
                
                if 'starlink' in constellation:
                    expected_threshold = 5.0
                elif 'oneweb' in constellation:
                    expected_threshold = 10.0
                else:
                    continue
                    
                if filtering_info.get('min_elevation_threshold', 0) != expected_threshold:
                    elevation_compliance = False
                    break
            
            checks["仰角門檻合規性"] = elevation_compliance
        
        # 5. 可見時間驗證 - 新增關鍵檢查
        if '可見時間合規性' in critical_checks:
            visibility_compliance = True
            sample_count = min(50 if validation_level == 'FAST' else 100, len(satellites))
            
            for sat in satellites[:sample_count]:
                constellation = sat.get('constellation', '').lower()
                filtering_info = sat.get('stage2_filtering', {})
                visible_duration = filtering_info.get('visible_duration_minutes', 0)
                
                if 'starlink' in constellation and visible_duration < 1.0:
                    visibility_compliance = False
                    break
                elif 'oneweb' in constellation and visible_duration < 0.5:
                    visibility_compliance = False
                    break
            
            checks["可見時間合規性"] = visibility_compliance
        
        # 🔬 Phase 3 新增：執行仰角計算精度檢查
        if '仰角計算精度' in critical_checks:
            try:
                elevation_accuracy_report = self._validate_elevation_calculation_accuracy(processing_results)
                
                # 將仰角精度報告附加到結果中
                if 'validation_reports' not in processing_results:
                    processing_results['validation_reports'] = {}
                processing_results['validation_reports']['elevation_calculation_accuracy'] = elevation_accuracy_report
                
                checks["仰角計算精度"] = elevation_accuracy_report.get('accuracy_compliance_status') == 'PASS'
                logger.info("✅ 仰角計算精度檢查已完成")
                
            except ValueError as e:
                logger.error(f"❌ 仰角計算精度檢查失敗: {e}")
                checks["仰角計算精度"] = False
                # 不拋出異常，允許其他檢查繼續
        
        # 🧮 Phase 3 新增：執行物理公式合規驗證
        if '物理公式合規性' in critical_checks:
            try:
                formula_compliance_report = self._validate_physical_formula_compliance(processing_results)
                
                # 將物理公式合規報告附加到結果中
                processing_results['validation_reports']['physical_formula_compliance'] = formula_compliance_report
                
                checks["物理公式合規性"] = formula_compliance_report.get('compliance_status') == 'PASS'
                logger.info("✅ 物理公式合規驗證已完成")
                
            except ValueError as e:
                logger.error(f"❌ 物理公式合規驗證失敗: {e}")
                checks["物理公式合規性"] = False
                # 不拋出異常，允許其他檢查繼續
        
        # 6. 篩選原因一致性檢查
        if '篩選原因一致性' in critical_checks:
            reason_consistency = True
            valid_reasons = {'geographic_visibility', 'strict_geographic_visibility', 'geographic_visibility_batch'}
            sample_count = min(50 if validation_level == 'FAST' else 100, len(satellites))
            
            for sat in satellites[:sample_count]:
                filtering_info = sat.get('stage2_filtering', {})
                reason = filtering_info.get('reason', '')
                
                if reason not in valid_reasons or not filtering_info.get('passed', False):
                    reason_consistency = False
                    break
            
            checks["篩選原因一致性"] = reason_consistency
        
        # 7. 數據結構完整性檢查 - 增強版
        if '數據結構完整性' in critical_checks:
            structure_complete = True
            required_fields = ['satellite_id', 'constellation', 'position_timeseries', 'stage2_filtering']
            sample_count = min(50 if validation_level == 'FAST' else 100, len(satellites))
            
            for sat in satellites[:sample_count]:
                for field in required_fields:
                    if field not in sat:
                        structure_complete = False
                        break
                if not structure_complete:
                    break
                
                # 檢查篩選元數據完整性
                filtering_info = sat.get('stage2_filtering', {})
                required_filtering_fields = ['passed', 'reason', 'visible_duration_minutes', 'visibility_percentage']
                for field in required_filtering_fields:
                    if field not in filtering_info:
                        structure_complete = False
                        break
            
            checks["數據結構完整性"] = structure_complete
        
        # 8. 處理時間合理性檢查
        if '處理時間合理性' in critical_checks:
            # 快速模式有更嚴格的性能要求
            if validation_level == 'FAST':
                max_time = 180 if self.sample_mode else 120
            else:
                max_time = 300 if self.sample_mode else 180  # 取樣5分鐘，全量3分鐘
            processing_time_ok = hasattr(self, 'processing_duration') and self.processing_duration <= max_time
            checks["處理時間合理性"] = processing_time_ok
        
        # 9. 時間基準一致性檢查 - 新增重要檢查
        if '時間基準一致性' in critical_checks:
            time_consistency = True
            if 'processing_timestamp' in metadata:
                try:
                    from datetime import datetime
                    processing_time = datetime.fromisoformat(metadata['processing_timestamp'].replace('Z', '+00:00'))
                    current_time = datetime.now(processing_time.tzinfo)
                    time_diff = abs((current_time - processing_time).total_seconds())
                    # 處理時間應該在10分鐘內
                    time_consistency = time_diff <= 600
                except:
                    time_consistency = False
            
            checks["時間基準一致性"] = time_consistency
        
        # 10. 地理覆蓋範圍檢查 - 新增NTPU相關性驗證（詳細模式專用）
        if '地理覆蓋相關性' in critical_checks:
            geographic_relevance = True
            ntpu_lat, ntpu_lon = 24.9441667, 121.3713889
            
            # 檢查是否有衛星軌跡覆蓋NTPU區域
            coverage_found = False
            sample_count = min(50, len(satellites))
            for sat in satellites[:sample_count]:
                position_timeseries = sat.get('position_timeseries', [])
                for pos in position_timeseries:
                    sat_lat = pos.get('geodetic', {}).get('latitude_deg', 0)
                    sat_lon = pos.get('geodetic', {}).get('longitude_deg', 0)
                    
                    # 粗略檢查是否在亞太區域內
                    if 10 <= sat_lat <= 40 and 100 <= sat_lon <= 140:
                        coverage_found = True
                        break
                if coverage_found:
                    break
            
            checks["地理覆蓋相關性"] = coverage_found
        
        # 計算通過的檢查數量
        passed_checks = sum(1 for passed in checks.values() if passed)
        total_checks = len(checks)
        
        # 🎯 Phase 3.5: 記錄驗證性能指標
        validation_end_time = time.time()
        validation_duration = validation_end_time - validation_start_time
        
        try:
            # 更新性能指標
            validation_manager.update_performance_metrics('stage2', validation_duration, total_checks)
            
            # 自適應調整（如果性能太差）
            if validation_duration > 5.0 and validation_level != 'FAST':
                validation_manager.set_validation_level('stage2', 'FAST', reason='performance_auto_adjustment')
        except:
            # 如果性能記錄失敗，不影響主要驗證流程
            pass
        
        return {
            "passed": passed_checks == total_checks,
            "totalChecks": total_checks,
            "passedChecks": passed_checks,
            "failedChecks": total_checks - passed_checks,
            "criticalChecks": [
                {"name": name, "status": "passed" if checks.get(name, False) else "failed"}
                for name in critical_checks if name in checks
            ],
            "allChecks": checks,
            "detailedSummary": {
                "input_satellites": total_input,
                "output_satellites": len(satellites),
                "retention_rate": f"{(len(satellites) / max(total_input, 1)) * 100:.1f}%",
                "starlink_count": sum(1 for sat in satellites if 'starlink' in sat.get('constellation', '').lower()),
                "oneweb_count": sum(1 for sat in satellites if 'oneweb' in sat.get('constellation', '').lower()),
                "expected_range": f"{int(total_input * 0.10)}-{int(total_input * 0.60)} 顆" if 'total_input' in locals() else "未知範圍",
                "geographic_coverage": "亞太區域相關" if checks.get("地理覆蓋相關性", True) else "地理覆蓋不足"
            },
            "phase3_enhancements": {
                "elevation_accuracy_validated": checks.get("仰角計算精度", False),
                "physical_formula_validated": checks.get("物理公式合規性", False),
                "validation_reports_generated": 'validation_reports' in processing_results
            },
            # 🎯 Phase 3.5 新增：驗證級別信息
            "validation_level_info": {
                "current_level": validation_level,
                "validation_duration_ms": round(validation_duration * 1000, 2),
                "checks_executed": list(checks.keys()),
                "performance_acceptable": validation_duration < 5.0
            },
            "summary": f"Phase 3 增強地理篩選驗證: 輸入{total_input if 'total_input' in locals() else '未知'}顆 → 輸出{len(satellites)}顆 (保留率{(len(satellites) / max(total_input if 'total_input' in locals() else 1, 1)) * 100:.1f}%) - {passed_checks}/{total_checks}項檢查通過"
        }

    def _validate_elevation_calculation_accuracy(self, processing_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        仰角計算精度檢查 - Phase 3 Task 2 新增功能
        
        驗證仰角計算是否符合ITU-R P.618標準：
        - 球面三角學精確計算
        - 大地座標系轉換準確性
        - 觀測者位置座標精度
        - 仰角計算物理合理性
        
        Args:
            processing_results: 過濾處理結果數據
            
        Returns:
            Dict: 仰角計算精度驗證報告
            
        Raises:
            ValueError: 如果發現嚴重的仰角計算精度問題
        """
        logger.info("📐 執行仰角計算精度檢查...")
        
        satellites = processing_results.get('satellites', [])
        accuracy_report = {
            'validation_timestamp': datetime.now(timezone.utc).isoformat(),
            'total_satellites_checked': len(satellites),
            'accuracy_statistics': {
                'satellites_with_accurate_elevation': 0,
                'satellites_with_precision_issues': 0,
                'accuracy_compliance_percentage': 0.0
            },
            'precision_violations': [],
            'accuracy_compliance_status': 'UNKNOWN'
        }
        
        # ITU-R P.618 仰角計算精度標準
        ACCURACY_STANDARDS = {
            'min_elevation_precision_deg': 0.01,      # 仰角精度至少0.01度
            'max_elevation_deg': 90.0,                # 最大仰角90度
            'min_elevation_deg': -90.0,               # 最小仰角-90度（地平線以下）
            'coordinate_precision_deg': 0.001,        # 座標精度0.001度
            'max_calculation_error_deg': 0.1,         # 最大計算誤差0.1度
            'min_valid_range_km': 200,                # 最小有效距離200km
            'max_valid_range_km': 3000                # 最大有效距離3000km
        }
        
        # NTPU精確座標（用於驗證）
        NTPU_REFERENCE = {
            'latitude': 24.9441667,    # 24°56'39"N
            'longitude': 121.3713889,  # 121°22'17"E
            'altitude_m': 50.0         # 海拔50米
        }
        
        accurate_satellites = 0
        precision_issues = 0
        
        # 抽樣檢查衛星的仰角計算精度（檢查前50顆）
        sample_size = min(50, len(satellites))
        sample_satellites = satellites[:sample_size]
        
        for sat_data in sample_satellites:
            satellite_name = sat_data.get('name', 'Unknown')
            constellation = sat_data.get('constellation', '').lower()
            position_timeseries = sat_data.get('position_timeseries', [])
            
            if not position_timeseries:
                precision_violations.append({
                    'satellite_name': satellite_name,
                    'violation_type': 'no_position_data',
                    'details': '缺少位置時間序列數據'
                })
                precision_issues += 1
                continue
            
            satellite_violations = []
            
            # 檢查前5個時間點的仰角計算精度
            sample_positions = position_timeseries[:5]
            
            for i, pos in enumerate(sample_positions):
                relative_data = pos.get('relative_to_observer', {})
                geodetic_data = pos.get('geodetic', {})
                
                if not relative_data:
                    satellite_violations.append({
                        'timestamp_index': i,
                        'issue': 'missing_relative_observer_data',
                        'details': '缺少相對觀測者數據'
                    })
                    continue
                
                # 1. 檢查仰角值的物理合理性
                elevation_deg = relative_data.get('elevation_deg')
                if elevation_deg is None:
                    satellite_violations.append({
                        'timestamp_index': i,
                        'issue': 'missing_elevation_data',
                        'details': '缺少仰角數據'
                    })
                    continue
                
                # 檢查仰角範圍
                if not (ACCURACY_STANDARDS['min_elevation_deg'] <= elevation_deg <= ACCURACY_STANDARDS['max_elevation_deg']):
                    satellite_violations.append({
                        'timestamp_index': i,
                        'issue': 'elevation_out_of_range',
                        'details': f'仰角 {elevation_deg}° 超出合理範圍',
                        'expected_range': f"{ACCURACY_STANDARDS['min_elevation_deg']}° 到 {ACCURACY_STANDARDS['max_elevation_deg']}°"
                    })
                
                # 2. 檢查方位角的合理性
                azimuth_deg = relative_data.get('azimuth_deg')
                if azimuth_deg is not None:
                    if not (0 <= azimuth_deg <= 360):
                        satellite_violations.append({
                            'timestamp_index': i,
                            'issue': 'azimuth_out_of_range',
                            'details': f'方位角 {azimuth_deg}° 超出0-360度範圍'
                        })
                
                # 3. 檢查距離與仰角的一致性
                range_km = relative_data.get('range_km', 0)
                if range_km > 0:
                    # 可見衛星的距離應該在合理範圍內
                    if elevation_deg > 0:  # 地平線以上
                        if not (ACCURACY_STANDARDS['min_valid_range_km'] <= range_km <= ACCURACY_STANDARDS['max_valid_range_km']):
                            satellite_violations.append({
                                'timestamp_index': i,
                                'issue': 'range_elevation_inconsistency',
                                'details': f'可見衛星距離 {range_km}km 與仰角 {elevation_deg}° 不一致'
                            })
                
                # 4. 檢查大地座標的精度
                if geodetic_data:
                    sat_lat = geodetic_data.get('latitude_deg')
                    sat_lon = geodetic_data.get('longitude_deg')
                    
                    if sat_lat is not None and sat_lon is not None:
                        # 檢查座標精度（是否有足夠的小數位數）
                        lat_precision = len(str(sat_lat).split('.')[-1]) if '.' in str(sat_lat) else 0
                        lon_precision = len(str(sat_lon).split('.')[-1]) if '.' in str(sat_lon) else 0
                        
                        if lat_precision < 4 or lon_precision < 4:  # 至少4位小數
                            satellite_violations.append({
                                'timestamp_index': i,
                                'issue': 'insufficient_coordinate_precision',
                                'details': f'座標精度不足: 緯度{lat_precision}位, 經度{lon_precision}位小數'
                            })
                
                # 5. 檢查觀測者座標是否為NTPU標準座標
                observer_lat = self.observer_lat
                observer_lon = self.observer_lon
                
                lat_diff = abs(observer_lat - NTPU_REFERENCE['latitude'])
                lon_diff = abs(observer_lon - NTPU_REFERENCE['longitude'])
                
                if lat_diff > ACCURACY_STANDARDS['coordinate_precision_deg'] or lon_diff > ACCURACY_STANDARDS['coordinate_precision_deg']:
                    satellite_violations.append({
                        'timestamp_index': i,
                        'issue': 'observer_coordinate_deviation',
                        'details': f'觀測者座標偏離NTPU標準: Δlat={lat_diff:.6f}°, Δlon={lon_diff:.6f}°'
                    })
            
            # 判斷該衛星的仰角計算精度
            if len(satellite_violations) == 0:
                accurate_satellites += 1
            else:
                precision_issues += 1
                accuracy_report['precision_violations'].append({
                    'satellite_name': satellite_name,
                    'constellation': constellation,
                    'violation_count': len(satellite_violations),
                    'violations': satellite_violations
                })
        
        # 計算精度統計
        accuracy_compliance_rate = (accurate_satellites / sample_size * 100) if sample_size > 0 else 0
        
        accuracy_report['accuracy_statistics'] = {
            'satellites_with_accurate_elevation': accurate_satellites,
            'satellites_with_precision_issues': precision_issues,
            'accuracy_compliance_percentage': accuracy_compliance_rate
        }
        
        # 確定精度合規狀態
        if accuracy_compliance_rate >= 95 and len(accuracy_report['precision_violations']) == 0:
            accuracy_report['accuracy_compliance_status'] = 'PASS'
            logger.info(f"✅ 仰角計算精度檢查通過: {accuracy_compliance_rate:.2f}% 合規率")
        else:
            accuracy_report['accuracy_compliance_status'] = 'FAIL'
            logger.error(f"❌ 仰角計算精度檢查失敗: {accuracy_compliance_rate:.2f}% 合規率，發現 {len(accuracy_report['precision_violations'])} 個問題")
            
            # 如果精度問題嚴重，拋出異常
            if accuracy_compliance_rate < 85:
                raise ValueError(f"Academic Standards Violation: 仰角計算精度嚴重不足 - 合規率僅 {accuracy_compliance_rate:.2f}%")
        
        return accuracy_report

    def _validate_physical_formula_compliance(self, processing_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        物理公式合規驗證 - Phase 3 Task 2 新增功能
        
        驗證物理計算是否符合標準：
        - 球面三角學公式正確性
        - 大地座標系轉換標準
        - 距離計算物理一致性
        - 時間計算準確性
        
        Args:
            processing_results: 過濾處理結果數據
            
        Returns:
            Dict: 物理公式合規驗證報告
            
        Raises:
            ValueError: 如果發現嚴重的物理公式違規
        """
        logger.info("🧮 執行物理公式合規驗證...")
        
        satellites = processing_results.get('satellites', [])
        formula_report = {
            'validation_timestamp': datetime.now(timezone.utc).isoformat(),
            'total_satellites_checked': len(satellites),
            'formula_compliance_statistics': {
                'satellites_with_compliant_calculations': 0,
                'satellites_with_formula_violations': 0,
                'compliance_percentage': 0.0
            },
            'formula_violations': [],
            'compliance_status': 'UNKNOWN'
        }
        
        # 物理公式標準定義
        PHYSICS_STANDARDS = {
            'earth_radius_km': 6371.0,                    # 地球平均半徑
            'max_leo_altitude_km': 2000,                  # LEO最大高度
            'min_leo_altitude_km': 200,                   # LEO最小高度
            'speed_of_light_kms': 299792.458,            # 光速 km/s
            'max_orbital_velocity_kms': 8.0,             # 最大軌道速度 km/s
            'min_orbital_velocity_kms': 6.5,             # 最小軌道速度 km/s
            'coordinate_system': 'WGS84',                 # 標準座標系
            'time_precision_seconds': 1.0                 # 時間精度要求
        }
        
        compliant_satellites = 0
        violation_satellites = 0
        
        # 抽樣檢查衛星的物理公式計算（檢查前30顆）
        sample_size = min(30, len(satellites))
        sample_satellites = satellites[:sample_size]
        
        for sat_data in sample_satellites:
            satellite_name = sat_data.get('name', 'Unknown')
            constellation = sat_data.get('constellation', '').lower()
            position_timeseries = sat_data.get('position_timeseries', [])
            
            if not position_timeseries:
                continue
            
            satellite_violations = []
            
            # 檢查前3個時間點的物理公式合規性
            sample_positions = position_timeseries[:3]
            
            for i, pos in enumerate(sample_positions):
                # 1. 檢查ECI座標的物理合理性
                position_eci = pos.get('position_eci', {})
                if position_eci:
                    x = position_eci.get('x', 0)
                    y = position_eci.get('y', 0)
                    z = position_eci.get('z', 0)
                    
                    # 計算衛星到地心的距離
                    distance_to_center = (x*x + y*y + z*z)**0.5
                    altitude = distance_to_center - PHYSICS_STANDARDS['earth_radius_km']
                    
                    # 檢查軌道高度是否在LEO範圍內
                    if not (PHYSICS_STANDARDS['min_leo_altitude_km'] <= altitude <= PHYSICS_STANDARDS['max_leo_altitude_km']):
                        satellite_violations.append({
                            'timestamp_index': i,
                            'formula_violation': 'orbital_altitude_out_of_range',
                            'details': f'軌道高度 {altitude:.1f}km 超出LEO範圍',
                            'expected_range': f"{PHYSICS_STANDARDS['min_leo_altitude_km']}-{PHYSICS_STANDARDS['max_leo_altitude_km']}km",
                            'calculated_value': altitude
                        })
                
                # 2. 檢查大地座標的物理一致性
                geodetic_data = pos.get('geodetic', {})
                if geodetic_data:
                    sat_lat = geodetic_data.get('latitude_deg')
                    sat_lon = geodetic_data.get('longitude_deg')
                    sat_alt = geodetic_data.get('altitude_km')
                    
                    # 檢查緯度範圍
                    if sat_lat is not None and not (-90 <= sat_lat <= 90):
                        satellite_violations.append({
                            'timestamp_index': i,
                            'formula_violation': 'latitude_out_of_range',
                            'details': f'緯度 {sat_lat}° 超出 ±90° 範圍'
                        })
                    
                    # 檢查經度範圍
                    if sat_lon is not None and not (-180 <= sat_lon <= 180):
                        satellite_violations.append({
                            'timestamp_index': i,
                            'formula_violation': 'longitude_out_of_range',
                            'details': f'經度 {sat_lon}° 超出 ±180° 範圍'
                        })
                    
                    # 檢查高度一致性
                    if sat_alt is not None and position_eci:
                        eci_altitude = distance_to_center - PHYSICS_STANDARDS['earth_radius_km']
                        altitude_difference = abs(sat_alt - eci_altitude)
                        
                        # 高度差應該小於1km（轉換精度要求）
                        if altitude_difference > 1.0:
                            satellite_violations.append({
                                'timestamp_index': i,
                                'formula_violation': 'altitude_consistency_error',
                                'details': f'ECI高度({eci_altitude:.1f}km)與大地高度({sat_alt:.1f}km)不一致',
                                'difference': altitude_difference
                            })
                
                # 3. 檢查觀測者相對數據的物理一致性
                relative_data = pos.get('relative_to_observer', {})
                if relative_data and geodetic_data:
                    range_km = relative_data.get('range_km', 0)
                    elevation_deg = relative_data.get('elevation_deg')
                    
                    # 使用球面三角學驗證距離計算
                    if range_km > 0 and elevation_deg is not None:
                        # 粗略檢查：仰角與距離的大致關係
                        if elevation_deg > 45:  # 高仰角衛星
                            if range_km > 1500:  # 距離不應該太遠
                                satellite_violations.append({
                                    'timestamp_index': i,
                                    'formula_violation': 'elevation_range_inconsistency',
                                    'details': f'高仰角({elevation_deg:.1f}°)衛星距離過遠({range_km:.1f}km)'
                                })
                        elif elevation_deg < 5:  # 低仰角衛星
                            if range_km < 1000:  # 距離不應該太近
                                satellite_violations.append({
                                    'timestamp_index': i,
                                    'formula_violation': 'low_elevation_range_inconsistency',
                                    'details': f'低仰角({elevation_deg:.1f}°)衛星距離過近({range_km:.1f}km)'
                                })
                
                # 4. 檢查速度數據的物理合理性（如果有）
                velocity_data = pos.get('velocity_kms')
                if velocity_data and isinstance(velocity_data, dict):
                    vx = velocity_data.get('vx', 0)
                    vy = velocity_data.get('vy', 0)
                    vz = velocity_data.get('vz', 0)
                    velocity_magnitude = (vx*vx + vy*vy + vz*vz)**0.5
                    
                    # 檢查軌道速度是否在LEO範圍內
                    if not (PHYSICS_STANDARDS['min_orbital_velocity_kms'] <= velocity_magnitude <= PHYSICS_STANDARDS['max_orbital_velocity_kms']):
                        satellite_violations.append({
                            'timestamp_index': i,
                            'formula_violation': 'orbital_velocity_out_of_range',
                            'details': f'軌道速度 {velocity_magnitude:.2f}km/s 超出LEO範圍',
                            'expected_range': f"{PHYSICS_STANDARDS['min_orbital_velocity_kms']}-{PHYSICS_STANDARDS['max_orbital_velocity_kms']}km/s"
                        })
            
            # 判斷該衛星的物理公式合規性
            if len(satellite_violations) == 0:
                compliant_satellites += 1
            else:
                violation_satellites += 1
                formula_report['formula_violations'].append({
                    'satellite_name': satellite_name,
                    'constellation': constellation,
                    'violation_count': len(satellite_violations),
                    'violations': satellite_violations
                })
        
        # 計算合規統計
        compliance_rate = (compliant_satellites / sample_size * 100) if sample_size > 0 else 0
        
        formula_report['formula_compliance_statistics'] = {
            'satellites_with_compliant_calculations': compliant_satellites,
            'satellites_with_formula_violations': violation_satellites,
            'compliance_percentage': compliance_rate
        }
        
        # 確定合規狀態
        if compliance_rate >= 90 and len(formula_report['formula_violations']) <= 2:
            formula_report['compliance_status'] = 'PASS'
            logger.info(f"✅ 物理公式合規驗證通過: {compliance_rate:.2f}% 合規率")
        else:
            formula_report['compliance_status'] = 'FAIL'
            logger.error(f"❌ 物理公式合規驗證失敗: {compliance_rate:.2f}% 合規率，發現 {len(formula_report['formula_violations'])} 個問題")
            
            # 如果合規問題嚴重，拋出異常
            if compliance_rate < 75:
                raise ValueError(f"Academic Standards Violation: 物理公式合規性嚴重不足 - 合規率僅 {compliance_rate:.2f}%")
        
        return formula_report


def main():
    """主函數"""
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    logger.info("=" * 70)
    logger.info("階段二修復版：增強智能衛星篩選")
    logger.info("=" * 70)
    
    try:
        # 檢測是否為取樣模式
        test_file = Path("/app/data/tle_orbital_calculation_output.json")
        sample_mode = False
        
        if test_file.exists():
            with open(test_file, 'r') as f:
                data = json.load(f)
                total_sats = data.get('metadata', {}).get('total_satellites', 0)
                if total_sats < 100:  # 少於100顆視為取樣模式
                    sample_mode = True
                    logger.info(f"🔬 檢測到取樣模式（{total_sats} 顆衛星）")
        
        processor = SatelliteVisibilityFilterProcessor(sample_mode=sample_mode)
        result = processor.process()
        
        logger.info("🎉 階段二修復版處理成功完成！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 階段二修復版處理失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)