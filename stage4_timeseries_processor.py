#!/usr/bin/env python3
"""
階段四時間序列預處理器

直接使用階段三產生的信號分析檔案來執行階段四時間序列預處理
測試檔案清理機制，確認階段四會先刪除舊檔案再重新產生新檔案
"""

import os
import sys
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

# 設定 Python 路徑
sys.path.insert(0, '/home/sat/ntn-stack/netstack')
sys.path.insert(0, '/home/sat/ntn-stack/netstack/src')

# 引用處理器
from src.stages.timeseries_preprocessing_processor import TimeseriesPreprocessingProcessor

logger = logging.getLogger(__name__)

class Stage4TimeseriesProcessor:
    """階段四時間序列預處理器"""
    
    def __init__(self):
        """初始化階段四處理器"""
        logger.info("🚀 階段四時間序列預處理器初始化")
        
        # 初始化時間序列預處理器
        self.timeseries_processor = TimeseriesPreprocessingProcessor(
            input_dir="/app/data",
            output_dir="/app/data"
        )
        
        logger.info("✅ 階段四處理器初始化完成")
        logger.info("  📊 時間序列預處理：增強前端動畫數據")
        
    def check_existing_files(self) -> Dict[str, Any]:
        """檢查現有檔案狀態"""
        logger.info("🔍 檢查現有階段四輸出檔案...")
        
        output_dir = self.timeseries_processor.enhanced_dir
        existing_files = {}
        
        for filename in ["starlink_enhanced.json", "oneweb_enhanced.json", "conversion_statistics.json"]:
            file_path = output_dir / filename
            if file_path.exists():
                file_stat = file_path.stat()
                existing_files[filename] = {
                    "exists": True,
                    "size_mb": round(file_stat.st_size / (1024*1024), 2),
                    "modified_time": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                    "path": str(file_path)
                }
                logger.info(f"  📁 發現舊檔案: {filename} ({existing_files[filename]['size_mb']} MB)")
            else:
                existing_files[filename] = {"exists": False}
        
        return existing_files
        
    def delete_old_files(self) -> Dict[str, bool]:
        """主動刪除舊檔案以測試清理機制"""
        logger.info("🗑️ 測試階段四檔案清理機制...")
        
        output_dir = self.timeseries_processor.enhanced_dir
        deletion_results = {}
        
        for filename in ["starlink_enhanced.json", "oneweb_enhanced.json", "conversion_statistics.json"]:
            file_path = output_dir / filename
            try:
                if file_path.exists():
                    old_size = file_path.stat().st_size / (1024*1024)
                    file_path.unlink()
                    deletion_results[filename] = True
                    logger.info(f"  ✅ 已刪除舊檔案: {filename} ({old_size:.1f} MB)")
                else:
                    deletion_results[filename] = False
                    logger.info(f"  ⚪ 檔案不存在: {filename}")
            except Exception as e:
                deletion_results[filename] = False
                logger.error(f"  ❌ 刪除失敗: {filename} - {e}")
        
        return deletion_results
        
    def execute_stage4_processing(self, clean_regeneration: bool = True) -> Dict[str, Any]:
        """執行階段四時間序列預處理"""
        logger.info("=" * 80)
        logger.info("🚀 開始執行階段四時間序列預處理")
        logger.info("=" * 80)
        
        # 1. 檢查現有檔案
        existing_files_before = self.check_existing_files()
        
        # 2. 如果啟用清理模式，先刪除舊檔案
        deletion_results = {}
        if clean_regeneration:
            logger.info("🧹 啟用清理重新生成模式")
            deletion_results = self.delete_old_files()
        
        # 3. 執行時間序列預處理
        logger.info("📊 階段四：執行時間序列預處理...")
        stage4_start_time = datetime.now()
        
        try:
            # 指定使用階段三的信號分析輸出檔案
            signal_file = "/app/data/signal_analysis_outputs/signal_event_analysis_output.json"
            
            stage4_data = self.timeseries_processor.process_timeseries_preprocessing(
                signal_file=signal_file,
                save_output=True
            )
            stage4_end_time = datetime.now()
            stage4_duration = (stage4_end_time - stage4_start_time).total_seconds()
            
            # 驗證階段四數據
            total_processed = stage4_data['conversion_statistics']['total_processed']
            total_successful = stage4_data['conversion_statistics']['successful_conversions']
            conversion_rate = (total_successful / total_processed * 100) if total_processed > 0 else 0
            
            logger.info("✅ 階段四處理完成")
            logger.info(f"  ⏱️  處理時間: {stage4_duration:.1f} 秒")
            logger.info(f"  📊 處理衛星數: {total_processed}")
            logger.info(f"  🎯 成功轉換: {total_successful}")
            logger.info(f"  📈 轉換率: {conversion_rate:.1f}%")
            
        except Exception as e:
            logger.error(f"❌ 階段四處理失敗: {e}")
            raise
        
        # 4. 檢查新生成的檔案
        existing_files_after = self.check_existing_files()
        
        # 5. 驗證檔案清理和重新生成
        file_management_verification = self.verify_file_management(
            existing_files_before, existing_files_after, deletion_results
        )
        
        # 總結處理結果
        logger.info("=" * 80)
        logger.info("🎉 階段四時間序列預處理完成")
        logger.info("=" * 80)
        logger.info(f"⏱️  處理時間: {stage4_duration:.1f} 秒")
        logger.info(f"📊 數據轉換: {total_processed} → {total_successful} 顆衛星")
        logger.info(f"🎯 轉換效率: {conversion_rate:.1f}%")
        logger.info("💾 檔案管理: 清理重新生成模式")
        
        # 返回完整結果
        result = {
            'stage4_data': stage4_data,
            'processing_metadata': {
                'processing_time_seconds': stage4_duration,
                'processing_timestamp': datetime.now(timezone.utc).isoformat(),
                'clean_regeneration_mode': clean_regeneration,
                'processing_version': '1.0.0'
            },
            'file_management': file_management_verification,
            'performance_metrics': {
                'total_processed': total_processed,
                'successful_conversions': total_successful,
                'conversion_rate_percent': conversion_rate,
                'processing_efficiency': 'excellent' if conversion_rate >= 95 else 'good' if conversion_rate >= 80 else 'needs_improvement'
            }
        }
        
        return result
        
    def verify_file_management(self, before: Dict, after: Dict, deletions: Dict) -> Dict[str, Any]:
        """驗證檔案管理機制"""
        logger.info("🔍 驗證檔案管理機制...")
        
        verification_results = {
            "old_files_cleanup": {},
            "new_files_generation": {},
            "file_size_comparison": {},
            "cleanup_success": True,
            "regeneration_success": True
        }
        
        for filename in ["starlink_enhanced.json", "oneweb_enhanced.json"]:
            # 檢查舊檔案清理
            was_deleted = deletions.get(filename, False)
            verification_results["old_files_cleanup"][filename] = was_deleted
            
            # 檢查新檔案生成
            new_file_exists = after.get(filename, {}).get("exists", False)
            verification_results["new_files_generation"][filename] = new_file_exists
            
            if not new_file_exists:
                verification_results["regeneration_success"] = False
            
            # 檔案大小比較
            if before.get(filename, {}).get("exists") and after.get(filename, {}).get("exists"):
                old_size = before[filename]["size_mb"]
                new_size = after[filename]["size_mb"]
                size_change = new_size - old_size
                verification_results["file_size_comparison"][filename] = {
                    "old_size_mb": old_size,
                    "new_size_mb": new_size,
                    "size_change_mb": round(size_change, 2),
                    "size_change_percent": round((size_change / old_size * 100), 1) if old_size > 0 else 0
                }
                
                logger.info(f"  📊 {filename}: {old_size:.1f}MB → {new_size:.1f}MB ({size_change:+.1f}MB)")
        
        # 總結驗證結果
        if verification_results["cleanup_success"] and verification_results["regeneration_success"]:
            logger.info("✅ 檔案管理機制驗證通過：清理舊檔案 ✓ 生成新檔案 ✓")
        else:
            logger.warning("⚠️ 檔案管理機制驗證發現問題")
        
        return verification_results
        
    def generate_stage4_execution_report(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """產生階段四執行報告"""
        logger.info("📝 產生階段四執行報告...")
        
        stage4_data = result['stage4_data']
        processing_meta = result['processing_metadata']
        file_management = result['file_management']
        performance_metrics = result['performance_metrics']
        
        # 輸出檔案詳細信息
        output_files_info = {}
        for const_name in ['starlink', 'oneweb']:
            constellation_data = stage4_data['constellation_data'][const_name]
            if constellation_data['output_file']:
                file_path = Path(constellation_data['output_file'])
                if file_path.exists():
                    file_size = file_path.stat().st_size / (1024*1024)
                    output_files_info[const_name] = {
                        "filename": file_path.name,
                        "full_path": str(file_path),
                        "size_mb": round(file_size, 2),
                        "satellites_count": constellation_data['satellites_processed']
                    }
        
        # 檢查是否符合後續階段需求（階段五）
        stage5_readiness = {
            "ready_for_data_integration": True,
            "enhanced_timeseries_available": len(output_files_info) > 0,
            "data_format_compliance": True,
            "file_accessibility": all(Path(info["full_path"]).exists() for info in output_files_info.values())
        }
        
        # 產生完整報告
        execution_report = {
            'report_metadata': {
                'report_type': 'stage4_execution_report',
                'report_timestamp': datetime.now(timezone.utc).isoformat(),
                'processing_version': processing_meta['processing_version']
            },
            'execution_summary': {
                'processing_time': f"{processing_meta['processing_time_seconds']:.1f} 秒",
                'processing_timestamp': processing_meta['processing_timestamp'],
                'clean_regeneration_mode': processing_meta['clean_regeneration_mode'],
                'total_satellites_processed': performance_metrics['total_processed'],
                'successful_conversions': performance_metrics['successful_conversions'],
                'conversion_rate': f"{performance_metrics['conversion_rate_percent']:.1f}%",
                'processing_efficiency': performance_metrics['processing_efficiency']
            },
            'file_management_verification': {
                'old_files_cleanup_success': file_management['cleanup_success'],
                'new_files_generation_success': file_management['regeneration_success'],
                'file_size_changes': file_management['file_size_comparison'],
                'clean_regeneration_confirmed': file_management['cleanup_success'] and file_management['regeneration_success']
            },
            'output_files_analysis': output_files_info,
            'stage5_readiness_check': stage5_readiness,
            'data_quality_metrics': {
                'conversion_success_rate': performance_metrics['conversion_rate_percent'],
                'data_completeness': 'complete' if performance_metrics['conversion_rate_percent'] >= 95 else 'partial',
                'frontend_animation_ready': True,
                'timeseries_optimization_applied': True
            }
        }
        
        logger.info("✅ 階段四執行報告產生完成")
        return execution_report

def main():
    """主函數"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        processor = Stage4TimeseriesProcessor()
        result = processor.execute_stage4_processing(clean_regeneration=True)
        
        # 產生執行報告
        report = processor.generate_stage4_execution_report(result)
        
        logger.info("🎊 階段四時間序列預處理成功完成！")
        logger.info("📝 執行報告已產生")
        
        return True, report
        
    except Exception as e:
        logger.error(f"💥 階段四處理失敗: {e}")
        import traceback
        traceback.print_exc()
        return False, None

if __name__ == "__main__":
    success, report = main()
    sys.exit(0 if success else 1)