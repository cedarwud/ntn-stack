#!/usr/bin/env python3

import os
import sys

sys.path.append("/app")

from app.core.config import get_scene_xml_path
from sionna.rt import load_scene


def test_scene_loading():
    """測試加載不同場景"""
    scenes = ["NYCU", "Lotus", "NTPU", "Nanliao"]

    for scene_name in scenes:
        try:
            print(f"\n=== 測試場景: {scene_name} ===")

            # 獲取 XML 路徑
            xml_path = get_scene_xml_path(scene_name)
            print(f"XML 路徑: {xml_path}")
            print(f"檔案存在: {os.path.exists(xml_path)}")

            if not os.path.exists(xml_path):
                print(f"❌ 檔案不存在，跳過")
                continue

            # 嘗試加載場景
            print("嘗試加載場景...")
            scene = load_scene(str(xml_path))
            print(f"✅ 場景 {scene_name} 加載成功")

            # 檢查場景屬性
            print(f"發射器數量: {len(scene.transmitters)}")
            print(f"接收器數量: {len(scene.receivers)}")

        except Exception as e:
            print(f"❌ 場景 {scene_name} 加載失敗: {e}")
            print(f"錯誤類型: {type(e).__name__}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    test_scene_loading()
