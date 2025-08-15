#!/usr/bin/env python3
"""
LEO Restructure Build Script
Executes LEO Phase 1 during Docker build process
"""

import sys
import asyncio
import os

# Add proper Python paths
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/src')
sys.path.insert(0, '/app/src/leo_core')

def main():
    try:
        # Check if leo_core exists
        leo_core_path = '/app/src/leo_core'
        if not os.path.exists(leo_core_path):
            print(f'❌ LEO重構系統路徑不存在: {leo_core_path}')
            return False
            
        # Check if run_phase1.py exists
        run_phase1_path = os.path.join(leo_core_path, 'run_phase1.py')
        if not os.path.exists(run_phase1_path):
            print(f'❌ LEO Phase 1腳本不存在: {run_phase1_path}')
            return False
        
        print(f'🔍 LEO重構系統路徑確認: {leo_core_path}')
        print(f'🔍 LEO Phase 1腳本確認: {run_phase1_path}')
        
        # Import LEO restructure system
        from src.leo_core.run_phase1 import main as leo_main
        
        # Execute LEO Phase 1 with production settings
        print('🛰️ LEO重構系統：啟動Phase 1完整處理...')
        
        # Set command line arguments for the script
        original_argv = sys.argv[:]
        sys.argv = ['run_phase1.py', '--output-dir', '/app/data', '--fast']
        
        try:
            asyncio.run(leo_main())
        finally:
            # Restore original argv
            sys.argv = original_argv
        print('✅ LEO重構系統：Phase 1完成')
        return True
        
    except ImportError as e:
        print(f'❌ LEO重構系統導入失敗: {e}')
        print('📂 可用目錄結構:')
        for root, dirs, files in os.walk('/app/src'):
            level = root.replace('/app/src', '').count(os.sep)
            indent = ' ' * 2 * level
            print(f'{indent}{os.path.basename(root)}/')
        return False
        
    except Exception as e:
        print(f'❌ LEO重構系統執行失敗: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)