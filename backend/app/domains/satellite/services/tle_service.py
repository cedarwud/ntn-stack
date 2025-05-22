import logging
import aiohttp
import asyncio
import json
from typing import List, Dict, Any, Optional, Set, Callable
from datetime import datetime, timedelta
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

import sgp4.api as sgp4
from sgp4.earth_gravity import wgs72
from sgp4.io import twoline2rv

from app.domains.satellite.interfaces.tle_service_interface import TLEServiceInterface
from app.domains.satellite.interfaces.satellite_repository import (
    SatelliteRepositoryInterface,
)
from app.domains.satellite.adapters.sqlmodel_satellite_repository import (
    SQLModelSatelliteRepository,
)

logger = logging.getLogger(__name__)


# 定義同步 OneWeb TLE 數據的函數
async def synchronize_oneweb_tles(
    session_factory: Callable[..., AsyncSession], redis_client: Redis
) -> bool:
    """同步 OneWeb 衛星的 TLE 數據

    Args:
        session_factory: 獲取資料庫會話的工廠函數
        redis_client: Redis 客戶端

    Returns:
        bool: 同步是否成功
    """
    try:
        logger.info("開始同步 OneWeb 衛星 TLE 數據...")

        # 創建 TLE 服務和衛星儲存庫
        satellite_repo = SQLModelSatelliteRepository(session_factory)
        tle_service = TLEService(satellite_repo)

        # 嘗試獲取 OneWeb 衛星的 TLE 數據
        tle_data = await tle_service.fetch_tle_from_celestrak(
            "starlink"
        )  # 暫時用 starlink 代替，實際應該單獨獲取 OneWeb

        if not tle_data:
            logger.warning("未獲取到 OneWeb 衛星 TLE 數據")
            return False

        # 將 TLE 數據存入 Redis
        tle_json = json.dumps(tle_data)
        await redis_client.set("oneweb_tle_data", tle_json)
        await redis_client.set("oneweb_tle_last_update", datetime.utcnow().isoformat())

        logger.info(f"成功同步 {len(tle_data)} 個 OneWeb 衛星 TLE 數據")
        return True

    except Exception as e:
        logger.error(f"同步 OneWeb 衛星 TLE 數據時出錯: {e}", exc_info=True)
        return False


