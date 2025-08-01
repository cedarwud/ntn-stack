#!/usr/bin/env python3
"""
Phase 0: Docker 建置時預計算數據生成
在容器建置過程中執行軌道預計算，確保啟動時數據即時可用
"""

import sys
import os
import json
import time
import logging
from pathlib import Path
from datetime import datetime

# 添加路徑
sys.path.append("/app/src")
sys.path.append("/app")

# 配置日誌
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """主建置函數"""
    logger.info("🚀 開始 Phase 0 預計算數據建置")

    build_start_time = time.time()

    try:
        # 導入 Phase 0 模組
        from src.services.satellite.coordinate_specific_orbit_engine import (
            CoordinateSpecificOrbitEngine,
        )
        from src.services.satellite.local_tle_loader import LocalTLELoader
        from src.services.satellite.ntpu_visibility_filter import NTPUVisibilityFilter

        # 初始化組件
        logger.info("📡 初始化軌道計算引擎")
        # NTPU 座標 (台灣新北市)
        observer_lat = 24.94417
        observer_lon = 121.37139
        orbit_engine = CoordinateSpecificOrbitEngine(observer_lat, observer_lon)
        tle_loader = LocalTLELoader("tle_data")
        visibility_filter = NTPUVisibilityFilter()

        # 載入 TLE 數據
        logger.info("📊 載入 TLE 數據")
        starlink_collection = tle_loader.load_collected_data("starlink")
        oneweb_collection = tle_loader.load_collected_data("oneweb")

        # 提取實際的衛星數據
        starlink_data = {}
        oneweb_data = {}

        if starlink_collection and "daily_data" in starlink_collection:
            # 取最新一天的數據
            daily_data = starlink_collection["daily_data"]
            if daily_data and len(daily_data) > 0:
                latest_data = daily_data[-1]  # 取最後一天的數據
                if "satellites" in latest_data:
                    starlink_data = {
                        sat["norad_id"]: sat for sat in latest_data["satellites"]
                    }
                    logger.info(f"📡 載入 Starlink 數據: {len(starlink_data)} 顆衛星")

        if oneweb_collection and "daily_data" in oneweb_collection:
            # 取最新一天的數據
            daily_data = oneweb_collection["daily_data"]
            if daily_data and len(daily_data) > 0:
                latest_data = daily_data[-1]  # 取最後一天的數據
                if "satellites" in latest_data:
                    oneweb_data = {
                        sat["norad_id"]: sat for sat in latest_data["satellites"]
                    }
                    logger.info(f"📡 載入 OneWeb 數據: {len(oneweb_data)} 顆衛星")

        if not starlink_data and not oneweb_data:
            logger.warning("⚠️ 沒有找到 TLE 數據，使用模擬數據")
            # 創建模擬數據用於建置
            starlink_data = {
                str(i): sat
                for i, sat in enumerate(create_mock_tle_data("starlink", 100))
            }
            oneweb_data = {
                str(i): sat for i, sat in enumerate(create_mock_tle_data("oneweb", 50))
            }

        # 執行預計算
        logger.info("⚙️ 執行軌道預計算")

        from datetime import datetime

        precomputed_data = {
            "metadata": {
                "generation_timestamp": datetime.now().isoformat(),
                "build_time_seconds": 0,  # 稍後更新
                "data_source": "phase0_build",
                "computation_type": "real_constellation_data",
            },
            "observer_location": {
                "name": "NTPU",
                "lat": 24.94417,
                "lon": 121.37139,
                "alt": 50.0,
            },
            "constellations": {},
        }

        # 處理 Starlink
        if starlink_data:
            logger.info("🛰️ 處理 Starlink 數據")
            starlink_results = {}
            for sat_id, sat_data in starlink_data.items():
                try:
                    sat_results = orbit_engine.compute_120min_orbital_cycle(
                        sat_data, datetime.now()
                    )
                    starlink_results[sat_id] = sat_results
                except Exception as e:
                    logger.warning(f"跳過衛星 {sat_id}: {e}")
            logger.info(f"✅ Starlink 處理完成: {len(starlink_results)} 顆衛星")
            precomputed_data["constellations"]["starlink"] = {
                "name": "STARLINK",
                "orbit_data": {
                    "metadata": {
                        "start_time": datetime.now().isoformat(),
                        "duration_minutes": 120,
                        "time_step_seconds": 30,
                        "total_time_points": 240,
                        "observer_location": {
                            "lat": observer_lat,
                            "lon": observer_lon,
                            "alt": 50.0,
                            "name": "NTPU",
                        },
                    },
                    "satellites": starlink_results,
                },
            }

        # 處理 OneWeb
        if oneweb_data:
            logger.info("🛰️ 處理 OneWeb 數據")
            oneweb_results = {}
            for sat_id, sat_data in oneweb_data.items():
                try:
                    sat_results = orbit_engine.compute_120min_orbital_cycle(
                        sat_data, datetime.now()
                    )
                    oneweb_results[sat_id] = sat_results
                except Exception as e:
                    logger.warning(f"跳過衛星 {sat_id}: {e}")
            logger.info(f"✅ OneWeb 處理完成: {len(oneweb_results)} 顆衛星")
            precomputed_data["constellations"]["oneweb"] = {
                "name": "ONEWEB",
                "orbit_data": {
                    "metadata": {
                        "start_time": datetime.now().isoformat(),
                        "duration_minutes": 120,
                        "time_step_seconds": 30,
                        "total_time_points": 240,
                        "observer_location": {
                            "lat": observer_lat,
                            "lon": observer_lon,
                            "alt": 50.0,
                            "name": "NTPU",
                        },
                    },
                    "satellites": oneweb_results,
                },
            }

        # 更新建置時間
        build_duration = time.time() - build_start_time
        precomputed_data["metadata"]["build_time_seconds"] = round(build_duration, 2)

        # 確保輸出目錄存在
        output_dir = Path("/app/data")
        output_dir.mkdir(parents=True, exist_ok=True)

        # 保存預計算數據（原始 JSON）
        output_file = output_dir / "phase0_precomputed_orbits.json"
        logger.info(f"💾 保存預計算數據: {output_file}")

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(precomputed_data, f, indent=2, ensure_ascii=False)


        # 生成建置摘要
        summary = {
            "build_timestamp": datetime.now().isoformat(),
            "build_duration_seconds": build_duration,
            "total_constellations": len(precomputed_data["constellations"]),
            "total_satellites": sum(
                len(constellation.get("orbit_data", {}).get("satellites", {}))
                for constellation in precomputed_data["constellations"].values()
            ),
            "visible_satellites": sum(
                len([sat for sat in constellation.get("orbit_data", {}).get("satellites", {}).values() 
                     if not sat.get("satellite_info", {}).get("status") == "not_visible"])
                for constellation in precomputed_data["constellations"].values()
            ),
            "output_file_size_bytes": (
                output_file.stat().st_size if output_file.exists() else 0
            ),
            "status": "success",
        }

        summary_file = output_dir / "phase0_build_summary.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        # Phase 2: 生成 D2/A4/A5 事件資料
        logger.info("🎯 開始 Phase 2: D2/A4/A5 事件檢測")
        try:
            from src.services.satellite.handover_event_detector import HandoverEventDetector
            
            # 初始化事件檢測器
            event_detector = HandoverEventDetector(scene_id="ntpu")
            
            # 處理軌道資料生成事件
            events_data = event_detector.process_orbit_data(precomputed_data)
            
            # 保存事件資料
            events_dir = output_dir / "events"
            events_dir.mkdir(exist_ok=True)
            
            events_file = events_dir / "ntpu_handover_events.json"
            logger.info(f"📋 保存事件資料: {events_file}")
            
            with open(events_file, "w", encoding="utf-8") as f:
                json.dump(events_data, f, indent=2, ensure_ascii=False)
            
            # 更新摘要
            summary.update({
                "events_generated": True,
                "total_d2_events": events_data["statistics"]["total_d2_events"],
                "total_a4_events": events_data["statistics"]["total_a4_events"],
                "total_a5_events": events_data["statistics"]["total_a5_events"],
                "events_file_size_bytes": events_file.stat().st_size if events_file.exists() else 0
            })
            
            logger.info(f"🎯 事件生成完成: D2={summary['total_d2_events']}, A4={summary['total_a4_events']}, A5={summary['total_a5_events']}")
            
        except Exception as e:
            logger.error(f"❌ Phase 2 事件檢測失敗: {e}")
            summary["events_generated"] = False
            summary["events_error"] = str(e)

        logger.info(f"✅ Phase 0+2 建置完成！耗時 {build_duration:.2f}s")
        logger.info(f"📊 處理衛星數: {summary['total_satellites']}")
        logger.info(f"💾 軌道檔案大小: {summary['output_file_size_bytes']:,} bytes")
        if summary.get("events_generated"):
            logger.info(f"🎯 事件檔案大小: {summary.get('events_file_size_bytes', 0):,} bytes")

        # 自動同步數據到前端 (如果在開發環境中)
        try:
            import subprocess

            sync_script = (
                Path(__file__).parent.parent / "scripts" / "sync-netstack-data.sh"
            )
            if sync_script.exists():
                logger.info("🔄 自動同步數據到前端...")
                result = subprocess.run(
                    [str(sync_script)], capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    logger.info("✅ 數據同步到前端成功")
                else:
                    logger.warning("⚠️ 數據同步到前端失敗，可手動運行同步腳本")
            else:
                logger.info("ℹ️ 同步腳本不存在，跳過自動同步")
        except Exception as sync_error:
            logger.warning(f"⚠️ 自動同步過程中出現錯誤: {sync_error}")
            logger.info("💡 可以手動運行: scripts/sync-netstack-data.sh")

        return True

    except Exception as e:
        logger.error(f"❌ Phase 0 建置失敗: {e}")

        # 創建錯誤報告
        error_report = {
            "build_timestamp": datetime.now().isoformat(),
            "build_duration_seconds": time.time() - build_start_time,
            "status": "failed",
            "error_message": str(e),
            "error_type": type(e).__name__,
        }

        output_dir = Path("/app/data")
        output_dir.mkdir(parents=True, exist_ok=True)

        error_file = output_dir / "phase0_build_error.json"
        with open(error_file, "w", encoding="utf-8") as f:
            json.dump(error_report, f, indent=2, ensure_ascii=False)

        return False


def create_mock_tle_data(constellation: str, count: int) -> list:
    """創建模擬 TLE 數據用於建置測試"""
    logger.info(f"🔧 創建 {constellation} 模擬數據 ({count} 顆衛星)")

    mock_data = []
    base_norad_id = 44713 if constellation == "starlink" else 47844

    for i in range(count):
        satellite = {
            "name": f"{constellation.upper()}-{i+1}",
            "norad_id": str(base_norad_id + i),
            "line1": f"1 {base_norad_id + i:05d}U 19074A   21001.00000000  .00000000  00000-0  00000-0 0  9990",
            "line2": f"2 {base_norad_id + i:05d}  53.0000 290.0000 0001000  90.0000 270.0000 15.50000000000010",
        }
        mock_data.append(satellite)

    return mock_data


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
