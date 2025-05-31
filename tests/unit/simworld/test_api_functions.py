#!/usr/bin/env python3

import os
import sys

sys.path.append("/app")

from app.domains.simulation.services.sionna_service import get_scene_xml_file_path


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