class TLEService(TLEServiceInterface):
    """TLE 服務實現"""

    def __init__(
        self, satellite_repository: Optional[SatelliteRepositoryInterface] = None
    ):
        self._satellite_repository = (
            satellite_repository or SQLModelSatelliteRepository()
        )

        # Celestrak API URL
        self._celestrak_base_url = "https://celestrak.org/NORAD/elements/gp.php"
        self._celestrak_categories = {
            "stations": "stations",
            "weather": "weather",
            "noaa": "noaa",
            "goes": "goes",
            "galileo": "galileo",
            "geo": "geo",
            "gps": "gps",
            "active": "active",
            "starlink": "starlink",
        }

        # Space-Track API 配置
        # 注意：實際應用中，這些應該從配置文件或環境變量讀取
        self._spacetrack_base_url = "https://www.space-track.org"
        self._spacetrack_auth_url = f"{self._spacetrack_base_url}/ajaxauth/login"
        self._spacetrack_tle_url = (
            f"{self._spacetrack_base_url}/basicspacedata/query/class/tle_latest"
        )
        self._spacetrack_username = None  # 應從環境變量讀取
        self._spacetrack_password = None  # 應從環境變量讀取

    async def fetch_tle_from_celestrak(
        self, category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """從 Celestrak 獲取 TLE 數據"""
        results = []

        # 將 category 轉換為小寫
        if category:
            category = category.lower()

        # 如果提供了類別且該類別不在支援的類別中，則返回空列表
        if category and category not in self._celestrak_categories:
            logger.warning(f"不支援的 Celestrak 類別: {category}")
            return []

        # 決定要請求的類別
        categories_to_fetch = (
            [category] if category else list(self._celestrak_categories.values())
        )

        for cat in categories_to_fetch:
            try:
                url = f"{self._celestrak_base_url}?GROUP={cat}&FORMAT=TLE"

                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            text = await response.text()
                            parsed_tle = self._parse_tle_text(text)
                            results.extend(parsed_tle)
                            logger.info(
                                f"從 Celestrak 獲取了 {len(parsed_tle)} 條 {cat} 類別的 TLE 數據"
                            )
                        else:
                            logger.error(
                                f"從 Celestrak 獲取 {cat} 類別的 TLE 數據失敗: {response.status}"
                            )
            except Exception as e:
                logger.error(f"從 Celestrak 獲取 {cat} 類別的 TLE 數據出錯: {e}")

        return results

    async def fetch_tle_from_spacetrack(
        self, norad_id_list: Optional[List[str]] = None, days: int = 30
    ) -> List[Dict[str, Any]]:
        """從 Space-Track 獲取 TLE 數據"""
        # 如果沒有設置 Space-Track 憑證，則退出
        if not self._spacetrack_username or not self._spacetrack_password:
            logger.error("未設置 Space-Track 憑證")
            return []

        results = []

        try:
            # 計算查詢日期範圍
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            # 格式化日期字符串
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")

            # 構建查詢參數
            params = {
                "predicates": "OBJECT_NAME,NORAD_CAT_ID,TLE_LINE1,TLE_LINE2",
                "orderby": "NORAD_CAT_ID asc",
                "format": "json",
                "epoch": f">={start_str},{end_str}",
            }

            # 如果提供了 NORAD ID 列表，則添加到查詢中
            if norad_id_list:
                norad_list_str = ",".join(norad_id_list)
                params["NORAD_CAT_ID"] = norad_list_str

            # 登錄 Space-Track
            async with aiohttp.ClientSession() as session:
                auth_data = {
                    "identity": self._spacetrack_username,
                    "password": self._spacetrack_password,
                }

                async with session.post(
                    self._spacetrack_auth_url, data=auth_data
                ) as auth_response:
                    if auth_response.status != 200:
                        logger.error(f"Space-Track 登錄失敗: {auth_response.status}")
                        return []

                # 獲取 TLE 數據
                async with session.get(
                    self._spacetrack_tle_url, params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()

                        # 將數據轉換為標準格式
                        for entry in data:
                            tle_data = {
                                "name": entry["OBJECT_NAME"].strip(),
                                "norad_id": entry["NORAD_CAT_ID"].strip(),
                                "line1": entry["TLE_LINE1"].strip(),
                                "line2": entry["TLE_LINE2"].strip(),
                            }

                            if await self.validate_tle(
                                tle_data["line1"], tle_data["line2"]
                            ):
                                results.append(tle_data)

                        logger.info(f"從 Space-Track 獲取了 {len(results)} 條 TLE 數據")
                    else:
                        logger.error(
                            f"從 Space-Track 獲取 TLE 數據失敗: {response.status}"
                        )
        except Exception as e:
            logger.error(f"從 Space-Track 獲取 TLE 數據出錯: {e}")

        return results

    async def _parse_tle_text(self, tle_text: str) -> List[Dict[str, Any]]:
        """解析 TLE 格式的文本，返回 TLE 數據列表"""
        results = []
        lines = tle_text.strip().split("\n")

        i = 0
        while i < len(lines):
            try:
                # 按 3 行一組處理 (名稱、第一行、第二行)
                if i + 2 < len(lines):
                    name = lines[i].strip()
                    line1 = lines[i + 1].strip()
                    line2 = lines[i + 2].strip()

                    # 檢查格式有效性
                    if (
                        line1.startswith("1 ")
                        and line2.startswith("2 ")
                        and await self.validate_tle(line1, line2)
                    ):
                        # 提取 NORAD ID
                        try:
                            norad_id = line1.split()[1].strip()

                            tle_data = {
                                "name": name,
                                "norad_id": norad_id,
                                "line1": line1,
                                "line2": line2,
                            }

                            results.append(tle_data)
                        except IndexError:
                            logger.warning(f"無法從 TLE 行提取 NORAD ID: {line1}")

                    i += 3
                else:
                    break
            except Exception as e:
                logger.error(f"解析 TLE 數據時出錯: {e}")
                i += 1

        return results

    async def update_satellite_tle(self, norad_id: str) -> bool:
        """更新指定衛星的 TLE 數據"""
        try:
            # 嘗試從 Space-Track 獲取最新的 TLE
            tle_data = await self.fetch_tle_from_spacetrack([norad_id])

            # 如果找不到，嘗試從 Celestrak 獲取
            if not tle_data:
                all_celestrak_tle = await self.fetch_tle_from_celestrak()
                tle_data = [
                    tle for tle in all_celestrak_tle if tle["norad_id"] == norad_id
                ]

            # 如果仍找不到，返回失敗
            if not tle_data:
                logger.warning(f"找不到 NORAD ID 為 {norad_id} 的 TLE 數據")
                return False

            # 獲取該衛星在資料庫中的記錄
            satellite = await self._satellite_repository.get_satellite_by_norad_id(
                norad_id
            )

            # 如果衛星不存在，創建新記錄
            if not satellite:
                tle = tle_data[0]
                satellite_data = {
                    "name": tle["name"],
                    "norad_id": tle["norad_id"],
                    "tle_data": {"line1": tle["line1"], "line2": tle["line2"]},
                }
                await self._satellite_repository.create_satellite(satellite_data)
                logger.info(f"創建了新衛星記錄: {tle['name']}")
                return True

            # 更新現有衛星的 TLE 數據
            tle = tle_data[0]
            update_data = {
                "tle_data": {"line1": tle["line1"], "line2": tle["line2"]},
                "last_updated": datetime.utcnow(),
            }

            # 將 TLE 數據解析為軌道參數並更新
            try:
                orbit_params = await self.parse_tle(tle["line1"], tle["line2"])
                update_data.update(orbit_params)
            except Exception as e:
                logger.warning(f"解析 TLE 參數時出錯: {e}")

            # 更新資料庫
            updated = await self._satellite_repository.update_tle_data(
                satellite.id, update_data
            )

            return updated is not None
        except Exception as e:
            logger.error(f"更新衛星 TLE 數據時出錯: {e}")
            return False

    async def update_all_tles(self) -> Dict[str, Any]:
        """更新所有衛星的 TLE 數據"""
        # 獲取所有衛星
        satellites = await self._satellite_repository.get_satellites()

        # 收集所有 NORAD ID
        norad_ids = [satellite.norad_id for satellite in satellites]

        # 追蹤結果
        results = {
            "total": len(norad_ids),
            "updated": 0,
            "failed": 0,
            "added": 0,
            "details": [],
        }

        # 從 Celestrak 獲取所有 TLE 數據
        celestrak_tle_data = await self.fetch_tle_from_celestrak()

        # 創建 NORAD ID 到 TLE 數據的映射
        tle_map = {tle["norad_id"]: tle for tle in celestrak_tle_data}

        # 找出現有衛星
        existing_norad_ids = set(norad_ids)

        # 更新現有衛星
        for satellite in satellites:
            norad_id = satellite.norad_id

            # 檢查是否有此衛星的 TLE 數據
            if norad_id in tle_map:
                try:
                    tle = tle_map[norad_id]
                    update_data = {
                        "tle_data": {"line1": tle["line1"], "line2": tle["line2"]},
                        "last_updated": datetime.utcnow(),
                    }

                    # 將 TLE 數據解析為軌道參數並更新
                    try:
                        orbit_params = await self.parse_tle(tle["line1"], tle["line2"])
                        update_data.update(orbit_params)
                    except Exception as e:
                        logger.warning(
                            f"解析 TLE 參數時出錯: {e}, NORAD ID: {norad_id}"
                        )

                    # 更新資料庫
                    updated = await self._satellite_repository.update_tle_data(
                        satellite.id, update_data
                    )

                    if updated:
                        results["updated"] += 1
                        results["details"].append(
                            {
                                "norad_id": norad_id,
                                "name": satellite.name,
                                "status": "updated",
                            }
                        )
                    else:
                        results["failed"] += 1
                        results["details"].append(
                            {
                                "norad_id": norad_id,
                                "name": satellite.name,
                                "status": "failed",
                                "reason": "database_error",
                            }
                        )
                except Exception as e:
                    results["failed"] += 1
                    results["details"].append(
                        {
                            "norad_id": norad_id,
                            "name": satellite.name,
                            "status": "failed",
                            "reason": str(e),
                        }
                    )

        return results

    async def validate_tle(self, line1: str, line2: str) -> bool:
        """驗證 TLE 數據的有效性"""
        try:
            # 使用 SGP4 檢查 TLE 數據格式
            satellite = twoline2rv(line1, line2, wgs72)

            # 嘗試計算位置，檢查是否正確
            position, _ = satellite.propagate(0.0, 0.0, 0.0)

            # 如果返回位置是 (None, None, None)，則 TLE 數據無效
            if position == (None, None, None):
                return False

            return True
        except Exception as e:
            logger.warning(f"TLE 驗證失敗: {e}")
            return False

    async def parse_tle(self, line1: str, line2: str) -> Dict[str, Any]:
        """解析 TLE 數據，返回衛星參數"""
        try:
            # 使用 SGP4 解析 TLE 數據
            satellite = twoline2rv(line1, line2, wgs72)

            # 從 TLE 獲取各種軌道參數
            result = {
                "inclination_deg": satellite.inclo * 180.0 / sgp4.pi,  # 軌道傾角（度）
                "period_minutes": 2
                * sgp4.pi
                / (satellite.no_kozai * 60),  # 軌道周期（分鐘）
                "apogee_km": (satellite.alta + 1.0) * 6378.137,  # 遠地點高度（公里）
                "perigee_km": (satellite.altp + 1.0) * 6378.137,  # 近地點高度（公里）
            }

            # 添加國際指定符（如果有）
            intl_designator = line1[9:17].strip()
            if intl_designator:
                result["international_designator"] = intl_designator

            # 嘗試解析發射日期
            try:
                year = int(intl_designator[:2])
                # 處理年份跨世紀問題
                if year < 57:  # Sputnik 1 於 1957 年發射
                    year += 2000
                else:
                    year += 1900

                day_of_year = int(intl_designator[2:5])
                result["launch_date"] = datetime(year, 1, 1) + timedelta(
                    days=day_of_year - 1
                )
            except Exception:
                pass  # 忽略日期解析錯誤

            return result
        except Exception as e:
            logger.warning(f"解析 TLE 數據時出錯: {e}")
            raise ValueError(f"無法解析 TLE 數據: {e}")
