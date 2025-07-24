"""
Phase 3 智能選擇系統測試示例

展示如何使用 Phase 3 的智能算法選擇系統進行環境分析、算法匹配和性能預測
"""

import asyncio
import json
from typing import Dict, Any

# 導入 Phase 3 智能選擇系統
from netstack.netstack_api.services.rl_training.selection import (
    IntelligentSelector,
    SelectionConfig,
    SelectionStrategy,
    SelectionMode,
    PredictionModel
)


async def test_intelligent_selection():
    """測試智能選擇系統"""
    print("=== Phase 3 智能選擇系統測試 ===\n")
    
    # 1. 初始化智能選擇器
    selector = IntelligentSelector(device="cpu")
    print("✓ 智能選擇器初始化完成")
    
    # 2. 模擬環境數據
    environment_data = {
        "environment_id": "test_env_001",
        "environment_type": "gym",
        "observation_space": {
            "type": "Box",
            "shape": [84, 84, 4],
            "low": 0,
            "high": 255
        },
        "action_space": {
            "type": "Discrete",
            "n": 4
        },
        "reward_range": [-1, 1],
        "episode_length": 1000,
        "performance_metrics": {
            "average_reward": 0.5,
            "success_rate": 0.7,
            "convergence_episodes": 500
        }
    }
    
    print("✓ 環境數據準備完成")
    
    # 3. 測試不同的選擇策略
    strategies = [
        SelectionStrategy.PERFORMANCE_OPTIMIZED,
        SelectionStrategy.CONVERGENCE_OPTIMIZED,
        SelectionStrategy.STABILITY_OPTIMIZED,
        SelectionStrategy.BALANCED
    ]
    
    results = {}
    
    for strategy in strategies:
        print(f"\n--- 測試策略: {strategy.value} ---")
        
        # 配置選擇參數
        config = SelectionConfig(
            strategy=strategy,
            mode=SelectionMode.SINGLE_BEST,
            confidence_threshold=0.6,
            prediction_model=PredictionModel.ENSEMBLE
        )
        
        # 執行智能選擇
        try:
            result = await selector.select_algorithm(environment_data, config)
            results[strategy.value] = result
            
            print(f"✓ 選擇完成: {result.selected_algorithms}")
            print(f"  - 決策置信度: {result.decision_confidence:.3f}")
            print(f"  - 分析時間: {result.selection_time_seconds:.3f}s")
            print(f"  - 選擇理由: {result.selection_rationale[:2]}")
            
        except Exception as e:
            print(f"✗ 選擇失敗: {e}")
    
    # 4. 測試比較分析
    print(f"\n--- 比較分析 ---")
    
    algorithms_to_compare = ["DQN", "PPO", "SAC", "A2C"]
    
    try:
        comparison = await selector.comparative_analysis(
            environment_data, algorithms_to_compare
        )
        
        print("✓ 比較分析完成")
        print(f"  - 算法排名: {list(comparison['algorithm_rankings'].keys())}")
        print(f"  - 環境複雜度: {comparison['environment_summary']['complexity']:.3f}")
        
    except Exception as e:
        print(f"✗ 比較分析失敗: {e}")
    
    # 5. 測試集成選擇
    print(f"\n--- 集成選擇 ---")
    
    ensemble_config = SelectionConfig(
        strategy=SelectionStrategy.BALANCED,
        mode=SelectionMode.ENSEMBLE,
        top_k=3,
        confidence_threshold=0.5
    )
    
    try:
        ensemble_result = await selector.select_algorithm(environment_data, ensemble_config)
        
        print("✓ 集成選擇完成")
        print(f"  - 選中的算法: {ensemble_result.selected_algorithms}")
        print(f"  - 風險評估: {ensemble_result.risk_assessment}")
        print(f"  - 優化建議: {ensemble_result.optimization_suggestions[:3]}")
        
    except Exception as e:
        print(f"✗ 集成選擇失敗: {e}")
    
    # 6. 顯示統計信息
    print(f"\n--- 統計信息 ---")
    
    try:
        history = selector.get_selection_history()
        stats = selector.get_algorithm_performance_stats()
        
        print(f"✓ 選擇歷史記錄: {len(history)} 次")
        print(f"✓ 算法性能統計: {len(stats)} 個算法")
        
        # 顯示最佳算法
        if stats:
            best_algo = max(stats.items(), key=lambda x: x[1].get('avg_score', 0))
            print(f"  - 最佳算法: {best_algo[0]} (平均分數: {best_algo[1]['avg_score']:.3f})")
        
    except Exception as e:
        print(f"✗ 統計信息獲取失敗: {e}")
    
    print("\n=== 測試完成 ===")
    return results


async def test_detailed_analysis():
    """詳細分析測試"""
    print("\n=== 詳細分析測試 ===\n")
    
    selector = IntelligentSelector(device="cpu")
    
    # 複雜環境數據
    complex_environment = {
        "environment_id": "complex_env_001",
        "environment_type": "custom",
        "observation_space": {
            "type": "Box",
            "shape": [64, 64, 3],
            "low": -1,
            "high": 1
        },
        "action_space": {
            "type": "Box",
            "shape": [2],
            "low": -1,
            "high": 1
        },
        "reward_range": [-10, 10],
        "episode_length": 2000,
        "performance_metrics": {
            "average_reward": -0.5,
            "success_rate": 0.3,
            "convergence_episodes": 1200
        },
        "complexity_indicators": {
            "state_space_size": 12288,
            "action_space_size": 2,
            "reward_sparsity": 0.8,
            "environment_stochasticity": 0.6
        }
    }
    
    # 自適應選擇
    adaptive_config = SelectionConfig(
        strategy=SelectionStrategy.BALANCED,
        mode=SelectionMode.ADAPTIVE,
        confidence_threshold=0.7,
        max_training_time=1500,
        min_performance_threshold=0.5
    )
    
    try:
        result = await selector.select_algorithm(complex_environment, adaptive_config)
        
        print("✓ 自適應選擇完成")
        print(f"  - 選中算法: {result.selected_algorithms}")
        print(f"  - 環境複雜度: {result.environment_analysis.overall_complexity:.3f}")
        print(f"  - 學習難度: {result.environment_analysis.learning_difficulty:.3f}")
        print(f"  - 替代推薦: {result.alternative_recommendations}")
        
        # 顯示參數推薦
        print(f"  - 參數推薦:")
        for algo, params in result.parameter_recommendations.items():
            print(f"    {algo}: {params}")
        
    except Exception as e:
        print(f"✗ 自適應選擇失敗: {e}")


if __name__ == "__main__":
    async def main():
        await test_intelligent_selection()
        await test_detailed_analysis()
    
    asyncio.run(main())
