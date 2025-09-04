#!/usr/bin/env python3
"""
衛星子集可行性評估
評估通過時空錯置選擇衛星子集，達到目標可見數量的可行性
"""

import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class FeasibilityAnalysis:
    """可行性分析結果"""
    constellation: str
    total_satellites: int
    target_min: int
    target_max: int
    current_min: int
    current_max: int
    current_avg: float
    required_subset_size: int
    subset_percentage: float
    is_feasible: bool
    analysis_notes: str

class SubsetFeasibilityAnalyzer:
    """衛星子集可行性分析器"""
    
    def __init__(self):
        self.data_dir = "/tmp/satellite_data"
        self.load_visibility_report()
        
    def load_visibility_report(self):
        """載入可見性報告"""
        with open(f"{self.data_dir}/visibility_report.json", 'r') as f:
            self.visibility_data = json.load(f)
            
    def analyze_subset_requirements(self) -> List[FeasibilityAnalysis]:
        """分析子集需求和可行性"""
        
        results = []
        
        # Starlink 分析 (目標: 10-15 顆)
        starlink_data = self.visibility_data[0]
        starlink_analysis = self.analyze_constellation_subset(
            constellation="Starlink",
            current_data=starlink_data,
            target_min=10,
            target_max=15
        )
        results.append(starlink_analysis)
        
        # OneWeb 分析 (目標: 3-6 顆)
        oneweb_data = self.visibility_data[1]
        oneweb_analysis = self.analyze_constellation_subset(
            constellation="OneWeb",
            current_data=oneweb_data,
            target_min=3,
            target_max=6
        )
        results.append(oneweb_analysis)
        
        return results
    
    def analyze_constellation_subset(self, constellation: str, current_data: Dict,
                                    target_min: int, target_max: int) -> FeasibilityAnalysis:
        """分析單個星座的子集可行性"""
        
        total_sats = current_data['total_satellites']
        current_min = current_data['min_visible']
        current_max = current_data['max_visible']
        current_avg = current_data['avg_visible']
        
        # 計算縮減比例
        # 使用平均值來估算需要的衛星數量
        target_avg = (target_min + target_max) / 2
        reduction_ratio = target_avg / current_avg
        
        # 估算需要的衛星子集大小
        required_subset_size = int(total_sats * reduction_ratio)
        subset_percentage = (required_subset_size / total_sats) * 100
        
        # 評估可行性
        is_feasible = self.evaluate_feasibility(
            constellation, total_sats, required_subset_size,
            current_min, current_max, target_min, target_max
        )
        
        # 生成分析說明
        analysis_notes = self.generate_analysis_notes(
            constellation, total_sats, required_subset_size,
            current_min, current_max, current_avg,
            target_min, target_max, reduction_ratio
        )
        
        return FeasibilityAnalysis(
            constellation=constellation,
            total_satellites=total_sats,
            target_min=target_min,
            target_max=target_max,
            current_min=current_min,
            current_max=current_max,
            current_avg=current_avg,
            required_subset_size=required_subset_size,
            subset_percentage=subset_percentage,
            is_feasible=is_feasible,
            analysis_notes=analysis_notes
        )
    
    def evaluate_feasibility(self, constellation: str, total_sats: int,
                            required_subset_size: int, current_min: int,
                            current_max: int, target_min: int, target_max: int) -> bool:
        """評估可行性"""
        
        # 基本檢查：是否有足夠的衛星
        if required_subset_size < target_max:
            return False
            
        # 檢查變異性是否合理
        current_variation = current_max - current_min
        target_variation = target_max - target_min
        
        # 如果目標變異範圍比當前的還大，可能有問題
        if target_variation > current_variation * 0.5:
            return False
            
        # Starlink 特殊考量
        if constellation == "Starlink":
            # 需要足夠的衛星來維持覆蓋
            # 至少需要 100+ 顆來確保全球覆蓋
            if required_subset_size < 100:
                return False
                
        # OneWeb 特殊考量
        if constellation == "OneWeb":
            # 極軌設計需要足夠的軌道面
            # 至少需要 40+ 顆來維持基本覆蓋
            if required_subset_size < 40:
                return False
                
        return True
    
    def generate_analysis_notes(self, constellation: str, total_sats: int,
                               required_subset_size: int, current_min: int,
                               current_max: int, current_avg: float,
                               target_min: int, target_max: int,
                               reduction_ratio: float) -> str:
        """生成分析說明"""
        
        notes = []
        
        # 基本統計
        notes.append(f"當前可見範圍: {current_min}-{current_max} 顆 (平均 {current_avg:.1f})")
        notes.append(f"目標可見範圍: {target_min}-{target_max} 顆")
        notes.append(f"需要縮減至原本的 {reduction_ratio*100:.1f}%")
        
        # 可行性評估
        if constellation == "Starlink":
            if required_subset_size >= 100:
                notes.append(f"✅ 子集大小 {required_subset_size} 顆足夠維持覆蓋")
                notes.append("建議策略: 選擇不同軌道面的衛星進行時空錯置")
            else:
                notes.append(f"⚠️ 子集大小 {required_subset_size} 顆可能不足")
                notes.append("風險: 可能出現覆蓋空隙")
                
        elif constellation == "OneWeb":
            if required_subset_size >= 40:
                notes.append(f"✅ 子集大小 {required_subset_size} 顆可維持基本覆蓋")
                notes.append("建議策略: 保留每個軌道面的關鍵衛星")
            else:
                notes.append(f"⚠️ 子集大小 {required_subset_size} 顆過少")
                notes.append("風險: 極區覆蓋可能中斷")
        
        # 實施建議
        if reduction_ratio < 0.2:
            notes.append("挑戰: 需要大幅縮減，需要精確的時空規劃")
        elif reduction_ratio < 0.5:
            notes.append("可行: 適度縮減，可通過軌道優化實現")
        else:
            notes.append("容易: 輕度縮減，有充足的選擇空間")
            
        return "\n".join(notes)
    
    def estimate_temporal_distribution(self, constellation: str, 
                                      subset_size: int, orbital_period: float) -> Dict:
        """估算時間分布特性"""
        
        # 計算關鍵參數
        if constellation == "Starlink":
            orbital_planes = 72  # Starlink 約有 72 個軌道面
            sats_per_plane = subset_size / orbital_planes
            coverage_gap = orbital_period / sats_per_plane if sats_per_plane > 0 else float('inf')
        else:  # OneWeb
            orbital_planes = 18  # OneWeb 約有 18 個軌道面
            sats_per_plane = subset_size / orbital_planes
            coverage_gap = orbital_period / sats_per_plane if sats_per_plane > 0 else float('inf')
            
        return {
            'orbital_planes': orbital_planes,
            'sats_per_plane': sats_per_plane,
            'avg_coverage_gap_minutes': coverage_gap,
            'continuous_coverage': coverage_gap < 5  # 小於 5 分鐘間隔視為連續覆蓋
        }

