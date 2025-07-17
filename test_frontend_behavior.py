#!/usr/bin/env python3
"""
🧪 測試前端行為
模擬前端的 API 調用順序，檢查暫停/恢復功能
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8080"

class FrontendBehaviorTester:
    """前端行為測試器"""
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def start_training(self, algorithm: str) -> bool:
        """模擬前端開始訓練"""
        url = f"{BASE_URL}/api/v1/rl/training/start/{algorithm}"
        payload = {
            "experiment_name": f"{algorithm}_training_{int(time.time())}",
            "total_episodes": 1000,
            "scenario_type": "interference_mitigation",
            "hyperparameters": {
                "learning_rate": 0.001,
                "batch_size": 32,
                "gamma": 0.99
            }
        }
        
        try:
            print(f"📤 [前端模擬] 發送訓練請求到: {url}")
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ [前端模擬] {algorithm} 訓練啟動成功: {result}")
                    return True
                else:
                    print(f"❌ [前端模擬] {algorithm} 訓練啟動失敗: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ [前端模擬] 啟動 {algorithm} 訓練異常: {e}")
            return False
    
    async def get_status(self, algorithm: str) -> Dict[str, Any]:
        """模擬前端獲取狀態"""
        url = f"{BASE_URL}/api/v1/rl/training/status/{algorithm}"
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"❌ [前端模擬] 獲取 {algorithm} 狀態失敗: {response.status}")
                    return {}
        except Exception as e:
            print(f"❌ [前端模擬] 獲取 {algorithm} 狀態異常: {e}")
            return {}
    
    async def pause_training(self, algorithm: str) -> bool:
        """模擬前端暫停訓練"""
        url = f"{BASE_URL}/api/v1/rl/training/pause/{algorithm}"
        try:
            print(f"⏸️ [前端模擬] 發送暫停請求到: {url}")
            async with self.session.post(url, headers={'Content-Type': 'application/json'}) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ [前端模擬] {algorithm} 訓練暫停成功: {result}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ [前端模擬] {algorithm} 訓練暫停失敗: {response.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"❌ [前端模擬] 暫停 {algorithm} 訓練異常: {e}")
            return False
    
    async def resume_training(self, algorithm: str) -> bool:
        """模擬前端恢復訓練"""
        url = f"{BASE_URL}/api/v1/rl/training/resume/{algorithm}"
        try:
            print(f"▶️ [前端模擬] 發送恢復請求到: {url}")
            async with self.session.post(url, headers={'Content-Type': 'application/json'}) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ [前端模擬] {algorithm} 訓練恢復成功: {result}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ [前端模擬] {algorithm} 訓練恢復失敗: {response.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"❌ [前端模擬] 恢復 {algorithm} 訓練異常: {e}")
            return False
    
    async def stop_training(self, algorithm: str) -> bool:
        """模擬前端停止訓練"""
        url = f"{BASE_URL}/api/v1/rl/training/stop-algorithm/{algorithm}"
        try:
            print(f"⏹️ [前端模擬] 發送停止請求到: {url}")
            async with self.session.post(url, headers={'Content-Type': 'application/json'}) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ [前端模擬] {algorithm} 訓練停止成功: {result}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ [前端模擬] {algorithm} 訓練停止失敗: {response.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"❌ [前端模擬] 停止 {algorithm} 訓練異常: {e}")
            return False
    
    def print_status_analysis(self, algorithm: str, status: Dict[str, Any]):
        """分析並打印狀態"""
        if not status:
            print(f"📊 [狀態分析] {algorithm.upper()}: 無法獲取狀態")
            return
        
        algo_status = status.get('status', 'unknown')
        training_active = status.get('training_active', False)
        is_training = status.get('is_training', False)
        episode = status.get('training_progress', {}).get('current_episode', 'N/A') if status.get('training_progress') else 'N/A'
        
        print(f"📊 [狀態分析] {algorithm.upper()}:")
        print(f"   - status: {algo_status}")
        print(f"   - training_active: {training_active}")
        print(f"   - is_training: {is_training}")
        print(f"   - episode: {episode}")
        
        # 根據狀態判斷前端應該顯示的按鈕
        if not training_active:
            if algo_status in ['stopped', 'completed', 'cancelled']:
                expected_buttons = "🔄 重新開始"
            else:
                expected_buttons = "▶️ 開始"
        else:
            if algo_status == 'paused':
                expected_buttons = "▶️ 恢復 + ⏹️ 停止"
            elif algo_status in ['running', 'active', 'training']:
                expected_buttons = "⏸️ 暫停 + ⏹️ 停止"
            else:
                expected_buttons = f"❓ 未知狀態: {algo_status}"
        
        print(f"   - 期望按鈕: {expected_buttons}")
    
    async def test_pause_resume_cycle(self, algorithm: str = "dqn"):
        """測試完整的暫停/恢復週期"""
        print(f"\n🧪 測試 {algorithm.upper()} 暫停/恢復週期...")
        print("="*60)
        
        # 1. 開始訓練
        print("\n1️⃣ 開始訓練...")
        if not await self.start_training(algorithm):
            print("❌ 無法開始訓練，測試終止")
            return False
        
        # 等待訓練開始
        await asyncio.sleep(3)
        status = await self.get_status(algorithm)
        self.print_status_analysis(algorithm, status)
        
        if status.get('status') != 'running':
            print("❌ 訓練未正確開始")
            return False
        
        # 2. 暫停訓練
        print("\n2️⃣ 暫停訓練...")
        if not await self.pause_training(algorithm):
            print("❌ 暫停失敗")
            return False
        
        # 等待狀態更新
        await asyncio.sleep(1)
        status = await self.get_status(algorithm)
        self.print_status_analysis(algorithm, status)
        
        if status.get('status') != 'paused':
            print("❌ 暫停狀態不正確")
            return False
        
        # 3. 測試暫停狀態下的停止按鈕
        print("\n3️⃣ 測試暫停狀態下的停止按鈕...")
        print("   (模擬用戶點擊停止按鈕)")
        
        if await self.stop_training(algorithm):
            print("✅ 停止按鈕在暫停狀態下正常工作")
            
            await asyncio.sleep(1)
            status = await self.get_status(algorithm)
            self.print_status_analysis(algorithm, status)
            
            if status.get('training_active') == False:
                print("✅ 停止後狀態正確")
                return True
            else:
                print("❌ 停止後狀態不正確")
                return False
        else:
            print("❌ 停止按鈕在暫停狀態下失效")
            return False
    
    async def test_pause_resume_functionality(self, algorithm: str = "dqn"):
        """測試暫停/恢復功能"""
        print(f"\n🧪 測試 {algorithm.upper()} 暫停/恢復功能...")
        print("="*60)
        
        # 1. 開始訓練
        print("\n1️⃣ 開始訓練...")
        if not await self.start_training(algorithm):
            print("❌ 無法開始訓練，測試終止")
            return False
        
        await asyncio.sleep(3)
        status = await self.get_status(algorithm)
        self.print_status_analysis(algorithm, status)
        
        # 2. 暫停訓練
        print("\n2️⃣ 暫停訓練...")
        if not await self.pause_training(algorithm):
            print("❌ 暫停失敗")
            return False
        
        await asyncio.sleep(1)
        status = await self.get_status(algorithm)
        self.print_status_analysis(algorithm, status)
        
        # 3. 恢復訓練
        print("\n3️⃣ 恢復訓練...")
        if not await self.resume_training(algorithm):
            print("❌ 恢復失敗")
            return False
        
        await asyncio.sleep(2)
        status = await self.get_status(algorithm)
        self.print_status_analysis(algorithm, status)
        
        # 4. 最終停止
        print("\n4️⃣ 最終停止...")
        await self.stop_training(algorithm)
        await asyncio.sleep(1)
        status = await self.get_status(algorithm)
        self.print_status_analysis(algorithm, status)
        
        return True

async def main():
    """主測試函數"""
    print("🚀 開始前端行為測試...")
    
    async with FrontendBehaviorTester() as tester:
        # 測試暫停/恢復週期
        success1 = await tester.test_pause_resume_cycle("dqn")
        
        # 等待一下再測試暫停/恢復功能
        await asyncio.sleep(2)
        success2 = await tester.test_pause_resume_functionality("dqn")
        
        if success1 and success2:
            print("\n🎉 所有測試通過!")
        else:
            print("\n⚠️ 部分測試失敗")
    
    print("\n📝 測試完成")

if __name__ == "__main__":
    asyncio.run(main())
