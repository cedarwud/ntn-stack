#!/usr/bin/env python3
"""
1.4 版本 UPF 整合測試執行器

執行方式:
cd /home/sat/ntn-stack/paper/1.4_upf_integration
python run_14_tests.py
"""

import asyncio
import sys
from pathlib import Path

# 添加項目路徑
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from test_14_comprehensive import main

if __name__ == "__main__":
    print("🚀 啟動 1.4 版本 UPF 整合測試")
    print("=" * 60)
    
    try:
        exit_code = asyncio.run(main())
        
        if exit_code == 0:
            print("\n🎉 1.4 版本測試全部通過！")
        else:
            print(f"\n⚠️ 1.4 版本測試完成，退出碼: {exit_code}")
            
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n⚠️ 測試被用戶中斷")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 測試執行失敗: {e}")
        sys.exit(1)