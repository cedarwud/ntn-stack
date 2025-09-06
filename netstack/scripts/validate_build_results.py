#!/usr/bin/env python3
"""
建構時六階段驗證結果檢查器
檢查所有階段的驗證快照，確保沒有驗證失敗
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

def check_validation_snapshots(data_dir="/app/data"):
    """檢查所有階段的驗證快照"""
    
    data_path = Path(data_dir)
    validation_dir = data_path / "validation_snapshots"
    
    print("🔍 檢查建構時驗證快照...")
    print(f"驗證目錄: {validation_dir}")
    
    if not validation_dir.exists():
        print("❌ 驗證快照目錄不存在")
        return False, "驗證目錄不存在"
    
    # 定義預期的階段
    expected_stages = {
        1: "stage1_validation.json",
        2: "stage2_validation.json", 
        3: "stage3_validation.json",
        4: "stage4_validation.json",
        5: "stage5_validation.json",
        6: "stage6_validation.json"
    }
    
    validation_results = {}
    failed_stages = []
    missing_stages = []
    
    for stage_num, filename in expected_stages.items():
        snapshot_file = validation_dir / filename
        
        if not snapshot_file.exists():
            print(f"⚠️ Stage {stage_num} 驗證快照缺失: {filename}")
            missing_stages.append(stage_num)
            continue
            
        try:
            with open(snapshot_file, 'r', encoding='utf-8') as f:
                snapshot = json.load(f)
            
            stage_passed = snapshot.get('validation', {}).get('passed', False)
            stage_status = snapshot.get('status', 'unknown')
            
            validation_results[stage_num] = {
                'file': filename,
                'passed': stage_passed,
                'status': stage_status,
                'snapshot': snapshot
            }
            
            if not stage_passed or stage_status != 'completed':
                failed_stages.append(stage_num)
                print(f"❌ Stage {stage_num} 驗證失敗:")
                print(f"   狀態: {stage_status}")
                print(f"   驗證通過: {stage_passed}")
                
                # 顯示失敗的檢查項目
                failed_checks = []
                all_checks = snapshot.get('validation', {}).get('allChecks', {})
                for check_name, check_result in all_checks.items():
                    if not check_result:
                        failed_checks.append(check_name)
                
                if failed_checks:
                    print(f"   失敗檢查: {', '.join(failed_checks)}")
            else:
                print(f"✅ Stage {stage_num} 驗證通過")
                
        except Exception as e:
            print(f"❌ Stage {stage_num} 驗證快照讀取失敗: {e}")
            failed_stages.append(stage_num)
    
    # 生成總結報告
    total_stages = len(expected_stages)
    completed_stages = len(validation_results)
    passed_stages = sum(1 for r in validation_results.values() if r['passed'])
    
    print(f"\n📊 建構驗證總結:")
    print(f"   預期階段: {total_stages}")
    print(f"   完成階段: {completed_stages}")
    print(f"   驗證通過: {passed_stages}")
    print(f"   驗證失敗: {len(failed_stages)}")
    print(f"   缺失階段: {len(missing_stages)}")
    
    # 判斷整體成功
    build_success = (len(failed_stages) == 0 and len(missing_stages) == 0)
    
    if build_success:
        print("✅ 所有階段驗證通過！建構成功。")
        return True, "所有階段驗證通過"
    else:
        error_msg = f"驗證失敗階段: {failed_stages}, 缺失階段: {missing_stages}"
        print(f"❌ 建構驗證失敗: {error_msg}")
        return False, error_msg

def create_build_status_file(success, message, data_dir="/app/data"):
    """創建建構狀態文件"""
    status_file = Path(data_dir) / ".build_validation_status"
    
    status_data = {
        "validation_success": success,
        "validation_message": message,
        "validation_timestamp": datetime.now(timezone.utc).isoformat(),
        "build_validation_completed": True
    }
    
    with open(status_file, 'w', encoding='utf-8') as f:
        json.dump(status_data, f, indent=2, ensure_ascii=False)
    
    print(f"📝 建構驗證狀態已保存: {status_file}")

def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description='建構時六階段驗證檢查')
    parser.add_argument('--data-dir', default='/app/data', help='數據目錄')
    parser.add_argument('--exit-on-fail', action='store_true', help='驗證失敗時退出並返回錯誤碼')
    args = parser.parse_args()
    
    print("🏗️ 建構時六階段驗證檢查器")
    print("=" * 50)
    
    success, message = check_validation_snapshots(args.data_dir)
    create_build_status_file(success, message, args.data_dir)
    
    if success:
        print("🎉 建構驗證完成！")
        return 0
    else:
        print("💥 建構驗證失敗！")
        if args.exit_on_fail:
            print("🚨 設定為驗證失敗時退出")
            return 1
        else:
            print("⚠️ 繼續建構，但標記為運行時處理")
            return 0

if __name__ == '__main__':
    sys.exit(main())