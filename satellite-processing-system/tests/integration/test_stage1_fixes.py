#!/usr/bin/env python3
"""
測試Stage 1修復的獨立腳本
"""

import sys
import os
import json
from datetime import datetime, timezone

# 設定路徑和環境
sys.path.append('/satellite-processing/src')
os.chdir('/satellite-processing')

# 設定取樣模式
os.environ['SAMPLE_MODE'] = 'true'
os.environ['SAMPLE_SIZE'] = '5'

from stages.stage1_orbital_calculation.tle_orbital_calculation_processor import Stage1TLEProcessor

def main():
    print("🚀 開始測試Stage 1修復...")
    
    try:
        # 創建處理器
        processor = Stage1TLEProcessor()
        
        # 執行處理
        print("📡 執行Stage 1處理...")
        result = processor.process({})
        
        print(f"✅ Stage 1執行完成")
        print(f"📊 處理衛星數量: {len(result.get('satellite_data', []))}")
        
        # 檢查是否有驗證結果
        if 'validation' in result:
            validation = result['validation']
            print(f"🔍 驗證結果: {validation['passedChecks']}/{validation['totalChecks']} 檢查通過")
            
            if validation['failedChecks'] > 0:
                print("❌ 失敗的檢查:")
                for check in validation.get('criticalChecks', []):
                    if check['status'] == 'FAILED':
                        print(f"   - {check['check']}")
            else:
                print("✅ 所有驗證檢查都通過了!")
        
        # 儲存結果到臨時文件進行檢查
        with open('/tmp/stage1_test_result.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        
        print("📝 結果已保存到 /tmp/stage1_test_result.json")
        
    except Exception as e:
        print(f"❌ 執行錯誤: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()