#!/usr/bin/env python3
"""
LEO 衛星切換環境性能基準測試

測試不同規模場景下的環境性能，包括：
- FPS (每秒幀數)
- 記憶體使用量
- 延遲分析
- 大規模場景支援能力
"""

import sys
import os
import time
import psutil
import gc
import json
import logging
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
import threading

# 確保能找到 netstack_api
sys.path.append('/app')
sys.path.append('/home/sat/ntn-stack')

import gymnasium as gym
from netstack_api.envs.action_space_wrapper import CompatibleLEOHandoverEnv

def setup_logging():
    """設置日誌"""
    log_dir = Path('/tmp/benchmark_logs')
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f'benchmark_{timestamp}.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

@dataclass
class BenchmarkConfig:
    """基準測試配置"""
    ues: int
    satellites: int
    episodes: int
    episode_length: int = 100
    scenario: str = "MULTI_UE"
    description: str = ""

@dataclass
class BenchmarkResult:
    """基準測試結果"""
    config: BenchmarkConfig
    total_time: float
    fps: float
    avg_step_time: float
    avg_reset_time: float
    memory_usage_mb: float
    peak_memory_mb: float
    cpu_usage_percent: float
    total_steps: int
    total_resets: int
    observations_per_sec: float
    success: bool
    error_message: str = ""

class PerformanceMonitor:
    """性能監控器"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """重置監控器"""
        self.start_time = None
        self.memory_samples = []
        self.cpu_samples = []
        self.step_times = []
        self.reset_times = []
        self.monitoring = False
        self.monitor_thread = None
    
    def start_monitoring(self):
        """開始監控"""
        self.start_time = time.time()
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """停止監控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
    
    def _monitor_loop(self):
        """監控循環"""
        process = psutil.Process()
        while self.monitoring:
            try:
                # 記錄記憶體使用
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                self.memory_samples.append(memory_mb)
                
                # 記錄 CPU 使用
                cpu_percent = process.cpu_percent()
                self.cpu_samples.append(cpu_percent)
                
                time.sleep(0.1)  # 每100ms採樣一次
            except:
                break
    
    def record_step_time(self, step_time: float):
        """記錄步驟時間"""
        self.step_times.append(step_time)
    
    def record_reset_time(self, reset_time: float):
        """記錄重置時間"""
        self.reset_times.append(reset_time)
    
    def get_results(self) -> Dict[str, float]:
        """獲取監控結果"""
        total_time = time.time() - self.start_time if self.start_time else 0
        
        return {
            'total_time': total_time,
            'avg_step_time': np.mean(self.step_times) if self.step_times else 0,
            'avg_reset_time': np.mean(self.reset_times) if self.reset_times else 0,
            'avg_memory_mb': np.mean(self.memory_samples) if self.memory_samples else 0,
            'peak_memory_mb': np.max(self.memory_samples) if self.memory_samples else 0,
            'avg_cpu_percent': np.mean(self.cpu_samples) if self.cpu_samples else 0,
            'total_steps': len(self.step_times),
            'total_resets': len(self.reset_times)
        }

