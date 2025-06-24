#!/usr/bin/env python3
"""
環境優化效果對比測試

比較原始環境與優化環境的性能差異：
- v0: 原始環境
- v1: 優化環境  
- Ultra: 極速環境
"""

import sys
import time
import logging
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# 確保能找到 netstack_api
sys.path.append('/app')
sys.path.append('/home/sat/ntn-stack')

import gymnasium as gym
from netstack_api.envs.action_space_wrapper import CompatibleLEOHandoverEnv

def setup_logging():
    """設置日誌"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def benchmark_environment(env_id: str, test_name: str, episodes: int = 50, steps_per_episode: int = 100) -> Dict:
    """測試單個環境的性能"""
    logger = logging.getLogger(__name__)
    logger.info(f"測試 {test_name} ({env_id})")
    
    try:
        # 創建環境
        import netstack_api.envs
        
        if env_id.endswith('-Ultra'):
            # 極速環境直接使用，不需要包裝器
            env = gym.make(env_id)
        else:
            base_env = gym.make(env_id)
            env = CompatibleLEOHandoverEnv(base_env, force_box_action=True)
        
        # 測試重置性能
        reset_times = []
        step_times = []
        total_steps = 0
        
        start_time = time.time()
        
        for episode in range(episodes):
            # 測試重置時間
            reset_start = time.time()
            obs, info = env.reset()
            reset_time = time.time() - reset_start
            reset_times.append(reset_time)
            
            # 測試步驟時間
            for step in range(steps_per_episode):
                step_start = time.time()
                action = env.action_space.sample()
                obs, reward, terminated, truncated, info = env.step(action)
                step_time = time.time() - step_start
                step_times.append(step_time)
                total_steps += 1
                
                if terminated or truncated:
                    break
        
        total_time = time.time() - start_time
        fps = total_steps / total_time
        
        env.close()
        
        results = {
            'env_id': env_id,
            'test_name': test_name,
            'total_time': total_time,
            'total_steps': total_steps,
            'episodes': episodes,
            'fps': fps,
            'avg_reset_time': np.mean(reset_times) * 1000,  # ms
            'avg_step_time': np.mean(step_times) * 1000,    # ms
            'reset_time_std': np.std(reset_times) * 1000,
            'step_time_std': np.std(step_times) * 1000,
            'observation_shape': obs.shape if hasattr(obs, 'shape') else len(obs),
            'action_space': str(env.action_space),
            'success': True
        }
        
        logger.info(f"✅ {test_name}: FPS={fps:.1f}, 重置={results['avg_reset_time']:.2f}ms, 步驟={results['avg_step_time']:.2f}ms")
        return results
        
    except Exception as e:
        logger.error(f"❌ {test_name} 測試失敗: {e}")
        return {
            'env_id': env_id,
            'test_name': test_name,
            'error': str(e),
            'success': False
        }

def run_optimization_comparison():
    """運行優化對比測試"""
    logger = setup_logging()
    
    logger.info("=" * 60)
    logger.info("LEO 衛星切換環境優化效果對比測試")
    logger.info("=" * 60)
    
    # 測試配置
    test_configs = [
        {
            'env_id': 'netstack/LEOSatelliteHandover-v0',
            'test_name': '原始環境 (v0)',
            'episodes': 30,
            'steps': 50
        },
        {
            'env_id': 'netstack/LEOSatelliteHandover-v1', 
            'test_name': '優化環境 (v1)',
            'episodes': 30,
            'steps': 50
        },
        {
            'env_id': 'netstack/LEOSatelliteHandover-Ultra',
            'test_name': '極速環境 (Ultra)',
            'episodes': 30,
            'steps': 50
        }
    ]
    
    results = []
    
    for config in test_configs:
        result = benchmark_environment(
            config['env_id'],
            config['test_name'], 
            config['episodes'],
            config['steps']
        )
        results.append(result)
        
        # 短暫休息
        time.sleep(0.5)
    
    # 分析結果
    analyze_optimization_results(results, logger)
    
    return results

def analyze_optimization_results(results: List[Dict], logger):
    """分析優化結果"""
    logger.info("\n" + "=" * 60)
    logger.info("優化效果分析")
    logger.info("=" * 60)
    
    successful_results = [r for r in results if r.get('success', False)]
    
    if len(successful_results) < 2:
        logger.error("成功測試結果不足，無法進行對比分析")
        return
    
    # 基準測試 (v0)
    baseline = next((r for r in successful_results if 'v0' in r['env_id']), None)
    optimized = next((r for r in successful_results if 'v1' in r['env_id']), None)
    ultra = next((r for r in successful_results if 'Ultra' in r['env_id']), None)
    
    if not baseline:
        logger.error("未找到基準測試結果 (v0)")
        return
    
    logger.info("\n📊 性能對比:")
    logger.info(f"{'環境':<15} {'FPS':<10} {'重置時間':<10} {'步驟時間':<10} {'觀測維度':<10}")
    logger.info("-" * 60)
    
    for result in successful_results:
        obs_shape = str(result['observation_shape']) if isinstance(result['observation_shape'], tuple) else result['observation_shape']
        logger.info(f"{result['test_name']:<15} "
                   f"{result['fps']:<10.1f} "
                   f"{result['avg_reset_time']:<10.2f} "
                   f"{result['avg_step_time']:<10.2f} "
                   f"{obs_shape:<10}")
    
    # 改善分析
    if optimized:
        fps_improvement = (optimized['fps'] - baseline['fps']) / baseline['fps'] * 100
        reset_improvement = (baseline['avg_reset_time'] - optimized['avg_reset_time']) / baseline['avg_reset_time'] * 100
        step_improvement = (baseline['avg_step_time'] - optimized['avg_step_time']) / baseline['avg_step_time'] * 100
        
        logger.info(f"\n🚀 v1 優化效果:")
        logger.info(f"  FPS 改善: {fps_improvement:+.1f}%")
        logger.info(f"  重置時間改善: {reset_improvement:+.1f}%")
        logger.info(f"  步驟時間改善: {step_improvement:+.1f}%")
    
    if ultra:
        fps_improvement = (ultra['fps'] - baseline['fps']) / baseline['fps'] * 100
        reset_improvement = (baseline['avg_reset_time'] - ultra['avg_reset_time']) / baseline['avg_reset_time'] * 100
        step_improvement = (baseline['avg_step_time'] - ultra['avg_step_time']) / baseline['avg_step_time'] * 100
        
        logger.info(f"\n⚡ Ultra 優化效果:")
        logger.info(f"  FPS 改善: {fps_improvement:+.1f}%")
        logger.info(f"  重置時間改善: {reset_improvement:+.1f}%")
        logger.info(f"  步驟時間改善: {step_improvement:+.1f}%")
    
    # 目標達成檢查
    logger.info(f"\n🎯 目標達成狀況:")
    
    target_fps = 20000  # 小規模場景目標
    
    for result in successful_results:
        fps_status = "✅" if result['fps'] >= target_fps else "❌"
        logger.info(f"  {result['test_name']}: {result['fps']:.1f} / {target_fps} FPS {fps_status}")
    
    # 保存詳細報告
    save_optimization_report(results)

def save_optimization_report(results: List[Dict]):
    """保存優化對比報告"""
    report_dir = Path('/tmp/optimization_reports')
    report_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = report_dir / f'optimization_comparison_{timestamp}.txt'
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("LEO 衛星切換環境優化效果對比報告\n")
        f.write("=" * 80 + "\n")
        f.write(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"測試環境: {len(results)} 個\n\n")
        
        successful_results = [r for r in results if r.get('success', False)]
        
        # 詳細結果
        f.write("詳細測試結果:\n")
        f.write("-" * 80 + "\n")
        for result in results:
            f.write(f"環境: {result['test_name']} ({result['env_id']})\n")
            if result.get('success', False):
                f.write(f"  狀態: ✅ 成功\n")
                f.write(f"  FPS: {result['fps']:.1f}\n")
                f.write(f"  總時間: {result['total_time']:.2f} 秒\n")
                f.write(f"  總步驟: {result['total_steps']}\n")
                f.write(f"  平均重置時間: {result['avg_reset_time']:.2f} ms\n")
                f.write(f"  平均步驟時間: {result['avg_step_time']:.2f} ms\n")
                f.write(f"  觀測維度: {result['observation_shape']}\n")
                f.write(f"  動作空間: {result['action_space']}\n")
            else:
                f.write(f"  狀態: ❌ 失敗\n")
                f.write(f"  錯誤: {result.get('error', 'Unknown')}\n")
            f.write("\n")
        
        # 效能對比
        if len(successful_results) >= 2:
            baseline = next((r for r in successful_results if 'v0' in r['env_id']), None)
            if baseline:
                f.write("優化效果對比 (相對於 v0 基準):\n")
                f.write("-" * 80 + "\n")
                for result in successful_results:
                    if result['env_id'] == baseline['env_id']:
                        continue
                    
                    fps_improvement = (result['fps'] - baseline['fps']) / baseline['fps'] * 100
                    reset_improvement = (baseline['avg_reset_time'] - result['avg_reset_time']) / baseline['avg_reset_time'] * 100
                    step_improvement = (baseline['avg_step_time'] - result['avg_step_time']) / baseline['avg_step_time'] * 100
                    
                    f.write(f"{result['test_name']}:\n")
                    f.write(f"  FPS 改善: {fps_improvement:+.1f}%\n")
                    f.write(f"  重置時間改善: {reset_improvement:+.1f}%\n")
                    f.write(f"  步驟時間改善: {step_improvement:+.1f}%\n")
                    f.write("\n")
    
    print(f"優化對比報告已保存: {report_file}")

def main():
    """主函數"""
    try:
        results = run_optimization_comparison()
        
        # 檢查是否有成功的結果
        successful_count = len([r for r in results if r.get('success', False)])
        
        if successful_count >= 2:
            print("\n🎉 優化對比測試完成！")
            return True
        else:
            print(f"\n⚠️  優化對比測試部分失敗 ({successful_count}/{len(results)})")
            return False
            
    except Exception as e:
        print(f"優化對比測試過程發生錯誤: {e}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)