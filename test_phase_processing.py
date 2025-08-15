#!/usr/bin/env python3
"""
測試階段一和階段二的完整處理流程
用真實TLE數據執行全量衛星計算
"""
import sys
import os
import json
from pathlib import Path
from datetime import datetime

# 添加路徑以便導入模組
sys.path.insert(0, '/home/sat/ntn-stack/netstack')

def test_stage1_full_processing():
    """測試階段一全量處理"""
    print("🚀 開始階段一：全量TLE數據載入與SGP4軌道計算")
    print("=" * 60)
    
    # 導入階段一處理器
    from netstack.src.stages.stage1_tle_processor import Stage1TLEProcessor
    
    # 初始化處理器 (debug_mode=False 表示全量處理)
    processor = Stage1TLEProcessor(
        tle_data_dir="/home/sat/ntn-stack/netstack/tle_data",
        output_dir="/home/sat/ntn-stack/data",
        debug_mode=False  # 全量處理模式
    )
    
    print(f"📊 處理模式: 全量處理 (預期8,735顆衛星)")
    
    # 執行階段一處理
    start_time = datetime.now()
    stage1_data = processor.process_stage1()
    end_time = datetime.now()
    
    print(f"⏱️ 階段一處理時間: {(end_time - start_time).total_seconds():.1f}秒")
    
    # 統計結果
    total_satellites = stage1_data['metadata']['total_satellites']
    total_constellations = stage1_data['metadata']['total_constellations']
    
    print("📈 階段一處理結果:")
    print(f"   總衛星數量: {total_satellites}")
    print(f"   星座數量: {total_constellations}")
    
    # 詳細統計每個星座
    for constellation_name, constellation_data in stage1_data['constellations'].items():
        satellite_count = constellation_data.get('satellite_count', 0)
        orbit_satellites = len(constellation_data.get('orbit_data', {}).get('satellites', {}))
        print(f"   {constellation_name}: {satellite_count} 顆 (軌道計算完成: {orbit_satellites})")
    
    print("✅ 階段一完成")
    return stage1_data

def test_stage2_filtering(stage1_data):
    """測試階段二智能篩選"""
    print("\n🎯 開始階段二：智能衛星篩選")
    print("=" * 60)
    
    # 導入階段二處理器
    from netstack.src.stages.stage2_filter_processor import Stage2FilterProcessor
    
    # 初始化處理器
    processor = Stage2FilterProcessor(
        observer_lat=24.9441667,
        observer_lon=121.3713889,
        input_dir="/home/sat/ntn-stack/data",
        output_dir="/home/sat/ntn-stack/data"
    )
    
    # 執行階段二處理 (使用記憶體傳遞，不保存文件)
    start_time = datetime.now()
    stage2_data = processor.process_stage2(
        stage1_data=stage1_data,  # 使用記憶體中的階段一數據
        save_output=True  # 保存輸出以便檢查
    )
    end_time = datetime.now()
    
    print(f"⏱️ 階段二處理時間: {(end_time - start_time).total_seconds():.1f}秒")
    
    # 統計篩選結果
    filtering_results = stage2_data['metadata'].get('unified_filtering_results', {})
    total_selected = filtering_results.get('total_selected', 0)
    starlink_selected = filtering_results.get('starlink_selected', 0) 
    oneweb_selected = filtering_results.get('oneweb_selected', 0)
    
    print("📈 階段二篩選結果:")
    print(f"   輸入衛星數量: {stage1_data['metadata']['total_satellites']}")
    print(f"   篩選後總數量: {total_selected}")
    print(f"   Starlink篩選: {starlink_selected}")
    print(f"   OneWeb篩選: {oneweb_selected}")
    
    # 計算篩選比例
    input_total = stage1_data['metadata']['total_satellites']
    if input_total > 0:
        selection_ratio = (total_selected / input_total) * 100
        print(f"   篩選比例: {selection_ratio:.1f}%")
    
    print("✅ 階段二完成")
    return stage2_data

def check_output_files():
    """檢查輸出文件大小"""
    print("\n📁 檢查輸出文件:")
    print("=" * 60)
    
    data_dir = Path("/home/sat/ntn-stack/data")
    files_to_check = [
        "stage2_intelligent_filtered_output.json"
    ]
    
    total_size = 0
    for filename in files_to_check:
        filepath = data_dir / filename
        if filepath.exists():
            file_size = filepath.stat().st_size
            size_mb = file_size / (1024 * 1024)
            total_size += file_size
            print(f"   {filename}: {size_mb:.2f} MB")
            
            # 如果是JSON文件，嘗試讀取並統計內容
            if filename.endswith('.json'):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if 'constellations' in data:
                        for const_name, const_data in data['constellations'].items():
                            satellites = const_data.get('satellites', [])
                            print(f"     {const_name}: {len(satellites)} 顆衛星")
                
                except Exception as e:
                    print(f"     讀取JSON失敗: {e}")
        else:
            print(f"   {filename}: 不存在")
    
    total_size_mb = total_size / (1024 * 1024)
    print(f"\n📊 總輸出大小: {total_size_mb:.2f} MB")
    
    return total_size_mb

def main():
    """主執行函數"""
    print("🛰️ LEO衛星數據預處理流程測試")
    print("實際TLE數據全量處理驗證")
    print("=" * 60)
    
    try:
        # 執行階段一
        stage1_data = test_stage1_full_processing()
        
        # 執行階段二  
        stage2_data = test_stage2_filtering(stage1_data)
        
        # 檢查輸出文件
        total_output_size = check_output_files()
        
        print("\n🎉 處理流程驗證完成!")
        print("=" * 60)
        print(f"✅ 階段一: {stage1_data['metadata']['total_satellites']} 顆衛星軌道計算完成")
        
        filtering_results = stage2_data['metadata'].get('unified_filtering_results', {})
        print(f"✅ 階段二: {filtering_results.get('total_selected', 0)} 顆衛星篩選完成")
        print(f"    - Starlink: {filtering_results.get('starlink_selected', 0)} 顆")
        print(f"    - OneWeb: {filtering_results.get('oneweb_selected', 0)} 顆")
        
        print(f"📁 輸出文件總大小: {total_output_size:.2f} MB")
        
        return True
        
    except Exception as e:
        print(f"❌ 處理失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)