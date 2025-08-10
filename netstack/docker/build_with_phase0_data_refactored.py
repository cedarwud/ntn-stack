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
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

# 添加 config 路徑
sys.path.insert(0, '/app/config')
sys.path.insert(0, '/app')

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Phase25DataPreprocessor:
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
        處理所有 TLE 數據 - Phase 2.5 重構版
        
        流程改進：
        1. 掃描 TLE 數據
        2. 載入原始衛星數據  
        3. 使用數據池準備器建構衛星池 (替代智能篩選)
        4. 輸出標準化數據格式
        """
        logger.info("🚀 開始 Phase 2.5 TLE 數據處理")
        
        # 1. 掃描數據源
        scan_result = self.scan_tle_data()
        logger.info(f"掃描結果: {scan_result['total_constellations']} 個星座, {scan_result['total_files']} 個文件")
        
        # 2. 處理每個星座
        processed_data = {
            "metadata": {
                "version": "2.0.0-phase25",
                "processing_time": datetime.now(timezone.utc).isoformat(),
                "config_version": self.config.version,
                "total_constellations": 0,
                "total_satellites": 0
            },
            "constellations": {}
        }
        
        # 收集所有原始衛星數據
        all_raw_satellites = {}
        
        for constellation in self.supported_constellations:
            constellation_data = scan_result['constellations'].get(constellation, {})
            
            if constellation_data.get('files', 0) == 0:
                logger.warning(f"跳過 {constellation}: 無可用數據")
                continue
            
            logger.info(f"處理 {constellation} 星座...")
            
            # 載入原始衛星數據
            raw_satellites = self._load_constellation_satellites(constellation, constellation_data)
            
            if not raw_satellites:
                logger.warning(f"{constellation}: 無法載入衛星數據")
                continue
            
            all_raw_satellites[constellation] = raw_satellites
            logger.info(f"{constellation}: 載入 {len(raw_satellites)} 顆原始衛星")
        
        # 3. 使用數據池準備器建構衛星池
        if all_raw_satellites:
            satellite_pools = self._build_satellite_pools(all_raw_satellites)
            
            # 4. 格式化輸出數據
            for constellation, satellite_pool in satellite_pools.items():
                if satellite_pool:
                    processed_data["constellations"][constellation] = {
                        "satellite_count": len(satellite_pool),
                        "target_size": self.config.constellations[constellation].total_satellites,
                        "satellites": satellite_pool
                    }
                    processed_data["metadata"]["total_constellations"] += 1
                    processed_data["metadata"]["total_satellites"] += len(satellite_pool)
            
        # 5. 保存處理結果
        output_file = self.output_dir / "phase25_satellite_data.json"
        self._save_processed_data(processed_data, output_file)
        
        logger.info(f"✅ Phase 2.5 數據處理完成")
        logger.info(f"  總星座數: {processed_data['metadata']['total_constellations']}")
        logger.info(f"  總衛星數: {processed_data['metadata']['total_satellites']}")
        logger.info(f"  輸出文件: {output_file}")
        
        return processed_data
    
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