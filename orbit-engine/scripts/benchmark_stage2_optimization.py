#!/usr/bin/env python3
"""
階段二性能基準測試腳本
比較原始版本vs優化版本的性能差異

使用方法:
python scripts/benchmark_stage2_optimization.py [--sample-size 100] [--gpu] [--cpu-only]
"""

import os
import sys
import time
import argparse
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

# 添加項目根目錄到路徑
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(project_root, 'src'))

# 導入處理器
from stages.stage2_orbital_computing.stage2_orbital_computing_processor import Stage2OrbitalComputingProcessor
from stages.stage2_orbital_computing.optimized_stage2_processor import OptimizedStage2Processor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Stage2Benchmark:
    """階段二性能基準測試器"""

    def __init__(self, sample_size: int = None):
        self.sample_size = sample_size
        self.results = {}

    def load_stage1_output(self) -> Dict[str, Any]:
        """載入階段一輸出作為測試數據"""
        # 尋找最新的階段一輸出文件
        stage1_dir = os.path.join(project_root, 'data', 'outputs', 'stage1')

        if not os.path.exists(stage1_dir):
            raise FileNotFoundError(f"找不到階段一輸出目錄: {stage1_dir}")

        # 找最新的JSON文件
        json_files = [f for f in os.listdir(stage1_dir) if f.endswith('.json')]
        if not json_files:
            raise FileNotFoundError(f"階段一輸出目錄中沒有JSON文件: {stage1_dir}")

        # 使用最新的文件
        latest_file = sorted(json_files)[-1]
        stage1_output_path = os.path.join(stage1_dir, latest_file)

        if not os.path.exists(stage1_output_path):
            raise FileNotFoundError(f"找不到階段一輸出文件: {stage1_output_path}")

        with open(stage1_output_path, 'r', encoding='utf-8') as f:
            stage1_data = json.load(f)

        # 如果指定了樣本大小，進行採樣
        if self.sample_size and 'data' in stage1_data:
            tle_data = stage1_data['data'].get('tle_data', [])
            if len(tle_data) > self.sample_size:
                tle_data = tle_data[:self.sample_size]
                stage1_data['data']['tle_data'] = tle_data
                logger.info(f"📊 採樣模式: 使用 {self.sample_size} 顆衛星進行測試")

        logger.info(f"📁 載入階段一輸出: {stage1_output_path}")
        logger.info(f"📊 衛星數量: {len(stage1_data.get('data', {}).get('tle_data', []))}")

        return stage1_data

    def benchmark_original_processor(self, stage1_output: Dict[str, Any]) -> Dict[str, Any]:
        """基準測試原始處理器"""
        logger.info("📊 開始測試原始階段二處理器...")
        start_time = time.time()

        try:
            # 創建原始處理器
            original_processor = Stage2OrbitalComputingProcessor()

            # 執行處理
            result = original_processor.execute(stage1_output)

            execution_time = time.time() - start_time

            benchmark_result = {
                'processor_type': 'original',
                'execution_time': execution_time,
                'success': True,
                'error': None,
                'satellites_processed': result.get('metadata', {}).get('input_count', 0),
                'visible_satellites': result.get('metadata', {}).get('output_count', 0),
                'memory_usage': self._get_memory_usage()
            }

            logger.info(f"✅ 原始處理器完成: {execution_time:.2f}秒")

        except Exception as e:
            execution_time = time.time() - start_time
            benchmark_result = {
                'processor_type': 'original',
                'execution_time': execution_time,
                'success': False,
                'error': str(e),
                'satellites_processed': 0,
                'visible_satellites': 0,
                'memory_usage': self._get_memory_usage()
            }

            logger.error(f"❌ 原始處理器失敗: {e}")

        return benchmark_result

    def benchmark_optimized_processor(self, stage1_output: Dict[str, Any],
                                    enable_gpu: bool = True) -> Dict[str, Any]:
        """基準測試優化處理器"""
        logger.info(f"🚀 開始測試優化階段二處理器 (GPU: {enable_gpu})...")
        start_time = time.time()

        try:
            # 創建優化處理器
            optimized_processor = OptimizedStage2Processor(enable_optimization=True)

            # 如果不使用GPU，禁用GPU組件
            if not enable_gpu and hasattr(optimized_processor, 'parallel_sgp4'):
                optimized_processor.parallel_sgp4.config.enable_gpu = False
                optimized_processor.gpu_converter = None

            # 執行處理
            result = optimized_processor.execute(stage1_output)

            execution_time = time.time() - start_time

            # 提取優化指標
            optimization_metrics = result.get('optimization_metrics', {})

            benchmark_result = {
                'processor_type': 'optimized',
                'execution_time': execution_time,
                'success': True,
                'error': None,
                'satellites_processed': result.get('metadata', {}).get('input_count', 0),
                'visible_satellites': result.get('metadata', {}).get('output_count', 0),
                'memory_usage': self._get_memory_usage(),
                'optimization_metrics': optimization_metrics,
                'gpu_enabled': enable_gpu,
                'gpu_used': optimization_metrics.get('performance_breakdown', {}).get('gpu_acceleration_used', False),
                'cpu_parallel_used': optimization_metrics.get('performance_breakdown', {}).get('cpu_parallel_used', False)
            }

            logger.info(f"✅ 優化處理器完成: {execution_time:.2f}秒")

        except Exception as e:
            execution_time = time.time() - start_time
            benchmark_result = {
                'processor_type': 'optimized',
                'execution_time': execution_time,
                'success': False,
                'error': str(e),
                'satellites_processed': 0,
                'visible_satellites': 0,
                'memory_usage': self._get_memory_usage(),
                'gpu_enabled': enable_gpu,
                'gpu_used': False,
                'cpu_parallel_used': False
            }

            logger.error(f"❌ 優化處理器失敗: {e}")

        return benchmark_result

    def _get_memory_usage(self) -> Dict[str, float]:
        """獲取記憶體使用情況"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()

            return {
                'rss_mb': memory_info.rss / (1024 * 1024),
                'vms_mb': memory_info.vms / (1024 * 1024)
            }
        except ImportError:
            return {'rss_mb': 0, 'vms_mb': 0}

    def run_comparison_benchmark(self, test_gpu: bool = True,
                               test_cpu_only: bool = True) -> Dict[str, Any]:
        """運行比較基準測試"""
        logger.info("🎯 開始階段二性能比較測試...")

        # 載入測試數據
        stage1_output = self.load_stage1_output()

        # 測試配置
        test_configs = [
            {'name': 'original', 'func': self.benchmark_original_processor, 'args': [stage1_output]}
        ]

        if test_gpu:
            test_configs.append({
                'name': 'optimized_gpu',
                'func': self.benchmark_optimized_processor,
                'args': [stage1_output, True]
            })

        if test_cpu_only:
            test_configs.append({
                'name': 'optimized_cpu',
                'func': self.benchmark_optimized_processor,
                'args': [stage1_output, False]
            })

        # 執行測試
        benchmark_results = {}
        for config in test_configs:
            logger.info(f"\n🔬 測試配置: {config['name']}")
            result = config['func'](*config['args'])
            benchmark_results[config['name']] = result

        # 生成比較報告
        comparison_report = self._generate_comparison_report(benchmark_results)

        # 完整測試結果
        full_results = {
            'benchmark_timestamp': datetime.now(timezone.utc).isoformat(),
            'test_configuration': {
                'sample_size': self.sample_size,
                'test_gpu': test_gpu,
                'test_cpu_only': test_cpu_only
            },
            'individual_results': benchmark_results,
            'comparison_report': comparison_report
        }

        return full_results

    def _generate_comparison_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """生成比較報告"""
        report = {
            'performance_comparison': {},
            'recommendations': []
        }

        # 獲取基準時間（原始處理器）
        baseline_time = None
        if 'original' in results and results['original']['success']:
            baseline_time = results['original']['execution_time']

        # 計算性能改善
        for test_name, result in results.items():
            if test_name == 'original' or not result['success']:
                continue

            if baseline_time and baseline_time > 0:
                speedup = baseline_time / result['execution_time']
                improvement = ((baseline_time - result['execution_time']) / baseline_time) * 100

                report['performance_comparison'][test_name] = {
                    'execution_time': result['execution_time'],
                    'speedup_ratio': speedup,
                    'improvement_percentage': improvement,
                    'time_saved_seconds': baseline_time - result['execution_time']
                }

                # 生成建議
                if speedup > 3:
                    report['recommendations'].append(f"🚀 {test_name}: 顯著性能改善 ({speedup:.1f}x)")
                elif speedup > 1.5:
                    report['recommendations'].append(f"✅ {test_name}: 良好性能改善 ({speedup:.1f}x)")
                else:
                    report['recommendations'].append(f"⚠️ {test_name}: 性能改善有限 ({speedup:.1f}x)")

        return report

    def save_results(self, results: Dict[str, Any], output_path: str = None):
        """保存測試結果"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(project_root, 'data', f'stage2_benchmark_{timestamp}.json')

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        logger.info(f"📊 測試結果已保存: {output_path}")

    def print_summary(self, results: Dict[str, Any]):
        """打印測試摘要"""
        print("\n" + "="*60)
        print("🎯 階段二性能基準測試摘要")
        print("="*60)

        comparison = results.get('comparison_report', {}).get('performance_comparison', {})

        for test_name, metrics in comparison.items():
            print(f"\n📊 {test_name.upper()}:")
            print(f"  ⏱️  執行時間: {metrics['execution_time']:.2f}秒")
            print(f"  🚀 性能提升: {metrics['speedup_ratio']:.2f}x")
            print(f"  📈 改善百分比: {metrics['improvement_percentage']:.1f}%")
            print(f"  💾 節省時間: {metrics['time_saved_seconds']:.1f}秒")

        print(f"\n🎖️ 建議:")
        for recommendation in results.get('comparison_report', {}).get('recommendations', []):
            print(f"  {recommendation}")

        print("\n" + "="*60)


def main():
    parser = argparse.ArgumentParser(description='階段二性能基準測試')
    parser.add_argument('--sample-size', type=int, default=None,
                       help='測試樣本大小（衛星數量）')
    parser.add_argument('--gpu', action='store_true', default=True,
                       help='測試GPU加速版本')
    parser.add_argument('--cpu-only', action='store_true', default=True,
                       help='測試CPU並行版本')
    parser.add_argument('--original-only', action='store_true',
                       help='只測試原始版本')
    parser.add_argument('--output', type=str, default=None,
                       help='結果輸出路徑')

    args = parser.parse_args()

    # 創建基準測試器
    benchmark = Stage2Benchmark(sample_size=args.sample_size)

    if args.original_only:
        # 只測試原始版本
        stage1_output = benchmark.load_stage1_output()
        result = benchmark.benchmark_original_processor(stage1_output)
        print(f"原始處理器執行時間: {result['execution_time']:.2f}秒")
    else:
        # 運行完整比較測試
        results = benchmark.run_comparison_benchmark(
            test_gpu=args.gpu,
            test_cpu_only=args.cpu_only
        )

        # 保存結果
        benchmark.save_results(results, args.output)

        # 打印摘要
        benchmark.print_summary(results)


if __name__ == '__main__':
    main()