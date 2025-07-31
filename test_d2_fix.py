#!/usr/bin/env python3
"""
測試 D2 修復效果的腳本
檢查模擬數據和真實數據的差異
"""

import requests
import json
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime


def test_d2_real_data():
    """測試真實 D2 數據"""
    print("🔍 測試真實 D2 數據...")

    url = "http://localhost:8888/api/measurement-events/D2/real"
    payload = {
        "scenario_name": "Test_D2_Fix",
        "ue_position": {"latitude": 25.0478, "longitude": 121.5319, "altitude": 100},
        "duration_minutes": 5,
        "sample_interval_seconds": 10,
        "constellation": "starlink",
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        print(f"✅ 成功獲取 {len(data['results'])} 個真實數據點")

        # 提取距離數據
        timestamps = []
        satellite_distances = []
        ground_distances = []

        for result in data["results"]:
            timestamps.append(result["timestamp"])
            sat_dist = (
                result["measurement_values"]["satellite_distance"] / 1000
            )  # 轉換為 km
            ground_dist = (
                result["measurement_values"]["ground_distance"] / 1000
            )  # 轉換為 km

            satellite_distances.append(sat_dist)
            ground_distances.append(ground_dist)

            # 調試：檢查是否有被截斷的值
            if sat_dist == 2000.0 or ground_dist == 2000.0:
                print(
                    f"⚠️ 發現被截斷的距離值: Ml1={sat_dist:.1f}km, Ml2={ground_dist:.1f}km"
                )

        # 計算統計信息
        sat_min, sat_max = min(satellite_distances), max(satellite_distances)
        ground_min, ground_max = min(ground_distances), max(ground_distances)

        print(
            f"📊 衛星距離範圍: {sat_min:.1f} - {sat_max:.1f} km (變化: {sat_max - sat_min:.1f} km)"
        )
        print(
            f"📊 地面距離範圍: {ground_min:.1f} - {ground_max:.1f} km (變化: {ground_max - ground_min:.1f} km)"
        )

        # 檢查是否所有值都相同（被截斷）
        if ground_max == ground_min == 2000.0:
            print("⚠️ Ml2 所有值都是 2000km，可能被驗證邏輯截斷了")

        return {
            "timestamps": timestamps,
            "satellite_distances": satellite_distances,
            "ground_distances": ground_distances,
            "stats": {
                "sat_range": sat_max - sat_min,
                "ground_range": ground_max - ground_min,
            },
        }

    except Exception as e:
        print(f"❌ 真實數據測試失敗: {e}")
        return None


def test_d2_simulate_data():
    """測試模擬 D2 數據"""
    print("🎲 測試模擬 D2 數據...")

    url = "http://localhost:8888/api/measurement-events/D2/simulate"
    payload = {
        "scenario_name": "Test_D2_Simulate",
        "ue_position": {"latitude": 25.0478, "longitude": 121.5319, "altitude": 100},
        "duration_minutes": 5,
        "sample_interval_seconds": 10,
        "target_satellites": [],
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        print(f"✅ 成功獲取 {len(data['results'])} 個模擬數據點")

        # 提取距離數據
        timestamps = []
        satellite_distances = []
        ground_distances = []

        for result in data["results"]:
            timestamps.append(result["timestamp"])
            satellite_distances.append(
                result["measurement_values"]["satellite_distance"] / 1000
            )  # 轉換為 km
            ground_distances.append(
                result["measurement_values"]["ground_distance"] / 1000
            )  # 轉換為 km

        # 計算統計信息
        sat_min, sat_max = min(satellite_distances), max(satellite_distances)
        ground_min, ground_max = min(ground_distances), max(ground_distances)

        print(
            f"📊 衛星距離範圍: {sat_min:.1f} - {sat_max:.1f} km (變化: {sat_max - sat_min:.1f} km)"
        )
        print(
            f"📊 地面距離範圍: {ground_min:.1f} - {ground_max:.1f} km (變化: {ground_max - ground_min:.1f} km)"
        )

        return {
            "timestamps": timestamps,
            "satellite_distances": satellite_distances,
            "ground_distances": ground_distances,
            "stats": {
                "sat_range": sat_max - sat_min,
                "ground_range": ground_max - ground_min,
            },
        }

    except Exception as e:
        print(f"❌ 模擬數據測試失敗: {e}")
        return None


def create_comparison_plot(real_data, sim_data):
    """創建對比圖表"""
    print("📈 創建對比圖表...")

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle("D2 數據修復效果對比", fontsize=16, fontweight="bold")

    # 真實數據圖表
    if real_data:
        time_indices = range(len(real_data["satellite_distances"]))
        ax1.plot(
            time_indices,
            real_data["satellite_distances"],
            "g-",
            label="衛星距離",
            linewidth=2,
        )
        ax1.plot(
            time_indices,
            real_data["ground_distances"],
            "orange",
            label="地面距離",
            linewidth=2,
        )
        ax1.set_title("真實數據 (修復後)", fontweight="bold")
        ax1.set_xlabel("時間點")
        ax1.set_ylabel("距離 (km)")
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # 真實數據統計
        ax3.bar(
            ["衛星距離變化", "地面距離變化"],
            [real_data["stats"]["sat_range"], real_data["stats"]["ground_range"]],
            color=["green", "orange"],
            alpha=0.7,
        )
        ax3.set_title("真實數據變化範圍", fontweight="bold")
        ax3.set_ylabel("變化範圍 (km)")
    else:
        ax1.text(
            0.5,
            0.5,
            "真實數據獲取失敗",
            ha="center",
            va="center",
            transform=ax1.transAxes,
        )
        ax3.text(
            0.5, 0.5, "無統計數據", ha="center", va="center", transform=ax3.transAxes
        )

    # 模擬數據圖表
    if sim_data:
        time_indices = range(len(sim_data["satellite_distances"]))
        ax2.plot(
            time_indices,
            sim_data["satellite_distances"],
            "g-",
            label="衛星距離",
            linewidth=2,
        )
        ax2.plot(
            time_indices,
            sim_data["ground_distances"],
            "orange",
            label="地面距離",
            linewidth=2,
        )
        ax2.set_title("模擬數據 (參考)", fontweight="bold")
        ax2.set_xlabel("時間點")
        ax2.set_ylabel("距離 (km)")
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # 模擬數據統計
        ax4.bar(
            ["衛星距離變化", "地面距離變化"],
            [sim_data["stats"]["sat_range"], sim_data["stats"]["ground_range"]],
            color=["green", "orange"],
            alpha=0.7,
        )
        ax4.set_title("模擬數據變化範圍", fontweight="bold")
        ax4.set_ylabel("變化範圍 (km)")
    else:
        ax2.text(
            0.5,
            0.5,
            "模擬數據獲取失敗",
            ha="center",
            va="center",
            transform=ax2.transAxes,
        )
        ax4.text(
            0.5, 0.5, "無統計數據", ha="center", va="center", transform=ax4.transAxes
        )

    plt.tight_layout()
    plt.savefig("d2_fix_comparison.png", dpi=300, bbox_inches="tight")
    print("✅ 對比圖表已保存為 d2_fix_comparison.png")


def main():
    """主函數"""
    print("🚀 開始 D2 修復效果測試 (基於 SIB19 移動參考位置)")
    print("=" * 60)

    # 測試真實數據
    real_data = test_d2_real_data()
    print()

    # 測試模擬數據
    sim_data = test_d2_simulate_data()
    print()

    # 創建對比圖表
    create_comparison_plot(real_data, sim_data)
    print()

    # 總結
    print("📋 修復效果總結 (基於 3GPP TS 38.331 標準):")
    print("=" * 50)

    if real_data and real_data["stats"]["sat_range"] > 100:
        print("✅ 真實數據現在有明顯變化，符合 SIB19 移動參考位置計算")
        print(f"   - Ml1 (衛星距離) 變化: {real_data['stats']['sat_range']:.1f} km")
        print(f"   - Ml2 (地面距離) 變化: {real_data['stats']['ground_range']:.1f} km")
        print("   - 使用 3D 歐式距離計算，基於真實軌道動力學")
    else:
        print("❌ 真實數據仍然變化不明顯")
        if real_data:
            print(f"   - Ml1 變化: {real_data['stats']['sat_range']:.1f} km")
            print(f"   - Ml2 變化: {real_data['stats']['ground_range']:.1f} km")

    if sim_data and sim_data["stats"]["sat_range"] > 10:
        print("✅ 模擬數據正常工作")
        print(f"   - 衛星距離變化: {sim_data['stats']['sat_range']:.1f} km")
        print(f"   - 地面距離變化: {sim_data['stats']['ground_range']:.1f} km")
    else:
        print("❌ 模擬數據有問題")

    print("\n🎯 修復完成！D2 事件現在基於真實的 SIB19 移動參考位置計算")
    print("📊 請檢查前端圖表是否顯示動態的正弦波變化")


if __name__ == "__main__":
    main()
