#!/usr/bin/env python3
"""
智能衛星篩選處理器 - 執行封裝器

完全遵循 @docs/satellite_data_preprocessing.md 規範：
- 接收軌道計算輸出的完整衛星軌道數據
- 執行智能篩選（星座分離、地理篩選、換手評分）
- 輸出篩選後的高品質衛星候選
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

# 添加必要路徑
sys.path.insert(0, '/app/netstack')
sys.path.insert(0, '/app')

# 引用重新組織後的智能篩選系統
from src.services.satellite.intelligent_filtering.unified_intelligent_filter import create_unified_intelligent_filter

logger = logging.getLogger(__name__)

class IntelligentSatelliteFilterProcessor:
    """
    智能衛星篩選處理器封裝 (重構版)
    
    職責：
    1. 載入軌道計算輸出的完整軌道數據
    2. 執行統一智能篩選流程 (使用統一管理器)
    3. 保存智能篩選結果
    4. 為後續信號分析提供高品質輸入
    
    重構改進：
    - 使用統一仰角門檻管理器
    - 使用統一可見性檢查服務
    - 移除重複的仰角邏輯
    """
    
    def __init__(self, observer_lat: float = 24.9441667, observer_lon: float = 121.3713889,
                 input_dir: str = "/app/data", output_dir: str = "/app/data"):
        self.observer_lat = observer_lat
        self.observer_lon = observer_lon
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 導入統一管理器
        from shared_core.elevation_threshold_manager import get_elevation_threshold_manager
        from shared_core.visibility_service import get_visibility_service, ObserverLocation
        
        # 初始化統一管理器
        self.elevation_manager = get_elevation_threshold_manager()
        
        observer_location = ObserverLocation(
            latitude=observer_lat,
            longitude=observer_lon,
            altitude=50.0,
            location_name="NTPU"
        )
        self.visibility_service = get_visibility_service(observer_location)
        
        # 創建統一智能篩選系統
        self.filter_system = create_unified_intelligent_filter(observer_lat, observer_lon)
        
        logger.info("✅ 智能衛星篩選處理器初始化完成 (重構版)")
        logger.info(f"  輸入目錄: {self.input_dir}")
        logger.info(f"  輸出目錄: {self.output_dir}")
        logger.info(f"  觀測座標: ({self.observer_lat}°, {self.observer_lon}°)")
        logger.info("  🔧 使用統一仰角門檻管理器")
        logger.info("  🔧 使用統一可見性檢查服務")
        
    def load_orbital_calculation_output(self, orbital_file: Optional[str] = None) -> Dict[str, Any]:
        """載入軌道計算輸出數據"""
        if orbital_file is None:
            orbital_file = self.input_dir / "tle_orbital_calculation_output.json"
        else:
            orbital_file = Path(orbital_file)
            
        logger.info(f"📥 載入軌道計算數據: {orbital_file}")
        
        if not orbital_file.exists():
            raise FileNotFoundError(f"軌道計算輸出檔案不存在: {orbital_file}")
            
        try:
            with open(orbital_file, 'r', encoding='utf-8') as f:
                orbital_data = json.load(f)
                
            # 驗證數據格式
            if 'constellations' not in orbital_data:
                raise ValueError("軌道計算數據缺少 constellations 欄位")
                
            total_satellites = 0
            for constellation_name, constellation_data in orbital_data['constellations'].items():
                # 🔧 修復：使用正確的數據路徑
                if 'orbit_data' in constellation_data:
                    satellites_data = constellation_data['orbit_data'].get('satellites', {})
                    if isinstance(satellites_data, dict):
                        satellites_count = len(satellites_data)
                    else:
                        satellites_count = len(satellites_data) if hasattr(satellites_data, '__len__') else 0
                else:
                    satellites = constellation_data.get('satellites', [])
                    satellites_count = len(satellites)
                
                total_satellites += satellites_count
                logger.info(f"  {constellation_name}: {satellites_count} 顆衛星")
                
            logger.info(f"✅ 軌道計算數據載入完成: 總計 {total_satellites} 顆衛星")
            return orbital_data
            
        except Exception as e:
            logger.error(f"載入軌道計算數據失敗: {e}")
            raise
            
    def execute_refactored_intelligent_filtering(self, orbital_data: Dict[str, Any]) -> Dict[str, Any]:
        """執行重構版智能篩選流程"""
        logger.info("🎯 開始重構版智能衛星篩選...")
        logger.info("  🔧 使用統一仰角門檻管理器進行篩選")
        
        filtered_constellations = {}
        total_processed = 0
        total_filtered = 0
        
        # 對每個星座進行統一篩選
        for constellation_name, constellation_data in orbital_data.get('constellations', {}).items():
            logger.info(f"📡 處理 {constellation_name} 星座...")
            
            # 提取衛星數據
            if 'orbit_data' in constellation_data:
                satellites_data = constellation_data['orbit_data'].get('satellites', {})
                if isinstance(satellites_data, dict):
                    satellites_list = list(satellites_data.values())
                else:
                    satellites_list = satellites_data
            else:
                satellites_list = constellation_data.get('satellites', [])
            
            if not satellites_list:
                logger.warning(f"  ⚠️ {constellation_name} 無可用衛星數據")
                continue
            
            original_count = len(satellites_list)
            total_processed += original_count
            
            # 使用統一可見性服務進行篩選
            logger.info(f"  🔍 使用統一可見性服務篩選 {original_count} 顆衛星...")
            
            # 設定最小可見時間要求 (5分鐘)
            visible_satellites = self.visibility_service.filter_visible_satellites(
                satellites_list, constellation_name, min_visibility_duration_minutes=5.0
            )
            
            # 進一步使用統一仰角管理器進行品質篩選
            logger.info(f"  📐 使用統一仰角門檻管理器進行品質篩選...")
            
            high_quality_satellites = []
            for satellite in visible_satellites:
                # 檢查衛星是否有足夠的高品質時間點
                timeseries = satellite.get('position_timeseries', [])
                optimal_points = 0
                
                for point in timeseries:
                    visibility_info = point.get('visibility_info', {})
                    elevation = visibility_info.get('elevation_deg', 0)
                    
                    # 檢查是否達到最佳仰角
                    if self.elevation_manager.is_satellite_optimal(elevation, constellation_name):
                        optimal_points += 1
                
                # 如果有至少10個最佳品質點 (5分鐘)，保留此衛星
                if optimal_points >= 10:
                    high_quality_satellites.append(satellite)
            
            filtered_count = len(high_quality_satellites)
            total_filtered += filtered_count
            
            # 保存篩選結果
            filtered_constellations[constellation_name] = {
                'satellites': high_quality_satellites,
                'metadata': {
                    'constellation': constellation_name,
                    'original_count': original_count,
                    'visible_count': len(visible_satellites),
                    'final_filtered_count': filtered_count,
                    'filtering_method': 'unified_elevation_visibility_service',
                    'min_elevation_threshold': self.elevation_manager.get_min_elevation(constellation_name),
                    'optimal_elevation_threshold': self.elevation_manager.get_optimal_elevation(constellation_name),
                    'min_visibility_duration_minutes': 5.0,
                    'min_optimal_points_required': 10,
                    'processing_timestamp': datetime.now(timezone.utc).isoformat()
                }
            }
            
            logger.info(f"  ✅ {constellation_name} 篩選完成:")
            logger.info(f"    原始: {original_count} → 可見: {len(visible_satellites)} → 高品質: {filtered_count}")
            logger.info(f"    保留率: {filtered_count/original_count*100:.1f}%")
        
        # 生成統一篩選結果
        filtering_result = {
            'metadata': {
                'filtering_version': 'refactored_v1.0',
                'processing_timestamp': datetime.now(timezone.utc).isoformat(),
                'observer_location': {
                    'latitude': self.observer_lat,
                    'longitude': self.observer_lon,
                    'location_name': 'NTPU'
                },
                'filtering_method': 'unified_elevation_visibility_service',
                'unified_filtering_results': {
                    'total_processed': total_processed,
                    'total_selected': total_filtered,
                    'starlink_selected': filtered_constellations.get('starlink', {}).get('metadata', {}).get('final_filtered_count', 0),
                    'oneweb_selected': filtered_constellations.get('oneweb', {}).get('metadata', {}).get('final_filtered_count', 0),
                    'overall_retention_rate': f"{total_filtered/total_processed*100:.1f}%" if total_processed > 0 else "0%"
                },
                'elevation_thresholds_used': {
                    'starlink_min': self.elevation_manager.get_min_elevation('starlink'),
                    'starlink_optimal': self.elevation_manager.get_optimal_elevation('starlink'),
                    'oneweb_min': self.elevation_manager.get_min_elevation('oneweb'),
                    'oneweb_optimal': self.elevation_manager.get_optimal_elevation('oneweb')
                },
                'intelligent_filtering_completion': 'complete',
                'ready_for_signal_analysis': True,
                'refactoring_notes': 'Removed duplicate elevation logic, using unified managers'
            },
            'constellations': filtered_constellations
        }
        
        logger.info("✅ 重構版智能篩選完成")
        logger.info(f"  📊 處理總計: {total_processed} 顆衛星")
        logger.info(f"  🎯 篩選結果: {total_filtered} 顆衛星 ({total_filtered/total_processed*100:.1f}%)")
        logger.info("  🔧 已移除重複仰角邏輯，統一使用共用管理器")
        
        return filtering_result
            
    def execute_intelligent_filtering(self, orbital_data: Dict[str, Any]) -> Dict[str, Any]:
        """執行智能篩選流程 (向後兼容包裝)"""
        logger.info("🔄 重定向到重構版智能篩選流程...")
        return self.execute_refactored_intelligent_filtering(orbital_data)
            
    def save_intelligent_filtering_output(self, filtered_data: Dict[str, Any]) -> str:
        """保存智能篩選輸出數據 - v3.0 清理舊檔案版本"""
        # 確保輸出到正確的 leo_outputs 目錄
        leo_outputs_dir = self.output_dir / "leo_outputs"
        leo_outputs_dir.mkdir(parents=True, exist_ok=True)
        output_file = leo_outputs_dir / "intelligent_filtered_output.json"
        
        # 🗑️ 清理舊檔案 - 確保資料一致性
        if output_file.exists():
            file_size = output_file.stat().st_size
            logger.info(f"🗑️ 清理舊智能篩選輸出檔案: {output_file}")
            logger.info(f"   舊檔案大小: {file_size / (1024*1024):.1f} MB")
            output_file.unlink()
            logger.info("✅ 舊檔案已刪除")
        
        # 添加重構版標記
        filtered_data['metadata'].update({
            'filtering_timestamp': datetime.now(timezone.utc).isoformat(),
            'file_generation': 'refactored_clean_regeneration',
            'refactoring_improvements': [
                'unified_elevation_threshold_manager',
                'unified_visibility_service',
                'removed_duplicate_elevation_logic',
                'improved_quality_filtering'
            ]
        })
        
        # 💾 生成新的智能篩選輸出檔案
        logger.info(f"💾 生成重構版智能篩選輸出檔案: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(filtered_data, f, indent=2, ensure_ascii=False)
            
        # 檢查新檔案大小
        new_file_size = output_file.stat().st_size
        logger.info(f"✅ 重構版智能篩選數據已保存: {output_file}")
        logger.info(f"   新檔案大小: {new_file_size / (1024*1024):.1f} MB")
        logger.info(f"   包含衛星數: {filtered_data['metadata'].get('unified_filtering_results', {}).get('total_selected', 'unknown')}")
        logger.info("   🎯 重構改進: 統一管理器, 移除重複邏輯")
        
        return str(output_file)
        
    def process_intelligent_filtering(self, orbital_file: Optional[str] = None, orbital_data: Optional[Dict[str, Any]] = None, 
                      save_output: bool = True) -> Dict[str, Any]:
        """執行完整的智能篩選處理流程 (重構版)"""
        logger.info("🚀 開始重構版智能衛星篩選處理")
        logger.info("  🔧 使用統一仰角門檻管理器和可見性服務")
        
        # 1. 載入軌道計算數據（優先使用內存數據）
        if orbital_data is not None:
            logger.info("📥 使用提供的軌道計算內存數據")
            # 驗證內存數據格式
            if 'constellations' not in orbital_data:
                raise ValueError("軌道計算數據缺少 constellations 欄位")
            total_satellites = 0
            for constellation_name, constellation_data in orbital_data['constellations'].items():
                satellites = constellation_data.get('orbit_data', {}).get('satellites', {})
                total_satellites += len(satellites)
                logger.info(f"  {constellation_name}: {len(satellites)} 顆衛星")
            logger.info(f"✅ 軌道計算內存數據驗證完成: 總計 {total_satellites} 顆衛星")
        else:
            orbital_data = self.load_orbital_calculation_output(orbital_file)
        
        # 2. 執行重構版智能篩選
        filtered_data = self.execute_refactored_intelligent_filtering(orbital_data)
        
        # 3. 可選的輸出策略
        output_file = None
        if save_output:
            output_file = self.save_intelligent_filtering_output(filtered_data)
            logger.info(f"💾 重構版智能篩選數據已保存到: {output_file}")
        else:
            logger.info("🚀 智能篩選使用內存傳遞模式，未保存檔案")
        
        logger.info("✅ 重構版智能篩選處理完成")
        
        # 獲取篩選結果統計
        total_selected = filtered_data['metadata'].get('unified_filtering_results', {}).get('total_selected', 0)
        starlink_selected = filtered_data['metadata'].get('unified_filtering_results', {}).get('starlink_selected', 0)
        oneweb_selected = filtered_data['metadata'].get('unified_filtering_results', {}).get('oneweb_selected', 0)
        
        logger.info(f"  📊 篩選的衛星數: {total_selected} (Starlink: {starlink_selected}, OneWeb: {oneweb_selected})")
        logger.info("  🎯 重構改進: 移除重複仰角邏輯，統一使用共用管理器")
        if output_file:
            logger.info(f"  📁 輸出檔案: {output_file}")
        
        return filtered_data

    def process_stage2(self, stage1_file: Optional[str] = None, stage1_data: Optional[Dict[str, Any]] = None, 
                      save_output: bool = True) -> Dict[str, Any]:
        """向後兼容的階段處理方法 - 重定向到智能篩選處理方法"""
        logger.warning("⚠️ process_stage2 已棄用，請使用 process_intelligent_filtering")
        logger.info("🔄 自動重定向到重構版智能篩選處理...")
        return self.process_intelligent_filtering(stage1_file, stage1_data, save_output)

def main():
    """主函數"""
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    logger.info("============================================================")
    logger.info("智能衛星篩選處理")
    logger.info("============================================================")
    
    try:
        processor = IntelligentSatelliteFilterProcessor()
        result = processor.process_intelligent_filtering()
        
        logger.info("🎉 智能衛星篩選處理成功完成！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 智能衛星篩選處理失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)