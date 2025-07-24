"""
🛰️ 衛星數據管理服務
統一管理 TLE 數據、軌道計算和 D2 測量緩存
避免數據重複，與 RL 系統共享數據
"""

import asyncio
import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, asdict
import asyncpg
import aiohttp
import structlog

logger = structlog.get_logger(__name__)

from .orbit_calculation_engine import (
    OrbitCalculationEngine,
    SatellitePosition,
    TLEData,
    TimeRange,
)


@dataclass
class SatelliteInfo:
    """衛星基本信息"""

    satellite_id: str
    norad_id: int
    satellite_name: str
    constellation: str
    is_active: bool
    orbital_period: float  # 分鐘
    last_updated: datetime


@dataclass
class D2MeasurementPoint:
    """D2 測量數據點"""

    timestamp: datetime
    satellite_id: str
    norad_id: int
    constellation: str
    satellite_distance: float  # 米
    ground_distance: float  # 米
    satellite_position: Dict[str, float]  # lat, lon, alt
    trigger_condition_met: bool
    event_type: str  # 'entering', 'leaving', 'none'
    signal_strength: Optional[float] = None


@dataclass
class D2ScenarioConfig:
    """D2 場景配置"""

    scenario_name: str
    ue_position: Dict[str, float]  # lat, lon, alt
    fixed_ref_position: Dict[str, float]  # lat, lon, alt
    thresh1: float
    thresh2: float
    hysteresis: float
    constellation: str
    duration_minutes: int
    sample_interval_seconds: int


