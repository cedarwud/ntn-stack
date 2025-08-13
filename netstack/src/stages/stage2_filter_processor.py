#!/usr/bin/env python3
"""
階段二：智能衛星篩選處理器 - 執行封裝器

完全遵循 @docs/satellite_data_preprocessing.md 規範：
- 接收階段一輸出的完整衛星軌道數據
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

class Stage2FilterProcessor:
    """階段二：智能衛星篩選處理器封裝
    
    職責：
    1. 載入階段一輸出的完整軌道數據
    2. 執行統一智能篩選流程
    3. 保存階段二篩選結果
    4. 為階段三提供高品質輸入
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
        
        logger.info("✅ 階段二處理器初始化完成")
        logger.info(f"  輸入目錄: {self.input_dir}")
        logger.info(f"  輸出目錄: {self.output_dir}")
        logger.info(f"  觀測座標: ({self.observer_lat}°, {self.observer_lon}°)")
        
    def load_stage1_output(self, stage1_file: Optional[str] = None) -> Dict[str, Any]:
        """載入階段一輸出數據"""
        if stage1_file is None:
            stage1_file = self.input_dir / "stage1_tle_sgp4_output.json"
        else:
            stage1_file = Path(stage1_file)
            
        logger.info(f"📥 載入階段一數據: {stage1_file}")
        
        if not stage1_file.exists():
            raise FileNotFoundError(f"階段一輸出檔案不存在: {stage1_file}")
            
        try:
            with open(stage1_file, 'r', encoding='utf-8') as f:
                stage1_data = json.load(f)
                
            # 驗證數據格式
            if 'constellations' not in stage1_data:
                raise ValueError("階段一數據缺少 constellations 欄位")
                
            total_satellites = 0
            for constellation_name, constellation_data in stage1_data['constellations'].items():
                satellites = constellation_data.get('satellites', [])
                total_satellites += len(satellites)
                logger.info(f"  {constellation_name}: {len(satellites)} 顆衛星")
                
            logger.info(f"✅ 階段一數據載入完成: 總計 {total_satellites} 顆衛星")
            return stage1_data
            
        except Exception as e:
            logger.error(f"載入階段一數據失敗: {e}")
            raise
            
    def execute_intelligent_filtering(self, stage1_data: Dict[str, Any]) -> Dict[str, Any]:
        """執行智能篩選流程"""
        logger.info("🎯 開始智能衛星篩選...")
        
        # 階段二採用動態篩選 - 不設固定數量限制，依據篩選條件動態決定
        # 移除硬編碼數量，讓智能篩選系統根據實際條件動態篩選
        selection_config = None  # 使用動態篩選模式
        
        try:
            # 執行完整智能篩選流程
            filtered_result = self.filter_system.process_complete_filtering(
                stage1_data, 
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
            
    def save_stage2_output(self, filtered_data: Dict[str, Any]) -> str:
        """保存階段二輸出數據"""
        output_file = self.output_dir / "stage2_intelligent_filtered_output.json"
        
        # 添加階段二完成標記
        filtered_data['metadata'].update({
            'stage2_completion': 'intelligent_filtering_complete',
            'stage2_timestamp': datetime.now(timezone.utc).isoformat(),
            'ready_for_stage3': True
        })
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(filtered_data, f, indent=2, ensure_ascii=False)
            
        logger.info(f"💾 階段二數據已保存到: {output_file}")
        return str(output_file)
        
    def process_stage2(self, stage1_file: Optional[str] = None, stage1_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """執行完整的階段二處理流程"""
        logger.info("🚀 開始階段二：智能衛星篩選")
        
        # 1. 載入階段一數據（優先使用內存數據）
        if stage1_data is not None:
            logger.info("📥 使用提供的階段一內存數據")
            # 驗證內存數據格式
            if 'constellations' not in stage1_data:
                raise ValueError("階段一數據缺少 constellations 欄位")
            total_satellites = 0
            for constellation_name, constellation_data in stage1_data['constellations'].items():
                satellites = constellation_data.get('orbit_data', {}).get('satellites', {})
                total_satellites += len(satellites)
                logger.info(f"  {constellation_name}: {len(satellites)} 顆衛星")
            logger.info(f"✅ 階段一內存數據驗證完成: 總計 {total_satellites} 顆衛星")
        else:
            stage1_data = self.load_stage1_output(stage1_file)
        
        # 2. 執行智能篩選
        filtered_data = self.execute_intelligent_filtering(stage1_data)
        
        # 3. 保存輸出
        output_file = self.save_stage2_output(filtered_data)
        
        logger.info("✅ 階段二處理完成")
        # 獲取篩選結果統計
        total_selected = filtered_data['metadata'].get('unified_filtering_results', {}).get('total_selected', 0)
        starlink_selected = filtered_data['metadata'].get('unified_filtering_results', {}).get('starlink_selected', 0)
        oneweb_selected = filtered_data['metadata'].get('unified_filtering_results', {}).get('oneweb_selected', 0)
        
        logger.info(f"  篩選的衛星數: {total_selected} (Starlink: {starlink_selected}, OneWeb: {oneweb_selected})")
        logger.info(f"  輸出檔案: {output_file}")
        
        return filtered_data

def main():
    """主函數"""
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    logger.info("============================================================")
    logger.info("階段二：智能衛星篩選")
    logger.info("============================================================")
    
    try:
        processor = Stage2FilterProcessor()
        result = processor.process_stage2()
        
        logger.info("🎉 階段二處理成功完成！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 階段二處理失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)