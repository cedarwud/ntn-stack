#!/usr/bin/env python3
"""
Phase 0: Docker 建置時預計算數據生成
在容器建置過程中執行軌道預計算，確保啟動時數據即時可用
"""

import sys
import os
import json
import time
import logging
from pathlib import Path
from datetime import datetime

# 添加路徑
sys.path.append('/app/src')
sys.path.append('/app')

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """主建置函數"""
    logger.info("🚀 開始 Phase 0 預計算數據建置")
    
    build_start_time = time.time()
    
    try:
        # 導入 Phase 0 模組
        from src.services.satellite.coordinate_specific_orbit_engine import CoordinateSpecificOrbitEngine
        from src.services.satellite.local_tle_loader import LocalTLELoader
        from src.services.satellite.ntpu_visibility_filter import NTPUVisibilityFilter
        
        # 初始化組件
        logger.info("📡 初始化軌道計算引擎")
        orbit_engine = CoordinateSpecificOrbitEngine()
        tle_loader = LocalTLELoader("tle_data")
        visibility_filter = NTPUVisibilityFilter()
        
        # 載入 TLE 數據
        logger.info("📊 載入 TLE 數據")
        starlink_data = tle_loader.load_collected_data('starlink')
        oneweb_data = tle_loader.load_collected_data('oneweb')
        
        if not starlink_data and not oneweb_data:
            logger.warning("⚠️ 沒有找到 TLE 數據，使用模擬數據")
            # 創建模擬數據用於建置
            starlink_data = create_mock_tle_data('starlink', 100)
            oneweb_data = create_mock_tle_data('oneweb', 50)
        
        # 執行預計算
        logger.info("⚙️ 執行軌道預計算")
        
        precomputed_data = {
            'metadata': {
                'generation_timestamp': datetime.now().isoformat(),
                'build_time_seconds': 0,  # 稍後更新
                'data_source': 'phase0_build'
            },
            'observer_location': {
                'name': 'NTPU',
                'lat': 24.94417,
                'lon': 121.37139,
                'alt': 50.0
            },
            'constellations': {}
        }
        
        # 處理 Starlink
        if starlink_data:
            logger.info("🛰️ 處理 Starlink 數據")
            starlink_results = orbit_engine.compute_visibility_windows(
                starlink_data, 
                observer_lat=24.94417,
                observer_lon=121.37139,
                observer_alt=50.0
            )
            precomputed_data['constellations']['starlink'] = starlink_results
        
        # 處理 OneWeb
        if oneweb_data:
            logger.info("🛰️ 處理 OneWeb 數據")
            oneweb_results = orbit_engine.compute_visibility_windows(
                oneweb_data,
                observer_lat=24.94417,
                observer_lon=121.37139,
                observer_alt=50.0
            )
            precomputed_data['constellations']['oneweb'] = oneweb_results
        
        # 更新建置時間
        build_duration = time.time() - build_start_time
        precomputed_data['metadata']['build_time_seconds'] = round(build_duration, 2)
        
        # 確保輸出目錄存在
        output_dir = Path('/app/data')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存預計算數據
        output_file = output_dir / 'phase0_precomputed_orbits.json'
        logger.info(f"💾 保存預計算數據: {output_file}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(precomputed_data, f, indent=2, ensure_ascii=False)
        
        # 生成建置摘要
        summary = {
            'build_timestamp': datetime.now().isoformat(),
            'build_duration_seconds': build_duration,
            'total_constellations': len(precomputed_data['constellations']),
            'total_satellites': sum(
                len(constellation.get('orbit_data', {})) 
                for constellation in precomputed_data['constellations'].values()
            ),
            'output_file_size_bytes': output_file.stat().st_size if output_file.exists() else 0,
            'status': 'success'
        }
        
        summary_file = output_dir / 'phase0_build_summary.json'
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Phase 0 建置完成！耗時 {build_duration:.2f}s")
        logger.info(f"📊 處理衛星數: {summary['total_satellites']}")
        logger.info(f"💾 輸出檔案大小: {summary['output_file_size_bytes']:,} bytes")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Phase 0 建置失敗: {e}")
        
        # 創建錯誤報告
        error_report = {
            'build_timestamp': datetime.now().isoformat(),
            'build_duration_seconds': time.time() - build_start_time,
            'status': 'failed',
            'error_message': str(e),
            'error_type': type(e).__name__
        }
        
        output_dir = Path('/app/data')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        error_file = output_dir / 'phase0_build_error.json'
        with open(error_file, 'w', encoding='utf-8') as f:
            json.dump(error_report, f, indent=2, ensure_ascii=False)
        
        return False

def create_mock_tle_data(constellation: str, count: int) -> list:
    """創建模擬 TLE 數據用於建置測試"""
    logger.info(f"🔧 創建 {constellation} 模擬數據 ({count} 顆衛星)")
    
    mock_data = []
    base_norad_id = 44713 if constellation == 'starlink' else 47844
    
    for i in range(count):
        satellite = {
            'name': f'{constellation.upper()}-{i+1}',
            'norad_id': str(base_norad_id + i),
            'line1': f'1 {base_norad_id + i:05d}U 19074A   21001.00000000  .00000000  00000-0  00000-0 0  9990',
            'line2': f'2 {base_norad_id + i:05d}  53.0000 290.0000 0001000  90.0000 270.0000 15.50000000000010'
        }
        mock_data.append(satellite)
    
    return mock_data

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