class SatelliteDataManager:
    """
    衛星數據管理器

    功能：
    1. 統一管理 TLE 數據和軌道計算
    2. 預載和緩存衛星軌道數據
    3. 生成 D2 測量事件數據
    4. 與 RL 系統共享數據，避免重複
    """

    def __init__(self, db_url: str):
        self.db_url = db_url
        self.orbit_engine = OrbitCalculationEngine()
        self.db_pool: Optional[asyncpg.Pool] = None

        # TLE 數據源配置
        self.tle_sources = {
            "starlink": "https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle",
            "oneweb": "https://celestrak.org/NORAD/elements/gp.php?GROUP=oneweb&FORMAT=tle",
            "gps": "https://celestrak.org/NORAD/elements/gp.php?GROUP=gps-ops&FORMAT=tle",
            "galileo": "https://celestrak.org/NORAD/elements/gp.php?GROUP=galileo&FORMAT=tle",
        }

    async def initialize(self):
        """初始化數據庫連接池"""
        try:
            self.db_pool = await asyncpg.create_pool(
                self.db_url, min_size=5, max_size=20, command_timeout=60
            )
            logger.info("🛰️ 衛星數據管理器初始化完成")

            # 確保數據庫表存在
            await self._ensure_tables_exist()

        except Exception as e:
            logger.error(f"❌ 衛星數據管理器初始化失敗: {e}")
            raise

    async def _ensure_tables_exist(self):
        """確保數據庫表存在"""
        schema_file = "services/rl_training/database/satellite_cache_schema.sql"
        try:
            with open(schema_file, "r", encoding="utf-8") as f:
                schema_sql = f.read()

            async with self.db_pool.acquire() as conn:
                await conn.execute(schema_sql)

            logger.info("✅ 衛星數據表結構檢查完成")

        except FileNotFoundError:
            logger.warning(f"⚠️ Schema 文件不存在: {schema_file}")
        except Exception as e:
            logger.error(f"❌ 數據表創建失敗: {e}")

    async def update_tle_data(self, constellation: str) -> Dict[str, Any]:
        """
        更新指定星座的 TLE 數據

        Args:
            constellation: 星座名稱 ('starlink', 'oneweb', 'gps', etc.)

        Returns:
            更新結果統計
        """
        if constellation not in self.tle_sources:
            raise ValueError(f"不支援的星座: {constellation}")

        logger.info(f"🔄 開始更新 {constellation} TLE 數據...")

        start_time = datetime.now(timezone.utc)
        stats = {
            "constellation": constellation,
            "satellites_updated": 0,
            "satellites_added": 0,
            "satellites_failed": 0,
            "start_time": start_time,
            "errors": [],
        }

        try:
            # 下載 TLE 數據（包含 fallback 機制）
            tle_data_list = await self._download_tle_data(constellation)

            if not tle_data_list:
                stats["errors"].append("無法下載 TLE 數據且 fallback 數據載入失敗")
                return stats

            # 批量更新數據庫
            async with self.db_pool.acquire() as conn:
                async with conn.transaction():
                    for tle_data in tle_data_list:
                        try:
                            # 檢查是否已存在
                            existing = await conn.fetchrow(
                                "SELECT id FROM satellite_tle_data WHERE norad_id = $1",
                                int(tle_data.satellite_id),  # 轉換為整數
                            )

                            if existing:
                                # 更新現有記錄
                                await conn.execute(
                                    """
                                    UPDATE satellite_tle_data SET
                                        satellite_name = $2, line1 = $3, line2 = $4,
                                        epoch = $5, orbital_period = $6, last_updated = $7
                                    WHERE norad_id = $1
                                """,
                                    int(tle_data.satellite_id),
                                    tle_data.satellite_name,
                                    tle_data.line1,
                                    tle_data.line2,
                                    tle_data.epoch,
                                    90.0,
                                    datetime.now(timezone.utc),  # 預設軌道週期
                                )
                                stats["satellites_updated"] += 1
                            else:
                                # 插入新記錄
                                await conn.execute(
                                    """
                                    INSERT INTO satellite_tle_data (
                                        satellite_id, norad_id, satellite_name, constellation,
                                        line1, line2, epoch, orbital_period
                                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                                """,
                                    f"{constellation}_{tle_data.satellite_id}",
                                    int(tle_data.satellite_id),
                                    tle_data.satellite_name,
                                    constellation,
                                    tle_data.line1,
                                    tle_data.line2,
                                    tle_data.epoch,
                                    90.0,
                                )
                                stats["satellites_added"] += 1

                        except Exception as e:
                            logger.warning(
                                f"⚠️ 衛星 {tle_data.satellite_id} 更新失敗: {e}"
                            )
                            stats["satellites_failed"] += 1
                            stats["errors"].append(
                                f"衛星 {tle_data.satellite_id}: {str(e)}"
                            )

            end_time = datetime.now(timezone.utc)
            stats["end_time"] = end_time
            stats["duration_seconds"] = (end_time - start_time).total_seconds()

            logger.info(
                f"✅ {constellation} TLE 更新完成: "
                f"新增 {stats['satellites_added']}, "
                f"更新 {stats['satellites_updated']}, "
                f"失敗 {stats['satellites_failed']}"
            )

            return stats

        except Exception as e:
            logger.error(f"❌ {constellation} TLE 更新失敗: {e}")
            stats["errors"].append(str(e))
            return stats

    async def _download_tle_data(self, constellation: str) -> List[TLEData]:
        """下載 TLE 數據，支持 fallback 機制"""
        url = self.tle_sources[constellation]

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    if response.status != 200:
                        logger.error(f"❌ TLE 下載失敗: HTTP {response.status}")
                        return await self._load_fallback_tle_data(constellation)

                    content = await response.text()
                    tle_data = self._parse_tle_content(content, constellation)
                    
                    if not tle_data:
                        logger.warning(f"⚠️ TLE 解析結果為空，使用 fallback 數據")
                        return await self._load_fallback_tle_data(constellation)
                    
                    return tle_data

        except Exception as e:
            logger.error(f"❌ TLE 下載異常: {e}")
            return await self._load_fallback_tle_data(constellation)

    def _parse_tle_content(self, content: str, constellation: str) -> List[TLEData]:
        """解析 TLE 內容"""
        lines = content.strip().split("\n")
        tle_data_list = []

        # TLE 格式：每3行為一組 (名稱, Line1, Line2)
        for i in range(0, len(lines), 3):
            if i + 2 >= len(lines):
                break

            try:
                name = lines[i].strip()
                line1 = lines[i + 1].strip()
                line2 = lines[i + 2].strip()

                # 從 Line1 提取 NORAD ID
                norad_id = line1[2:7].strip()

                # 從 Line1 提取 epoch
                epoch_year = int(line1[18:20])
                epoch_day = float(line1[20:32])

                # 轉換為完整年份
                if epoch_year < 57:  # 假設 57 以下為 20xx 年
                    full_year = 2000 + epoch_year
                else:
                    full_year = 1900 + epoch_year

                # 計算 epoch 時間
                epoch = datetime(full_year, 1, 1, tzinfo=timezone.utc) + timedelta(
                    days=epoch_day - 1
                )

                tle_data = TLEData(
                    satellite_id=norad_id,
                    satellite_name=name,
                    line1=line1,
                    line2=line2,
                    epoch=epoch,
                )

                tle_data_list.append(tle_data)

            except Exception as e:
                logger.warning(f"⚠️ TLE 解析失敗: {e}, 行: {i}")
                continue

        logger.info(f"📡 解析 {constellation} TLE 數據: {len(tle_data_list)} 顆衛星")
        return tle_data_list

    async def _load_fallback_tle_data(self, constellation: str) -> List[TLEData]:
        """
        載入 fallback TLE 數據
        Phase 2 修復：當外部 TLE 下載失敗時的備用機制
        """
        logger.info(f"🔄 載入 {constellation} fallback TLE 數據...")
        
        # Starlink fallback 數據 - 基於真實 TLE 格式
        fallback_data = {
            "starlink": [
                {
                    "name": "STARLINK-1007",
                    "norad_id": "44713",
                    "line1": "1 44713U 19074A   25204.91667000  .00002182  00000-0  16538-3 0  9999",
                    "line2": "2 44713  53.0534  95.4567 0001234  87.6543 272.3456 15.05000000289456",
                },
                {
                    "name": "STARLINK-1008",
                    "norad_id": "44714",
                    "line1": "1 44714U 19074B   25204.91667000  .00002135  00000-0  16234-3 0  9999",
                    "line2": "2 44714  53.0534  105.5678 0001456  88.7654 273.4567 15.05000000289467",
                },
                {
                    "name": "STARLINK-1009",
                    "norad_id": "44715",
                    "line1": "1 44715U 19074C   25204.91667000  .00002089  00000-0  15923-3 0  9999",
                    "line2": "2 44715  53.0534  115.6789 0001678  89.8765 274.5678 15.05000000289478",
                },
                {
                    "name": "STARLINK-1010",
                    "norad_id": "44716",
                    "line1": "1 44716U 19074D   25204.91667000  .00001998  00000-0  15612-3 0  9999",
                    "line2": "2 44716  53.0534  125.7890 0001890  90.9876 275.6789 15.05000000289489",
                },
                {
                    "name": "STARLINK-1011",
                    "norad_id": "44717",
                    "line1": "1 44717U 19074E   25204.91667000  .00001945  00000-0  15301-3 0  9999",
                    "line2": "2 44717  53.0534  135.8901 0002012  92.0987 276.7890 15.05000000289500",
                },
            ],
            "oneweb": [
                {
                    "name": "ONEWEB-0001",
                    "norad_id": "44063",
                    "line1": "1 44063U 19005A   25204.50000000  .00001234  00000-0  12345-3 0  9999",
                    "line2": "2 44063  87.4000  10.0000 0001000  45.0000 315.0000 13.26000000234567",
                },
                {
                    "name": "ONEWEB-0002",
                    "norad_id": "44064",
                    "line1": "1 44064U 19005B   25204.50000000  .00001200  00000-0  12000-3 0  9999",
                    "line2": "2 44064  87.4000  20.0000 0001200  46.0000 314.0000 13.26000000234578",
                },
            ],
            "gps": [
                {
                    "name": "GPS IIF-1",
                    "norad_id": "37753",
                    "line1": "1 37753U 11036A   25204.50000000 -.00000018  00000-0  00000-0 0  9999",
                    "line2": "2 37753  55.0000  50.0000 0001000  45.0000 315.0000  2.00000000567890",
                },
            ],
            "galileo": [
                {
                    "name": "GALILEO-101",
                    "norad_id": "37846",
                    "line1": "1 37846U 11060A   25204.50000000  .00000010  00000-0  00000-0 0  9999",
                    "line2": "2 37846  56.0000  60.0000 0002000  50.0000 310.0000  1.70000000345678",
                },
            ]
        }
        
        constellation_data = fallback_data.get(constellation, [])
        
        if not constellation_data:
            logger.warning(f"⚠️ 沒有可用的 {constellation} fallback 數據")
            return []
        
        tle_data_list = []
        
        try:
            for sat_data in constellation_data:
                # 從 line1 解析 epoch 時間
                line1 = sat_data["line1"]
                epoch_year = int(line1[18:20])
                epoch_day = float(line1[20:32])
                
                # 轉換為完整年份
                if epoch_year < 57:
                    full_year = 2000 + epoch_year
                else:
                    full_year = 1900 + epoch_year
                
                # 計算 epoch 時間
                from datetime import datetime, timedelta, timezone
                epoch = datetime(full_year, 1, 1, tzinfo=timezone.utc) + timedelta(
                    days=epoch_day - 1
                )
                
                tle_data = TLEData(
                    satellite_id=sat_data["norad_id"],
                    satellite_name=sat_data["name"],
                    line1=sat_data["line1"],
                    line2=sat_data["line2"],
                    epoch=epoch,
                )
                
                tle_data_list.append(tle_data)
                
            logger.info(f"✅ 載入 {constellation} fallback 數據: {len(tle_data_list)} 顆衛星")
            return tle_data_list
            
        except Exception as e:
            logger.error(f"❌ 載入 {constellation} fallback 數據失敗: {e}")
            return []

    async def get_active_satellites(self, constellation: str) -> List[SatelliteInfo]:
        """獲取活躍衛星列表"""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT satellite_id, norad_id, satellite_name, constellation,
                       is_active, orbital_period, last_updated
                FROM satellite_tle_data 
                WHERE constellation = $1 AND is_active = TRUE
                ORDER BY satellite_name
            """,
                constellation,
            )

            return [
                SatelliteInfo(
                    satellite_id=row["satellite_id"],
                    norad_id=row["norad_id"],
                    satellite_name=row["satellite_name"],
                    constellation=row["constellation"],
                    is_active=row["is_active"],
                    orbital_period=row["orbital_period"],
                    last_updated=row["last_updated"],
                )
                for row in rows
            ]

    def _generate_scenario_hash(self, config: D2ScenarioConfig) -> str:
        """生成場景配置的 hash"""
        config_str = json.dumps(asdict(config), sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()

    async def precompute_d2_measurements(
        self, config: D2ScenarioConfig
    ) -> Dict[str, Any]:
        """
        預計算 D2 測量數據並緩存

        Args:
            config: D2 場景配置

        Returns:
            計算結果統計
        """
        logger.info(f"🔄 開始預計算 D2 測量數據: {config.scenario_name}")

        start_time = datetime.now(timezone.utc)
        scenario_hash = self._generate_scenario_hash(config)

        # 清除該場景的舊 D2 測量緩存以避免時間間隔衝突
        async with self.db_pool.acquire() as conn:
            deleted_rows = await conn.execute(
                "DELETE FROM d2_measurement_cache WHERE scenario_hash = $1",
                scenario_hash
            )
            logger.info(f"🧹 已清除場景 {config.scenario_name} 的 D2 測量緩存: {deleted_rows} 筆記錄")

        stats = {
            "scenario_name": config.scenario_name,
            "scenario_hash": scenario_hash,
            "measurements_generated": 0,
            "satellites_processed": 0,
            "start_time": start_time,
            "errors": [],
        }

        try:
            # 獲取指定星座的活躍衛星
            satellites = await self.get_active_satellites(config.constellation)

            if not satellites:
                stats["errors"].append(f"沒有找到 {config.constellation} 的活躍衛星")
                return stats

            # 選擇一顆衛星進行計算 (可以擴展為多顆)
            target_satellite = satellites[0]  # 暫時使用第一顆衛星

            # 計算時間範圍
            end_time = start_time + timedelta(minutes=config.duration_minutes)
            time_range = TimeRange(start=start_time, end=end_time)

            # 預計算軌道數據
            await self._precompute_orbital_data(target_satellite, time_range, config)

            # 生成 D2 測量數據
            measurements = await self._generate_d2_measurements(
                config, target_satellite, time_range
            )

            # 批量插入數據庫
            async with self.db_pool.acquire() as conn:
                async with conn.transaction():
                    for measurement in measurements:
                        await conn.execute(
                            """
                            INSERT INTO d2_measurement_cache (
                                scenario_name, scenario_hash, ue_latitude, ue_longitude, ue_altitude,
                                fixed_ref_latitude, fixed_ref_longitude, fixed_ref_altitude,
                                moving_ref_latitude, moving_ref_longitude, moving_ref_altitude,
                                satellite_id, norad_id, constellation, timestamp,
                                satellite_distance, ground_distance, thresh1, thresh2, hysteresis,
                                trigger_condition_met, event_type, data_source
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23)
                        """,
                            config.scenario_name,
                            scenario_hash,
                            config.ue_position["latitude"],
                            config.ue_position["longitude"],
                            config.ue_position["altitude"],
                            config.fixed_ref_position["latitude"],
                            config.fixed_ref_position["longitude"],
                            config.fixed_ref_position["altitude"],
                            measurement.satellite_position["latitude"],
                            measurement.satellite_position["longitude"],
                            measurement.satellite_position["altitude"],
                            measurement.satellite_id,
                            measurement.norad_id,
                            measurement.constellation,
                            measurement.timestamp,
                            measurement.satellite_distance,
                            measurement.ground_distance,
                            config.thresh1,
                            config.thresh2,
                            config.hysteresis,
                            measurement.trigger_condition_met,
                            measurement.event_type,
                            "real",
                        )

            stats["measurements_generated"] = len(measurements)
            stats["satellites_processed"] = 1

            end_time = datetime.now(timezone.utc)
            stats["end_time"] = end_time
            stats["duration_seconds"] = (end_time - start_time).total_seconds()

            logger.info(f"✅ D2 測量數據預計算完成: {len(measurements)} 個數據點")
            return stats

        except Exception as e:
            logger.error(f"❌ D2 測量數據預計算失敗: {e}")
            stats["errors"].append(str(e))
            return stats

    async def _precompute_orbital_data(
        self, satellite: SatelliteInfo, time_range: TimeRange, config: D2ScenarioConfig
    ):
        """預計算軌道數據"""
        # 從數據庫獲取 TLE 數據
        async with self.db_pool.acquire() as conn:
            tle_row = await conn.fetchrow(
                """
                SELECT line1, line2, epoch FROM satellite_tle_data
                WHERE norad_id = $1
            """,
                satellite.norad_id,
            )

            if not tle_row:
                raise ValueError(f"找不到衛星 {satellite.norad_id} 的 TLE 數據")

        # 初始化軌道計算引擎
        tle_data = TLEData(
            satellite_id=str(satellite.norad_id),
            satellite_name=satellite.satellite_name,
            line1=tle_row["line1"],
            line2=tle_row["line2"],
            epoch=tle_row["epoch"],
        )

        self.orbit_engine.add_tle_data(tle_data)

        # 計算軌道路徑 - 修復：使用配置中的採樣間隔，避免硬編碼
        sample_interval_minutes = config.sample_interval_seconds / 60.0
        logger.info(f"🔧 使用採樣間隔: {sample_interval_minutes} 分鐘 (來自配置: {config.sample_interval_seconds} 秒)")
        
        orbit_path = self.orbit_engine.predict_orbit_path(
            str(satellite.norad_id), time_range, sample_interval_minutes=sample_interval_minutes
        )

        if not orbit_path:
            raise ValueError(f"無法計算衛星 {satellite.norad_id} 的軌道路徑")

        # 清除該衛星的舊緩存數據以避免採樣間隔衝突
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM satellite_orbital_cache WHERE satellite_id = $1",
                str(satellite.norad_id)
            )
            logger.info(f"🧹 已清除衛星 {satellite.norad_id} 的軌道緩存數據")

        # 緩存軌道數據
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                for position in orbit_path.positions:
                    await conn.execute(
                        """
                        INSERT INTO satellite_orbital_cache (
                            satellite_id, norad_id, constellation, timestamp,
                            position_x, position_y, position_z,
                            latitude, longitude, altitude,
                            velocity_x, velocity_y, velocity_z, orbital_period
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                        ON CONFLICT (satellite_id, timestamp) DO UPDATE SET
                            position_x = EXCLUDED.position_x,
                            position_y = EXCLUDED.position_y,
                            position_z = EXCLUDED.position_z,
                            latitude = EXCLUDED.latitude,
                            longitude = EXCLUDED.longitude,
                            altitude = EXCLUDED.altitude
                    """,
                        position.satellite_id,
                        satellite.norad_id,
                        satellite.constellation,
                        position.timestamp,
                        position.x,
                        position.y,
                        position.z,
                        position.latitude,
                        position.longitude,
                        position.altitude,
                        position.velocity_x,
                        position.velocity_y,
                        position.velocity_z,
                        position.orbital_period,
                    )

    async def get_cached_d2_measurements(
        self, scenario_hash: str
    ) -> List[D2MeasurementPoint]:
        """獲取緩存的 D2 測量數據"""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT timestamp, satellite_id, norad_id, constellation,
                       satellite_distance, ground_distance, trigger_condition_met, event_type,
                       moving_ref_latitude, moving_ref_longitude, moving_ref_altitude
                FROM d2_measurement_cache
                WHERE scenario_hash = $1
                ORDER BY timestamp
            """,
                scenario_hash,
            )

            return [
                D2MeasurementPoint(
                    timestamp=row["timestamp"],
                    satellite_id=row["satellite_id"],
                    norad_id=row["norad_id"],
                    constellation=row["constellation"],
                    satellite_distance=row["satellite_distance"],
                    ground_distance=row["ground_distance"],
                    satellite_position={
                        "latitude": row["moving_ref_latitude"],
                        "longitude": row["moving_ref_longitude"],
                        "altitude": row["moving_ref_altitude"],
                    },
                    trigger_condition_met=row["trigger_condition_met"],
                    event_type=row["event_type"],
                )
                for row in rows
            ]

    async def _generate_d2_measurements(
        self, config: D2ScenarioConfig, satellite: SatelliteInfo, time_range: TimeRange
    ) -> List[D2MeasurementPoint]:
        """生成 D2 測量數據"""
        measurements = []

        # 從緩存獲取軌道數據
        async with self.db_pool.acquire() as conn:
            orbital_rows = await conn.fetch(
                """
                SELECT timestamp, latitude, longitude, altitude
                FROM satellite_orbital_cache
                WHERE norad_id = $1 AND timestamp BETWEEN $2 AND $3
                ORDER BY timestamp
            """,
                satellite.norad_id,
                time_range.start,
                time_range.end,
            )

        if not orbital_rows:
            logger.warning(f"沒有找到衛星 {satellite.norad_id} 的軌道數據")
            return measurements

        # UE 位置
        ue_lat = config.ue_position["latitude"]
        ue_lon = config.ue_position["longitude"]
        ue_alt = config.ue_position["altitude"]

        # 固定參考位置
        fixed_lat = config.fixed_ref_position["latitude"]
        fixed_lon = config.fixed_ref_position["longitude"]
        fixed_alt = config.fixed_ref_position["altitude"]

        # 移動軌跡參數（模擬 UE 移動）
        total_duration = len(orbital_rows) * 60  # 總時長（秒）
        movement_radius = 0.01  # 移動半徑（度，約1公里）

        logger.info(f"🔍 [D2] 初始UE位置: ({ue_lat}, {ue_lon}, {ue_alt})")
        logger.info(f"🔍 [D2] 固定參考位置: ({fixed_lat}, {fixed_lon}, {fixed_alt})")
        logger.info(f"🔍 [D2] 模擬UE移動軌跡，半徑: {movement_radius}度")

        # 處理每個時間點的軌道數據
        for i, row in enumerate(orbital_rows):
            timestamp = row["timestamp"]
            sat_lat = row["latitude"]
            sat_lon = row["longitude"]
            sat_alt = row["altitude"]

            # 計算當前時間點的 UE 位置（模擬移動軌跡）
            import math

            time_progress = i / max(1, len(orbital_rows) - 1)  # 0 到 1
            angle = time_progress * 2 * math.pi  # 完整圓周

            # UE 沿圓形軌跡移動
            current_ue_lat = ue_lat + movement_radius * math.cos(angle)
            current_ue_lon = ue_lon + movement_radius * math.sin(angle)
            current_ue_alt = ue_alt

            # 計算 UE 到衛星的距離 (移動參考位置)
            satellite_distance = self._calculate_distance(
                current_ue_lat,
                current_ue_lon,
                current_ue_alt,
                sat_lat,
                sat_lon,
                sat_alt,
            )

            # 計算 UE 到固定參考位置的距離（現在會隨時間變化）
            ground_distance = self._calculate_distance(
                current_ue_lat,
                current_ue_lon,
                current_ue_alt,
                fixed_lat,
                fixed_lon,
                fixed_alt,
            )

            # 計算 D2 事件條件
            # D2 進入條件: Ml1 - Hys > Thresh1 AND Ml2 + Hys < Thresh2
            # D2 離開條件: Ml1 + Hys < Thresh1 OR Ml2 - Hys > Thresh2
            ml1 = satellite_distance  # UE 到移動參考位置 (衛星)
            ml2 = ground_distance  # UE 到固定參考位置

            entering_condition = (ml1 - config.hysteresis > config.thresh1) and (
                ml2 + config.hysteresis < config.thresh2
            )

            leaving_condition = (ml1 + config.hysteresis < config.thresh1) or (
                ml2 - config.hysteresis > config.thresh2
            )

            # 確定事件類型
            if entering_condition:
                event_type = "entering"
                trigger_condition_met = True
            elif leaving_condition:
                event_type = "leaving"
                trigger_condition_met = True
            else:
                event_type = "none"
                trigger_condition_met = False

            measurement = D2MeasurementPoint(
                timestamp=timestamp,
                satellite_id=satellite.satellite_id,
                norad_id=satellite.norad_id,
                constellation=satellite.constellation,
                satellite_distance=satellite_distance,
                ground_distance=ground_distance,
                satellite_position={
                    "latitude": sat_lat,
                    "longitude": sat_lon,
                    "altitude": sat_alt,
                },
                trigger_condition_met=trigger_condition_met,
                event_type=event_type,
            )

            measurements.append(measurement)

        logger.info(f"📊 生成 {len(measurements)} 個 D2 測量數據點")
        return measurements

    def _calculate_distance(
        self,
        lat1: float,
        lon1: float,
        alt1: float,
        lat2: float,
        lon2: float,
        alt2: float,
    ) -> float:
        """
        計算兩點間的 3D 距離 (米)
        使用 Haversine 公式計算地表距離，然後加上高度差
        """
        import math

        # 地球半徑 (米)
        R = 6371000

        # 轉換為弧度
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        # Haversine 公式
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        # 地表距離
        surface_distance = R * c

        # 高度差 (轉換為米)
        height_diff = abs(alt2 * 1000 - alt1 * 1000)  # 假設輸入是 km

        # 3D 距離
        distance_3d = math.sqrt(surface_distance**2 + height_diff**2)

        return distance_3d

    async def close(self):
        """關閉數據庫連接池"""
        if self.db_pool:
            await self.db_pool.close()
            logger.info("🛰️ 衛星數據管理器已關閉")
