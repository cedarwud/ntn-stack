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
    
    def __init__(self, tle_data_dir: str = "/app/tle_data", output_dir: str = "/app/data", debug_mode: bool = False, sample_size: int = 50):
        """
        階段一處理器初始化 - v3.0 重新設計版本
    
    Args:
        tle_data_dir: TLE數據目錄路徑
        output_dir: 輸出目錄路徑（僅用於臨時檔案清理）
        debug_mode: 處理模式控制
            - False (預設): 全量處理模式（8,735顆衛星）
            - True: 除錯取樣模式（每星座最多sample_size顆）
        sample_size: debug_mode=True時每個星座的取樣數量
    
    檔案儲存策略:
        - v3.0版本完全停用JSON檔案儲存（避免2.2GB問題）
        - 採用純記憶體傳遞給階段二
    """
    self.tle_data_dir = Path(tle_data_dir)
    self.output_dir = Path(output_dir)
    self.output_dir.mkdir(parents=True, exist_ok=True)
    
    # 🎯 v3.0 重新定義：debug_mode統一控制處理模式
    self.debug_mode = debug_mode  # True=取樣除錯, False=全量處理
    self.sample_size = sample_size  # 取樣數量
    
    # 載入配置（只使用觀測點座標）
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
        
    logger.info("✅ 階段一處理器初始化完成 (v3.0)")
    logger.info(f"  TLE 數據目錄: {self.tle_data_dir}")
    logger.info(f"  輸出目錄: {self.output_dir}")
    logger.info(f"  觀測座標: ({self.observer_lat}°, {self.observer_lon}°)")
    logger.info("  💾 檔案策略: 純記憶體傳遞（不生成任何JSON檔案）")
    
    if self.debug_mode:
        logger.info(f"  🔧 除錯模式: 啟用（每星座取樣 {self.sample_size} 顆衛星）")
    else:
        logger.info("  🚀 全量模式: 處理所有 8,735 顆衛星")
    """
    重新定義初始化參數語義：
    
    Args:
        debug_mode: 控制是否使用取樣模式進行快速除錯（預設False=全量處理）
        sampling_mode: 已廢棄，由debug_mode統一控制
        sample_size: debug_mode=True時的每個星座取樣數量
    """
    self.tle_data_dir = Path(tle_data_dir)
    self.output_dir = Path(output_dir)
    self.output_dir.mkdir(parents=True, exist_ok=True)
    
    # 🔄 重新定義語義：debug_mode控制取樣，不控制檔案儲存
    self.use_sampling = debug_mode  # debug_mode=True時使用取樣
    self.sample_size = sample_size  # 每個星座的取樣數量
    
    # 💾 檔案儲存策略：預設不儲存（避免2.2GB問題）
    self.save_to_file = False  # 一律不儲存到檔案，直接記憶體傳遞
    
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
    logger.info(f"  💾 儲存策略: 僅記憶體傳遞（避免2.2GB檔案）")
    
    if self.use_sampling:
        logger.info(f"  🔧 除錯模式: 啟用（每個星座取樣 {self.sample_size} 顆衛星）")
    else:
        logger.info(f"  🚀 生產模式: 全量處理（8,735顆衛星）")        
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
    """載入所有原始衛星數據 - v3.0 統一處理模式"""
    logger.info("📥 載入原始衛星數據...")
    
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
            
            # 🎯 v3.0 統一模式控制
            if self.debug_mode:
                # 除錯取樣模式：限制衛星數量
                original_count = len(satellites)
                satellites = satellites[:self.sample_size]
                logger.info(f"🔧 {constellation} 除錯取樣: {original_count} → {len(satellites)} 顆衛星")
            else:
                # 全量處理模式：使用所有衛星
                logger.info(f"🚀 {constellation}: 全量載入 {len(satellites)} 顆衛星")
            
            all_raw_satellites[constellation] = satellites
            logger.info(f"從 {latest_file} 處理完成: {len(satellites)} 顆衛星")
            
        except Exception as e:
            logger.error(f"載入 {constellation} 數據失敗: {e}")
            all_raw_satellites[constellation] = []
    
    total_loaded = sum(len(sats) for sats in all_raw_satellites.values())
    mode_info = f"除錯取樣 (每星座最多{self.sample_size}顆)" if self.debug_mode else "全量處理"
    logger.info(f"✅ 原始數據載入完成 ({mode_info}): 總計 {total_loaded} 顆衛星")
    
    return all_raw_satellites
    """載入所有原始衛星數據（支援取樣模式）"""
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
            
            # 🔧 使用新的取樣邏輯
            if self.use_sampling:
                original_count = len(satellites)
                satellites = satellites[:self.sample_size]  # 只取前N顆
                logger.info(f"🔧 {constellation} 除錯取樣: {original_count} → {len(satellites)} 顆衛星")
            else:
                logger.info(f"🚀 {constellation}: 載入 {len(satellites)} 顆衛星（全量模式）")
            
            all_raw_satellites[constellation] = satellites
            
            logger.info(f"從 {latest_file} 載入 {len(satellites)} 顆衛星")
            logger.info(f"{constellation}: 從 {info['latest_date']} 載入 {len(satellites)} 顆衛星")
            
        except Exception as e:
            logger.error(f"載入 {constellation} 數據失敗: {e}")
            all_raw_satellites[constellation] = []
    
    total_loaded = sum(len(sats) for sats in all_raw_satellites.values())
    mode_str = f"除錯取樣模式 (每個星座最多{self.sample_size}顆)" if self.use_sampling else "全量模式"
    logger.info(f"✅ 原始數據載入完成 ({mode_str}): 總計 {total_loaded} 顆衛星")
    
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
        """v3.0版本：完全停用檔案儲存，採用純記憶體傳遞策略"""
        logger.info("🚀 v3.0記憶體傳遞策略：不產生任何JSON檔案")
        
        # 🗑️ 清理任何可能存在的舊檔案
        legacy_files = [
            self.output_dir / "stage1_tle_sgp4_output.json",
            self.output_dir / "stage1_tle_sgp4_output.tmp",
        ]
        
        for legacy_file in legacy_files:
            if legacy_file.exists():
                logger.info(f"🗑️ 清理舊檔案: {legacy_file}")
                legacy_file.unlink()
                logger.info(f"  已刪除: {legacy_file}")
        
        logger.info("✅ v3.0策略：數據準備完成，將直接透過記憶體傳遞給階段二")
        logger.info("  💾 優勢：無2.2GB檔案、無I/O延遲、即時驗證")
        return None  # 不返回檔案路徑，表示採用記憶體傳遞
            
        output_file = self.output_dir / "stage1_tle_sgp4_output.json"
        
        logger.info(f"💾 Debug 模式：開始保存階段一數據到: {output_file}")
        
        try:
            # 使用更安全的JSON寫入方式，避免內存問題和格式錯誤
            import json
            import tempfile
            
            # 首先寫入臨時檔案
            temp_file = output_file.with_suffix('.tmp')
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                # 使用較小的indent來減少檔案大小，並確保ASCII安全
                json.dump(stage1_data, f, indent=1, ensure_ascii=True, separators=(',', ': '))
            
            # 驗證臨時檔案的JSON格式
            with open(temp_file, 'r', encoding='utf-8') as f:
                json.load(f)  # 驗證JSON格式
            
            # 如果驗證成功，將臨時檔案重命名為最終檔案
            if output_file.exists():
                output_file.unlink()
            temp_file.rename(output_file)
            
            logger.info(f"💾 Debug 模式：階段一數據已安全保存到: {output_file}")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"❌ 保存階段一數據失敗: {e}")
            # 清理臨時檔案
            if 'temp_file' in locals() and temp_file.exists():
                temp_file.unlink()
            return None
        
    def process_stage1(self) -> Dict[str, Any]:
        """執行完整的階段一處理流程"""
        logger.info("🚀 開始階段一：TLE數據載入與SGP4軌道計算")
        
        # 檢查現有檔案
        existing_data_file = self.output_dir / "stage1_tle_sgp4_output.json"
        
        # 💾 v3.0儲存策略：完全停用檔案儲存，純記憶體傳遞
        logger.info("🚀 v3.0記憶體傳遞模式：執行即時計算（不儲存檔案）")
        
        # 🗑️ 清理任何可能存在的舊檔案
        existing_data_file = self.output_dir / "stage1_tle_sgp4_output.json"
        if existing_data_file.exists():
            logger.info(f"🗑️ 清理舊檔案: {existing_data_file}")
            existing_data_file.unlink()
            logger.info(f"  已刪除: {existing_data_file}")
        
        # 執行計算（支援除錯取樣模式）
        stage1_data = self._execute_full_calculation()
            # 不存檔，確保 2.2GB 檔案不會持續存在
        
        logger.info("✅ 階段一處理完成")
        logger.info(f"  處理的衛星數: {stage1_data['metadata']['total_satellites']}")
        
        processing_mode = "除錯取樣模式" if self.debug_mode else "全量處理模式"
        logger.info(f"  🎯 處理模式: {processing_mode}")
        logger.info("  💾 v3.0記憶體傳遞：數據已準備好直接傳遞給階段二（零檔案儲存）")
        
        return stage1_data
        
    def _execute_full_calculation(self) -> Dict[str, Any]:
        """執行完整的計算流程（抽取為私有方法）"""
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