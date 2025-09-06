#!/usr/bin/env python3
"""
建構狀態檢查器
檢查Docker映像檔建構時的六階段處理狀態
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone
import argparse

def check_build_status(data_dir="/app/data"):
    """檢查建構狀態"""
    
    print("🔍 檢查映像檔建構時六階段處理狀態")
    print("=" * 60)
    
    data_path = Path(data_dir)
    
    # 1. 檢查建構狀態檔案
    build_status_file = data_path / ".build_status"
    build_validation_status_file = data_path / ".build_validation_status"
    
    build_status = {}
    build_validation_status = {}
    
    # 讀取建構狀態
    if build_status_file.exists():
        print(f"📄 讀取建構狀態: {build_status_file}")
        try:
            with open(build_status_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        build_status[key] = value
        except Exception as e:
            print(f"⚠️ 建構狀態檔案讀取錯誤: {e}")
    else:
        print(f"❌ 建構狀態檔案不存在: {build_status_file}")
    
    # 讀取建構驗證狀態
    if build_validation_status_file.exists():
        print(f"📄 讀取建構驗證狀態: {build_validation_status_file}")
        try:
            with open(build_validation_status_file, 'r', encoding='utf-8') as f:
                build_validation_status = json.load(f)
        except Exception as e:
            print(f"⚠️ 建構驗證狀態檔案讀取錯誤: {e}")
    else:
        print(f"❌ 建構驗證狀態檔案不存在: {build_validation_status_file}")
    
    print("\n" + "=" * 60)
    print("📊 建構狀態分析結果")
    print("=" * 60)
    
    # 2. 分析建構狀態
    overall_success = False
    detailed_report = []
    
    if build_status.get('BUILD_SUCCESS') == 'true':
        print("✅ 建構狀態: 成功")
        if build_status.get('BUILD_IMMEDIATE_VALIDATION_PASSED') == 'true':
            print("✅ 即時驗證: 通過")
            overall_success = True
            detailed_report.append("所有六階段處理與即時驗證完成")
        else:
            print("⚠️ 即時驗證: 狀態不明")
    elif build_status.get('BUILD_IMMEDIATE_VALIDATION_FAILED') == 'true':
        print("❌ 建構狀態: 即時驗證失敗")
        failed_stage = build_status.get('FAILED_STAGE', '未知')
        print(f"❌ 失敗階段: {failed_stage}")
        detailed_report.append(f"階段{failed_stage}驗證失敗")
    elif build_status.get('BUILD_TIMEOUT') == 'true':
        print("⏰ 建構狀態: 處理超時")
        detailed_report.append("六階段處理超時 (30分鐘限制)")
    elif build_status.get('BUILD_FAILED') == 'true':
        print("❌ 建構狀態: 處理失敗")
        exit_code = build_status.get('BUILD_EXIT_CODE', '未知')
        print(f"❌ 退出碼: {exit_code}")
        detailed_report.append(f"六階段處理失敗 (退出碼: {exit_code})")
    else:
        print("❓ 建構狀態: 未知或未完成")
        detailed_report.append("建構狀態檔案缺失或格式錯誤")
    
    # 3. 檢查驗證快照
    validation_dir = data_path / "validation_snapshots"
    validation_snapshots = []
    
    if validation_dir.exists():
        print(f"\n🔍 檢查驗證快照: {validation_dir}")
        for stage in range(1, 7):
            snapshot_file = validation_dir / f"stage{stage}_validation.json"
            if snapshot_file.exists():
                try:
                    with open(snapshot_file, 'r', encoding='utf-8') as f:
                        snapshot = json.load(f)
                    
                    stage_status = snapshot.get('status', 'unknown')
                    validation_passed = snapshot.get('validation', {}).get('passed', False)
                    
                    if stage_status == 'completed' and validation_passed:
                        print(f"✅ 階段{stage}: 完成且驗證通過")
                        validation_snapshots.append({
                            'stage': stage,
                            'status': 'success',
                            'duration': snapshot.get('duration_seconds', 0)
                        })
                    else:
                        print(f"❌ 階段{stage}: {stage_status}, 驗證: {validation_passed}")
                        validation_snapshots.append({
                            'stage': stage,
                            'status': 'failed',
                            'duration': snapshot.get('duration_seconds', 0)
                        })
                except Exception as e:
                    print(f"⚠️ 階段{stage}驗證快照讀取錯誤: {e}")
                    validation_snapshots.append({
                        'stage': stage,
                        'status': 'error',
                        'error': str(e)
                    })
            else:
                print(f"❌ 階段{stage}: 驗證快照缺失")
                break  # 即時驗證架構下，如果某階段缺失，後續階段不會執行
    else:
        print(f"❌ 驗證快照目錄不存在: {validation_dir}")
    
    # 4. 檢查數據輸出完整性
    print(f"\n📁 檢查數據輸出完整性:")
    expected_outputs = {
        1: "tle_calculation_outputs/tle_orbital_calculation_output.json",
        2: "intelligent_filtering_outputs/intelligent_filtered_output.json", 
        3: "signal_analysis_outputs/signal_event_analysis_output.json",
        4: "timeseries_preprocessing_outputs/",
        5: "data_integration_outputs/data_integration_output.json",
        6: "dynamic_pool_planning_outputs/enhanced_dynamic_pools_output.json"
    }
    
    output_status = {}
    for stage, expected_path in expected_outputs.items():
        full_path = data_path / expected_path
        if full_path.exists():
            if full_path.is_file():
                size_mb = full_path.stat().st_size / (1024 * 1024)
                print(f"✅ 階段{stage}輸出: {expected_path} ({size_mb:.1f}MB)")
                output_status[stage] = 'exists'
            else:
                # 目錄檢查
                files = list(full_path.glob("*.json"))
                if files:
                    total_size = sum(f.stat().st_size for f in files) / (1024 * 1024)
                    print(f"✅ 階段{stage}輸出: {expected_path} ({len(files)}個檔案, {total_size:.1f}MB)")
                    output_status[stage] = 'exists'
                else:
                    print(f"❌ 階段{stage}輸出: {expected_path} (目錄存在但無檔案)")
                    output_status[stage] = 'empty'
        else:
            print(f"❌ 階段{stage}輸出: {expected_path} (不存在)")
            output_status[stage] = 'missing'
    
    # 5. 生成最終報告
    print("\n" + "=" * 60)
    print("📋 最終建構狀態報告")
    print("=" * 60)
    
    completed_stages = len([s for s in validation_snapshots if s['status'] == 'success'])
    total_expected_stages = 6
    
    if overall_success and completed_stages == total_expected_stages:
        print("🎉 建構狀態: 完全成功")
        print(f"✅ 已完成階段: {completed_stages}/{total_expected_stages}")
        print("✅ 即時驗證: 全部通過")
        print("✅ 數據輸出: 完整")
        status = "SUCCESS"
    elif completed_stages > 0:
        print("⚠️ 建構狀態: 部分成功")
        print(f"⚠️ 已完成階段: {completed_stages}/{total_expected_stages}")
        
        if completed_stages < total_expected_stages:
            failed_stage = completed_stages + 1
            print(f"❌ 失敗於階段: {failed_stage}")
        
        print("⚠️ 需要運行時重新處理")
        status = "PARTIAL"
    else:
        print("❌ 建構狀態: 失敗")
        print("❌ 已完成階段: 0/6")
        print("❌ 需要完全重新處理")
        status = "FAILED"
    
    # 6. 建議操作
    print("\n🔧 建議操作:")
    if status == "SUCCESS":
        print("✅ 無需額外操作，系統已就緒")
    elif status == "PARTIAL":
        print("⚠️ 建議在運行時重新執行六階段處理:")
        print("   docker exec netstack-api python /app/scripts/run_six_stages_with_validation.py")
    else:
        print("❌ 建議重新建構映像檔或檢查建構腳本配置")
        print("   檢查 Dockerfile 中的六階段處理調用")
        print("   檢查 TLE 數據是否正確載入")
    
    # 7. 時間信息
    build_timestamp = build_status.get('BUILD_TIMESTAMP')
    if build_timestamp:
        print(f"\n⏰ 建構時間: {build_timestamp}")
    
    validation_timestamp = build_validation_status.get('validation_timestamp')
    if validation_timestamp:
        print(f"⏰ 驗證時間: {validation_timestamp}")
    
    return status == "SUCCESS", {
        'overall_status': status,
        'completed_stages': completed_stages,
        'total_stages': total_expected_stages,
        'validation_snapshots': validation_snapshots,
        'output_status': output_status,
        'detailed_report': detailed_report,
        'build_status': build_status,
        'build_validation_status': build_validation_status
    }

def main():
    """主程序"""
    parser = argparse.ArgumentParser(description='建構狀態檢查器')
    parser.add_argument('--data-dir', default='/app/data', help='數據目錄路徑')
    parser.add_argument('--json', action='store_true', help='輸出JSON格式結果')
    parser.add_argument('--exit-on-fail', action='store_true', help='失敗時退出並返回錯誤碼')
    args = parser.parse_args()
    
    success, report = check_build_status(args.data_dir)
    
    if args.json:
        print("\n" + "=" * 60)
        print("JSON 格式報告:")
        print("=" * 60)
        print(json.dumps(report, indent=2, ensure_ascii=False))
    
    if args.exit_on_fail and not success:
        print("\n💥 建構狀態檢查失敗，退出...")
        sys.exit(1)
    else:
        print(f"\n✅ 建構狀態檢查完成 ({'成功' if success else '有問題'})")
        sys.exit(0)

if __name__ == '__main__':
    main()