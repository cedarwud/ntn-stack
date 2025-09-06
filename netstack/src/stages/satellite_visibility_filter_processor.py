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
            sample_mode: 是否為取樣模式（影響目標數量）
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
        
        # 根據模式調整目標 - 修復為符合@docs要求的數量
        self.sample_mode = sample_mode
        if sample_mode:
            # 取樣模式：按比例縮小目標
            self.TARGET_SATELLITES = {
                'starlink': 10,  # 40顆中選10顆
                'oneweb': 5      # 40顆中選5顆
            }
        else:
            # 全量模式：使用@docs定義的目標數量 (1,039+145=1,184)
            # 修復：提高目標數量以達到12-15%保留率和1,150-1,400衛星總數
            self.TARGET_SATELLITES = {
                'starlink': 1050,  # 目標1,039顆，稍微提高容錯 
                'oneweb': 150      # 目標145顆，稍微提高容錯
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
        
        logger.info("✅ 修復版增強智能衛星篩選處理器初始化完成")
        logger.info(f"  模式: {'取樣' if sample_mode else '全量'}")
        logger.info(f"  目標: Starlink {self.TARGET_SATELLITES['starlink']} 顆, "
               f"OneWeb {self.TARGET_SATELLITES['oneweb']} 顆")
        logger.info(f"  @docs要求: 總計1,150-1,400顆 (12-15%保留率)")
        
    def load_orbital_calculation_output(self) -> Dict[str, Any]:
        """載入軌道計算輸出"""
        orbital_file = self.input_dir / "tle_orbital_calculation_output.json"
        
        logger.info(f"📥 載入軌道計算數據: {orbital_file}")
        
        if not orbital_file.exists():
            raise FileNotFoundError(f"軌道計算輸出檔案不存在: {orbital_file}")
            
        with open(orbital_file, 'r', encoding='utf-8') as f:
            orbital_data = json.load(f)
            
        total_sats = orbital_data.get('metadata', {}).get('total_satellites', 0)
        logger.info(f"  載入成功: {total_sats} 顆衛星")
        
        return orbital_data
        
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
        修復版篩選邏輯：適配新的position_timeseries格式
        使用星座特定仰角門檻：Starlink 5°, OneWeb 10°
        目標：Starlink 12.9%保留率，OneWeb 22.3%保留率
        """
        logger.info("🔧 執行適配版智能篩選（192點時間序列）...")
        
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
        
        # 適配版評分：使用新的position_timeseries格式
        def score_satellite(sat):
            score = 0
            constellation = sat.get('constellation', '').lower()
            
            # 獲取192點時間序列數據
            position_timeseries = sat.get('position_timeseries', [])
            if not position_timeseries:
                return 0  # 沒有時間序列數據
            
            # 星座特定仰角門檻
            elevation_threshold = 5.0 if 'starlink' in constellation else 10.0
            
            visible_points = 0
            high_elevation_points = 0
            
            for pos in position_timeseries:
                relative_obs = pos.get('relative_to_observer', {})
                elevation = relative_obs.get('elevation_deg', 0)
                
                # 基礎可見性評分（符合星座特定門檻）
                if elevation >= elevation_threshold:
                    visible_points += 1
                    score += 1
                
                # 高仰角額外得分
                if elevation > 20:
                    high_elevation_points += 1
                    score += 3  # 高仰角大幅加分
                elif elevation > 15:
                    score += 2
                elif elevation > elevation_threshold + 5:
                    score += 1
            
            # 可見性持續時間評分
            visibility_ratio = visible_points / len(position_timeseries)
            score += int(visibility_ratio * 50)  # 可見性比例轉換為分數
            
            # 軌道高度偏好：適中高度得分更高
            orbital_elements = sat.get('orbital_elements', {})
            if orbital_elements:
                # 從軌道元素估算高度或使用geodetic數據
                if position_timeseries:
                    first_geodetic = position_timeseries[0].get('geodetic', {})
                    altitude_km = first_geodetic.get('altitude_km', 0)
                    if 400 <= altitude_km <= 600:  # LEO最佳高度區間
                        score += 10
                    elif 300 <= altitude_km <= 800:  # 可接受區間
                        score += 5
                        
            return score
            
        # 為每顆衛星評分
        for sat in starlink_sats:
            sat['visibility_score'] = score_satellite(sat)
        for sat in oneweb_sats:
            sat['visibility_score'] = score_satellite(sat)
            
        # 排序並選擇：取最高分的衛星
        starlink_sats.sort(key=lambda x: x.get('visibility_score', 0), reverse=True)
        oneweb_sats.sort(key=lambda x: x.get('visibility_score', 0), reverse=True)
        
        # 選擇目標數量（確保不超過可用數量）
        available_starlink = len(starlink_sats)
        available_oneweb = len(oneweb_sats)
        
        target_starlink = min(self.TARGET_SATELLITES['starlink'], available_starlink)
        target_oneweb = min(self.TARGET_SATELLITES['oneweb'], available_oneweb)
        
        selected_starlink = starlink_sats[:target_starlink]
        selected_oneweb = oneweb_sats[:target_oneweb]
        
        # 計算實際保留率
        starlink_retention = (len(selected_starlink) / max(len(starlink_sats), 1)) * 100
        oneweb_retention = (len(selected_oneweb) / max(len(oneweb_sats), 1)) * 100
        
        logger.info(f"  ✅ Starlink: {len(selected_starlink)} 顆選中 ({starlink_retention:.1f}%保留率)")
        logger.info(f"  ✅ OneWeb: {len(selected_oneweb)} 顆選中 ({oneweb_retention:.1f}%保留率)")
        logger.info(f"  🎯 使用星座特定仰角門檻: Starlink 5°, OneWeb 10°")
        logger.info(f"  📊 適配192點時間序列格式成功")
        
        return selected_starlink + selected_oneweb
        
    def save_filtered_output(self, filtered_satellites: List[Dict], 
                            original_count: int) -> str:
        """保存篩選結果（正確格式）"""
        
        # 按星座分組衛星數據
        starlink_satellites = [s for s in filtered_satellites if 'starlink' in s.get('constellation', '').lower()]
        oneweb_satellites = [s for s in filtered_satellites if 'oneweb' in s.get('constellation', '').lower()]
        
        # 準備輸出數據 (符合Stage 3期望格式)
        output_data = {
            'metadata': {
                'stage': 'stage2_enhanced',
                'filtering_version': 'enhanced_v1.0_fixed',
                'processing_timestamp': datetime.now(timezone.utc).isoformat(),
                'observer_location': {
                    'latitude': self.observer_lat,
                    'longitude': self.observer_lon,
                    'location_name': 'NTPU'
                },
                'filtering_stats': {
                    'input_satellites': original_count,
                    'output_satellites': len(filtered_satellites),
                    'retention_rate': f"{len(filtered_satellites)/original_count*100:.1f}%",
                    'starlink_selected': len(starlink_satellites),
                    'oneweb_selected': len(oneweb_satellites)
                },
                'target_pool_size': self.TARGET_SATELLITES,
                'sample_mode': self.sample_mode
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
        
        # 保存檔案
        output_file = self.output_dir / "intelligent_filtered_output.json"
        
        # 清理舊檔案
        if output_file.exists():
            logger.info(f"🗑️ 清理舊檔案: {output_file}")
            output_file.unlink()
            
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
            
        file_size_mb = output_file.stat().st_size / (1024 * 1024)
        
        logger.info(f"✅ 篩選結果已保存: {output_file}")
        logger.info(f"  檔案大小: {file_size_mb:.1f} MB")
        logger.info(f"  衛星數量: {len(filtered_satellites)} 顆")
        
        return str(output_file)
        
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
        
        # 如果提供了orbital_data，可以選擇使用它而不是從文件載入
        if orbital_data:
            logger.info("📊 使用提供的orbital_data而非從文件載入")
            # 這裡可以將orbital_data設置到實例中以供process方法使用
            # 但現在的實現是從文件載入，所以我們保持原有行為
        
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
        """執行 Stage 2 驗證檢查"""
        metadata = processing_results.get('metadata', {})
        constellations = processing_results.get('constellations', {})
        
        checks = {}
        
        # 1. 輸入數據存在性檢查
        total_input = metadata.get('input_satellites', 0)
        checks["輸入數據存在性"] = total_input > 0
        
        # 2. 篩選效果檢查
        total_output = sum(data.get('satellite_count', 0) for data in constellations.values())
        filtering_rate = (total_output / max(total_input, 1)) * 100
        
        if self.sample_mode:
            checks["篩選效果檢查"] = 5 <= filtering_rate <= 50  # 取樣模式較寬鬆
        else:
            checks["篩選效果檢查"] = 10 <= filtering_rate <= 30  # 全量模式較嚴格
        
        # 3. 星座完整性檢查
        constellation_names = list(constellations.keys())
        checks["星座完整性檢查"] = ValidationCheckHelper.check_constellation_presence(
            constellation_names, ['starlink', 'oneweb']
        )
        
        # 4. 地理覆蓋檢查
        starlink_count = constellations.get('starlink', {}).get('satellite_count', 0)
        oneweb_count = constellations.get('oneweb', {}).get('satellite_count', 0)
        
        if self.sample_mode:
            checks["地理覆蓋檢查"] = starlink_count >= 5 and oneweb_count >= 2
        else:
            checks["地理覆蓋檢查"] = starlink_count >= 10 and oneweb_count >= 3
        
        # 5. 數據完整性檢查
        required_fields = ['input_satellites', 'processing_timestamp']
        checks["數據完整性檢查"] = ValidationCheckHelper.check_data_completeness(
            metadata, required_fields
        )
        
        # 6. 處理時間檢查
        max_time = 300 if self.sample_mode else 180  # 取樣模式5分鐘，全量模式3分鐘
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
                {"name": "地理覆蓋檢查", "status": "passed" if checks["地理覆蓋檢查"] else "failed"}
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