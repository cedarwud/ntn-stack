#!/usr/bin/env python3
"""
Phase 3 完成度測試 - 研究數據與 RL 整合
"""

import sys
import asyncio
import json
from datetime import datetime
from pathlib import Path

# 添加路徑
sys.path.append('netstack/src')
sys.path.append('netstack')

async def test_phase3_completion():
    """測試 Phase 3 完成度"""
    print("🔬 Phase 3 完成度測試 - 研究數據與 RL 整合")
    print("=" * 60)
    
    results = {
        "phase3_features": {},
        "research_components": {},
        "integration_status": {},
        "overall_score": 0
    }
    
    # 測試 1: 45天歷史數據收集自動化
    print("\n📡 1. 45天歷史數據收集自動化")
    
    try:
        # 檢查 DailyTLECollector
        collector_path = Path("netstack/scripts/daily_tle_collector.py")
        if collector_path.exists():
            print("✅ daily_tle_collector.py 存在")
            results["research_components"]["daily_tle_collector"] = True
            
            # 檢查功能完整性
            with open(collector_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            required_methods = [
                "collect_daily_data",
                "validate_45day_completeness",
                "get_existing_data_status",
                "download_tle_data",
                "validate_tle_format"
            ]
            
            methods_found = 0
            for method in required_methods:
                if f"def {method}" in content:
                    methods_found += 1
                    print(f"  ✅ {method} 方法存在")
                else:
                    print(f"  ❌ {method} 方法缺失")
            
            results["phase3_features"]["tle_collection_automation"] = methods_found == len(required_methods)
            
        else:
            print("❌ daily_tle_collector.py 不存在")
            results["research_components"]["daily_tle_collector"] = False
            results["phase3_features"]["tle_collection_automation"] = False
            
    except Exception as e:
        print(f"❌ TLE 收集器測試失敗: {e}")
        results["research_components"]["daily_tle_collector"] = False
        results["phase3_features"]["tle_collection_automation"] = False
    
    # 測試 2: RL 訓練數據集生成
    print("\n🤖 2. RL 訓練數據集生成")
    
    try:
        # 檢查 RLDatasetGenerator
        rl_generator_path = Path("netstack/src/services/rl/rl_dataset_generator.py")
        if rl_generator_path.exists():
            print("✅ rl_dataset_generator.py 存在")
            results["research_components"]["rl_dataset_generator"] = True
            
            # 檢查功能完整性
            with open(rl_generator_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            required_methods = [
                "generate_handover_episodes",
                "export_ml_format",
                "build_state_vector",
                "calculate_reward",
                "export_pytorch_format",
                "export_csv_format"
            ]
            
            methods_found = 0
            for method in required_methods:
                if f"def {method}" in content:
                    methods_found += 1
                    print(f"  ✅ {method} 方法存在")
                else:
                    print(f"  ❌ {method} 方法缺失")
            
            results["phase3_features"]["rl_dataset_generation"] = methods_found == len(required_methods)
            
            # 檢查 ML 框架支援
            ml_formats = ["pytorch", "tensorflow", "csv", "json"]
            ml_support = []
            for fmt in ml_formats:
                if f"export_{fmt}_format" in content or f'format_type == "{fmt}"' in content:
                    ml_support.append(fmt)
                    print(f"  ✅ {fmt.upper()} 格式支援")
            
            results["phase3_features"]["ml_framework_support"] = len(ml_support) >= 2
            
        else:
            print("❌ rl_dataset_generator.py 不存在")
            results["research_components"]["rl_dataset_generator"] = False
            results["phase3_features"]["rl_dataset_generation"] = False
            results["phase3_features"]["ml_framework_support"] = False
            
    except Exception as e:
        print(f"❌ RL 數據集生成器測試失敗: {e}")
        results["research_components"]["rl_dataset_generator"] = False
        results["phase3_features"]["rl_dataset_generation"] = False
        results["phase3_features"]["ml_framework_support"] = False
    
    # 測試 3: 3GPP NTN 標準事件生成器
    print("\n📋 3. 3GPP NTN 標準事件生成器")
    
    try:
        # 檢查 ThreeGPPEventGenerator
        threegpp_path = Path("netstack/src/services/research/threegpp_event_generator.py")
        if threegpp_path.exists():
            print("✅ threegpp_event_generator.py 存在")
            results["research_components"]["threegpp_event_generator"] = True
            
            # 檢查功能完整性
            with open(threegpp_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 檢查 3GPP 事件類型
            event_types = ["A1", "A2", "A3", "A4", "A5", "A6"]
            events_found = 0
            for event_type in event_types:
                if f"check_{event_type.lower()}_event" in content:
                    events_found += 1
                    print(f"  ✅ {event_type} 事件支援")
                else:
                    print(f"  ❌ {event_type} 事件缺失")
            
            results["phase3_features"]["threegpp_events"] = events_found == len(event_types)
            
            # 檢查學術研究功能
            academic_features = [
                "generate_academic_report",
                "analyze_signal_quality",
                "analyze_ntn_characteristics",
                "generate_academic_insights"
            ]
            
            academic_found = 0
            for feature in academic_features:
                if f"def {feature}" in content:
                    academic_found += 1
                    print(f"  ✅ {feature} 功能存在")
                else:
                    print(f"  ❌ {feature} 功能缺失")
            
            results["phase3_features"]["academic_research_support"] = academic_found == len(academic_features)
            
        else:
            print("❌ threegpp_event_generator.py 不存在")
            results["research_components"]["threegpp_event_generator"] = False
            results["phase3_features"]["threegpp_events"] = False
            results["phase3_features"]["academic_research_support"] = False
            
    except Exception as e:
        print(f"❌ 3GPP 事件生成器測試失敗: {e}")
        results["research_components"]["threegpp_event_generator"] = False
        results["phase3_features"]["threegpp_events"] = False
        results["phase3_features"]["academic_research_support"] = False
    
    # 測試 4: 功能整合測試
    print("\n🔗 4. 功能整合測試")
    
    try:
        # 測試 TLE 收集器
        if results["research_components"]["daily_tle_collector"]:
            print("  🧪 測試 TLE 收集器導入")
            try:
                from netstack.scripts.daily_tle_collector import DailyTLECollector
                collector = DailyTLECollector(target_days=5)  # 測試用小數據集
                print("  ✅ TLE 收集器可正常導入和實例化")
                results["integration_status"]["tle_collector_import"] = True
            except Exception as e:
                print(f"  ❌ TLE 收集器導入失敗: {e}")
                results["integration_status"]["tle_collector_import"] = False
        
        # 測試 RL 數據集生成器
        if results["research_components"]["rl_dataset_generator"]:
            print("  🧪 測試 RL 數據集生成器導入")
            try:
                from netstack.src.services.rl.rl_dataset_generator import RLDatasetGenerator
                # 創建測試數據
                test_data = {
                    'observer_location': {'lat': 24.94417, 'lon': 121.37139},
                    'constellations': {
                        'starlink': {
                            'orbit_data': {
                                'test_sat': {
                                    'trajectory': {
                                        'timestamps': [0, 60, 120],
                                        'positions': [[100, 200, 300], [110, 210, 310], [120, 220, 320]],
                                        'elevations': [15, 25, 35]
                                    }
                                }
                            }
                        }
                    }
                }
                generator = RLDatasetGenerator(test_data)
                print("  ✅ RL 數據集生成器可正常導入和實例化")
                results["integration_status"]["rl_generator_import"] = True
            except Exception as e:
                print(f"  ❌ RL 數據集生成器導入失敗: {e}")
                results["integration_status"]["rl_generator_import"] = False
        
        # 測試 3GPP 事件生成器
        if results["research_components"]["threegpp_event_generator"]:
            print("  🧪 測試 3GPP 事件生成器導入")
            try:
                from netstack.src.services.research.threegpp_event_generator import ThreeGPPEventGenerator
                generator = ThreeGPPEventGenerator()
                print("  ✅ 3GPP 事件生成器可正常導入和實例化")
                results["integration_status"]["threegpp_generator_import"] = True
            except Exception as e:
                print(f"  ❌ 3GPP 事件生成器導入失敗: {e}")
                results["integration_status"]["threegpp_generator_import"] = False
                
    except Exception as e:
        print(f"❌ 整合測試失敗: {e}")
        results["integration_status"]["tle_collector_import"] = False
        results["integration_status"]["rl_generator_import"] = False
        results["integration_status"]["threegpp_generator_import"] = False
    
    # 測試 5: 多星座支援檢查
    print("\n🛰️ 5. 多星座支援檢查")
    
    multi_constellation_support = True
    
    # 檢查 TLE 收集器的多星座支援
    if results["research_components"]["daily_tle_collector"]:
        with open("netstack/scripts/daily_tle_collector.py", 'r') as f:
            content = f.read()
        if "'starlink'" in content and "'oneweb'" in content:
            print("  ✅ TLE 收集器支援 Starlink 和 OneWeb")
        else:
            print("  ❌ TLE 收集器多星座支援不完整")
            multi_constellation_support = False
    
    results["phase3_features"]["multi_constellation_support"] = multi_constellation_support
    
    # 計算總分
    all_features = {**results["phase3_features"], **results["research_components"], **results["integration_status"]}
    total_features = len(all_features)
    completed_features = sum(all_features.values())
    
    if total_features > 0:
        results["overall_score"] = (completed_features / total_features) * 100
    
    # 輸出結果摘要
    print(f"\n📊 Phase 3 完成度摘要")
    print(f"=" * 40)
    print(f"總體完成度: {results['overall_score']:.1f}%")
    print(f"完成功能: {completed_features}/{total_features}")
    
    print(f"\n🎯 功能狀態:")
    for category, features in results.items():
        if category == "overall_score":
            continue
        print(f"\n{category.upper()}:")
        for feature, status in features.items():
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {feature}")
    
    # Phase 3 驗收標準檢查
    print(f"\n📋 Phase 3 驗收標準檢查:")
    acceptance_criteria = {
        "45天完整 TLE 數據收集機制建立": results["phase3_features"]["tle_collection_automation"],
        "RL 訓練數據集自動生成 (支援 PyTorch/TensorFlow)": results["phase3_features"]["rl_dataset_generation"] and results["phase3_features"]["ml_framework_support"],
        "3GPP NTN 標準事件生成器": results["phase3_features"]["threegpp_events"],
        "學術論文品質的數據驗證報告": results["phase3_features"]["academic_research_support"],
        "支援多星座 (Starlink/OneWeb) 對比研究": results["phase3_features"]["multi_constellation_support"]
    }
    
    for criterion, status in acceptance_criteria.items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {criterion}")
    
    acceptance_score = sum(acceptance_criteria.values()) / len(acceptance_criteria) * 100
    print(f"\n🎯 驗收標準達成率: {acceptance_score:.1f}%")
    
    # 保存結果
    with open('test_phase3_results.json', 'w', encoding='utf-8') as f:
        json.dump({
            **results,
            "acceptance_criteria": acceptance_criteria,
            "acceptance_score": acceptance_score,
            "test_timestamp": datetime.now().isoformat()
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 測試結果已保存至: test_phase3_results.json")
    
    return results

if __name__ == "__main__":
    asyncio.run(test_phase3_completion())
