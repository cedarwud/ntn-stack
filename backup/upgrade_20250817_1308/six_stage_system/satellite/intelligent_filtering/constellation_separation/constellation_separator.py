#!/usr/bin/env python3
"""
星座分離篩選模組 - 階段二智能篩選系統

依據: @docs/satellite_data_preprocessing.md 階段二處理順序優化
核心原則: Starlink 和 OneWeb 完全分離處理，禁用跨星座換手
"""

from typing import Dict, List, Any
import json

class ConstellationSeparator:
    """星座分離篩選器"""
    
    def __init__(self):
        self.starlink_config = {
            "constellation_name": "starlink",
            "frequency_ghz": 12.0,          # Ku 頻段
            "altitude_km": 550,             # 平均軌道高度
            "inclination_deg": 53,          # 軌道傾角
            "orbital_period_min": 96,       # 軌道週期
            "tx_power_dbm": 43.0,          # 發射功率
            "antenna_gain_db": 15.0        # 最大天線增益
        }
        
        self.oneweb_config = {
            "constellation_name": "oneweb",
            "frequency_ghz": 20.0,          # Ka 頻段
            "altitude_km": 1200,            # 平均軌道高度
            "inclination_deg": 87,          # 極地軌道傾角
            "orbital_period_min": 109,      # 軌道週期
            "tx_power_dbm": 40.0,          # 發射功率
            "antenna_gain_db": 18.0        # 高增益天線
        }
        
    def separate_constellations(self, satellite_data: List[Dict]) -> Dict[str, List[Dict]]:
        """
        將混合衛星數據分離為獨立星座
        
        Args:
            satellite_data: 階段一輸出的完整衛星軌道數據
            
        Returns:
            Dict[str, List[Dict]]: 分離後的星座數據
            {
                "starlink": [...],
                "oneweb": [...]
            }
        """
        separated_data = {
            "starlink": [],
            "oneweb": []
        }
        
        for satellite in satellite_data:
            constellation = self._identify_constellation(satellite)
            if constellation in separated_data:
                separated_data[constellation].append(satellite)
        
        return separated_data
    
    def _identify_constellation(self, satellite: Dict) -> str:
        """
        識別衛星所屬星座
        
        Args:
            satellite: 單顆衛星數據
            
        Returns:
            str: 星座名稱 ("starlink" or "oneweb")
        """
        satellite_id = satellite.get("satellite_id", "").upper()
        
        if "STARLINK" in satellite_id:
            return "starlink"
        elif "ONEWEB" in satellite_id:
            return "oneweb"
        else:
            # 基於軌道參數推斷
            orbit_data = satellite.get("orbit_data", {})
            altitude = orbit_data.get("altitude", 0)
            
            if 400 <= altitude <= 700:  # Starlink 高度範圍
                return "starlink"
            elif 1000 <= altitude <= 1400:  # OneWeb 高度範圍
                return "oneweb"
        
        return "unknown"
    
    def apply_constellation_specific_filtering(self, constellation_data: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """
        星座分離階段：僅分類，不做篩選
        
        在階段二的星座分離步驟中，我們只需要按星座分類衛星，
        不應該根據軌道參數進行過濾，避免過早丟失衛星數據。
        
        Args:
            constellation_data: 分離後的星座數據
            
        Returns:
            Dict[str, List[Dict]]: 分類後的數據（不篩選）
        """
        # 直接返回分類後的數據，不做任何篩選
        # 篩選邏輯應該在後續的地理篩選和換手評分階段執行
        return constellation_data
    
    def _apply_starlink_filtering(self, starlink_satellites: List[Dict]) -> List[Dict]:
        """
        Starlink 特定篩選邏輯
        
        針對 53° 傾角、550km 高度、96分鐘軌道週期優化
        """
        filtered_satellites = []
        
        for satellite in starlink_satellites:
            orbit_data = satellite.get("orbit_data", {})
            
            # Starlink 特定篩選條件
            altitude = orbit_data.get("altitude", 0)
            inclination = orbit_data.get("inclination", 0)
            
            # 高度範圍檢查 (Starlink 典型範圍)
            if 400 <= altitude <= 700:
                # 傾角範圍檢查 (Starlink 典型傾角)
                if 50 <= inclination <= 56:
                    filtered_satellites.append(satellite)
        
        return filtered_satellites
    
    def _apply_oneweb_filtering(self, oneweb_satellites: List[Dict]) -> List[Dict]:
        """
        OneWeb 特定篩選邏輯
        
        針對 87° 傾角、1200km 高度、109分鐘軌道週期優化
        """
        filtered_satellites = []
        
        for satellite in oneweb_satellites:
            orbit_data = satellite.get("orbit_data", {})
            
            # OneWeb 特定篩選條件
            altitude = orbit_data.get("altitude", 0)
            inclination = orbit_data.get("inclination", 0)
            
            # 高度範圍檢查 (OneWeb 典型範圍)
            if 1000 <= altitude <= 1400:
                # 傾角範圍檢查 (OneWeb 極地軌道)
                if 85 <= inclination <= 90:
                    filtered_satellites.append(satellite)
        
        return filtered_satellites
    
    def get_separation_statistics(self, separated_data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """
        獲取星座分離統計信息
        
        Returns:
            Dict: 分離統計數據
        """
        stats = {
            "total_satellites": sum(len(sats) for sats in separated_data.values()),
            "constellation_breakdown": {},
            "separation_config": {
                "starlink": self.starlink_config,
                "oneweb": self.oneweb_config
            }
        }
        
        for constellation, satellites in separated_data.items():
            stats["constellation_breakdown"][constellation] = {
                "count": len(satellites),
                "percentage": len(satellites) / stats["total_satellites"] * 100 if stats["total_satellites"] > 0 else 0
            }
        
        return stats


def main():
    """測試星座分離功能"""
    separator = ConstellationSeparator()
    
    # 模擬階段一輸出數據
    test_data = [
        {
            "satellite_id": "STARLINK-1007",
            "orbit_data": {
                "altitude": 550,
                "inclination": 53,
                "position": {"x": 1234, "y": 5678, "z": 9012}
            }
        },
        {
            "satellite_id": "ONEWEB-0123",
            "orbit_data": {
                "altitude": 1200,
                "inclination": 87,
                "position": {"x": 2345, "y": 6789, "z": 123}
            }
        }
    ]
    
    # 執行分離
    separated = separator.separate_constellations(test_data)
    filtered = separator.apply_constellation_specific_filtering(separated)
    stats = separator.get_separation_statistics(filtered)
    
    print("星座分離測試結果:")
    print(json.dumps(stats, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()