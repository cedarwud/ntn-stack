#!/usr/bin/env python3
"""
Enhanced Six-Stage Build Script
建構時執行增強六階段系統，為容器預計算衛星數據
"""

import sys
import asyncio
import os
import argparse

# Add proper Python paths
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/src')

def main():
    try:
        # Check if main pipeline controller exists
        controller_path = '/app/src/leo_core/main_pipeline_controller.py'
        if not os.path.exists(controller_path):
            print(f'❌ 增強六階段主流程控制器不存在: {controller_path}')
            return False
            
        print(f'🔍 增強六階段主流程控制器確認: {controller_path}')
        
        # Import the main pipeline controller
        from src.leo_core.main_pipeline_controller import main as pipeline_main
        
        # Execute Enhanced Six-Stage System with build settings
        print('🛰️ 增強六階段系統：啟動建構時完整處理...')
        
        # Set command line arguments for the script - complete six-stage execution
        original_argv = sys.argv[:]
        sys.argv = ['main_pipeline_controller.py', '--mode', 'full', '--data-dir', '/app/data']
        
        print('🎯 六階段系統執行配置:')
        print('   Stage1-2: 記憶體傳遞模式 (高效處理大數據)')
        print('   Stage3-6: 檔案儲存模式 (篩選後數據)')
        print('   完整流程: TLE載入→智能篩選→信號分析→時間序列→數據整合→動態池規劃')
        
        try:
            asyncio.run(pipeline_main())
        finally:
            # Restore original argv
            sys.argv = original_argv
        print('✅ 增強六階段系統：建構時處理完成')
        return True
        
    except ImportError as e:
        print(f'❌ 導入錯誤: {e}')
        print('💡 這可能是因為相依模組缺失，將在運行時重新嘗試')
        return False
    except Exception as e:
        print(f'❌ 執行錯誤: {e}')
        print('💡 建構時預計算失敗，容器將使用運行時計算')
        return False

if __name__ == '__main__':
    success = main()
    if success:
        print('🎉 六階段建構腳本執行成功')
        sys.exit(0)
    else:
        print('⚠️ 六階段建構腳本執行失敗，容器仍可正常啟動')
        sys.exit(0)  # Don't fail the build, just use runtime computation