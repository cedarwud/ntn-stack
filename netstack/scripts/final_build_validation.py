#!/usr/bin/env python3
"""
映像檔建構最終驗證腳本
在建構結束前自動執行，生成最終建構狀態報告
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime, timezone
import argparse
import time

def clear_old_reports(data_dir="/app/data"):
    """清理舊的建構報告"""
    data_path = Path(data_dir)
    
    print("🗑️ 清理舊的建構報告...")
    
    old_reports = [
        ".build_status",
        ".build_validation_status", 
        ".final_build_report.json",
        ".build_summary.txt"
    ]
    
    for report_file in old_reports:
        report_path = data_path / report_file
        if report_path.exists():
            try:
                report_path.unlink()
                print(f"   ✅ 已刪除舊報告: {report_file}")
            except Exception as e:
                print(f"   ⚠️ 刪除失敗: {report_file} - {e}")
        else:
            print(f"   📝 舊報告不存在: {report_file}")

def generate_final_build_report(data_dir="/app/data"):
    """生成最終建構報告"""
    
    build_start_time = time.time()
    current_time = datetime.now(timezone.utc)
    
    print("=" * 70)
    print("🏗️ 映像檔建構最終驗證報告")
    print("=" * 70)
    print(f"⏰ 報告生成時間: {current_time.isoformat()}")
    print()
    
    data_path = Path(data_dir)
    
    # 1. 檢查驗證快照
    print("🔍 第一步：檢查驗證快照...")
    validation_dir = data_path / "validation_snapshots"
    validation_results = {}
    completed_stages = 0
    total_processing_time = 0
    
    if validation_dir.exists():
        print(f"   📁 驗證快照目錄: {validation_dir}")
        
        for stage in range(1, 7):
            snapshot_file = validation_dir / f"stage{stage}_validation.json"
            if snapshot_file.exists():
                try:
                    with open(snapshot_file, 'r', encoding='utf-8') as f:
                        snapshot = json.load(f)
                    
                    stage_status = snapshot.get('status', 'unknown')
                    validation_passed = snapshot.get('validation', {}).get('passed', False)
                    duration = snapshot.get('duration_seconds', 0)
                    stage_name = snapshot.get('stageName', f'階段{stage}')
                    timestamp = snapshot.get('timestamp', '')
                    
                    if stage_status == 'completed' and validation_passed:
                        print(f"   ✅ 階段{stage}: {stage_name} - 完成 ({duration:.1f}秒)")
                        completed_stages += 1
                        total_processing_time += duration
                        status = 'success'
                    else:
                        print(f"   ❌ 階段{stage}: {stage_name} - 失敗 (狀態: {stage_status}, 驗證: {validation_passed})")
                        status = 'failed'
                    
                    validation_results[stage] = {
                        'stage_name': stage_name,
                        'status': status,
                        'duration_seconds': duration,
                        'validation_passed': validation_passed,
                        'timestamp': timestamp,
                        'snapshot_file': str(snapshot_file)
                    }
                    
                except Exception as e:
                    print(f"   ⚠️ 階段{stage}: 驗證快照讀取錯誤 - {e}")
                    validation_results[stage] = {
                        'status': 'error',
                        'error': str(e)
                    }
            else:
                print(f"   ❌ 階段{stage}: 驗證快照缺失")
                break  # 即時驗證架構下，缺失意味著該階段未執行
    else:
        print(f"   ❌ 驗證快照目錄不存在: {validation_dir}")
    
    # 2. 檢查輸出檔案
    print("\n📁 第二步：檢查輸出檔案...")
    expected_outputs = {
        1: {
            'path': 'tle_orbital_calculation_output.json',
            'description': 'SGP4軌道計算結果',
            'min_size_mb': 1000  # 至少1GB
        },
        2: {
            'path': 'intelligent_filtered_output.json',
            'description': '智能衛星篩選結果',
            'min_size_mb': 10
        },
        3: {
            'path': 'signal_event_analysis_output.json',
            'description': '信號品質分析結果',
            'min_size_mb': 50
        },
        4: {
            'path': 'enhanced_timeseries_output.json',
            'description': '時間序列預處理結果',
            'min_size_mb': 30,
            'is_directory': True
        },
        5: {
            'path': 'data_integration_output.json',
            'description': '數據整合結果',
            'min_size_mb': 50
        },
        6: {
            'path': 'enhanced_dynamic_pools_output.json',
            'description': '動態池規劃結果',
            'min_size_mb': 5
        }
    }
    
    output_status = {}
    valid_outputs = 0
    
    for stage, config in expected_outputs.items():
        output_path = data_path / config['path']
        
        if output_path.exists():
            if config.get('is_directory', False):
                # 目錄檢查
                json_files = list(output_path.glob("*.json"))
                if json_files:
                    total_size_mb = sum(f.stat().st_size for f in json_files) / (1024 * 1024)
                    if total_size_mb >= config['min_size_mb']:
                        print(f"   ✅ 階段{stage}: {config['description']} - {len(json_files)}個檔案 ({total_size_mb:.1f}MB)")
                        valid_outputs += 1
                        output_status[stage] = 'valid'
                    else:
                        print(f"   ⚠️ 階段{stage}: {config['description']} - 檔案太小 ({total_size_mb:.1f}MB < {config['min_size_mb']}MB)")
                        output_status[stage] = 'size_error'
                else:
                    print(f"   ❌ 階段{stage}: {config['description']} - 目錄存在但無檔案")
                    output_status[stage] = 'empty'
            else:
                # 檔案檢查
                size_mb = output_path.stat().st_size / (1024 * 1024)
                if size_mb >= config['min_size_mb']:
                    print(f"   ✅ 階段{stage}: {config['description']} - {size_mb:.1f}MB")
                    valid_outputs += 1
                    output_status[stage] = 'valid'
                else:
                    print(f"   ⚠️ 階段{stage}: {config['description']} - 檔案太小 ({size_mb:.1f}MB < {config['min_size_mb']}MB)")
                    output_status[stage] = 'size_error'
        else:
            print(f"   ❌ 階段{stage}: {config['description']} - 檔案不存在")
            output_status[stage] = 'missing'
    
    # 3. 計算總體狀態
    print("\n📊 第三步：計算總體建構狀態...")
    
    total_expected_stages = 6
    total_expected_outputs = 6
    
    # 判斷總體狀態
    if completed_stages == total_expected_stages and valid_outputs == total_expected_outputs:
        overall_status = "SUCCESS"
        status_emoji = "🎉"
        status_message = "完全成功"
    elif completed_stages > 0 and valid_outputs > 0:
        overall_status = "PARTIAL"
        status_emoji = "⚠️"
        status_message = "部分成功"
    else:
        overall_status = "FAILED"
        status_emoji = "❌"
        status_message = "建構失敗"
    
    # 4. 生成詳細報告
    report_generation_time = time.time()
    
    detailed_report = {
        'build_validation_metadata': {
            'report_version': '1.0.0',
            'validation_framework': 'immediate_stage_validation',
            'report_generation_time': current_time.isoformat(),
            'report_generation_duration_seconds': round(report_generation_time - build_start_time, 2)
        },
        'overall_status': {
            'status': overall_status,
            'status_message': status_message,
            'completed_stages': completed_stages,
            'total_expected_stages': total_expected_stages,
            'valid_outputs': valid_outputs,
            'total_expected_outputs': total_expected_outputs,
            'total_processing_time_seconds': round(total_processing_time, 2),
            'total_processing_time_minutes': round(total_processing_time / 60, 1)
        },
        'stage_validation_details': validation_results,
        'output_file_details': {},
        'build_recommendations': []
    }
    
    # 加入輸出檔案詳細資訊
    for stage, config in expected_outputs.items():
        output_path = data_path / config['path']
        file_info = {
            'expected_path': config['path'],
            'description': config['description'],
            'status': output_status.get(stage, 'unknown')
        }
        
        if output_path.exists():
            if config.get('is_directory', False):
                json_files = list(output_path.glob("*.json"))
                file_info['file_count'] = len(json_files)
                file_info['total_size_mb'] = round(sum(f.stat().st_size for f in json_files) / (1024 * 1024), 2)
            else:
                file_info['size_mb'] = round(output_path.stat().st_size / (1024 * 1024), 2)
                file_info['last_modified'] = datetime.fromtimestamp(output_path.stat().st_mtime, timezone.utc).isoformat()
        
        detailed_report['output_file_details'][stage] = file_info
    
    # 5. 生成建議
    if overall_status == "SUCCESS":
        detailed_report['build_recommendations'] = [
            "✅ 建構完全成功，系統已就緒使用",
            "💡 無需額外操作",
            "🎯 所有六階段處理和驗證完成"
        ]
    elif overall_status == "PARTIAL":
        failed_stage = completed_stages + 1
        detailed_report['build_recommendations'] = [
            f"⚠️ 建構部分成功，在階段{failed_stage}停止",
            "🔧 容器啟動後執行運行時重新處理:",
            "   docker exec netstack-api python /app/scripts/run_six_stages_with_validation.py",
            f"📊 已完成 {completed_stages}/{total_expected_stages} 個階段"
        ]
    else:
        detailed_report['build_recommendations'] = [
            "❌ 建構失敗，需要檢查配置",
            "🔍 建議檢查項目:",
            "   - TLE 數據是否正確載入 (/app/tle_data/)",
            "   - Docker 記憶體限制是否足夠 (建議 6GB+)",
            "   - 建構腳本配置是否正確",
            "🔧 或在容器啟動後執行完整重新處理"
        ]
    
    # 6. 保存報告
    print("\n💾 第四步：保存建構報告...")
    
    # JSON詳細報告
    json_report_path = data_path / ".final_build_report.json"
    with open(json_report_path, 'w', encoding='utf-8') as f:
        json.dump(detailed_report, f, indent=2, ensure_ascii=False)
    print(f"   ✅ 詳細JSON報告: {json_report_path}")
    
    # 簡化狀態檔案 (向後相容)
    status_file_path = data_path / ".build_status"
    with open(status_file_path, 'w', encoding='utf-8') as f:
        f.write(f"BUILD_OVERALL_STATUS={overall_status}\n")
        if overall_status == "SUCCESS":
            f.write("BUILD_SUCCESS=true\n")
            f.write("BUILD_IMMEDIATE_VALIDATION_PASSED=true\n")
        elif overall_status == "PARTIAL":
            f.write("BUILD_PARTIAL_SUCCESS=true\n")
            f.write(f"BUILD_COMPLETED_STAGES={completed_stages}\n")
            f.write("RUNTIME_PROCESSING_REQUIRED=true\n")
        else:
            f.write("BUILD_FAILED=true\n")
            f.write("RUNTIME_PROCESSING_REQUIRED=true\n")
        
        f.write("BUILD_VALIDATION_MODE=immediate\n")
        f.write(f"BUILD_TIMESTAMP={current_time.isoformat()}\n")
        f.write(f"BUILD_PROCESSING_TIME_SECONDS={total_processing_time:.2f}\n")
        f.write(f"BUILD_COMPLETED_STAGES={completed_stages}\n")
        f.write(f"BUILD_VALID_OUTPUTS={valid_outputs}\n")
    
    print(f"   ✅ 狀態檔案: {status_file_path}")
    
    # 簡化文本報告
    summary_report_path = data_path / ".build_summary.txt"
    with open(summary_report_path, 'w', encoding='utf-8') as f:
        f.write("NTN Stack 映像檔建構狀態報告\n")
        f.write("=" * 50 + "\n")
        f.write(f"報告生成時間: {current_time.strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        f.write(f"建構狀態: {status_emoji} {status_message}\n")
        f.write(f"完成階段: {completed_stages}/{total_expected_stages}\n")
        f.write(f"有效輸出: {valid_outputs}/{total_expected_outputs}\n")
        f.write(f"總處理時間: {total_processing_time:.1f} 秒 ({total_processing_time/60:.1f} 分鐘)\n")
        f.write("\n")
        
        if detailed_report['build_recommendations']:
            f.write("建議操作:\n")
            for recommendation in detailed_report['build_recommendations']:
                f.write(f"  {recommendation}\n")
    
    print(f"   ✅ 文本摘要報告: {summary_report_path}")
    
    # 7. 最終狀態顯示
    print("\n" + "=" * 70)
    print("📋 映像檔建構最終驗證結果")
    print("=" * 70)
    print(f"{status_emoji} 建構狀態: {status_message}")
    print(f"📊 完成階段: {completed_stages}/{total_expected_stages}")
    print(f"📁 有效輸出: {valid_outputs}/{total_expected_outputs}")
    print(f"⏱️ 總處理時間: {total_processing_time:.1f} 秒 ({total_processing_time/60:.1f} 分鐘)")
    print(f"📅 報告時間: {current_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    print("\n💡 建議操作:")
    for recommendation in detailed_report['build_recommendations']:
        print(f"   {recommendation}")
    
    print(f"\n📄 詳細報告位置:")
    print(f"   JSON詳細報告: {json_report_path}")
    print(f"   狀態檔案: {status_file_path}")
    print(f"   文本摘要: {summary_report_path}")
    
    return overall_status == "SUCCESS", detailed_report

def main():
    """主程序"""
    parser = argparse.ArgumentParser(description='映像檔建構最終驗證')
    parser.add_argument('--data-dir', default='/app/data', help='數據目錄')
    parser.add_argument('--exit-on-fail', action='store_true', help='建構驗證失敗時退出')
    parser.add_argument('--clear-old', action='store_true', default=True, help='清理舊報告')
    
    args = parser.parse_args()
    
    print("🏗️ 映像檔建構最終驗證腳本啟動")
    print(f"📁 數據目錄: {args.data_dir}")
    print(f"🗑️ 清理舊報告: {'是' if args.clear_old else '否'}")
    print(f"❌ 失敗時退出: {'是' if args.exit_on_fail else '否'}")
    print()
    
    try:
        if args.clear_old:
            clear_old_reports(args.data_dir)
            print()
        
        success, report = generate_final_build_report(args.data_dir)
        
        if args.exit_on_fail and not success:
            print("\n💥 建構驗證失敗，退出映像檔建構...")
            sys.exit(1)
        else:
            print(f"\n✅ 建構驗證完成，狀態: {'成功' if success else '需要運行時處理'}")
            sys.exit(0)
            
    except Exception as e:
        print(f"\n💥 建構驗證腳本執行錯誤: {e}")
        import traceback
        traceback.print_exc()
        
        if args.exit_on_fail:
            sys.exit(1)
        else:
            sys.exit(2)

if __name__ == '__main__':
    main()