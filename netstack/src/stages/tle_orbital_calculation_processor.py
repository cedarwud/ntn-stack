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
    
    def __init__(self, tle_data_dir: str = "/app/tle_data", output_dir: str = "/app/data", sample_mode: bool = False, sample_size: int = 50):
        """
        階段一處理器初始化 - v3.1 重構版本（移除硬編碼座標）
        
        Args:
            tle_data_dir: TLE數據目錄路徑
            output_dir: 輸出目錄路徑（僅用於臨時檔案清理）
            sample_mode: 處理模式控制
                - False (預設): 全量處理模式（8,735顆衛星）
                - True: 取樣模式（每星座最多sample_size顆）
            sample_size: sample_mode=True時每個星座的取樣數量
        
        檔案儲存策略:
            - v3.0版本完全停用JSON檔案儲存（避免2.2GB問題）
            - 採用純記憶體傳遞給階段二
        
        重構改進:
            - 移除硬編碼NTPU座標
            - 使用統一觀測配置服務
            - 保持與統一配置系統的兼容性
        """
        self.tle_data_dir = Path(tle_data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 🎯 v3.1 重構：統一觀測配置管理
        self.sample_mode = sample_mode  # True=取樣模式, False=全量處理
        self.sample_size = sample_size  # 取樣數量
        
        # 🔧 重構：使用統一觀測配置服務（消除硬編碼）
        try:
            from shared_core.observer_config_service import get_ntpu_coordinates
            self.observer_lat, self.observer_lon, self.observer_alt = get_ntpu_coordinates()
            logger.info("✅ 使用統一觀測配置服務")
        except Exception as e:
            # 降級到統一配置系統
            try:
                self.config = get_unified_config()
                self.observer_lat = self.config.observer.latitude
                self.observer_lon = self.config.observer.longitude
                self.observer_alt = self.config.observer.altitude_m
                logger.info("✅ 使用統一配置系統")
            except Exception as e2:
                logger.error(f"配置載入完全失敗: {e}, {e2}")
                raise RuntimeError("無法載入觀測點配置，請檢查配置系統")
        
        logger.info("✅ 階段一處理器初始化完成 (v3.1 重構版)")
        logger.info(f"  TLE 數據目錄: {self.tle_data_dir}")
        logger.info(f"  輸出目錄: {self.output_dir}")
        logger.info(f"  觀測座標: ({self.observer_lat}°, {self.observer_lon}°)")
        logger.info("  📐 座標來源: 統一觀測配置服務（已消除硬編碼）")
        logger.info("  💾 檔案策略: 檔案保存模式（支援後續階段處理）")
        
        if self.sample_mode:
            logger.info(f"  🔬 取樣模式: 啟用（每星座取樣 {self.sample_size} 顆衛星）")
        else:
            logger.info("  🚀 全量模式: 處理所有 8,735 顆衛星")   
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
        """載入所有原始衛星數據 - v3.1 數據血統追蹤版本"""
        logger.info("📥 載入原始衛星數據...")
        
        all_raw_satellites = {}
        
        # 🎯 v3.1 使用統一的數據血統追蹤管理器
        try:
            from shared_core import get_lineage_manager, create_tle_data_source
            lineage_manager = get_lineage_manager()
            
            # 開始新的數據血統追蹤
            lineage_id = lineage_manager.start_new_lineage("satellite_orbital_data")
            logger.info(f"🎯 開始數據血統追蹤: {lineage_id}")
            
        except ImportError:
            # 降級到原有機制
            logger.warning("🔄 降級到傳統TLE數據來源追蹤機制")
            lineage_manager = None
        
        # 🎯 原有TLE數據來源追蹤機制（保持兼容性）
        self.tle_source_info = {
            'tle_files_used': {},
            'processing_timestamp': datetime.now(timezone.utc).isoformat(),
            'data_lineage': {}
        }
        
        processing_start_time = datetime.now(timezone.utc)
        input_data_sources = []
        
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
                            # 🎯 解析 TLE epoch 時間
                            tle_epoch_day = float(line1[20:32])  # 儒略日
                            tle_year = int(line1[18:20])
                            if tle_year < 57:
                                tle_year += 2000
                            else:
                                tle_year += 1900
                            
                            satellite_data = {
                                'satellite_id': f"{constellation}_{satellite_count:05d}",
                                'name': name_line,
                                'tle_line1': line1,
                                'tle_line2': line2,
                                'constellation': constellation,
                                # 🎯 新增：TLE 數據來源資訊
                                'tle_source_file': str(latest_file),
                                'tle_epoch_year': tle_year,
                                'tle_epoch_day': tle_epoch_day
                            }
                            satellites.append(satellite_data)
                            satellite_count += 1
                
                # 🎯 v3.0 統一模式控制
                if self.sample_mode:
                    # 取樣模式：限制衛星數量
                    original_count = len(satellites)
                    satellites = satellites[:self.sample_size]
                    logger.info(f"🔬 {constellation} 取樣模式: {original_count} → {len(satellites)} 顆衛星")
                else:
                    # 全量處理模式：使用所有衛星
                    logger.info(f"🚀 {constellation}: 全量載入 {len(satellites)} 顆衛星")
                
                all_raw_satellites[constellation] = satellites
                
                # 🎯 記錄 TLE 數據來源（兼容舊機制）
                file_stat = latest_file.stat()
                file_date = latest_file.name.split('_')[-1].replace('.tle', '')
                
                self.tle_source_info['tle_files_used'][constellation] = {
                    'file_path': str(latest_file),
                    'file_name': latest_file.name,
                    'file_date': file_date,
                    'file_size_bytes': file_stat.st_size,
                    'file_modified_time': datetime.fromtimestamp(file_stat.st_mtime, timezone.utc).isoformat(),
                    'satellites_count': len(satellites)
                }
                
                # 🎯 v3.1 添加到統一數據血統追蹤
                if lineage_manager:
                    data_source = create_tle_data_source(
                        tle_file_path=str(latest_file),
                        tle_date=file_date
                    )
                    input_data_sources.append(data_source)
                
                logger.info(f"從 {latest_file} 處理完成: {len(satellites)} 顆衛星")
                logger.info(f"📅 TLE 數據日期: {file_date}")
                
            except Exception as e:
                logger.error(f"載入 {constellation} 數據失敗: {e}")
                all_raw_satellites[constellation] = []
        
        # 🎯 v3.1 記錄處理階段到數據血統追蹤
        if lineage_manager and input_data_sources:
            try:
                lineage_manager.record_processing_stage(
                    stage_name="stage1_tle_data_loading",
                    input_data_sources=input_data_sources,
                    processing_start_time=processing_start_time,
                    configuration={
                        'sample_mode': self.sample_mode,
                        'sample_size': self.sample_size if self.sample_mode else None,
                        'observer_coordinates': {
                            'latitude': self.observer_lat,
                            'longitude': self.observer_lon,
                            'altitude_m': self.observer_alt
                        }
                    }
                )
                logger.info("✅ Stage 1 數據載入已記錄到數據血統追蹤")
            except Exception as e:
                logger.warning(f"數據血統記錄失敗，但不影響處理: {e}")
        
        total_loaded = sum(len(sats) for sats in all_raw_satellites.values())
        mode_info = f"取樣模式 (每星座最多{self.sample_size}顆)" if self.sample_mode else "全量處理"
        logger.info(f"✅ 原始數據載入完成 ({mode_info}): 總計 {total_loaded} 顆衛星")
        
        return all_raw_satellites
        
    def calculate_all_orbits(self, raw_satellite_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """對所有衛星進行 SGP4 軌道計算（全量處理） - 修復數據血統追蹤"""
        logger.info("🛰️ 開始全量 SGP4 軌道計算...")
        
        # 🎯 修復：將 processing_timestamp 和 tle_data_timestamp 分離
        current_time = datetime.now(timezone.utc)
        
        final_data = {
            'metadata': {
                'version': '1.0.0-tle-orbital-calculation',
                'processing_timestamp': current_time.isoformat(),
                'processing_stage': 'tle_orbital_calculation',
                'observer_coordinates': {
                    'latitude': self.observer_lat,
                    'longitude': self.observer_lon,
                    'altitude_m': self.observer_alt
                },
                # 🎯 修復：完整的TLE數據來源追蹤
                'tle_data_sources': getattr(self, 'tle_source_info', {}),
                'data_lineage': {
                    'input_tle_files': [info['file_path'] for info in getattr(self, 'tle_source_info', {}).get('tle_files_used', {}).values()],
                    'tle_dates': {const: info['file_date'] for const, info in getattr(self, 'tle_source_info', {}).get('tle_files_used', {}).items()},
                    'processing_mode': 'complete_sgp4_calculation',
                    # 🎯 新增：明確區分數據時間戳和處理時間戳
                    'data_timestamps': {
                        'tle_data_dates': {const: info['file_date'] for const, info in getattr(self, 'tle_source_info', {}).get('tle_files_used', {}).items()},
                        'processing_execution_time': current_time.isoformat(),
                        'calculation_base_time_strategy': 'tle_epoch_time'
                    }
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
                    
                    # 🎯 使用 TLE epoch 時間作為計算基準，而非當前時間
                    from datetime import timedelta
                    
                    # 計算 TLE epoch 對應的實際時間
                    tle_epoch_year = sat_data.get('tle_epoch_year', datetime.now().year)
                    tle_epoch_day = sat_data.get('tle_epoch_day', 1.0)
                    tle_epoch_date = datetime(tle_epoch_year, 1, 1, tzinfo=timezone.utc) + timedelta(days=tle_epoch_day - 1)
                    
                    # 🎯 重要修復：記錄實際使用的TLE epoch時間，而不是處理時間
                    logger.debug(f"衛星 {sat_data['satellite_id']}: TLE epoch = {tle_epoch_date.isoformat()}, 處理時間 = {current_time.isoformat()}")
                    
                    # 使用 TLE epoch 時間作為計算基準
                    orbit_result = orbit_engine.compute_96min_orbital_cycle(
                        tle_data,
                        tle_epoch_date  # 🎯 修復：使用 TLE epoch 時間而非當前時間
                    )
                    
                    if orbit_result and 'positions' in orbit_result:
                        satellite_orbit_data = {
                            'satellite_id': sat_data['satellite_id'],
                            'name': sat_data['name'],
                            'constellation': constellation,
                            'tle_data': {
                                'line1': sat_data['tle_line1'],
                                'line2': sat_data['tle_line2'],
                                # 🎯 修復：完整的TLE數據血統追蹤
                                'source_file': sat_data.get('tle_source_file', 'unknown'),
                                'source_file_date': self.tle_source_info.get('tle_files_used', {}).get(constellation, {}).get('file_date', 'unknown'),
                                'epoch_year': sat_data.get('tle_epoch_year', 'unknown'),
                                'epoch_day': sat_data.get('tle_epoch_day', 'unknown'),
                                'calculation_base_time': tle_epoch_date.isoformat(),
                                # 🎯 新增：明確數據血統記錄
                                'data_lineage': {
                                    'data_source_date': self.tle_source_info.get('tle_files_used', {}).get(constellation, {}).get('file_date', 'unknown'),
                                    'tle_epoch_date': tle_epoch_date.isoformat(),
                                    'processing_execution_date': current_time.isoformat(),
                                    'calculation_strategy': 'sgp4_with_tle_epoch_base'
                                }
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
        
        # 🎯 修復：在日誌中明確顯示數據血統信息
        for const, info in getattr(self, 'tle_source_info', {}).get('tle_files_used', {}).items():
            logger.info(f"  📅 {const} 數據來源日期: {info.get('file_date', 'unknown')} (TLE文件日期)")
        logger.info(f"  🕐 處理執行時間: {current_time.isoformat()}")
        
        logger.info(f"✅ 階段一完成: {total_processed} 顆衛星已完成完整軌道計算並格式化")
        
        return final_data
        
    def save_tle_calculation_output(self, tle_data: Dict[str, Any]) -> Optional[str]:
        """重新啟用檔案保存以支持階段二到六的數據讀取 - 修復數據血統追蹤"""
        logger.info("💾 重新啟用檔案保存模式以支持後續階段處理")
        
        # 生成輸出檔案路徑
        output_file = self.output_dir / "tle_orbital_calculation_output.json"
        
        try:
            # 🎯 修復：在保存前增強metadata，確保數據血統信息完整
            enhanced_metadata = tle_data.get('metadata', {}).copy()
            
            # 添加檔案保存特定的數據血統信息
            enhanced_metadata['file_output'] = {
                'output_file_path': str(output_file),
                'file_generation_time': datetime.now(timezone.utc).isoformat(),
                'data_governance': {
                    'data_source_dates': enhanced_metadata.get('data_lineage', {}).get('tle_dates', {}),
                    'processing_execution_date': enhanced_metadata.get('processing_timestamp'),
                    'file_purpose': 'stage1_to_stage6_data_transfer',
                    'data_freshness_note': 'TLE數據日期反映實際衛星軌道元素時間，處理時間戳反映計算執行時間'
                }
            }
            
            # 更新增強後的metadata
            tle_data['metadata'] = enhanced_metadata
            
            # 保存到 JSON 檔案
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(tle_data, f, ensure_ascii=False, indent=2)
            
            # 計算檔案大小
            file_size_mb = output_file.stat().st_size / (1024 * 1024)
            
            logger.info(f"✅ TLE軌道計算數據已保存: {output_file}")
            logger.info(f"  檔案大小: {file_size_mb:.1f} MB")
            logger.info(f"  包含衛星數: {tle_data['metadata']['total_satellites']}")
            logger.info(f"  包含星座數: {tle_data['metadata']['total_constellations']}")
            
            # 🎯 修復：明確顯示數據血統信息
            logger.info("  📊 數據血統摘要:")
            for const, date in enhanced_metadata.get('data_lineage', {}).get('tle_dates', {}).items():
                logger.info(f"    {const}: TLE數據日期 = {date}")
            logger.info(f"    處理執行時間: {enhanced_metadata.get('processing_timestamp')}")
            logger.info("    ✅ 數據血統追蹤: TLE來源日期與處理時間已正確分離")
            
            return str(output_file)
            
        except Exception as e:
            logger.error(f"保存TLE軌道計算數據失敗: {e}")
            return None  # 不返回檔案路徑，表示採用記憶體傳遞  # 不返回檔案路徑，表示採用記憶體傳遞
        
    def process_tle_orbital_calculation(self) -> Dict[str, Any]:
        """執行完整的TLE軌道計算處理流程"""
        logger.info("🚀 開始階段一：TLE數據載入與SGP4軌道計算")
        
        # 🔧 啟用檔案保存模式以支援後續階段
        logger.info("💾 啟用檔案保存模式以支援階段二到六處理")
        
        # 🗑️ 清理任何可能存在的舊檔案
        existing_data_file = self.output_dir / "tle_orbital_calculation_output.json"
        if existing_data_file.exists():
            logger.info(f"🗑️ 清理舊檔案: {existing_data_file}")
            existing_data_file.unlink()
            logger.info(f"  已刪除: {existing_data_file}")
        
        # 執行計算（支援取樣模式）
        tle_data = self._execute_full_calculation()
        
        # 💾 保存檔案以供後續階段使用
        output_file_path = self.save_tle_calculation_output(tle_data)
        
        logger.info("✅ TLE軌道計算處理完成")
        logger.info(f"  處理的衛星數: {tle_data['metadata']['total_satellites']}")
        
        processing_mode = "取樣模式" if self.sample_mode else "全量處理模式"
        logger.info(f"  🎯 處理模式: {processing_mode}")
        
        if output_file_path:
            logger.info(f"  💾 檔案已保存: {output_file_path}")
        else:
            logger.warning("  ⚠️ 檔案保存失敗")
        
        return tle_data
        
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
        tle_data = self.calculate_all_orbits(raw_satellite_data)
        
        return tle_data

def main():
    """主函數"""
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    logger.info("============================================================")
    logger.info("階段一：TLE數據載入與SGP4軌道計算")
    logger.info("============================================================")
    
    try:
        processor = Stage1TLEProcessor()
        result = processor.process_tle_orbital_calculation()
        
        logger.info("🎉 階段一處理成功完成！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 階段一處理失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

# 為了向後兼容，提供別名
TLEOrbitalCalculationProcessor = Stage1TLEProcessor

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)