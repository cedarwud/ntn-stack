#!/usr/bin/env python3
"""
即時修復 RL 系統腳本

直接修復運行中的 NetStack 服務的 RL 系統狀態
"""

import requests
import time
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def instant_fix_rl_system():
    """即時修復 RL 系統狀態"""
    logger.info("🚀 開始即時修復 RL 系統...")

    try:
        # 首先檢查當前狀態
        logger.info("📋 檢查當前 RL 系統狀態...")
        response = requests.get("http://localhost:8080/api/v1/rl/health")

        if response.status_code == 200:
            current_status = response.json()
            logger.info(f"🔍 當前狀態: {current_status['details']['ecosystem_status']}")

            if current_status["details"]["ecosystem_status"] == "not_initialized":
                logger.info("⚠️ 系統狀態為 not_initialized，需要修復")

                # 方法1: 嘗試調用訓練啟動來觸發初始化
                logger.info("📝 方法 1: 嘗試通過訓練啟動觸發初始化...")
                try:
                    train_response = requests.post(
                        "http://localhost:8080/api/v1/rl/training/start/dqn"
                    )
                    if train_response.status_code in [200, 201, 202]:
                        logger.info("✅ 訓練請求成功發送")
                    else:
                        logger.warning(
                            f"⚠️ 訓練請求返回狀態: {train_response.status_code}"
                        )
                except Exception as e:
                    logger.warning(f"⚠️ 訓練請求失敗: {e}")

                # 等待一下讓系統處理
                time.sleep(2)

                # 方法2: 多次調用健康檢查來觸發管理器創建
                logger.info("📝 方法 2: 多次調用健康檢查...")
                for i in range(5):
                    try:
                        health_response = requests.get(
                            "http://localhost:8080/api/v1/rl/health"
                        )
                        logger.info(f"健康檢查 {i+1}/5 完成")
                        time.sleep(1)
                    except Exception as e:
                        logger.warning(f"健康檢查 {i+1} 失敗: {e}")

                # 方法3: 調用算法列表來觸發初始化
                logger.info("📝 方法 3: 調用算法列表...")
                try:
                    algo_response = requests.get(
                        "http://localhost:8080/api/v1/rl/algorithms"
                    )
                    if algo_response.status_code == 200:
                        logger.info("✅ 算法列表請求成功")
                    else:
                        logger.warning(
                            f"⚠️ 算法列表請求狀態: {algo_response.status_code}"
                        )
                except Exception as e:
                    logger.warning(f"⚠️ 算法列表請求失敗: {e}")

                # 最終檢查
                logger.info("🔍 檢查修復後的狀態...")
                final_response = requests.get("http://localhost:8080/api/v1/rl/health")

                if final_response.status_code == 200:
                    final_status = final_response.json()
                    new_status = final_status["details"]["ecosystem_status"]

                    if new_status != "not_initialized":
                        logger.info(f"✅ 修復成功！新狀態: {new_status}")
                        return True
                    else:
                        logger.warning("⚠️ 狀態仍然是 not_initialized")

                        # 顯示詳細信息幫助診斷
                        logger.info("📋 當前系統詳細狀態:")
                        logger.info(
                            f"  - ecosystem_status: {final_status['details']['ecosystem_status']}"
                        )
                        logger.info(
                            f"  - registered_algorithms: {final_status['details']['registered_algorithms']}"
                        )

                        # 建議的解決方案
                        logger.info("💡 建議的解決方案:")
                        logger.info("1. 重新啟動 NetStack 服務以應用代碼修復")
                        logger.info("2. 檢查服務日誌以了解具體錯誤")
                        logger.info("3. 驗證 AlgorithmEcosystemManager 是否正確加載")

                        return False
                else:
                    logger.error(
                        f"❌ 最終健康檢查失敗，狀態碼: {final_response.status_code}"
                    )
                    return False

            else:
                logger.info(
                    f"✅ 系統狀態正常: {current_status['details']['ecosystem_status']}"
                )
                return True

        else:
            logger.error(f"❌ 無法獲取系統狀態，HTTP 狀態碼: {response.status_code}")
            return False

    except Exception as e:
        logger.error(f"💥 即時修復失敗: {e}")
        return False


def main():
    """主函數"""
    logger.info("🛠️ RL 系統即時修復工具啟動")

    success = instant_fix_rl_system()

    if success:
        logger.info("🎉 即時修復完成！")
        logger.info(
            "📋 驗證命令: curl -s http://localhost:8080/api/v1/rl/health | jq .details.ecosystem_status"
        )
    else:
        logger.warning("⚠️ 即時修復未完全成功，可能需要重新啟動服務")
        logger.info("🔄 建議執行: docker-compose restart netstack-api")


if __name__ == "__main__":
    main()
