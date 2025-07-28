#!/usr/bin/env python3
"""
Docker 建置時預處理功能 - Phase 0 增強版
支援手動收集的 TLE 歷史數據預處理
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Phase0DataPreprocessor:
    """Phase 0 數據預處理器 - 真正的 SGP4 軌道預計算"""
    
    def __init__(self, tle_data_dir: str = "/app/tle_data", output_dir: str = "/app/data"):
        """
        初始化預處理器
        
        Args:
            tle_data_dir: TLE 數據根目錄
            output_dir: 輸出目錄
        """
        self.tle_data_dir = Path(tle_data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.supported_constellations = ['starlink', 'oneweb']
        
        # NTPU 觀測座標 (預設觀測點)
        self.observer_lat = 24.94417  # 24°56'39"N
        self.observer_lon = 121.37139  # 121°22'17"E 
        self.observer_alt = 50.0  # 海拔50米
        self.min_elevation = 5.0  # 最小仰角閾值
        
        # 預計算參數
        self.time_step_seconds = 30  # 30秒間隔
        self.orbital_period_minutes = 96  # 96分鐘軌道週期
        
        logger.info(f"Phase0DataPreprocessor 初始化 (SGP4 軌道預計算版)")
        logger.info(f"  TLE 數據目錄: {self.tle_data_dir}")
        logger.info(f"  輸出目錄: {self.output_dir}")
        logger.info(f"  觀測座標: ({self.observer_lat:.5f}, {self.observer_lon:.5f})")
    
    def scan_available_data(self) -> Dict[str, Any]:
        """掃描可用的數據"""
        scan_result = {
            'total_constellations': 0,
            'total_files': 0,
            'total_satellites': 0,
            'constellations': {},
            'overall_date_range': {
                'start': None,
                'end': None
            }
        }
        
        all_dates = []
        
        for constellation in self.supported_constellations:
            tle_dir = self.tle_data_dir / constellation / "tle"
            json_dir = self.tle_data_dir / constellation / "json"
            
            constellation_data = {
                'name': constellation,
                'files': 0,
                'satellites': 0,
                'dates': [],
                'dual_format_count': 0,
                'data_quality': 'unknown'
            }
            
            if tle_dir.exists():
                import glob
                import re
                
                # 掃描 TLE 文件
                tle_files = glob.glob(str(tle_dir / f"{constellation}_*.tle"))
                
                for tle_file in tle_files:
                    match = re.search(r'(\d{8})\.tle$', tle_file)
                    if match:
                        date_str = match.group(1)
                        file_path = Path(tle_file)
                        
                        if file_path.exists() and file_path.stat().st_size > 0:
                            constellation_data['files'] += 1
                            constellation_data['dates'].append(date_str)
                            all_dates.append(date_str)
                            
                            # 計算衛星數量（估算：每3行一顆衛星）
                            try:
                                with open(file_path, 'r') as f:
                                    lines = len([l for l in f if l.strip()])
                                satellite_count = lines // 3
                                constellation_data['satellites'] += satellite_count
                            except:
                                pass
                            
                            # 檢查是否有對應的 JSON 文件
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
                else:
                    constellation_data['data_quality'] = 'missing'
            
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
        """載入指定日期的 TLE 衛星數據"""
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
                        logger.warning(f"無法解析 NORAD ID: {line1[:10]} - {e}")
                
                i += 3
                    
        except Exception as e:
            logger.error(f"解析 TLE 文件失敗 {tle_file}: {e}")
            
        logger.info(f"從 {tle_file} 載入 {len(satellites)} 顆衛星")
        return satellites
    
    def compute_sgp4_orbit_positions(self, satellites: List[Dict[str, Any]], 
                                   start_time: datetime, duration_minutes: int = 96) -> Dict[str, Any]:
        """使用 SGP4 計算衛星軌道位置"""
        try:
            from sgp4.api import Satrec, jday
            from sgp4 import exporter
            import numpy as np
            from math import degrees, radians, sin, cos, sqrt, atan2, asin
            
            logger.info(f"開始 SGP4 軌道計算: {len(satellites)} 顆衛星, {duration_minutes} 分鐘")
            
            # 計算時間點
            total_seconds = duration_minutes * 60
            time_points = list(range(0, total_seconds, self.time_step_seconds))
            
            orbit_data = {
                'metadata': {
                    'start_time': start_time.isoformat(),
                    'duration_minutes': duration_minutes,
                    'time_step_seconds': self.time_step_seconds,
                    'total_time_points': len(time_points),
                    'observer_location': {
                        'lat': self.observer_lat,
                        'lon': self.observer_lon,
                        'alt': self.observer_alt
                    },
                    'min_elevation': self.min_elevation
                },
                'satellites': {},
                'statistics': {
                    'total_satellites_processed': 0,
                    'visible_satellites': 0,
                    'calculation_errors': 0
                }
            }
            
            for sat_data in satellites:
                try:
                    # 創建 SGP4 衛星對象
                    satellite = Satrec.twoline2rv(sat_data['line1'], sat_data['line2'])
                    
                    # 儲存軌道位置
                    positions = []
                    visibility_windows = []
                    current_window = None
                    
                    for t_offset in time_points:
                        current_time = start_time + timedelta(seconds=t_offset)
                        
                        # 轉換為 Julian Day
                        jd, fr = jday(current_time.year, current_time.month, current_time.day,
                                     current_time.hour, current_time.minute, current_time.second)
                        
                        # SGP4 計算位置和速度
                        error, position, velocity = satellite.sgp4(jd, fr)
                        
                        if error == 0:  # 無錯誤
                            # 轉換為地理座標
                            x, y, z = position  # km
                            
                            # 計算相對於觀測點的位置
                            lat_rad = radians(self.observer_lat)
                            lon_rad = radians(self.observer_lon)
                            
                            # 地心距離
                            range_km = sqrt(x*x + y*y + z*z)
                            
                            # 簡化的仰角計算 (近似)
                            # 實際應用需要更精確的座標轉換
                            dx = x - 6371.0 * cos(lat_rad) * cos(lon_rad)  # 近似地球半徑
                            dy = y - 6371.0 * cos(lat_rad) * sin(lon_rad)
                            dz = z - 6371.0 * sin(lat_rad)
                            
                            ground_range = sqrt(dx*dx + dy*dy)
                            elevation_rad = atan2(dz, ground_range)
                            elevation_deg = degrees(elevation_rad)
                            
                            # 方位角計算 (簡化)
                            azimuth_rad = atan2(dy, dx)
                            azimuth_deg = degrees(azimuth_rad)
                            if azimuth_deg < 0:
                                azimuth_deg += 360
                            
                            position_data = {
                                'time': current_time.isoformat(),
                                'time_offset_seconds': t_offset,
                                'position_eci': {'x': x, 'y': y, 'z': z},  # ECI座標
                                'velocity_eci': {'x': velocity[0], 'y': velocity[1], 'z': velocity[2]},
                                'range_km': range_km,
                                'elevation_deg': elevation_deg,
                                'azimuth_deg': azimuth_deg,
                                'is_visible': elevation_deg >= self.min_elevation
                            }
                            
                            positions.append(position_data)
                            
                            # 追蹤可見性窗口
                            if elevation_deg >= self.min_elevation:
                                if current_window is None:
                                    current_window = {
                                        'start_time': current_time.isoformat(),
                                        'start_elevation': elevation_deg,
                                        'max_elevation': elevation_deg,
                                        'end_time': None,
                                        'duration_seconds': 0
                                    }
                                else:
                                    current_window['max_elevation'] = max(current_window['max_elevation'], elevation_deg)
                                    current_window['end_time'] = current_time.isoformat()
                                    current_window['duration_seconds'] = t_offset - time_points[0]
                            else:
                                if current_window is not None:
                                    visibility_windows.append(current_window)
                                    current_window = None
                    
                    # 結束最後一個窗口
                    if current_window is not None:
                        visibility_windows.append(current_window)
                    
                    # 統計資訊
                    visible_positions = [p for p in positions if p['is_visible']]
                    is_ever_visible = len(visible_positions) > 0
                    
                    if is_ever_visible:
                        orbit_data['statistics']['visible_satellites'] += 1
                    
                    # 儲存衛星軌道數據
                    orbit_data['satellites'][sat_data['norad_id']] = {
                        'name': sat_data['name'],
                        'norad_id': sat_data['norad_id'],
                        'tle_date': sat_data['tle_date'],
                        'positions': positions,
                        'visibility_windows': visibility_windows,
                        'statistics': {
                            'total_positions': len(positions),
                            'visible_positions': len(visible_positions),
                            'visibility_percentage': len(visible_positions) / len(positions) * 100 if positions else 0,
                            'max_elevation': max([p['elevation_deg'] for p in visible_positions]) if visible_positions else -90,
                            'is_ever_visible': is_ever_visible
                        }
                    }
                    
                    orbit_data['statistics']['total_satellites_processed'] += 1
                    
                    if orbit_data['statistics']['total_satellites_processed'] % 100 == 0:
                        logger.info(f"已處理 {orbit_data['statistics']['total_satellites_processed']} 顆衛星...")
                        
                except Exception as e:
                    logger.error(f"計算衛星 {sat_data['name']} 軌道失敗: {e}")
                    orbit_data['statistics']['calculation_errors'] += 1
                    continue
            
            logger.info(f"SGP4 軌道計算完成:")
            logger.info(f"  - 處理衛星: {orbit_data['statistics']['total_satellites_processed']}")
            logger.info(f"  - 可見衛星: {orbit_data['statistics']['visible_satellites']}")
            logger.info(f"  - 計算錯誤: {orbit_data['statistics']['calculation_errors']}")
            
            return orbit_data
            
        except ImportError as e:
            logger.error(f"SGP4 模組導入失敗: {e}")
            return {'error': 'SGP4 module not available'}
        except Exception as e:
            logger.error(f"SGP4 軌道計算失敗: {e}")
            return {'error': str(e)}
    
    def generate_precomputed_orbit_data(self, scan_result: Dict[str, Any]) -> Dict[str, Any]:
        """生成預計算的軌道數據"""
        logger.info("🚀 開始生成預計算軌道數據...")
        
        precomputed_data = {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'computation_type': 'sgp4_orbit_precomputation',
            'observer_location': {
                'lat': self.observer_lat,
                'lon': self.observer_lon,
                'alt': self.observer_alt,
                'name': 'NTPU'
            },
            'constellations': {},
            'aggregated_statistics': {
                'total_satellites': 0,
                'total_visible_satellites': 0,
                'total_visibility_windows': 0,
                'computation_errors': 0
            }
        }
        
        # 使用參考時間 (當前時間)
        reference_time = datetime.now(timezone.utc)
        
        for constellation, data in scan_result['constellations'].items():
            if data['files'] == 0:
                continue
                
            constellation_data = {
                'name': constellation,
                'orbit_data': {},
                'statistics': {
                    'satellites_processed': 0,
                    'visible_satellites': 0,
                    'avg_visibility_percentage': 0.0
                }
            }
            
            # 使用最新的日期數據
            latest_date = data['dates'][-1] if data['dates'] else None
            if latest_date:
                logger.info(f"處理 {constellation} 星座，日期: {latest_date}")
                
                # 載入衛星數據
                satellites = self.load_tle_satellites(constellation, latest_date)
                
                if satellites:
                    # 計算軌道位置
                    orbit_computation = self.compute_sgp4_orbit_positions(
                        satellites, reference_time, self.orbital_period_minutes)
                    
                    if 'error' not in orbit_computation:
                        constellation_data['orbit_data'] = orbit_computation
                        constellation_data['statistics']['satellites_processed'] = orbit_computation['statistics']['total_satellites_processed']
                        constellation_data['statistics']['visible_satellites'] = orbit_computation['statistics']['visible_satellites']
                        
                        # 計算平均可見性百分比
                        if orbit_computation['satellites']:
                            visibility_percentages = [
                                sat_data['statistics']['visibility_percentage'] 
                                for sat_data in orbit_computation['satellites'].values()
                            ]
                            constellation_data['statistics']['avg_visibility_percentage'] = (
                                sum(visibility_percentages) / len(visibility_percentages) if visibility_percentages else 0
                            )
                    else:
                        logger.error(f"軌道計算失敗: {orbit_computation['error']}")
                        constellation_data['computation_error'] = orbit_computation['error']
            
            precomputed_data['constellations'][constellation] = constellation_data
            
            # 更新總計統計
            precomputed_data['aggregated_statistics']['total_satellites'] += constellation_data['statistics']['satellites_processed']
            precomputed_data['aggregated_statistics']['total_visible_satellites'] += constellation_data['statistics']['visible_satellites']
        
        logger.info("✅ 預計算軌道數據生成完成")
        return precomputed_data
    
    def generate_build_time_config(self, scan_result: Dict[str, Any]) -> Dict[str, Any]:
        """生成建置時配置"""
        config = {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'build_environment': 'docker',
            'phase0_version': '1.0.1',  # 更新版本號
            'computation_type': 'sgp4_orbit_precomputation',  # 新增類型標識
            'data_source': 'local_manual_collection',
            'scan_result': scan_result,
            'runtime_settings': {
                'default_constellation': 'starlink',
                'data_validation_level': 'strict',
                'cache_enabled': True,
                'precomputed_data_available': True,
                'sgp4_orbit_data_enabled': True  # 新增 SGP4 標識
            }
        }
        
        # 根據可用數據調整設置
        if scan_result['total_constellations'] >= 2:
            config['runtime_settings']['multi_constellation_support'] = True
        
        if scan_result['overall_date_range']['start']:
            config['runtime_settings']['historical_data_range'] = scan_result['overall_date_range']
        
        return config
    
    def generate_rl_training_dataset(self, scan_result: Dict[str, Any]) -> Dict[str, Any]:
        """生成 RL 訓練數據集metadata"""
        rl_dataset = {
            'dataset_type': 'satellite_handover_rl_training',
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'computation_method': 'sgp4_orbit_precomputation',  # 新增計算方法
            'constellations': {},
            'training_parameters': {
                'observation_space_size': 0,
                'action_space_size': 0,
                'episode_length_minutes': 45,
                'reward_function': 'handover_efficiency',
                'orbit_computation_enabled': True  # 新增軌道計算標識
            }
        }
        
        total_episodes = 0
        
        for constellation, data in scan_result['constellations'].items():
            if data['files'] > 0:
                # 每天可以生成多個訓練episode
                episodes_per_day = 24  # 每小時一個episode
                constellation_episodes = data['files'] * episodes_per_day
                
                rl_dataset['constellations'][constellation] = {
                    'available_days': data['files'],
                    'satellite_count': data['satellites'],
                    'episodes_count': constellation_episodes,
                    'data_quality': data['data_quality'],
                    'orbit_precomputed': True  # 新增預計算標識
                }
                
                total_episodes += constellation_episodes
        
        rl_dataset['training_parameters']['total_episodes'] = total_episodes
        
        # 根據可用數據調整observation space
        if scan_result['total_satellites'] > 0:
            # 假設每次觀測最多追蹤10顆衛星
            max_tracked_satellites = min(10, scan_result['total_satellites'])
            features_per_satellite = 8  # lat, lon, elevation, azimuth, distance, signal_strength, velocity_x, velocity_y
            rl_dataset['training_parameters']['observation_space_size'] = max_tracked_satellites * features_per_satellite
            
            # 動作空間：選擇目標衛星 + 是否切換
            rl_dataset['training_parameters']['action_space_size'] = max_tracked_satellites + 1
        
        return rl_dataset
    
    def export_build_artifacts(self, scan_result: Dict[str, Any]) -> List[str]:
        """導出建置產物 - 包含真正的軌道數據"""
        artifacts = []
        
        try:
            # 1. 生成建置配置
            build_config = self.generate_build_time_config(scan_result)
            config_path = self.output_dir / "phase0_build_config.json"
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(build_config, f, indent=2, ensure_ascii=False)
            
            artifacts.append(str(config_path))
            logger.info(f"✅ 建置配置已生成: {config_path}")
            
            # 2. 生成預計算軌道數據 (新增!)
            precomputed_orbit_data = self.generate_precomputed_orbit_data(scan_result)
            orbit_path = self.output_dir / "phase0_precomputed_orbits.json"
            
            with open(orbit_path, 'w', encoding='utf-8') as f:
                json.dump(precomputed_orbit_data, f, indent=2, ensure_ascii=False)
            
            artifacts.append(str(orbit_path))
            logger.info(f"✅ 預計算軌道數據已生成: {orbit_path}")
            
            # 3. 生成 RL 訓練數據集metadata
            rl_dataset = self.generate_rl_training_dataset(scan_result)
            rl_path = self.output_dir / "phase0_rl_dataset_metadata.json"
            
            with open(rl_path, 'w', encoding='utf-8') as f:
                json.dump(rl_dataset, f, indent=2, ensure_ascii=False)
            
            artifacts.append(str(rl_path))
            logger.info(f"✅ RL 數據集metadata已生成: {rl_path}")
            
            # 4. 生成數據摘要報告
            summary_report = {
                'phase0_data_summary': {
                    'total_constellations': scan_result['total_constellations'],
                    'total_files': scan_result['total_files'],
                    'total_satellites': scan_result['total_satellites'],
                    'date_range': scan_result['overall_date_range'],
                    'constellation_details': scan_result['constellations']
                },
                'orbit_computation_summary': {
                    'total_visible_satellites': precomputed_orbit_data['aggregated_statistics']['total_visible_satellites'],
                    'computation_errors': precomputed_orbit_data['aggregated_statistics']['computation_errors'],
                    'observer_location': precomputed_orbit_data['observer_location'],
                    'computation_method': 'SGP4',
                    'orbital_period_minutes': self.orbital_period_minutes
                },
                'build_recommendations': []
            }
            
            # 添加建議
            if scan_result['total_constellations'] < 2:
                summary_report['build_recommendations'].append("Consider collecting data for both Starlink and OneWeb")
            
            if scan_result['total_files'] < 5:
                summary_report['build_recommendations'].append("More historical data days recommended for better RL training")
            
            for const, data in scan_result['constellations'].items():
                if data['data_quality'] in ['poor', 'missing']:
                    summary_report['build_recommendations'].append(f"Improve data quality for {const}")
            
            # 軌道計算相關建議
            visible_percentage = (precomputed_orbit_data['aggregated_statistics']['total_visible_satellites'] / 
                                precomputed_orbit_data['aggregated_statistics']['total_satellites'] * 100 
                                if precomputed_orbit_data['aggregated_statistics']['total_satellites'] > 0 else 0)
            
            if visible_percentage < 20:
                summary_report['build_recommendations'].append("Low satellite visibility - consider adjusting observer location or elevation threshold")
            
            summary_path = self.output_dir / "phase0_data_summary.json"
            
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary_report, f, indent=2, ensure_ascii=False)
            
            artifacts.append(str(summary_path))
            logger.info(f"✅ 數據摘要報告已生成: {summary_path}")
            
            # 5. 生成環境變數文件（供 Docker 使用）
            env_vars = {
                'PHASE0_DATA_AVAILABLE': 'true',
                'PHASE0_ORBIT_PRECOMPUTED': 'true',  # 新增軌道預計算標識
                'PHASE0_TOTAL_CONSTELLATIONS': str(scan_result['total_constellations']),
                'PHASE0_TOTAL_FILES': str(scan_result['total_files']),
                'PHASE0_TOTAL_SATELLITES': str(scan_result['total_satellites']),
                'PHASE0_VISIBLE_SATELLITES': str(precomputed_orbit_data['aggregated_statistics']['total_visible_satellites']),
                'PHASE0_DATE_START': scan_result['overall_date_range']['start'] or '',
                'PHASE0_DATE_END': scan_result['overall_date_range']['end'] or '',
                'PHASE0_OBSERVER_LAT': str(self.observer_lat),
                'PHASE0_OBSERVER_LON': str(self.observer_lon),
                'PHASE0_MIN_ELEVATION': str(self.min_elevation),
                'PHASE0_BUILD_TIMESTAMP': datetime.now(timezone.utc).isoformat()
            }
            
            env_path = self.output_dir / "phase0.env"
            
            with open(env_path, 'w') as f:
                for key, value in env_vars.items():
                    f.write(f"{key}={value}\n")
            
            artifacts.append(str(env_path))
            logger.info(f"✅ 環境變數文件已生成: {env_path}")
            
        except Exception as e:
            logger.error(f"導出建置產物失敗: {e}")
            raise
        
        return artifacts
    
    def run_build_preprocessing(self) -> Dict[str, Any]:
        """執行完整的建置預處理"""
        logger.info("🚀 開始 Phase 0 建置預處理 (SGP4 軌道預計算版)...")
        
        try:
            # 1. 掃描數據
            logger.info("📊 掃描可用數據...")
            scan_result = self.scan_available_data()
            
            logger.info("📋 掃描結果:")
            logger.info(f"  - 星座數: {scan_result['total_constellations']}")
            logger.info(f"  - 文件數: {scan_result['total_files']}")
            logger.info(f"  - 衛星數: {scan_result['total_satellites']}")
            logger.info(f"  - 日期範圍: {scan_result['overall_date_range']['start']} - {scan_result['overall_date_range']['end']}")
            
            # 2. 生成建置產物 (包含軌道預計算)
            logger.info("📦 生成建置產物 (包含 SGP4 軌道預計算)...")
            artifacts = self.export_build_artifacts(scan_result)
            
            # 3. 生成處理結果
            processing_result = {
                'success': True,
                'computation_method': 'sgp4_orbit_precomputation',
                'scan_result': scan_result,
                'artifacts': artifacts,
                'processing_time': datetime.now(timezone.utc).isoformat(),
                'recommendations': []
            }
            
            # 添加建議
            if scan_result['total_files'] == 0:
                processing_result['recommendations'].append("No TLE data files found - container will use fallback data")
            elif scan_result['total_files'] < 3:
                processing_result['recommendations'].append("Limited historical data - consider collecting more days")
            
            if scan_result['total_satellites'] == 0:
                processing_result['recommendations'].append("No satellites found - orbit computation skipped")
            
            logger.info("✅ Phase 0 建置預處理完成 (包含 SGP4 軌道預計算)")
            return processing_result
            
        except Exception as e:
            logger.error(f"建置預處理失敗: {e}")
            return {
                'success': False,
                'error': str(e),
                'processing_time': datetime.now(timezone.utc).isoformat()
            }

def main():
    """主程序"""
    print("🐳 Phase 0 Docker 建置預處理系統")
    print("=" * 50)
    
    # 從環境變數或命令行參數獲取配置
    tle_data_dir = os.environ.get('TLE_DATA_DIR', '/app/tle_data')
    output_dir = os.environ.get('OUTPUT_DIR', '/app/data')
    
    # 檢查命令行參數
    if len(sys.argv) > 1:
        if '--tle-data-dir' in sys.argv:
            idx = sys.argv.index('--tle-data-dir')
            if idx + 1 < len(sys.argv):
                tle_data_dir = sys.argv[idx + 1]
        
        if '--output-dir' in sys.argv:
            idx = sys.argv.index('--output-dir')
            if idx + 1 < len(sys.argv):
                output_dir = sys.argv[idx + 1]
    
    print(f"📂 TLE 數據目錄: {tle_data_dir}")
    print(f"📁 輸出目錄: {output_dir}")
    
    # 初始化預處理器
    preprocessor = Phase0DataPreprocessor(tle_data_dir, output_dir)
    
    # 執行預處理
    result = preprocessor.run_build_preprocessing()
    
    # 顯示結果
    if result['success']:
        print("\n🎉 建置預處理成功完成")
        print(f"📊 掃描到 {result['scan_result']['total_files']} 個數據文件")
        print(f"🛰️ 總計 {result['scan_result']['total_satellites']} 顆衛星")
        print(f"📦 生成 {len(result['artifacts'])} 個建置產物")
        
        if result['recommendations']:
            print("\n💡 建議:")
            for rec in result['recommendations']:
                print(f"  - {rec}")
    else:
        print(f"\n❌ 建置預處理失敗: {result['error']}")
        sys.exit(1)

if __name__ == "__main__":
    main()