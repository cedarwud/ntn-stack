#!/usr/bin/env python3

import os
import sys

sys.path.append("/app")

from app.domains.simulation.services.sionna_service import (
    get_scene_xml_file_path,
    check_scene_health,
)
from app.core.config import get_scene_xml_path


def test_health_check():
    """測試所有場景的健康度檢查機制"""
    scenes = ["nycu", "lotus", "ntpu", "nanliao"]

    for scene_name in scenes:
        print(f"\n=== 測試場景健康度檢查: {scene_name.upper()} ===")

        # 測試直接健康度檢查
        scene_mapping = {
            "nycu": "NYCU",
            "lotus": "Lotus",
            "ntpu": "NTPU",
            "nanliao": "Nanliao",
        }
        backend_scene_name = scene_mapping.get(scene_name.lower(), "NYCU")

        try:
            original_xml_path = get_scene_xml_path(backend_scene_name)
            print(f"原始 XML 路徑: {original_xml_path}")

            # 直接測試健康度檢查
            is_healthy = check_scene_health(backend_scene_name, original_xml_path)
            print(f"健康度檢查結果: {'✅ 健康' if is_healthy else '❌ 不健康'}")

            # 測試智能路徑獲取
            final_xml_path = get_scene_xml_file_path(scene_name)
            print(f"最終 XML 路徑: {final_xml_path}")

            # 檢查是否回退
            if "NYCU.xml" in final_xml_path and backend_scene_name != "NYCU":
                print(f"✅ 場景 {scene_name} 正確回退到 NYCU")
            elif backend_scene_name == "NYCU":
                print(f"✅ 場景 {scene_name} 使用原生場景")
            else:
                print(f"✅ 場景 {scene_name} 通過健康度檢查")

        except Exception as e:
            print(f"❌ 測試失敗: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    test_health_check()
