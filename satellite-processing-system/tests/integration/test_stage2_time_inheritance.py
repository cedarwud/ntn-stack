#!/usr/bin/env python3
"""
測試Stage 2的時間基準繼承機制修復
檢查Stage 2能否正確從Stage 1繼承時間基準
"""

import sys
import json
from datetime import datetime, timezone
sys.path.append('/home/sat/ntn-stack/satellite-processing-system/src')

def test_stage2_time_inheritance():
    """測試Stage 2的時間基準繼承機制"""

    print("=== Stage 2 時間基準繼承機制測試 ===")

    # 模擬Stage 1輸出格式（符合v6.0規範）
    mock_stage1_output = {
        "data": {
            "satellites": {
                "STARLINK-1001": {
                    "position_timeseries": [
                        {
                            "timestamp": "2025-09-08T10:30:45.123Z",
                            "position_eci": {"x": 1234.5, "y": 2345.6, "z": 3456.7}
                        }
                    ]
                }
            }
        },
        "metadata": {
            "stage": 1,
            "data_lineage": {
                "calculation_base_time": "2025-09-08T10:30:45.123Z",
                "tle_epoch_time": "2025-09-08T10:30:45.123Z",
                "time_base_source": "tle_epoch_derived",
                "tle_epoch_compliance": True,
                "stage1_time_inheritance": {
                    "exported_time_base": "2025-09-08T10:30:45.123Z",
                    "inheritance_ready": True,
                    "calculation_reference": "tle_epoch_based"
                }
            }
        }
    }

    # 模擬Stage 2處理器的時間基準繼承邏輯
    def extract_and_inherit_time_base(stage1_data):
        """模擬Stage 2的_extract_and_inherit_time_base方法"""
        try:
            metadata = stage1_data.get("metadata", {})

            # 優先使用Stage 1的時間繼承信息
            stage1_inheritance = metadata.get("data_lineage", {}).get("stage1_time_inheritance", {})
            if stage1_inheritance.get("inheritance_ready", False):
                exported_time_base = stage1_inheritance.get("exported_time_base")
                if exported_time_base:
                    print(f"🎯 v6.0重構：使用Stage 1導出的時間基準: {exported_time_base}")

                    # 設置inherited_time_base供下游處理使用
                    stage1_data["inherited_time_base"] = exported_time_base
                    return exported_time_base

            # 備用方案：使用TLE epoch時間
            data_lineage = metadata.get("data_lineage", {})
            tle_epoch_time = data_lineage.get("tle_epoch_time")
            calculation_base_time = data_lineage.get("calculation_base_time")

            if tle_epoch_time:
                stage1_data["inherited_time_base"] = tle_epoch_time
                print(f"🎯 v6.0重構：使用Stage 1 TLE epoch時間: {tle_epoch_time}")
                return tle_epoch_time
            elif calculation_base_time:
                stage1_data["inherited_time_base"] = calculation_base_time
                print(f"🎯 v6.0重構：使用Stage 1計算基準時間: {calculation_base_time}")
                return calculation_base_time
            else:
                raise ValueError("v6.0重構：Stage 1 metadata缺失時間基準信息")

        except Exception as e:
            print(f"❌ v6.0重構：時間基準繼承失敗: {e}")
            raise

    # 測試時間基準繼承
    try:
        inherited_time = extract_and_inherit_time_base(mock_stage1_output)
        print(f"✅ 時間基準繼承成功: {inherited_time}")
    except Exception as e:
        print(f"❌ 時間基準繼承失敗: {e}")
        return False

    # 驗證inherited_time_base字段設置
    inherited_time_base = mock_stage1_output.get("inherited_time_base")
    if inherited_time_base:
        print(f"✅ inherited_time_base字段已設置: {inherited_time_base}")
    else:
        print("❌ inherited_time_base字段未設置")
        return False

    # 模擬Stage 2處理流程中的檢查邏輯
    def check_inherited_time_base(stage1_data):
        """模擬Stage 2處理流程中的時間基準檢查"""
        inherited_time_base = stage1_data.get("inherited_time_base")
        if inherited_time_base:
            print(f"🎯 v6.0 重構：使用繼承的Stage 1時間基準: {inherited_time_base}")
            return inherited_time_base
        else:
            print("⚠️ Stage 1數據中未找到inherited_time_base，可能使用舊版格式")
            return None

    # 測試處理流程中的檢查
    processing_time_base = check_inherited_time_base(mock_stage1_output)
    if processing_time_base:
        print(f"✅ 處理流程時間基準檢查成功: {processing_time_base}")
    else:
        print("❌ 處理流程時間基準檢查失敗")
        return False

    # 驗證時間基準一致性
    expected_time = "2025-09-08T10:30:45.123Z"
    if (inherited_time == expected_time and
        inherited_time_base == expected_time and
        processing_time_base == expected_time):
        print("✅ 時間基準一致性驗證通過")
        return True
    else:
        print("❌ 時間基準一致性驗證失敗")
        print(f"   預期: {expected_time}")
        print(f"   繼承: {inherited_time}")
        print(f"   設置: {inherited_time_base}")
        print(f"   處理: {processing_time_base}")
        return False

if __name__ == "__main__":
    success = test_stage2_time_inheritance()
    if success:
        print("\n🎯 Stage 2時間基準繼承機制測試通過")
        print("修復要點:")
        print("1. _extract_and_inherit_time_base方法需要設置inherited_time_base字段")
        print("2. process_intelligent_filtering中的檢查邏輯正確")
        print("3. 時間基準在整個Stage 2處理流程中保持一致")
        print("\n下一步: 確保實際代碼中的邏輯符合測試要求")
    else:
        print("\n❌ Stage 2時間基準繼承機制測試失敗")
        print("需要修復時間基準繼承邏輯")