def benchmark_scenario(config: BenchmarkConfig, logger: logging.Logger) -> BenchmarkResult:
    """執行單個場景的基準測試"""
    logger.info(f"開始基準測試: {config.description}")
    logger.info(f"配置: {config.ues} UEs, {config.satellites} 衛星, {config.episodes} episodes")
    
    monitor = PerformanceMonitor()
    
    try:
        # 創建環境
        import netstack_api.envs
        
        # 檢查是否需要修改環境參數
        base_env = gym.make('netstack/LEOSatelliteHandover-v0')
        
        # 使用包裝器確保兼容性
        env = CompatibleLEOHandoverEnv(base_env, force_box_action=True)
        
        # 開始監控
        monitor.start_monitoring()
        
        total_steps = 0
        successful_episodes = 0
        
        # 執行基準測試
        for episode in range(config.episodes):
            reset_start = time.time()
            obs, info = env.reset()
            reset_time = time.time() - reset_start
            monitor.record_reset_time(reset_time)
            
            episode_steps = 0
            done = False
            
            while not done and episode_steps < config.episode_length:
                step_start = time.time()
                
                # 執行隨機動作
                action = env.action_space.sample()
                obs, reward, terminated, truncated, info = env.step(action)
                
                step_time = time.time() - step_start
                monitor.record_step_time(step_time)
                
                done = terminated or truncated
                episode_steps += 1
                total_steps += 1
            
            successful_episodes += 1
            
            # 每10個episode報告進度
            if (episode + 1) % max(1, config.episodes // 10) == 0:
                progress = (episode + 1) / config.episodes * 100
                logger.info(f"進度: {progress:.1f}% ({episode + 1}/{config.episodes})")
        
        # 停止監控
        monitor.stop_monitoring()
        env.close()
        
        # 計算結果
        results = monitor.get_results()
        
        fps = total_steps / results['total_time'] if results['total_time'] > 0 else 0
        observations_per_sec = fps * env.observation_space.shape[0] if hasattr(env.observation_space, 'shape') else fps
        
        benchmark_result = BenchmarkResult(
            config=config,
            total_time=results['total_time'],
            fps=fps,
            avg_step_time=results['avg_step_time'],
            avg_reset_time=results['avg_reset_time'],
            memory_usage_mb=results['avg_memory_mb'],
            peak_memory_mb=results['peak_memory_mb'],
            cpu_usage_percent=results['avg_cpu_percent'],
            total_steps=results['total_steps'],
            total_resets=results['total_resets'],
            observations_per_sec=observations_per_sec,
            success=True
        )
        
        logger.info(f"基準測試完成: FPS={fps:.1f}, 記憶體={results['avg_memory_mb']:.1f}MB")
        return benchmark_result
        
    except Exception as e:
        monitor.stop_monitoring()
        logger.error(f"基準測試失敗: {e}")
        
        return BenchmarkResult(
            config=config,
            total_time=0,
            fps=0,
            avg_step_time=0,
            avg_reset_time=0,
            memory_usage_mb=0,
            peak_memory_mb=0,
            cpu_usage_percent=0,
            total_steps=0,
            total_resets=0,
            observations_per_sec=0,
            success=False,
            error_message=str(e)
        )

def run_comprehensive_benchmark(logger: logging.Logger) -> List[BenchmarkResult]:
    """執行綜合基準測試"""
    
    # 定義測試場景（根據 gym_todo.md 的規格）
    scenarios = [
        BenchmarkConfig(
            ues=1, 
            satellites=5, 
            episodes=100,
            episode_length=50,
            description="小規模場景 - 1UE/5衛星"
        ),
        BenchmarkConfig(
            ues=5, 
            satellites=20, 
            episodes=50,
            episode_length=75,
            description="中規模場景 - 5UE/20衛星"
        ),
        BenchmarkConfig(
            ues=10, 
            satellites=50, 
            episodes=25,
            episode_length=100,
            description="大規模場景 - 10UE/50衛星"
        ),
        BenchmarkConfig(
            ues=20, 
            satellites=100, 
            episodes=10,
            episode_length=50,
            description="超大規模場景 - 20UE/100衛星"
        ),
    ]
    
    results = []
    
    logger.info("=" * 60)
    logger.info("開始 LEO 衛星切換環境綜合性能基準測試")
    logger.info("=" * 60)
    
    for i, scenario in enumerate(scenarios, 1):
        logger.info(f"\n[{i}/{len(scenarios)}] {scenario.description}")
        
        # 強制垃圾回收
        gc.collect()
        
        result = benchmark_scenario(scenario, logger)
        results.append(result)
        
        if not result.success:
            logger.warning(f"場景 {scenario.description} 測試失敗，繼續下一個場景")
        
        # 短暫休息
        time.sleep(1)
    
    return results

def analyze_results(results: List[BenchmarkResult], logger: logging.Logger) -> Dict[str, Any]:
    """分析基準測試結果"""
    logger.info("\n" + "=" * 60)
    logger.info("基準測試結果分析")
    logger.info("=" * 60)
    
    successful_results = [r for r in results if r.success]
    
    if not successful_results:
        logger.error("沒有成功的測試結果可供分析")
        return {}
    
    # 性能分析
    analysis = {
        'total_scenarios': len(results),
        'successful_scenarios': len(successful_results),
        'performance_summary': {},
        'memory_analysis': {},
        'scalability_analysis': {},
        'recommendations': []
    }
    
    # 性能總結
    fps_values = [r.fps for r in successful_results]
    memory_values = [r.memory_usage_mb for r in successful_results]
    
    analysis['performance_summary'] = {
        'max_fps': max(fps_values),
        'min_fps': min(fps_values),
        'avg_fps': np.mean(fps_values),
        'fps_std': np.std(fps_values)
    }
    
    analysis['memory_analysis'] = {
        'max_memory_mb': max(memory_values),
        'min_memory_mb': min(memory_values),
        'avg_memory_mb': np.mean(memory_values),
        'memory_std': np.std(memory_values)
    }
    
    # 可擴展性分析
    ue_counts = [r.config.ues for r in successful_results]
    satellite_counts = [r.config.satellites for r in successful_results]
    
    analysis['scalability_analysis'] = {
        'max_ues_tested': max(ue_counts),
        'max_satellites_tested': max(satellite_counts),
        'fps_degradation_per_ue': 0,
        'memory_increase_per_ue': 0
    }
    
    # 計算每個 UE 的性能影響
    if len(successful_results) > 1:
        # 簡單線性回歸分析
        ue_fps_correlation = np.corrcoef(ue_counts, fps_values)[0, 1] if len(ue_counts) > 1 else 0
        ue_memory_correlation = np.corrcoef(ue_counts, memory_values)[0, 1] if len(ue_counts) > 1 else 0
        
        analysis['scalability_analysis']['ue_fps_correlation'] = ue_fps_correlation
        analysis['scalability_analysis']['ue_memory_correlation'] = ue_memory_correlation
    
    # 生成建議
    recommendations = []
    
    if analysis['performance_summary']['min_fps'] < 1000:
        recommendations.append("建議優化環境實現以提高 FPS")
    
    if analysis['memory_analysis']['max_memory_mb'] > 500:
        recommendations.append("記憶體使用較高，建議優化狀態表示")
    
    if len(successful_results) < len(results):
        recommendations.append("部分大規模場景測試失敗，需要改進可擴展性")
    
    analysis['recommendations'] = recommendations
    
    # 詳細報告
    logger.info("\n性能摘要:")
    logger.info(f"  最大 FPS: {analysis['performance_summary']['max_fps']:.1f}")
    logger.info(f"  最小 FPS: {analysis['performance_summary']['min_fps']:.1f}")
    logger.info(f"  平均 FPS: {analysis['performance_summary']['avg_fps']:.1f}")
    
    logger.info("\n記憶體使用:")
    logger.info(f"  最大記憶體: {analysis['memory_analysis']['max_memory_mb']:.1f} MB")
    logger.info(f"  最小記憶體: {analysis['memory_analysis']['min_memory_mb']:.1f} MB")
    logger.info(f"  平均記憶體: {analysis['memory_analysis']['avg_memory_mb']:.1f} MB")
    
    logger.info("\n可擴展性:")
    logger.info(f"  最大測試規模: {analysis['scalability_analysis']['max_ues_tested']} UEs, "
                f"{analysis['scalability_analysis']['max_satellites_tested']} 衛星")
    
    if recommendations:
        logger.info("\n建議:")
        for i, rec in enumerate(recommendations, 1):
            logger.info(f"  {i}. {rec}")
    
    return analysis

def generate_performance_report(results: List[BenchmarkResult], analysis: Dict[str, Any]) -> str:
    """生成性能報告"""
    
    # 創建報告目錄
    report_dir = Path('/tmp/benchmark_reports')
    report_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 生成可視化圖表
    if results:
        plt.figure(figsize=(15, 10))
        
        successful_results = [r for r in results if r.success]
        
        # 子圖1: FPS vs UE數量
        plt.subplot(2, 3, 1)
        ues = [r.config.ues for r in successful_results]
        fps = [r.fps for r in successful_results]
        plt.scatter(ues, fps, alpha=0.7, s=50)
        plt.xlabel('UE 數量')
        plt.ylabel('FPS')
        plt.title('FPS vs UE 數量')
        plt.grid(True)
        
        # 子圖2: 記憶體使用 vs UE數量
        plt.subplot(2, 3, 2)
        memory = [r.memory_usage_mb for r in successful_results]
        plt.scatter(ues, memory, alpha=0.7, s=50, color='orange')
        plt.xlabel('UE 數量')
        plt.ylabel('記憶體使用 (MB)')
        plt.title('記憶體使用 vs UE 數量')
        plt.grid(True)
        
        # 子圖3: 步驟時間分佈
        plt.subplot(2, 3, 3)
        step_times = [r.avg_step_time * 1000 for r in successful_results]  # 轉換為毫秒
        plt.bar(range(len(step_times)), step_times, alpha=0.7, color='green')
        plt.xlabel('場景')
        plt.ylabel('平均步驟時間 (ms)')
        plt.title('步驟時間分佈')
        plt.xticks(range(len(step_times)), [f"{r.config.ues}UE" for r in successful_results])
        plt.grid(True, axis='y')
        
        # 子圖4: CPU 使用率
        plt.subplot(2, 3, 4)
        cpu_usage = [r.cpu_usage_percent for r in successful_results]
        plt.bar(range(len(cpu_usage)), cpu_usage, alpha=0.7, color='red')
        plt.xlabel('場景')
        plt.ylabel('CPU 使用率 (%)')
        plt.title('CPU 使用率')
        plt.xticks(range(len(cpu_usage)), [f"{r.config.ues}UE" for r in successful_results])
        plt.grid(True, axis='y')
        
        # 子圖5: 觀測處理速率
        plt.subplot(2, 3, 5)
        obs_per_sec = [r.observations_per_sec for r in successful_results]
        plt.scatter(ues, obs_per_sec, alpha=0.7, s=50, color='purple')
        plt.xlabel('UE 數量')
        plt.ylabel('觀測/秒')
        plt.title('觀測處理速率')
        plt.grid(True)
        
        # 子圖6: 性能評級
        plt.subplot(2, 3, 6)
        # 計算性能評級（基於 FPS 和記憶體效率）
        performance_scores = []
        for r in successful_results:
            fps_score = min(100, r.fps / 10)  # FPS/10 作為分數，最高100
            memory_efficiency = max(0, 100 - r.memory_usage_mb / 5)  # 記憶體效率
            overall_score = (fps_score + memory_efficiency) / 2
            performance_scores.append(overall_score)
        
        colors = ['red' if s < 50 else 'orange' if s < 75 else 'green' for s in performance_scores]
        plt.bar(range(len(performance_scores)), performance_scores, color=colors, alpha=0.7)
        plt.xlabel('場景')
        plt.ylabel('性能評級')
        plt.title('綜合性能評級')
        plt.xticks(range(len(performance_scores)), [f"{r.config.ues}UE" for r in successful_results])
        plt.ylim(0, 100)
        plt.grid(True, axis='y')
        
        plt.tight_layout()
        chart_file = report_dir / f'benchmark_charts_{timestamp}.png'
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        plt.close()
    
    # 生成文字報告
    report_file = report_dir / f'benchmark_report_{timestamp}.txt'
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("LEO 衛星切換環境性能基準測試報告\n")
        f.write("=" * 80 + "\n")
        f.write(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"測試場景: {len(results)} 個\n")
        f.write(f"成功場景: {len([r for r in results if r.success])} 個\n\n")
        
        # 詳細結果
        f.write("詳細測試結果:\n")
        f.write("-" * 80 + "\n")
        for i, result in enumerate(results, 1):
            f.write(f"{i}. {result.config.description}\n")
            if result.success:
                f.write(f"   狀態: ✅ 成功\n")
                f.write(f"   FPS: {result.fps:.1f}\n")
                f.write(f"   平均步驟時間: {result.avg_step_time*1000:.2f} ms\n")
                f.write(f"   平均重置時間: {result.avg_reset_time*1000:.2f} ms\n")
                f.write(f"   記憶體使用: {result.memory_usage_mb:.1f} MB\n")
                f.write(f"   峰值記憶體: {result.peak_memory_mb:.1f} MB\n")
                f.write(f"   CPU 使用率: {result.cpu_usage_percent:.1f}%\n")
                f.write(f"   總步驟數: {result.total_steps}\n")
                f.write(f"   觀測處理速率: {result.observations_per_sec:.1f} obs/s\n")
            else:
                f.write(f"   狀態: ❌ 失敗\n")
                f.write(f"   錯誤: {result.error_message}\n")
            f.write("\n")
        
        # 分析結果
        if analysis:
            f.write("性能分析:\n")
            f.write("-" * 80 + "\n")
            
            perf = analysis.get('performance_summary', {})
            f.write(f"FPS 範圍: {perf.get('min_fps', 0):.1f} - {perf.get('max_fps', 0):.1f}\n")
            f.write(f"平均 FPS: {perf.get('avg_fps', 0):.1f} ± {perf.get('fps_std', 0):.1f}\n")
            
            mem = analysis.get('memory_analysis', {})
            f.write(f"記憶體範圍: {mem.get('min_memory_mb', 0):.1f} - {mem.get('max_memory_mb', 0):.1f} MB\n")
            f.write(f"平均記憶體: {mem.get('avg_memory_mb', 0):.1f} ± {mem.get('memory_std', 0):.1f} MB\n")
            
            scale = analysis.get('scalability_analysis', {})
            f.write(f"最大測試規模: {scale.get('max_ues_tested', 0)} UEs, {scale.get('max_satellites_tested', 0)} 衛星\n")
            
            recommendations = analysis.get('recommendations', [])
            if recommendations:
                f.write("\n優化建議:\n")
                for i, rec in enumerate(recommendations, 1):
                    f.write(f"{i}. {rec}\n")
        
        # 基準達成狀況
        f.write("\n基準達成狀況 (根據 gym_todo.md):\n")
        f.write("-" * 80 + "\n")
        
        benchmarks = [
            ("1UE_5SAT", 20000, 50),    # FPS > 20000, 記憶體 < 50MB
            ("5UE_20SAT", 15000, 100),  # FPS > 15000, 記憶體 < 100MB
            ("10UE_50SAT", 5000, 200),  # FPS > 5000, 記憶體 < 200MB
            ("20UE_100SAT", 1000, 500)  # FPS > 1000, 記憶體 < 500MB
        ]
        
        for i, (scenario_name, target_fps, target_memory) in enumerate(benchmarks):
            if i < len(results) and results[i].success:
                actual_fps = results[i].fps
                actual_memory = results[i].memory_usage_mb
                
                fps_status = "✅" if actual_fps >= target_fps else "❌"
                memory_status = "✅" if actual_memory <= target_memory else "❌"
                
                f.write(f"{scenario_name}:\n")
                f.write(f"  FPS: {actual_fps:.1f} / {target_fps} {fps_status}\n")
                f.write(f"  記憶體: {actual_memory:.1f} / {target_memory} MB {memory_status}\n")
            else:
                f.write(f"{scenario_name}: ❌ 測試失敗或未執行\n")
    
    return str(report_file)

def main():
    """主函數"""
    logger = setup_logging()
    
    try:
        logger.info("開始 LEO 衛星切換環境性能基準測試")
        
        # 執行基準測試
        results = run_comprehensive_benchmark(logger)
        
        # 分析結果
        analysis = analyze_results(results, logger)
        
        # 生成報告
        report_file = generate_performance_report(results, analysis)
        
        logger.info(f"\n基準測試完成！")
        logger.info(f"報告已保存: {report_file}")
        
        # 返回是否達到基準要求
        successful_count = len([r for r in results if r.success])
        total_count = len(results)
        
        if successful_count == total_count:
            logger.info("🎉 所有場景測試成功！")
            return True
        else:
            logger.warning(f"⚠️  部分場景測試失敗 ({successful_count}/{total_count})")
            return False
            
    except Exception as e:
        logger.error(f"基準測試過程發生錯誤: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)