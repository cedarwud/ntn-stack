#!/usr/bin/env python3
"""
🧪 測試按鈕狀態修復效果
驗證訓練控制按鈕的狀態轉換是否正常工作
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8080"

class ButtonStateTester:
    """按鈕狀態測試器"""
    
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
            "experiment_name": f"{algorithm}_test_{int(time.time())}",
            "total_episodes": 50,
            "scenario_type": "test",
            "hyperparameters": {
                "learning_rate": 0.001,
                "batch_size": 32,
                "gamma": 0.99
            }
        }
        
        try:
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ {algorithm} 訓練啟動成功: {result.get('message', '')}")
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
                    print(f"⏸️ {algorithm} 訓練暫停成功: {result.get('message', '')}")
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
                    print(f"▶️ {algorithm} 訓練恢復成功: {result.get('message', '')}")
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
                    print(f"⏹️ {algorithm} 訓練停止成功: {result.get('message', '')}")
                    return True
                else:
                    print(f"❌ {algorithm} 訓練停止失敗: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ 停止 {algorithm} 訓練異常: {e}")
            return False
    
    def print_status(self, algorithm: str, status: Dict[str, Any]):
        """打印狀態信息"""
        if not status:
            print(f"📊 {algorithm.upper()} 狀態: 無法獲取")
            return
        
        print(f"📊 {algorithm.upper()} 狀態:")
        print(f"   - status: {status.get('status', 'unknown')}")
        print(f"   - training_active: {status.get('training_active', False)}")
        print(f"   - is_training: {status.get('is_training', False)}")
        print(f"   - session_id: {status.get('session_id', 'None')}")
        print(f"   - message: {status.get('message', '')}")
    
    async def test_button_state_transitions(self, algorithm: str = "dqn"):
        """測試按鈕狀態轉換"""
        print(f"\n🧪 開始測試 {algorithm.upper()} 按鈕狀態轉換...")
        print("="*60)
        
        # 1. 初始狀態檢查
        print("\n1️⃣ 檢查初始狀態...")
        status = await self.get_algorithm_status(algorithm)
        self.print_status(algorithm, status)
        
        # 2. 開始訓練
        print("\n2️⃣ 開始訓練...")
        if await self.start_training(algorithm):
            await asyncio.sleep(2)  # 等待狀態更新
            status = await self.get_algorithm_status(algorithm)
            self.print_status(algorithm, status)
            
            # 3. 暫停訓練
            print("\n3️⃣ 暫停訓練...")
            if await self.pause_training(algorithm):
                await asyncio.sleep(1)
                status = await self.get_algorithm_status(algorithm)
                self.print_status(algorithm, status)
                
                # 4. 恢復訓練
                print("\n4️⃣ 恢復訓練...")
                if await self.resume_training(algorithm):
                    await asyncio.sleep(1)
                    status = await self.get_algorithm_status(algorithm)
                    self.print_status(algorithm, status)
                
                # 5. 停止訓練
                print("\n5️⃣ 停止訓練...")
                if await self.stop_training(algorithm):
                    await asyncio.sleep(1)
                    status = await self.get_algorithm_status(algorithm)
                    self.print_status(algorithm, status)
                    
                    # 6. 再次檢查狀態（確保可以重新開始）
                    print("\n6️⃣ 停止後狀態檢查...")
                    await asyncio.sleep(1)
                    status = await self.get_algorithm_status(algorithm)
                    self.print_status(algorithm, status)
                    
                    # 7. 測試重新開始
                    print("\n7️⃣ 測試重新開始...")
                    if await self.start_training(algorithm):
                        await asyncio.sleep(2)
                        status = await self.get_algorithm_status(algorithm)
                        self.print_status(algorithm, status)
                        
                        # 8. 最終停止
                        print("\n8️⃣ 最終停止...")
                        await self.stop_training(algorithm)
                        await asyncio.sleep(1)
                        status = await self.get_algorithm_status(algorithm)
                        self.print_status(algorithm, status)
        
        print(f"\n✅ {algorithm.upper()} 按鈕狀態轉換測試完成!")
        print("="*60)

async def main():
    """主測試函數"""
    print("🚀 開始按鈕狀態修復測試...")
    
    async with ButtonStateTester() as tester:
        # 測試 DQN 算法
        await tester.test_button_state_transitions("dqn")
        
        # 可以測試其他算法
        # await tester.test_button_state_transitions("ppo")
        # await tester.test_button_state_transitions("sac")
    
    print("\n🎉 所有測試完成!")

if __name__ == "__main__":
    asyncio.run(main())
