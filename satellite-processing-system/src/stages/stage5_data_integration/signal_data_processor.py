"""
Signal Data Processor - 信號數據處理組件
專責信號統計提取、RSRP估算和信號品質分級
"""

import logging
import math
from typing import Dict, Any, Optional
import psycopg2

# 從CLAUDE.md的Grade A要求: 使用標準噪聲底層值
noise_floor = -120  # 3GPP TS 38.214標準噪聲門檻

logger = logging.getLogger(__name__)

class SignalDataProcessor:
    """信號數據處理器 - 專責信號統計分析和PostgreSQL存儲"""

    def __init__(self, connection: psycopg2.extensions.connection):
        """
        初始化信號數據處理器

        Args:
            connection: PostgreSQL數據庫連接
        """
        self.logger = logging.getLogger(__name__)
        self.connection = connection
        self.processing_statistics = {
            "satellites_processed": 0,
            "signal_statistics_extracted": 0,
            "metadata_inserted": 0,
            "estimation_fallback_used": 0
        }

    def extract_signal_statistics(self, satellite: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """提取信號統計數據"""
        stats = {}

        # 從Stage 4信號分析提取
        stage4_data = satellite.get("stage4_signal_analysis", {})
        if stage4_data:
            signal_quality = stage4_data.get("signal_quality", {})
            stats.update(signal_quality)

        # 從Stage 3時間序列數據計算RSRP統計
        stage3_data = satellite.get("stage3_timeseries", {})
        if stage3_data:
            timeseries_data = stage3_data.get("timeseries_data", [])

            if timeseries_data:
                rsrp_values = []
                for point in timeseries_data:
                    if "rsrp_dbm" in point:
                        rsrp_values.append(point["rsrp_dbm"])

                if rsrp_values:
                    stats["avg_rsrp_dbm"] = sum(rsrp_values) / len(rsrp_values)
                    stats["min_rsrp_dbm"] = min(rsrp_values)
                    stats["max_rsrp_dbm"] = max(rsrp_values)

                    # 計算標準差
                    if len(rsrp_values) > 1:
                        mean = stats["avg_rsrp_dbm"]
                        variance = sum((x - mean) ** 2 for x in rsrp_values) / len(rsrp_values)
                        stats["rsrp_std_dev"] = variance ** 0.5
                    else:
                        stats["rsrp_std_dev"] = 0.0

        # 如果沒有RSRP數據，基於仰角估算
        if "avg_rsrp_dbm" not in stats:
            stage2_data = satellite.get("stage2_visibility", {})
            if stage2_data:
                elevation_profile = stage2_data.get("elevation_profile", [])
                if elevation_profile:
                    # 基於平均仰角估算RSRP
                    avg_elevation = sum(point.get("elevation_deg", 0) for point in elevation_profile) / len(elevation_profile)
                    estimated_rsrp = self.estimate_rsrp_from_elevation(avg_elevation, satellite.get("constellation", "unknown"))

                    stats["avg_rsrp_dbm"] = estimated_rsrp
                    stats["min_rsrp_dbm"] = estimated_rsrp - 10
                    stats["max_rsrp_dbm"] = estimated_rsrp + 5
                    stats["rsrp_std_dev"] = 5.0
                    self.processing_statistics["estimation_fallback_used"] += 1

        # 計算信號品質等級
        if "avg_rsrp_dbm" in stats:
            stats["signal_quality_grade"] = self.grade_signal_quality(stats["avg_rsrp_dbm"])

        # 計算可見性比率
        stage2_data = satellite.get("stage2_visibility", {})
        if stage2_data:
            visibility_stats = stage2_data.get("visibility_statistics", {})
            stats["visibility_rate"] = visibility_stats.get("visibility_rate", 0.0)

        if stats:
            self.processing_statistics["signal_statistics_extracted"] += 1

        return stats if stats else None

    def estimate_rsrp_from_elevation(self, elevation_deg: float, constellation: str) -> float:
        """基於仰角估算RSRP值 - 委派給共用工具函數"""
        from .stage5_shared_utilities import estimate_rsrp_from_elevation
        return estimate_rsrp_from_elevation(elevation_deg, constellation)

    def grade_signal_quality(self, rsrp_dbm: float) -> str:
        """基於RSRP值進行信號品質分級 - 委派給共用工具函數"""
        from .stage5_shared_utilities import grade_signal_quality
        return grade_signal_quality(rsrp_dbm)

    def insert_satellite_metadata(self, satellite: Dict[str, Any]) -> Dict[str, Any]:
        """插入衛星元數據到PostgreSQL"""
        result = {"success": True, "errors": []}

        cursor = self.connection.cursor()

        try:
            satellite_id = satellite.get("satellite_id")
            constellation = satellite.get("constellation", "unknown")

            # 從多階段數據中提取元數據
            stage1_data = satellite.get("stage1_orbital", {})
            stage2_data = satellite.get("stage2_visibility", {})

            metadata = {
                "satellite_id": satellite_id,
                "constellation": constellation,
                "orbital_period_minutes": stage1_data.get("orbital_period_minutes"),
                "inclination_deg": stage1_data.get("inclination_deg"),
                "eccentricity": stage1_data.get("eccentricity"),
                "mean_motion": stage1_data.get("mean_motion"),
                "visibility_rate": stage2_data.get("visibility_statistics", {}).get("visibility_rate", 0.0),
                "max_elevation_deg": stage2_data.get("visibility_statistics", {}).get("max_elevation_deg"),
                "data_integration_timestamp": "NOW()"
            }

            # 構建插入SQL
            columns = list(metadata.keys())
            placeholders = ["%s"] * len(columns)
            values = list(metadata.values())

            insert_sql = f"""
                INSERT INTO satellite_metadata ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                ON CONFLICT (satellite_id) DO UPDATE SET
                constellation = EXCLUDED.constellation,
                visibility_rate = EXCLUDED.visibility_rate,
                data_integration_timestamp = EXCLUDED.data_integration_timestamp;
            """

            cursor.execute(insert_sql, values)
            self.processing_statistics["metadata_inserted"] += 1

        except Exception as e:
            error_msg = f"元數據插入失敗 {satellite_id}: {e}"
            result["success"] = False
            result["errors"].append(error_msg)
            self.logger.error(f"   ❌ {error_msg}")
        finally:
            cursor.close()

        return result

    def insert_signal_statistics(self, satellite: Dict[str, Any], signal_stats: Dict[str, Any]) -> Dict[str, Any]:
        """插入信號統計數據到PostgreSQL"""
        result = {"success": True, "errors": []}

        cursor = self.connection.cursor()

        try:
            satellite_id = satellite.get("satellite_id")

            # 準備信號統計數據
            stats_data = {
                "satellite_id": satellite_id,
                "avg_rsrp_dbm": signal_stats.get("avg_rsrp_dbm"),
                "min_rsrp_dbm": signal_stats.get("min_rsrp_dbm"),
                "max_rsrp_dbm": signal_stats.get("max_rsrp_dbm"),
                "rsrp_std_dev": signal_stats.get("rsrp_std_dev"),
                "signal_quality_grade": signal_stats.get("signal_quality_grade"),
                "visibility_rate": signal_stats.get("visibility_rate"),
                "timestamp": "NOW()"
            }

            # 構建插入SQL
            columns = list(stats_data.keys())
            placeholders = ["%s"] * len(columns)
            values = list(stats_data.values())

            insert_sql = f"""
                INSERT INTO signal_statistics ({', '.join(columns)})
                VALUES ({', '.join(placeholders)});
            """

            cursor.execute(insert_sql, values)

        except Exception as e:
            error_msg = f"信號統計插入失敗 {satellite_id}: {e}"
            result["success"] = False
            result["errors"].append(error_msg)
            self.logger.error(f"   ❌ {error_msg}")
        finally:
            cursor.close()

        return result

    def get_processing_statistics(self) -> Dict[str, Any]:
        """獲取信號處理統計信息"""
        return self.processing_statistics.copy()