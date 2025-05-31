#!/usr/bin/env python3

import os
import sys

# 添加 simworld backend 到 Python 路徑
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../simworld/backend"))

try:
    from app.domains.simulation.services.sionna_service import get_scene_xml_file_path
except ImportError as e:
    print(f"警告：無法導入 simworld 模組: {e}")
    print("這可能是因為 simworld 服務未啟動或模組路徑不正確")

    # 創建模擬函數以便測試能夠執行
    def get_scene_xml_file_path(scene_name):
        return f"/mock/path/{scene_name}.xml"


def test_scene_path_function():
    """測試 get_scene_xml_file_path 函數的修復"""
    scenes = ["nycu", "lotus", "ntpu", "nanliao"]

    for scene_name in scenes:
        try:
            print(f"\n=== 測試場景路徑函數: {scene_name} ===")

            # 調用我們的函數
            xml_path = get_scene_xml_file_path(scene_name)
            print(f"返回的 XML 路徑: {xml_path}")

            # 檢查是否回退到了 NYCU
            if "NYCU.xml" in xml_path:
                print(f"✅ 場景 {scene_name} 正確回退到 NYCU")
            else:
                print(f"⚠️  場景 {scene_name} 未回退")

        except Exception as e:
            print(f"❌ 場景 {scene_name} 測試失敗: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    test_scene_path_function()
