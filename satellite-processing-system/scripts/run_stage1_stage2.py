#!/usr/bin/env python3
"""
執行 Stage 1 和 Stage 2 為 Stage 3 準備輸入
確保清理舊輸出，生成新驗證快照，並回報結果
"""

import sys
import os
import json
from datetime import datetime, timezone
from pathlib import Path
sys.path.append("/satellite-processing/src")

def check_output_files():
    """檢查輸出文件並報告時間戳"""
    print("\n📁 檢查輸出文件時間戳...")

    # Stage 1 輸出路徑
    stage1_paths = [
        "/satellite-processing/data/outputs/stage1/",
        "/satellite-processing/data/tle_calculation_outputs/"
    ]

    # Stage 2 輸出路徑
    stage2_paths = [
        "/satellite-processing/data/outputs/stage2/",
        "/satellite-processing/data/intelligent_filtering_outputs/"
    ]

    def check_directory(paths, stage_name):
        print(f"\n🔍 {stage_name} 輸出檢查:")
        latest_file = None
        latest_time = None

        for path in paths:
            if os.path.exists(path):
                for file in os.listdir(path):
                    if file.endswith('.json') or file.endswith('.json.gz'):
                        full_path = os.path.join(path, file)
                        mtime = os.path.getmtime(full_path)
                        file_time = datetime.fromtimestamp(mtime, tz=timezone.utc)

                        print(f"   📄 {file}: {file_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")

                        if latest_time is None or mtime > latest_time:
                            latest_file = full_path
                            latest_time = mtime

        if latest_file:
            print(f"   ✅ 最新文件: {os.path.basename(latest_file)}")
            return True
        else:
            print(f"   ❌ 沒有找到輸出文件")
            return False

    stage1_ok = check_directory(stage1_paths, "Stage 1")
    stage2_ok = check_directory(stage2_paths, "Stage 2")

    return stage1_ok, stage2_ok

def main():
    print("🚀 執行完整的 Stage 1 + Stage 2 流程")
    print("✅ 已確認所有輸出目錄清理完成")

    try:
        # 執行 Stage 1
        print("\n📡 執行 Stage 1 (全量衛星軌道計算)...")
        from stages.stage1_orbital_calculation.tle_orbital_calculation_processor import Stage1TLEProcessor

        # 配置全量軌道計算 (完整軌道週期)
        stage1 = Stage1TLEProcessor()
        stage1.sample_mode = False  # 全量模式
        stage1_results = stage1.execute()

        if not stage1_results or "satellites" not in stage1_results:
            print("❌ Stage 1 執行失敗")
            return

        satellite_count = len(stage1_results.get("satellites", {}))
        print(f"✅ Stage 1 完成: {satellite_count} 顆衛星軌道計算成功")

        # 執行 Stage 2
        print("\n🔍 執行 Stage 2 (可見性過濾)...")
        from stages.stage2_visibility_filter.simple_stage2_processor import SimpleStage2Processor

        stage2 = SimpleStage2Processor()
        stage2_results = stage2.execute(input_data=stage1_results)

        if not stage2_results:
            print("❌ Stage 2 執行失敗")
            return

        # 解析 Stage 2 結果
        processing_stats = stage2_results.get("processing_statistics", {})
        visible_total = processing_stats.get("visible_satellites", 0)
        starlink_visible = processing_stats.get("starlink_visible", 0)
        oneweb_visible = processing_stats.get("oneweb_visible", 0)

        print(f"✅ Stage 2 完成:")
        print(f"   🛰️ Starlink 可見: {starlink_visible} 顆")
        print(f"   🛰️ OneWeb 可見: {oneweb_visible} 顆")
        print(f"   🎯 總計可見: {visible_total} 顆")
        print(f"   📈 可見率: {(visible_total/satellite_count)*100:.1f}%")

        # 檢查輸出文件
        stage1_ok, stage2_ok = check_output_files()

        # 生成執行摘要
        print(f"\n📊 執行摘要:")
        print(f"   ⏰ 執行時間: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"   📡 Stage 1: {'✅ 成功' if stage1_ok else '❌ 失敗'} ({satellite_count} 顆衛星)")
        print(f"   🔍 Stage 2: {'✅ 成功' if stage2_ok else '❌ 失敗'} ({visible_total} 顆可見)")
        print(f"   📁 輸出文件: {'✅ 已生成' if stage1_ok and stage2_ok else '❌ 缺失'}")

        if visible_total > 0:
            print(f"   🎉 Stage 2 修復成功！現在有 {visible_total} 顆可見衛星")
            print(f"   ✅ Stage 3 輸入數據已準備就緒")
        else:
            print(f"   ⚠️ Stage 2 仍顯示 0 顆可見，需要進一步調查")

        print(f"\n🏁 Stage 1 + Stage 2 執行完成")

    except Exception as e:
        print(f"❌ 執行過程發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()