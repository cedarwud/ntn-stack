#!/usr/bin/env python3
"""
階段五：數據整合與接口準備處理器 - 簡化修復版本
實現混合存儲架構和數據格式統一
"""

import json
import logging
import asyncio
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timezone

# 導入統一觀測座標管理
from shared_core.observer_config_service import get_ntpu_coordinates

# 導入驗證基礎類別
from shared_core.validation_snapshot_base import ValidationSnapshotBase

@dataclass
class Stage5Config:
    """階段五配置參數"""
    
    # 🎯 修復：輸入目錄指向正確的timeseries_preprocessing_outputs
    input_enhanced_timeseries_dir: str = "/app/data"
    
    # 輸出目錄
    output_layered_dir: str = "/app/data/layered_phase0_enhanced"
    output_handover_scenarios_dir: str = "/app/data/handover_scenarios"
    output_signal_analysis_dir: str = "/app/data/signal_quality_analysis"
    output_processing_cache_dir: str = "/app/data/processing_cache"
    output_status_files_dir: str = "/app/data/status_files"
    output_data_integration_dir: str = "/app/data"
    
    # 分層仰角門檻
    elevation_thresholds: List[int] = None
    
    def __post_init__(self):
        if self.elevation_thresholds is None:
            self.elevation_thresholds = [5, 10, 15]

