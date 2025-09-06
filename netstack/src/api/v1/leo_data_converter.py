"""
LEO 數據轉換器 - 將 LEO 系統輸出轉換為前端格式
Phase 1 Week 4: 前端數據格式相容性
"""
import json
import tempfile
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
    
    def convert_leo_to_frontend_format(self, leo_output_dir: str = None) -> List[Dict[str, Any]]:
        """
        將LEO系統輸出轉換為前端格式（多階段回退版本）
        
        Args:
            leo_output_dir: LEO系統輸出目錄路徑（可選，使用新的自動檢測）
            
        Returns:
            List[Dict]: 前端格式的衛星數據列表
        """
        try:
            # 🚀 使用新的多階段數據管理器
            from shared_core.stage_data_manager import StageDataManager
            
            # 初始化數據管理器
            data_dir = leo_output_dir if leo_output_dir else "/app/data"
            stage_manager = StageDataManager(data_dir)
            
            # 獲取最佳可用階段數據
            stage_num, stage_info = stage_manager.get_best_available_stage()
            
            print(f"🎯 使用 Stage {stage_num} 數據源")
            print(f"   - 衛星數量: {stage_info.satellite_count}")
            print(f"   - 文件大小: {stage_info.file_size_mb:.1f} MB")
            print(f"   - 處理時間: {stage_info.processing_time}")
            print(f"   - 數據狀態: {stage_info.status.value}")
            
            if stage_info.status.value == "missing":
                print("❌ 沒有可用的階段數據")
                return []
            
            # 獲取統一格式的衛星數據
            satellites = stage_manager.get_unified_satellite_data()
            
            print(f"✅ 數據轉換完成: {len(satellites)} 顆衛星")
            print(f"   - 數據來源: Stage {stage_num} ({stage_info.stage_name})")
            
            # 添加數據來源信息到每個衛星記錄
            for sat in satellites:
                sat['data_source'] = {
                    'stage_number': stage_num,
                    'stage_name': stage_info.stage_name,
                    'file_path': stage_info.file_path,
                    'processing_time': stage_info.processing_time.isoformat() if stage_info.processing_time else None
                }
            
            return satellites
            
        except Exception as e:
            print(f"❌ 多階段轉換失敗，嘗試回退到原始方法: {e}")
            
            # 回退到原始轉換邏輯
            return self._fallback_conversion(leo_output_dir)
    
    def _fallback_conversion(self, leo_output_dir: str) -> List[Dict[str, Any]]:
        """
        回退轉換方法（保留原始邏輯）
        """
        if not leo_output_dir:
            return []
            
        output_path = Path(leo_output_dir)
        
        # 🔧 修復：前端應該讀取A1最終優化結果，而不是F2中間篩選結果
        optimization_results_path = output_path / "dynamic_satellite_pool_optimization_results.json"
        if not optimization_results_path.exists():
            print(f"❌ 最終優化結果檔案不存在: {optimization_results_path}")
            # 備用方案：嘗試讀取臨時目錄的F2篩選結果
            temp_filtering_path = Path(tempfile.gettempdir()) / "leo_temporary_outputs" / "satellite_filtering_and_candidate_selection_results.json"
            if temp_filtering_path.exists():
                print(f"⚠️ 使用臨時篩選結果: {temp_filtering_path}")
                filtering_results_path = temp_filtering_path
            else:
                return []
        else:
            # 使用A1最終結果
            filtering_results_path = optimization_results_path
        
        with open(filtering_results_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # 根據檔案類型處理數據結構
        if 'final_solution' in data:
            # A1最終優化結果格式
            filtering_data = {
                'candidates': {
                    'starlink': [{'satellite_id': sat_id} for sat_id in data['final_solution']['starlink_satellites']],
                    'oneweb': [{'satellite_id': sat_id} for sat_id in data['final_solution']['oneweb_satellites']]
                },
                'orbital_positions': {}  # A1結果中沒有詳細軌道數據
            }
        else:
            # F2篩選結果格式
            filtering_data = data
        
        frontend_satellites = []
        
        # 處理 Starlink 衛星
        if 'candidates' in filtering_data and 'starlink' in filtering_data['candidates']:
            for satellite in filtering_data['candidates']['starlink']:
                frontend_sat = self._convert_satellite_to_frontend(satellite, 'starlink')
                if frontend_sat:
                    frontend_satellites.append(frontend_sat)
        
        # 處理 OneWeb 衛星
        if 'candidates' in filtering_data and 'oneweb' in filtering_data['candidates']:
            for satellite in filtering_data['candidates']['oneweb']:
                frontend_sat = self._convert_satellite_to_frontend(satellite, 'oneweb')
                if frontend_sat:
                    frontend_satellites.append(frontend_sat)
        
        print(f"⚠️ 回退轉換完成: {len(frontend_satellites)} 顆衛星")
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
            "source": "LEO_F1_F2_F3_A1_System",
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
    leo_output_dir = "/app/data/dynamic_pool_planning_outputs"
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