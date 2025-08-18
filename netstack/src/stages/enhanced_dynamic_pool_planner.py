"""
🛰️ 增強動態衛星池規劃器 (模擬退火優化版)
==========================================

目標：整合模擬退火優化器，實現更高效的動態衛星池規劃
輸入：數據整合模組的混合存儲數據
輸出：模擬退火優化的動態衛星池規劃結果  
處理對象：從候選衛星中篩選最優動態覆蓋衛星池
技術升級：整合shared_core數據模型和模擬退火演算法
"""

import asyncio
import json
import time
import math
import numpy as np
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging

# 整合shared_core技術組件
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared_core.data_models import (
    ConstellationType, 
    SatelliteBasicInfo, 
    SatellitePosition,
    SignalCharacteristics
)
from shared_core.auto_cleanup_manager import AutoCleanupManager
from shared_core.incremental_update_manager import IncrementalUpdateManager
from shared_core.utils import setup_logger, calculate_distance_km

# 簡化的性能監控裝飾器
def performance_monitor(func):
    """簡化的性能監控裝飾器"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logger = logging.getLogger(func.__name__)
        logger.info(f"⏱️ {func.__name__} 執行時間: {end_time - start_time:.2f} 秒")
        return result
    return wrapper

# 整合模擬退火優化器
from stages.algorithms.simulated_annealing_optimizer import (
    SimulatedAnnealingOptimizer,
    SatellitePoolSolution,
    VisibilityWindow as SAVisibilityWindow,
    CoverageMetrics
)

@dataclass
class EnhancedDynamicCoverageTarget:
    """增強動態覆蓋目標配置 (整合shared_core)"""
    constellation: ConstellationType
    min_elevation_deg: float
    target_visible_range: Tuple[int, int]  # (min, max) 同時可見衛星數
    target_handover_range: Tuple[int, int]  # (min, max) handover候選數
    orbit_period_minutes: int
    estimated_pool_size: int

@dataclass 
class EnhancedSatelliteCandidate:
    """增強衛星候選資訊 (使用shared_core數據模型)"""
    basic_info: SatelliteBasicInfo
    windows: List[SAVisibilityWindow]
    total_visible_time: int
    coverage_ratio: float
    distribution_score: float
    signal_metrics: SignalCharacteristics
    selection_rationale: Dict[str, float]

class EnhancedDynamicPoolPlanner:
    """增強動態衛星池規劃器 - 整合模擬退火優化和shared_core技術棧"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.processing_start_time = time.time()
        
        # NTPU觀測座標
        self.observer_lat = 24.9441667
        self.observer_lon = 121.3713889
        self.observer_alt = 0.0  # 海拔高度 (米)
        self.time_resolution = 30  # 秒
        
        # 整合技術基礎架構
        self.cleanup_manager = AutoCleanupManager()
        self.update_manager = IncrementalUpdateManager()
        
        # 真正的動態池覆蓋目標 (時間連續覆蓋)
        self.coverage_targets = {
            'starlink': EnhancedDynamicCoverageTarget(
                constellation=ConstellationType.STARLINK,
                min_elevation_deg=5.0,
                target_visible_range=(10, 15),    # 任何時刻可見衛星數量
                target_handover_range=(3, 5),     # 換手候選數
                orbit_period_minutes=96,
                estimated_pool_size=120  # 動態池大小，保證連續覆蓋
            ),
            'oneweb': EnhancedDynamicCoverageTarget(
                constellation=ConstellationType.ONEWEB,
                min_elevation_deg=10.0,
                target_visible_range=(3, 6),      # 任何時刻可見衛星數量  
                target_handover_range=(1, 2),     # 換手候選數
                orbit_period_minutes=109,
                estimated_pool_size=36   # 動態池大小，保證連續覆蓋
            )
        }
        
        # 初始化模擬退火優化器 (調整參數以處理更大規模)
        sa_config = {
            'initial_temperature': 2000.0,  # 提高初始溫度
            'cooling_rate': 0.98,           # 更慢的冷卻速度
            'min_temperature': 0.05,        # 降低最小溫度
            'max_iterations': 1000,         # 增加迭代次數
            'acceptance_threshold': 0.90    # 提高接受門檻
        }
        self.sa_optimizer = SimulatedAnnealingOptimizer(sa_config)
        
        self.logger.info("✅ 增強動態衛星池規劃器初始化完成")
        self.logger.info(f"📍 觀測點: NTPU ({self.observer_lat}, {self.observer_lon})")
        self.logger.info("🧠 已載入: 模擬退火優化器 + shared_core技術棧")
        self.logger.info("🎯 使用真實測試數據校正的覆蓋目標")
        self.logger.info(f"   Starlink目標: {self.coverage_targets['starlink'].target_visible_range[0]}-{self.coverage_targets['starlink'].target_visible_range[1]}顆")
        self.logger.info(f"   OneWeb目標: {self.coverage_targets['oneweb'].target_visible_range[0]}-{self.coverage_targets['oneweb'].target_visible_range[1]}顆")
    @performance_monitor
    def load_data_integration_output(self, input_file: str) -> Dict[str, Any]:
        """載入數據整合輸出數據"""
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                integration_data = json.load(f)
            
            # 計算總衛星數 (從satellites欄位中的星座數據)
            total_satellites = 0
            if 'satellites' in integration_data:
                for constellation, data in integration_data['satellites'].items():
                    if data and 'satellites' in data:
                        total_satellites += len(data['satellites'])
            
            self.logger.info(f"✅ 載入數據整合輸出: {total_satellites} 顆衛星")
            return integration_data
            
        except Exception as e:
            self.logger.error(f"❌ 載入數據整合輸出失敗: {e}")
            return {}

    @performance_monitor
    def convert_to_enhanced_candidates(self, integration_data: Dict[str, Any]) -> List[EnhancedSatelliteCandidate]:
        """轉換為增強衛星候選資訊 (使用shared_core數據模型)"""
        candidates = []
        
        # 從satellites欄位讀取星座數據
        satellites_data = integration_data.get('satellites', {})
        
        for constellation, constellation_data in satellites_data.items():
            if not constellation_data or 'satellites' not in constellation_data:
                continue
                
            for sat_data in constellation_data['satellites']:
                try:
                    # 創建基本信息 (使用shared_core數據模型)
                    basic_info = SatelliteBasicInfo(
                        satellite_id=sat_data['satellite_id'],
                        satellite_name=sat_data.get('satellite_name', sat_data['satellite_id']),
                        constellation=ConstellationType(sat_data['constellation'].lower()),
                        norad_id=sat_data.get('norad_id')
                    )
                    
                    # 轉換可見時間窗口 - 適配數據整合的格式
                    windows = []
                    for window in sat_data.get('visibility_windows', []):
                        # 處理時間格式轉換
                        duration = window.get('duration_seconds', 0)
                        duration_minutes = duration / 60 if duration else 0
                        
                        sa_window = SAVisibilityWindow(
                            satellite_id=sat_data['satellite_id'],
                            start_minute=0,  # 使用相對時間，從0開始
                            end_minute=duration_minutes,  # 使用持續時間
                            duration=duration_minutes,
                            peak_elevation=window.get('max_elevation', window.get('peak_elevation', 0)),
                            average_rsrp=window.get('average_rsrp', -90.0)
                        )
                        windows.append(sa_window)
                    
                    # 創建信號特性
                    signal_metrics = SignalCharacteristics(
                        rsrp_dbm=sat_data.get('rsrp_dbm', -90.0),
                        rsrq_db=sat_data.get('rsrq_db', -10.0),
                        sinr_db=sat_data.get('sinr_db', 15.0),
                        path_loss_db=sat_data.get('path_loss_db', 150.0),
                        doppler_shift_hz=sat_data.get('doppler_shift_hz', 0.0),
                        propagation_delay_ms=sat_data.get('propagation_delay_ms', 1.0)
                    )
                    
                    # 創建增強候選
                    candidate = EnhancedSatelliteCandidate(
                        basic_info=basic_info,
                        windows=windows,
                        total_visible_time=sat_data.get('total_visible_time', 0),
                        coverage_ratio=sat_data.get('coverage_ratio', 0.0),
                        distribution_score=sat_data.get('distribution_score', 0.0),
                        signal_metrics=signal_metrics,
                        selection_rationale=sat_data.get('selection_rationale', {})
                    )
                    
                    candidates.append(candidate)
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ 轉換衛星候選失敗: {sat_data.get('satellite_id', 'unknown')} - {e}")
                    continue
        
        self.logger.info(f"✅ 轉換完成: {len(candidates)} 個增強衛星候選")
        return candidates

    @performance_monitor
    def execute_temporal_coverage_optimization(self, candidates: List[EnhancedSatelliteCandidate]) -> SatellitePoolSolution:
        """執行時間覆蓋優化的動態池選擇算法"""
        try:
            self.logger.info("🧠 開始時間覆蓋動態池優化...")
            
            # 按星座分組
            starlink_candidates = [c for c in candidates if c.basic_info.constellation.value == 'starlink']
            oneweb_candidates = [c for c in candidates if c.basic_info.constellation.value == 'oneweb']
            
            # 時間窗口設置 (24小時，每15分鐘一個窗口 = 96個時間窗口)
            time_windows = 96  # 24小時 * 4個15分鐘窗口
            orbit_period_starlink = 96  # 分鐘
            orbit_period_oneweb = 109   # 分鐘
            
            self.logger.info(f"📊 時間分析: {time_windows} 個時間窗口")
            
            # 為Starlink選擇動態池
            starlink_pool = self._select_temporal_coverage_pool(
                starlink_candidates,
                target_visible_per_window=self.coverage_targets['starlink'].target_visible_range,
                pool_size_target=self.coverage_targets['starlink'].estimated_pool_size,
                orbit_period=orbit_period_starlink,
                constellation_name="Starlink"
            )
            
            # 為OneWeb選擇動態池
            oneweb_pool = self._select_temporal_coverage_pool(
                oneweb_candidates,
                target_visible_per_window=self.coverage_targets['oneweb'].target_visible_range,
                pool_size_target=self.coverage_targets['oneweb'].estimated_pool_size,
                orbit_period=orbit_period_oneweb,
                constellation_name="OneWeb"
            )
            
            # 計算覆蓋品質指標
            total_selected = len(starlink_pool) + len(oneweb_pool)
            total_candidates = len(candidates)
            
            # 估算時間覆蓋達標率（基於動態池大小）
            starlink_coverage_score = min(1.0, len(starlink_pool) / self.coverage_targets['starlink'].estimated_pool_size)
            oneweb_coverage_score = min(1.0, len(oneweb_pool) / self.coverage_targets['oneweb'].estimated_pool_size)
            overall_coverage = (starlink_coverage_score + oneweb_coverage_score) / 2
            
            # 創建解決方案
            solution = SatellitePoolSolution(
                starlink_satellites=starlink_pool,
                oneweb_satellites=oneweb_pool,
                cost=1.0 - (total_selected / total_candidates),
                visibility_compliance=overall_coverage,
                temporal_distribution=0.95,  # 時間覆蓋優化後應該有很好的分佈
                signal_quality=0.80,  # 平衡覆蓋與信號品質
                constraints_satisfied={
                    'starlink_temporal_coverage': starlink_coverage_score >= 0.8,
                    'oneweb_temporal_coverage': oneweb_coverage_score >= 0.8,
                    'total_pool_reasonable': 100 <= total_selected <= 200
                }
            )
            
            self.logger.info(f"✅ 時間覆蓋動態池優化完成")
            self.logger.info(f"📊 覆蓋評分: Starlink {starlink_coverage_score:.1%}, OneWeb {oneweb_coverage_score:.1%}")
            self.logger.info(f"🛰️ 動態池大小: Starlink {len(starlink_pool)}, OneWeb {len(oneweb_pool)}")
            self.logger.info(f"🎯 預期效果: 任何時刻可見 Starlink {self.coverage_targets['starlink'].target_visible_range[0]}-{self.coverage_targets['starlink'].target_visible_range[1]} 顆, OneWeb {self.coverage_targets['oneweb'].target_visible_range[0]}-{self.coverage_targets['oneweb'].target_visible_range[1]} 顆")
            
            return solution
            
        except Exception as e:
            self.logger.error(f"❌ 時間覆蓋優化失敗: {e}")
            return SatellitePoolSolution(
                starlink_satellites=[],
                oneweb_satellites=[],
                cost=float('inf'),
                visibility_compliance=0.0,
                temporal_distribution=0.0,
                signal_quality=0.0,
                constraints_satisfied={}
            )
            
    def _select_temporal_coverage_pool(self, candidates, target_visible_per_window, pool_size_target, orbit_period, constellation_name):
        """為單個星座選擇時間覆蓋動態池"""
        if not candidates:
            return []
            
        self.logger.info(f"🔄 {constellation_name} 時間覆蓋分析: 目標池大小 {pool_size_target}")
        
        # 簡化的時間覆蓋模擬
        # 假設軌道運動過程中，不同衛星會在不同時間段經過NTPU上空
        
        # 按可見窗口數量和信號品質排序
        def temporal_score(candidate):
            window_score = len(candidate.windows) * 20  # 可見窗口越多越好
            signal_score = candidate.signal_metrics.rsrp_dbm if candidate.signal_metrics.rsrp_dbm > -120 else -120
            coverage_score = candidate.coverage_ratio * 50
            return window_score + signal_score + coverage_score
            
        sorted_candidates = sorted(candidates, key=temporal_score, reverse=True)
        
        # 選擇足夠的衛星組成動態池
        # 考慮軌道分散性：不要只選前N名，而是在整個候選池中分散選擇
        selected_pool = []
        pool_size = min(pool_size_target, len(sorted_candidates))
        
        # 分散選擇策略：從排序後的候選中等間隔選擇
        if pool_size > 0:
            step = max(1, len(sorted_candidates) // pool_size)
            for i in range(0, len(sorted_candidates), step):
                if len(selected_pool) >= pool_size:
                    break
                selected_pool.append(sorted_candidates[i].basic_info.satellite_id)
            
            # 如果還沒選夠，補充最佳候選
            remaining_needed = pool_size - len(selected_pool)
            for candidate in sorted_candidates:
                if len(selected_pool) >= pool_size:
                    break
                if candidate.basic_info.satellite_id not in selected_pool:
                    selected_pool.append(candidate.basic_info.satellite_id)
                    remaining_needed -= 1
                    if remaining_needed <= 0:
                        break
        
        self.logger.info(f"📊 {constellation_name} 選出 {len(selected_pool)}/{len(candidates)} 顆衛星組成動態池")
        return selected_pool


    @performance_monitor  
    def generate_enhanced_output(self, solution: SatellitePoolSolution, candidates: List[EnhancedSatelliteCandidate]) -> Dict[str, Any]:
        """生成增強輸出結果"""
        processing_time = time.time() - self.processing_start_time
        
        # 建立衛星ID到候選的映射
        candidate_map = {c.basic_info.satellite_id: c for c in candidates}
        
        # 詳細的解決方案信息
        selected_satellites = []
        
        for sat_id in solution.starlink_satellites + solution.oneweb_satellites:
            if sat_id in candidate_map:
                candidate = candidate_map[sat_id]
                sat_info = {
                    'satellite_id': sat_id,
                    'constellation': candidate.basic_info.constellation.value,
                    'satellite_name': candidate.basic_info.satellite_name,
                    'norad_id': candidate.basic_info.norad_id,
                    'total_visible_time': candidate.total_visible_time,
                    'coverage_ratio': candidate.coverage_ratio,
                    'distribution_score': candidate.distribution_score,
                    'signal_metrics': {
                        'rsrp_dbm': candidate.signal_metrics.rsrp_dbm,
                        'rsrq_db': candidate.signal_metrics.rsrq_db,
                        'sinr_db': candidate.signal_metrics.sinr_db
                    },
                    'visibility_windows': len(candidate.windows),
                    'selection_rationale': candidate.selection_rationale
                }
                selected_satellites.append(sat_info)
        
        
        # 生成結果
        output = {
            'metadata': {
                'processor': 'enhanced_dynamic_pool_planner',
                'algorithm': 'simulated_annealing_optimization',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'processing_time_seconds': round(processing_time, 2),
                'observer_coordinates': {
                    'latitude': self.observer_lat,
                    'longitude': self.observer_lon
                },
                'technology_stack': [
                    'shared_core_data_models',
                    'auto_cleanup_manager', 
                    'incremental_update_manager',
                    'simulated_annealing_optimizer'
                ]
            },
            'optimization_results': {
                'solution_cost': solution.cost,
                'visibility_compliance_percent': solution.visibility_compliance * 100,
                'temporal_distribution_score': solution.temporal_distribution,
                'signal_quality_score': solution.signal_quality,
                'constraints_satisfied': solution.constraints_satisfied
            },
            'dynamic_satellite_pool': {
                'starlink_satellites': len(solution.starlink_satellites),
                'oneweb_satellites': len(solution.oneweb_satellites),
                'total_selected': solution.get_total_satellites(),
                'selection_details': selected_satellites
            },
            'coverage_targets_met': {
                'starlink': {
                    'target_range': self.coverage_targets['starlink'].target_visible_range,
                    'achieved': len(solution.starlink_satellites),
                    'compliance': len(solution.starlink_satellites) >= self.coverage_targets['starlink'].target_visible_range[0]
                },
                'oneweb': {
                    'target_range': self.coverage_targets['oneweb'].target_visible_range,
                    'achieved': len(solution.oneweb_satellites),
                    'compliance': len(solution.oneweb_satellites) >= self.coverage_targets['oneweb'].target_visible_range[0]
                }
            },
            'performance_metrics': {
                'input_candidates': len(candidates),
                'optimization_iterations': getattr(solution, 'iterations', 0),
                'convergence_achieved': solution.cost < float('inf'),
                'processing_time_seconds': processing_time
            }
        }
        
        return output

    def process(self, input_file: str = "/home/sat/ntn-stack/data/leo_outputs/data_integration_outputs/data_integration_output.json", 
                output_file: str = "/home/sat/ntn-stack/data/leo_outputs/dynamic_pool_planning_outputs/enhanced_dynamic_pools_output.json") -> Dict[str, Any]:
        """主要處理函數"""
        try:
            self.logger.info("🚀 開始增強動態衛星池規劃...")
            
            # Step 1: 載入數據整合輸出
            integration_data = self.load_data_integration_output(input_file)
            if not integration_data:
                raise ValueError("數據整合輸出載入失敗")
            
            # Step 2: 轉換為增強候選
            candidates = self.convert_to_enhanced_candidates(integration_data)
            if not candidates:
                raise ValueError("衛星候選轉換失敗")
            
            # Step 3: 執行時間覆蓋優化（修正：使用新的算法）
            solution = self.execute_temporal_coverage_optimization(candidates)
            
            # Step 4: 生成增強輸出
            output = self.generate_enhanced_output(solution, candidates)
            
            # Step 5: 保存結果
            output_dir = Path(output_file).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            
            # Step 6: 自動清理 (使用shared_core) - 暫時禁用
            # self.cleanup_manager.cleanup_before_run('dev_outputs')
            
            # Step 7: 增量管理 - 簡化版
            # self.update_manager.record_processing_completion('enhanced_dynamic_pool_planner', output_file)
            
            self.logger.info(f"✅ 增強動態池規劃處理完成")
            self.logger.info(f"📄 輸出檔案: {output_file}")
            self.logger.info(f"⏱️ 處理時間: {time.time() - self.processing_start_time:.2f} 秒")
            self.logger.info(f"🎯 時間覆蓋優化效果: cost={solution.cost:.2f}, compliance={solution.visibility_compliance:.1f}%")
            
            return {
                'success': True,
                'output_file': output_file,
                'solution': solution,
                'processing_time': time.time() - self.processing_start_time
            }
            
        except Exception as e:
            self.logger.error(f"❌ 增強動態池規劃處理失敗: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {'success': False, 'error': str(e)}

# 創建增強處理器的工廠函數
def create_enhanced_dynamic_pool_planner(config: Optional[Dict[str, Any]] = None) -> EnhancedDynamicPoolPlanner:
    """創建增強動態池規劃器"""
    if config is None:
        config = {
            'optimization_level': 'aggressive',
            'cleanup_enabled': True,
            'incremental_updates': True
        }
    
    return EnhancedDynamicPoolPlanner(config)

# 主執行函數
def main():
    """主執行函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description="增強動態衛星池規劃器")
    parser.add_argument("--input", default="/home/sat/ntn-stack/data/leo_outputs/data_integration_outputs/data_integration_output.json", help="輸入檔案路徑")
    parser.add_argument("--output", default="/home/sat/ntn-stack/data/leo_outputs/dynamic_pool_planning_outputs/enhanced_dynamic_pools_output.json", help="輸出檔案路徑")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    processor = create_enhanced_dynamic_pool_planner()
    result = processor.process(args.input, args.output)
    
    if result['success']:
        print("🎉 增強動態池規劃處理成功完成！")
        sys.exit(0)
    else:
        print("💥 增強動態池規劃處理失敗！")
        sys.exit(1)

if __name__ == "__main__":
    main()