#!/usr/bin/env python3
"""
簡化數據生成器 - 用於測試 Volume 共享架構
生成基本結構的預計算數據，驗證 volume 共享機制
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_simple_test_data():
    """生成簡化的測試數據"""
    logger.info("🚀 生成簡化測試數據...")
    
    # 基本結構數據
    test_data = {
        'generated_at': datetime.now().isoformat(),
        'computation_type': 'simplified_test',
        'observer_location': {
            'lat': 24.94417,
            'lon': 121.37139,
            'alt': 50,
            'name': 'NTPU'
        },
        'constellations': {
            'starlink': {
                'name': 'STARLINK',
                'orbit_data': {
                    'metadata': {
                        'start_time': datetime.now().isoformat(),
                        'duration_minutes': 360,
                        'time_step_seconds': 60,
                        'total_time_points': 360,
                        'observer_location': {
                            'lat': 24.94417,
                            'lon': 121.37139,
                            'alt': 50,
                            'name': 'NTPU'
                        }
                    },
                    'satellites': {}
                }
            }
        }
    }
    
    # 生成3顆模擬衛星數據
    logger.info("📡 生成模擬衛星數據...")
    for i in range(1, 4):
        sat_id = f"starlink_{i:03d}"
        norad_id = 44700 + i
        
        # 生成可見性數據
        visibility_data = []
        base_time = datetime.now()
        
        for t in range(360):  # 6小時數據
            timestamp = base_time.replace(second=0, microsecond=0) 
            timestamp = timestamp.replace(minute=t % 60, hour=timestamp.hour + t // 60)
            
            # 簡化的軌道計算
            orbit_progress = (t + i * 120) / 95  # 95分鐘軌道週期
            elevation = max(0, 45 - abs((t % 180) - 90))  # 模擬仰角變化
            is_visible = elevation > 10
            
            visibility_data.append({
                'timestamp': timestamp.isoformat(),
                'position': {
                    'latitude': 53 * (0.5 - (t % 190) / 190),  # -26.5 到 26.5
                    'longitude': ((t * 4) % 360) - 180,  # -180 到 180
                    'altitude': 550000 + (t % 20) * 1000  # 550-570 km
                },
                'elevation': elevation,
                'azimuth': (t * 2) % 360,
                'distance': 1000000 + (t % 100) * 10000,  # 1000-2000 km
                'is_visible': is_visible
            })
        
        test_data['constellations']['starlink']['orbit_data']['satellites'][sat_id] = {
            'satellite_id': sat_id,
            'norad_id': norad_id,
            'satellite_name': f'STARLINK-{i}',
            'tle_line1': f'1 {norad_id}U 19074A   24210.50000000  .00001234  00000-0  12345-3 0  9999',
            'tle_line2': f'2 {norad_id}  53.0534  95.4567 0001234  87.6543 272.3456 15.05000000123456',
            'visibility_data': visibility_data
        }
    
    return test_data

def main():
    """主函數"""
    logger.info("🚀 開始簡化數據生成...")
    
    try:
        # 確保輸出目錄存在
        output_dir = Path('/app/data')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成測試數據
        test_data = generate_simple_test_data()
        
        # 保存數據
        output_file = output_dir / 'phase0_precomputed_orbits.json'
        logger.info(f"💾 保存測試數據到: {output_file}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2, ensure_ascii=False)
        
        # 創建完成標記
        marker_file = output_dir / '.data_ready'
        with open(marker_file, 'w') as f:
            f.write(datetime.now().isoformat())
        
        # 顯示文件信息
        file_size = output_file.stat().st_size
        logger.info(f"✅ 數據生成完成，文件大小: {file_size / 1024 / 1024:.2f} MB")
        logger.info(f"✅ 創建完成標記: {marker_file}")
        
    except Exception as e:
        logger.error(f"❌ 數據生成失敗: {e}")
        raise

if __name__ == '__main__':
    main()