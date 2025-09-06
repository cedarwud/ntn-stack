#!/usr/bin/env python3
"""
簡單的管道同步執行腳本
快速同步所有六個階段的時間戳
"""
import subprocess
import sys
from datetime import datetime

def run_command(cmd, stage_name):
    """執行命令並輸出結果"""
    print(f"\n🔄 執行 {stage_name}...")
    print(f"命令: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            print(f"✅ {stage_name} 完成")
            return True
        else:
            print(f"❌ {stage_name} 失敗")
            print(f"錯誤: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏰ {stage_name} 超時")
        return False
    except Exception as e:
        print(f"❌ {stage_name} 異常: {e}")
        return False

def cleanup_previous_outputs():
    """清理所有階段的舊輸出文件"""
    print("\n🗑️ 清理階段：刪除所有舊輸出文件")
    print("-" * 40)
    
    # 要清理的輸出文件和目錄
    cleanup_paths = [
        "/app/data/tle_calculation_outputs/",
        "/app/data/intelligent_filtering_outputs/", 
        "/app/data/signal_analysis_outputs/",
        "/app/data/timeseries_preprocessing_outputs/",
        "/app/data/data_integration_outputs/",
        "/app/data/dynamic_pool_planning_outputs/",
        "/app/data/tle_orbital_calculation_output.json",
        "/app/data/signal_event_analysis_output.json",
        "/app/data/data_integration_output.json",
        "/app/data/enhanced_dynamic_pools_output.json"
    ]
    
    cleaned_count = 0
    for path in cleanup_paths:
        cmd = f"docker exec netstack-api rm -rf {path}"
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                cleaned_count += 1
                print(f"✅ 已清理: {path}")
            else:
                print(f"⚠️ 清理失敗: {path} ({result.stderr.strip()})")
        except Exception as e:
            print(f"❌ 清理異常: {path} - {e}")
    
    print(f"🧹 清理完成: {cleaned_count}/{len(cleanup_paths)} 項目")
    
    # 重新創建輸出目錄
    output_dirs = [
        "/app/data/tle_calculation_outputs",
        "/app/data/intelligent_filtering_outputs", 
        "/app/data/signal_analysis_outputs",
        "/app/data/timeseries_preprocessing_outputs",
        "/app/data/data_integration_outputs",
        "/app/data/dynamic_pool_planning_outputs"
    ]
    
    for dir_path in output_dirs:
        cmd = f"docker exec netstack-api mkdir -p {dir_path}"
        subprocess.run(cmd, shell=True, capture_output=True)
        print(f"📁 已創建目錄: {dir_path}")
    
    return cleaned_count

def main():
    print("🚀 開始同步執行六階段管道")
    print(f"⏰ 開始時間: {datetime.now()}")
    print("=" * 60)
    
    # 1. 清理舊輸出文件
    cleanup_previous_outputs()
    
    # 基礎命令前綴
    base_cmd = "docker exec -w /app/src netstack-api python -c"
    
    # 各階段命令
    stages = [
        ("階段1：TLE軌道計算", f'{base_cmd} "import sys; sys.path.insert(0, \\"/app/src\\"); from stages.orbital_calculation_processor import Stage1OrbitalProcessor; processor = Stage1OrbitalProcessor(); processor.process()"'),
        ("階段2：智能篩選", f'{base_cmd} "import sys; sys.path.insert(0, \\"/app/src\\"); from stages.satellite_visibility_filter_processor import Stage2VisibilityFilter; processor = Stage2VisibilityFilter(); processor.process()"'),
        ("階段3：信號分析", f'{base_cmd} "import sys; sys.path.insert(0, \\"/app/src\\"); from stages.signal_analysis_processor import Stage3SignalAnalyzer; processor = Stage3SignalAnalyzer(); processor.process()"'),
        ("階段4：時間序列", f'{base_cmd} "import sys; sys.path.insert(0, \\"/app/src\\"); from stages.timeseries_optimization_processor import Stage4TimeseriesProcessor; processor = Stage4TimeseriesProcessor(); processor.process()"'),
        ("階段5：數據整合", f'{base_cmd} "import sys; sys.path.insert(0, \\"/app/src\\"); from stages.data_integration_processor import Stage5IntegrationProcessor; processor = Stage5IntegrationProcessor(); processor.process()"'),
        ("階段6：動態池規劃", f'{base_cmd} "import sys; sys.path.insert(0, \\"/app/src\\"); from stages.dynamic_pool_planner import Stage6DynamicPoolPlanner; processor = Stage6DynamicPoolPlanner(); processor.process()"'),
    ]
    
    success_count = 0
    for stage_name, cmd in stages:
        if run_command(cmd, stage_name):
            success_count += 1
        else:
            print(f"⚠️ {stage_name} 失敗，但繼續執行後續階段...")
    
    print("\n" + "=" * 60)
    print(f"🏁 管道執行完成: {success_count}/{len(stages)} 個階段成功")
    print(f"⏰ 結束時間: {datetime.now()}")
    
    if success_count == len(stages):
        print("✅ 全部階段同步完成！")
        return 0
    else:
        print("⚠️ 部分階段失敗，請檢查日誌")
        return 1

if __name__ == '__main__':
    sys.exit(main())