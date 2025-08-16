#!/usr/bin/env python3
"""
LEO Restructure Build Script
Executes LEO Phase 1 during Docker build process
"""

import sys
import asyncio
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/src')
sys.path.insert(0, '/app/src/leo_core')

def main():
    try:
        # Import LEO restructure system
        from src.leo_core.main import main as leo_main
        
        # Execute LEO Phase 1 with production settings
        print('🛰️ LEO重構系統：啟動Phase 1完整處理...')
        leo_args = ['--output-dir', '/app/data', '--fast']
        asyncio.run(leo_main(leo_args))
        print('✅ LEO重構系統：Phase 1完成')
        return True
    except Exception as e:
        print(f'❌ LEO重構系統執行失敗: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)