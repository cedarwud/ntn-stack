#!/usr/bin/env python3
"""
衛星可見性計算器測試腳本
快速驗證程式的正確性和性能
"""

import subprocess
import sys
import time
import os

def run_test(description, command, expect_success=True):
    """運行單個測試"""
    print(f"\n🧪 測試: {description}")
    print(f"📝 指令: {' '.join(command)}")
    print("-" * 60)

    start_time = time.time()
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )

        elapsed_time = time.time() - start_time

        if result.returncode == 0 and expect_success:
            print(f"✅ 測試通過 ({elapsed_time:.1f}秒)")

            # 顯示部分輸出
            output_lines = result.stdout.split('\n')
            key_lines = [line for line in output_lines if any(keyword in line for keyword in
                        ['最大同時可見', '最小同時可見', '平均可見數量', '覆蓋連續性', '✅', '📊', '🎯'])]

            print("📋 關鍵結果:")
            for line in key_lines[-10:]:  # 最後10行關鍵資訊
                if line.strip():
                    print(f"   {line}")

        elif result.returncode != 0 and not expect_success:
            print(f"✅ 測試通過 (預期失敗)")
        else:
            print(f"❌ 測試失敗 ({elapsed_time:.1f}秒)")
            print(f"返回碼: {result.returncode}")

            if result.stderr:
                print("錯誤輸出:")
                print(result.stderr)

        return result.returncode == 0

    except Exception as e:
        print(f"❌ 測試異常: {e}")
        return False

def main():
    """主測試流程"""
    print("🚀 衛星可見性計算器測試套件")
    print("=" * 60)

    # 檢查Python環境
    print(f"🐍 Python版本: {sys.version}")

    # 檢查必要的庫
    required_modules = ['sgp4', 'skyfield', 'numpy']
    missing_modules = []

    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}: 已安裝")
        except ImportError:
            print(f"❌ {module}: 未安裝")
            missing_modules.append(module)

    if missing_modules:
        print(f"\n❌ 缺少必需模組: {', '.join(missing_modules)}")
        print("請執行: pip install sgp4 skyfield numpy")
        return False

    # 檢查計算器程式
    calculator_path = 'satellite_visibility_calculator.py'
    if not os.path.exists(calculator_path):
        print(f"❌ 找不到計算器程式: {calculator_path}")
        return False

    print(f"✅ 計算器程式: {calculator_path}")

    # 測試案例
    test_cases = [
        {
            'description': '小規模快速測試 (10顆Starlink, 1小時)',
            'command': [
                'python', calculator_path,
                '--constellation', 'starlink',
                '--satellites', '10',
                '--location', 'ntpu',
                '--duration', '1',
                '--interval', '10'
            ],
            'expect_success': True
        },
        {
            'description': '中等規模測試 (50顆Starlink, 2小時)',
            'command': [
                'python', calculator_path,
                '--constellation', 'starlink',
                '--satellites', '50',
                '--location', 'ntpu',
                '--duration', '2',
                '--interval', '10'
            ],
            'expect_success': True
        },
        {
            'description': 'OneWeb星座測試 (30顆OneWeb, 2小時)',
            'command': [
                'python', calculator_path,
                '--constellation', 'oneweb',
                '--satellites', '30',
                '--location', 'ntpu',
                '--duration', '2',
                '--interval', '15'
            ],
            'expect_success': True
        },
        {
            'description': '雙星座測試 (80顆混合, 2小時)',
            'command': [
                'python', calculator_path,
                '--constellation', 'both',
                '--satellites', '80',
                '--location', 'ntpu',
                '--duration', '2',
                '--interval', '15'
            ],
            'expect_success': True
        },
        {
            'description': '自定義位置測試 (台北, 20顆)',
            'command': [
                'python', calculator_path,
                '--constellation', 'starlink',
                '--satellites', '20',
                '--location', 'custom',
                '--lat', '25.0330',
                '--lon', '121.5654',
                '--alt', '10',
                '--duration', '1',
                '--interval', '15'
            ],
            'expect_success': True
        },
        {
            'description': '高仰角門檻測試 (10°)',
            'command': [
                'python', calculator_path,
                '--constellation', 'starlink',
                '--satellites', '30',
                '--location', 'ntpu',
                '--duration', '2',
                '--interval', '10',
                '--elevation', '10.0'
            ],
            'expect_success': True
        },
        {
            'description': '錯誤測試: 無效星座',
            'command': [
                'python', calculator_path,
                '--constellation', 'invalid',
                '--satellites', '10',
                '--location', 'ntpu'
            ],
            'expect_success': False
        },
        {
            'description': '錯誤測試: 缺少自定義座標',
            'command': [
                'python', calculator_path,
                '--constellation', 'starlink',
                '--satellites', '10',
                '--location', 'custom'
            ],
            'expect_success': False
        }
    ]

    # 執行測試
    passed_tests = 0
    total_tests = len(test_cases)

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'=' * 60}")
        print(f"測試 {i}/{total_tests}")

        success = run_test(
            test_case['description'],
            test_case['command'],
            test_case['expect_success']
        )

        if success:
            passed_tests += 1

    # 測試結果摘要
    print(f"\n{'=' * 60}")
    print(f"🎯 測試完成摘要")
    print(f"{'=' * 60}")
    print(f"✅ 通過測試: {passed_tests}/{total_tests}")
    print(f"❌ 失敗測試: {total_tests - passed_tests}/{total_tests}")
    print(f"🎉 成功率: {passed_tests/total_tests*100:.1f}%")

    if passed_tests == total_tests:
        print(f"\n🎉 所有測試通過！程式運行正常。")
        return True
    else:
        print(f"\n⚠️ 部分測試失敗，請檢查錯誤訊息。")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)