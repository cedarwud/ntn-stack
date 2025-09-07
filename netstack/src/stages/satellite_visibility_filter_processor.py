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

logger = logging.getLogger(__name__)


class SimplifiedVisibilityPreFilter:
    """簡化版可見性預篩選器（避免過度篩選）"""
    
    def __init__(self, observer_location: Tuple[float, float, float]):
        self.observer_lat, self.observer_lon, self.observer_alt = observer_location
        self.earth_radius_km = 6371.0
        
    def check_orbital_coverage(self, satellite_data: Dict) -> bool:
        """
        簡化的檢查，只排除明顯不可能的情況
        """
        try:
            # 從 TLE 提取傾角
            tle_line2 = satellite_data.get('tle_data', {}).get('line2', '')
            if not tle_line2:
                return True  # 無數據時假設可見
                
            inclination = float(tle_line2[8:16].strip())
            
            # 只排除極端情況（例如赤道軌道對高緯度地區）
            if inclination < 10 and abs(self.observer_lat) > 40:
                return False  # 低傾角對高緯度不可見
                
            # 極軌衛星總是可見
            if inclination > 80:
                return True
                
            # 其他情況假設可見（保守策略）
            return True
            
        except:
            return True  # 錯誤時假設可見


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
        
        logger.info("✅ 地理可見性自然篩選處理器初始化完成")
        logger.info(f"  觀測點: NTPU ({self.observer_lat:.6f}°, {self.observer_lon:.6f}°)")
        logger.info(f"  篩選模式: 地理可見性自然篩選（無數量限制）")
        logger.info(f"  Starlink條件: 仰角≥{self.filtering_criteria['starlink']['min_elevation_deg']}°, 可見時間≥{self.filtering_criteria['starlink']['min_visible_time_min']}分鐘")
        logger.info(f"  OneWeb條件: 仰角≥{self.filtering_criteria['oneweb']['min_elevation_deg']}°, 可見時間≥{self.filtering_criteria['oneweb']['min_visible_time_min']}分鐘")
        
    def load_orbital_calculation_output(self) -> Dict[str, Any]:
        """載入軌道計算結果檔案 - 修復版本"""
        # 🎯 更新為新的檔案命名
        orbital_file = self.input_dir / "tle_orbital_calculation_output.json"
        
        if not orbital_file.exists():
            logger.error(f"❌ 軌道計算檔案不存在: {orbital_file}")
            return {}
        
        try:
            logger.info(f"📥 載入軌道計算檔案: {orbital_file}")
            
            with open(orbital_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 檢查數據結構和統計
            if 'satellites' in data:
                satellite_count = len(data['satellites'])
                logger.info(f"  ✅ 載入 {satellite_count} 顆衛星數據")
                
                # 統計星座分布
                constellations = {}
                for sat in data['satellites']:
                    const = sat.get('constellation', 'unknown')
                    constellations[const] = constellations.get(const, 0) + 1
                
                for const, count in constellations.items():
                    logger.info(f"    {const}: {count} 顆衛星")
                
            elif 'constellations' in data:
                # 舊格式兼容
                total_satellites = 0
                for const_name, const_data in data['constellations'].items():
                    const_sat_count = const_data.get('satellite_count', 0)
                    total_satellites += const_sat_count
                    logger.info(f"    {const_name}: {const_sat_count} 顆衛星")
                logger.info(f"  ✅ 載入 {total_satellites} 顆衛星數據")
            
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
        """執行完整的篩選流程"""
        logger.info("🚀 開始修復版增強智能衛星篩選處理")
        logger.info("=" * 60)
        
        # 清理舊驗證快照 (確保生成最新驗證快照)
        if self.snapshot_file.exists():
            logger.info(f"🗑️ 清理舊驗證快照: {self.snapshot_file}")
            self.snapshot_file.unlink()
        
        # 載入軌道數據
        orbital_data = self.load_orbital_calculation_output()
        
        # 整理所有衛星數據 - 適配新的SGP4輸出格式
        all_satellites = []
        
        # 檢查新的SGP4格式（直接包含satellites列表）
        if 'satellites' in orbital_data:
            constellation_name = orbital_data.get('constellation', 'unknown')
            satellites_list = orbital_data.get('satellites', [])
            
            for sat_data in satellites_list:
                sat_data['constellation'] = constellation_name
                all_satellites.append(sat_data)
                
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
        
        # 返回符合後續階段期望的格式
        return {
            'metadata': {
                'total_satellites': len(filtered_satellites),
                'processing_complete': True
            },
            'satellites': filtered_satellites
        }
    
    def process_intelligent_filtering(self, orbital_data=None, save_output=True):
        """
        兼容性方法：保持與原有API接口一致
        """
        logger.info("🔄 使用兼容性API呼叫process_intelligent_filtering")
        
        # 開始處理計時
        self.start_processing_timer()
        
        # 🎯 CRITICAL FIX: 如果提供了orbital_data，直接使用而不是從文件載入
        if orbital_data:
            logger.info("📊 使用提供的orbital_data而非從文件載入")
            result = self._process_with_data(orbital_data)
        else:
            result = self.process()
        
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
        
        return result

    def extract_key_metrics(self, processing_results: Dict[str, Any]) -> Dict[str, Any]:
        """提取 Stage 2 關鍵指標"""
        metadata = processing_results.get('metadata', {})
        constellations = processing_results.get('constellations', {})
        
        # 計算總輸入和輸出
        total_input = metadata.get('input_satellites', 0)
        total_output = sum(data.get('satellite_count', 0) for data in constellations.values())
        
        starlink_count = constellations.get('starlink', {}).get('satellite_count', 0)
        oneweb_count = constellations.get('oneweb', {}).get('satellite_count', 0)
        
        filtering_rate = (total_output / max(total_input, 1)) * 100
        
        return {
            "輸入衛星": total_input,
            "輸出衛星": total_output,
            "Starlink篩選": starlink_count,
            "OneWeb篩選": oneweb_count,
            "篩選率": f"{filtering_rate:.1f}%",
            "地理相關性": f"{total_output}顆",
            "處理模式": "取樣模式" if self.sample_mode else "全量模式"
        }
    
    def run_validation_checks(self, processing_results: Dict[str, Any]) -> Dict[str, Any]:
        """執行 Stage 2 驗證檢查 - 專注於地理篩選準確性"""
        metadata = processing_results.get('metadata', {})
        constellations = processing_results.get('constellations', {})
        
        checks = {}
        
        # 1. 輸入數據存在性檢查
        filtering_stats = metadata.get('filtering_stats', {})
        total_input = filtering_stats.get('input_satellites', metadata.get('input_satellites', 0))
        checks["輸入數據存在性"] = total_input > 0
        
        # 2. 篩選效果檢查 - 確保篩選出合理數量的地理相關衛星
        total_output = filtering_stats.get('output_satellites', metadata.get('total_satellites', 0))
        filtering_rate = (total_output / max(total_input, 1)) * 100
        
        if self.sample_mode:
            checks["篩選效果檢查"] = 5 <= filtering_rate <= 70  # 取樣模式寬鬆
        else:
            # 地理篩選應該保留25-45%的衛星（排除地理上不相關的）
            checks["篩選效果檢查"] = 25 <= filtering_rate <= 45
        
        # 3. 星座完整性檢查 - 確保兩個星座都有篩選結果
        constellation_names = list(constellations.keys())
        checks["星座完整性檢查"] = ValidationCheckHelper.check_constellation_presence(
            constellation_names, ['starlink', 'oneweb']
        )
        
        # 4. 地理篩選平衡性檢查 - 確保兩個星座都有合理的篩選結果
        starlink_count = constellations.get('starlink', {}).get('satellite_count', 0)
        oneweb_count = constellations.get('oneweb', {}).get('satellite_count', 0)
        
        if self.sample_mode:
            checks["地理篩選平衡性"] = starlink_count >= 10 and oneweb_count >= 3
        else:
            # 確保兩個星座都有足夠的地理相關衛星
            starlink_ok = starlink_count >= 1000  # Starlink應該有較多數量
            oneweb_ok = oneweb_count >= 50       # OneWeb應該有合理數量
            checks["地理篩選平衡性"] = starlink_ok and oneweb_ok
        
        # 5. 數據完整性檢查 - 確保metadata結構正確
        required_fields = ['processing_timestamp', 'filtering_stats', 'total_satellites']
        checks["數據完整性檢查"] = ValidationCheckHelper.check_data_completeness(
            metadata, required_fields
        )
        
        # 6. 處理時間檢查 - 地理篩選應該相對快速
        max_time = 200 if self.sample_mode else 120  # 取樣3.3分鐘，全量2分鐘
        checks["處理時間合理性"] = ValidationCheckHelper.check_processing_time(
            self.processing_duration, max_time
        )
        
        # 計算通過的檢查數量
        passed_checks = sum(1 for passed in checks.values() if passed)
        total_checks = len(checks)
        
        return {
            "passed": passed_checks == total_checks,
            "totalChecks": total_checks,
            "passedChecks": passed_checks,
            "failedChecks": total_checks - passed_checks,
            "criticalChecks": [
                {"name": "輸入數據存在性", "status": "passed" if checks["輸入數據存在性"] else "failed"},
                {"name": "篩選效果檢查", "status": "passed" if checks["篩選效果檢查"] else "failed"},
                {"name": "星座完整性檢查", "status": "passed" if checks["星座完整性檢查"] else "failed"},
                {"name": "地理篩選平衡性", "status": "passed" if checks["地理篩選平衡性"] else "failed"}
            ],
            "allChecks": checks
        }


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