#!/usr/bin/env python3
"""
Phase 0 集成模組 - Starlink 完整數據下載與換手篩選工具
整合所有 Phase 0 功能的主要入口點

功能集成:
1. 完整 Starlink TLE 數據下載器
2. 衛星候選預篩選器  
3. 最佳時間段分析功能
4. 前端數據源格式化

使用方法:
python phase0_integration.py --coordinates 24.9441667,121.3713889 --output results.json
"""

import asyncio
import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

from .starlink_tle_downloader import StarlinkTLEDownloader
from .satellite_prefilter import SatellitePrefilter, ObserverLocation
from .optimal_timeframe_analyzer import OptimalTimeframeAnalyzer
from .frontend_data_formatter import FrontendDataFormatter


# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Phase0Integration:
    """Phase 0 完整集成系統"""
    
    def __init__(self, cache_dir: str = "data/phase0_cache"):
        """
        初始化 Phase 0 集成系統
        
        Args:
            cache_dir: 緩存目錄路徑
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化各個組件
        self.downloader = StarlinkTLEDownloader(cache_dir=str(self.cache_dir))
        self.prefilter = SatellitePrefilter()
        self.analyzer = OptimalTimeframeAnalyzer()
        self.formatter = FrontendDataFormatter()
        
        logger.info("Phase 0 集成系統初始化完成")
    
    async def run_complete_analysis(self, observer_lat: float, observer_lon: float, 
                                  observer_alt: float = 0.0, 
                                  force_download: bool = False) -> Dict[str, Any]:
        """
        執行完整的 Phase 0 分析流程
        
        Args:
            observer_lat: 觀察者緯度 (度)
            observer_lon: 觀察者經度 (度)
            observer_alt: 觀察者海拔高度 (米)
            force_download: 是否強制重新下載 TLE 數據
            
        Returns:
            完整的分析結果
        """
        analysis_start_time = datetime.now(timezone.utc)
        logger.info("=== 開始 Phase 0 完整分析流程 ===")
        logger.info(f"觀察者座標: ({observer_lat}, {observer_lon}, {observer_alt}m)")
        
        try:
            # 步驟 1: 下載完整 Starlink TLE 數據
            logger.info("步驟 1/4: 下載完整 Starlink TLE 數據...")
            satellites = await self.downloader.get_starlink_tle_data(force_download=force_download)
            
            if not satellites:
                raise Exception("無法獲取 Starlink TLE 數據")
            
            logger.info(f"成功下載 {len(satellites)} 顆 Starlink 衛星數據")
            
            # 步驟 2: 衛星候選預篩選
            logger.info("步驟 2/4: 執行衛星候選預篩選...")
            observer = ObserverLocation(observer_lat, observer_lon, observer_alt)
            candidate_satellites, excluded_satellites = self.prefilter.pre_filter_satellites_by_orbit(
                observer, satellites
            )
            
            logger.info(f"預篩選結果: {len(candidate_satellites)} 候選衛星, {len(excluded_satellites)} 排除衛星")
            
            # 步驟 3: 最佳時間段分析
            logger.info("步驟 3/4: 分析最佳換手時間段...")
            optimal_timeframe = self.analyzer.find_optimal_handover_timeframe(
                observer_lat, observer_lon, candidate_satellites
            )
            
            if not optimal_timeframe:
                raise Exception("未找到符合條件的最佳時間段")
            
            logger.info(f"找到最佳時間段: {optimal_timeframe.start_timestamp}, "
                       f"{optimal_timeframe.duration_minutes} 分鐘, "
                       f"{optimal_timeframe.satellite_count} 顆衛星")
            
            # 步驟 4: 前端數據源格式化
            logger.info("步驟 4/4: 格式化前端數據源...")
            frontend_data = self.formatter.format_for_frontend_display(
                optimal_timeframe, {"lat": observer_lat, "lon": observer_lon}
            )
            
            # 生成完整結果
            analysis_end_time = datetime.now(timezone.utc)
            analysis_duration = (analysis_end_time - analysis_start_time).total_seconds()
            
            result = {
                "analysis_metadata": {
                    "analysis_start_time": analysis_start_time.isoformat(),
                    "analysis_end_time": analysis_end_time.isoformat(),
                    "analysis_duration_seconds": analysis_duration,
                    "observer_coordinates": {
                        "latitude": observer_lat,
                        "longitude": observer_lon,
                        "altitude_m": observer_alt
                    },
                    "phase0_version": "1.0"
                },
                "raw_data_statistics": {
                    "total_starlink_satellites": len(satellites),
                    "candidate_satellites": len(candidate_satellites),
                    "excluded_satellites": len(excluded_satellites),
                    "prefilter_reduction_ratio": round(len(excluded_satellites) / len(satellites) * 100, 1)
                },
                "optimal_timeframe": {
                    "start_timestamp": optimal_timeframe.start_timestamp,
                    "duration_minutes": optimal_timeframe.duration_minutes,
                    "satellite_count": optimal_timeframe.satellite_count,
                    "coverage_quality_score": optimal_timeframe.coverage_quality_score,
                    "handover_sequence_count": len(optimal_timeframe.handover_sequence),
                    "satellites": [
                        {
                            "norad_id": sat.norad_id,
                            "name": sat.name,
                            "max_elevation": sat.visibility_window.max_elevation,
                            "duration_minutes": sat.visibility_window.duration_minutes,
                            "handover_priority": sat.handover_priority
                        }
                        for sat in optimal_timeframe.satellites
                    ]
                },
                "frontend_data_sources": frontend_data,
                "validation_results": await self._validate_results(optimal_timeframe)
            }
            
            logger.info(f"=== Phase 0 分析完成 (耗時 {analysis_duration:.1f} 秒) ===")
            return result
            
        except Exception as e:
            logger.error(f"Phase 0 分析失敗: {e}")
            raise
    
    async def _validate_results(self, optimal_timeframe) -> Dict[str, Any]:
        """驗證分析結果的合理性"""
        validation_results = {
            "validation_passed": True,
            "warnings": [],
            "errors": []
        }
        
        # 檢查衛星數量
        if optimal_timeframe.satellite_count < 3:
            validation_results["warnings"].append(f"衛星數量較少: {optimal_timeframe.satellite_count}")
        elif optimal_timeframe.satellite_count > 15:
            validation_results["warnings"].append(f"衛星數量較多: {optimal_timeframe.satellite_count}")
        
        # 檢查覆蓋品質
        if optimal_timeframe.coverage_quality_score < 0.5:
            validation_results["warnings"].append(f"覆蓋品質偏低: {optimal_timeframe.coverage_quality_score:.2f}")
        
        # 檢查時間段長度
        if optimal_timeframe.duration_minutes < 30:
            validation_results["errors"].append(f"時間段過短: {optimal_timeframe.duration_minutes} 分鐘")
        elif optimal_timeframe.duration_minutes > 45:
            validation_results["warnings"].append(f"時間段較長: {optimal_timeframe.duration_minutes} 分鐘")
        
        # 檢查換手序列
        if len(optimal_timeframe.handover_sequence) == 0:
            validation_results["warnings"].append("無換手序列")
        
        # 檢查衛星仰角
        low_elevation_count = sum(1 for sat in optimal_timeframe.satellites 
                                if sat.visibility_window.max_elevation < 30)
        if low_elevation_count > optimal_timeframe.satellite_count // 2:
            validation_results["warnings"].append(f"過多低仰角衛星: {low_elevation_count}")
        
        if validation_results["errors"]:
            validation_results["validation_passed"] = False
        
        return validation_results
    
    async def save_results(self, results: Dict[str, Any], output_file: str) -> None:
        """保存分析結果到文件"""
        output_path = Path(output_file)
        
        # 確保輸出目錄存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存結果
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"分析結果已保存到: {output_path}")
    
    async def export_for_academic_research(self, results: Dict[str, Any], 
                                         export_dir: str = "data/academic_export") -> Dict[str, str]:
        """導出學術研究所需的標準化數據格式"""
        export_path = Path(export_dir)
        export_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 導出文件路徑
        files = {
            "complete_results": export_path / f"phase0_complete_{timestamp}.json",
            "satellite_trajectories": export_path / f"trajectories_{timestamp}.csv",
            "handover_sequence": export_path / f"handover_sequence_{timestamp}.csv",
            "analysis_summary": export_path / f"analysis_summary_{timestamp}.txt"
        }
        
        # 保存完整結果
        with open(files["complete_results"], 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # 導出軌跡數據為 CSV
        import csv
        with open(files["satellite_trajectories"], 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'satellite_name', 'norad_id', 'time', 'elevation', 'azimuth', 
                'latitude', 'longitude', 'altitude_km', 'distance_km', 'visible'
            ])
            
            for sat_data in results["frontend_data_sources"]["animation_data"]["animation_trajectories"]:
                sat_name = sat_data["satellite_name"]
                sat_id = sat_data["satellite_id"].split('-')[1]  # 提取 NORAD ID
                
                for point in sat_data["trajectory_points"]:
                    writer.writerow([
                        sat_name, sat_id, point["time_offset"], point["elevation"],
                        point["azimuth"], 0, 0, 0, 0, point["visible"]  # 簡化版本
                    ])
        
        # 導出換手序列為 CSV
        with open(files["handover_sequence"], 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'sequence_id', 'from_satellite', 'to_satellite', 'handover_time',
                'handover_type', 'signal_overlap_duration', 'quality_score'
            ])
            
            for handover in results["frontend_data_sources"]["handover_sequence"]["handover_sequence"]:
                writer.writerow([
                    handover["sequence_id"], handover["from_satellite"], handover["to_satellite"],
                    handover["handover_time"], handover["handover_type"],
                    handover["signal_overlap_duration"], handover["quality_score"]
                ])
        
        # 生成分析摘要
        with open(files["analysis_summary"], 'w', encoding='utf-8') as f:
            f.write("=== Phase 0 Starlink Handover Analysis Summary ===\n\n")
            f.write(f"Analysis Time: {results['analysis_metadata']['analysis_start_time']}\n")
            f.write(f"Observer Location: {results['analysis_metadata']['observer_coordinates']}\n")
            f.write(f"Analysis Duration: {results['analysis_metadata']['analysis_duration_seconds']:.1f} seconds\n\n")
            
            f.write("=== Data Statistics ===\n")
            f.write(f"Total Starlink Satellites: {results['raw_data_statistics']['total_starlink_satellites']}\n")
            f.write(f"Candidate Satellites: {results['raw_data_statistics']['candidate_satellites']}\n")
            f.write(f"Reduction Ratio: {results['raw_data_statistics']['prefilter_reduction_ratio']}%\n\n")
            
            f.write("=== Optimal Timeframe ===\n")
            f.write(f"Start Time: {results['optimal_timeframe']['start_timestamp']}\n")
            f.write(f"Duration: {results['optimal_timeframe']['duration_minutes']} minutes\n")
            f.write(f"Satellite Count: {results['optimal_timeframe']['satellite_count']}\n")
            f.write(f"Quality Score: {results['optimal_timeframe']['coverage_quality_score']:.3f}\n")
            f.write(f"Handover Events: {results['optimal_timeframe']['handover_sequence_count']}\n\n")
            
            f.write("=== Validation Results ===\n")
            validation = results["validation_results"]
            f.write(f"Validation Passed: {validation['validation_passed']}\n")
            if validation["warnings"]:
                f.write("Warnings:\n")
                for warning in validation["warnings"]:
                    f.write(f"  - {warning}\n")
            if validation["errors"]:
                f.write("Errors:\n")
                for error in validation["errors"]:
                    f.write(f"  - {error}\n")
        
        logger.info(f"學術研究數據已導出到: {export_path}")
        return {name: str(path) for name, path in files.items()}


async def main():
    """主函數 - 命令行接口"""
    parser = argparse.ArgumentParser(description="Phase 0 Starlink 換手分析工具")
    parser.add_argument("--coordinates", required=True, 
                       help="觀察者座標 (格式: lat,lon 或 lat,lon,alt)")
    parser.add_argument("--output", default="phase0_results.json",
                       help="輸出文件路徑")
    parser.add_argument("--force-download", action="store_true",
                       help="強制重新下載 TLE 數據")
    parser.add_argument("--export-academic", action="store_true",
                       help="導出學術研究格式")
    parser.add_argument("--cache-dir", default="data/phase0_cache",
                       help="緩存目錄")
    
    args = parser.parse_args()
    
    # 解析座標
    try:
        coords = [float(x.strip()) for x in args.coordinates.split(',')]
        if len(coords) == 2:
            observer_lat, observer_lon, observer_alt = coords[0], coords[1], 0.0
        elif len(coords) == 3:
            observer_lat, observer_lon, observer_alt = coords
        else:
            raise ValueError("座標格式錯誤")
    except ValueError as e:
        logger.error(f"座標解析失敗: {e}")
        sys.exit(1)
    
    # 執行分析
    try:
        phase0 = Phase0Integration(cache_dir=args.cache_dir)
        
        results = await phase0.run_complete_analysis(
            observer_lat, observer_lon, observer_alt, 
            force_download=args.force_download
        )
        
        # 保存結果
        await phase0.save_results(results, args.output)
        
        # 導出學術格式
        if args.export_academic:
            export_files = await phase0.export_for_academic_research(results)
            logger.info("學術格式文件:")
            for name, path in export_files.items():
                logger.info(f"  {name}: {path}")
        
        # 顯示摘要
        print("\n=== Phase 0 分析結果摘要 ===")
        print(f"觀察者座標: ({observer_lat}, {observer_lon})")
        print(f"分析耗時: {results['analysis_metadata']['analysis_duration_seconds']:.1f} 秒")
        print(f"原始衛星數量: {results['raw_data_statistics']['total_starlink_satellites']}")
        print(f"候選衛星數量: {results['raw_data_statistics']['candidate_satellites']}")
        print(f"計算量減少: {results['raw_data_statistics']['prefilter_reduction_ratio']}%")
        print(f"最佳時間段: {results['optimal_timeframe']['start_timestamp']}")
        print(f"時間段長度: {results['optimal_timeframe']['duration_minutes']} 分鐘")
        print(f"衛星數量: {results['optimal_timeframe']['satellite_count']}")
        print(f"品質評分: {results['optimal_timeframe']['coverage_quality_score']:.3f}")
        print(f"換手事件: {results['optimal_timeframe']['handover_sequence_count']}")
        
        validation = results["validation_results"]
        print(f"驗證通過: {'是' if validation['validation_passed'] else '否'}")
        if validation["warnings"]:
            print("警告:")
            for warning in validation["warnings"]:
                print(f"  - {warning}")
        
        logger.info("Phase 0 分析完成")
        
    except Exception as e:
        logger.error(f"分析失敗: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())