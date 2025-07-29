#!/usr/bin/env python3
"""
Phase 4: 容器啟動性能優化器
確保整個系統快速啟動，預計算數據即時可用
"""

import os
import time
import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Optional
import sys

# 添加路徑
sys.path.append("/app/src")
sys.path.append("/app")

# 配置日誌
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class StartupOptimizer:
    """容器啟動性能優化器"""

    def __init__(self):
        self.startup_start_time = time.time()
        self.startup_file = "/tmp/netstack_startup_time"
        self.data_paths = {
            "phase0_data": "/app/data",
            "tle_data": "/app/tle_data",
            "data": "/app/data",  # 修正路徑：從 test_output 改為 data
        }
        self.required_files = [
            "phase0_precomputed_orbits.json",
            "phase0_data_summary.json",
            "phase0_build_config.json",
        ]

    def record_startup_time(self):
        """記錄啟動時間"""
        try:
            with open(self.startup_file, "w") as f:
                f.write(str(self.startup_start_time))
            logger.info(f"✅ 啟動時間已記錄: {self.startup_start_time}")
        except Exception as e:
            logger.error(f"❌ 記錄啟動時間失敗: {e}")

    def check_data_availability(self) -> Dict[str, bool]:
        """檢查數據可用性"""
        logger.info("🔍 檢查預計算數據可用性")

        availability = {}

        for data_type, data_path in self.data_paths.items():
            path = Path(data_path)
            availability[data_type] = {
                "path_exists": path.exists(),
                "is_directory": path.is_dir() if path.exists() else False,
                "file_count": (
                    len(list(path.glob("*"))) if path.exists() and path.is_dir() else 0
                ),
            }

            if availability[data_type]["path_exists"]:
                logger.info(
                    f"✅ {data_type}: {data_path} 存在 ({availability[data_type]['file_count']} 個檔案)"
                )
            else:
                logger.warning(f"⚠️ {data_type}: {data_path} 不存在")

        return availability

    def preload_critical_data(self) -> Dict[str, any]:
        """預載入關鍵數據"""
        logger.info("📊 預載入關鍵數據")

        preloaded_data = {}

        # 檢查 data 目錄中的 Phase 0 數據
        data_path = Path(self.data_paths["data"])

        for required_file in self.required_files:
            file_path = data_path / required_file

            if file_path.exists():
                try:
                    start_time = time.time()

                    if required_file.endswith(".json"):
                        with open(file_path, "r", encoding="utf-8") as f:
                            data = json.load(f)

                        # 只載入元數據，不載入大型數據
                        if required_file == "phase0_precomputed_orbits.json":
                            # 只載入摘要信息，不載入完整軌道數據
                            summary_data = {
                                "metadata": data.get("metadata", {}),
                                "observer_location": data.get("observer_location", {}),
                                "generation_info": data.get("generation_info", {}),
                                "constellations_summary": {},
                            }

                            # 為每個星座只載入統計信息
                            constellations = data.get("constellations", {})
                            for (
                                constellation,
                                constellation_data,
                            ) in constellations.items():
                                summary_data["constellations_summary"][
                                    constellation
                                ] = {
                                    "satellite_count": len(
                                        constellation_data.get("orbit_data", {})
                                    ),
                                    "statistics": constellation_data.get(
                                        "statistics", {}
                                    ),
                                }

                            preloaded_data[required_file] = summary_data
                        else:
                            preloaded_data[required_file] = data

                    load_time = time.time() - start_time
                    file_size = file_path.stat().st_size

                    logger.info(
                        f"✅ {required_file}: 載入成功 ({file_size:,} bytes, {load_time:.3f}s)"
                    )

                except Exception as e:
                    logger.error(f"❌ {required_file}: 載入失敗 - {e}")
                    preloaded_data[required_file] = None
            else:
                logger.warning(f"⚠️ {required_file}: 檔案不存在")
                preloaded_data[required_file] = None

        return preloaded_data

    def optimize_memory_usage(self):
        """優化記憶體使用"""
        logger.info("🧠 優化記憶體使用")

        try:
            import gc

            # 強制垃圾回收
            collected = gc.collect()
            logger.info(f"✅ 垃圾回收完成，釋放 {collected} 個對象")

            # 設置垃圾回收閾值
            gc.set_threshold(700, 10, 10)
            logger.info("✅ 垃圾回收閾值已優化")

        except Exception as e:
            logger.error(f"❌ 記憶體優化失敗: {e}")

    def setup_environment_variables(self):
        """設置環境變量"""
        logger.info("🔧 設置環境變量")

        env_vars = {
            "PYTHONUNBUFFERED": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
            "PRECOMPUTED_DATA_ENABLED": "true",
            "ORBIT_CACHE_PRELOAD": "true",
        }

        for key, value in env_vars.items():
            if key not in os.environ:
                os.environ[key] = value
                logger.info(f"✅ 設置環境變量: {key}={value}")

    def validate_startup_requirements(self) -> bool:
        """驗證啟動需求"""
        logger.info("✅ 驗證啟動需求")

        requirements = {
            "python_version": sys.version_info >= (3, 8),
            "data_availability": False,
            "memory_sufficient": True,
            "disk_space_sufficient": True,
        }

        # 檢查數據可用性
        availability = self.check_data_availability()
        requirements["data_availability"] = any(
            info["path_exists"] for info in availability.values()
        )

        # 檢查記憶體
        try:
            import psutil

            memory = psutil.virtual_memory()
            requirements["memory_sufficient"] = (
                memory.available > 512 * 1024 * 1024
            )  # 512MB
            logger.info(f"可用記憶體: {memory.available / 1024 / 1024:.1f} MB")
        except ImportError:
            logger.warning("無法檢查記憶體使用量 (psutil 未安裝)")

        # 檢查磁碟空間
        try:
            import shutil

            disk_usage = shutil.disk_usage("/")
            free_space_gb = disk_usage.free / (1024**3)
            requirements["disk_space_sufficient"] = free_space_gb > 1.0  # 1GB
            logger.info(f"可用磁碟空間: {free_space_gb:.1f} GB")
        except:
            logger.warning("無法檢查磁碟空間")

        # 輸出驗證結果
        all_passed = all(requirements.values())

        for requirement, passed in requirements.items():
            status = "✅" if passed else "❌"
            logger.info(f"{status} {requirement}: {'通過' if passed else '失敗'}")

        return all_passed

    def create_readiness_probe(self):
        """創建就緒探針"""
        logger.info("🏥 創建就緒探針")

        readiness_file = "/tmp/netstack_ready"

        try:
            with open(readiness_file, "w") as f:
                f.write(
                    json.dumps(
                        {
                            "ready": True,
                            "timestamp": time.time(),
                            "startup_duration": time.time() - self.startup_start_time,
                        }
                    )
                )

            logger.info(f"✅ 就緒探針已創建: {readiness_file}")

        except Exception as e:
            logger.error(f"❌ 創建就緒探針失敗: {e}")

    def generate_startup_report(self, preloaded_data: Dict) -> Dict:
        """生成啟動報告"""
        startup_duration = time.time() - self.startup_start_time

        report = {
            "startup_info": {
                "start_time": self.startup_start_time,
                "duration_seconds": round(startup_duration, 3),
                "status": "completed",
            },
            "data_status": {
                "preloaded_files": len(
                    [f for f in preloaded_data.values() if f is not None]
                ),
                "total_files": len(self.required_files),
                "success_rate": len(
                    [f for f in preloaded_data.values() if f is not None]
                )
                / len(self.required_files),
            },
            "performance_metrics": {
                "startup_target_seconds": 30,
                "actual_startup_seconds": startup_duration,
                "target_achieved": startup_duration < 30,
                "performance_score": min(100, (30 / max(startup_duration, 1)) * 100),
            },
            "system_info": {
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "platform": sys.platform,
                "pid": os.getpid(),
            },
        }

        return report

    async def optimize_startup(self) -> Dict:
        """執行完整的啟動優化流程"""
        logger.info("🚀 開始容器啟動優化")

        # 記錄啟動時間
        self.record_startup_time()

        # 設置環境變量
        self.setup_environment_variables()

        # 驗證啟動需求
        requirements_ok = self.validate_startup_requirements()
        if not requirements_ok:
            logger.warning("⚠️ 部分啟動需求未滿足，但繼續啟動")

        # 預載入關鍵數據
        preloaded_data = self.preload_critical_data()

        # 優化記憶體使用
        self.optimize_memory_usage()

        # 創建就緒探針
        self.create_readiness_probe()

        # 生成啟動報告
        report = self.generate_startup_report(preloaded_data)

        # 保存啟動報告
        report_file = "/tmp/netstack_startup_report.json"
        try:
            with open(report_file, "w") as f:
                json.dump(report, f, indent=2)
            logger.info(f"📊 啟動報告已保存: {report_file}")
        except Exception as e:
            logger.error(f"❌ 保存啟動報告失敗: {e}")

        # 輸出最終結果
        duration = report["startup_info"]["duration_seconds"]
        target_achieved = report["performance_metrics"]["target_achieved"]

        if target_achieved:
            logger.info(f"🎉 啟動優化完成！耗時 {duration:.3f}s (目標: <30s) ✅")
        else:
            logger.warning(
                f"⚠️ 啟動優化完成，但超過目標時間。耗時 {duration:.3f}s (目標: <30s)"
            )

        return report


async def main():
    """主函數"""
    optimizer = StartupOptimizer()
    report = await optimizer.optimize_startup()

    # 輸出關鍵指標
    print(f"\n📊 啟動性能摘要:")
    print(f"啟動時間: {report['startup_info']['duration_seconds']:.3f}s")
    print(
        f"目標達成: {'是' if report['performance_metrics']['target_achieved'] else '否'}"
    )
    print(f"數據載入成功率: {report['data_status']['success_rate']:.1%}")
    print(f"性能評分: {report['performance_metrics']['performance_score']:.1f}/100")


if __name__ == "__main__":
    asyncio.run(main())
