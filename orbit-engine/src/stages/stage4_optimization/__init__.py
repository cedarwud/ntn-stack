"""
Stage 4: 優化決策層 (Optimization Decision Layer)

根據 @docs/stages/stage4-optimization.md 設計

核心架構:
- stage4_optimization_processor.py           # 主處理器 - 優化決策協調
- pool_planner.py                           # 動態池規劃器
- handover_optimizer.py                     # 換手優化器
- multi_obj_optimizer.py                    # 多目標優化器

目標:
- 基於信號分析結果進行衛星選擇優化和換手決策
- 動態池規劃和衛星選擇優化
- 換手決策算法和策略制定
- 多目標優化（信號品質vs覆蓋範圍vs切換成本）
- 強化學習擴展點預留

設計原則:
- 決策集中: 所有優化和決策邏輯統一管理
- 多目標優化: 平衡信號品質、覆蓋範圍、切換成本
- 可擴展性: 為RL和其他高級算法預留擴展接口
- 實時響應: 支援動態環境變化的快速決策
"""

# 導入主要組件 - 優化決策層
from .stage4_optimization_processor import Stage4OptimizationProcessor
from .pool_planner import PoolPlanner, PoolRequirements, SatelliteCandidate
from .handover_optimizer import HandoverOptimizer, HandoverThresholds, HandoverEvent, HandoverTriggerType
from .multi_obj_optimizer import MultiObjectiveOptimizer, OptimizationObjective, ObjectiveFunction, OptimizationConstraint, ParetoSolution

# 向後兼容導入 (舊架構)
Stage4MainProcessor = Stage4OptimizationProcessor

__all__ = [
    # ✅ 新架構 - 優化決策層 (主要組件)
    'Stage4OptimizationProcessor',
    'PoolPlanner',
    'PoolRequirements',
    'SatelliteCandidate',
    'HandoverOptimizer',
    'HandoverThresholds',
    'HandoverEvent',
    'HandoverTriggerType',
    'MultiObjectiveOptimizer',
    'OptimizationObjective',
    'ObjectiveFunction',
    'OptimizationConstraint',
    'ParetoSolution',

    # 🔗 向後兼容 (舊架構別名)
    'Stage4MainProcessor'
]

# 模組版本信息
__version__ = "2.0.0"
__architecture__ = "optimization_decision_layer"
__compliance__ = "Grade_A_optimization_focused"