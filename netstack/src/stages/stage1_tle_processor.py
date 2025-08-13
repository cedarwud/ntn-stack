#!/usr/bin/env python3
"""
階段一：TLE數據載入與SGP4軌道計算

完全遵循 @docs/satellite_data_preprocessing.md 規範：
- 只做 TLE 載入和 SGP4 軌道計算
- 絕對不做任何篩選或取樣
- 全量處理 8,715 顆衛星 (8,064 Starlink + 651 OneWeb)
- 輸出完整的軌道數據供階段二使用
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

# 添加必要路徑
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/src')

# 引用現有的模組
from src.services.satellite.sgp4_engine import SGP4Engine, create_sgp4_engine
from src.services.satellite.coordinate_specific_orbit_engine import CoordinateSpecificOrbitEngine
from config.unified_satellite_config import get_unified_config

logger = logging.getLogger(__name__)

class Stage1TLEProcessor:
    """階段一：純TLE數據載入與SGP4軌道計算處理器
    
    職責：
    1. 掃描和載入 TLE 數據
    2. 使用 SGP4 算法計算所有衛星軌道
    3. 輸出完整的 8,715 顆衛星數據
    4. 絕對不做任何篩選或取樣
    """
    
    def __init__(self, tle_data_dir: str = "/app/tle_data", output_dir: str = "/app/data", debug_mode: bool = True):
        self.tle_data_dir = Path(tle_data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.debug_mode = debug_mode  # 控制是否生成檔案
        
        # 載入配置（只使用觀測點座標，忽略取樣配置）
        try:
            self.config = get_unified_config()
            self.observer_lat = self.config.observer.latitude
            self.observer_lon = self.config.observer.longitude
            self.observer_alt = self.config.observer.altitude_m
        except Exception as e:
            logger.warning(f"配置載入失敗，使用預設值: {e}")
            self.observer_lat = 24.9441667
            self.observer_lon = 121.3713889
            self.observer_alt = 50.0
            
        logger.info("✅ 階段一處理器初始化完成")
        logger.info(f"  TLE 數據目錄: {self.tle_data_dir}")
        logger.info(f"  輸出目錄: {self.output_dir}")
        logger.info(f"  觀測座標: ({self.observer_lat}°, {self.observer_lon}°)")
        logger.info(f"  Debug 模式: {'啟用 (將生成檔案)' if self.debug_mode else '停用 (即時處理模式)'}")
        
    def scan_tle_data(self) -> Dict[str, Any]:
        """掃描所有可用的 TLE 數據檔案"""
        logger.info("🔍 掃描 TLE 數據檔案...")
        
        scan_result = {
            'constellations': {},
            'total_constellations': 0,
            'total_files': 0,
            'total_satellites': 0
        }
        
        for constellation in ['starlink', 'oneweb']:
            tle_dir = self.tle_data_dir / constellation / "tle"
            
            if not tle_dir.exists():
                logger.warning(f"TLE 目錄不存在: {tle_dir}")
                continue
                
            tle_files = list(tle_dir.glob(f"{constellation}_*.tle"))
            
            if not tle_files:
                logger.warning(f"未找到 {constellation} TLE 檔案")
                continue
                
            # 找出最新日期的檔案
            latest_date = None
            latest_file = None
            latest_satellite_count = 0
            
            for tle_file in tle_files:
                date_str = tle_file.stem.split('_')[-1]
                if latest_date is None or date_str > latest_date:
                    latest_date = date_str
                    latest_file = tle_file
                    
                    # 計算衛星數量
                    if tle_file.stat().st_size > 0:
                        with open(tle_file, 'r', encoding='utf-8') as f:
                            lines = len([l for l in f if l.strip()])
                        latest_satellite_count = lines // 3
                        
            scan_result['constellations'][constellation] = {
                'files_count': len(tle_files),
                'latest_date': latest_date,
                'latest_file': str(latest_file),
                'satellite_count': latest_satellite_count
            }
            
            scan_result['total_files'] += len(tle_files)
            scan_result['total_satellites'] += latest_satellite_count
            
            logger.info(f"📡 {constellation} 掃描結果: {len(tle_files)} 個檔案, 最新({latest_date}): {latest_satellite_count} 顆衛星")
        
        scan_result['total_constellations'] = len(scan_result['constellations'])
        
        logger.info(f"🎯 TLE掃描完成: 總計 {scan_result['total_satellites']} 顆衛星")
        logger.info(f"   掃描結果: {scan_result['total_constellations']} 個星座, {scan_result['total_files']} 個文件")
        
        return scan_result
        
    def load_raw_satellite_data(self, scan_result: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """載入所有原始衛星數據（全量，無篩選）"""
        logger.info("📥 載入所有原始衛星數據...")
        
        all_raw_satellites = {}
        
        for constellation, info in scan_result['constellations'].items():
            logger.info(f"   處理 {constellation} 星座...")
            
            latest_file = Path(info['latest_file'])
            
            try:
                with open(latest_file, 'r', encoding='utf-8') as f:
                    tle_lines = f.readlines()
                
                satellites = []
                satellite_count = 0
                
                # 解析 TLE 數據
                for i in range(0, len(tle_lines), 3):
                    if i + 2 < len(tle_lines):
                        name_line = tle_lines[i].strip()
                        line1 = tle_lines[i + 1].strip()
                        line2 = tle_lines[i + 2].strip()
                        
                        if line1.startswith('1 ') and line2.startswith('2 '):
                            satellite_data = {
                                'satellite_id': f"{constellation}_{satellite_count:05d}",
                                'name': name_line,
                                'tle_line1': line1,
                                'tle_line2': line2,
                                'constellation': constellation
                            }
                            satellites.append(satellite_data)
                            satellite_count += 1
                
                all_raw_satellites[constellation] = satellites
                
                logger.info(f"從 {latest_file} 載入 {len(satellites)} 顆衛星")
                logger.info(f"{constellation}: 從 {info['latest_date']} 載入 {len(satellites)} 顆衛星")
                logger.info(f"   {constellation}: 載入 {len(satellites)} 顆原始衛星")
                
            except Exception as e:
                logger.error(f"載入 {constellation} 數據失敗: {e}")
                all_raw_satellites[constellation] = []
        
        total_loaded = sum(len(sats) for sats in all_raw_satellites.values())
        logger.info(f"✅ 原始數據載入完成: 總計 {total_loaded} 顆衛星")
        
        return all_raw_satellites
        
    def calculate_all_orbits(self, raw_satellite_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """對所有衛星進行 SGP4 軌道計算（全量處理）"""
        logger.info("🛰️ 開始全量 SGP4 軌道計算...")
        
        final_data = {
            'metadata': {
                'version': '1.0.0-stage1-only',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'processing_stage': 'stage1_tle_sgp4',
                'observer_coordinates': {
                    'latitude': self.observer_lat,
                    'longitude': self.observer_lon,
                    'altitude_m': self.observer_alt
                },
                'total_satellites': 0,
                'total_constellations': 0
            },
            'constellations': {}
        }
        
        total_processed = 0
        
        for constellation, satellites in raw_satellite_data.items():
            if not satellites:
                logger.warning(f"跳過 {constellation}: 無可用數據")
                continue
                
            logger.info(f"   執行 {constellation} SGP4軌道計算: {len(satellites)} 顆衛星")
            
            # 使用現有的軌道引擎
            orbit_engine = CoordinateSpecificOrbitEngine(
                observer_lat=self.observer_lat,
                observer_lon=self.observer_lon,
                observer_alt=self.observer_alt,
                min_elevation=0.0  # 階段一不做仰角篩選
            )
            
            constellation_data = {
                'satellite_count': len(satellites),
                'orbit_data': {
                    'satellites': {}  # 使用字典格式以保持與階段二的兼容性
                }
            }
            
            successful_calculations = 0
            
            for sat_data in satellites:
                try:
                    # 準備 TLE 數據格式
                    tle_data = {
                        'name': sat_data['name'],
                        'line1': sat_data['tle_line1'],
                        'line2': sat_data['tle_line2'],
                        'norad_id': 0  # 從 TLE 中提取
                    }
                    
                    # 從 TLE line1 提取 NORAD ID
                    try:
                        tle_data['norad_id'] = int(sat_data['tle_line1'][2:7])
                    except:
                        tle_data['norad_id'] = successful_calculations
                    
                    # 使用正確的軌道計算方法
                    orbit_result = orbit_engine.compute_96min_orbital_cycle(
                        tle_data,
                        datetime.now(timezone.utc)
                    )
                    
                    if orbit_result and 'positions' in orbit_result:
                        satellite_orbit_data = {
                            'satellite_id': sat_data['satellite_id'],
                            'name': sat_data['name'],
                            'constellation': constellation,
                            'tle_data': {
                                'line1': sat_data['tle_line1'],
                                'line2': sat_data['tle_line2']
                            },
                            'orbit_data': orbit_result,
                            'positions': orbit_result['positions']  # 提供階段二需要的位置數據
                        }
                        
                        # 儲存到字典格式中
                        constellation_data['orbit_data']['satellites'][sat_data['satellite_id']] = satellite_orbit_data
                        successful_calculations += 1
                        
                except Exception as e:
                    logger.warning(f"衛星 {sat_data['satellite_id']} 軌道計算失敗: {e}")
                    continue
                    
            final_data['constellations'][constellation] = constellation_data
            total_processed += successful_calculations
            
            logger.info(f"  {constellation}: {successful_calculations}/{len(satellites)} 顆衛星軌道計算完成")
        
        final_data['metadata']['total_satellites'] = total_processed
        final_data['metadata']['total_constellations'] = len(final_data['constellations'])
        
        logger.info(f"✅ 階段一完成: {total_processed} 顆衛星已完成完整軌道計算並格式化")
        
        return final_data
        
    def save_stage1_output(self, stage1_data: Dict[str, Any]) -> Optional[str]:
        """保存階段一輸出數據（根據 debug_mode 控制）"""
        if not self.debug_mode:
            logger.info("🚀 即時處理模式：跳過檔案生成，數據將直接傳遞給階段二")
            return None
            
        output_file = self.output_dir / "stage1_tle_sgp4_output.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(stage1_data, f, indent=2, ensure_ascii=False)
            
        logger.info(f"💾 Debug 模式：階段一數據已保存到: {output_file}")
        return str(output_file)
        
    def process_stage1(self) -> Dict[str, Any]:
        """執行完整的階段一處理流程"""
        logger.info("🚀 開始階段一：TLE數據載入與SGP4軌道計算")
        
        # 1. 掃描 TLE 數據
        scan_result = self.scan_tle_data()
        
        if scan_result['total_satellites'] == 0:
            raise RuntimeError("未找到任何 TLE 數據")
            
        # 2. 載入原始數據
        raw_satellite_data = self.load_raw_satellite_data(scan_result)
        
        if not raw_satellite_data:
            raise RuntimeError("載入原始衛星數據失敗")
            
        # 3. 全量 SGP4 軌道計算
        stage1_data = self.calculate_all_orbits(raw_satellite_data)
        
        # 4. 根據模式決定是否保存輸出
        output_file = self.save_stage1_output(stage1_data)
        
        logger.info("✅ 階段一處理完成")
        logger.info(f"  處理的衛星數: {stage1_data['metadata']['total_satellites']}")
        
        if output_file:
            logger.info(f"  輸出檔案: {output_file}")
        else:
            logger.info("  即時處理模式: 數據已準備好直接傳遞給階段二")
        
        return stage1_data

def main():
    """主函數"""
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    logger.info("============================================================")
    logger.info("階段一：TLE數據載入與SGP4軌道計算")
    logger.info("============================================================")
    
    try:
        processor = Stage1TLEProcessor()
        result = processor.process_stage1()
        
        logger.info("🎉 階段一處理成功完成！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 階段一處理失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)