def main():
    """主程式"""
    print("=" * 70)
    print("衛星子集可行性評估")
    print("=" * 70)
    
    analyzer = SubsetFeasibilityAnalyzer()
    
    # 進行可行性分析
    results = analyzer.analyze_subset_requirements()
    
    print("\n" + "=" * 70)
    print("可行性分析結果")
    print("=" * 70)
    
    for analysis in results:
        print(f"\n{'='*30} {analysis.constellation.upper()} {'='*30}")
        print(f"\n基本資訊:")
        print(f"  總衛星數: {analysis.total_satellites} 顆")
        print(f"  當前可見: {analysis.current_min}-{analysis.current_max} 顆 (平均 {analysis.current_avg:.1f})")
        print(f"  目標可見: {analysis.target_min}-{analysis.target_max} 顆")
        
        print(f"\n子集需求:")
        print(f"  需要衛星數: {analysis.required_subset_size} 顆")
        print(f"  佔總數比例: {analysis.subset_percentage:.1f}%")
        print(f"  可行性: {'✅ 可行' if analysis.is_feasible else '❌ 不可行'}")
        
        print(f"\n詳細分析:")
        for line in analysis.analysis_notes.split('\n'):
            print(f"  {line}")
        
        # 估算時間分布
        if analysis.constellation == "Starlink":
            orbital_period = 93.63
        else:
            orbital_period = 109.64
            
        temporal = analyzer.estimate_temporal_distribution(
            analysis.constellation, 
            analysis.required_subset_size,
            orbital_period
        )
        
        print(f"\n時空分布估算:")
        print(f"  軌道面數: {temporal['orbital_planes']}")
        print(f"  每軌道面衛星: {temporal['sats_per_plane']:.1f} 顆")
        print(f"  平均覆蓋間隔: {temporal['avg_coverage_gap_minutes']:.1f} 分鐘")
        print(f"  連續覆蓋: {'✅ 是' if temporal['continuous_coverage'] else '❌ 否'}")
    
    # 總結
    print("\n" + "=" * 70)
    print("總體評估")
    print("=" * 70)
    
    all_feasible = all(r.is_feasible for r in results)
    
    if all_feasible:
        print("\n✅ 時空錯置方案【可行】")
        print("\n實施建議:")
        print("1. Starlink: 選擇 100-120 顆分布在不同軌道面的衛星")
        print("2. OneWeb: 選擇 45-60 顆確保極區覆蓋的衛星")
        print("3. 使用智能排程算法優化衛星切換時機")
        print("4. 實施動態調整機制應對突發情況")
    else:
        print("\n❌ 時空錯置方案【挑戰較大】")
        print("\n主要問題:")
        for r in results:
            if not r.is_feasible:
                print(f"- {r.constellation}: 需要的子集過小，可能無法維持穩定覆蓋")
        print("\n替代方案:")
        print("1. 適當放寬目標可見數量範圍")
        print("2. 採用動態調整策略而非固定子集")
        print("3. 結合預測算法提前規劃衛星切換")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()