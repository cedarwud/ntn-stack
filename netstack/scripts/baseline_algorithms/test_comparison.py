"""
測試算法對比框架的簡化版本

驗證所有基準算法都能正常工作並進行基本對比
"""

import sys
import os
import numpy as np
import time
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# 添加項目路徑
sys.path.append('/home/sat/ntn-stack')
sys.path.append('/home/sat/ntn-stack/netstack')

# 導入環境
import gymnasium as gym
from netstack_api.envs.optimized_handover_env import OptimizedLEOSatelliteHandoverEnv
from netstack_api.envs.action_space_wrapper import CompatibleLEOHandoverEnv

# 導入基準算法
from baseline_algorithms import (
    InfocomAlgorithm, 
    SimpleThresholdAlgorithm, 
    RandomAlgorithm,
    AlgorithmEvaluator
)

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_algorithm_comparison():
    """測試算法對比功能"""
    print("=== 測試 LEO 衛星切換算法對比框架 ===")
    
    try:
        # 1. 設置環境
        print("\n1. 設置測試環境...")
        env_config = {
            'num_ues': 2,
            'num_satellites': 5,
            'simulation_time': 50.0,
            'random_seed': 42
        }
        
        base_env = OptimizedLEOSatelliteHandoverEnv(env_config)
        env = CompatibleLEOHandoverEnv(base_env)
        print(f"✓ 環境設置完成: {env_config}")
        
        # 2. 創建基準算法
        print("\n2. 創建基準算法...")
        algorithms = [
            InfocomAlgorithm({
                'delta_t': 5.0,
                'binary_search_precision': 0.01,
                'use_enhanced': True
            }),
            
            SimpleThresholdAlgorithm({
                'handover_threshold': 0.4,
                'emergency_threshold': 0.2,
                'hysteresis_margin': 0.1
            }),
            
            RandomAlgorithm({
                'handover_probability': 0.2,
                'prepare_probability': 0.3,
                'random_seed': 42
            })
        ]
        
        # 3. 註冊算法到評估器
        print("\n3. 註冊算法...")
        evaluator = AlgorithmEvaluator()
        for algo in algorithms:
            evaluator.register_algorithm(algo)
            print(f"✓ 已註冊: {algo.name}")
        
        # 4. 生成測試場景
        print("\n4. 生成測試場景...")
        scenarios = []
        observations = []
        infos = []
        
        for i in range(20):  # 生成20個場景
            obs, info = env.reset()
            
            # 運行幾步收集不同狀態
            for step in range(5):
                scenarios.append({
                    'observation': obs.copy(),
                    'info': info.copy(),
                    'episode': i,
                    'step': step
                })
                
                observations.append(obs.copy())
                infos.append(info.copy())
                
                # 隨機動作
                action = env.action_space.sample()
                obs, reward, terminated, truncated, info = env.step(action)
                
                if terminated or truncated:
                    break
        
        print(f"✓ 已生成 {len(scenarios)} 個測試場景")
        
        # 5. 運行算法對比
        print("\n5. 運行算法對比...")
        start_time = time.time()
        
        comparison_results = evaluator.compare_algorithms(observations, infos)
        
        evaluation_time = time.time() - start_time
        print(f"✓ 對比評估完成，耗時: {evaluation_time:.2f}秒")
        
        # 6. 顯示結果
        print("\n6. 對比結果:")
        print("=" * 80)
        
        individual_results = comparison_results.get('individual_results', {})
        
        for algo_name, data in individual_results.items():
            print(f"\n算法: {algo_name}")
            print("-" * 40)
            
            metrics = data.get('metrics', {})
            statistics = data.get('statistics', {})
            
            print(f"  平均決策時間: {metrics.get('average_decision_time', 0):.3f} ms")
            print(f"  平均預期延遲: {metrics.get('average_expected_latency', 0):.2f} ms")
            print(f"  平均預期成功率: {metrics.get('average_expected_success_rate', 0):.3f}")
            print(f"  切換率: {metrics.get('handover_rate', 0):.3f}")
            print(f"  準備率: {metrics.get('preparation_rate', 0):.3f}")
            print(f"  總決策數: {statistics.get('total_decisions', 0)}")
        
        # 7. 顯示排名
        print("\n7. 性能排名:")
        print("=" * 80)
        
        summary = comparison_results.get('summary', {})
        rankings = summary.get('algorithm_ranking', [])
        
        if rankings:
            print("綜合性能排名:")
            for i, entry in enumerate(rankings, 1):
                algo_name = entry['algorithm']
                score = entry['score']
                metrics = entry['metrics']
                
                print(f"{i}. {algo_name}")
                print(f"   綜合評分: {score:.4f}")
                print(f"   決策時間: {metrics.get('average_decision_time', 0):.3f} ms")
                print(f"   預期延遲: {metrics.get('average_expected_latency', 0):.2f} ms")
                print(f"   預期成功率: {metrics.get('average_expected_success_rate', 0):.3f}")
                print()
        
        # 8. 測試各算法的詳細資訊
        print("\n8. 算法詳細資訊:")
        print("=" * 80)
        
        for algo in algorithms:
            print(f"\n{algo.name}:")
            
            if hasattr(algo, 'get_algorithm_info'):
                info = algo.get_algorithm_info()
                print(f"  類型: {info.get('type', 'N/A')}")
                print(f"  描述: {info.get('description', 'N/A')}")
                
                features = info.get('features', [])
                if features:
                    print(f"  特性: {', '.join(features)}")
                
                perf_chars = info.get('performance_characteristics', {})
                if perf_chars:
                    print("  性能特徵:")
                    for key, value in perf_chars.items():
                        print(f"    {key}: {value}")
        
        # 9. 保存測試結果
        print("\n9. 保存測試結果...")
        
        output_dir = "/home/sat/ntn-stack/results/algorithm_comparison_test"
        os.makedirs(output_dir, exist_ok=True)
        
        test_results = {
            'test_metadata': {
                'timestamp': datetime.now().isoformat(),
                'scenarios_count': len(scenarios),
                'algorithms_count': len(algorithms),
                'evaluation_time': evaluation_time,
                'environment_config': env_config
            },
            'comparison_results': comparison_results,
            'algorithm_details': [
                algo.get_algorithm_info() if hasattr(algo, 'get_algorithm_info') else {'name': algo.name}
                for algo in algorithms
            ]
        }
        
        result_file = f"{output_dir}/test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(test_results, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 測試結果已保存: {result_file}")
        
        print("\n=== 測試完成 ===")
        print("所有基準算法都能正常工作，對比框架運行正常！")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        logger.error(f"測試過程中出現錯誤: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = test_algorithm_comparison()
    exit(0 if success else 1)