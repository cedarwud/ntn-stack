"""
歷史數據緩存系統 - 支持 d2.md 中指定的歷史時段數據

功能：
1. 緩存指定時間段的 TLE 數據
2. 支持 2024年1月1日 00:00:00 UTC 開始的3小時數據
3. 高效的時間索引和檢索
4. 數據壓縮和存儲優化
"""

import json
import logging
import math
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

from .tle_data_service import TLEData, TLEDataService

logger = logging.getLogger(__name__)


@dataclass
class HistoricalTLERecord:
    """歷史 TLE 記錄"""

    timestamp: datetime
    constellation: str
    satellites: List[TLEData]
    data_source: str  # 'cached', 'interpolated', 'live'
    quality: str  # 'high', 'medium', 'low'


@dataclass
class TimeRange:
    """時間範圍"""

    start: datetime
    end: datetime


@dataclass
class CacheMetadata:
    """緩存元數據"""

    time_range: TimeRange
    constellation: str
    total_records: int
    sample_interval: int  # 分鐘
    created_at: datetime
    last_accessed: datetime
    file_size: int


class HistoricalDataCache:
    """歷史數據緩存系統"""

    # d2.md 中推薦的歷史數據時段
    RECOMMENDED_TIME_RANGES = {
        "primary": {
            "start": datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            "end": datetime(2024, 1, 1, 3, 0, 0, tzinfo=timezone.utc),
            "description": "主要時段 - 包含完整的 LEO 衛星軌道週期",
        },
        "backup1": {
            "start": datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
            "end": datetime(2024, 1, 15, 15, 0, 0, tzinfo=timezone.utc),
            "description": "備選時段1 - 太陽最大活動期",
        },
        "backup2": {
            "start": datetime(2024, 2, 1, 6, 0, 0, tzinfo=timezone.utc),
            "end": datetime(2024, 2, 1, 9, 0, 0, tzinfo=timezone.utc),
            "description": "備選時段2 - 地磁暴期間",
        },
        "backup3": {
            "start": datetime(2024, 3, 21, 18, 0, 0, tzinfo=timezone.utc),
            "end": datetime(2024, 3, 21, 21, 0, 0, tzinfo=timezone.utc),
            "description": "備選時段3 - 春分點，最佳幾何條件",
        },
    }

    def __init__(self, tle_service: Optional[TLEDataService] = None):
        self.cache_dir = Path("./data/tle_cache")
        self.historical_dir = Path("./data/tle_historical")
        self.metadata_dir = self.historical_dir / "metadata"
        self.tle_service = tle_service or TLEDataService()

        # 初始化目錄
        self._initialize_directories()

    def _initialize_directories(self) -> None:
        """初始化緩存目錄"""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.historical_dir.mkdir(parents=True, exist_ok=True)
            self.metadata_dir.mkdir(parents=True, exist_ok=True)

            logger.info(f"歷史數據緩存目錄初始化完成: {self.historical_dir}")
        except Exception as e:
            logger.error(f"歷史數據緩存目錄初始化失敗: {e}")
            raise

    async def cache_historical_tle(
        self,
        constellation: str,
        time_range: TimeRange,
        sample_interval_minutes: int = 10,
    ) -> None:
        """緩存指定時間段的歷史 TLE 數據"""
        try:
            logger.info(
                f"開始緩存歷史 TLE 數據: {constellation}, {time_range.start} - {time_range.end}"
            )

            records = []
            current = time_range.start
            interval_delta = timedelta(minutes=sample_interval_minutes)

            # 獲取基準 TLE 數據
            base_tle = await self.tle_service.fetch_tle_from_source(constellation)
            if not base_tle:
                raise ValueError(f"無法獲取 {constellation} 星座的 TLE 數據")

            while current <= time_range.end:
                # 生成歷史數據（基於時間的軌道演化）
                historical_tle = self._generate_historical_tle(base_tle, current)

                records.append(
                    HistoricalTLERecord(
                        timestamp=current,
                        constellation=constellation,
                        satellites=historical_tle,
                        data_source="interpolated",
                        quality="medium",
                    )
                )

                current += interval_delta

            # 保存到文件
            await self._save_historical_records(
                constellation, time_range, records, sample_interval_minutes
            )

            logger.info(
                f"歷史 TLE 數據緩存完成: {constellation}, {len(records)} 條記錄"
            )

        except Exception as e:
            logger.error(f"歷史 TLE 數據緩存失敗: {e}")
            raise

    async def get_historical_tle(
        self, constellation: str, timestamp: datetime
    ) -> Optional[HistoricalTLERecord]:
        """獲取特定時間點的歷史 TLE 數據"""
        try:
            cache_files = await self._find_cache_files_for_time(
                constellation, timestamp
            )

            for cache_file in cache_files:
                records = await self._load_historical_records(cache_file)

                closest_record = self._find_closest_record(records, timestamp)
                if closest_record:
                    await self._update_access_time(cache_file)
                    return closest_record

            logger.warning(
                f"未找到指定時間的歷史 TLE 數據: {constellation}, {timestamp}"
            )
            return None

        except Exception as e:
            logger.error(f"獲取歷史 TLE 數據失敗: {e}")
            return None

    async def get_historical_tle_range(
        self, constellation: str, time_range: TimeRange, max_records: int = 1000
    ) -> List[HistoricalTLERecord]:
        """獲取時間範圍內的歷史 TLE 數據"""
        try:
            cache_files = await self._find_cache_files_for_time_range(
                constellation, time_range
            )
            all_records = []

            for cache_file in cache_files:
                records = await self._load_historical_records(cache_file)

                # 過濾時間範圍內的記錄
                filtered_records = [
                    record
                    for record in records
                    if time_range.start <= record.timestamp <= time_range.end
                ]

                all_records.extend(filtered_records)

            # 按時間排序並限制數量
            all_records.sort(key=lambda x: x.timestamp)
            result = all_records[:max_records]

            logger.info(f"獲取歷史 TLE 數據範圍: {constellation}, {len(result)} 條記錄")
            return result

        except Exception as e:
            logger.error(f"獲取歷史 TLE 數據範圍失敗: {e}")
            return []

    def _generate_historical_tle(
        self, base_tle: List[TLEData], timestamp: datetime
    ) -> List[TLEData]:
        """生成基於時間的歷史 TLE 數據（模擬軌道演化）"""
        now = datetime.now(timezone.utc)
        time_diff_hours = (timestamp - now).total_seconds() / 3600

        historical_tle = []
        for tle in base_tle:
            # 簡單的軌道演化模擬
            # 在實際應用中，這裡應該使用 SGP4 算法進行精確計算
            mean_anomaly_change = (tle.mean_motion * time_diff_hours * 360 / 24) % 360
            new_mean_anomaly = (tle.mean_anomaly + mean_anomaly_change + 360) % 360

            # 考慮軌道衰減（大氣阻力）
            altitude_decay = abs(time_diff_hours) * 0.001  # 每小時約1米的衰減
            mean_motion_increase = (
                altitude_decay * 0.000001
            )  # 軌道衰減導致的平均運動增加

            # 創建新的 TLE 數據
            new_tle = TLEData(
                satellite_name=tle.satellite_name,
                catalog_number=tle.catalog_number,
                epoch_year=tle.epoch_year,
                epoch_day=tle.epoch_day + time_diff_hours / 24,
                first_derivative=tle.first_derivative,
                second_derivative=tle.second_derivative,
                drag_term=tle.drag_term,
                inclination=tle.inclination,
                right_ascension=tle.right_ascension,
                eccentricity=tle.eccentricity,
                argument_of_perigee=tle.argument_of_perigee,
                mean_anomaly=new_mean_anomaly,
                mean_motion=tle.mean_motion + mean_motion_increase,
                revolution_number=tle.revolution_number,
                line1=tle.line1,
                line2=tle.line2,
                last_updated=timestamp,
                constellation=tle.constellation,
            )

            historical_tle.append(new_tle)

        return historical_tle

    async def _save_historical_records(
        self,
        constellation: str,
        time_range: TimeRange,
        records: List[HistoricalTLERecord],
        sample_interval: int,
    ) -> None:
        """保存歷史記錄到文件"""
        filename = self._generate_cache_filename(constellation, time_range)
        filepath = self.historical_dir / filename

        # 準備數據進行序列化
        serializable_records = []
        for record in records:
            serializable_record = {
                "timestamp": record.timestamp.isoformat(),
                "constellation": record.constellation,
                "satellites": [asdict(sat) for sat in record.satellites],
                "data_source": record.data_source,
                "quality": record.quality,
            }

            # 轉換衛星數據中的 datetime
            for sat in serializable_record["satellites"]:
                if isinstance(sat["last_updated"], datetime):
                    sat["last_updated"] = sat["last_updated"].isoformat()

            serializable_records.append(serializable_record)

        # 保存數據
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(serializable_records, f, indent=2, ensure_ascii=False)

        # 保存元數據
        metadata = CacheMetadata(
            time_range=time_range,
            constellation=constellation,
            total_records=len(records),
            sample_interval=sample_interval,
            created_at=datetime.now(timezone.utc),
            last_accessed=datetime.now(timezone.utc),
            file_size=filepath.stat().st_size,
        )

        metadata_dict = {
            "time_range": {
                "start": metadata.time_range.start.isoformat(),
                "end": metadata.time_range.end.isoformat(),
            },
            "constellation": metadata.constellation,
            "total_records": metadata.total_records,
            "sample_interval": metadata.sample_interval,
            "created_at": metadata.created_at.isoformat(),
            "last_accessed": metadata.last_accessed.isoformat(),
            "file_size": metadata.file_size,
        }

        metadata_path = self.metadata_dir / f"{filename}.meta"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata_dict, f, indent=2, ensure_ascii=False)

    def _generate_cache_filename(
        self, constellation: str, time_range: TimeRange
    ) -> str:
        """生成緩存文件名"""
        start_str = time_range.start.isoformat().replace(":", "-").replace(".", "-")
        end_str = time_range.end.isoformat().replace(":", "-").replace(".", "-")
        return f"{constellation}_{start_str}_{end_str}.json"

    async def _find_cache_files_for_time(
        self, constellation: str, timestamp: datetime
    ) -> List[Path]:
        """查找包含指定時間的緩存文件"""
        try:
            matching_files = []

            for meta_file in self.metadata_dir.glob(f"{constellation}_*.meta"):
                with open(meta_file, "r", encoding="utf-8") as f:
                    metadata = json.load(f)

                start_time = datetime.fromisoformat(
                    metadata["time_range"]["start"].replace("Z", "+00:00")
                )
                end_time = datetime.fromisoformat(
                    metadata["time_range"]["end"].replace("Z", "+00:00")
                )

                if start_time <= timestamp <= end_time:
                    data_file = self.historical_dir / meta_file.name.replace(
                        ".meta", ""
                    )
                    matching_files.append(data_file)

            return matching_files
        except Exception as e:
            logger.error(f"查找緩存文件失敗: {e}")
            return []

    async def _find_cache_files_for_time_range(
        self, constellation: str, time_range: TimeRange
    ) -> List[Path]:
        """查找時間範圍內的緩存文件"""
        try:
            matching_files = []

            for meta_file in self.metadata_dir.glob(f"{constellation}_*.meta"):
                with open(meta_file, "r", encoding="utf-8") as f:
                    metadata = json.load(f)

                meta_start = datetime.fromisoformat(
                    metadata["time_range"]["start"].replace("Z", "+00:00")
                )
                meta_end = datetime.fromisoformat(
                    metadata["time_range"]["end"].replace("Z", "+00:00")
                )

                # 檢查時間範圍是否有重疊
                if meta_start <= time_range.end and meta_end >= time_range.start:
                    data_file = self.historical_dir / meta_file.name.replace(
                        ".meta", ""
                    )
                    matching_files.append(data_file)

            return matching_files
        except Exception as e:
            logger.error(f"查找時間範圍緩存文件失敗: {e}")
            return []

    async def _load_historical_records(
        self, filepath: Path
    ) -> List[HistoricalTLERecord]:
        """載入歷史記錄"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            records = []
            for record_data in data:
                # 轉換時間戳
                timestamp = datetime.fromisoformat(
                    record_data["timestamp"].replace("Z", "+00:00")
                )

                # 轉換衛星數據
                satellites = []
                for sat_data in record_data["satellites"]:
                    sat_data["last_updated"] = datetime.fromisoformat(
                        sat_data["last_updated"].replace("Z", "+00:00")
                    )
                    satellites.append(TLEData(**sat_data))

                record = HistoricalTLERecord(
                    timestamp=timestamp,
                    constellation=record_data["constellation"],
                    satellites=satellites,
                    data_source=record_data["data_source"],
                    quality=record_data["quality"],
                )
                records.append(record)

            return records
        except Exception as e:
            logger.error(f"載入歷史記錄失敗: {e}")
            return []

    def _find_closest_record(
        self, records: List[HistoricalTLERecord], timestamp: datetime
    ) -> Optional[HistoricalTLERecord]:
        """找到最接近指定時間的記錄"""
        if not records:
            return None

        closest = records[0]
        min_diff = abs((records[0].timestamp - timestamp).total_seconds())

        for record in records:
            diff = abs((record.timestamp - timestamp).total_seconds())
            if diff < min_diff:
                min_diff = diff
                closest = record

        return closest

    async def _update_access_time(self, filepath: Path) -> None:
        """更新文件訪問時間"""
        try:
            meta_path = self.metadata_dir / f"{filepath.name}.meta"

            with open(meta_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            metadata["last_accessed"] = datetime.now(timezone.utc).isoformat()

            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.debug(f"更新訪問時間失敗: {e}")

    async def cleanup_expired_cache(self, max_age_hours: int = 168) -> None:
        """清理過期的緩存文件"""
        try:
            now = datetime.now(timezone.utc)
            cleaned_count = 0

            for meta_file in self.metadata_dir.glob("*.meta"):
                with open(meta_file, "r", encoding="utf-8") as f:
                    metadata = json.load(f)

                last_accessed = datetime.fromisoformat(
                    metadata["last_accessed"].replace("Z", "+00:00")
                )
                age_hours = (now - last_accessed).total_seconds() / 3600

                if age_hours > max_age_hours:
                    # 刪除數據文件和元數據文件
                    data_file = self.historical_dir / meta_file.name.replace(
                        ".meta", ""
                    )

                    try:
                        if data_file.exists():
                            data_file.unlink()
                        meta_file.unlink()
                        cleaned_count += 1
                    except Exception as e:
                        logger.warning(f"刪除過期緩存文件失敗: {e}")

            logger.info(f"緩存清理完成: 清理了 {cleaned_count} 個文件")
        except Exception as e:
            logger.error(f"緩存清理失敗: {e}")

    async def get_cache_stats(self) -> Dict[str, Any]:
        """獲取緩存統計信息"""
        try:
            total_files = 0
            total_size = 0
            constellations = set()
            oldest_cache = None
            newest_cache = None

            for meta_file in self.metadata_dir.glob("*.meta"):
                with open(meta_file, "r", encoding="utf-8") as f:
                    metadata = json.load(f)

                total_files += 1
                total_size += metadata["file_size"]
                constellations.add(metadata["constellation"])

                created_at = datetime.fromisoformat(
                    metadata["created_at"].replace("Z", "+00:00")
                )
                if oldest_cache is None or created_at < oldest_cache:
                    oldest_cache = created_at
                if newest_cache is None or created_at > newest_cache:
                    newest_cache = created_at

            return {
                "total_files": total_files,
                "total_size": total_size,
                "constellations": list(constellations),
                "oldest_cache": oldest_cache.isoformat() if oldest_cache else None,
                "newest_cache": newest_cache.isoformat() if newest_cache else None,
            }
        except Exception as e:
            logger.error(f"獲取緩存統計失敗: {e}")
            return {
                "total_files": 0,
                "total_size": 0,
                "constellations": [],
                "oldest_cache": None,
                "newest_cache": None,
            }

    async def preload_recommended_time_ranges(
        self, constellation: str = "starlink"
    ) -> None:
        """預載推薦時段的歷史數據"""
        logger.info(f"開始預載推薦時段的歷史數據: {constellation}")

        for key, time_range_data in self.RECOMMENDED_TIME_RANGES.items():
            try:
                time_range = TimeRange(
                    start=time_range_data["start"], end=time_range_data["end"]
                )

                await self.cache_historical_tle(
                    constellation, time_range, 10
                )  # 10分鐘間隔
                logger.info(f"預載完成: {time_range_data['description']}")
            except Exception as e:
                logger.error(f"預載失敗: {time_range_data['description']}, {e}")

        logger.info(f"推薦時段歷史數據預載完成: {constellation}")
