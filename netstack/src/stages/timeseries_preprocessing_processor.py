#!/usr/bin/env python3
"""
時間序列預處理器
==============================

職責：將信號分析結果轉換為增強時間序列數據
輸入：signal_event_analysis_output.json
輸出：timeseries_preprocessing_outputs/ 目錄中的格式化數據
處理對象：554顆經過信號分析的衛星
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class TimeseriesPreprocessingProcessor:
    """時間序列預處理器
    
    將信號分析的複雜數據結構轉換為後續處理需要的 enhanced_timeseries 格式
    """
    
    def __init__(self, input_dir: str = "/app/data", output_dir: str = "/app/data"):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        # 使用標準化目錄結構，符合功能描述性命名
        self.enhanced_dir = self.output_dir / "timeseries_preprocessing_outputs"
        self.enhanced_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("✅ 時間序列預處理器初始化完成")
        logger.info(f"  輸入目錄: {self.input_dir}")
        logger.info(f"  增強時間序列輸出: {self.enhanced_dir}")
        
    def load_signal_analysis_output(self, signal_file: Optional[str] = None) -> Dict[str, Any]:
        """載入信號分析輸出數據"""
        if signal_file is None:
            # 使用功能描述性檔案路徑，符合命名規範
            signal_file = self.input_dir / "signal_analysis_outputs" / "signal_event_analysis_output.json"
        else:
            signal_file = Path(signal_file)
            
        logger.info(f"📥 載入信號分析數據: {signal_file}")
        
        if not signal_file.exists():
            raise FileNotFoundError(f"信號分析輸出檔案不存在: {signal_file}")
            
        try:
            with open(signal_file, 'r', encoding='utf-8') as f:
                signal_data = json.load(f)
                
            # 驗證數據格式
            if 'constellations' not in signal_data:
                raise ValueError("信號分析數據缺少 constellations 欄位")
                
            total_satellites = 0
            for constellation_name, constellation_data in signal_data['constellations'].items():
                satellites = constellation_data.get('satellites', [])
                total_satellites += len(satellites)
                logger.info(f"  {constellation_name}: {len(satellites)} 顆衛星")
                
            logger.info(f"✅ 信號分析數據載入完成: 總計 {total_satellites} 顆衛星")
            return signal_data
            
        except Exception as e:
            logger.error(f"載入信號分析數據失敗: {e}")
            raise
            
    def convert_to_enhanced_timeseries(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """將信號分析數據轉換為增強時間序列格式"""
        logger.info("🔄 開始時間序列數據轉換...")
        
        conversion_results = {
            "starlink": None,
            "oneweb": None,
            "conversion_statistics": {
                "total_processed": 0,
                "successful_conversions": 0,
                "failed_conversions": 0
            }
        }
        
        constellations = signal_data.get('constellations', {})
        
        for const_name, const_data in constellations.items():
            if const_name not in ['starlink', 'oneweb']:
                continue
                
            satellites = const_data.get('satellites', [])
            logger.info(f"📊 處理 {const_name}: {len(satellites)} 顆衛星")
            
            enhanced_satellites = []
            successful_count = 0
            failed_count = 0
            
            for satellite in satellites:
                try:
                    enhanced_satellite = self._convert_satellite_to_timeseries(satellite, const_name)
                    if enhanced_satellite:
                        enhanced_satellites.append(enhanced_satellite)
                        successful_count += 1
                    else:
                        failed_count += 1
                        
                except Exception as e:
                    sat_id = satellite.get('satellite_id', 'Unknown')
                    logger.warning(f"衛星 {sat_id} 轉換失敗: {e}")
                    failed_count += 1
            
            # 組裝星座數據
            enhanced_constellation = {
                "metadata": {
                    "constellation": const_name,
                    "processing_type": "timeseries_preprocessing",
                    "generation_time": datetime.now(timezone.utc).isoformat(),
                    "source_data": "signal_event_analysis",
                    "total_satellites": len(satellites),
                    "successful_conversions": successful_count,
                    "failed_conversions": failed_count,
                    "conversion_rate": f"{successful_count/len(satellites)*100:.1f}%" if satellites else "0%"
                },
                "satellites": enhanced_satellites,
                "constellation_statistics": {
                    "total_satellites": len(enhanced_satellites),
                    "avg_visibility_windows": sum(len(s.get('visibility_windows', [])) for s in enhanced_satellites) / len(enhanced_satellites) if enhanced_satellites else 0,
                    "avg_signal_quality": sum(s.get('signal_quality', {}).get('statistics', {}).get('mean_rsrp_dbm', -150) for s in enhanced_satellites) / len(enhanced_satellites) if enhanced_satellites else 0
                }
            }
            
            conversion_results[const_name] = enhanced_constellation
            conversion_results["conversion_statistics"]["total_processed"] += len(satellites)
            conversion_results["conversion_statistics"]["successful_conversions"] += successful_count
            conversion_results["conversion_statistics"]["failed_conversions"] += failed_count
            
            logger.info(f"✅ {const_name} 轉換完成: {successful_count}/{len(satellites)} 顆衛星成功")
        
        total_processed = conversion_results["conversion_statistics"]["total_processed"]
        total_successful = conversion_results["conversion_statistics"]["successful_conversions"]
        
        logger.info(f"🎯 時間序列轉換完成: {total_successful}/{total_processed} 顆衛星成功轉換")
        
        return conversion_results
        
    def _convert_satellite_to_timeseries(self, satellite: Dict[str, Any], constellation: str) -> Optional[Dict[str, Any]]:
        """將單顆衛星轉換為增強時間序列格式"""
        
        # 基本衛星信息
        enhanced_satellite = {
            "satellite_id": satellite.get('satellite_id', ''),
            "name": satellite.get('name', ''),
            "constellation": constellation,
            "norad_id": satellite.get('norad_id', 0)
        }
        
        # 1. 處理軌道數據
        orbit_data = satellite.get('orbit_data', {})
        if orbit_data:
            enhanced_satellite["orbit_parameters"] = {
                "altitude": orbit_data.get('altitude', 0),
                "inclination": orbit_data.get('inclination', 0),
                "semi_major_axis": orbit_data.get('semi_major_axis', 0),
                "eccentricity": orbit_data.get('eccentricity', 0),
                "mean_motion": orbit_data.get('mean_motion', 0)
            }
        
        # 2. 處理位置時間序列
        # 🎯 關鍵修復：Stage 3 現在輸出 "position_timeseries" 而不是 "positions"
        # 需要兼容兩種字段名稱
        positions = satellite.get('position_timeseries', satellite.get('positions', []))
        if positions:
            enhanced_satellite["position_timeseries"] = []
            for pos in positions:
                # 兼容不同的數據格式
                enhanced_pos = {
                    "time": pos.get('time', ''),
                    "time_offset_seconds": pos.get('time_offset_seconds', 0),
                    "elevation_deg": pos.get('elevation_deg', -999),
                    "azimuth_deg": pos.get('azimuth_deg', 0),
                    "range_km": pos.get('range_km', 0),
                    "is_visible": pos.get('is_visible', False),
                    "position_eci": pos.get('position_eci', {}),
                    "velocity_eci": pos.get('velocity_eci', {})
                }
                enhanced_satellite["position_timeseries"].append(enhanced_pos)
            logger.debug(f"  成功處理 {len(positions)} 個時間點的軌道數據")
        
        # 3. 處理簡化時間序列（來自原始 timeseries）
        timeseries = satellite.get('timeseries', [])
        if timeseries:
            enhanced_satellite["elevation_azimuth_timeseries"] = timeseries
        
        # 4. 處理可見性窗口
        visibility_windows = orbit_data.get('visibility_windows', [])
        if visibility_windows:
            enhanced_satellite["visibility_windows"] = visibility_windows
        
        # 5. 處理信號品質數據
        signal_quality = satellite.get('signal_quality', {})
        if signal_quality:
            enhanced_satellite["signal_quality"] = signal_quality
        
        # 6. 處理事件分析結果
        if 'event_potential' in satellite:
            enhanced_satellite["event_analysis"] = {
                "event_potential": satellite.get('event_potential', {}),
                "supported_events": ["A4_intra_frequency", "A5_intra_frequency", "D2_beam_switch"]
            }
        
        # 7. 處理綜合評分
        if 'composite_score' in satellite:
            enhanced_satellite["performance_scores"] = {
                "composite_score": satellite.get('composite_score', 0),
                "geographic_score": satellite.get('geographic_relevance_score', 0),
                "handover_score": satellite.get('handover_suitability_score', 0)
            }
        
        # 8. 添加時間序列預處理標記
        enhanced_satellite["processing_metadata"] = {
            "processed_by_timeseries_preprocessing": True,
            "processing_time": datetime.now(timezone.utc).isoformat(),
            "data_source": "signal_event_analysis",
            "enhanced_features": [
                "position_timeseries",
                "elevation_azimuth_timeseries", 
                "visibility_windows",
                "signal_quality",
                "event_analysis",
                "performance_scores"
            ]
        }
        
        return enhanced_satellite
        
    def save_enhanced_timeseries(self, conversion_results: Dict[str, Any]) -> Dict[str, str]:
        """保存增強時間序列數據到文件"""
        logger.info("💾 保存增強時間序列數據...")
        
        output_files = {}
        
        # 使用固定檔案名，符合標準化命名規範
        FIXED_FILENAMES = {
            "starlink": "starlink_enhanced.json",
            "oneweb": "oneweb_enhanced.json"
        }
        
        for const_name in ['starlink', 'oneweb']:
            if conversion_results[const_name] is None:
                continue
                
            # 使用固定檔案名而非動態命名
            filename = FIXED_FILENAMES[const_name]
            output_file = self.enhanced_dir / filename
            
            # 將統計信息添加到檔案內容中
            constellation_data = conversion_results[const_name].copy()
            satellite_count = len(constellation_data['satellites'])
            
            # 在 metadata 中記錄統計信息
            constellation_data["metadata"]["satellite_count"] = satellite_count
            constellation_data["metadata"]["filename_standard"] = "fixed_naming"
            constellation_data["metadata"]["previous_dynamic_name"] = f"{const_name}_enhanced_{satellite_count}sats.json"
            
            # 保存文件
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(constellation_data, f, indent=2, ensure_ascii=False)
            
            file_size = output_file.stat().st_size
            output_files[const_name] = str(output_file)
            
            logger.info(f"✅ {const_name} 數據已保存: {output_file}")
            logger.info(f"   文件大小: {file_size / (1024*1024):.1f} MB")
            logger.info(f"   衛星數量: {satellite_count} 顆 (記錄在檔案內)")
        
        # 保存轉換統計
        stats_file = self.enhanced_dir / "conversion_statistics.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(conversion_results["conversion_statistics"], f, indent=2, ensure_ascii=False)
        
        logger.info(f"📊 轉換統計已保存: {stats_file}")
        
        return output_files
        
    def process_timeseries_preprocessing(self, signal_file: Optional[str] = None, save_output: bool = True) -> Dict[str, Any]:
        """執行完整的時間序列預處理流程"""
        logger.info("🚀 開始時間序列預處理")
        
        # 1. 載入信號分析數據
        signal_data = self.load_signal_analysis_output(signal_file)
        
        # 2. 轉換為增強時間序列格式
        conversion_results = self.convert_to_enhanced_timeseries(signal_data)
        
        # 3. 保存增強時間序列數據
        output_files = {}
        if save_output:
            output_files = self.save_enhanced_timeseries(conversion_results)
            logger.info(f"📁 時間序列預處理數據已保存到: {self.enhanced_dir}")
        else:
            logger.info("🚀 時間序列預處理使用內存傳遞模式，未保存檔案")
        
        # 4. 組裝返回結果
        results = {
            "success": True,
            "processing_type": "timeseries_preprocessing",
            "processing_timestamp": datetime.now(timezone.utc).isoformat(),
            "input_source": "signal_event_analysis_output.json",
            "output_directory": str(self.enhanced_dir),
            "output_files": output_files,
            "conversion_statistics": conversion_results["conversion_statistics"],
            "constellation_data": {
                "starlink": {
                    "satellites_processed": len(conversion_results["starlink"]["satellites"]) if conversion_results["starlink"] else 0,
                    "output_file": output_files.get("starlink", None)
                },
                "oneweb": {
                    "satellites_processed": len(conversion_results["oneweb"]["satellites"]) if conversion_results["oneweb"] else 0,
                    "output_file": output_files.get("oneweb", None)
                }
            }
        }
        
        total_processed = results["conversion_statistics"]["total_processed"]
        total_successful = results["conversion_statistics"]["successful_conversions"]
        
        logger.info("✅ 時間序列預處理完成")
        logger.info(f"  處理的衛星數: {total_processed}")
        logger.info(f"  成功轉換: {total_successful}")
        logger.info(f"  轉換率: {total_successful/total_processed*100:.1f}%" if total_processed > 0 else "  轉換率: 0%")
        
        if output_files:
            logger.info(f"  輸出文件:")
            for const, file_path in output_files.items():
                logger.info(f"    {const}: {file_path}")
        
        return results

def main():
    """主函數"""
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    logger.info("============================================================")
    logger.info("時間序列預處理")
    logger.info("============================================================")
    
    try:
        processor = TimeseriesPreprocessingProcessor()
        result = processor.process_timeseries_preprocessing()
        
        logger.info("🎉 時間序列預處理成功完成！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 時間序列預處理失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)