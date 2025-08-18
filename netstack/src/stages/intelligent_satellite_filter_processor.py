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
    """智能衛星篩選處理器封裝
    
    職責：
    1. 載入軌道計算輸出的完整軌道數據
    2. 執行統一智能篩選流程
    3. 保存智能篩選結果
    4. 為後續信號分析提供高品質輸入
    """
    
    def __init__(self, observer_lat: float = 24.9441667, observer_lon: float = 121.3713889,
                 input_dir: str = "/app/data", output_dir: str = "/app/data"):
        self.observer_lat = observer_lat
        self.observer_lon = observer_lon
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 創建統一智能篩選系統
        self.filter_system = create_unified_intelligent_filter(observer_lat, observer_lon)
        
        logger.info("✅ 智能衛星篩選處理器初始化完成")
        logger.info(f"  輸入目錄: {self.input_dir}")
        logger.info(f"  輸出目錄: {self.output_dir}")
        logger.info(f"  觀測座標: ({self.observer_lat}°, {self.observer_lon}°)")
        
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
                satellites = constellation_data.get('satellites', [])
                total_satellites += len(satellites)
                logger.info(f"  {constellation_name}: {len(satellites)} 顆衛星")
                
            logger.info(f"✅ 軌道計算數據載入完成: 總計 {total_satellites} 顆衛星")
            return orbital_data
            
        except Exception as e:
            logger.error(f"載入軌道計算數據失敗: {e}")
            raise
            
    def execute_intelligent_filtering(self, orbital_data: Dict[str, Any]) -> Dict[str, Any]:
        """執行智能篩選流程"""
        logger.info("🎯 開始智能衛星篩選...")
        
        # 智能篩選採用動態篩選 - 不設固定數量限制，依據篩選條件動態決定
        # 移除硬編碼數量，讓智能篩選系統根據實際條件動態篩選
        selection_config = None  # 使用動態篩選模式
        
        try:
            # 執行智能篩選專用流程（不包含信號品質和事件分析）
            filtered_result = self.filter_system.process_f2_filtering_only(
                orbital_data, 
                selection_config
            )
            
            # 驗證篩選結果
            validation = self.filter_system.validate_filtering_results(filtered_result)
            
            if not validation['overall_quality']:
                logger.warning("⚠️ 篩選結果品質檢查未完全通過")
                for key, status in validation.items():
                    if not status:
                        logger.warning(f"   {key}: 未通過")
            else:
                logger.info("✅ 篩選結果品質檢查全部通過")
            
            return filtered_result
            
        except Exception as e:
            logger.error(f"智能篩選執行失敗: {e}")
            raise
            
    def save_intelligent_filtering_output(self, filtered_data: Dict[str, Any]) -> str:
        """保存智能篩選輸出數據 - v3.0 清理舊檔案版本"""
        output_file = self.output_dir / "intelligent_filtered_output.json"
        
        # 🗑️ 清理舊檔案 - 確保資料一致性
        if output_file.exists():
            file_size = output_file.stat().st_size
            logger.info(f"🗑️ 清理舊智能篩選輸出檔案: {output_file}")
            logger.info(f"   舊檔案大小: {file_size / (1024*1024):.1f} MB")
            output_file.unlink()
            logger.info("✅ 舊檔案已刪除")
        
        # 添加智能篩選完成標記
        filtered_data['metadata'].update({
            'intelligent_filtering_completion': 'complete',
            'filtering_timestamp': datetime.now(timezone.utc).isoformat(),
            'ready_for_signal_analysis': True,
            'file_generation': 'clean_regeneration'  # 標記為重新生成
        })
        
        # 💾 生成新的智能篩選輸出檔案
        logger.info(f"💾 生成新的智能篩選輸出檔案: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(filtered_data, f, indent=2, ensure_ascii=False)
            
        # 檢查新檔案大小
        new_file_size = output_file.stat().st_size
        logger.info(f"✅ 智能篩選數據已保存: {output_file}")
        logger.info(f"   新檔案大小: {new_file_size / (1024*1024):.1f} MB")
        logger.info(f"   包含衛星數: {filtered_data['metadata'].get('unified_filtering_results', {}).get('total_selected', 'unknown')}")
        
        return str(output_file)
        
    def process_intelligent_filtering(self, orbital_file: Optional[str] = None, orbital_data: Optional[Dict[str, Any]] = None, 
                      save_output: bool = True) -> Dict[str, Any]:
        """執行完整的智能篩選處理流程"""
        logger.info("🚀 開始智能衛星篩選處理")
        
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
        
        # 2. 執行智能篩選
        filtered_data = self.execute_intelligent_filtering(orbital_data)
        
        # 3. 可選的輸出策略
        output_file = None
        if save_output:
            output_file = self.save_intelligent_filtering_output(filtered_data)
            logger.info(f"💾 智能篩選數據已保存到: {output_file}")
        else:
            logger.info("🚀 智能篩選使用內存傳遞模式，未保存檔案")
        
        logger.info("✅ 智能篩選處理完成")
        # 獲取篩選結果統計
        total_selected = filtered_data['metadata'].get('unified_filtering_results', {}).get('total_selected', 0)
        starlink_selected = filtered_data['metadata'].get('unified_filtering_results', {}).get('starlink_selected', 0)
        oneweb_selected = filtered_data['metadata'].get('unified_filtering_results', {}).get('oneweb_selected', 0)
        
        logger.info(f"  篩選的衛星數: {total_selected} (Starlink: {starlink_selected}, OneWeb: {oneweb_selected})")
        if output_file:
            logger.info(f"  輸出檔案: {output_file}")
        
        return filtered_data

    def process_stage2(self, stage1_file: Optional[str] = None, stage1_data: Optional[Dict[str, Any]] = None, 
                      save_output: bool = True) -> Dict[str, Any]:
        """向後兼容的階段處理方法 - 重定向到智能篩選處理方法"""
        logger.warning("⚠️ process_stage2 已棄用，請使用 process_intelligent_filtering")
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