#!/usr/bin/env python3
"""
整合 Phase 1 和 Phase 2 的完整衛星篩選系統
從原始 TLE 數據到最終的 500 顆高品質多樣性衛星
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any
import numpy as np

from rl_optimized_satellite_filter import RLOptimizedSatelliteFilter
from orbital_diversity_filter import OrbitalDiversityFilter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntegratedSatelliteFilterSystem:
    """
    整合的衛星篩選系統
    執行完整的 Phase 1 + Phase 2 篩選流程
    """
    
    def __init__(self, target_lat: float = 24.9441, target_lon: float = 121.3714):
        self.target_lat = target_lat
        self.target_lon = target_lon
        
        # 初始化兩個篩選器
        self.phase1_filter = RLOptimizedSatelliteFilter(target_lat, target_lon)
        self.phase2_filter = OrbitalDiversityFilter(target_lat, target_lon)
        
        # 結果存儲
        self.phase1_results = {}
        self.phase2_results = {}
        self.final_results = {}
    
    def execute_complete_filtering(self, tle_data_dir: Path) -> Dict[str, Any]:
        """
        執行完整的兩階段篩選流程
        """
        logger.info("🚀 開始執行完整的兩階段衛星篩選")
        logger.info(f"📍 目標座標: {self.target_lat:.4f}°N, {self.target_lon:.4f}°E")
        
        # Phase 1: 零容忍篩選
        logger.info("\n" + "="*60)
        logger.info("🔍 Phase 1: 零容忍篩選")
        logger.info("="*60)
        
        phase1_results = self._execute_phase1(tle_data_dir)
        self.phase1_results = phase1_results
        
        # Phase 2: 軌道多樣性篩選
        logger.info("\n" + "="*60)
        logger.info("🌐 Phase 2: 軌道多樣性篩選")
        logger.info("="*60)
        
        phase2_results = self._execute_phase2(phase1_results)
        self.phase2_results = phase2_results
        
        # 生成最終結果報告
        final_results = self._generate_final_report()
        self.final_results = final_results
        
        logger.info("\n" + "="*60)
        logger.info("✅ 完整篩選流程完成")
        logger.info("="*60)
        
        return final_results
    
    def _execute_phase1(self, tle_data_dir: Path) -> Dict[str, Any]:
        """
        執行 Phase 1 零容忍篩選
        """
        phase1_results = {}
        
        # 處理 Starlink
        starlink_file = tle_data_dir / "starlink/json/starlink_20250731.json"
        if starlink_file.exists():
            logger.info("📡 處理 Starlink 數據...")
            with open(starlink_file, 'r') as f:
                starlink_data = json.load(f)
            
            starlink_results = self.phase1_filter.filter_constellation(starlink_data, "starlink")
            phase1_results['starlink'] = starlink_results
            
            logger.info(f"  Starlink: {len(starlink_data)} → {len(starlink_results['accepted'])} 顆")
        
        # 處理 OneWeb
        oneweb_file = tle_data_dir / "oneweb/json/oneweb_20250731.json"
        if oneweb_file.exists():
            logger.info("📡 處理 OneWeb 數據...")
            with open(oneweb_file, 'r') as f:
                oneweb_data = json.load(f)
            
            oneweb_results = self.phase1_filter.filter_constellation(oneweb_data, "oneweb")
            phase1_results['oneweb'] = oneweb_results
            
            logger.info(f"  OneWeb: {len(oneweb_data)} → {len(oneweb_results['accepted'])} 顆")
        
        # 計算 Phase 1 總計
        total_input = sum(len(self._load_constellation_data(tle_data_dir, const)) 
                         for const in ['starlink', 'oneweb'] 
                         if (tle_data_dir / f"{const}/json/{const}_20250731.json").exists())
        
        total_output = sum(len(results['accepted']) for results in phase1_results.values())
        
        logger.info(f"\n📊 Phase 1 總結:")
        logger.info(f"  總輸入: {total_input} 顆衛星")
        logger.info(f"  總輸出: {total_output} 顆衛星")
        logger.info(f"  通過率: {total_output/total_input*100:.1f}%")
        
        return phase1_results
    
    def _execute_phase2(self, phase1_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行 Phase 2 軌道多樣性篩選
        """
        logger.info("🌐 開始軌道多樣性篩選...")
        
        phase2_results = self.phase2_filter.filter_for_diversity(phase1_results)
        
        logger.info(f"\n📊 Phase 2 總結:")
        logger.info(f"  輸入: {phase2_results['input_count']} 顆衛星")
        logger.info(f"  輸出: {phase2_results['output_count']} 顆衛星")
        logger.info(f"  篩選比例: {phase2_results['reduction_ratio']:.1%}")
        logger.info(f"  RAAN 覆蓋度: {phase2_results['diversity_metrics']['raan_coverage_percent']:.1f}%")
        logger.info(f"  平均品質分數: {phase2_results['quality_metrics']['avg_total_score']:.1f}")
        
        # 星座分布
        for const, stats in phase2_results['constellation_breakdown'].items():
            logger.info(f"  {const.upper()}: {stats['count']} 顆 (平均分數: {stats['avg_quality_score']:.1f})")
        
        return phase2_results
    
    def _generate_final_report(self) -> Dict[str, Any]:
        """
        生成最終的完整報告
        """
        # 計算完整的統計數據
        phase1_total_input = 0
        phase1_total_output = 0
        
        for constellation, results in self.phase1_results.items():
            # 需要重新計算輸入數量（從統計中獲取）
            if 'statistics' in results:
                phase1_total_input += results['statistics'].get('total_processed', 0)
            phase1_total_output += len(results['accepted'])
        
        phase2_input = self.phase2_results['input_count']
        phase2_output = self.phase2_results['output_count']
        
        final_results = {
            'summary': {
                'target_coordinate': f"{self.target_lat:.4f}°N, {self.target_lon:.4f}°E",
                'processing_date': str(Path().cwd()),
                'total_processing_stages': 2
            },
            'phase1_summary': {
                'name': 'Zero-Tolerance Filtering',
                'input_satellites': phase1_total_input,
                'output_satellites': phase1_total_output,
                'acceptance_rate': phase1_total_output / phase1_total_input * 100 if phase1_total_input > 0 else 0,
                'constellation_breakdown': {}
            },
            'phase2_summary': {
                'name': 'Orbital Diversity Filtering',
                'input_satellites': phase2_input,
                'output_satellites': phase2_output,
                'reduction_ratio': phase2_output / phase2_input if phase2_input > 0 else 0,
                'diversity_metrics': self.phase2_results['diversity_metrics'],
                'quality_metrics': self.phase2_results['quality_metrics'],
                'constellation_breakdown': self.phase2_results['constellation_breakdown']
            },
            'overall_summary': {
                'initial_satellites': phase1_total_input,
                'final_satellites': phase2_output,
                'overall_reduction_ratio': phase2_output / phase1_total_input if phase1_total_input > 0 else 0,
                'overall_acceptance_rate': phase2_output / phase1_total_input * 100 if phase1_total_input > 0 else 0
            },
            'final_satellite_list': self.phase2_results['selected_satellites'],
            'phase1_details': self.phase1_results,
            'phase2_details': self.phase2_results
        }
        
        # 填充 Phase 1 星座分布
        for constellation, results in self.phase1_results.items():
            final_results['phase1_summary']['constellation_breakdown'][constellation] = {
                'input_count': results['statistics'].get('total_processed', 0),
                'output_count': len(results['accepted']),
                'acceptance_rate': len(results['accepted']) / results['statistics'].get('total_processed', 1) * 100
            }
        
        return final_results
    
    def _load_constellation_data(self, tle_data_dir: Path, constellation: str) -> list:
        """
        載入星座數據
        """
        file_path = tle_data_dir / f"{constellation}/json/{constellation}_20250731.json"
        if file_path.exists():
            with open(file_path, 'r') as f:
                return json.load(f)
        return []
    
    def save_results(self, output_dir: Path):
        """
        保存篩選結果到文件
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存最終結果
        final_results_file = output_dir / "integrated_filtering_results.json"
        with open(final_results_file, 'w', encoding='utf-8') as f:
            json.dump(self.final_results, f, indent=2, ensure_ascii=False)
        
        # 保存最終衛星列表（簡化版）
        final_satellites = self.final_results['final_satellite_list']
        simplified_satellites = []
        
        for sat in final_satellites:
            simplified_sat = {
                'name': sat.get('name', ''),
                'norad_id': sat.get('norad_id', ''),
                'constellation': sat.get('constellation', ''),
                'orbital_parameters': {
                    'inclination': sat.get('INCLINATION'),
                    'raan': sat.get('RA_OF_ASC_NODE'),
                    'eccentricity': sat.get('ECCENTRICITY'),
                    'mean_motion': sat.get('MEAN_MOTION')
                },
                'quality_scores': sat.get('quality_scores', {})
            }
            simplified_satellites.append(simplified_sat)
        
        satellites_file = output_dir / "final_selected_satellites.json"
        with open(satellites_file, 'w', encoding='utf-8') as f:
            json.dump(simplified_satellites, f, indent=2, ensure_ascii=False)
        
        logger.info(f"結果已保存到: {output_dir}")
        logger.info(f"  完整結果: {final_results_file}")
        logger.info(f"  衛星列表: {satellites_file}")

def main():
    """主要執行程序"""
    
    # TLE 數據目錄
    tle_data_dir = Path("/home/sat/ntn-stack/netstack/tle_data")
    
    # 結果輸出目錄
    output_dir = Path("/home/sat/ntn-stack/simworld/backend/filtering_results")
    
    # 初始化整合篩選系統
    filter_system = IntegratedSatelliteFilterSystem()
    
    try:
        # 執行完整篩選
        results = filter_system.execute_complete_filtering(tle_data_dir)
        
        # 保存結果
        filter_system.save_results(output_dir)
        
        # 打印最終摘要
        print("\n" + "="*60)
        print("🎯 最終篩選摘要")
        print("="*60)
        print(f"📍 目標座標: {results['summary']['target_coordinate']}")
        print(f"🔢 初始衛星數: {results['overall_summary']['initial_satellites']:,}")
        print(f"🎯 最終衛星數: {results['overall_summary']['final_satellites']:,}")
        print(f"📊 整體通過率: {results['overall_summary']['overall_acceptance_rate']:.2f}%")
        print(f"🌐 RAAN 覆蓋度: {results['phase2_summary']['diversity_metrics']['raan_coverage_percent']:.1f}%")
        print(f"⭐ 平均品質分數: {results['phase2_summary']['quality_metrics']['avg_total_score']:.1f}")
        
        print(f"\n📡 最終星座分布:")
        for const, stats in results['phase2_summary']['constellation_breakdown'].items():
            print(f"  {const.upper()}: {stats['count']} 顆")
        
        print(f"\n💾 結果已保存到: {output_dir}")
        
    except Exception as e:
        logger.error(f"篩選過程發生錯誤: {e}")
        raise

if __name__ == "__main__":
    main()