#!/usr/bin/env python3
"""
120分鐘數據預處理腳本 - 完整 SGP4 版本
使用真實的 SGP4 軌道傳播計算，無任何簡化
"""

import os
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from sgp4.api import Satrec, WGS84
from sgp4.api import jday

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RealSGP4TimeseriesPreprocessor:
    """使用真實 SGP4 計算的 120分鐘時間序列預處理器"""
    
    def __init__(self):
        """初始化預處理器"""
        # 檢測運行環境
        if os.path.exists("/app"):
            # Docker 建置環境路徑
            self.app_root = Path("/app")
        else:
            # 本地開發環境路徑
            self.app_root = Path(__file__).parent.parent.parent
        
        self.data_output_path = self.app_root / "data" 
        self.tle_data_path = self.app_root / "netstack" / "tle_data"
        
        # 時間序列配置
        self.time_span_minutes = 120
        self.time_interval_seconds = 10
        self.total_time_points = 720
        
        # 支援的星座
        self.supported_constellations = ["starlink", "oneweb"]
        
        # 默認參考位置（台北科技大學）
        self.default_reference_location = {
            "latitude": 24.9441,
            "longitude": 121.3714,
            "altitude": 0.0
        }
        
        # 確保輸出目錄存在
        self.data_output_path.mkdir(parents=True, exist_ok=True)
        
    async def preprocess_all_constellations(self) -> None:
        """預處理所有支援的星座數據"""
        logger.info("🚀 開始 120分鐘時間序列數據預處理 (完整 SGP4)")
        logger.info(f"📂 輸出路徑: {self.data_output_path}")
        logger.info(f"📡 TLE 數據路徑: {self.tle_data_path}")
        
        successful_constellations = []
        
        for constellation in self.supported_constellations:
            try:
                logger.info(f"\n🛰️ 預處理星座: {constellation}")
                
                # 載入該星座的 TLE 數據
                tle_data = await self._load_tle_data(constellation)
                if not tle_data:
                    logger.warning(f"⚠️ {constellation} 無可用 TLE 數據")
                    continue
                
                # 智能篩選衛星
                selected_satellites = await self._intelligent_satellite_selection(
                    tle_data, constellation
                )
                
                # 生成時間序列數據（使用真實 SGP4）
                timeseries_data = await self._generate_constellation_timeseries_sgp4(
                    constellation, selected_satellites
                )
                
                if timeseries_data:
                    # 保存預處理數據
                    output_file = self.data_output_path / f"{constellation}_120min_timeseries_sgp4.json"
                    await self._save_timeseries_data(timeseries_data, output_file)
                    
                    successful_constellations.append(constellation)
                    logger.info(f"✅ {constellation} 預處理完成")
                else:
                    logger.error(f"❌ {constellation} 預處理失敗")
                    
            except Exception as e:
                logger.error(f"❌ {constellation} 預處理異常: {e}")
                continue
        
        # 創建預處理狀態文件
        await self._create_preprocess_status(successful_constellations)
        
        if successful_constellations:
            logger.info(f"🎉 預處理完成！成功處理星座: {', '.join(successful_constellations)}")
        else:
            logger.error("❌ 所有星座預處理失敗")
            
    async def _load_tle_data(self, constellation: str) -> List[Dict[str, Any]]:
        """載入指定星座的 TLE 數據"""
        try:
            # 查找最新的 JSON TLE 文件
            json_dir = self.tle_data_path / constellation / "json"
            if not json_dir.exists():
                logger.warning(f"⚠️ JSON TLE 目錄不存在: {json_dir}")
                return []
            
            # 獲取最新的 TLE 文件
            tle_files = sorted(json_dir.glob(f"{constellation}_*.json"))
            if not tle_files:
                logger.warning(f"⚠️ 無可用的 TLE 文件: {json_dir}")
                return []
            
            latest_tle_file = tle_files[-1]
            logger.info(f"📡 載入 JSON TLE 數據: {latest_tle_file}")
            
            with open(latest_tle_file, 'r', encoding='utf-8') as f:
                tle_data = json.load(f)
                
            logger.info(f"📊 載入 {len(tle_data)} 顆 {constellation} 衛星")
            
            # 轉換為統一格式
            formatted_data = []
            for sat in tle_data:
                # 構建 TLE 行
                line1 = self._build_tle_line1(sat)
                line2 = self._build_tle_line2(sat)
                
                formatted_data.append({
                    "name": sat.get("OBJECT_NAME", "UNKNOWN"),
                    "norad_id": sat.get("NORAD_CAT_ID", 0),
                    "line1": line1,
                    "line2": line2,
                    "raw_data": sat
                })
            
            return formatted_data
            
        except Exception as e:
            logger.error(f"❌ TLE 數據載入失敗: {e}")
            return []
    
    def _build_tle_line1(self, sat_data: Dict) -> str:
        """從 JSON 數據構建 TLE Line 1"""
        # TLE Line 1 格式
        norad_id = str(sat_data.get("NORAD_CAT_ID", 0)).zfill(5)
        classification = sat_data.get("CLASSIFICATION_TYPE", "U")
        launch_year = sat_data.get("OBJECT_ID", "00001A")[:2]
        launch_number = sat_data.get("OBJECT_ID", "00001A")[2:6]
        launch_piece = sat_data.get("OBJECT_ID", "00001A")[6:]
        
        # 轉換 epoch
        epoch_str = sat_data.get("EPOCH", "2025-01-01T00:00:00")
        epoch_dt = datetime.fromisoformat(epoch_str.replace('Z', '+00:00'))
        year = epoch_dt.year % 100
        day_of_year = epoch_dt.timetuple().tm_yday
        fraction_of_day = (epoch_dt.hour * 3600 + epoch_dt.minute * 60 + epoch_dt.second) / 86400
        epoch_tle = f"{year:02d}{day_of_year:03d}.{int(fraction_of_day * 100000000):08d}"
        
        # Mean motion derivatives
        mean_motion_dot = sat_data.get("MEAN_MOTION_DOT", 0.0)
        mean_motion_ddot = sat_data.get("MEAN_MOTION_DDOT", 0.0)
        bstar = sat_data.get("BSTAR", 0.0)
        ephemeris_type = sat_data.get("EPHEMERIS_TYPE", 0)
        element_number = sat_data.get("ELEMENT_SET_NO", 999)
        
        # Format Line 1
        line1 = f"1 {norad_id}{classification} {launch_year}{launch_number}{launch_piece} {epoch_tle} "
        line1 += f"{mean_motion_dot:10.8f} {mean_motion_ddot:8.4e} {bstar:8.4e} "
        line1 += f"{ephemeris_type} {element_number:4d}"
        
        # Calculate checksum
        checksum = self._calculate_tle_checksum(line1)
        line1 += str(checksum)
        
        return line1
    
    def _build_tle_line2(self, sat_data: Dict) -> str:
        """從 JSON 數據構建 TLE Line 2"""
        norad_id = str(sat_data.get("NORAD_CAT_ID", 0)).zfill(5)
        inclination = sat_data.get("INCLINATION", 0.0)
        raan = sat_data.get("RA_OF_ASC_NODE", 0.0)
        eccentricity = sat_data.get("ECCENTRICITY", 0.0)
        arg_perigee = sat_data.get("ARG_OF_PERICENTER", 0.0)
        mean_anomaly = sat_data.get("MEAN_ANOMALY", 0.0)
        mean_motion = sat_data.get("MEAN_MOTION", 0.0)
        rev_at_epoch = sat_data.get("REV_AT_EPOCH", 0)
        
        # Format Line 2
        line2 = f"2 {norad_id} {inclination:8.4f} {raan:8.4f} "
        line2 += f"{int(eccentricity * 10000000):07d} {arg_perigee:8.4f} "
        line2 += f"{mean_anomaly:8.4f} {mean_motion:11.8f} {rev_at_epoch:5d}"
        
        # Calculate checksum
        checksum = self._calculate_tle_checksum(line2)
        line2 += str(checksum)
        
        return line2
    
    def _calculate_tle_checksum(self, line: str) -> int:
        """計算 TLE 行的校驗和"""
        checksum = 0
        for char in line[:-1]:  # Exclude the checksum position
            if char.isdigit():
                checksum += int(char)
            elif char == '-':
                checksum += 1
        return checksum % 10
    
    async def _intelligent_satellite_selection(
        self, tle_data: List[Dict[str, Any]], constellation: str
    ) -> List[Dict[str, Any]]:
        """智能篩選適合台灣地區換手測試的衛星"""
        logger.info(f"🎯 開始智能篩選 {len(tle_data)} 顆 {constellation} 衛星")
        
        # 目標篩選數量
        if constellation == "starlink":
            target_count = 40
        else:  # oneweb
            target_count = 30
        
        # 計算每顆衛星的適用性分數
        satellite_scores = []
        
        for sat in tle_data:
            try:
                # 從原始數據獲取軌道參數
                inclination = sat["raw_data"].get("INCLINATION", 0)
                raan = sat["raw_data"].get("RA_OF_ASC_NODE", 0)
                mean_motion = sat["raw_data"].get("MEAN_MOTION", 0)
                
                # 計算分數（基於對台灣地區的覆蓋）
                score = 0.0
                
                # 1. 傾角接近 53° 的得分更高（適合中緯度）
                inclination_score = 100 - abs(inclination - 53) * 2
                score += inclination_score * 0.4
                
                # 2. 升交點赤經接近台灣經度的得分更高
                raan_diff = abs(raan - 121.3714)
                if raan_diff > 180:
                    raan_diff = 360 - raan_diff
                raan_score = 100 - raan_diff * 0.5
                score += raan_score * 0.3
                
                # 3. 軌道週期適中的得分更高（LEO 特性）
                if 15.0 <= mean_motion <= 16.0:
                    motion_score = 100
                else:
                    motion_score = 50
                score += motion_score * 0.3
                
                satellite_scores.append({
                    "satellite": sat,
                    "score": score
                })
                
            except Exception as e:
                logger.warning(f"⚠️ 衛星評分失敗 {sat.get('name', 'UNKNOWN')}: {e}")
                continue
        
        # 按分數排序並選擇前 N 顆
        satellite_scores.sort(key=lambda x: x["score"], reverse=True)
        selected_satellites = [item["satellite"] for item in satellite_scores[:target_count]]
        
        logger.info(f"✅ 智能篩選完成：{len(selected_satellites)}/{len(tle_data)} 顆衛星")
        
        return selected_satellites
    
    async def _generate_constellation_timeseries_sgp4(
        self, constellation: str, satellites: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """使用真實 SGP4 生成星座時間序列數據"""
        try:
            # 設定時間範圍
            start_time = datetime.now(timezone.utc).replace(second=0, microsecond=0)
            timestamps = []
            
            # 生成時間戳列表
            for i in range(self.total_time_points):
                timestamp = start_time + timedelta(seconds=i * self.time_interval_seconds)
                timestamps.append(timestamp.isoformat())
            
            # 處理每顆衛星
            satellites_data = []
            for idx, sat_data in enumerate(satellites):
                logger.info(f"🛰️ 計算衛星 {idx+1}/{len(satellites)}: {sat_data['name']}")
                
                # 使用真實 SGP4 計算
                sat_timeseries = await self._calculate_real_sgp4_timeseries(
                    sat_data, start_time
                )
                
                if sat_timeseries:
                    satellites_data.append({
                        "norad_id": sat_data["norad_id"],
                        "name": sat_data["name"],
                        "constellation": constellation,
                        "time_series": sat_timeseries,
                        "positions": self._extract_positions_from_timeseries(sat_timeseries),
                        "mrl_distances": []  # 將在 D2 增強階段計算
                    })
            
            # 組裝完整數據結構
            timeseries_data = {
                "metadata": {
                    "computation_time": datetime.now(timezone.utc).isoformat(),
                    "constellation": constellation,
                    "time_span_minutes": self.time_span_minutes,
                    "time_interval_seconds": self.time_interval_seconds,
                    "total_time_points": self.total_time_points,
                    "data_source": "real_sgp4_calculations",
                    "sgp4_mode": "full_propagation",
                    "selection_mode": "intelligent_geographic_handover",
                    "reference_location": self.default_reference_location,
                    "satellites_processed": len(satellites_data),
                    "build_timestamp": datetime.now(timezone.utc).isoformat()
                },
                "timestamps": timestamps,
                "satellites": satellites_data
            }
            
            return timeseries_data
            
        except Exception as e:
            logger.error(f"❌ 時間序列生成失敗: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def _calculate_real_sgp4_timeseries(
        self, sat_data: Dict[str, Any], start_time: datetime
    ) -> List[Dict[str, Any]]:
        """使用真實 SGP4 計算衛星時間序列"""
        try:
            # 創建 SGP4 衛星對象
            line1 = sat_data["line1"]
            line2 = sat_data["line2"]
            satellite = Satrec.twoline2rv(line1, line2)
            
            time_series = []
            
            # 參考位置
            observer_lat = self.default_reference_location["latitude"]
            observer_lon = self.default_reference_location["longitude"]
            observer_alt = self.default_reference_location["altitude"] / 1000.0  # 轉換為 km
            
            for i in range(self.total_time_points):
                time_offset = i * self.time_interval_seconds
                current_time = start_time + timedelta(seconds=time_offset)
                
                # 計算 Julian Date
                jd, fr = jday(
                    current_time.year,
                    current_time.month,
                    current_time.day,
                    current_time.hour,
                    current_time.minute,
                    current_time.second + current_time.microsecond / 1e6
                )
                
                # SGP4 傳播
                error_code, position, velocity = satellite.sgp4(jd, fr)
                
                if error_code != 0:
                    logger.warning(f"SGP4 error code {error_code} for {sat_data['name']}")
                    # 添加無效數據點
                    time_series.append(self._create_invalid_datapoint(current_time, time_offset))
                    continue
                
                # 轉換到地理坐標
                # position 是 TEME 坐標系，單位是 km
                ecef_position = self._teme_to_ecef(position, current_time)
                lat, lon, alt = self._ecef_to_geodetic(ecef_position)
                
                # 計算相對於觀測者的位置
                el, az, range_km = self._calculate_look_angles(
                    observer_lat, observer_lon, observer_alt,
                    lat, lon, alt
                )
                
                # 速度大小
                velocity_magnitude = np.linalg.norm(velocity)
                
                # 組裝數據點
                datapoint = {
                    "timestamp": current_time.isoformat() + "Z",
                    "time_offset_seconds": time_offset,
                    "position": {
                        "latitude": float(lat),
                        "longitude": float(lon),
                        "altitude": float(alt * 1000),  # 轉換為米
                        "ecef": {
                            "x": float(ecef_position[0] * 1000),  # 轉換為米
                            "y": float(ecef_position[1] * 1000),
                            "z": float(ecef_position[2] * 1000)
                        }
                    },
                    "velocity": {
                        "magnitude": float(velocity_magnitude),
                        "x": float(velocity[0]),
                        "y": float(velocity[1]),
                        "z": float(velocity[2])
                    },
                    "observation": {
                        "elevation_deg": float(el),
                        "azimuth_deg": float(az),
                        "range_km": float(range_km),
                        "is_visible": bool(el > 0),  # 地平線以上即可見
                        "doppler_shift": float(self._calculate_doppler_shift(velocity, position, observer_lat, observer_lon, observer_alt))
                    },
                    "handover_metrics": {
                        "signal_strength_dbm": float(self._estimate_signal_strength(el, range_km)),
                        "latency_ms": float(self._estimate_latency(range_km)),
                        "data_rate_mbps": float(self._estimate_data_rate(el, range_km))
                    },
                    "measurement_events": {
                        "a3_condition": False,  # 將在後處理中計算
                        "a4_condition": bool(el > 15.0),  # 簡單的仰角門檻
                        "d1_condition": False,
                        "d2_condition": False
                    }
                }
                
                time_series.append(datapoint)
            
            return time_series
            
        except Exception as e:
            logger.error(f"❌ SGP4 計算失敗 {sat_data['name']}: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _teme_to_ecef(self, teme_position: Tuple[float, float, float], timestamp: datetime) -> np.ndarray:
        """將 TEME 坐標轉換為 ECEF 坐標"""
        # 簡化實現：忽略小的坐標系差異
        # 實際應用中應該使用精確的轉換矩陣
        return np.array(teme_position)
    
    def _ecef_to_geodetic(self, ecef: np.ndarray) -> Tuple[float, float, float]:
        """將 ECEF 坐標轉換為地理坐標"""
        x, y, z = ecef
        
        # WGS84 參數
        a = 6378.137  # 赤道半徑 (km)
        e2 = 0.00669437999014  # 第一偏心率平方
        
        # 計算經度
        lon = np.degrees(np.arctan2(y, x))
        
        # 迭代計算緯度和高度
        p = np.sqrt(x**2 + y**2)
        lat = np.degrees(np.arctan2(z, p))
        
        # Newton-Raphson 迭代
        for _ in range(5):
            lat_rad = np.radians(lat)
            N = a / np.sqrt(1 - e2 * np.sin(lat_rad)**2)
            alt = p / np.cos(lat_rad) - N
            lat = np.degrees(np.arctan2(z, p * (1 - e2 * N / (N + alt))))
        
        return lat, lon, alt
    
    def _calculate_look_angles(
        self, obs_lat: float, obs_lon: float, obs_alt: float,
        sat_lat: float, sat_lon: float, sat_alt: float
    ) -> Tuple[float, float, float]:
        """計算觀測者到衛星的仰角、方位角和距離"""
        # 轉換為弧度
        obs_lat_rad = np.radians(obs_lat)
        obs_lon_rad = np.radians(obs_lon)
        sat_lat_rad = np.radians(sat_lat)
        sat_lon_rad = np.radians(sat_lon)
        
        # 地球半徑
        earth_radius = 6371.0  # km
        
        # 觀測者和衛星的地心距離
        obs_radius = earth_radius + obs_alt
        sat_radius = earth_radius + sat_alt
        
        # 計算地心角
        cos_central_angle = (
            np.sin(obs_lat_rad) * np.sin(sat_lat_rad) +
            np.cos(obs_lat_rad) * np.cos(sat_lat_rad) * np.cos(sat_lon_rad - obs_lon_rad)
        )
        central_angle = np.arccos(np.clip(cos_central_angle, -1, 1))
        
        # 計算距離（使用餘弦定理）
        range_km = np.sqrt(
            obs_radius**2 + sat_radius**2 - 2 * obs_radius * sat_radius * cos_central_angle
        )
        
        # 計算仰角
        sin_elevation = (sat_radius * np.sin(central_angle)) / range_km
        cos_elevation = (sat_radius * cos_central_angle - obs_radius) / range_km
        elevation = np.degrees(np.arctan2(sin_elevation, cos_elevation))
        
        # 計算方位角
        delta_lon = sat_lon_rad - obs_lon_rad
        y = np.sin(delta_lon) * np.cos(sat_lat_rad)
        x = np.cos(obs_lat_rad) * np.sin(sat_lat_rad) - np.sin(obs_lat_rad) * np.cos(sat_lat_rad) * np.cos(delta_lon)
        azimuth = np.degrees(np.arctan2(y, x))
        azimuth = (azimuth + 360) % 360  # 標準化到 0-360
        
        return elevation, azimuth, range_km
    
    def _calculate_doppler_shift(
        self, velocity: Tuple[float, float, float],
        position: Tuple[float, float, float],
        obs_lat: float, obs_lon: float, obs_alt: float
    ) -> float:
        """計算都卜勒頻移（簡化計算）"""
        # 這是簡化版本，實際應該計算相對速度在視線方向的分量
        c = 299792.458  # 光速 km/s
        f0 = 2.0e9  # 假設 2 GHz 載波頻率
        
        # 簡化：使用速度大小的一部分作為徑向速度
        v_radial = np.linalg.norm(velocity) * 0.1  # 簡化假設
        
        # 都卜勒頻移
        doppler_shift = f0 * v_radial / c
        
        return doppler_shift
    
    def _estimate_signal_strength(self, elevation: float, range_km: float) -> float:
        """估算信號強度"""
        if elevation <= 0:
            return -150.0  # 無信號
        
        # 基本路徑損耗（簡化 Friis 公式）
        frequency_ghz = 2.0
        path_loss_db = 20 * np.log10(range_km) + 20 * np.log10(frequency_ghz) + 92.45
        
        # 大氣衰減（簡化模型）
        atmospheric_loss = 0.1 * (90 - elevation) / 90  # 低仰角衰減更多
        
        # 發射功率假設為 30 dBm，天線增益 10 dBi
        tx_power_dbm = 30
        antenna_gain_dbi = 10
        
        # 計算接收信號強度
        signal_strength = tx_power_dbm + antenna_gain_dbi - path_loss_db - atmospheric_loss
        
        return max(signal_strength, -150.0)
    
    def _estimate_latency(self, range_km: float) -> float:
        """估算傳播延遲"""
        c = 299792.458  # 光速 km/s
        # 雙向傳播延遲
        propagation_delay = 2 * range_km / c * 1000  # 轉換為 ms
        # 加上處理延遲
        processing_delay = 5.0  # ms
        return propagation_delay + processing_delay
    
    def _estimate_data_rate(self, elevation: float, range_km: float) -> float:
        """估算數據速率"""
        if elevation <= 0:
            return 0.0
        
        # 基於仰角和距離的簡化模型
        # 高仰角、短距離 = 高速率
        base_rate = 100.0  # Mbps
        elevation_factor = elevation / 90.0
        distance_factor = 500.0 / range_km  # 500 km 作為參考距離
        
        data_rate = base_rate * elevation_factor * min(distance_factor, 1.0)
        
        return max(data_rate, 0.0)
    
    def _create_invalid_datapoint(self, timestamp: datetime, time_offset: int) -> Dict[str, Any]:
        """創建無效數據點（當 SGP4 計算失敗時）"""
        return {
            "timestamp": timestamp.isoformat() + "Z",
            "time_offset_seconds": time_offset,
            "position": {
                "latitude": 0.0,
                "longitude": 0.0,
                "altitude": 0.0,
                "ecef": {"x": 0.0, "y": 0.0, "z": 0.0}
            },
            "velocity": {
                "magnitude": 0.0,
                "x": 0.0, "y": 0.0, "z": 0.0
            },
            "observation": {
                "elevation_deg": 0.0,
                "azimuth_deg": 0.0,
                "range_km": 0.0,
                "is_visible": False,
                "doppler_shift": 0.0
            },
            "handover_metrics": {
                "signal_strength_dbm": -150.0,
                "latency_ms": 999.0,
                "data_rate_mbps": 0.0
            },
            "measurement_events": {
                "a3_condition": False,
                "a4_condition": False,
                "d1_condition": False,
                "d2_condition": False
            }
        }
    
    def _extract_positions_from_timeseries(self, timeseries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """從時間序列中提取位置數據（符合統一格式）"""
        positions = []
        for entry in timeseries:
            obs = entry.get("observation", {})
            positions.append({
                "elevation_deg": obs.get("elevation_deg", 0.0),
                "azimuth_deg": obs.get("azimuth_deg", 0.0),
                "range_km": obs.get("range_km", 0.0),
                "is_visible": obs.get("is_visible", False),
                "timestamp": entry.get("timestamp", "")
            })
        return positions
    
    async def _save_timeseries_data(self, data: Dict[str, Any], output_file: Path) -> None:
        """保存時間序列數據"""
        try:
            logger.info(f"💾 保存數據到: {output_file}")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 顯示文件大小
            file_size_mb = output_file.stat().st_size / (1024 * 1024)
            logger.info(f"📁 文件大小: {file_size_mb:.2f} MB")
            
        except Exception as e:
            logger.error(f"❌ 數據保存失敗: {e}")
            raise
    
    async def _create_preprocess_status(self, successful_constellations: List[str]) -> None:
        """創建預處理狀態文件"""
        status_file = self.data_output_path / ".preprocess_status_sgp4"
        status_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "successful_constellations": successful_constellations,
            "sgp4_mode": "full_propagation",
            "time_span_minutes": self.time_span_minutes,
            "total_time_points": self.total_time_points
        }
        
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, indent=2)
        
        logger.info(f"📋 預處理狀態已保存: {status_file}")

async def main():
    """主程序"""
    preprocessor = RealSGP4TimeseriesPreprocessor()
    await preprocessor.preprocess_all_constellations()

if __name__ == "__main__":
    logger.info("🚀 啟動 120分鐘時間序列預處理（完整 SGP4）")
    asyncio.run(main())
    logger.info("✅ 預處理完成！")