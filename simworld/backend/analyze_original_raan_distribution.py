#!/usr/bin/env python3
"""
分析原始TLE數據的RAAN分布
檢查Phase 1篩選是否過於嚴格，影響RAAN覆蓋度
"""

import json
import logging
from collections import defaultdict
from pathlib import Path
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_raan_distribution(data, constellation_name):
    """分析RAAN分布"""
    raan_bins = defaultdict(int)
    raan_values = []
    
    logger.info(f"分析 {constellation_name} 數據，衛星總數: {len(data)}")
    
    for sat in data:
        try:
            raan = float(sat['RA_OF_ASC_NODE'])
            raan_values.append(raan)
            bin_index = int(raan / 10)  # 10度一個bin
            raan_bins[bin_index] += 1
        except (KeyError, ValueError, TypeError):
            continue
    
    # 計算覆蓋度
    covered_bins = len(raan_bins)
    total_bins = 36
    coverage_percent = covered_bins / total_bins * 100
    
    logger.info(f"{constellation_name} RAAN 分析結果:")
    logger.info(f"  覆蓋區間: {covered_bins}/36 ({coverage_percent:.1f}%)")
    logger.info(f"  RAAN範圍: {min(raan_values):.1f}° - {max(raan_values):.1f}°")
    
    # 顯示每個bin的分布
    logger.info(f"  RAAN分布詳情:")
    for bin_idx in range(36):
        if raan_bins[bin_idx] > 0:
            logger.info(f"    區間 {bin_idx} ({bin_idx*10}-{(bin_idx+1)*10}°): {raan_bins[bin_idx]} 顆")
    
    return {
        'covered_bins': covered_bins,
        'total_bins': total_bins,
        'coverage_percent': coverage_percent,
        'distribution': dict(raan_bins),
        'total_satellites': len(data)
    }

def test_direct_phase2_filtering():
    """測試直接對原始數據進行Phase 2篩選"""
    from orbital_diversity_filter import OrbitalDiversityFilter
    
    logger.info("🚀 測試直接對原始數據進行Phase 2篩選")
    
    # 載入原始數據
    tle_data_dir = Path("/home/sat/ntn-stack/netstack/tle_data")
    
    starlink_file = tle_data_dir / "starlink/json/starlink_20250731.json"
    oneweb_file = tle_data_dir / "oneweb/json/oneweb_20250731.json"
    
    raw_data = {}
    
    # 載入Starlink數據
    if starlink_file.exists():
        with open(starlink_file, 'r') as f:
            starlink_data = json.load(f)
        raw_data['starlink'] = {'accepted': starlink_data}
        
        logger.info(f"載入 Starlink 原始數據: {len(starlink_data)} 顆")
        starlink_analysis = analyze_raan_distribution(starlink_data, "Starlink")
    
    # 載入OneWeb數據
    if oneweb_file.exists():
        with open(oneweb_file, 'r') as f:
            oneweb_data = json.load(f)
        raw_data['oneweb'] = {'accepted': oneweb_data}
        
        logger.info(f"載入 OneWeb 原始數據: {len(oneweb_data)} 顆")
        oneweb_analysis = analyze_raan_distribution(oneweb_data, "OneWeb")
    
    # 合併分析
    all_satellites = []
    for constellation_data in raw_data.values():
        all_satellites.extend(constellation_data['accepted'])
    
    logger.info(f"\n📊 合併原始數據分析:")
    combined_analysis = analyze_raan_distribution(all_satellites, "Combined")
    
    # 直接執行Phase 2篩選
    logger.info(f"\n🌐 對原始數據執行Phase 2篩選...")
    
    filter_system = OrbitalDiversityFilter()
    phase2_results = filter_system.filter_for_diversity(raw_data)
    
    logger.info(f"\n✅ Phase 2 篩選結果:")
    logger.info(f"  輸入: {phase2_results['input_count']} 顆")
    logger.info(f"  輸出: {phase2_results['output_count']} 顆")
    logger.info(f"  RAAN覆蓋度: {phase2_results['diversity_metrics']['raan_coverage_percent']:.1f}%")
    logger.info(f"  平均品質分數: {phase2_results['quality_metrics']['avg_total_score']:.1f}")
    
    # 比較結果
    logger.info(f"\n📈 對比分析:")
    logger.info(f"原始數據 RAAN 覆蓋度: {combined_analysis['coverage_percent']:.1f}%")
    logger.info(f"Phase 2 後 RAAN 覆蓋度: {phase2_results['diversity_metrics']['raan_coverage_percent']:.1f}%")
    logger.info(f"衛星數量變化: {combined_analysis['total_satellites']} → {phase2_results['output_count']}")
    
    return {
        'original_analysis': combined_analysis,
        'phase2_results': phase2_results,
        'starlink_analysis': starlink_analysis,
        'oneweb_analysis': oneweb_analysis
    }

def main():
    """主程序"""
    logger.info("🔍 開始分析原始TLE數據的RAAN分布")
    
    try:
        results = test_direct_phase2_filtering()
        
        # 保存分析結果
        output_file = Path("/home/sat/ntn-stack/simworld/backend/original_data_raan_analysis.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"📄 詳細分析報告已保存至: {output_file}")
        
    except Exception as e:
        logger.error(f"❌ 分析過程發生錯誤: {e}")
        raise

if __name__ == "__main__":
    main()