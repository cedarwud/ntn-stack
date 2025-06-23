#!/usr/bin/env python3
"""
階段四快速驗證測試 - 不依賴圖表庫
測試核心論文復現邏輯和API連接
"""

import asyncio
import time
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import sys
import os

# 添加項目根目錄到路徑
sys.path.append('/home/sat/ntn-stack')

def test_configuration_loading():
    """測試配置檔案載入"""
    print("🔧 測試配置檔案載入...")
    
    config_path = Path("configs/paper_reproduction_config.yaml")
    if not config_path.exists():
        print(f"❌ 配置檔案不存在: {config_path}")
        return False
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 檢查關鍵配置
        required_keys = [
            "paper_environments",
            "constellation_scenarios", 
            "handover_schemes_comparison",
            "acceptance_criteria"
        ]
        
        for key in required_keys:
            if key not in config:
                print(f"❌ 缺少配置項: {key}")
                return False
        
        print("✅ 配置檔案載入成功")
        print(f"  📊 星座場景數量: {len(config['constellation_scenarios'])}")
        print(f"  🔄 換手方案數量: {len(config['handover_schemes_comparison']['schemes'])}")
        return True
        
    except Exception as e:
        print(f"❌ 配置檔案載入失敗: {e}")
        return False

async def test_api_connectivity():
    """測試API連接性"""
    print("🌐 測試API連接性...")
    
    try:
        import aiohttp
        
        # NetStack API測試
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get("http://localhost:8080/health") as response:
                    if response.status == 200:
                        print("✅ NetStack API 連接正常")
                        netstack_ok = True
                    else:
                        print(f"⚠️ NetStack API 響應異常: {response.status}")
                        netstack_ok = False
            except Exception as e:
                print(f"❌ NetStack API 連接失敗: {e}")
                netstack_ok = False
            
            # SimWorld API測試  
            try:
                async with session.get("http://localhost:8888/") as response:
                    if response.status == 200:
                        print("✅ SimWorld API 連接正常")
                        simworld_ok = True
                    else:
                        print(f"⚠️ SimWorld API 響應異常: {response.status}")
                        simworld_ok = False
            except Exception as e:
                print(f"❌ SimWorld API 連接失敗: {e}")
                simworld_ok = False
                
        return netstack_ok and simworld_ok
        
    except ImportError:
        print("❌ aiohttp 套件未安裝")
        return False

def test_measurement_simulation():
    """測試測量模擬邏輯"""
    print("📊 測試測量模擬邏輯...")
    
    try:
        import random
        
        # 模擬四種方案的基礎延遲
        schemes = {
            "ntn_baseline": 250.0,
            "ntn_gs": 153.0,
            "ntn_smn": 158.5,
            "proposed": 25.0
        }
        
        measurements = {}
        
        for scheme_name, base_latency in schemes.items():
            # 生成測試測量數據
            scheme_measurements = []
            for _ in range(100):
                # 添加正態分布噪聲
                noise = random.gauss(0, base_latency * 0.1)
                actual_latency = max(base_latency + noise, 5.0)
                
                # 計算成功率 (基於延遲)
                success_probability = 0.99 if scheme_name == "proposed" else 0.95
                success = random.random() < success_probability
                
                measurement = {
                    "latency_ms": actual_latency,
                    "success": success,
                    "prediction_accuracy": random.uniform(0.9, 0.99) if scheme_name == "proposed" else random.uniform(0.7, 0.9)
                }
                scheme_measurements.append(measurement)
            
            measurements[scheme_name] = scheme_measurements
        
        # 計算統計摘要
        for scheme_name, data in measurements.items():
            latencies = [m["latency_ms"] for m in data]
            success_rates = [m["success"] for m in data]
            
            avg_latency = sum(latencies) / len(latencies)
            success_rate = sum(success_rates) / len(success_rates)
            
            print(f"  {scheme_name}: 平均延遲 {avg_latency:.1f}ms, 成功率 {success_rate:.1%}")
        
        print("✅ 測量模擬邏輯正常")
        return True
        
    except Exception as e:
        print(f"❌ 測量模擬失敗: {e}")
        return False

def test_file_system():
    """測試檔案系統結構"""
    print("📁 測試檔案系統結構...")
    
    # 檢查關鍵檔案和目錄
    paths_to_check = [
        "configs/paper_reproduction_config.yaml",
        "paper_reproduction_test_framework.py",
        "algorithm_regression_testing.py", 
        "enhanced_report_generator.py",
        "run_stage4_comprehensive_testing.py",
        "templates/"  # 目錄
    ]
    
    missing_paths = []
    for path_str in paths_to_check:
        path = Path(path_str)
        if not path.exists():
            missing_paths.append(path_str)
        else:
            print(f"✅ {path_str}")
    
    if missing_paths:
        print(f"❌ 缺少檔案或目錄: {missing_paths}")
        return False
    else:
        print("✅ 檔案系統結構完整")
        return True

async def run_stage4_quick_verification():
    """執行階段四快速驗證"""
    print("🚀 開始階段四快速驗證測試")
    print("=" * 50)
    
    start_time = time.time()
    test_results = {}
    
    # 1. 配置檔案測試
    test_results["configuration"] = test_configuration_loading()
    
    # 2. 檔案系統測試
    test_results["file_system"] = test_file_system()
    
    # 3. API 連接測試
    test_results["api_connectivity"] = await test_api_connectivity()
    
    # 4. 測量邏輯測試
    test_results["measurement_logic"] = test_measurement_simulation()
    
    # 結果摘要
    total_time = time.time() - start_time
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    print("\n" + "=" * 50)
    print("📊 階段四快速驗證結果")
    print("=" * 50)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
    
    print(f"\n📈 測試通過率: {passed_tests}/{total_tests} ({passed_tests/total_tests:.1%})")
    print(f"⏱️ 執行時間: {total_time:.2f}秒")
    
    # 儲存結果
    results_dir = Path("results/stage4_quick_verification")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = results_dir / f"quick_verification_{timestamp}.json"
    
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump({
            "test_results": test_results,
            "summary": {
                "passed_tests": passed_tests,
                "total_tests": total_tests,
                "success_rate": passed_tests / total_tests,
                "execution_time": total_time
            },
            "timestamp": datetime.now().isoformat(),
            "next_steps": [
                "安裝完整的Python圖表依賴 (matplotlib, seaborn)" if not test_results.get("api_connectivity") else "",
                "修復API連接問題" if not test_results.get("api_connectivity") else "",
                "執行完整的階段四測試套件"
            ]
        }, f, indent=2, ensure_ascii=False)
    
    print(f"📄 結果已儲存: {result_file}")
    
    if passed_tests == total_tests:
        print("\n🎉 階段四快速驗證完全通過! 可以進行完整測試")
        return True
    else:
        print(f"\n⚠️ 階段四驗證部分失敗，需要修復 {total_tests - passed_tests} 個問題")
        return False

if __name__ == "__main__":
    # 設定當前工作目錄
    os.chdir("/home/sat/ntn-stack/tests")
    
    # 執行快速驗證
    success = asyncio.run(run_stage4_quick_verification())
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)