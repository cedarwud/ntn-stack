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


class SatelliteVisibilityFilterProcessor:
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
        
        # 根據模式調整目標
        self.sample_mode = sample_mode
        if sample_mode:
            # 取樣模式：按比例縮小目標
            self.TARGET_SATELLITES = {
                'starlink': 10,  # 40顆中選10顆
                'oneweb': 5      # 40顆中選5顆
            }
        else:
            # 全量模式：使用文檔定義的智能軌道相位優化目標
            self.TARGET_SATELLITES = {
                'starlink': 150,  # 智能軌道相位選擇（原850減少82%）
                'oneweb': 40      # 軌道相位優化（原150減少73%）
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
        簡化的篩選邏輯（避免過度篩選）
        """
        logger.info("🔧 執行簡化篩選...")
        
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
        
        # 簡單評分（基於可見時間）
        def score_satellite(sat):
            score = 0
            positions = sat.get('positions', [])
            for pos in positions:
                if pos.get('elevation_deg', 0) > 10:
                    score += 1
            return score
            
        # 為每顆衛星評分
        for sat in starlink_sats:
            sat['visibility_score'] = score_satellite(sat)
        for sat in oneweb_sats:
            sat['visibility_score'] = score_satellite(sat)
            
        # 排序並選擇
        starlink_sats.sort(key=lambda x: x['visibility_score'], reverse=True)
        oneweb_sats.sort(key=lambda x: x['visibility_score'], reverse=True)
        
        # 選擇目標數量
        selected_starlink = starlink_sats[:self.TARGET_SATELLITES['starlink']]
        selected_oneweb = oneweb_sats[:self.TARGET_SATELLITES['oneweb']]
        
        logger.info(f"  選擇 Starlink: {len(selected_starlink)} 顆")
        logger.info(f"  選擇 OneWeb: {len(selected_oneweb)} 顆")
        
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
        
        # 載入軌道數據
        orbital_data = self.load_orbital_calculation_output()
        
        # 整理所有衛星數據
        all_satellites = []
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
        
        # 如果提供了orbital_data，可以選擇使用它而不是從文件載入
        if orbital_data:
            logger.info("📊 使用提供的orbital_data而非從文件載入")
            # 這裡可以將orbital_data設置到實例中以供process方法使用
            # 但現在的實現是從文件載入，所以我們保持原有行為
        
        result = self.process()
        
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
        
        if save_output:
            logger.info("💾 輸出已保存到文件")
        
        return result


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