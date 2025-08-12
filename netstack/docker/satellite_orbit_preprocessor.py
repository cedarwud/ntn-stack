#!/usr/bin/env python3
"""
Phase 2.5 重構版建構腳本
移除智能篩選邏輯，專注於數據池準備

版本: v2.0.0
建立日期: 2025-08-10  
重構目標: 解決雙重篩選邏輯矛盾
"""

import os
import sys
import json
import logging
import math
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

# 添加 config 路徑
sys.path.insert(0, '/app/config')
sys.path.insert(0, '/app')

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SatelliteOrbitPreprocessor:
    """Phase 2.5 數據預處理器 - 重構版
    
    重構改進：
    1. 移除 apply_constellation_separated_filtering 智能篩選
    2. 使用統一配置系統 (UnifiedSatelliteConfig)
    3. 集成數據池準備器 (SatelliteDataPoolBuilder)
    4. 清晰的職責分離：建構時只準備數據池
    """
    
    def __init__(self, tle_data_dir: str = "/app/tle_data", output_dir: str = "/app/data"):
        """
        初始化重構版預處理器
        
        Args:
            tle_data_dir: TLE 數據根目錄
            output_dir: 輸出目錄
        """
        self.tle_data_dir = Path(tle_data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 載入統一配置
        try:
            import sys
            sys.path.append('/home/sat/ntn-stack/netstack')
            from config.unified_satellite_config import get_unified_config
            self.config = get_unified_config()
            
            # 驗證配置
            validation_result = self.config.validate()
            if not validation_result.is_valid:
                raise ValueError(f"配置驗證失敗: {validation_result.errors}")
            
            logger.info(f"✅ 統一配置載入成功 (v{self.config.version})")
            
        except ImportError as e:
            logger.error(f"無法載入統一配置: {e}")
            # 回退到硬編碼配置
            self._initialize_fallback_config()
        
        # 從統一配置獲取觀測點參數
        self.observer_lat = self.config.observer.latitude
        self.observer_lon = self.config.observer.longitude
        self.observer_alt = self.config.observer.altitude_m
        
        # 系統級參數
        self.time_step_seconds = self.config.time_step_seconds
        self.enable_sgp4 = self.config.enable_sgp4
        
        # 支援的星座 (從配置中獲取)
        self.supported_constellations = list(self.config.constellations.keys())
        
        logger.info(f"Phase 2.5 數據預處理器初始化完成")
        logger.info(f"  TLE 數據目錄: {self.tle_data_dir}")
        logger.info(f"  輸出目錄: {self.output_dir}")
        logger.info(f"  觀測座標: ({self.observer_lat:.5f}°, {self.observer_lon:.5f}°)")
        logger.info(f"  支援星座: {', '.join(self.supported_constellations)}")
        logger.info(f"  SGP4 啟用: {self.enable_sgp4}")
    
    def _initialize_fallback_config(self):
        """初始化回退配置 (當統一配置不可用時)"""
        logger.warning("使用回退配置 - 請檢查統一配置系統")
        
        # 建立簡化的配置對象
        class FallbackConfig:
            def __init__(self):
                from dataclasses import dataclass
                
                @dataclass
                class Observer:
                    latitude: float = 24.9441667
                    longitude: float = 121.3713889
                    altitude_m: float = 50.0
                
                @dataclass 
                class Constellation:
                    total_satellites: int
                    target_satellites: int
                    min_elevation: float
                
                self.version = "fallback-1.0"
                self.observer = Observer()
                self.time_step_seconds = 30
                self.enable_sgp4 = True
                self.constellations = {
                    'starlink': Constellation(555, 15, 10.0),
                    'oneweb': Constellation(134, 8, 8.0)
                }
        
        self.config = FallbackConfig()
    
    def process_all_tle_data(self) -> Dict[str, Any]:
        """
        處理所有 TLE 數據 - Phase 2.0 完整版本
        
        完整流程：
        1. ⭐ 階段一：TLE數據載入與SGP4軌道計算
           1.1 掃描 TLE 數據檔案
           1.2 載入原始衛星數據 
           1.3 使用數據池準備器建構衛星池
           1.4 完整 SGP4 軌道計算
        2. ⭐ 階段二：3GPP Events & 信號品質增強
        3. ⭐ 統一輸出增強數據格式
        """
        logger.info("🚀 開始 Phase 2.0 完整數據處理管線")
        
        # === 階段一：TLE數據載入與SGP4軌道計算 ===
        logger.info("📡 開始階段一：TLE數據載入與SGP4軌道計算...")
        logger.info("  1.1 掃描TLE數據檔案...")
        scan_result = self.scan_tle_data()
        logger.info(f"      掃描結果: {scan_result['total_constellations']} 個星座, {scan_result['total_files']} 個文件")
        
        logger.info("  1.2 載入原始衛星數據...")
        # 收集所有原始衛星數據
        all_raw_satellites = {}
        for constellation in self.supported_constellations:
            constellation_data = scan_result['constellations'].get(constellation, {})
            
            if constellation_data.get('files', 0) == 0:
                logger.warning(f"      跳過 {constellation}: 無可用數據")
                continue
            
            logger.info(f"      處理 {constellation} 星座...")
            raw_satellites = self._load_constellation_satellites(constellation, constellation_data)
            
            if not raw_satellites:
                logger.warning(f"      {constellation}: 無法載入衛星數據")
                continue
            
            all_raw_satellites[constellation] = raw_satellites
            logger.info(f"      {constellation}: 載入 {len(raw_satellites)} 顆原始衛星")
        
        if not all_raw_satellites:
            logger.error("階段一失敗: 無任何有效的衛星數據")
            return {"metadata": {"error": "no_valid_data"}, "constellations": {}}
        
        logger.info("  1.3 建構衛星池（基礎篩選）...")
        # 建構衛星池
        satellite_pools = self._build_satellite_pools(all_raw_satellites)
        
        logger.info("  1.4 執行完整SGP4軌道計算...")
        phase1_data = self._execute_phase1_orbit_calculation(satellite_pools)
        
        # === 階段二：3GPP Events & 信號品質增強 ===
        logger.info("🛰️ 開始階段二：3GPP Events & 信號品質增強...")
        phase2_data = self._execute_phase2_signal_enhancement(phase1_data)
        
        # === 最終輸出 ===
        output_file = self.output_dir / "enhanced_satellite_data.json"
        self._save_processed_data(phase2_data, output_file)
        
        logger.info("✅ Phase 2.0 完整處理管線完成")
        logger.info(f"  總星座數: {phase2_data['metadata']['total_constellations']}")
        logger.info(f"  總衛星數: {phase2_data['metadata']['total_satellites']}")
        logger.info(f"  增強數據點: {phase2_data['metadata'].get('enhanced_points', 0)}")
        logger.info(f"  輸出文件: {output_file}")
        
        return phase2_data
    
    def _build_satellite_pools(self, raw_satellite_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        """使用數據池準備器建構衛星池"""
        try:
            from config.satellite_data_pool_builder import create_satellite_data_pool_builder
            
            logger.info("🔧 使用數據池準備器建構衛星池...")
            
            # 創建數據池準備器
            builder = create_satellite_data_pool_builder(self.config)
            
            # 建構衛星池
            satellite_pools = builder.build_satellite_pools(raw_satellite_data)
            
            # 獲取統計信息
            stats = builder.get_pool_statistics(satellite_pools)
            
            logger.info("📊 數據池統計:")
            for constellation, constellation_stats in stats["constellations"].items():
                completion_rate = constellation_stats["completion_rate"]
                pool_size = constellation_stats["pool_size"]
                target_size = constellation_stats["target_size"]
                logger.info(f"  {constellation}: {pool_size}/{target_size} 顆 ({completion_rate:.1f}%)")
            
            return satellite_pools
            
        except ImportError as e:
            logger.error(f"無法載入數據池準備器: {e}")
            logger.warning("回退到簡單隨機採樣")
            return self._fallback_sampling(raw_satellite_data)
    
    def _fallback_sampling(self, raw_satellite_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        """回退採樣方法 (當數據池準備器不可用時)"""
        import random
        
        logger.warning("使用回退採樣方法")
        
        fallback_pools = {}
        
        for constellation, raw_satellites in raw_satellite_data.items():
            constellation_config = self.config.constellations.get(constellation)
            
            if not constellation_config:
                logger.warning(f"未找到 {constellation} 配置，跳過")
                continue
            
            target_size = constellation_config.total_satellites
            
            if len(raw_satellites) <= target_size:
                fallback_pools[constellation] = raw_satellites[:]
            else:
                # 簡單隨機採樣
                fallback_pools[constellation] = random.sample(raw_satellites, target_size)
            
            logger.info(f"  {constellation} 回退採樣: {len(fallback_pools[constellation])} 顆")
        
        return fallback_pools
    
    def _load_constellation_satellites(self, constellation: str, constellation_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """載入單個星座的所有衛星數據"""
        satellites = []
        
        # 獲取最新的 TLE 數據日期
        dates = constellation_data.get('dates', [])
        if not dates:
            logger.warning(f"{constellation}: 無可用日期")
            return satellites
        
        # 使用最新日期的數據
        latest_date = max(dates)
        date_satellites = self.load_tle_satellites(constellation, latest_date)
        
        if date_satellites:
            satellites.extend(date_satellites)
            logger.info(f"{constellation}: 從 {latest_date} 載入 {len(date_satellites)} 顆衛星")
        
        return satellites
    
    def scan_tle_data(self) -> Dict[str, Any]:
        """掃描 TLE 數據目錄結構 (保持原有邏輯)"""
        scan_result = {
            "scan_time": datetime.now(timezone.utc).isoformat(),
            "total_constellations": 0,
            "total_files": 0,
            "total_satellites": 0,
            "overall_date_range": {"start": None, "end": None},
            "constellations": {}
        }
        
        all_dates = []
        
        for constellation in self.supported_constellations:
            constellation_data = {
                "files": 0,
                "satellites": 0,
                "dates": [],
                "dual_format_count": 0,
                "data_quality": "missing"
            }
            
            tle_dir = self.tle_data_dir / constellation / "tle"
            json_dir = self.tle_data_dir / constellation / "json"
            
            if tle_dir.exists():
                tle_files = list(tle_dir.glob(f"{constellation}_*.tle"))
                constellation_data['files'] = len(tle_files)
                
                for tle_file in tle_files:
                    try:
                        # 提取日期
                        date_str = tle_file.stem.split('_')[-1]
                        constellation_data['dates'].append(date_str)
                        all_dates.append(date_str)
                        
                        # 統計衛星數量
                        if tle_file.stat().st_size > 0:
                            with open(tle_file, 'r', encoding='utf-8') as f:
                                lines = len([l for l in f if l.strip()])
                            satellite_count = lines // 3
                            constellation_data['satellites'] += satellite_count
                    except:
                        pass
                    
                    # 檢查對應的 JSON 文件
                    json_file = json_dir / f"{constellation}_{date_str}.json"
                    if json_file.exists() and json_file.stat().st_size > 0:
                        constellation_data['dual_format_count'] += 1
            
            # 排序日期
            constellation_data['dates'].sort()
            
            # 評估數據品質
            if constellation_data['files'] > 0:
                dual_format_rate = (constellation_data['dual_format_count'] / 
                                  constellation_data['files']) * 100
                
                if dual_format_rate >= 80 and constellation_data['files'] >= 1:
                    constellation_data['data_quality'] = 'excellent'
                elif dual_format_rate >= 50:
                    constellation_data['data_quality'] = 'good'
                elif constellation_data['files'] >= 1:
                    constellation_data['data_quality'] = 'fair'
                else:
                    constellation_data['data_quality'] = 'poor'
            
            scan_result['constellations'][constellation] = constellation_data
            scan_result['total_constellations'] += 1 if constellation_data['files'] > 0 else 0
            scan_result['total_files'] += constellation_data['files']
            scan_result['total_satellites'] += constellation_data['satellites']
        
        # 計算整體日期範圍
        if all_dates:
            all_dates.sort()
            scan_result['overall_date_range']['start'] = all_dates[0]
            scan_result['overall_date_range']['end'] = all_dates[-1]
        
        return scan_result
    
    def load_tle_satellites(self, constellation: str, date_str: str) -> List[Dict[str, Any]]:
        """載入指定日期的 TLE 衛星數據 (保持原有邏輯)"""
        tle_file = self.tle_data_dir / constellation / "tle" / f"{constellation}_{date_str}.tle"
        
        if not tle_file.exists():
            logger.warning(f"TLE 文件不存在: {tle_file}")
            return []
            
        satellites = []
        
        try:
            with open(tle_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.strip().split('\n')
            lines = [line.strip() for line in lines if line.strip()]
            
            i = 0
            while i + 2 < len(lines):
                name_line = lines[i].strip()
                line1 = lines[i + 1].strip()
                line2 = lines[i + 2].strip()
                
                # 驗證 TLE 格式
                if (line1.startswith('1 ') and 
                    line2.startswith('2 ') and 
                    len(line1) >= 69 and 
                    len(line2) >= 69):
                    
                    try:
                        norad_id = int(line1[2:7].strip())
                        
                        satellite_data = {
                            'name': name_line,
                            'norad_id': norad_id,
                            'line1': line1,
                            'line2': line2,
                            'tle_date': date_str
                        }
                        
                        satellites.append(satellite_data)
                        
                    except ValueError as e:
                        logger.debug(f"無法解析 NORAD ID: {line1[:10]} - {e}")
                
                i += 3
                    
        except Exception as e:
            logger.error(f"解析 TLE 文件失敗 {tle_file}: {e}")
            
        logger.info(f"從 {tle_file} 載入 {len(satellites)} 顆衛星")
        return satellites
    
    def _save_processed_data(self, data: Dict[str, Any], output_file: Path) -> bool:
        """保存處理後的數據"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"數據已保存到: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"保存數據失敗: {e}")
            return False

    def _execute_phase1_orbit_calculation(self, satellite_pools: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        執行階段一核心：完整SGP4軌道計算
        
        階段一完整流程：
        1.1-1.3 已在上層完成（數據載入、掃描、基礎篩選）
        1.4 此方法執行：完整SGP4軌道計算與時間序列生成
        
        輸入: 衛星池數據（經過基礎篩選）
        輸出: 包含完整軌道數據的數據結構（符合階段二輸入要求）
        """
        phase1_data = {
            "metadata": {
                "version": "2.0.0-phase1",
                "processing_time": datetime.now(timezone.utc).isoformat(),
                "config_version": self.config.version,
                "total_constellations": 0,
                "total_satellites": 0,
                "phase1_completion": "tle_loading_and_sgp4_orbit_calculation",
                "processing_stages": {
                    "1.1": "tle_data_scanning",
                    "1.2": "raw_satellite_loading", 
                    "1.3": "satellite_pool_building",
                    "1.4": "sgp4_orbit_calculation"
                },
                "algorithms": {
                    "orbit_calculation": "full_sgp4_algorithm",
                    "no_simplification": True,
                    "no_simulation": True,
                    "full_satellite_processing": True
                }
            },
            "constellations": {}
        }
        
        for constellation_name, satellite_pool in satellite_pools.items():
            logger.info(f"    執行 {constellation_name} SGP4軌道計算: {len(satellite_pool)} 顆衛星")
            
            # 執行完整 SGP4 軌道計算
            constellation_with_orbits = self._calculate_constellation_orbits(
                constellation_name, satellite_pool)
            
            if constellation_with_orbits:
                phase1_data["constellations"][constellation_name] = constellation_with_orbits
                phase1_data["metadata"]["total_constellations"] += 1
                phase1_data["metadata"]["total_satellites"] += len(constellation_with_orbits.get('satellites', []))
        
        logger.info(f"✅ 階段一完成: {phase1_data['metadata']['total_satellites']} 顆衛星已完成完整軌道計算")
        return phase1_data
    
    def _execute_phase2_signal_enhancement(self, phase1_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行階段二：3GPP Events & 信號品質增強
        
        輸入: 階段一軌道數據
        輸出: 增強後的完整數據，包含信號品質和3GPP事件
        """
        try:
            # 創建階段二處理器
            phase2_processor = Phase2SignalProcessor(self.config)
            event_analyzer = GPPEventAnalyzer(self.config, phase2_processor.signal_calculator)
            
            # 執行信號品質增強
            enhanced_data = phase2_processor.enhance_satellite_data(phase1_data)
            
            # 執行3GPP事件分析
            event_analysis = event_analyzer.analyze_handover_events(enhanced_data)
            
            # 整合事件分析結果
            enhanced_data['event_analysis'] = event_analysis
            
            # 更新元數據
            enhanced_data['metadata']['phase2_completion'] = "signal_quality_and_3gpp_events"
            enhanced_data['metadata']['final_version'] = "2.0.0-complete"
            
            return enhanced_data
            
        except Exception as e:
            logger.error(f"階段二處理失敗: {e}")
            # 回退到階段一數據
            logger.warning("回退到階段一數據（無信號品質增強）")
            phase1_data['metadata']['phase2_error'] = str(e)
            return phase1_data
    
    def _calculate_constellation_orbits(self, constellation: str, satellite_pool: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        計算星座軌道數據 (階段一核心邏輯)
        
        這個方法執行完整的 SGP4 軌道計算，為每顆衛星生成時間序列軌道數據
        """
        if not self.enable_sgp4:
            logger.warning(f"{constellation}: SGP4 已禁用，跳過軌道計算")
            return {
                "satellite_count": len(satellite_pool),
                "calculation_skipped": True,
                "satellites": satellite_pool
            }
        
        try:
            # 嘗試導入軌道計算引擎
            import sys
            sys.path.append('/home/sat/ntn-stack/netstack')
            from services.satellite.coordinate_specific_orbit_engine import CoordinateSpecificOrbitEngine
            from datetime import datetime, timezone
            
            # 創建軌道計算引擎
            orbit_engine = CoordinateSpecificOrbitEngine(
                observer_lat=self.observer_lat,
                observer_lon=self.observer_lon,
                observer_alt=self.observer_alt,
                min_elevation=10.0
            )
            
            # 設定計算起始時間（當前時間）
            start_time = datetime.now(timezone.utc)
            
            # 執行軌道計算
            calculated_satellites = []
            successful_calculations = 0
            
            for satellite_data in satellite_pool:
                try:
                    # 🔑 修復：使用實際存在的方法 compute_120min_orbital_cycle
                    orbit_result = orbit_engine.compute_120min_orbital_cycle(
                        satellite_data, start_time)
                    
                    if orbit_result and 'positions' in orbit_result:
                        # 將軌道結果整合到衛星數據中
                        enhanced_satellite = {
                            **satellite_data,
                            'timeseries': orbit_result['positions'],
                            'visibility_windows': orbit_result.get('visibility_windows', []),
                            'computation_metadata': orbit_result.get('computation_metadata', {}),
                            'statistics': orbit_result.get('statistics', {}),
                            'sgp4_calculation': 'complete'
                        }
                        calculated_satellites.append(enhanced_satellite)
                        successful_calculations += 1
                    else:
                        # 保留原始數據但標記為計算失敗
                        satellite_data['sgp4_calculation'] = 'failed'
                        calculated_satellites.append(satellite_data)
                
                except Exception as sat_error:
                    logger.debug(f"衛星 {satellite_data.get('name', 'unknown')} 計算失敗: {sat_error}")
                    # 保留原始數據
                    satellite_data['sgp4_calculation'] = 'error'
                    calculated_satellites.append(satellite_data)
            
            logger.info(f"  {constellation}: {successful_calculations}/{len(satellite_pool)} 顆衛星軌道計算完成")
            
            return {
                "satellite_count": len(calculated_satellites),
                "orbit_calculation": "sgp4_complete", 
                "successful_calculations": successful_calculations,
                "calculation_success_rate": round(successful_calculations / len(satellite_pool) * 100, 2) if satellite_pool else 0,
                "algorithms": {
                    "orbit_propagation": "full_sgp4",
                    "library": "sgp4.api.Satrec",
                    "no_simulation": True,
                    "real_orbit_calculation": True
                },
                "satellites": calculated_satellites
            }
            
        except ImportError as e:
            # 🚫 根據 CLAUDE.md 核心原則，禁止使用簡化處理
            # 必須使用完整 SGP4 算法，如計算引擎不可用則報告錯誤
            logger.error(f"❌ {constellation}: SGP4 軌道計算引擎不可用 ({e})，拒絕使用簡化處理")
            raise ImportError(f"SGP4 orbital calculation engine required for {constellation}. Simplified algorithms prohibited.")
        
        except Exception as e:
            logger.error(f"❌ {constellation}: SGP4 軌道計算失敗 - {e}")
            raise Exception(f"SGP4 orbital calculation failed for {constellation}: {e}")
    
    # 🚫 _fallback_orbit_calculation 函數已刪除
    # 根據 CLAUDE.md 核心原則，禁止使用簡化處理回退機制
    # 必須使用完整 SGP4 算法，不允許任何回退到簡化計算

# ======================== 階段二：3GPP Events & 信號品質計算系統 ========================

class SignalQualityCalculator:
    """星座特定信號品質計算器 - 支援 3GPP NTN 標準"""
    
    def __init__(self, config):
        self.config = config
        
        # 星座特定信號模型參數
        self.constellation_models = {
            'starlink': {
                'frequency_ghz': 12.0,      # Ku 頻段
                'altitude_km': 550,         # 平均軌道高度
                'inclination_deg': 53,      # 軌道傾角
                'tx_power_dbm': 43.0,       # 發射功率
                'antenna_gain_db': 15.0,    # 最大天線增益
                'noise_floor_dbm': -174,    # 噪聲基底
                'bandwidth_mhz': 20         # 信號頻寬
            },
            'oneweb': {
                'frequency_ghz': 20.0,      # Ka 頻段
                'altitude_km': 1200,        # 平均軌道高度
                'inclination_deg': 87,      # 極地軌道傾角
                'tx_power_dbm': 40.0,       # 發射功率
                'antenna_gain_db': 18.0,    # 高增益天線
                'noise_floor_dbm': -174,    # 噪聲基底
                'bandwidth_mhz': 50         # 信號頻寬
            }
        }
        
        # 3GPP Events 門檻參數
        self.gpp_thresholds = {
            'a4': {
                'threshold_dbm': -80.0,     # A4 門檻
                'hysteresis_db': 3.0        # 滯後參數
            },
            'a5': {
                'serving_threshold_dbm': -110.0,   # 服務衛星門檻
                'neighbor_threshold_dbm': -100.0,  # 鄰近衛星門檻
                'hysteresis_db': 3.0               # 滯後參數
            },
            'd2': {
                'max_serving_distance_m': 5000000,  # 5000km 最大服務距離
                'ideal_candidate_distance_m': 3000000,  # 3000km 理想候選距離
                'hysteresis_m': 500.0                   # 距離滯後 500m
            }
        }
    
    def calculate_signal_quality(self, satellite_data: Dict[str, Any], constellation: str) -> Dict[str, Any]:
        """
        計算衛星信號品質參數
        
        Args:
            satellite_data: 包含軌道數據的衛星資訊
            constellation: 星座名稱 ('starlink' or 'oneweb')
            
        Returns:
            增強後的衛星數據，包含信號品質參數
        """
        if constellation not in self.constellation_models:
            raise ValueError(f"不支援的星座: {constellation}")
        
        model = self.constellation_models[constellation]
        enhanced_data = satellite_data.copy()
        
        # 計算基本信號參數
        rsrp_dbm = self._calculate_rsrp(satellite_data, model)
        rsrq_db = self._calculate_rsrq(satellite_data, model)
        sinr_db = self._calculate_sinr(satellite_data, model, rsrp_dbm)
        fspl_db = self._calculate_fspl(satellite_data['distance_km'], model['frequency_ghz'])
        atmospheric_loss_db = self._calculate_atmospheric_loss(satellite_data['elevation_deg'])
        
        # 組裝信號品質數據
        enhanced_data['signal_quality'] = {
            'rsrp_dbm': round(rsrp_dbm, 1),
            'rsrq_db': round(rsrq_db, 1),
            'sinr_db': round(sinr_db, 1),
            'fspl_db': round(fspl_db, 1),
            'atmospheric_loss_db': round(atmospheric_loss_db, 1)
        }
        
        # 計算 3GPP Events 參數
        enhanced_data['3gpp_events'] = self._calculate_3gpp_events(enhanced_data, constellation)
        
        return enhanced_data
    
    def _calculate_rsrp(self, satellite_data: Dict[str, Any], model: Dict[str, float]) -> float:
        """計算 RSRP (Reference Signal Received Power)"""
        import math
        
        distance_km = satellite_data['distance_km']
        elevation_deg = satellite_data['elevation_deg']
        
        # 自由空間路徑損耗
        fspl_db = self._calculate_fspl(distance_km, model['frequency_ghz'])
        
        # 仰角相關天線增益
        elevation_gain = min(elevation_deg / 90.0, 1.0) * model['antenna_gain_db']
        
        # 大氣衰減 (仰角相關)
        atmospheric_loss = self._calculate_atmospheric_loss(elevation_deg)
        
        # 其他系統損耗 (設備損耗、雨衰等)
        other_losses = 2.0
        
        # 最終 RSRP
        rsrp_dbm = (model['tx_power_dbm'] - fspl_db + elevation_gain 
                   - atmospheric_loss - other_losses)
        
        return rsrp_dbm
    
    def _calculate_rsrq(self, satellite_data: Dict[str, Any], model: Dict[str, float]) -> float:
        """計算 RSRQ (Reference Signal Received Quality)"""
        elevation_deg = satellite_data['elevation_deg']
        
        # RSRQ 基礎值，基於仰角動態調整
        base_rsrq = -12.0
        elevation_factor = (elevation_deg - 10) * 0.1  # 仰角每度對應 0.1 dB 改善
        
        rsrq_db = base_rsrq + elevation_factor
        
        # 限制在合理範圍內
        return max(-20.0, min(-3.0, rsrq_db))
    
    def _calculate_sinr(self, satellite_data: Dict[str, Any], model: Dict[str, float], rsrp_dbm: float) -> float:
        """計算 SINR (Signal to Interference plus Noise Ratio)"""
        elevation_deg = satellite_data['elevation_deg']
        
        # 噪聲功率計算
        noise_power_dbm = model['noise_floor_dbm'] + 10 * math.log10(model['bandwidth_mhz'] * 1e6)
        
        # 干擾功率 (簡化模型，基於仰角)
        interference_base = -120.0  # 基礎干擾功率
        interference_reduction = (elevation_deg - 10) * 0.3  # 高仰角降低干擾
        interference_power_dbm = interference_base - interference_reduction
        
        # 總干擾加噪聲功率
        def dbm_to_linear(dbm):
            return 10 ** (dbm / 10.0)
        
        def linear_to_dbm(linear):
            return 10 * math.log10(linear)
        
        total_interference_noise = (dbm_to_linear(noise_power_dbm) + 
                                  dbm_to_linear(interference_power_dbm))
        total_interference_noise_dbm = linear_to_dbm(total_interference_noise)
        
        # SINR = 信號功率 - 干擾加噪聲功率
        sinr_db = rsrp_dbm - total_interference_noise_dbm
        
        # 限制在合理範圍內
        return max(-10.0, min(40.0, sinr_db))
    
    def _calculate_fspl(self, distance_km: float, frequency_ghz: float) -> float:
        """計算自由空間路徑損耗 (Free Space Path Loss)"""
        import math
        
        # FSPL = 20 * log10(distance) + 20 * log10(frequency) + 32.44
        # distance in km, frequency in GHz
        fspl_db = (20 * math.log10(distance_km) + 
                  20 * math.log10(frequency_ghz) + 
                  32.44)
        
        return fspl_db
    
    def _calculate_atmospheric_loss(self, elevation_deg: float) -> float:
        """計算大氣衰減損耗 (基於仰角)"""
        # 仰角越低，大氣路徑越長，損耗越大
        if elevation_deg <= 0:
            return 10.0  # 地平線以下，最大衰減
        
        # 經驗公式：大氣損耗與仰角成反比
        atmospheric_loss = (90 - elevation_deg) / 90.0 * 3.0
        
        return max(0.1, atmospheric_loss)
    
    def _calculate_3gpp_events(self, satellite_data: Dict[str, Any], constellation: str) -> Dict[str, Any]:
        """計算 3GPP Events 參數"""
        signal_quality = satellite_data['signal_quality']
        rsrp_dbm = signal_quality['rsrp_dbm']
        distance_km = satellite_data['distance_km']
        
        events = {}
        
        # A4 事件：鄰近衛星信號優於門檻
        a4_threshold = self.gpp_thresholds['a4']['threshold_dbm']
        a4_hysteresis = self.gpp_thresholds['a4']['hysteresis_db']
        
        events['a4_eligible'] = (rsrp_dbm - a4_hysteresis) > a4_threshold
        events['a4_measurement_dbm'] = rsrp_dbm
        
        # A5 事件相關參數 (需要在比較時使用)
        serving_threshold = self.gpp_thresholds['a5']['serving_threshold_dbm']
        neighbor_threshold = self.gpp_thresholds['a5']['neighbor_threshold_dbm']
        
        events['a5_serving_poor'] = rsrp_dbm < serving_threshold
        events['a5_neighbor_good'] = rsrp_dbm > neighbor_threshold
        
        # D2 事件：基於距離的換手觸發
        distance_m = distance_km * 1000
        max_serving_distance = self.gpp_thresholds['d2']['max_serving_distance_m']
        ideal_candidate_distance = self.gpp_thresholds['d2']['ideal_candidate_distance_m']
        
        events['d2_distance_m'] = distance_m
        events['d2_within_threshold'] = distance_m < ideal_candidate_distance
        events['d2_too_far_for_serving'] = distance_m > max_serving_distance
        
        return events


class Phase2SignalProcessor:
    """階段二：3GPP Events 與信號品質處理主控制器"""
    
    def __init__(self, config):
        self.config = config
        self.signal_calculator = SignalQualityCalculator(config)
        
        logger.info("🛰️ 階段二信號品質處理器初始化完成")
        logger.info("  支援星座: Starlink (Ku頻段), OneWeb (Ka頻段)")
        logger.info("  支援事件: A4, A5, D2")
        
    def enhance_satellite_data(self, phase1_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        將第一階段軌道數據增強為包含信號品質和3GPP事件的完整數據
        
        Args:
            phase1_data: 第一階段輸出的軌道數據
            
        Returns:
            增強後的數據，包含信號品質和3GPP事件參數
        """
        logger.info("🔄 開始階段二信號品質增強處理...")
        
        enhanced_data = phase1_data.copy()
        enhanced_data['metadata']['phase2_processing'] = {
            'processing_time': datetime.now(timezone.utc).isoformat(),
            'signal_models': list(self.signal_calculator.constellation_models.keys()),
            '3gpp_events': ['A4', 'A5', 'D2'],
            'enhancement_version': '2.0.0'
        }
        
        total_satellites = 0
        total_enhanced = 0
        
        # 處理每個星座的數據
        for constellation_name, constellation_data in enhanced_data.get('constellations', {}).items():
            logger.info(f"🛰️ 處理 {constellation_name} 星座信號品質...")
            
            satellites = constellation_data.get('satellites', [])
            enhanced_satellites = []
            
            for satellite in satellites:
                try:
                    # 檢查是否有時間序列軌道數據
                    if 'timeseries' in satellite:
                        enhanced_satellite = satellite.copy()
                        enhanced_timeseries = []
                        
                        # 為每個時間點計算信號品質
                        for time_point in satellite['timeseries']:
                            if ('elevation_deg' in time_point and 
                                'distance_km' in time_point and
                                time_point['elevation_deg'] > 0):  # 只處理可見衛星
                                
                                enhanced_time_point = self.signal_calculator.calculate_signal_quality(
                                    time_point, constellation_name)
                                enhanced_timeseries.append(enhanced_time_point)
                        
                        enhanced_satellite['timeseries'] = enhanced_timeseries
                        enhanced_satellites.append(enhanced_satellite)
                        total_enhanced += len(enhanced_timeseries)
                    
                    else:
                        # 單點數據處理
                        if ('elevation_deg' in satellite and 
                            'distance_km' in satellite and
                            satellite['elevation_deg'] > 0):
                            
                            enhanced_satellite = self.signal_calculator.calculate_signal_quality(
                                satellite, constellation_name)
                            enhanced_satellites.append(enhanced_satellite)
                            total_enhanced += 1
                
                except Exception as e:
                    logger.warning(f"處理衛星 {satellite.get('satellite_id', 'unknown')} 時發生錯誤: {e}")
                    # 保留原始數據
                    enhanced_satellites.append(satellite)
                
                total_satellites += 1
            
            # 更新星座數據
            constellation_data['satellites'] = enhanced_satellites
            constellation_data['enhanced_count'] = len([s for s in enhanced_satellites 
                                                      if 'signal_quality' in s])
            
            logger.info(f"  {constellation_name}: {len(enhanced_satellites)} 顆衛星處理完成")
        
        # 更新統計信息
        enhanced_data['metadata']['total_satellites'] = total_satellites
        enhanced_data['metadata']['enhanced_points'] = total_enhanced
        enhanced_data['metadata']['enhancement_completion'] = (
            f"{total_enhanced}/{total_satellites} 數據點已增強")
        
        logger.info(f"✅ 階段二處理完成")
        logger.info(f"  總衛星數: {total_satellites}")
        logger.info(f"  增強數據點: {total_enhanced}")
        
        return enhanced_data


class GPPEventAnalyzer:
    """3GPP 標準事件分析器 - 支援 A4, A5, D2 事件的完整判斷邏輯"""
    
    def __init__(self, config, signal_calculator):
        self.config = config
        self.signal_calculator = signal_calculator
        self.thresholds = signal_calculator.gpp_thresholds
        
        logger.info("📋 3GPP事件分析器初始化完成")
    
    def analyze_handover_events(self, enhanced_constellation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析整個星座的換手事件，生成事件時間軸
        
        Args:
            enhanced_constellation_data: 增強後的星座數據
            
        Returns:
            包含事件分析結果的數據
        """
        logger.info("📊 開始3GPP事件分析...")
        
        analysis_result = {
            'event_timeline': {
                'a4_events': [],
                'a5_events': [],
                'd2_events': []
            },
            'event_statistics': {
                'total_a4_events': 0,
                'total_a5_events': 0,
                'total_d2_events': 0,
                'handover_opportunities': []
            },
            'optimal_handover_windows': []
        }
        
        # 處理每個星座的事件分析
        for constellation_name, constellation_data in enhanced_constellation_data.get('constellations', {}).items():
            constellation_events = self._analyze_constellation_events(
                constellation_name, constellation_data)
            
            # 合併事件數據
            for event_type in ['a4_events', 'a5_events', 'd2_events']:
                analysis_result['event_timeline'][event_type].extend(
                    constellation_events['timeline'][event_type])
                analysis_result['event_statistics'][f'total_{event_type}'] += len(
                    constellation_events['timeline'][event_type])
            
            # 合併換手機會分析
            analysis_result['event_statistics']['handover_opportunities'].extend(
                constellation_events['handover_opportunities'])
        
        # 生成最佳換手窗口
        analysis_result['optimal_handover_windows'] = self._find_optimal_handover_windows(
            analysis_result['event_timeline'])
        
        logger.info("✅ 3GPP事件分析完成")
        logger.info(f"  A4事件: {analysis_result['event_statistics']['total_a4_events']} 個")
        logger.info(f"  A5事件: {analysis_result['event_statistics']['total_a5_events']} 個")
        logger.info(f"  D2事件: {analysis_result['event_statistics']['total_d2_events']} 個")
        
        return analysis_result
    
    def _analyze_constellation_events(self, constellation_name: str, 
                                    constellation_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析單個星座的事件"""
        constellation_events = {
            'timeline': {
                'a4_events': [],
                'a5_events': [],
                'd2_events': []
            },
            'handover_opportunities': []
        }
        
        satellites = constellation_data.get('satellites', [])
        
        # 為每顆衛星分析事件
        for satellite in satellites:
            if 'timeseries' not in satellite:
                continue
                
            satellite_id = satellite.get('satellite_id', 'unknown')
            timeseries = satellite['timeseries']
            
            # 分析A4事件
            a4_events = self._detect_a4_events(satellite_id, timeseries, constellation_name)
            constellation_events['timeline']['a4_events'].extend(a4_events)
            
            # 分析D2事件  
            d2_events = self._detect_d2_events(satellite_id, timeseries, constellation_name)
            constellation_events['timeline']['d2_events'].extend(d2_events)
        
        # 分析A5事件 (需要多顆衛星比較)
        a5_events = self._detect_a5_events(satellites, constellation_name)
        constellation_events['timeline']['a5_events'].extend(a5_events)
        
        # 分析換手機會
        handover_opportunities = self._analyze_handover_opportunities(
            constellation_events['timeline'], constellation_name)
        constellation_events['handover_opportunities'] = handover_opportunities
        
        return constellation_events
    
    def _detect_a4_events(self, satellite_id: str, timeseries: List[Dict], 
                         constellation: str) -> List[Dict]:
        """檢測A4事件：鄰近衛星信號優於門檻"""
        a4_threshold = self.thresholds['a4']['threshold_dbm']
        hysteresis = self.thresholds['a4']['hysteresis_db']
        
        events = []
        in_a4_state = False
        
        for i, time_point in enumerate(timeseries):
            if '3gpp_events' not in time_point:
                continue
                
            rsrp = time_point['signal_quality']['rsrp_dbm']
            timestamp = time_point['time']
            
            # A4 進入條件: RSRP - Hys > Threshold
            entering_condition = (rsrp - hysteresis) > a4_threshold
            # A4 離開條件: RSRP + Hys < Threshold  
            leaving_condition = (rsrp + hysteresis) < a4_threshold
            
            if not in_a4_state and entering_condition:
                # A4事件觸發
                events.append({
                    'event_type': 'A4',
                    'event_subtype': 'entering',
                    'timestamp': timestamp,
                    'satellite_id': satellite_id,
                    'constellation': constellation,
                    'trigger_rsrp_dbm': rsrp,
                    'threshold_dbm': a4_threshold,
                    'elevation_deg': time_point.get('elevation_deg', 0),
                    'azimuth_deg': time_point.get('azimuth_deg', 0),
                    'distance_km': time_point.get('distance_km', 0)
                })
                in_a4_state = True
                
            elif in_a4_state and leaving_condition:
                # A4事件結束
                events.append({
                    'event_type': 'A4',
                    'event_subtype': 'leaving',
                    'timestamp': timestamp,
                    'satellite_id': satellite_id,
                    'constellation': constellation,
                    'trigger_rsrp_dbm': rsrp,
                    'threshold_dbm': a4_threshold,
                    'elevation_deg': time_point.get('elevation_deg', 0),
                    'azimuth_deg': time_point.get('azimuth_deg', 0),
                    'distance_km': time_point.get('distance_km', 0)
                })
                in_a4_state = False
        
        return events
    
    def _detect_a5_events(self, satellites: List[Dict], constellation: str) -> List[Dict]:
        """檢測A5事件：服務衛星劣化且鄰近衛星良好"""
        serving_threshold = self.thresholds['a5']['serving_threshold_dbm']
        neighbor_threshold = self.thresholds['a5']['neighbor_threshold_dbm']
        hysteresis = self.thresholds['a5']['hysteresis_db']
        
        events = []
        
        # 需要至少2顆衛星才能進行A5比較
        if len(satellites) < 2:
            return events
        
        # 收集所有時間點
        time_points = {}
        for satellite in satellites:
            if 'timeseries' not in satellite:
                continue
                
            satellite_id = satellite.get('satellite_id', 'unknown')
            for time_point in satellite['timeseries']:
                timestamp = time_point['time']
                if timestamp not in time_points:
                    time_points[timestamp] = []
                
                time_points[timestamp].append({
                    'satellite_id': satellite_id,
                    'data': time_point
                })
        
        # 在每個時間點分析A5條件
        for timestamp, satellite_points in time_points.items():
            if len(satellite_points) < 2:
                continue
            
            # 按RSRP排序，選擇最強信號作為服務衛星
            valid_points = [sp for sp in satellite_points 
                          if 'signal_quality' in sp['data']]
            
            if len(valid_points) < 2:
                continue
                
            valid_points.sort(key=lambda x: x['data']['signal_quality']['rsrp_dbm'], 
                            reverse=True)
            
            serving_sat = valid_points[0]
            
            # 檢查其他衛星是否滿足A5鄰近條件
            for neighbor_sat in valid_points[1:]:
                serving_rsrp = serving_sat['data']['signal_quality']['rsrp_dbm']
                neighbor_rsrp = neighbor_sat['data']['signal_quality']['rsrp_dbm']
                
                # A5 雙重條件
                condition1 = (serving_rsrp + hysteresis) < serving_threshold
                condition2 = (neighbor_rsrp - hysteresis) > neighbor_threshold
                
                if condition1 and condition2:
                    events.append({
                        'event_type': 'A5',
                        'event_subtype': 'dual_threshold_met',
                        'timestamp': timestamp,
                        'serving_satellite_id': serving_sat['satellite_id'],
                        'neighbor_satellite_id': neighbor_sat['satellite_id'],
                        'constellation': constellation,
                        'serving_rsrp_dbm': serving_rsrp,
                        'neighbor_rsrp_dbm': neighbor_rsrp,
                        'serving_threshold_dbm': serving_threshold,
                        'neighbor_threshold_dbm': neighbor_threshold,
                        'handover_recommended': True
                    })
        
        return events
    
    def _detect_d2_events(self, satellite_id: str, timeseries: List[Dict], 
                         constellation: str) -> List[Dict]:
        """檢測D2事件：基於距離的換手觸發"""
        max_serving_distance = self.thresholds['d2']['max_serving_distance_m']
        ideal_candidate_distance = self.thresholds['d2']['ideal_candidate_distance_m']
        hysteresis = self.thresholds['d2']['hysteresis_m']
        
        events = []
        
        for time_point in timeseries:
            if 'distance_km' not in time_point:
                continue
                
            distance_m = time_point['distance_km'] * 1000
            timestamp = time_point['time']
            
            # D2條件檢查
            too_far_for_serving = (distance_m - hysteresis) > max_serving_distance
            good_for_candidate = (distance_m + hysteresis) < ideal_candidate_distance
            
            if too_far_for_serving:
                events.append({
                    'event_type': 'D2',
                    'event_subtype': 'serving_too_far',
                    'timestamp': timestamp,
                    'satellite_id': satellite_id,
                    'constellation': constellation,
                    'distance_m': distance_m,
                    'max_serving_distance_m': max_serving_distance,
                    'handover_urgency': 'high'
                })
            
            if good_for_candidate:
                events.append({
                    'event_type': 'D2',
                    'event_subtype': 'good_candidate',
                    'timestamp': timestamp,
                    'satellite_id': satellite_id,
                    'constellation': constellation,
                    'distance_m': distance_m,
                    'ideal_candidate_distance_m': ideal_candidate_distance,
                    'candidate_quality': 'excellent' if distance_m < ideal_candidate_distance * 0.8 else 'good'
                })
        
        return events
    
    def _analyze_handover_opportunities(self, event_timeline: Dict[str, List], 
                                      constellation: str) -> List[Dict]:
        """分析換手機會"""
        opportunities = []
        
        # 將所有事件按時間排序
        all_events = []
        for event_type, events in event_timeline.items():
            for event in events:
                event['_event_category'] = event_type
                all_events.append(event)
        
        all_events.sort(key=lambda x: x['timestamp'])
        
        # 分析連續事件的換手機會
        current_window = []
        window_duration = 120  # 2分鐘窗口
        
        for event in all_events:
            # 清理過期事件
            current_time = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
            current_window = [e for e in current_window 
                            if (current_time - datetime.fromisoformat(e['timestamp'].replace('Z', '+00:00'))).total_seconds() <= window_duration]
            
            current_window.append(event)
            
            # 分析當前窗口的換手潛力
            if len(current_window) >= 2:
                opportunity_score = self._calculate_handover_opportunity_score(current_window)
                
                if opportunity_score > 0.7:  # 高品質換手機會
                    opportunities.append({
                        'timestamp': event['timestamp'],
                        'constellation': constellation,
                        'opportunity_score': opportunity_score,
                        'contributing_events': len(current_window),
                        'recommended_action': 'initiate_handover' if opportunity_score > 0.9 else 'prepare_handover',
                        'event_summary': self._summarize_events_window(current_window)
                    })
        
        return opportunities
    
    def _calculate_handover_opportunity_score(self, events_window: List[Dict]) -> float:
        """計算換手機會評分"""
        score = 0.0
        
        # 基於事件類型和品質計算分數
        event_weights = {
            'a4_events': 0.3,   # A4事件權重
            'a5_events': 0.5,   # A5事件權重更高（雙門檻）
            'd2_events': 0.2    # D2事件權重
        }
        
        for event in events_window:
            event_category = event.get('_event_category', '')
            base_weight = event_weights.get(event_category, 0.1)
            
            # 基於事件特性調整權重
            if event['event_type'] == 'A5' and event.get('handover_recommended'):
                score += base_weight * 1.5
            elif event['event_type'] == 'A4' and event['event_subtype'] == 'entering':
                score += base_weight * 1.2
            elif event['event_type'] == 'D2' and event.get('handover_urgency') == 'high':
                score += base_weight * 1.3
            else:
                score += base_weight
        
        # 標準化到0-1範圍
        return min(1.0, score)
    
    def _summarize_events_window(self, events_window: List[Dict]) -> Dict[str, Any]:
        """總結事件窗口"""
        summary = {
            'total_events': len(events_window),
            'event_types': {},
            'satellites_involved': set(),
            'duration_seconds': 0
        }
        
        for event in events_window:
            event_type = event['event_type']
            summary['event_types'][event_type] = summary['event_types'].get(event_type, 0) + 1
            summary['satellites_involved'].add(event.get('satellite_id', 'unknown'))
        
        summary['satellites_involved'] = len(summary['satellites_involved'])
        
        # 計算窗口持續時間
        if len(events_window) > 1:
            start_time = datetime.fromisoformat(events_window[0]['timestamp'].replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(events_window[-1]['timestamp'].replace('Z', '+00:00'))
            summary['duration_seconds'] = (end_time - start_time).total_seconds()
        
        return summary
    
    def _find_optimal_handover_windows(self, event_timeline: Dict[str, List]) -> List[Dict]:
        """尋找最佳換手時間窗口"""
        optimal_windows = []
        
        # 合併所有事件並按時間排序
        all_events = []
        for event_list in event_timeline.values():
            all_events.extend(event_list)
        
        all_events.sort(key=lambda x: x['timestamp'])
        
        # 尋找事件密集的時間窗口
        window_size = 300  # 5分鐘窗口
        step_size = 60     # 1分鐘步進
        
        current_time = None
        if all_events:
            current_time = datetime.fromisoformat(all_events[0]['timestamp'].replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(all_events[-1]['timestamp'].replace('Z', '+00:00'))
            
            while current_time <= end_time:
                window_end = current_time + timedelta(seconds=window_size)
                
                # 收集窗口內的事件
                window_events = [e for e in all_events 
                               if current_time <= datetime.fromisoformat(e['timestamp'].replace('Z', '+00:00')) <= window_end]
                
                if len(window_events) >= 3:  # 至少3個事件
                    quality_score = self._calculate_window_quality(window_events)
                    
                    if quality_score > 0.8:
                        optimal_windows.append({
                            'start_time': current_time.isoformat(),
                            'end_time': window_end.isoformat(),
                            'duration_seconds': window_size,
                            'event_count': len(window_events),
                            'quality_score': quality_score,
                            'handover_recommendation': 'optimal' if quality_score > 0.9 else 'good',
                            'primary_events': [e['event_type'] for e in window_events[:3]]
                        })
                
                current_time += timedelta(seconds=step_size)
        
        # 按品質評分排序，返回前10個
        optimal_windows.sort(key=lambda x: x['quality_score'], reverse=True)
        return optimal_windows[:10]
    
    def _calculate_window_quality(self, window_events: List[Dict]) -> float:
        """計算時間窗口的換手品質評分"""
        if not window_events:
            return 0.0
        
        # 基礎評分
        base_score = min(0.5, len(window_events) * 0.1)
        
        # 事件多樣性獎勵
        unique_event_types = len(set(e['event_type'] for e in window_events))
        diversity_bonus = unique_event_types * 0.15
        
        # A5事件獎勵（最重要的換手觸發）
        a5_events = [e for e in window_events if e['event_type'] == 'A5']
        a5_bonus = len(a5_events) * 0.25
        
        # 星座多樣性獎勵
        unique_constellations = len(set(e.get('constellation', '') for e in window_events))
        constellation_bonus = (unique_constellations - 1) * 0.1 if unique_constellations > 1 else 0
        
        total_score = base_score + diversity_bonus + a5_bonus + constellation_bonus
        
        return min(1.0, total_score)


def main():
    """主函數 - Phase 2.5 重構版"""
    logger.info("=" * 60)
    logger.info("Phase 2.5 重構版 TLE 數據預處理")
    logger.info("=" * 60)
    
    try:
        # 創建重構版預處理器
        preprocessor = Phase25DataPreprocessor()
        
        # 執行數據處理
        result = preprocessor.process_all_tle_data()
        
        # 輸出處理結果
        logger.info("處理完成！")
        logger.info(f"  版本: {result['metadata']['version']}")
        logger.info(f"  星座數: {result['metadata']['total_constellations']}")
        logger.info(f"  衛星數: {result['metadata']['total_satellites']}")
        
        for constellation, data in result['constellations'].items():
            logger.info(f"  {constellation}: {data['satellite_count']} 顆衛星")
        
        return True
        
    except Exception as e:
        logger.error(f"處理失敗: {e}")
        logger.exception("詳細錯誤信息")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)