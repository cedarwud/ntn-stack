"""
TLE 數據服務 - 真實衛星軌道數據集成

功能：
1. 從 CelesTrak API 獲取真實 TLE 數據
2. 支持 Starlink 星座數據
3. 歷史數據緩存和管理
4. 數據驗證和清理

符合 d2.md 中 Phase 1 的要求
"""

import asyncio
import aiohttp
import json
import math
import os
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class TLEData:
    """TLE 數據結構"""

    satellite_name: str
    catalog_number: int
    epoch_year: int
    epoch_day: float
    first_derivative: float
    second_derivative: float
    drag_term: float
    inclination: float
    right_ascension: float
    eccentricity: float
    argument_of_perigee: float
    mean_anomaly: float
    mean_motion: float
    revolution_number: int
    line1: str  # 原始 TLE 第一行
    line2: str  # 原始 TLE 第二行
    last_updated: datetime
    constellation: str = "unknown"


@dataclass
class TLESource:
    """TLE 數據源配置"""

    name: str
    url: str
    constellation: str
    description: str


class TLEDataService:
    """TLE 數據服務"""

    def __init__(self):
        self.celestrak_base_url = "https://celestrak.org/NORAD/elements/gp.php"
        self.cache_dir = Path("./data/tle_cache")
        self.historical_dir = Path("./data/tle_historical")

        # 支持的 TLE 數據源
        self.tle_sources = {
            "starlink": TLESource(
                name="Starlink",
                url=f"{self.celestrak_base_url}?GROUP=starlink&FORMAT=tle",
                constellation="starlink",
                description="SpaceX Starlink constellation",
            ),
            "oneweb": TLESource(
                name="OneWeb",
                url=f"{self.celestrak_base_url}?GROUP=oneweb&FORMAT=tle",
                constellation="oneweb",
                description="OneWeb constellation",
            ),
            "gps": TLESource(
                name="GPS",
                url=f"{self.celestrak_base_url}?GROUP=gps-ops&FORMAT=tle",
                constellation="gps",
                description="GPS operational satellites",
            ),
        }

        # 初始化目錄（同步方式）
        self._initialize_directories_sync()

    def _initialize_directories_sync(self) -> None:
        """初始化緩存目錄（同步版本）"""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.historical_dir.mkdir(parents=True, exist_ok=True)
            logger.info(
                f"TLE 緩存目錄初始化完成: {self.cache_dir}, {self.historical_dir}"
            )
        except Exception as e:
            logger.error(f"TLE 緩存目錄初始化失敗: {e}")
            raise

    async def _initialize_directories(self) -> None:
        """初始化緩存目錄（異步版本）"""
        self._initialize_directories_sync()

    async def fetch_starlink_tle(self) -> List[TLEData]:
        """獲取 Starlink 星座 TLE 數據"""
        return await self.fetch_tle_from_source("starlink")

    async def fetch_tle_from_source(self, constellation: str) -> List[TLEData]:
        """獲取指定星座的 TLE 數據"""
        source = self.tle_sources.get(constellation)
        if not source:
            raise ValueError(f"不支援的星座: {constellation}")

        try:
            logger.info(f"開始獲取 {source.name} TLE 數據: {source.url}")

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    source.url,
                    timeout=aiohttp.ClientTimeout(total=30),
                    headers={"User-Agent": "NTN-Stack-Research/1.0"},
                ) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP {response.status}: {response.reason}")

                    tle_text = await response.text()

            tle_data = self._parse_tle_text(tle_text, constellation)

            # 緩存數據
            await self._cache_tle_data(constellation, tle_data)

            logger.info(f"成功獲取 {source.name} TLE 數據: {len(tle_data)} 顆衛星")
            return tle_data

        except Exception as e:
            logger.error(f"獲取 {source.name} TLE 數據失敗: {e}")

            # 嘗試從緩存讀取
            cached_data = await self._get_cached_tle_data(constellation)
            if cached_data:
                logger.warning(
                    f"使用緩存的 {source.name} TLE 數據: {len(cached_data)} 顆衛星"
                )
                return cached_data

            raise

    async def fetch_specific_satellite(self, norad_id: int) -> Optional[TLEData]:
        """獲取特定衛星的 TLE 數據"""
        try:
            url = f"{self.celestrak_base_url}?CATNR={norad_id}&FORMAT=tle"
            logger.info(f"獲取特定衛星 TLE 數據: NORAD ID {norad_id}")

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=10),
                    headers={"User-Agent": "NTN-Stack-Research/1.0"},
                ) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP {response.status}: {response.reason}")

                    tle_text = await response.text()

            if not tle_text.strip():
                logger.warning(f"未找到 NORAD ID {norad_id} 的 TLE 數據")
                return None

            tle_data = self._parse_tle_text(tle_text, "individual")
            return tle_data[0] if tle_data else None

        except Exception as e:
            logger.error(f"獲取特定衛星 TLE 數據失敗: {e}")
            return None

    def _parse_tle_text(self, tle_text: str, constellation: str) -> List[TLEData]:
        """解析 TLE 文本數據"""
        lines = [line.strip() for line in tle_text.strip().split("\n") if line.strip()]
        tle_data = []

        # TLE 格式：每3行為一組（衛星名稱 + 兩行軌道數據）
        for i in range(0, len(lines), 3):
            if i + 2 >= len(lines):
                break

            satellite_name = lines[i]
            line1 = lines[i + 1]
            line2 = lines[i + 2]

            # 驗證 TLE 格式
            if not line1.startswith("1 ") or not line2.startswith("2 "):
                logger.warning(f"無效的 TLE 格式: {satellite_name}")
                continue

            try:
                tle = self._parse_tle_lines(satellite_name, line1, line2, constellation)
                tle_data.append(tle)
            except Exception as e:
                logger.warning(f"TLE 解析失敗: {satellite_name}, {e}")

        return tle_data

    def _parse_tle_lines(
        self, satellite_name: str, line1: str, line2: str, constellation: str
    ) -> TLEData:
        """解析單個 TLE 記錄"""
        # 解析第一行
        catalog_number = int(line1[2:7])
        epoch_year = int(line1[18:20])
        epoch_day = float(line1[20:32])
        first_derivative = float(line1[33:43])
        second_derivative = self._parse_scientific_notation(line1[44:52])
        drag_term = self._parse_scientific_notation(line1[53:61])

        # 解析第二行
        inclination = float(line2[8:16])
        right_ascension = float(line2[17:25])
        eccentricity = float("0." + line2[26:33])
        argument_of_perigee = float(line2[34:42])
        mean_anomaly = float(line2[43:51])
        mean_motion = float(line2[52:63])
        revolution_number = int(line2[63:68])

        # 處理年份
        full_epoch_year = 2000 + epoch_year if epoch_year < 57 else 1900 + epoch_year

        return TLEData(
            satellite_name=satellite_name.strip(),
            catalog_number=catalog_number,
            epoch_year=full_epoch_year,
            epoch_day=epoch_day,
            first_derivative=first_derivative,
            second_derivative=second_derivative,
            drag_term=drag_term,
            inclination=inclination,
            right_ascension=right_ascension,
            eccentricity=eccentricity,
            argument_of_perigee=argument_of_perigee,
            mean_anomaly=mean_anomaly,
            mean_motion=mean_motion,
            revolution_number=revolution_number,
            line1=line1,
            line2=line2,
            last_updated=datetime.now(timezone.utc),
            constellation=constellation,
        )

    def _parse_scientific_notation(self, s: str) -> float:
        """解析科學記數法格式（TLE 特殊格式）"""
        if not s or not s.strip():
            return 0.0

        trimmed = s.strip()
        if trimmed in ["00000-0", "00000+0"]:
            return 0.0

        try:
            # TLE 格式：±.12345-6 表示 ±0.12345e-6
            sign = -1 if trimmed[0] == "-" else 1
            mantissa = float("0." + trimmed[1:6])
            exponent = int(trimmed[6:8])

            return sign * mantissa * (10**exponent)
        except (ValueError, IndexError):
            return 0.0

    async def _cache_tle_data(
        self, constellation: str, tle_data: List[TLEData]
    ) -> None:
        """緩存 TLE 數據到本地"""
        try:
            cache_file = self.cache_dir / f"{constellation}_latest.json"
            cache_data = {
                "constellation": constellation,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "satellite_count": len(tle_data),
                "data": [asdict(tle) for tle in tle_data],
            }

            # 轉換 datetime 為字符串
            for item in cache_data["data"]:
                item["last_updated"] = (
                    item["last_updated"].isoformat()
                    if isinstance(item["last_updated"], datetime)
                    else item["last_updated"]
                )

            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)

            logger.info(f"TLE 數據緩存完成: {constellation}, {len(tle_data)} 顆衛星")
        except Exception as e:
            logger.error(f"TLE 數據緩存失敗: {e}")

    async def _get_cached_tle_data(self, constellation: str) -> List[TLEData]:
        """從緩存讀取 TLE 數據"""
        try:
            cache_file = self.cache_dir / f"{constellation}_latest.json"
            if not cache_file.exists():
                return []

            with open(cache_file, "r", encoding="utf-8") as f:
                cache_data = json.load(f)

            # 檢查緩存時效性（24小時）
            cache_time = datetime.fromisoformat(
                cache_data["timestamp"].replace("Z", "+00:00")
            )
            now = datetime.now(timezone.utc)
            hours_diff = (now - cache_time).total_seconds() / 3600

            if hours_diff > 24:
                logger.warning(
                    f"緩存數據已過期: {constellation}, {hours_diff:.1f} 小時"
                )
                return []

            # 轉換回 TLEData 對象
            tle_data = []
            for item in cache_data["data"]:
                item["last_updated"] = datetime.fromisoformat(
                    item["last_updated"].replace("Z", "+00:00")
                )
                tle_data.append(TLEData(**item))

            logger.info(
                f"使用緩存的 TLE 數據: {constellation}, {len(tle_data)} 顆衛星, 緩存時間: {hours_diff:.1f} 小時"
            )
            return tle_data

        except Exception as e:
            logger.debug(f"無法讀取緩存數據: {constellation}, {e}")
            return []

    def get_supported_constellations(self) -> List[Dict[str, str]]:
        """獲取支持的星座列表"""
        return [asdict(source) for source in self.tle_sources.values()]

    def validate_tle_data(self, tle: TLEData) -> bool:
        """驗證 TLE 數據的有效性"""
        # 基本範圍檢查
        if not (0 <= tle.inclination <= 180):
            return False
        if not (0 <= tle.eccentricity < 1):
            return False
        if tle.mean_motion <= 0:
            return False
        if tle.catalog_number <= 0:
            return False

        # 檢查軌道週期是否合理（30分鐘到24小時）
        orbital_period = 1440 / tle.mean_motion  # 分鐘
        if not (30 <= orbital_period <= 1440):
            return False

        return True

    async def get_constellation_stats(self, constellation: str) -> Dict[str, Any]:
        """獲取星座統計信息"""
        try:
            # 從緩存獲取數據
            cached_data = await self._get_cached_tle_data(constellation)

            if not cached_data:
                # 如果沒有緩存，嘗試獲取新數據
                cached_data = await self.fetch_tle_from_source(constellation)

            if not cached_data:
                return {
                    "totalSatellites": 0,
                    "validSatellites": 0,
                    "lastUpdated": None,
                    "averageAltitude": 0,
                    "inclinationRange": {"min": 0, "max": 0},
                }

            valid_satellites = [
                tle for tle in cached_data if self.validate_tle_data(tle)
            ]
            inclinations = [tle.inclination for tle in valid_satellites]

            # 估算平均高度（基於平均運動）
            if valid_satellites:
                avg_mean_motion = sum(
                    tle.mean_motion for tle in valid_satellites
                ) / len(valid_satellites)
                avg_orbital_period = 1440 / avg_mean_motion  # 分鐘
                # 使用開普勒第三定律估算軌道半徑
                mu = 3.986004418e14  # m³/s²
                period_seconds = avg_orbital_period * 60
                semi_major_axis = (
                    (mu * (period_seconds / (2 * math.pi)) ** 2) ** (1 / 3)
                ) / 1000  # km
                avg_altitude = semi_major_axis - 6371  # 地球半徑
            else:
                avg_altitude = 0

            return {
                "totalSatellites": len(cached_data),
                "validSatellites": len(valid_satellites),
                "lastUpdated": (
                    cached_data[0].last_updated.isoformat() if cached_data else None
                ),
                "averageAltitude": round(avg_altitude),
                "inclinationRange": {
                    "min": min(inclinations) if inclinations else 0,
                    "max": max(inclinations) if inclinations else 0,
                },
            }
        except Exception as e:
            logger.error(f"獲取星座統計失敗: {e}")
            return {
                "totalSatellites": 0,
                "validSatellites": 0,
                "lastUpdated": None,
                "averageAltitude": 0,
                "inclinationRange": {"min": 0, "max": 0},
            }
