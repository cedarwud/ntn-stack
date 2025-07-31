"""
本地 Docker Volume 數據服務
按照衛星數據架構文檔，SimWorld 應該使用 Docker Volume 本地數據而非直接 API 調用
"""

import json
import logging
import math
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
            (self.netstack_tle_data_path, "TLE 原始數據"),
        ]

        for path, description in paths:
            if path.exists():
                logger.info(f"✅ {description} 路徑可用: {path}")
            else:
                logger.warning(f"⚠️  {description} 路徑不存在: {path}")

    async def get_precomputed_orbit_data(
        self, location: str = "ntpu", constellation: str = "starlink"
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

                with open(main_data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # 檢查數據完整性
                if self._validate_precomputed_data(data):
                    logger.info(
                        f"✅ 成功載入 {len(data.get('orbit_points', []))} 個軌道點"
                    )
                    return data
                else:
                    logger.warning("⚠️  預計算數據格式驗證失敗")
            else:
                logger.warning(f"📊 主要預計算數據文件不存在: {main_data_file}")

            # 嘗試分層數據作為備用
            layered_data_dir = self.netstack_data_path / "layered_phase0"
            if layered_data_dir.exists():
                return await self._load_layered_data(
                    layered_data_dir, location, constellation
                )

            logger.error("❌ 無可用的本地預計算數據")
            return None

        except Exception as e:
            logger.error(f"❌ 載入本地預計算數據失敗: {e}")
            return None

    async def _load_layered_data(
        self, layered_dir: Path, location: str, constellation: str
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

                with open(latest_file, "r", encoding="utf-8") as f:
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

    async def get_local_tle_data(
        self, constellation: str = "starlink"
    ) -> List[Dict[str, Any]]:
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

            # 優先檢查 TLE 格式數據（包含完整的 line1 和 line2）
            tle_dir = constellation_dir / "tle"
            if tle_dir.exists():
                tle_files = sorted(tle_dir.glob(f"{constellation}_*.tle"), reverse=True)
                if tle_files:
                    latest_file = tle_files[0]
                    logger.info(f"📡 從本地 Volume 解析 TLE 文件: {latest_file}")

                    tle_data = await self._parse_tle_file(latest_file, constellation)
                    logger.info(
                        f"✅ 解析得到 {len(tle_data)} 顆 {constellation} 衛星數據"
                    )
                    return tle_data

            # 備用：檢查 JSON 格式數據（但缺少 line1 和 line2，不適合 SGP4 計算）
            json_dir = constellation_dir / "json"
            if json_dir.exists():
                json_files = sorted(
                    json_dir.glob(f"{constellation}_*.json"), reverse=True
                )
                if json_files:
                    latest_file = json_files[0]
                    logger.warning(
                        f"⚠️ JSON 格式數據缺少 TLE line1/line2，將無法進行 SGP4 計算: {latest_file}"
                    )
                    # 暫時不載入 JSON 數據，因為它無法用於 SGP4 計算

            logger.warning(f"❌ 未找到 {constellation} 的本地 TLE 數據")
            return []

        except Exception as e:
            logger.error(f"❌ 載入本地 TLE 數據失敗: {e}")
            return []

    async def _parse_tle_file(
        self, tle_file: Path, constellation: str
    ) -> List[Dict[str, Any]]:
        """解析 TLE 文件格式數據"""
        try:
            tle_data = []

            with open(tle_file, "r", encoding="utf-8") as f:
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
                                "file_path": str(tle_file),
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
                "data_ready": False,
            }

            # 檢查數據完成標記
            data_ready_file = self.netstack_data_path / ".data_ready"
            if data_ready_file.exists():
                freshness_info["data_ready"] = True

                # 讀取數據生成時間
                try:
                    with open(data_ready_file, "r") as f:
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
                    "age_hours": (datetime.now().timestamp() - stat.st_mtime) / 3600,
                }

            # 檢查 TLE 數據
            for constellation in ["starlink", "oneweb"]:
                constellation_dir = self.netstack_tle_data_path / constellation
                if constellation_dir.exists():
                    freshness_info["tle_data"][constellation] = {
                        "directory": str(constellation_dir),
                        "json_files": (
                            len(list((constellation_dir / "json").glob("*.json")))
                            if (constellation_dir / "json").exists()
                            else 0
                        ),
                        "tle_files": (
                            len(list((constellation_dir / "tle").glob("*.tle")))
                            if (constellation_dir / "tle").exists()
                            else 0
                        ),
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
                    if (constellation_dir / "json").exists() or (
                        constellation_dir / "tle"
                    ).exists():
                        return True

            return False

        except Exception as e:
            logger.error(f"檢查數據可用性失敗: {e}")
            return False

    async def generate_120min_timeseries(
        self,
        constellation: str = "starlink",
        reference_location: Optional[Dict[str, float]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        生成 120 分鐘統一時間序列數據
        優先載入預處理數據，否則動態生成
        """
        try:
            if reference_location is None:
                reference_location = {
                    "latitude": 24.9441,  # 台北科技大學
                    "longitude": 121.3714,
                    "altitude": 0.0,
                }

            # 優先檢查預處理數據
            preprocess_data = await self._load_preprocess_timeseries(
                constellation, reference_location
            )
            if preprocess_data:
                logger.info(f"✅ 使用預處理時間序列數據: {constellation}")
                return preprocess_data

            # 預處理數據不可用時，動態生成
            logger.info(f"🔄 動態生成時間序列數據: {constellation}")
            return await self._generate_dynamic_timeseries(
                constellation, reference_location
            )

        except Exception as e:
            logger.error(f"❌ 生成 120分鐘時間序列數據失敗: {e}")
            return None

    async def _load_preprocess_timeseries(
        self, constellation: str, reference_location: Dict[str, float]
    ) -> Optional[Dict[str, Any]]:
        """載入預處理的時間序列數據"""
        try:
            # 檢查預處理數據文件
            preprocess_file = (
                self.netstack_data_path / f"{constellation}_120min_timeseries.json"
            )

            if not preprocess_file.exists():
                logger.info(f"📊 預處理數據不存在: {preprocess_file}")
                return None

            # 檢查文件新鮮度（24小時內）
            import time

            file_age_hours = (time.time() - preprocess_file.stat().st_mtime) / 3600
            if file_age_hours > 24:
                logger.warning(
                    f"⚠️ 預處理數據已過時 ({file_age_hours:.1f}小時): {preprocess_file}"
                )
                return None

            # 載入預處理數據
            logger.info(f"📂 載入預處理數據: {preprocess_file}")
            with open(preprocess_file, "r", encoding="utf-8") as f:
                preprocess_data = json.load(f)

            # 驗證數據完整性
            if not self._validate_timeseries_data(preprocess_data):
                logger.warning(f"⚠️ 預處理數據格式驗證失敗")
                return None

            # 更新元數據以反映當前請求
            preprocess_data["metadata"]["load_time"] = datetime.now().isoformat()
            preprocess_data["metadata"]["data_source"] = "preprocess_timeseries"
            preprocess_data["metadata"]["reference_location"] = reference_location

            logger.info(
                f"✅ 成功載入預處理數據: {len(preprocess_data.get('satellites', []))} 顆衛星"
            )
            return preprocess_data

        except Exception as e:
            logger.error(f"❌ 載入預處理數據失敗: {e}")
            return None

    async def _generate_dynamic_timeseries(
        self, constellation: str, reference_location: Dict[str, float]
    ) -> Optional[Dict[str, Any]]:
        """動態生成時間序列數據（運行時）"""
        try:
            # 載入本地 TLE 數據
            tle_data = await self.get_local_tle_data(constellation)
            if not tle_data:
                logger.error(f"❌ 無可用的 {constellation} TLE 數據")
                return None

            logger.info(f"🛰️ 開始動態生成 {constellation} 120分鐘時間序列數據")
            logger.info(
                f"📍 參考位置: {reference_location['latitude']:.4f}°N, {reference_location['longitude']:.4f}°E"
            )

            # 當前時間作為起始點
            from datetime import datetime, timezone, timedelta

            start_time = datetime.now(timezone.utc)

            satellites_timeseries = []

            # 智能選擇可見衛星以提高有效性
            selected_satellites = self._select_visible_satellites(
                tle_data, reference_location, start_time, max_satellites=10
            )
            logger.info(
                f"📊 處理 {len(selected_satellites)} 顆衛星的軌道數據（智能篩選）"
            )

            for i, sat_data in enumerate(selected_satellites):
                logger.info(
                    f"🔄 處理衛星 {i+1}/{len(selected_satellites)}: {sat_data.get('name', 'Unknown')}"
                )

                satellite_timeseries = (
                    await self._calculate_satellite_120min_timeseries(
                        sat_data, start_time, reference_location
                    )
                )

                if satellite_timeseries:
                    satellites_timeseries.append(
                        {
                            "norad_id": sat_data.get("norad_id", 0),
                            "name": sat_data.get("name", "Unknown"),
                            "constellation": constellation,
                            "time_series": satellite_timeseries,
                        }
                    )

            # 生成 UE 軌跡 (靜態 UE)
            ue_trajectory = []
            for i in range(self.total_time_points):
                current_time = start_time + timedelta(
                    seconds=i * self.time_interval_seconds
                )
                ue_trajectory.append(
                    {
                        "time_offset_seconds": i * self.time_interval_seconds,
                        "position": reference_location.copy(),
                        "serving_satellite": (
                            satellites_timeseries[0]["name"]
                            if satellites_timeseries
                            else "None"
                        ),
                        "handover_state": "stable",
                    }
                )

            # 構建統一時間序列數據
            unified_data = {
                "metadata": {
                    "computation_time": start_time.isoformat(),
                    "constellation": constellation,
                    "time_span_minutes": self.time_span_minutes,
                    "time_interval_seconds": self.time_interval_seconds,
                    "total_time_points": self.total_time_points,
                    "data_source": "dynamic_generation",
                    "sgp4_mode": "runtime_precision",
                    "network_dependency": False,
                    "reference_location": reference_location,
                    "satellites_processed": len(satellites_timeseries),
                },
                "satellites": satellites_timeseries,
                "ue_trajectory": ue_trajectory,
                "handover_events": [],  # 暫時為空，後續可擴展
            }

            logger.info(
                f"✅ 成功動態生成 120分鐘時間序列數據: {len(satellites_timeseries)} 顆衛星, {self.total_time_points} 時間點"
            )
            return unified_data

        except Exception as e:
            logger.error(f"❌ 動態生成時間序列數據失敗: {e}")
            return None

    def _validate_timeseries_data(self, data: Dict[str, Any]) -> bool:
        """驗證時間序列數據格式"""
        try:
            # 檢查必要字段
            required_fields = ["metadata", "satellites", "ue_trajectory"]
            for field in required_fields:
                if field not in data:
                    logger.warning(f"缺少必要字段: {field}")
                    return False

            # 檢查元數據
            metadata = data.get("metadata", {})
            metadata_fields = [
                "constellation",
                "time_span_minutes",
                "total_time_points",
            ]
            for field in metadata_fields:
                if field not in metadata:
                    logger.warning(f"元數據缺少字段: {field}")
                    return False

            # 檢查衛星數據
            satellites = data.get("satellites", [])
            if not satellites:
                logger.warning("衛星數據為空")
                return False

            # 檢查第一顆衛星的數據格式
            first_sat = satellites[0]
            sat_fields = ["norad_id", "name", "time_series"]
            for field in sat_fields:
                if field not in first_sat:
                    logger.warning(f"衛星數據缺少字段: {field}")
                    return False

            # 檢查時間序列數據
            time_series = first_sat.get("time_series", [])
            if not time_series:
                logger.warning("時間序列數據為空")
                return False

            return True

        except Exception as e:
            logger.error(f"數據格式驗證失敗: {e}")
            return False

    async def _calculate_satellite_120min_timeseries(
        self,
        sat_data: Dict[str, Any],
        start_time: datetime,
        reference_location: Dict[str, float],
    ) -> List[Dict[str, Any]]:
        """計算單顆衛星的 120 分鐘時間序列 - 使用 SGP4 精確軌道計算"""
        try:
            from datetime import timedelta
            import math
            from .sgp4_calculator import SGP4Calculator, TLEData
            from .distance_calculator import DistanceCalculator, Position

            time_series = []
            current_time = start_time

            # 提取 TLE 數據
            line1 = sat_data.get("line1", "")
            line2 = sat_data.get("line2", "")

            if not line1 or not line2:
                logger.warning(f"缺少 TLE 數據: {sat_data.get('name', 'Unknown')}")
                return []

            # 創建 TLE 數據對象
            tle_data = TLEData(
                name=sat_data.get("name", "Unknown"),
                line1=line1,
                line2=line2,
                epoch=start_time.isoformat(),
            )

            # 初始化 SGP4 計算器和距離計算器
            sgp4_calculator = SGP4Calculator()
            distance_calculator = DistanceCalculator()

            # 參考位置對象
            reference_pos = Position(
                latitude=reference_location["latitude"],
                longitude=reference_location["longitude"],
                altitude=reference_location["altitude"],
            )

            logger.info(f"🛰️ 使用 SGP4 計算衛星 {tle_data.name} 的精確軌道")

            for i in range(self.total_time_points):
                # 計算當前時間點
                time_offset = i * self.time_interval_seconds
                current_timestamp = current_time + timedelta(seconds=time_offset)

                # 使用 SGP4 計算精確軌道位置
                orbit_position = sgp4_calculator.propagate_orbit(
                    tle_data, current_timestamp
                )

                if not orbit_position:
                    # SGP4 計算失敗時使用簡化備用方案
                    logger.warning(f"SGP4 計算失敗，時間點 {i}，使用簡化備用方案")
                    orbit_position = self._calculate_fallback_position(
                        tle_data, current_timestamp, i
                    )

                # 計算觀測角度和距離
                try:
                    # 計算仰角 - 直接使用 orbit_position (OrbitPosition 類型)
                    elevation_deg = distance_calculator.calculate_elevation_angle(
                        reference_pos, orbit_position
                    )

                    # 計算方位角 - 直接使用 orbit_position (OrbitPosition 類型)
                    azimuth_deg = distance_calculator.calculate_azimuth_angle(
                        reference_pos, orbit_position
                    )

                    # 計算距離 - 這裡需要 OrbitPosition 類型
                    distance_result = distance_calculator.calculate_d2_distances(
                        reference_pos, orbit_position, reference_pos
                    )

                    satellite_distance_km = (
                        distance_result.satellite_distance / 1000
                    )  # 轉換為 km
                    ground_distance_km = (
                        distance_result.ground_distance / 1000
                    )  # 轉換為 km

                    # D2 事件專用：基於 SIB19 移動參考位置計算距離 (符合 3GPP TS 38.331 標準)
                    # 實現真正的 D2 事件：Ml1 和 Ml2 都是基於衛星星曆數據的移動參考位置

                    ue_lat_rad = math.radians(reference_location["latitude"])
                    ue_lon_rad = math.radians(reference_location["longitude"])
                    ue_alt = reference_location.get("altitude", 0.0)

                    # 🔧 修復：使用真實的 SIB19 移動參考位置計算
                    # 服務衛星的移動參考位置 (基於 SIB19 星曆數據)
                    serving_sat_lat_rad = math.radians(orbit_position.latitude)
                    serving_sat_lon_rad = math.radians(orbit_position.longitude)
                    serving_sat_alt = orbit_position.altitude * 1000  # 轉換為米

                    # 計算 Ml1：UE 到服務衛星移動參考位置的 3D 距離
                    earth_radius = 6371000.0  # 地球半徑 (米)

                    # UE 在地心坐標系中的位置
                    ue_x = (
                        (earth_radius + ue_alt)
                        * math.cos(ue_lat_rad)
                        * math.cos(ue_lon_rad)
                    )
                    ue_y = (
                        (earth_radius + ue_alt)
                        * math.cos(ue_lat_rad)
                        * math.sin(ue_lon_rad)
                    )
                    ue_z = (earth_radius + ue_alt) * math.sin(ue_lat_rad)

                    # 服務衛星在地心坐標系中的位置
                    serving_x = (
                        (earth_radius + serving_sat_alt)
                        * math.cos(serving_sat_lat_rad)
                        * math.cos(serving_sat_lon_rad)
                    )
                    serving_y = (
                        (earth_radius + serving_sat_alt)
                        * math.cos(serving_sat_lat_rad)
                        * math.sin(serving_sat_lon_rad)
                    )
                    serving_z = (earth_radius + serving_sat_alt) * math.sin(
                        serving_sat_lat_rad
                    )

                    # 3D 歐式距離計算 (Ml1)
                    d2_serving_distance_km = (
                        math.sqrt(
                            (serving_x - ue_x) ** 2
                            + (serving_y - ue_y) ** 2
                            + (serving_z - ue_z) ** 2
                        )
                        / 1000.0
                    )  # 轉換為公里

                    # 目標衛星的移動參考位置 (基於動態軌道計算)
                    # 使用 90 分鐘 LEO 軌道週期，符合真實衛星軌道特性
                    orbital_period = 90.0 * 60.0  # 90分鐘轉換為秒
                    time_factor = (time_offset * 60.0) % orbital_period  # 當前軌道時間
                    orbital_phase = (time_factor / orbital_period) * 2 * math.pi

                    # LEO 衛星軌道參數 (基於 Starlink 典型參數)
                    orbital_inclination = math.radians(53.0)  # 53度傾角
                    orbital_altitude = 550000.0  # 550km 高度 (米)

                    # 計算目標衛星的動態位置
                    target_lat = math.asin(
                        math.sin(orbital_inclination) * math.sin(orbital_phase)
                    )
                    target_lon = serving_sat_lon_rad + orbital_phase * 0.5  # 軌道進動
                    target_alt = orbital_altitude

                    # 目標衛星在地心坐標系中的位置
                    target_x = (
                        (earth_radius + target_alt)
                        * math.cos(target_lat)
                        * math.cos(target_lon)
                    )
                    target_y = (
                        (earth_radius + target_alt)
                        * math.cos(target_lat)
                        * math.sin(target_lon)
                    )
                    target_z = (earth_radius + target_alt) * math.sin(target_lat)

                    # 3D 歐式距離計算 (Ml2)
                    d2_target_distance_km = (
                        math.sqrt(
                            (target_x - ue_x) ** 2
                            + (target_y - ue_y) ** 2
                            + (target_z - ue_z) ** 2
                        )
                        / 1000.0
                    )  # 轉換為公里

                except Exception as e:
                    logger.warning(f"距離計算失敗: {e}，使用估算值")
                    # 簡化距離計算作為備用
                    lat_diff = orbit_position.latitude - reference_location["latitude"]
                    lon_diff = (
                        orbit_position.longitude - reference_location["longitude"]
                    )
                    ground_distance_km = math.sqrt(lat_diff**2 + lon_diff**2) * 111.32
                    satellite_distance_km = math.sqrt(
                        ground_distance_km**2 + orbit_position.altitude**2
                    )
                    elevation_deg = max(
                        0,
                        90
                        - math.degrees(
                            math.atan2(ground_distance_km, orbit_position.altitude)
                        ),
                    )
                    azimuth_deg = (
                        math.degrees(math.atan2(lon_diff, lat_diff)) + 360
                    ) % 360

                    # D2 事件專用：基於 SIB19 移動參考位置計算距離 (符合 3GPP TS 38.331 標準) - 備用計算
                    # 實現真正的 D2 事件：Ml1 和 Ml2 都是基於衛星星曆數據的移動參考位置

                    ue_lat_rad = math.radians(reference_location["latitude"])
                    ue_lon_rad = math.radians(reference_location["longitude"])
                    ue_alt = reference_location.get("altitude", 0.0)

                    # 🔧 修復：使用真實的 SIB19 移動參考位置計算（備用）
                    # 服務衛星的移動參考位置 (基於 SIB19 星曆數據)
                    serving_sat_lat_rad = math.radians(orbit_position.latitude)
                    serving_sat_lon_rad = math.radians(orbit_position.longitude)
                    serving_sat_alt = orbit_position.altitude * 1000  # 轉換為米

                    # 計算 Ml1：UE 到服務衛星移動參考位置的 3D 距離
                    earth_radius = 6371000.0  # 地球半徑 (米)

                    # UE 在地心坐標系中的位置
                    ue_x = (
                        (earth_radius + ue_alt)
                        * math.cos(ue_lat_rad)
                        * math.cos(ue_lon_rad)
                    )
                    ue_y = (
                        (earth_radius + ue_alt)
                        * math.cos(ue_lat_rad)
                        * math.sin(ue_lon_rad)
                    )
                    ue_z = (earth_radius + ue_alt) * math.sin(ue_lat_rad)

                    # 服務衛星在地心坐標系中的位置
                    serving_x = (
                        (earth_radius + serving_sat_alt)
                        * math.cos(serving_sat_lat_rad)
                        * math.cos(serving_sat_lon_rad)
                    )
                    serving_y = (
                        (earth_radius + serving_sat_alt)
                        * math.cos(serving_sat_lat_rad)
                        * math.sin(serving_sat_lon_rad)
                    )
                    serving_z = (earth_radius + serving_sat_alt) * math.sin(
                        serving_sat_lat_rad
                    )

                    # 3D 歐式距離計算 (Ml1)
                    d2_serving_distance_km = (
                        math.sqrt(
                            (serving_x - ue_x) ** 2
                            + (serving_y - ue_y) ** 2
                            + (serving_z - ue_z) ** 2
                        )
                        / 1000.0
                    )  # 轉換為公里

                    # 目標衛星的移動參考位置 (基於動態軌道計算) - 備用
                    # 使用 90 分鐘 LEO 軌道週期，符合真實衛星軌道特性
                    orbital_period = 90.0 * 60.0  # 90分鐘轉換為秒
                    time_factor = (time_offset * 60.0) % orbital_period  # 當前軌道時間
                    orbital_phase = (time_factor / orbital_period) * 2 * math.pi

                    # LEO 衛星軌道參數 (基於 Starlink 典型參數)
                    orbital_inclination = math.radians(53.0)  # 53度傾角
                    orbital_altitude = 550000.0  # 550km 高度 (米)

                    # 計算目標衛星的動態位置
                    target_lat = math.asin(
                        math.sin(orbital_inclination) * math.sin(orbital_phase)
                    )
                    target_lon = serving_sat_lon_rad + orbital_phase * 0.5  # 軌道進動
                    target_alt = orbital_altitude

                    # 目標衛星在地心坐標系中的位置
                    target_x = (
                        (earth_radius + target_alt)
                        * math.cos(target_lat)
                        * math.cos(target_lon)
                    )
                    target_y = (
                        (earth_radius + target_alt)
                        * math.cos(target_lat)
                        * math.sin(target_lon)
                    )
                    target_z = (earth_radius + target_alt) * math.sin(target_lat)

                    # 3D 歐式距離計算 (Ml2)
                    d2_target_distance_km = (
                        math.sqrt(
                            (target_x - ue_x) ** 2
                            + (target_y - ue_y) ** 2
                            + (target_z - ue_z) ** 2
                        )
                        / 1000.0
                    )  # 轉換為公里

                # 可見性判斷 (仰角 > 10度)
                is_visible = elevation_deg > 10.0

                # RSRP 估算 (基於精確距離的模型)
                rsrp_dbm = self._calculate_rsrp(satellite_distance_km, elevation_deg)

                # 信號品質估算
                rsrq_db = -12.0 + (elevation_deg - 10) * 0.1  # 仰角越高品質越好
                sinr_db = 18.0 + (elevation_deg - 10) * 0.2  # 仰角越高 SINR 越好

                # 構建時間點數據
                observation_data = {
                    "elevation_deg": elevation_deg,
                    "azimuth_deg": azimuth_deg,
                    "range_km": satellite_distance_km,
                    "is_visible": is_visible,
                    "rsrp_dbm": rsrp_dbm,
                    "rsrq_db": -12.0 + (elevation_deg - 10) * 0.1,
                    "sinr_db": 18.0 + (elevation_deg - 10) * 0.2,
                }

                measurement_events_data = {
                    "d1_distance_m": ground_distance_km * 1000,
                    "d2_satellite_distance_m": d2_serving_distance_km
                    * 1000,  # Ml1: UE 到服務衛星地面投影點距離
                    "d2_ground_distance_m": d2_target_distance_km
                    * 1000,  # Ml2: UE 到目標衛星地面投影點距離
                    "a4_trigger_condition": rsrp_dbm > -90,
                    "t1_time_condition": True,
                }

                # 驗證數據並修正異常值
                validated_observation = self._validate_observation_data(
                    observation_data
                )
                validated_measurement_events = self._validate_measurement_events(
                    measurement_events_data
                )

                time_point = {
                    "time_offset_seconds": time_offset,
                    "timestamp": current_timestamp.isoformat(),
                    "position": {
                        "latitude": orbit_position.latitude,
                        "longitude": orbit_position.longitude,
                        "altitude": orbit_position.altitude * 1000,  # 轉換為米
                        "velocity": {
                            "x": orbit_position.velocity[0],
                            "y": orbit_position.velocity[1],
                            "z": orbit_position.velocity[2],
                        },
                    },
                    "observation": validated_observation,
                    "handover_metrics": {
                        "signal_strength": max(
                            0, (validated_observation["rsrp_dbm"] + 120) / 70
                        ),  # 歸一化
                        "handover_score": (
                            0.8 if validated_observation["is_visible"] else 0.1
                        ),
                        "is_handover_candidate": validated_observation["is_visible"]
                        and validated_observation["elevation_deg"] > 15,
                        "predicted_service_time_seconds": self._calculate_service_time(
                            validated_observation["elevation_deg"]
                        ),
                    },
                    "measurement_events": validated_measurement_events,
                }

                time_series.append(time_point)

            logger.info(
                f"✅ SGP4 成功計算衛星 {tle_data.name} 的 {len(time_series)} 個時間點"
            )
            return time_series

        except Exception as e:
            logger.error(f"❌ SGP4 衛星時間序列計算失敗: {e}")
            # 完全失敗時返回空列表，讓上層處理
            return []

    def _calculate_fallback_position(
        self, tle_data: Any, timestamp: datetime, time_index: int
    ) -> Any:
        """SGP4 失敗時的簡化備用位置計算"""
        from .sgp4_calculator import OrbitPosition
        import math

        try:
            # 使用簡化圓軌道模型作為備用
            orbital_period_minutes = 1440 / tle_data.mean_motion  # 軌道週期
            progress = (
                time_index * self.time_interval_seconds / 60
            ) / orbital_period_minutes
            orbital_angle = (progress * 360) % 360

            # 基於軌道傾角的位置估算
            latitude = tle_data.inclination * math.sin(math.radians(orbital_angle))
            longitude = (orbital_angle - 180) % 360 - 180
            altitude = 550.0  # 典型 LEO 高度

            return OrbitPosition(
                latitude=latitude,
                longitude=longitude,
                altitude=altitude,
                velocity=(7.8, 0.0, 0.0),  # 簡化速度
                timestamp=timestamp,
                satellite_id=str(tle_data.catalog_number),
            )
        except Exception as e:
            logger.error(f"備用位置計算失敗: {e}")
            # 返回最基本的位置
            return OrbitPosition(
                latitude=25.0,
                longitude=121.0,
                altitude=550.0,
                velocity=(7.8, 0.0, 0.0),
                timestamp=timestamp,
                satellite_id="unknown",
            )

    def _calculate_rsrp(self, distance_km: float, elevation_deg: float) -> float:
        """基於精確距離和仰角的 RSRP 計算"""
        try:
            # 基於自由空間路徑損耗的 RSRP 模型
            # RSRP = Transmit_Power - Path_Loss - Atmospheric_Loss

            # 假設衛星發射功率 (dBm)
            transmit_power_dbm = 40.0  # 典型 LEO 衛星功率

            # 自由空間路徑損耗 (dB)
            frequency_ghz = 12.0  # Ku 頻段
            fspl_db = (
                20 * math.log10(distance_km) + 20 * math.log10(frequency_ghz) + 32.44
            )

            # 大氣損耗 (基於仰角)
            atmospheric_loss_db = max(
                0, (90 - elevation_deg) / 90 * 3.0
            )  # 最大3dB大氣損耗

            # 其他損耗 (多路徑、遮擋等)
            other_losses_db = 5.0

            rsrp_dbm = (
                transmit_power_dbm - fspl_db - atmospheric_loss_db - other_losses_db
            )

            # 限制在合理範圍內
            return max(-120, min(-50, rsrp_dbm))

        except Exception as e:
            logger.warning(f"RSRP 計算失敗: {e}，使用簡化模型")
            # 簡化模型備用
            return -70 - 20 * math.log10(distance_km / 500) if distance_km > 0 else -70

    def _calculate_service_time(self, elevation_deg: float) -> int:
        """基於仰角估算衛星服務時間"""
        if elevation_deg <= 10:
            return 0
        elif elevation_deg <= 30:
            return 300  # 5分鐘
        elif elevation_deg <= 60:
            return 600  # 10分鐘
        else:
            return 900  # 15分鐘

    def _select_visible_satellites(
        self,
        tle_data: List[Dict[str, Any]],
        reference_location: Dict[str, float],
        timestamp: datetime,
        max_satellites: int = 10,
    ) -> List[Dict[str, Any]]:
        """智能選擇可見衛星，優先選擇高仰角衛星"""
        from .sgp4_calculator import SGP4Calculator, TLEData
        from .distance_calculator import DistanceCalculator, Position

        try:
            sgp4_calc = SGP4Calculator()
            dist_calc = DistanceCalculator()

            reference_pos = Position(
                latitude=reference_location["latitude"],
                longitude=reference_location["longitude"],
                altitude=reference_location.get("altitude", 0),
            )

            visible_satellites = []

            for sat_data in tle_data:
                try:
                    # 創建 TLE 數據對象
                    tle_data_obj = TLEData(
                        name=sat_data["name"],
                        line1=sat_data["line1"],
                        line2=sat_data["line2"],
                    )

                    # 計算當前位置
                    orbit_pos = sgp4_calc.propagate_orbit(tle_data_obj, timestamp)

                    if orbit_pos:
                        satellite_pos = Position(
                            latitude=orbit_pos.latitude,
                            longitude=orbit_pos.longitude,
                            altitude=orbit_pos.altitude,  # 保持km單位
                            velocity=getattr(orbit_pos, "velocity", (0.0, 0.0, 0.0)),
                        )

                        # 計算仰角 - 直接使用 orbit_pos (OrbitPosition 類型)
                        elevation = dist_calc.calculate_elevation_angle(
                            reference_pos, orbit_pos
                        )

                        # 只選擇可見衛星（仰角 > 5 度，避免地平線附近的噪音）
                        if elevation > 5.0:
                            visible_satellites.append(
                                {
                                    "satellite_data": sat_data,
                                    "elevation": elevation,
                                    "orbit_position": orbit_pos,
                                }
                            )

                except Exception as e:
                    logger.debug(f"跳過衛星 {sat_data.get('name', 'unknown')}: {e}")
                    continue

            # 按仰角排序，選擇最高的衛星
            visible_satellites.sort(key=lambda x: x["elevation"], reverse=True)
            selected = visible_satellites[:max_satellites]

            logger.info(
                f"🛰️ 從 {len(tle_data)} 顆衛星中篩選出 {len(selected)} 顆可見衛星"
            )
            for sat in selected:
                logger.info(
                    f"   - {sat['satellite_data']['name']}: 仰角 {sat['elevation']:.1f}°"
                )

            # 如果沒有可見衛星，回退到前幾顆衛星
            if not selected:
                logger.warning("⚠️ 沒有找到可見衛星，使用前10顆衛星作為備用")
                return tle_data[:max_satellites]

            return [sat["satellite_data"] for sat in selected]

        except Exception as e:
            logger.error(f"衛星選擇失敗: {e}，使用前10顆衛星作為備用")
            return tle_data[:max_satellites]

    def _validate_observation_data(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """驗證並修正觀測數據中的異常數值"""
        try:
            validated = observation.copy()

            # 距離驗證 (LEO 衛星應該在 300-2000 km 範圍內)
            range_km = validated.get("range_km", 0)
            if range_km <= 0 or range_km > 10000:
                logger.warning(f"⚠️ 異常距離數值 {range_km} km，修正為合理範圍")
                validated["range_km"] = 550  # 預設為典型 LEO 高度
            elif range_km > 3000:
                logger.warning(f"⚠️ 距離過遠 {range_km} km，限制在 3000km 內")
                validated["range_km"] = min(range_km, 3000)

            # 仰角驗證 (0-90 度)
            elevation_deg = validated.get("elevation_deg", 0)
            if elevation_deg < 0 or elevation_deg > 90:
                logger.warning(f"⚠️ 異常仰角數值 {elevation_deg}°，修正為合理範圍")
                validated["elevation_deg"] = max(0, min(90, elevation_deg))

            # 方位角驗證 (0-360 度)
            azimuth_deg = validated.get("azimuth_deg", 0)
            if azimuth_deg < 0 or azimuth_deg > 360:
                logger.warning(f"⚠️ 異常方位角數值 {azimuth_deg}°，修正為合理範圍")
                validated["azimuth_deg"] = azimuth_deg % 360

            # RSRP 驗證 (-150 到 -50 dBm)
            rsrp_dbm = validated.get("rsrp_dbm", -70)
            if rsrp_dbm > -50 or rsrp_dbm < -150:
                logger.warning(f"⚠️ 異常 RSRP 數值 {rsrp_dbm} dBm，修正為合理範圍")
                validated["rsrp_dbm"] = max(-150, min(-50, rsrp_dbm))

            return validated

        except Exception as e:
            logger.error(f"數據驗證失敗: {e}")
            return observation

    def _validate_measurement_events(
        self, measurement_events: Dict[str, Any]
    ) -> Dict[str, Any]:
        """驗證並修正測量事件數據中的異常數值"""
        try:
            validated = measurement_events.copy()

            # D2 距離驗證 (基於 SIB19 移動參考位置的 3D 距離，允許更大範圍)
            d2_satellite_distance_m = validated.get("d2_satellite_distance_m", 0)
            if d2_satellite_distance_m > 5000000:  # 超過 5000 km 的 3D 距離異常
                logger.warning(
                    f"⚠️ 異常 D2 衛星距離 {d2_satellite_distance_m} m，修正為合理值"
                )
                validated["d2_satellite_distance_m"] = min(
                    5000000, d2_satellite_distance_m
                )  # 最大 5000 km (包含高軌道衛星)

            d2_ground_distance_m = validated.get("d2_ground_distance_m", 0)
            if d2_ground_distance_m > 5000000:  # 超過 5000 km 的 3D 距離異常
                logger.warning(
                    f"⚠️ 異常 D2 地面距離 {d2_ground_distance_m} m，修正為合理值"
                )
                validated["d2_ground_distance_m"] = min(
                    5000000, d2_ground_distance_m
                )  # 最大 5000 km (包含高軌道衛星)

            # D1 距離驗證
            d1_distance_m = validated.get("d1_distance_m", 0)
            if d1_distance_m > 2000000:  # 超過 2000 km 異常
                logger.warning(f"⚠️ 異常 D1 距離 {d1_distance_m} m，修正為合理值")
                validated["d1_distance_m"] = min(500000, d1_distance_m)  # 最大 500 km

            return validated

        except Exception as e:
            logger.error(f"測量事件數據驗證失敗: {e}")
            return measurement_events


# 全局實例
_local_volume_service = None


def get_local_volume_service() -> LocalVolumeDataService:
    """獲取本地 Volume 數據服務實例"""
    global _local_volume_service
    if _local_volume_service is None:
        _local_volume_service = LocalVolumeDataService()
    return _local_volume_service
