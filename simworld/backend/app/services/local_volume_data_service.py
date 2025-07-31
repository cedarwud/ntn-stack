"""
本地 Docker Volume 數據服務
按照衛星數據架構文檔，SimWorld 應該使用 Docker Volume 本地數據而非直接 API 調用
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class LocalVolumeDataService:
    """本地 Docker Volume 數據服務 - 遵循衛星數據架構"""
    
    def __init__(self):
        """初始化本地數據服務"""
        # Docker Volume 掛載路徑
        self.netstack_data_path = Path("/app/data")  # 主要預計算數據
        self.netstack_tle_data_path = Path("/app/netstack/tle_data")  # TLE 原始數據
        
        # 統一時間序列配置
        self.time_span_minutes = 120
        self.time_interval_seconds = 10
        self.total_time_points = 720
        
        # 檢查路徑是否存在
        self._check_volume_paths()
    
    def _check_volume_paths(self):
        """檢查 Docker Volume 路徑是否正確掛載"""
        paths = [
            (self.netstack_data_path, "預計算軌道數據"),
            (self.netstack_tle_data_path, "TLE 原始數據")
        ]
        
        for path, description in paths:
            if path.exists():
                logger.info(f"✅ {description} 路徑可用: {path}")
            else:
                logger.warning(f"⚠️  {description} 路徑不存在: {path}")
    
    async def get_precomputed_orbit_data(
        self,
        location: str = "ntpu",
        constellation: str = "starlink"
    ) -> Optional[Dict[str, Any]]:
        """
        從本地 Docker Volume 獲取預計算軌道數據
        優先級: phase0 數據 > layered 數據 > 無數據
        """
        try:
            # 主要預計算數據文件
            main_data_file = self.netstack_data_path / "phase0_precomputed_orbits.json"
            
            if main_data_file.exists():
                logger.info(f"📊 從本地 Volume 載入預計算軌道數據: {main_data_file}")
                
                with open(main_data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 檢查數據完整性
                if self._validate_precomputed_data(data):
                    logger.info(f"✅ 成功載入 {len(data.get('orbit_points', []))} 個軌道點")
                    return data
                else:
                    logger.warning("⚠️  預計算數據格式驗證失敗")
            else:
                logger.warning(f"📊 主要預計算數據文件不存在: {main_data_file}")
            
            # 嘗試分層數據作為備用
            layered_data_dir = self.netstack_data_path / "layered_phase0"
            if layered_data_dir.exists():
                return await self._load_layered_data(layered_data_dir, location, constellation)
            
            logger.error("❌ 無可用的本地預計算數據")
            return None
            
        except Exception as e:
            logger.error(f"❌ 載入本地預計算數據失敗: {e}")
            return None
    
    async def _load_layered_data(
        self,
        layered_dir: Path,
        location: str,
        constellation: str
    ) -> Optional[Dict[str, Any]]:
        """載入分層門檻數據"""
        try:
            # 尋找對應的分層數據文件
            pattern = f"{location}_{constellation}_*.json"
            data_files = list(layered_dir.glob(pattern))
            
            if data_files:
                # 選擇最新的文件
                latest_file = max(data_files, key=lambda p: p.stat().st_mtime)
                logger.info(f"📊 從分層數據載入: {latest_file}")
                
                with open(latest_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if self._validate_precomputed_data(data):
                    return data
            
            logger.warning(f"⚠️  未找到 {location}_{constellation} 的分層數據")
            return None
            
        except Exception as e:
            logger.error(f"❌ 載入分層數據失敗: {e}")
            return None
    
    def _validate_precomputed_data(self, data: Dict[str, Any]) -> bool:
        """驗證預計算數據格式"""
        try:
            required_fields = ["orbit_points", "metadata"]
            for field in required_fields:
                if field not in data:
                    logger.warning(f"缺少必要字段: {field}")
                    return False
            
            orbit_points = data.get("orbit_points", [])
            if not orbit_points:
                logger.warning("orbit_points 為空")
                return False
            
            # 檢查第一個軌道點的格式
            first_point = orbit_points[0]
            point_fields = ["timestamp", "latitude", "longitude", "altitude_km"]
            for field in point_fields:
                if field not in first_point:
                    logger.warning(f"軌道點缺少字段: {field}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"數據驗證失敗: {e}")
            return False
    
    async def get_local_tle_data(self, constellation: str = "starlink") -> List[Dict[str, Any]]:
        """
        從本地 Docker Volume 獲取 TLE 數據
        替代直接 API 調用
        """
        try:
            # 尋找對應星座的最新 TLE 數據
            constellation_dir = self.netstack_tle_data_path / constellation
            
            if not constellation_dir.exists():
                logger.warning(f"星座目錄不存在: {constellation_dir}")
                return []
            
            # 檢查 JSON 格式數據
            json_dir = constellation_dir / "json"
            if json_dir.exists():
                json_files = sorted(json_dir.glob(f"{constellation}_*.json"), reverse=True)
                if json_files:
                    latest_file = json_files[0]
                    logger.info(f"📡 從本地 Volume 載入 TLE 數據: {latest_file}")
                    
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        tle_data = json.load(f)
                    
                    logger.info(f"✅ 成功載入 {len(tle_data)} 顆 {constellation} 衛星數據")
                    return tle_data
            
            # 檢查 TLE 格式數據
            tle_dir = constellation_dir / "tle"
            if tle_dir.exists():
                tle_files = sorted(tle_dir.glob(f"{constellation}_*.tle"), reverse=True)
                if tle_files:
                    latest_file = tle_files[0]
                    logger.info(f"📡 從本地 Volume 解析 TLE 文件: {latest_file}")
                    
                    tle_data = await self._parse_tle_file(latest_file, constellation)
                    logger.info(f"✅ 解析得到 {len(tle_data)} 顆 {constellation} 衛星數據")
                    return tle_data
            
            logger.warning(f"❌ 未找到 {constellation} 的本地 TLE 數據")
            return []
            
        except Exception as e:
            logger.error(f"❌ 載入本地 TLE 數據失敗: {e}")
            return []
    
    async def _parse_tle_file(self, tle_file: Path, constellation: str) -> List[Dict[str, Any]]:
        """解析 TLE 文件格式數據"""
        try:
            tle_data = []
            
            with open(tle_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 按照 TLE 格式解析 (3行一組)
            for i in range(0, len(lines), 3):
                if i + 2 < len(lines):
                    name = lines[i].strip()
                    line1 = lines[i + 1].strip()
                    line2 = lines[i + 2].strip()
                    
                    if line1.startswith("1 ") and line2.startswith("2 "):
                        try:
                            norad_id = int(line1[2:7])
                            satellite_data = {
                                "name": name,
                                "norad_id": norad_id,
                                "line1": line1,
                                "line2": line2,
                                "constellation": constellation,
                                "source": "local_volume_tle_file",
                                "file_path": str(tle_file)
                            }
                            tle_data.append(satellite_data)
                        except (ValueError, IndexError) as e:
                            logger.warning(f"解析 TLE 行失敗: {e}")
                            continue
            
            return tle_data
            
        except Exception as e:
            logger.error(f"解析 TLE 文件失敗: {e}")
            return []
    
    async def check_data_freshness(self) -> Dict[str, Any]:
        """檢查本地數據的新鮮度"""
        try:
            freshness_info = {
                "precomputed_data": None,
                "tle_data": {},
                "data_ready": False
            }
            
            # 檢查數據完成標記
            data_ready_file = self.netstack_data_path / ".data_ready"
            if data_ready_file.exists():
                freshness_info["data_ready"] = True
                
                # 讀取數據生成時間
                try:
                    with open(data_ready_file, 'r') as f:
                        ready_info = f.read().strip()
                    freshness_info["data_ready_info"] = ready_info
                except:
                    pass
            
            # 檢查主要預計算數據
            main_data_file = self.netstack_data_path / "phase0_precomputed_orbits.json"
            if main_data_file.exists():
                stat = main_data_file.stat()
                freshness_info["precomputed_data"] = {
                    "file": str(main_data_file),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "age_hours": (datetime.now().timestamp() - stat.st_mtime) / 3600
                }
            
            # 檢查 TLE 數據
            for constellation in ["starlink", "oneweb"]:
                constellation_dir = self.netstack_tle_data_path / constellation
                if constellation_dir.exists():
                    freshness_info["tle_data"][constellation] = {
                        "directory": str(constellation_dir),
                        "json_files": len(list((constellation_dir / "json").glob("*.json"))) if (constellation_dir / "json").exists() else 0,
                        "tle_files": len(list((constellation_dir / "tle").glob("*.tle"))) if (constellation_dir / "tle").exists() else 0
                    }
            
            return freshness_info
            
        except Exception as e:
            logger.error(f"檢查數據新鮮度失敗: {e}")
            return {"error": str(e)}
    
    def is_data_available(self) -> bool:
        """檢查是否有可用的本地數據"""
        try:
            # 檢查主要數據文件
            main_data_file = self.netstack_data_path / "phase0_precomputed_orbits.json"
            if main_data_file.exists() and main_data_file.stat().st_size > 0:
                return True
            
            # 檢查分層數據
            layered_data_dir = self.netstack_data_path / "layered_phase0"
            if layered_data_dir.exists():
                json_files = list(layered_data_dir.glob("*.json"))
                if json_files:
                    return True
            
            # 檢查 TLE 數據
            for constellation in ["starlink", "oneweb"]:
                constellation_dir = self.netstack_tle_data_path / constellation
                if constellation_dir.exists():
                    if (constellation_dir / "json").exists() or (constellation_dir / "tle").exists():
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"檢查數據可用性失敗: {e}")
            return False

    async def generate_120min_timeseries(
        self,
        constellation: str = "starlink",
        reference_location: Optional[Dict[str, float]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        生成 120 分鐘統一時間序列數據
        直接從 Docker Volume 處理，無需 NetStack API
        """
        try:
            if reference_location is None:
                reference_location = {
                    "latitude": 24.9441,   # 台北科技大學
                    "longitude": 121.3714,
                    "altitude": 0.0
                }
            
            # 載入本地 TLE 數據
            tle_data = await self.get_local_tle_data(constellation)
            if not tle_data:
                logger.error(f"❌ 無可用的 {constellation} TLE 數據")
                return None
            
            logger.info(f"🛰️ 開始生成 {constellation} 120分鐘時間序列數據")
            logger.info(f"📍 參考位置: {reference_location['latitude']:.4f}°N, {reference_location['longitude']:.4f}°E")
            
            # 當前時間作為起始點
            from datetime import datetime, timezone, timedelta
            start_time = datetime.now(timezone.utc)
            
            satellites_timeseries = []
            
            # 只處理前10顆衛星以提高性能 (可根據需要調整)
            selected_satellites = tle_data[:10]
            logger.info(f"📊 處理 {len(selected_satellites)} 顆衛星的軌道數據")
            
            for i, sat_data in enumerate(selected_satellites):
                logger.info(f"🔄 處理衛星 {i+1}/{len(selected_satellites)}: {sat_data.get('name', 'Unknown')}")
                
                satellite_timeseries = await self._calculate_satellite_120min_timeseries(
                    sat_data, start_time, reference_location
                )
                
                if satellite_timeseries:
                    satellites_timeseries.append({
                        "norad_id": sat_data.get("norad_id", 0),
                        "name": sat_data.get("name", "Unknown"),
                        "constellation": constellation,
                        "time_series": satellite_timeseries
                    })
            
            # 生成 UE 軌跡 (靜態 UE)
            ue_trajectory = []
            for i in range(self.total_time_points):
                current_time = start_time + timedelta(seconds=i * self.time_interval_seconds)
                ue_trajectory.append({
                    "time_offset_seconds": i * self.time_interval_seconds,
                    "position": reference_location.copy(),
                    "serving_satellite": satellites_timeseries[0]["name"] if satellites_timeseries else "None",
                    "handover_state": "stable"
                })
            
            # 構建統一時間序列數據
            unified_data = {
                "metadata": {
                    "computation_time": start_time.isoformat(),
                    "constellation": constellation,
                    "time_span_minutes": self.time_span_minutes,
                    "time_interval_seconds": self.time_interval_seconds,
                    "total_time_points": self.total_time_points,
                    "data_source": "local_docker_volume_direct",
                    "network_dependency": False,
                    "reference_location": reference_location,
                    "satellites_processed": len(satellites_timeseries)
                },
                "satellites": satellites_timeseries,
                "ue_trajectory": ue_trajectory,
                "handover_events": []  # 暫時為空，後續可擴展
            }
            
            logger.info(f"✅ 成功生成 120分鐘時間序列數據: {len(satellites_timeseries)} 顆衛星, {self.total_time_points} 時間點")
            return unified_data
            
        except Exception as e:
            logger.error(f"❌ 生成 120分鐘時間序列數據失敗: {e}")
            return None
    
    async def _calculate_satellite_120min_timeseries(
        self,
        sat_data: Dict[str, Any],
        start_time: datetime,
        reference_location: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """計算單顆衛星的 120 分鐘時間序列"""
        try:
            from datetime import timedelta
            import math
            
            time_series = []
            current_time = start_time
            
            # 提取 TLE 數據
            line1 = sat_data.get("line1", "")
            line2 = sat_data.get("line2", "")
            
            # 簡化的軌道計算 (基於圓軌道近似)
            # 在實際實施中，應使用 SGP4 進行精確計算
            try:
                # 從 TLE line2 提取平均運動 (每日繞行次數)
                mean_motion = float(line2[52:63]) if len(line2) > 63 else 15.5
                orbital_period_minutes = 1440 / mean_motion  # 軌道週期(分鐘)
                
                # 軌道傾角
                inclination = float(line2[8:16]) if len(line2) > 16 else 53.0
                
                # 軌道高度估算 (基於平均運動)
                altitude_km = 550.0  # Starlink 典型高度
                
            except (ValueError, IndexError):
                # Fallback 值
                mean_motion = 15.5
                orbital_period_minutes = 96.0
                inclination = 53.0
                altitude_km = 550.0
            
            for i in range(self.total_time_points):
                # 時間進度
                time_offset = i * self.time_interval_seconds
                progress = (time_offset / 60) / orbital_period_minutes  # 軌道進度比例
                
                # 簡化的位置計算 (圓軌道近似)
                orbital_angle = (progress * 360) % 360  # 軌道角度
                
                # 緯度變化 (基於軌道傾角)
                latitude = inclination * math.sin(math.radians(orbital_angle))
                longitude = (orbital_angle - 180) % 360 - 180  # -180 到 180
                
                # 計算與參考位置的距離和角度
                lat_diff = latitude - reference_location["latitude"]
                lon_diff = longitude - reference_location["longitude"]
                
                # 地面距離估算 (球面距離公式簡化版)
                ground_distance_km = math.sqrt(lat_diff**2 + lon_diff**2) * 111.32  # 1度≈111.32km
                
                # 3D 距離 (包含高度)
                satellite_distance_km = math.sqrt(ground_distance_km**2 + altitude_km**2)
                
                # 仰角計算
                elevation_deg = max(0, 90 - math.degrees(math.atan2(ground_distance_km, altitude_km)))
                
                # 方位角簡化計算
                azimuth_deg = (math.degrees(math.atan2(lon_diff, lat_diff)) + 360) % 360
                
                # 可見性判斷 (仰角 > 10度)
                is_visible = elevation_deg > 10.0
                
                # RSRP 估算 (基於距離的簡化模型)
                rsrp_dbm = -70 - 20 * math.log10(satellite_distance_km / 500) if satellite_distance_km > 0 else -70
                rsrp_dbm = max(-120, min(-50, rsrp_dbm))  # 限制在合理範圍
                
                time_point = {
                    "time_offset_seconds": time_offset,
                    "timestamp": (current_time + timedelta(seconds=time_offset)).isoformat(),
                    "position": {
                        "latitude": latitude,
                        "longitude": longitude,
                        "altitude": altitude_km * 1000,  # 轉換為米
                        "velocity": {"x": 7.8, "y": 0.0, "z": 0.0}  # 簡化速度
                    },
                    "observation": {
                        "elevation_deg": elevation_deg,
                        "azimuth_deg": azimuth_deg,
                        "range_km": satellite_distance_km,
                        "is_visible": is_visible,
                        "rsrp_dbm": rsrp_dbm,
                        "rsrq_db": -12.0,  # 固定值
                        "sinr_db": 18.0    # 固定值
                    },
                    "handover_metrics": {
                        "signal_strength": max(0, (rsrp_dbm + 120) / 70),  # 歸一化
                        "handover_score": 0.8 if is_visible else 0.1,
                        "is_handover_candidate": is_visible and elevation_deg > 15,
                        "predicted_service_time_seconds": 300 if is_visible else 0
                    },
                    "measurement_events": {
                        "d1_distance_m": ground_distance_km * 1000,
                        "d2_satellite_distance_m": satellite_distance_km * 1000,
                        "d2_ground_distance_m": ground_distance_km * 1000,
                        "a4_trigger_condition": rsrp_dbm > -90,
                        "t1_time_condition": True
                    }
                }
                
                time_series.append(time_point)
            
            return time_series
            
        except Exception as e:
            logger.error(f"❌ 計算衛星時間序列失敗: {e}")
            return []


# 全局實例
_local_volume_service = None


def get_local_volume_service() -> LocalVolumeDataService:
    """獲取本地 Volume 數據服務實例"""
    global _local_volume_service
    if _local_volume_service is None:
        _local_volume_service = LocalVolumeDataService()
    return _local_volume_service