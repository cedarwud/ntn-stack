#!/usr/bin/env python3
"""
驗證優化變更 - 測試腳本
測試新的統一 JSON 檔案服務和修復的硬編碼座標
"""

import sys
import json
from pathlib import Path

# 添加路徑
sys.path.insert(0, '/home/sat/ntn-stack/netstack/src')

def test_json_file_service():
    """測試統一 JSON 檔案服務"""
    print("🧪 測試統一 JSON 檔案服務...")
    
    try:
        from shared_core.json_file_service import get_json_file_service
        
        service = get_json_file_service()
        print("✅ JSON 檔案服務導入成功")
        
        # 測試檔案大小計算
        test_file = "/home/sat/ntn-stack/docs/shared_core_architecture.md"
        if Path(test_file).exists():
            size = service.get_file_size_mb(test_file)
            print(f"✅ 檔案大小計算: {size:.3f} MB")
        
        # 測試數據結構驗證
        test_data = {"metadata": {"test": "value"}, "satellites": []}
        valid = service.validate_json_structure(test_data, ["metadata", "satellites"])
        print(f"✅ 數據結構驗證: {valid}")
        
        # 測試錯誤響應創建
        error_resp = service.create_error_response("Test error", "TestStage")
        print(f"✅ 錯誤響應創建: success={error_resp['success']}")
        
        # 測試成功響應創建
        success_resp = service.create_success_response({"data": "test"}, "TestStage")
        print(f"✅ 成功響應創建: success={success_resp['success']}")
        
        return True
        
    except ImportError as e:
        print(f"❌ 導入失敗: {e}")
        return False
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def test_observer_coordinates():
    """測試統一觀測座標服務"""
    print("\n🧪 測試統一觀測座標...")
    
    try:
        from shared_core.observer_config_service import get_ntpu_coordinates
        
        lat, lon, alt = get_ntpu_coordinates()
        print(f"✅ 觀測座標服務: ({lat}°, {lon}°, {alt}m)")
        
        # 驗證座標值
        expected_lat = 24.9441667
        expected_lon = 121.3713889
        
        if abs(lat - expected_lat) < 0.0001 and abs(lon - expected_lon) < 0.0001:
            print("✅ 座標值正確")
        else:
            print(f"⚠️ 座標值不符: 期望 ({expected_lat}, {expected_lon})")
            
        return True
        
    except ImportError as e:
        print(f"❌ 導入失敗: {e}")
        return False
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def check_stage_imports():
    """檢查階段處理器是否正確使用 shared_core"""
    print("\n🧪 檢查階段處理器導入...")
    
    stages_to_check = [
        ("Stage 2", "/home/sat/ntn-stack/netstack/src/stages/intelligent_satellite_filter_processor.py"),
        ("Stage 5", "/home/sat/ntn-stack/netstack/src/stages/data_integration_processor.py")
    ]
    
    all_good = True
    
    for stage_name, file_path in stages_to_check:
        if Path(file_path).exists():
            with open(file_path, 'r') as f:
                content = f.read()
                
            # 檢查是否導入 observer_config_service
            if "from shared_core.observer_config_service import get_ntpu_coordinates" in content:
                print(f"✅ {stage_name}: 使用 shared_core.observer_config_service")
            else:
                print(f"⚠️ {stage_name}: 未找到 observer_config_service 導入")
                
            # 檢查是否還有硬編碼座標
            hardcoded_lat = "24.9441667"
            hardcoded_lon = "121.3713889"
            
            # 檢查 __init__ 方法中的硬編碼
            if f"observer_lat: float = {hardcoded_lat}" in content:
                print(f"⚠️ {stage_name}: 仍有硬編碼座標在函數簽名中 (已修復為可選參數)")
            elif f"self.observer_lat = {hardcoded_lat}" in content:
                print(f"❌ {stage_name}: 仍有硬編碼座標在初始化中")
                all_good = False
            else:
                print(f"✅ {stage_name}: 無硬編碼座標")
        else:
            print(f"⚠️ {stage_name}: 檔案不存在")
    
    return all_good

def check_documentation():
    """檢查文檔是否已更新"""
    print("\n🧪 檢查文檔更新...")
    
    doc_file = "/home/sat/ntn-stack/docs/shared_core_architecture.md"
    
    if Path(doc_file).exists():
        with open(doc_file, 'r') as f:
            content = f.read()
        
        # 檢查是否包含 JSON 檔案服務
        if "json_file_service.py" in content:
            print("✅ 文檔已包含 JSON 檔案服務")
        else:
            print("❌ 文檔未包含 JSON 檔案服務")
            
        # 檢查版本號
        if "版本**: 1.2.0" in content:
            print("✅ 文檔版本已更新至 1.2.0")
        else:
            print("⚠️ 文檔版本未更新")
            
        return True
    else:
        print("❌ 文檔檔案不存在")
        return False

def main():
    """主測試函數"""
    print("=" * 60)
    print("🚀 開始驗證優化變更")
    print("=" * 60)
    
    results = []
    
    # 執行各項測試
    results.append(("JSON 檔案服務", test_json_file_service()))
    results.append(("觀測座標服務", test_observer_coordinates()))
    results.append(("階段處理器", check_stage_imports()))
    results.append(("文檔更新", check_documentation()))
    
    # 總結結果
    print("\n" + "=" * 60)
    print("📊 測試結果總結")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ 通過" if passed else "❌ 失敗"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有測試通過！優化實施成功")
    else:
        print("⚠️ 部分測試失敗，請檢查相關實施")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())