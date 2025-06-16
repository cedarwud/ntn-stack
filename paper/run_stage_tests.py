#!/usr/bin/env python3
"""
NTN-Stack 論文復現階段測試統一執行腳本

支援的測試階段：
- 1.2: 同步演算法 (Algorithm 1)
- 1.3: 快速衛星預測演算法 (Algorithm 2)  
- 1.4: UPF 整合與綜合測試
- all: 執行所有階段測試

使用方式:
python paper/run_stage_tests.py --stage 1.2 --comprehensive
python paper/run_stage_tests.py --stage all --comprehensive
"""

import subprocess
import sys
import argparse
from pathlib import Path

def run_stage_test(stage: str, comprehensive: bool = False):
    """執行指定階段的測試"""
    
    stage_configs = {
        "1.2": {
            "script": "paper/1.2_synchronized_algorithm/test_algorithm_1.py",
            "name": "同步演算法 (Algorithm 1)",
            "description": "核心網與 RAN 同步"
        },
        "1.3": {
            "script": "paper/1.3_fast_prediction/test_algorithm_2.py", 
            "name": "快速衛星預測演算法 (Algorithm 2)",
            "description": "地理區塊劃分與衛星選擇"
        },
        "1.4": {
            "script": "paper/1.4_upf_integration/test_14_comprehensive.py",
            "name": "UPF 整合與綜合測試",
            "description": "C 模組整合與完整系統驗證"
        }
    }
    
    if stage not in stage_configs:
        print(f"❌ 不支援的階段: {stage}")
        return False
    
    config = stage_configs[stage]
    script_path = Path(config["script"])
    
    if not script_path.exists():
        print(f"❌ 測試腳本不存在: {script_path}")
        return False
    
    print(f"🚀 執行階段 {stage}: {config['name']}")
    print(f"📝 描述: {config['description']}")
    print("=" * 60)
    
    # 構建命令
    cmd = [sys.executable, str(script_path)]
    if comprehensive:
        cmd.append("--comprehensive")
    
    try:
        # 執行測試
        result = subprocess.run(cmd, cwd=Path.cwd(), check=False)
        
        if result.returncode == 0:
            print(f"\n✅ 階段 {stage} 測試成功")
            return True
        else:
            print(f"\n❌ 階段 {stage} 測試失敗 (返回碼: {result.returncode})")
            return False
            
    except Exception as e:
        print(f"\n💥 執行階段 {stage} 測試時發生錯誤: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description='NTN-Stack 論文復現階段測試統一執行腳本'
    )
    parser.add_argument(
        '--stage', 
        choices=['1.2', '1.3', '1.4', 'all'],
        required=True,
        help='要執行的測試階段'
    )
    parser.add_argument(
        '--comprehensive',
        action='store_true',
        help='執行綜合測試（包含額外驗證）'
    )
    
    args = parser.parse_args()
    
    print("🎯 NTN-Stack 論文復現階段測試")
    print("=" * 60)
    
    if args.stage == "all":
        # 執行所有階段測試
        stages = ["1.2", "1.3", "1.4"]
        results = {}
        
        for stage in stages:
            print(f"\n{'=' * 20} 階段 {stage} {'=' * 20}")
            results[stage] = run_stage_test(stage, args.comprehensive)
        
        # 總結報告
        print("\n" + "=" * 60)
        print("📊 所有階段測試結果總結:")
        
        passed = 0
        for stage, success in results.items():
            status = "✅ 通過" if success else "❌ 失敗"
            print(f"  階段 {stage}: {status}")
            if success:
                passed += 1
        
        total = len(results)
        success_rate = (passed / total) * 100
        
        print(f"\n總成功率: {passed}/{total} ({success_rate:.1f}%)")
        
        if success_rate == 100:
            print("🎉 所有階段測試全部通過！")
            print("✨ NTN-Stack 論文復現第一階段完成")
        else:
            print("⚠️  部分階段測試失敗，建議檢查")
        
        return success_rate == 100
        
    else:
        # 執行單一階段測試
        return run_stage_test(args.stage, args.comprehensive)

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  測試被用戶中斷")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 執行錯誤: {e}")
        sys.exit(1)