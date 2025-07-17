#!/usr/bin/env python3
"""
🧪 測試暫停功能問題
模擬用戶報告的問題：暫停按鈕功能變成停止，停止按鈕失效
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8080"


class PauseIssueTester:
    """暫停功能問題測試器"""

    def __init__(self):
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_algorithm_status(self, algorithm: str) -> Dict[str, Any]:
        """獲取算法狀態"""
        url = f"{BASE_URL}/api/v1/rl/training/status/{algorithm}"
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"❌ 獲取 {algorithm} 狀態失敗: {response.status}")
                    return {}
        except Exception as e:
            print(f"❌ 請求 {algorithm} 狀態異常: {e}")
            return {}

    async def start_training(self, algorithm: str) -> bool:
        """開始訓練"""
        url = f"{BASE_URL}/api/v1/rl/training/start/{algorithm}"
        payload = {
            "experiment_name": f"{algorithm}_pause_test_{int(time.time())}",
            "total_episodes": 200,
            "scenario_type": "pause_test",
            "hyperparameters": {
                "learning_rate": 0.001,
                "batch_size": 32,
                "gamma": 0.99,
            },
        }

        try:
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ {algorithm} 訓練啟動成功")
                    return True
                else:
                    print(f"❌ {algorithm} 訓練啟動失敗: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ 啟動 {algorithm} 訓練異常: {e}")
            return False

    async def pause_training(self, algorithm: str) -> bool:
        """暫停訓練"""
        url = f"{BASE_URL}/api/v1/rl/training/pause/{algorithm}"
        try:
            async with self.session.post(url) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"⏸️ {algorithm} 訓練暫停成功")
                    return True
                else:
                    print(f"❌ {algorithm} 訓練暫停失敗: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ 暫停 {algorithm} 訓練異常: {e}")
            return False

    async def resume_training(self, algorithm: str) -> bool:
        """恢復訓練"""
        url = f"{BASE_URL}/api/v1/rl/training/resume/{algorithm}"
        try:
            async with self.session.post(url) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"▶️ {algorithm} 訓練恢復成功")
                    return True
                else:
                    print(f"❌ {algorithm} 訓練恢復失敗: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ 恢復 {algorithm} 訓練異常: {e}")
            return False

    async def stop_training(self, algorithm: str) -> bool:
        """停止訓練"""
        url = f"{BASE_URL}/api/v1/rl/training/stop-algorithm/{algorithm}"
        try:
            async with self.session.post(url) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"⏹️ {algorithm} 訓練停止成功")
                    return True
                else:
                    print(f"❌ {algorithm} 訓練停止失敗: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ 停止 {algorithm} 訓練異常: {e}")
            return False

    def analyze_status(self, algorithm: str, status: Dict[str, Any]) -> str:
        """分析狀態並返回前端應該顯示的按鈕"""
        if not status:
            return "❌ 無法獲取狀態"

        algo_status = status.get("status", "unknown")
        training_active = status.get("training_active", False)
        is_training = status.get("is_training", False)

        print(f"📊 {algorithm.upper()} 狀態分析:")
        print(f"   - status: {algo_status}")
        print(f"   - training_active: {training_active}")
        print(f"   - is_training: {is_training}")

        # 模擬前端邏輯
        if not training_active:
            if algo_status in ["stopped", "completed", "cancelled"]:
                return "🔄 重新開始"
            else:
                return "▶️ 開始"
        else:
            if algo_status == "paused":
                return "▶️ 恢復 + ⏹️ 停止"
            elif algo_status in ["running", "active", "training"]:
                return "⏸️ 暫停 + ⏹️ 停止"
            else:
                return f"❓ 未知狀態: {algo_status}"

    async def test_pause_issue_scenario(self, algorithm: str = "dqn"):
        """測試用戶報告的暫停問題場景"""
        print(f"\n🧪 測試 {algorithm.upper()} 暫停功能問題...")
        print("=" * 60)

        # 1. 開始訓練
        print("\n1️⃣ 開始訓練...")
        if not await self.start_training(algorithm):
            print("❌ 無法開始訓練，測試終止")
            return

        # 等待訓練開始
        await asyncio.sleep(3)
        status = await self.get_algorithm_status(algorithm)
        expected_buttons = self.analyze_status(algorithm, status)
        print(f"   期望按鈕: {expected_buttons}")

        # 2. 暫停訓練
        print("\n2️⃣ 暫停訓練...")
        if not await self.pause_training(algorithm):
            print("❌ 暫停失敗")
            return

        await asyncio.sleep(1)
        status = await self.get_algorithm_status(algorithm)
        expected_buttons = self.analyze_status(algorithm, status)
        print(f"   期望按鈕: {expected_buttons}")

        # 3. 測試停止按鈕是否有效（用戶報告的問題）
        print("\n3️⃣ 測試暫停狀態下的停止按鈕...")
        if await self.stop_training(algorithm):
            print("✅ 停止按鈕在暫停狀態下正常工作")
        else:
            print("❌ 停止按鈕在暫停狀態下失效！")

        await asyncio.sleep(1)
        status = await self.get_algorithm_status(algorithm)
        expected_buttons = self.analyze_status(algorithm, status)
        print(f"   期望按鈕: {expected_buttons}")

        # 4. 測試重新開始
        print("\n4️⃣ 測試重新開始...")
        if not await self.start_training(algorithm):
            print("❌ 重新開始失敗")
            return

        await asyncio.sleep(3)
        status = await self.get_algorithm_status(algorithm)
        expected_buttons = self.analyze_status(algorithm, status)
        print(f"   期望按鈕: {expected_buttons}")

        # 5. 再次測試暫停和恢復
        print("\n5️⃣ 再次測試暫停...")
        if not await self.pause_training(algorithm):
            print("❌ 第二次暫停失敗")
            return

        await asyncio.sleep(1)
        status = await self.get_algorithm_status(algorithm)
        expected_buttons = self.analyze_status(algorithm, status)
        print(f"   期望按鈕: {expected_buttons}")

        # 6. 測試恢復
        print("\n6️⃣ 測試恢復...")
        if not await self.resume_training(algorithm):
            print("❌ 恢復失敗")
            return

        await asyncio.sleep(1)
        status = await self.get_algorithm_status(algorithm)
        expected_buttons = self.analyze_status(algorithm, status)
        print(f"   期望按鈕: {expected_buttons}")

        # 7. 最終停止
        print("\n7️⃣ 最終停止...")
        await self.stop_training(algorithm)
        await asyncio.sleep(1)
        status = await self.get_algorithm_status(algorithm)
        expected_buttons = self.analyze_status(algorithm, status)
        print(f"   期望按鈕: {expected_buttons}")

        print(f"\n✅ {algorithm.upper()} 暫停功能測試完成!")
        print("=" * 60)


async def main():
    """主測試函數"""
    print("🚀 開始暫停功能問題測試...")

    async with PauseIssueTester() as tester:
        await tester.test_pause_issue_scenario("dqn")

    print("\n🎉 測試完成!")
    print("\n📝 如果所有步驟都成功，說明後端邏輯正確。")
    print("   如果用戶仍然遇到問題，可能是前端緩存或配置問題。")


if __name__ == "__main__":
    asyncio.run(main())
