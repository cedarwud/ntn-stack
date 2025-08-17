"""
LEO 數據轉換器 - 將 LEO 系統輸出轉換為前端格式
Phase 1 Week 4: 前端數據格式相容性
"""
import json
import tempfile
import os
from typing import List, Dict, Any
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

@dataclass
class VisibleSatelliteInfo:
    """前端期望的衛星資訊格式"""
    norad_id: int
    name: str
    elevation_deg: float
    azimuth_deg: float
    distance_km: float
    line1: str  # TLE line 1
    line2: str  # TLE line 2
    ecef_x_km: float = None
    ecef_y_km: float = None
    ecef_z_km: float = None
    constellation: str = None

class LEODataConverter:
    """LEO系統數據轉換器"""
    
    def __init__(self):
        self.default_tle_data = {
            # 預設的TLE數據（用於沒有TLE line的情況）
            "starlink_default": {
                "line1": "1 44713U 19074A   25227.50000000  .00001234  00000-0  12345-3 0  9990",
                "line2": "2 44713  53.0000 123.4567 0001234  12.3456 347.6543 15.05000000123456"
            },
            "oneweb_default": {
                "line1": "1 44713U 19074A   25227.50000000  .00001234  00000-0  12345-3 0  9990", 
                "line2": "2 44713  87.9000 123.4567 0001234  12.3456 347.6543 13.20000000123456"
            }
        }
    
    def convert_leo_to_frontend_format(self, leo_output_dir: str) -> List[Dict[str, Any]]:
        """
        將LEO系統輸出轉換為前端格式
        
        Args:
            leo_output_dir: LEO系統輸出目錄路徑
            
        Returns:
            List[Dict]: 前端格式的衛星數據列表
        """
        output_path = Path(leo_output_dir)
        
        # 🎯 修復：讀取A1最終優化結果而不是F2中間篩選結果
        optimization_results_path = output_path / "dynamic_satellite_pool_optimization_results.json"
        if not optimization_results_path.exists():
            print(f"❌ A1最終優化結果不存在: {optimization_results_path}")
            # 🔄 容錯：嘗試讀取F2篩選結果作為備選
            fallback_path = output_path / "satellite_filtering_and_candidate_selection_results.json"
            if fallback_path.exists():
                print(f"⚠️ 使用F2篩選結果作為備選: {fallback_path}")
                optimization_results_path = fallback_path
            else:
                print(f"❌ F2篩選結果也不存在: {fallback_path}")
                return []
        
        with open(optimization_results_path, 'r', encoding='utf-8') as f:
            optimization_data = json.load(f)
        
        frontend_satellites = []
        
        # 🎯 處理 A1最終優化結果：適配實際的數據結構
        # A1優化結果包含最終選中的衛星池ID列表，需要從F2數據中找到詳細信息
        if 'final_solution' in optimization_data:
            final_solution = optimization_data['final_solution']
            
            # 🔄 需要從F2數據中獲取衛星詳細信息，因為A1只有ID列表
            # F2數據在臨時目錄中 - 使用跨平台路徑
            temp_dir = Path(tempfile.gettempdir()) / "leo_temporary_outputs" if not os.environ.get('DOCKER_CONTAINER') else Path("/tmp/leo_temporary_outputs")
            fallback_path = temp_dir / "satellite_filtering_and_candidate_selection_results.json"
            if fallback_path.exists():
                with open(fallback_path, 'r', encoding='utf-8') as f:
                    f2_data = json.load(f)
                
                # 創建衛星ID到詳細信息的映射
                satellite_details = {}
                if 'candidates' in f2_data:
                    for constellation, candidates in f2_data['candidates'].items():
                        for satellite in candidates:
                            satellite_details[satellite['satellite_id']] = satellite
                
                # 處理 Starlink 最終衛星池
                if 'starlink_satellites' in final_solution:
                    for satellite_id in final_solution['starlink_satellites']:
                        if satellite_id in satellite_details:
                            satellite = satellite_details[satellite_id]
                            frontend_sat = self._convert_satellite_to_frontend(satellite, 'starlink')
                            if frontend_sat:
                                frontend_satellites.append(frontend_sat)
                
                # 處理 OneWeb 最終衛星池
                if 'oneweb_satellites' in final_solution:
                    for satellite_id in final_solution['oneweb_satellites']:
                        if satellite_id in satellite_details:
                            satellite = satellite_details[satellite_id]
                            frontend_sat = self._convert_satellite_to_frontend(satellite, 'oneweb')
                            if frontend_sat:
                                frontend_satellites.append(frontend_sat)
            else:
                print("⚠️ 無法找到F2數據來獲取衛星詳細信息")
        
        # 🔄 容錯：如果A1格式不匹配，嘗試F2格式
        elif 'candidates' in optimization_data:
            # 處理 Starlink 候選衛星
            if 'starlink' in optimization_data['candidates']:
                for satellite in optimization_data['candidates']['starlink']:
                    frontend_sat = self._convert_satellite_to_frontend(satellite, 'starlink')
                    if frontend_sat:
                        frontend_satellites.append(frontend_sat)
            
            # 處理 OneWeb 候選衛星
            if 'oneweb' in optimization_data['candidates']:
                for satellite in optimization_data['candidates']['oneweb']:
                    frontend_sat = self._convert_satellite_to_frontend(satellite, 'oneweb')
                    if frontend_sat:
                        frontend_satellites.append(frontend_sat)
        
        print(f"✅ 轉換完成: {len(frontend_satellites)} 顆衛星")
        return frontend_satellites
    
    def _convert_satellite_to_frontend(self, satellite: Dict, constellation: str) -> Dict[str, Any]:
        """
        轉換單顆衛星數據到前端格式
        
        Args:
            satellite: LEO系統的衛星數據
            constellation: 星座名稱 ('starlink' 或 'oneweb')
            
        Returns:
            Dict: 前端格式的衛星數據
        """
        try:
            # 提取 NORAD ID
            satellite_id = satellite.get('satellite_id', '')
            norad_id = self._extract_norad_id(satellite_id)
            
            # 獲取可見性分析
            visibility = satellite.get('visibility_analysis', {})
            
            # 獲取當前位置（使用最高仰角時間點）
            current_elevation = visibility.get('max_elevation_deg', 0.0)
            current_distance = 7000.0  # 預設距離
            current_azimuth = 180.0   # 預設方位角
            
            # 獲取TLE數據
            tle_data = self._get_tle_data(satellite_id, constellation)
            
            # 構建前端格式
            frontend_data = {
                "norad_id": norad_id,
                "name": satellite_id.replace('_', '-').upper(),
                "elevation_deg": current_elevation,
                "azimuth_deg": current_azimuth,
                "distance_km": current_distance,
                "line1": tle_data['line1'],
                "line2": tle_data['line2'],
                "ecef_x_km": None,  # 前端會動態計算
                "ecef_y_km": None,  # 前端會動態計算
                "ecef_z_km": None,  # 前端會動態計算
                "constellation": constellation.upper(),
                # 額外的 LEO 系統數據
                "leo_visibility_analysis": visibility,
                "leo_total_score": satellite.get('total_score', 0.0),
                "leo_visible_time_minutes": visibility.get('total_visible_time_minutes', 0.0)
            }
            
            return frontend_data
            
        except Exception as e:
            print(f"❌ 轉換衛星數據失敗 {satellite.get('satellite_id', 'unknown')}: {e}")
            return None
    
    def _extract_norad_id(self, satellite_id: str) -> int:
        """從衛星ID中提取NORAD ID"""
        try:
            # satellite_id格式通常是 "starlink_44714" 或 "oneweb_63724"
            if '_' in satellite_id:
                return int(satellite_id.split('_')[1])
            else:
                # 如果沒有下劃線，嘗試提取數字
                import re
                numbers = re.findall(r'\d+', satellite_id)
                if numbers:
                    return int(numbers[0])
        except:
            pass
        
        # 預設值
        return 44714
    
    def _get_tle_data(self, satellite_id: str, constellation: str) -> Dict[str, str]:
        """獲取TLE數據"""
        # 在實際實現中，這裡應該從TLE數據庫中獲取真實的TLE
        # 現在使用預設值
        default_key = f"{constellation}_default"
        return self.default_tle_data.get(default_key, self.default_tle_data['starlink_default'])
    
    def save_frontend_format(self, leo_output_dir: str, output_file: str = None) -> str:
        """
        轉換並保存前端格式數據
        
        Args:
            leo_output_dir: LEO系統輸出目錄
            output_file: 輸出檔案路徑（可選）
            
        Returns:
            str: 輸出檔案路徑
        """
        frontend_data = self.convert_leo_to_frontend_format(leo_output_dir)
        
        if output_file is None:
            output_file = f"{leo_output_dir}/frontend_satellite_data.json"
        
        # 構建完整的前端格式
        frontend_format = {
            "generated_at": datetime.now().isoformat(),
            "source": "LEO_Phase1_System",
            "satellites": frontend_data,
            "statistics": {
                "total_satellites": len(frontend_data),
                "starlink_count": len([s for s in frontend_data if s['constellation'] == 'STARLINK']),
                "oneweb_count": len([s for s in frontend_data if s['constellation'] == 'ONEWEB']),
                "avg_elevation": sum(s['elevation_deg'] for s in frontend_data) / len(frontend_data) if frontend_data else 0,
                "max_elevation": max(s['elevation_deg'] for s in frontend_data) if frontend_data else 0
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(frontend_format, f, indent=2, ensure_ascii=False)
        
        print(f"📁 前端格式數據已保存: {output_file}")
        print(f"📊 統計: {frontend_format['statistics']}")
        
        return output_file

# 使用範例和測試函數
def test_converter():
    """測試轉換器功能"""
    converter = LEODataConverter()
    
    # 測試轉換
    leo_output_dir = "/tmp/leo_temporary_outputs"
    output_file = converter.save_frontend_format(leo_output_dir)
    
    print(f"✅ 轉換測試完成: {output_file}")
    
    # 驗證格式
    with open(output_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"🔍 前端格式驗證:")
    print(f"  - 衛星總數: {data['statistics']['total_satellites']}")
    print(f"  - Starlink: {data['statistics']['starlink_count']}")
    print(f"  - OneWeb: {data['statistics']['oneweb_count']}")
    print(f"  - 平均仰角: {data['statistics']['avg_elevation']:.1f}°")
    print(f"  - 最高仰角: {data['statistics']['max_elevation']:.1f}°")
    
    if data['satellites']:
        sample = data['satellites'][0]
        print(f"  - 範例衛星: {sample['name']} (仰角: {sample['elevation_deg']:.1f}°)")

if __name__ == "__main__":
    test_converter()