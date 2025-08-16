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
        
        # Skip build-time precomputation - do everything at runtime
        print('ℹ️ LEO重構系統：跳過建構時預計算，將在運行時使用全量數據處理')
        print('🎯 運行時將使用--full-test模式處理8736顆真實衛星')
        return True
    except Exception as e:
        print(f'❌ LEO重構系統執行失敗: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)