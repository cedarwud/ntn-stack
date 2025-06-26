#!/usr/bin/env python3
"""
統一測試執行器

執行方式:
cd /home/sat/ntn-stack
python paper/core_tests/run_unified_tests.py
"""

import asyncio
import sys
from pathlib import Path

# 添加項目路徑
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from paper.core_tests.test_unified_paper_reproduction import main

if __name__ == "__main__":
    print("🚀 啟動統一論文復現測試")
    print("🎯 整合 Algorithm 1 + 2，提高測試效率")
    print("=" * 60)
    
    try:
        exit_code = asyncio.run(main())
        
        if exit_code == 0:
            print("\n🎉 統一測試全部通過！")
            print("📝 建議：可以考慮使用此統一測試取代原有 1.2/1.3 階段測試")
        else:
            print(f"\n⚠️ 統一測試完成，退出碼: {exit_code}")
            
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n⚠️ 測試被用戶中斷")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 測試執行失敗: {e}")
        sys.exit(1)