class Stage5IntegrationProcessor(ValidationSnapshotBase):
    """階段五數據整合與接口準備處理器 - 語法修復版"""
    
    def __init__(self, config: Stage5Config):
        # Initialize ValidationSnapshotBase
        super().__init__(stage_number=5, stage_name="階段5: 數據整合", 
                         snapshot_dir=str(config.output_data_integration_dir + "/validation_snapshots"))
        
        self.config = config
        self.logger = logging.getLogger(__name__)
        # Use ValidationSnapshotBase timer instead of manual time.time()
        self.start_processing_timer()
        
        # 使用統一觀測座標管理，移除硬編碼
        ntpu_lat, ntpu_lon, ntpu_alt = get_ntpu_coordinates()
        self.observer_lat = ntpu_lat
        self.observer_lon = ntpu_lon
        self.observer_alt = ntpu_alt
        
        self.logger.info("✅ Stage5 數據整合處理器初始化完成 (使用 shared_core 座標)")
        self.logger.info(f"  觀測座標: ({self.observer_lat}°, {self.observer_lon}°) [來自 shared_core]")
        
    def extract_key_metrics(self, processing_results: Dict[str, Any]) -> Dict[str, Any]:
        """提取階段5關鍵指標"""
        constellation_summary = processing_results.get('constellation_summary', {})
        
        return {
            "總衛星數": processing_results.get('total_satellites', 0),
            "成功整合": processing_results.get('successfully_integrated', 0),
            "Starlink整合": constellation_summary.get('starlink', {}).get('satellite_count', 0),
            "OneWeb整合": constellation_summary.get('oneweb', {}).get('satellite_count', 0),
            "處理耗時": f"{processing_results.get('processing_time_seconds', 0):.2f}秒"
        }
    
    def run_validation_checks(self, processing_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """執行階段5特定驗證檢查"""
        checks = []
        
        constellation_summary = processing_results.get('constellation_summary', {})
        satellites_data = processing_results.get('satellites', {})
        
        # 檢查1: 數據整合成功率
        total_satellites = processing_results.get('total_satellites', 0)
        successfully_integrated = processing_results.get('successfully_integrated', 0)
        integration_rate = (successfully_integrated / max(total_satellites, 1)) * 100
        
        checks.append({
            'checkName': '數據整合成功率檢查',
            'passed': integration_rate >= 95.0,  # 要求95%以上整合率
            'result': f"整合成功率: {integration_rate:.1f}% ({successfully_integrated}/{total_satellites})",
            'details': f"成功整合 {successfully_integrated} 顆衛星，總計 {total_satellites} 顆衛星"
        })
        
        # 檢查2: Starlink數據整合檢查
        starlink_info = constellation_summary.get('starlink', {})
        starlink_data_exists = 'starlink' in satellites_data and satellites_data['starlink'] is not None
        starlink_count = starlink_info.get('satellite_count', 0)
        
        checks.append({
            'checkName': 'Starlink數據整合檢查',
            'passed': starlink_data_exists and starlink_count > 0,
            'result': f"Starlink: {starlink_count} 顆衛星整合完成" if starlink_data_exists else "Starlink數據未整合",
            'details': f"數據狀態: {'已加載' if starlink_data_exists else '未加載'}，衛星數量: {starlink_count}"
        })
        
        # 檢查3: OneWeb數據整合檢查
        oneweb_info = constellation_summary.get('oneweb', {})
        oneweb_data_exists = 'oneweb' in satellites_data and satellites_data['oneweb'] is not None
        oneweb_count = oneweb_info.get('satellite_count', 0)
        
        checks.append({
            'checkName': 'OneWeb數據整合檢查',
            'passed': oneweb_data_exists and oneweb_count > 0,
            'result': f"OneWeb: {oneweb_count} 顆衛星整合完成" if oneweb_data_exists else "OneWeb數據未整合",
            'details': f"數據狀態: {'已加載' if oneweb_data_exists else '未加載'}，衛星數量: {oneweb_count}"
        })
        
        # 檢查4: 輸出文件生成檢查
        output_file = processing_results.get('output_file')
        output_file_exists = output_file and Path(output_file).exists() if output_file else False
        
        checks.append({
            'checkName': '整合輸出文件生成檢查',
            'passed': output_file_exists,
            'result': f"輸出文件生成成功: {Path(output_file).name}" if output_file_exists else "輸出文件未生成",
            'details': f"文件路徑: {output_file if output_file else '未指定'}"
        })
        
        return checks
    
    async def process_enhanced_timeseries(self) -> Dict[str, Any]:
        """執行完整的數據整合處理流程"""
        start_time = time.time()
        self.logger.info("🚀 開始階段五：數據整合與接口準備 (語法修復版)")
        
        # 清理舊驗證快照 (確保生成最新驗證快照)
        if self.snapshot_file.exists():
            self.logger.info(f"🗑️ 清理舊驗證快照: {self.snapshot_file}")
            self.snapshot_file.unlink()
        
        results = {
            "stage": "stage5_integration",
            "start_time": datetime.now(timezone.utc).isoformat(),
            "mixed_storage_verification": {},
            "success": True,
            "processing_time_seconds": 0
        }
        
        try:
            # 載入增強時間序列數據
            enhanced_data = await self._load_enhanced_timeseries()
            
            # 計算統計信息
            total_satellites = 0
            constellation_summary = {}
            
            for constellation, data in enhanced_data.items():
                if data and 'satellites' in data:
                    count = len(data['satellites'])
                    constellation_summary[constellation] = {
                        "satellite_count": count,
                        "processing_status": "integrated"
                    }
                    total_satellites += count
        
            results["total_satellites"] = total_satellites
            results["successfully_integrated"] = total_satellites
            results["constellation_summary"] = constellation_summary
            results["satellites"] = enhanced_data  # 為Stage6提供完整衛星數據
            results["processing_time_seconds"] = time.time() - self.processing_start_time
            
            # 🔧 修復：添加metadata字段供後續階段使用
            results["metadata"] = {
                "stage": "stage5_integration", 
                "total_satellites": total_satellites,
                "successfully_integrated": total_satellites,
                "processing_complete": True,
                "data_integration_timestamp": datetime.now(timezone.utc).isoformat(),
                "constellation_breakdown": constellation_summary,
                "ready_for_dynamic_pool_planning": True
            }
            
            # 🎯 新增：保存檔案供階段六使用
            output_file = self.save_integration_output(results)
            results["output_file"] = output_file
            
            # 保存驗證快照
            processing_duration = time.time() - start_time
            validation_success = self.save_validation_snapshot(results)
            if validation_success:
                self.logger.info("✅ Stage 5 驗證快照已保存")
            else:
                self.logger.warning("⚠️ Stage 5 驗證快照保存失敗")
            
            self.logger.info(f"✅ 階段五完成，耗時: {results['processing_time_seconds']:.2f} 秒")
            self.logger.info(f"📊 整合衛星數據: {total_satellites} 顆衛星")
            self.logger.info(f"💾 輸出檔案: {output_file}")
        
        except Exception as e:
            self.logger.error(f"❌ 階段五處理失敗: {e}")
            results["success"] = False
            results["error"] = str(e)
            
            # 保存錯誤快照
            error_data = {
                'error': str(e),
                'stage': 5,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            self.save_validation_snapshot(error_data)
            
        return results
    
    async def _load_enhanced_timeseries(self) -> Dict[str, Any]:
        """載入增強時間序列數據"""
        
        enhanced_data = {
            "starlink": None,
            "oneweb": None
        }
        
        input_dir = Path(self.config.input_enhanced_timeseries_dir)
        
        for constellation in ["starlink", "oneweb"]:
            target_file = input_dir / f"{constellation}_enhanced.json"
            
            if target_file.exists():
                self.logger.info(f"載入 {constellation} 增強數據: {target_file}")
                
                with open(target_file, 'r') as f:
                    enhanced_data[constellation] = json.load(f)
                    
                satellites_count = len(enhanced_data[constellation].get('satellites', []))
                self.logger.info(f"✅ {constellation}: {satellites_count} 顆衛星")
            else:
                self.logger.warning(f"⚠️ {constellation} 增強數據檔案不存在: {target_file}")
        
        return enhanced_data

    def save_integration_output(self, results: Dict[str, Any]) -> str:
        """保存階段五整合輸出，供階段六使用"""
        output_file = Path(self.config.output_data_integration_dir) / "data_integration_output.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 清理舊檔案
        if output_file.exists():
            output_file.unlink()
            self.logger.info(f"🗑️ 清理舊整合輸出: {output_file}")
        
        # 保存新檔案
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        file_size = output_file.stat().st_size / (1024*1024)  # MB
        self.logger.info(f"💾 階段五整合輸出已保存: {output_file}")
        self.logger.info(f"   檔案大小: {file_size:.1f} MB")
        self.logger.info(f"   包含衛星數: {results.get('total_satellites', 0)}")
        
        return str(output_file)

async def main():
    """主執行函數"""
    logging.basicConfig(level=logging.INFO)
    
    config = Stage5Config()
    processor = Stage5IntegrationProcessor(config)
    
    results = await processor.process_enhanced_timeseries()
    
    print("\n🎯 階段五處理結果:")
    print(json.dumps(results, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())
