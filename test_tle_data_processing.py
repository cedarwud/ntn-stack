#!/usr/bin/env python3
"""
測試 TLE 數據處理的實際邏輯
驗證第1階段 SGP4 計算是否真的處理全量衛星數據
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timezone

# 添加 netstack 模組路徑
sys.path.insert(0, '/home/sat/ntn-stack/netstack')

def test_tle_data_loading():
    """測試 TLE 數據載入的實際數量"""
    print("🔍 測試 TLE 數據載入邏輯")
    print("=" * 60)
    
    # 模擬 Phase25DataPreprocessor 的載入邏輯
    tle_data_dir = Path("/home/sat/ntn-stack/netstack/tle_data")
    
    total_satellites = 0
    constellations_data = {}
    
    for constellation in ['starlink', 'oneweb']:
        tle_dir = tle_data_dir / constellation / "tle"
        
        if not tle_dir.exists():
            print(f"❌ {constellation} TLE 目錄不存在: {tle_dir}")
            continue
            
        # 尋找最新的 TLE 文件
        tle_files = list(tle_dir.glob(f"{constellation}_*.tle"))
        
        if not tle_files:
            print(f"❌ {constellation} 無 TLE 文件")
            continue
            
        # 選擇最新文件
        latest_file = max(tle_files, key=lambda x: x.stem.split('_')[-1])
        
        print(f"\n📡 處理 {constellation.upper()} 星座")
        print(f"   文件: {latest_file.name}")
        
        # 實際載入並解析 TLE 數據
        satellites = load_tle_file(latest_file)
        
        constellations_data[constellation] = {
            'file': latest_file.name,
            'satellites': len(satellites),
            'sample_satellites': satellites[:3]  # 顯示前3個作為樣本
        }
        
        total_satellites += len(satellites)
        
        print(f"   載入衛星數: {len(satellites)}")
        
        # 顯示前幾個衛星的 NORAD ID
        if satellites:
            sample_ids = [sat['norad_id'] for sat in satellites[:5]]
            print(f"   前5個 NORAD ID: {sample_ids}")
    
    print(f"\n🎯 測試結果摘要")
    print(f"   總衛星數: {total_satellites}")
    print(f"   Starlink: {constellations_data.get('starlink', {}).get('satellites', 0)}")
    print(f"   OneWeb: {constellations_data.get('oneweb', {}).get('satellites', 0)}")
    
    return total_satellites, constellations_data

def load_tle_file(tle_file):
    """載入並解析單個 TLE 文件"""
    satellites = []
    
    try:
        with open(tle_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.strip().split('\n')
        lines = [line.strip() for line in lines if line.strip()]
        
        i = 0
        while i + 2 < len(lines):
            name_line = lines[i].strip()
            line1 = lines[i + 1].strip()
            line2 = lines[i + 2].strip()
            
            # 驗證 TLE 格式
            if (line1.startswith('1 ') and 
                line2.startswith('2 ') and 
                len(line1) >= 69 and 
                len(line2) >= 69):
                
                try:
                    norad_id = int(line1[2:7].strip())
                    
                    satellite_data = {
                        'name': name_line,
                        'norad_id': norad_id,
                        'line1': line1,
                        'line2': line2
                    }
                    
                    satellites.append(satellite_data)
                    
                except ValueError:
                    pass  # 跳過無效的 NORAD ID
            
            i += 3
                
    except Exception as e:
        print(f"❌ 載入文件失敗 {tle_file}: {e}")
        
    return satellites

def analyze_sgp4_processing():
    """分析 SGP4 處理邏輯"""
    print("\n🚀 分析 SGP4 處理邏輯")
    print("=" * 60)
    
    try:
        # 嘗試導入 SGP4 相關模組
        from netstack.docker.build_with_phase0_data_refactored import Phase25DataPreprocessor
        
        processor = Phase25DataPreprocessor()
        
        print("✅ 成功載入 Phase25DataPreprocessor")
        print(f"   觀測座標: ({processor.observer_lat:.5f}°, {processor.observer_lon:.5f}°)")
        print(f"   時間間隔: {processor.time_step_seconds} 秒")
        print(f"   SGP4 啟用: {processor.enable_sgp4}")
        print(f"   支援星座: {processor.supported_constellations}")
        
        # 掃描 TLE 數據
        scan_result = processor.scan_tle_data()
        
        print("\n📊 TLE 數據掃描結果:")
        print(f"   總星座數: {scan_result['total_constellations']}")
        print(f"   總文件數: {scan_result['total_files']}")
        print(f"   總衛星數: {scan_result['total_satellites']}")
        
        for constellation, data in scan_result['constellations'].items():
            print(f"   {constellation}: {data['satellites']} 顆衛星, {data['files']} 個文件")
            
        return scan_result
        
    except ImportError as e:
        print(f"❌ 無法導入處理器: {e}")
        return None
    except Exception as e:
        print(f"❌ 分析失敗: {e}")
        return None

def verify_documented_numbers():
    """驗證文檔中提到的數量"""
    print("\n📚 驗證文檔中提到的數量")
    print("=" * 60)
    
    documented_numbers = {
        'starlink_expected': 8042,  # 文檔中的數字
        'oneweb_expected': 651,     # 文檔中的數字  
        'total_expected': 8693,     # 8042 + 651
        'processed_claimed': 8695   # 文檔中聲稱處理的數量
    }
    
    # 實際檢測的數量
    total_actual, constellation_data = test_tle_data_loading()
    
    actual_numbers = {
        'starlink_actual': constellation_data.get('starlink', {}).get('satellites', 0),
        'oneweb_actual': constellation_data.get('oneweb', {}).get('satellites', 0),
        'total_actual': total_actual
    }
    
    print("📊 數量對比:")
    print(f"   Starlink - 文檔: {documented_numbers['starlink_expected']}, 實際: {actual_numbers['starlink_actual']}")
    print(f"   OneWeb   - 文檔: {documented_numbers['oneweb_expected']}, 實際: {actual_numbers['oneweb_actual']}")
    print(f"   總計     - 文檔: {documented_numbers['total_expected']}, 實際: {actual_numbers['total_actual']}")
    print(f"   聲稱處理 - 文檔: {documented_numbers['processed_claimed']}")
    
    # 分析差異
    print("\n🔍 差異分析:")
    starlink_diff = actual_numbers['starlink_actual'] - documented_numbers['starlink_expected']
    oneweb_diff = actual_numbers['oneweb_actual'] - documented_numbers['oneweb_expected']
    total_diff = actual_numbers['total_actual'] - documented_numbers['total_expected']
    processed_diff = actual_numbers['total_actual'] - documented_numbers['processed_claimed']
    
    print(f"   Starlink 差異: {starlink_diff:+d}")
    print(f"   OneWeb 差異: {oneweb_diff:+d}")
    print(f"   總計差異: {total_diff:+d}")
    print(f"   與聲稱處理數差異: {processed_diff:+d}")
    
    return {
        'documented': documented_numbers,
        'actual': actual_numbers,
        'differences': {
            'starlink': starlink_diff,
            'oneweb': oneweb_diff, 
            'total': total_diff,
            'processed': processed_diff
        }
    }

def main():
    """主測試函數"""
    print("🧪 TLE 數據處理驗證測試")
    print("=" * 80)
    print("目的: 驗證第1階段 SGP4 是否真的處理全量衛星數據")
    print("=" * 80)
    
    # 1. 測試 TLE 數據載入
    total_satellites, constellation_data = test_tle_data_loading()
    
    # 2. 分析 SGP4 處理邏輯
    sgp4_result = analyze_sgp4_processing()
    
    # 3. 驗證文檔數量
    verification_result = verify_documented_numbers()
    
    print("\n" + "=" * 80)
    print("🎯 最終結論")
    print("=" * 80)
    
    if verification_result:
        total_diff = verification_result['differences']['total']
        processed_diff = verification_result['differences']['processed']
        
        if abs(total_diff) <= 50:  # 允許小幅差異
            print("✅ 基本符合: 實際處理的衛星數量與文檔基本一致")
        else:
            print("⚠️  存在顯著差異: 實際處理數量與文檔不符")
        
        if abs(processed_diff) <= 50:
            print("✅ 處理聲稱準確: 聲稱處理的數量基本正確")
        else:
            print("❌ 處理聲稱有誤: 聲稱處理的數量與實際不符")
        
        # 回答關鍵問題
        print("\n🔍 回答關鍵問題:")
        print("   Q: 第1階段是否處理全量衛星數據?")
        
        actual_total = verification_result['actual']['total_actual']
        if actual_total > 8000:
            print(f"   A: 是的，處理了 {actual_total} 顆衛星，接近全量")
            print("      這包含了幾乎所有可用的 Starlink 和 OneWeb 衛星")
        else:
            print(f"   A: 不是，只處理了 {actual_total} 顆衛星，不是全量")
            
        print("\n   Q: 為什麼不是真正的全量?")
        if verification_result['actual']['starlink_actual'] > verification_result['documented']['starlink_expected']:
            print("   A: 實際上是超過文檔預期的！可能是:")
            print("      1. TLE 數據更新，衛星數量增加")
            print("      2. 文檔數字是舊數據")
            print("      3. 包含了一些測試或已失效的衛星")
        else:
            print("   A: 可能的原因:")
            print("      1. TLE 文件解析時跳過了無效或損壞的記錄")
            print("      2. 某些衛星的 TLE 格式不符合標準")
            print("      3. 程式有篩選邏輯過濾掉某些衛星")

if __name__ == "__main__":
    main()