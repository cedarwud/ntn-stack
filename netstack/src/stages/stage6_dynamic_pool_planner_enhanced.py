"""
🛰️ 階段六：動態衛星池規劃器 (模擬退火增強版)
==============================================

目標：整合leo_restructure模擬退火優化器，實現更高效的動態衛星池規劃
輸入：階段五的混合存儲數據
輸出：模擬退火優化的動態衛星池規劃結果  
處理對象：從563顆候選中篩選最優動態覆蓋衛星池
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
sys.path.insert(0, '/app/src')
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

class Stage6EnhancedDynamicPoolPlanner:
    """增強動態衛星池規劃器 - 整合模擬退火優化和shared_core技術棧"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.processing_start_time = time.time()
        
        # NTPU觀測座標
        self.observer_lat = 24.9441667
        self.observer_lon = 121.3713889
        self.time_resolution = 30  # 秒
        
        # 整合技術基礎架構
        self.cleanup_manager = AutoCleanupManager()
        self.update_manager = IncrementalUpdateManager()
        
        # 動態覆蓋目標 (使用shared_core數據模型)
        self.coverage_targets = {
            'starlink': EnhancedDynamicCoverageTarget(
                constellation=ConstellationType.STARLINK,
                min_elevation_deg=5.0,
                target_visible_range=(10, 15),
                target_handover_range=(6, 8),
                orbit_period_minutes=96,
                estimated_pool_size=45
            ),
            'oneweb': EnhancedDynamicCoverageTarget(
                constellation=ConstellationType.ONEWEB,
                min_elevation_deg=10.0,
                target_visible_range=(3, 6),
                target_handover_range=(2, 3),
                orbit_period_minutes=109,
                estimated_pool_size=18
            )
        }
        
        # 初始化模擬退火優化器
        sa_config = {
            'initial_temperature': 1000.0,
            'cooling_rate': 0.95,
            'min_temperature': 0.1,
            'max_iterations': 500,
            'acceptance_threshold': 0.85
        }
        self.sa_optimizer = SimulatedAnnealingOptimizer(sa_config)
        
        self.logger.info("✅ 增強動態衛星池規劃器初始化完成")
        self.logger.info(f"📍 觀測點: NTPU ({self.observer_lat}, {self.observer_lon})")
        self.logger.info("🧠 已載入: 模擬退火優化器 + shared_core技術棧")

    @performance_monitor
    def load_stage5_data(self, input_file: str) -> Dict[str, Any]:
        """載入階段五輸出數據"""
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                stage5_data = json.load(f)
            
            self.logger.info(f"✅ 載入階段五數據: {len(stage5_data.get('integrated_satellites', []))} 顆衛星")
            return stage5_data
            
        except Exception as e:
            self.logger.error(f"❌ 載入階段五數據失敗: {e}")
            return {}

    @performance_monitor
    def convert_to_enhanced_candidates(self, stage5_data: Dict[str, Any]) -> List[EnhancedSatelliteCandidate]:
        """轉換為增強衛星候選資訊 (使用shared_core數據模型)"""
        candidates = []
        
        for sat_data in stage5_data.get('integrated_satellites', []):
            try:
                # 創建基本信息 (使用shared_core數據模型)
                basic_info = SatelliteBasicInfo(
                    satellite_id=sat_data['satellite_id'],
                    satellite_name=sat_data.get('satellite_name', sat_data['satellite_id']),
                    constellation=ConstellationType(sat_data['constellation'].lower()),
                    norad_id=sat_data.get('norad_id')
                )
                
                # 轉換可見時間窗口
                windows = []
                for window in sat_data.get('visibility_windows', []):
                    sa_window = SAVisibilityWindow(
                        satellite_id=sat_data['satellite_id'],
                        start_minute=window['start_minute'],
                        end_minute=window['end_minute'], 
                        duration=window['duration'],
                        peak_elevation=window['peak_elevation'],
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
    def execute_simulated_annealing_optimization(self, candidates: List[EnhancedSatelliteCandidate]) -> SatellitePoolSolution:
        """執行模擬退火優化"""
        try:
            self.logger.info("🧠 開始模擬退火優化...")
            
            # 準備輸入數據
            satellite_data = {}
            for candidate in candidates:
                satellite_data[candidate.basic_info.satellite_id] = {
                    'constellation': candidate.basic_info.constellation.value,
                    'windows': [
                        {
                            'start_minute': w.start_minute,
                            'end_minute': w.end_minute,
                            'duration': w.duration,
                            'peak_elevation': w.peak_elevation,
                            'average_rsrp': w.average_rsrp
                        }
                        for w in candidate.windows
                    ],
                    'signal_quality': candidate.signal_metrics.rsrp_dbm
                }
            
            # 執行優化
            solution = asyncio.run(self.sa_optimizer.optimize_satellite_pool(satellite_data))
            
            self.logger.info(f"✅ 模擬退火優化完成")
            self.logger.info(f"📊 解決方案品質: cost={solution.cost:.2f}, compliance={solution.visibility_compliance:.1f}%")
            self.logger.info(f"🛰️ 選中衛星: Starlink {len(solution.starlink_satellites)} + OneWeb {len(solution.oneweb_satellites)}")
            
            return solution
            
        except Exception as e:
            self.logger.error(f"❌ 模擬退火優化失敗: {e}")
            # 返回空解決方案
            return SatellitePoolSolution(
                starlink_satellites=[],
                oneweb_satellites=[],
                cost=float('inf'),
                visibility_compliance=0.0,
                temporal_distribution=0.0,
                signal_quality=0.0,
                constraints_satisfied={}
            )

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
                'stage': 'stage6_enhanced',
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

    def process(self, input_file: str = "/app/data/stage5_integration_output.json", 
                output_file: str = "/app/data/stage6_enhanced_dynamic_pools_output.json") -> Dict[str, Any]:
        """主要處理函數"""
        try:
            self.logger.info("🚀 開始階段六增強動態衛星池規劃...")
            
            # Step 1: 載入階段五數據
            stage5_data = self.load_stage5_data(input_file)
            if not stage5_data:
                raise ValueError("階段五數據載入失敗")
            
            # Step 2: 轉換為增強候選
            candidates = self.convert_to_enhanced_candidates(stage5_data)
            if not candidates:
                raise ValueError("衛星候選轉換失敗")
            
            # Step 3: 執行模擬退火優化
            solution = self.execute_simulated_annealing_optimization(candidates)
            
            # Step 4: 生成增強輸出
            output = self.generate_enhanced_output(solution, candidates)
            
            # Step 5: 保存結果
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            
            # Step 6: 自動清理 (使用shared_core)
            self.cleanup_manager.cleanup_old_outputs('dev_outputs')
            
            # Step 7: 更新增量管理
            self.update_manager.record_processing_completion('stage6_enhanced', output_file)
            
            self.logger.info(f"✅ 階段六增強處理完成")
            self.logger.info(f"📄 輸出檔案: {output_file}")
            self.logger.info(f"⏱️ 處理時間: {time.time() - self.processing_start_time:.2f} 秒")
            self.logger.info(f"🎯 優化效果: cost={solution.cost:.2f}, compliance={solution.visibility_compliance:.1f}%")
            
            return {
                'success': True,
                'output_file': output_file,
                'solution': solution,
                'processing_time': time.time() - self.processing_start_time
            }
            
        except Exception as e:
            self.logger.error(f"❌ 階段六增強處理失敗: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {'success': False, 'error': str(e)}

# 創建增強處理器的工廠函數
def create_enhanced_stage6_processor(config: Optional[Dict[str, Any]] = None) -> Stage6EnhancedDynamicPoolPlanner:
    """創建增強的階段六處理器"""
    if config is None:
        config = {
            'optimization_level': 'aggressive',
            'cleanup_enabled': True,
            'incremental_updates': True
        }
    
    return Stage6EnhancedDynamicPoolPlanner(config)

# 主執行函數
def main():
    """主執行函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description="階段六增強動態衛星池規劃器")
    parser.add_argument("--input", default="/app/data/stage5_integration_output.json", help="輸入檔案路徑")
    parser.add_argument("--output", default="/app/data/stage6_enhanced_dynamic_pools_output.json", help="輸出檔案路徑")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    processor = create_enhanced_stage6_processor()
    result = processor.process(args.input, args.output)
    
    if result['success']:
        print("🎉 階段六增強處理成功完成！")
        sys.exit(0)
    else:
        print("💥 階段六增強處理失敗！")
        sys.exit(1)

if __name__ == "__main__":
    main()