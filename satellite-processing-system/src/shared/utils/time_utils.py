"""
時間處理工具

整合來源：
- 各Stage中的時間處理邏輯
- TLE時間解析功能
- 軌道計算時間基準處理
"""

import math
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Union, List
import calendar


logger = logging.getLogger(__name__)


class TimeUtils:
    """時間處理工具類"""

    @staticmethod
    def parse_tle_epoch(tle_epoch_year: int, tle_epoch_day: float) -> datetime:
        """
        解析TLE時間格式為標準datetime

        Args:
            tle_epoch_year: TLE年份 (2位數或4位數)
            tle_epoch_day: TLE年內天數 (包含小數部分)

        Returns:
            標準UTC時間
        """
        try:
            # 處理2位數年份
            if tle_epoch_year < 50:
                full_year = 2000 + tle_epoch_year
            elif tle_epoch_year < 100:
                full_year = 1900 + tle_epoch_year
            else:
                full_year = tle_epoch_year

            # 計算年初時間
            year_start = datetime(full_year, 1, 1, tzinfo=timezone.utc)

            # 加上天數差值 (注意：TLE的天數從1開始)
            days_offset = tle_epoch_day - 1.0
            epoch_time = year_start + timedelta(days=days_offset)

            return epoch_time

        except Exception as e:
            logger.error(f"TLE時間解析失敗: year={tle_epoch_year}, day={tle_epoch_day}, error={e}")
            return datetime.now(timezone.utc)

    @staticmethod
    def datetime_to_tle_epoch(dt: datetime) -> Dict[str, float]:
        """
        將datetime轉換為TLE時間格式

        Args:
            dt: 標準datetime對象

        Returns:
            包含year和day的字典
        """
        try:
            # 確保時區為UTC
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            elif dt.tzinfo != timezone.utc:
                dt = dt.astimezone(timezone.utc)

            year = dt.year
            year_start = datetime(year, 1, 1, tzinfo=timezone.utc)

            # 計算年內天數 (從1開始)
            time_diff = dt - year_start
            day_of_year = time_diff.total_seconds() / 86400.0 + 1.0

            return {
                'year': year % 100,  # TLE使用2位數年份
                'day': day_of_year
            }

        except Exception as e:
            logger.error(f"datetime轉TLE格式失敗: {e}")
            return {'year': 0, 'day': 1.0}

    @staticmethod
    def get_time_since_epoch(current_time: datetime, epoch_time: datetime) -> float:
        """
        計算從歷元時間的秒數差

        Args:
            current_time: 當前時間
            epoch_time: 歷元時間

        Returns:
            時間差（秒）
        """
        try:
            # 確保時區一致
            if current_time.tzinfo is None:
                current_time = current_time.replace(tzinfo=timezone.utc)
            if epoch_time.tzinfo is None:
                epoch_time = epoch_time.replace(tzinfo=timezone.utc)

            time_diff = current_time - epoch_time
            return time_diff.total_seconds()

        except Exception as e:
            logger.error(f"時間差計算失敗: {e}")
            return 0.0

    @staticmethod
    def format_duration(seconds: float) -> str:
        """
        格式化時間長度為可讀字符串

        Args:
            seconds: 秒數

        Returns:
            格式化的時間字符串
        """
        try:
            if seconds < 60:
                return f"{seconds:.1f}秒"
            elif seconds < 3600:
                minutes = seconds / 60
                return f"{minutes:.1f}分鐘"
            elif seconds < 86400:
                hours = seconds / 3600
                return f"{hours:.1f}小時"
            else:
                days = seconds / 86400
                return f"{days:.1f}天"

        except Exception:
            return "未知時長"

    @staticmethod
    def create_time_series(start_time: datetime, end_time: datetime, step_minutes: int) -> List[datetime]:
        """
        創建時間序列

        Args:
            start_time: 開始時間
            end_time: 結束時間
            step_minutes: 時間步長(分鐘)

        Returns:
            時間點列表
        """
        time_series = []
        current_time = start_time
        step_delta = timedelta(minutes=step_minutes)

        while current_time <= end_time:
            time_series.append(current_time)
            current_time += step_delta

        return time_series

    @staticmethod
    def generate_time_series(start_time: datetime, end_time: datetime, step_minutes: int = 5) -> List[datetime]:
        """
        生成時間序列 (別名方法)

        Args:
            start_time: 開始時間
            end_time: 結束時間
            step_minutes: 時間步長(分鐘)

        Returns:
            時間點列表
        """
        return TimeUtils.create_time_series(start_time, end_time, step_minutes)

    @staticmethod
    def validate_time_range(start_time: datetime, end_time: datetime, max_duration_hours: int = 48) -> Dict[str, Any]:
        """
        驗證時間範圍的合理性

        Args:
            start_time: 開始時間
            end_time: 結束時間
            max_duration_hours: 最大允許時長（小時）

        Returns:
            驗證結果
        """
        result = {
            'valid': True,
            'errors': [],
            'duration_hours': 0.0
        }

        try:
            if start_time >= end_time:
                result['valid'] = False
                result['errors'].append('開始時間必須早於結束時間')

            duration = end_time - start_time
            duration_hours = duration.total_seconds() / 3600

            result['duration_hours'] = duration_hours

            if duration_hours > max_duration_hours:
                result['valid'] = False
                result['errors'].append(f'時間範圍過長: {duration_hours:.1f}小時 > {max_duration_hours}小時')

            if duration_hours < 0.1:
                result['valid'] = False
                result['errors'].append('時間範圍過短')

        except Exception as e:
            result['valid'] = False
            result['errors'].append(f'時間驗證錯誤: {str(e)}')

        return result

    @staticmethod
    def get_time_window_overlap(window1: Dict[str, datetime], window2: Dict[str, datetime]) -> Optional[Dict[str, datetime]]:
        """
        計算兩個時間窗口的重疊部分

        Args:
            window1: 時間窗口1 {'start': datetime, 'end': datetime}
            window2: 時間窗口2 {'start': datetime, 'end': datetime}

        Returns:
            重疊時間窗口，如果沒有重疊則返回None
        """
        try:
            start1, end1 = window1['start'], window1['end']
            start2, end2 = window2['start'], window2['end']

            # 計算重疊部分
            overlap_start = max(start1, start2)
            overlap_end = min(end1, end2)

            if overlap_start < overlap_end:
                return {
                    'start': overlap_start,
                    'end': overlap_end,
                    'duration_seconds': (overlap_end - overlap_start).total_seconds()
                }
            else:
                return None

        except Exception as e:
            logger.error(f"時間窗口重疊計算失敗: {e}")
            return None

    @staticmethod
    def round_to_nearest_minute(dt: datetime) -> datetime:
        """
        將時間四捨五入到最近的分鐘

        Args:
            dt: 輸入時間

        Returns:
            四捨五入後的時間
        """
        try:
            # 如果秒數大於等於30，則進位到下一分鐘
            if dt.second >= 30:
                dt = dt.replace(second=0, microsecond=0) + timedelta(minutes=1)
            else:
                dt = dt.replace(second=0, microsecond=0)

            return dt

        except Exception as e:
            logger.error(f"時間四捨五入失敗: {e}")
            return dt

    @staticmethod
    def get_utc_timestamp() -> float:
        """
        獲取當前UTC時間戳

        Returns:
            UTC時間戳（秒）
        """
        return datetime.now(timezone.utc).timestamp()

    @staticmethod
    def timestamp_to_datetime(timestamp: float) -> datetime:
        """
        將時間戳轉換為UTC datetime

        Args:
            timestamp: 時間戳（秒）

        Returns:
            UTC datetime
        """
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)

    @staticmethod
    def is_time_within_window(check_time: datetime, window_start: datetime, window_end: datetime) -> bool:
        """
        檢查時間是否在指定窗口內

        Args:
            check_time: 要檢查的時間
            window_start: 窗口開始時間
            window_end: 窗口結束時間

        Returns:
            是否在窗口內
        """
        try:
            return window_start <= check_time <= window_end
        except Exception:
            return False

    @staticmethod
    def get_time_zone_offset(dt: datetime) -> timedelta:
        """
        獲取時間的時區偏移

        Args:
            dt: 時間對象

        Returns:
            時區偏移量
        """
        if dt.tzinfo is None:
            return timedelta(0)
        return dt.utcoffset() or timedelta(0)


# 便捷函數
def parse_tle_time(year: int, day: float) -> datetime:
    """便捷函數：解析TLE時間"""
    return TimeUtils.parse_tle_epoch(year, day)


def format_time_duration(seconds: float) -> str:
    """便捷函數：格式化時間長度"""
    return TimeUtils.format_duration(seconds)


def create_prediction_timeline(start: datetime, hours: int, step_minutes: int = 5) -> List[datetime]:
    """便捷函數：創建預測時間線"""
    end = start + timedelta(hours=hours)
    return TimeUtils.create_time_series(start, end, step_minutes)


def get_current_utc() -> datetime:
    """便捷函數：獲取當前UTC時間"""
    return datetime.now(timezone.utc)


def ensure_utc(dt: datetime) -> datetime:
    """便捷函數：確保datetime為UTC時區"""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    elif dt.tzinfo != timezone.utc:
        return dt.astimezone(timezone.utc)
    return dt