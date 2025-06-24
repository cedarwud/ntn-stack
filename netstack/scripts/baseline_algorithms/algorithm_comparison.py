"""
算法綜合對比評估腳本

對所有基準算法和 RL 算法進行全面性能對比，生成詳細報告和可視化結果
"""

import sys
import os
import numpy as np
import time
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# Optional dependencies for visualization
try:
    import matplotlib.pyplot as plt

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    print("Warning: matplotlib not available. Visualization will be skipped.")
    MATPLOTLIB_AVAILABLE = False

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    print(
        "Warning: pandas not available. Some data processing features will be limited."
    )
    PANDAS_AVAILABLE = False
from pathlib import Path

# 添加項目路徑
sys.path.append("/home/sat/ntn-stack")
sys.path.append("/home/sat/ntn-stack/netstack")

# 導入環境
import gymnasium as gym
from netstack_api.envs.optimized_handover_env import OptimizedLEOSatelliteHandoverEnv
from netstack_api.envs.action_space_wrapper import CompatibleLEOHandoverEnv

# 導入基準算法 (避免循環導入)
from .base_algorithm import BaseAlgorithm, AlgorithmResult
from .infocom2024_algorithm import InfocomAlgorithm
from .simple_threshold_algorithm import SimpleThresholdAlgorithm
from .random_algorithm import RandomAlgorithm

# 導入 RL 算法
try:
    from stable_baselines3 import DQN, PPO, SAC
    from stable_baselines3.common.evaluation import evaluate_policy

    STABLE_BASELINES_AVAILABLE = True
except ImportError:
    print("Warning: stable-baselines3 not available. RL algorithms will be skipped.")
    STABLE_BASELINES_AVAILABLE = False

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlgorithmEvaluator:
    """
    基準算法評估器

    提供標準化的算法對比評估功能
    """

    def __init__(self):
        """初始化評估器"""
        self.algorithms = []

    def register_algorithm(self, algorithm: BaseAlgorithm):
        """註冊算法"""
        self.algorithms.append(algorithm)

    def compare_algorithms(
        self, observations: List[np.ndarray], infos: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """對比多個算法的性能"""
        results = {
            "individual_results": {},
            "summary": {
                "total_scenarios": len(observations),
                "algorithm_count": len(self.algorithms),
                "algorithm_ranking": [],
            },
        }

        # 評估每個算法
        for algo in self.algorithms:
            algo_results = self._evaluate_single_algorithm(algo, observations, infos)
            results["individual_results"][algo.name] = algo_results

        # 生成排名
        ranking = []
        for algo_name, data in results["individual_results"].items():
            metrics = data.get("metrics", {})
            # 簡單評分：延遲越低越好，成功率越高越好，決策時間越短越好
            score = (
                (1 / (metrics.get("average_expected_latency", 1) + 0.1)) * 0.4
                + metrics.get("average_expected_success_rate", 0) * 0.4
                + (1 / (metrics.get("average_decision_time", 1) + 0.1)) * 0.2
            )

            ranking.append({"algorithm": algo_name, "score": score, "metrics": metrics})

        # 按分數排序
        ranking.sort(key=lambda x: x["score"], reverse=True)
        results["summary"]["algorithm_ranking"] = ranking

        return results

    def _evaluate_single_algorithm(
        self,
        algorithm: BaseAlgorithm,
        observations: List[np.ndarray],
        infos: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """評估單個算法"""
        metrics = {
            "total_decisions": len(observations),
            "handover_decisions": 0,
            "prepare_decisions": 0,
            "maintain_decisions": 0,
            "total_decision_time": 0,
            "expected_latencies": [],
            "expected_success_rates": [],
            "confidences": [],
        }

        # 逐個場景評估
        for obs, info in zip(observations, infos):
            start_time = time.time()

            try:
                result = algorithm.make_decision(obs, info)

                # 記錄決策時間
                decision_time = (time.time() - start_time) * 1000  # 轉為毫秒
                metrics["total_decision_time"] += decision_time

                # 記錄決策類型
                if result.handover_decision == 1:
                    metrics["handover_decisions"] += 1
                elif result.handover_decision == 2:
                    metrics["prepare_decisions"] += 1
                else:
                    metrics["maintain_decisions"] += 1

                # 記錄性能指標
                metrics["expected_latencies"].append(result.expected_latency)
                metrics["expected_success_rates"].append(result.expected_success_rate)
                metrics["confidences"].append(result.confidence)

            except Exception as e:
                logger.warning(f"算法 {algorithm.name} 決策失敗: {e}")
                # 使用默認值
                metrics["expected_latencies"].append(50.0)
                metrics["expected_success_rates"].append(0.5)
                metrics["confidences"].append(0.1)

        # 計算統計量
        statistics = {
            "total_decisions": metrics["total_decisions"],
            "handover_count": metrics["handover_decisions"],
            "prepare_count": metrics["prepare_decisions"],
            "maintain_count": metrics["maintain_decisions"],
        }

        # 計算平均值
        avg_metrics = {
            "average_decision_time": (
                metrics["total_decision_time"] / metrics["total_decisions"]
                if metrics["total_decisions"] > 0
                else 0
            ),
            "average_expected_latency": (
                np.mean(metrics["expected_latencies"])
                if metrics["expected_latencies"]
                else 0
            ),
            "average_expected_success_rate": (
                np.mean(metrics["expected_success_rates"])
                if metrics["expected_success_rates"]
                else 0
            ),
            "average_confidence": (
                np.mean(metrics["confidences"]) if metrics["confidences"] else 0
            ),
            "handover_rate": (
                metrics["handover_decisions"] / metrics["total_decisions"]
                if metrics["total_decisions"] > 0
                else 0
            ),
            "preparation_rate": (
                metrics["prepare_decisions"] / metrics["total_decisions"]
                if metrics["total_decisions"] > 0
                else 0
            ),
        }

        return {
            "metrics": avg_metrics,
            "statistics": statistics,
            "raw_data": {
                "expected_latencies": metrics["expected_latencies"],
                "expected_success_rates": metrics["expected_success_rates"],
                "confidences": metrics["confidences"],
            },
        }


class ComprehensiveAlgorithmComparison:
    """
    綜合算法對比評估系統

    支持基準算法與 RL 算法的全面性能對比
    """

    def __init__(
        self, output_dir: str = "/home/sat/ntn-stack/results/algorithm_comparison"
    ):
        """
        初始化對比評估系統

        Args:
            output_dir: 結果輸出目錄
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 初始化環境
        self.env = None
        self.test_scenarios = []

        # 算法容器
        self.baseline_evaluator = AlgorithmEvaluator()
        self.rl_models = {}

        # 結果存儲
        self.comparison_results = {}
        self.performance_metrics = {}

        logger.info(f"算法對比評估系統初始化完成，輸出目錄: {self.output_dir}")

    def setup_environment(self, env_config: Optional[Dict[str, Any]] = None):
        """設置測試環境"""
        try:
            # 使用優化版環境
            if env_config is None:
                env_config = {
                    "num_ues": 5,
                    "num_satellites": 10,
                    "simulation_time": 100.0,
                    "random_seed": 42,
                }

            base_env = OptimizedLEOSatelliteHandoverEnv(env_config)
            self.env = CompatibleLEOHandoverEnv(base_env)

            logger.info(f"測試環境設置完成: {env_config}")
            return True

        except Exception as e:
            logger.error(f"環境設置失敗: {e}")
            return False

    def register_baseline_algorithms(self):
        """註冊所有基準算法"""
        algorithms = [
            # IEEE INFOCOM 2024 算法
            InfocomAlgorithm(
                {"delta_t": 5.0, "binary_search_precision": 0.01, "use_enhanced": True}
            ),
            # 簡單閾值算法（不同配置）
            SimpleThresholdAlgorithm(
                {
                    "handover_threshold": 0.4,
                    "emergency_threshold": 0.2,
                    "hysteresis_margin": 0.1,
                }
            ),
            SimpleThresholdAlgorithm(
                {
                    "handover_threshold": 0.5,
                    "emergency_threshold": 0.3,
                    "hysteresis_margin": 0.05,
                    "name_suffix": "_Conservative",
                }
            ),
            # 隨機基準算法（不同配置）
            RandomAlgorithm(
                {
                    "handover_probability": 0.2,
                    "prepare_probability": 0.3,
                    "random_seed": 42,
                }
            ),
            RandomAlgorithm(
                {
                    "handover_probability": 0.1,
                    "prepare_probability": 0.2,
                    "random_seed": 42,
                    "name_suffix": "_Conservative",
                }
            ),
        ]

        for algo in algorithms:
            # 處理名稱後綴
            if hasattr(algo, "config") and "name_suffix" in algo.config:
                algo.name += algo.config["name_suffix"]

            self.baseline_evaluator.register_algorithm(algo)
            logger.info(f"已註冊基準算法: {algo.name}")

        return len(algorithms)

    def load_rl_models(self, model_dir: str = "/home/sat/ntn-stack/netstack/models"):
        """載入訓練好的 RL 模型"""
        if not STABLE_BASELINES_AVAILABLE:
            logger.warning("stable-baselines3 不可用，跳過 RL 模型載入")
            return 0

        model_dir = Path(model_dir)
        loaded_count = 0

        # 嘗試載入不同的 RL 模型
        model_configs = [
            ("DQN", "dqn_leo_handover.zip", DQN),
            ("PPO", "ppo_leo_handover.zip", PPO),
            ("SAC", "sac_leo_handover.zip", SAC),
        ]

        for name, filename, model_class in model_configs:
            model_path = model_dir / filename

            if model_path.exists():
                try:
                    model = model_class.load(str(model_path), env=self.env)
                    self.rl_models[name] = model
                    loaded_count += 1
                    logger.info(f"已載入 RL 模型: {name}")
                except Exception as e:
                    logger.error(f"載入 RL 模型 {name} 失敗: {e}")
            else:
                logger.warning(f"RL 模型文件不存在: {model_path}")

        return loaded_count

    def generate_test_scenarios(self, scenario_count: int = 100):
        """生成測試場景"""
        if self.env is None:
            raise ValueError("環境未初始化，請先調用 setup_environment()")

        scenarios = []

        logger.info(f"生成 {scenario_count} 個測試場景...")

        for i in range(scenario_count):
            # 重置環境獲得初始觀測
            obs, info = self.env.reset()

            # 運行幾步收集不同狀態
            episode_scenarios = []
            for step in range(np.random.randint(5, 20)):  # 隨機步數
                episode_scenarios.append(
                    {
                        "observation": obs.copy(),
                        "info": info.copy(),
                        "episode": i,
                        "step": step,
                    }
                )

                # 隨機動作以產生多樣化場景
                action = self.env.action_space.sample()
                obs, reward, terminated, truncated, info = self.env.step(action)

                if terminated or truncated:
                    break

            scenarios.extend(episode_scenarios)

        self.test_scenarios = scenarios
        logger.info(f"共生成 {len(scenarios)} 個測試場景")

        return len(scenarios)

    def evaluate_baseline_algorithms(self):
        """評估所有基準算法"""
        if not self.test_scenarios:
            raise ValueError("測試場景未生成，請先調用 generate_test_scenarios()")

        logger.info("開始評估基準算法...")

        # 準備評估數據
        observations = [scenario["observation"] for scenario in self.test_scenarios]
        infos = [scenario["info"] for scenario in self.test_scenarios]

        # 運行對比評估
        start_time = time.time()
        baseline_results = self.baseline_evaluator.compare_algorithms(
            observations, infos
        )
        evaluation_time = time.time() - start_time

        logger.info(f"基準算法評估完成，耗時: {evaluation_time:.2f}秒")

        # 存儲結果
        self.comparison_results["baseline"] = baseline_results
        self.comparison_results["baseline"]["evaluation_time"] = evaluation_time

        return baseline_results

    def evaluate_rl_algorithms(self):
        """評估 RL 算法"""
        if not self.rl_models:
            logger.warning("未載入 RL 模型，跳過 RL 算法評估")
            return {}

        logger.info("開始評估 RL 算法...")

        rl_results = {}

        for name, model in self.rl_models.items():
            logger.info(f"評估 RL 算法: {name}")

            start_time = time.time()

            try:
                # 使用 stable-baselines3 的評估函數
                mean_reward, std_reward = evaluate_policy(
                    model,
                    self.env,
                    n_eval_episodes=20,
                    deterministic=True,
                    return_episode_rewards=False,
                )

                # 收集詳細的決策資訊
                detailed_results = self._evaluate_rl_detailed(model, name)

                evaluation_time = time.time() - start_time

                rl_results[name] = {
                    "mean_reward": float(mean_reward),
                    "std_reward": float(std_reward),
                    "evaluation_time": evaluation_time,
                    "detailed_metrics": detailed_results,
                }

                logger.info(
                    f"RL 算法 {name} 評估完成: reward={mean_reward:.3f}±{std_reward:.3f}"
                )

            except Exception as e:
                logger.error(f"RL 算法 {name} 評估失敗: {e}")
                rl_results[name] = {
                    "error": str(e),
                    "evaluation_time": time.time() - start_time,
                }

        self.comparison_results["rl"] = rl_results
        return rl_results

    def _evaluate_rl_detailed(self, model, model_name: str) -> Dict[str, Any]:
        """詳細評估 RL 模型性能"""
        metrics = {
            "total_decisions": 0,
            "handover_decisions": 0,
            "avg_episode_length": 0,
            "avg_reward": 0,
            "success_episodes": 0,
            "decision_times": [],
        }

        total_episodes = 10

        for episode in range(total_episodes):
            obs, info = self.env.reset()
            episode_reward = 0
            episode_length = 0
            episode_decisions = 0

            while episode_length < 100:  # 限制最大步數
                start_time = time.time()

                # RL 模型預測
                action, _states = model.predict(obs, deterministic=True)

                decision_time = (time.time() - start_time) * 1000  # 轉為毫秒
                metrics["decision_times"].append(decision_time)

                obs, reward, terminated, truncated, info = self.env.step(action)

                episode_reward += reward
                episode_length += 1
                episode_decisions += 1

                # 檢查是否為切換決策（根據動作空間定義）
                if hasattr(action, "__iter__"):
                    if action[0] == 1:  # 假設第一個元素是切換決策
                        metrics["handover_decisions"] += 1

                if terminated or truncated:
                    if episode_reward > 0:  # 簡單的成功標準
                        metrics["success_episodes"] += 1
                    break

            metrics["total_decisions"] += episode_decisions
            metrics["avg_reward"] += episode_reward
            metrics["avg_episode_length"] += episode_length

        # 計算平均值
        metrics["avg_episode_length"] /= total_episodes
        metrics["avg_reward"] /= total_episodes
        metrics["avg_decision_time"] = (
            np.mean(metrics["decision_times"]) if metrics["decision_times"] else 0
        )
        metrics["handover_rate"] = (
            metrics["handover_decisions"] / metrics["total_decisions"]
            if metrics["total_decisions"] > 0
            else 0
        )
        metrics["success_rate"] = metrics["success_episodes"] / total_episodes

        return metrics

    def generate_comparison_report(self):
        """生成詳細的對比報告"""
        if not self.comparison_results:
            raise ValueError("尚未進行算法評估，請先運行評估")

        logger.info("生成算法對比報告...")

        report = {
            "metadata": {
                "generation_time": datetime.now().isoformat(),
                "test_scenarios_count": len(self.test_scenarios),
                "baseline_algorithms_count": len(self.baseline_evaluator.algorithms),
                "rl_algorithms_count": len(self.rl_models),
                "environment_config": str(self.env) if self.env else "N/A",
            },
            "baseline_results": self.comparison_results.get("baseline", {}),
            "rl_results": self.comparison_results.get("rl", {}),
            "overall_comparison": self._generate_overall_comparison(),
        }

        # 保存 JSON 報告
        report_path = (
            self.output_dir
            / f"algorithm_comparison_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"對比報告已保存: {report_path}")

        # 生成 Markdown 摘要報告
        self._generate_markdown_summary(report)

        return report

    def _generate_overall_comparison(self) -> Dict[str, Any]:
        """生成整體對比分析"""
        comparison = {
            "performance_ranking": [],
            "key_insights": [],
            "recommendations": [],
        }

        # 收集所有算法的關鍵指標
        all_algorithms = {}

        # 基準算法
        if "baseline" in self.comparison_results:
            baseline_data = self.comparison_results["baseline"]
            if "individual_results" in baseline_data:
                for algo_name, data in baseline_data["individual_results"].items():
                    metrics = data.get("metrics", {})
                    all_algorithms[algo_name] = {
                        "type": "baseline",
                        "avg_decision_time": metrics.get("average_decision_time", 0),
                        "avg_latency": metrics.get("average_expected_latency", 0),
                        "avg_success_rate": metrics.get(
                            "average_expected_success_rate", 0
                        ),
                        "handover_rate": metrics.get("handover_rate", 0),
                    }

        # RL 算法
        if "rl" in self.comparison_results:
            rl_data = self.comparison_results["rl"]
            for algo_name, data in rl_data.items():
                if "error" not in data and "detailed_metrics" in data:
                    detailed = data["detailed_metrics"]
                    all_algorithms[algo_name] = {
                        "type": "rl",
                        "avg_decision_time": detailed.get("avg_decision_time", 0),
                        "avg_reward": data.get("mean_reward", 0),
                        "success_rate": detailed.get("success_rate", 0),
                        "handover_rate": detailed.get("handover_rate", 0),
                    }

        # 生成排名（基於多個指標的綜合評分）
        for algo_name, metrics in all_algorithms.items():
            if metrics["type"] == "baseline":
                # 基準算法評分
                score = (
                    (1 / (metrics["avg_decision_time"] + 0.1)) * 0.2  # 決策速度
                    + (1 / (metrics["avg_latency"] + 0.1)) * 0.4  # 延遲性能
                    + metrics["avg_success_rate"] * 0.4  # 成功率
                )
            else:
                # RL 算法評分
                score = (
                    (1 / (metrics["avg_decision_time"] + 0.1)) * 0.2  # 決策速度
                    + (metrics["avg_reward"] + 100) / 100 * 0.4  # 獎勵性能
                    + metrics["success_rate"] * 0.4  # 成功率
                )

            comparison["performance_ranking"].append(
                {
                    "algorithm": algo_name,
                    "type": metrics["type"],
                    "score": score,
                    "metrics": metrics,
                }
            )

        # 按分數排序
        comparison["performance_ranking"].sort(key=lambda x: x["score"], reverse=True)

        # 生成洞察
        if comparison["performance_ranking"]:
            best_algo = comparison["performance_ranking"][0]
            comparison["key_insights"].append(
                f"最佳算法: {best_algo['algorithm']} (類型: {best_algo['type']})"
            )

            if len(comparison["performance_ranking"]) > 1:
                score_gap = (
                    best_algo["score"] - comparison["performance_ranking"][1]["score"]
                )
                comparison["key_insights"].append(f"最佳算法領先優勢: {score_gap:.3f}")

        return comparison

    def _generate_markdown_summary(self, report: Dict[str, Any]):
        """生成 Markdown 格式的摘要報告"""

        md_content = f"""# LEO 衛星切換算法對比報告

## 報告概覽
- **生成時間**: {report['metadata']['generation_time']}
- **測試場景數**: {report['metadata']['test_scenarios_count']}
- **基準算法數量**: {report['metadata']['baseline_algorithms_count']}
- **RL 算法數量**: {report['metadata']['rl_algorithms_count']}

## 性能排名

"""

        if (
            "overall_comparison" in report
            and "performance_ranking" in report["overall_comparison"]
        ):
            ranking = report["overall_comparison"]["performance_ranking"]

            md_content += "| 排名 | 算法名稱 | 類型 | 綜合評分 | 主要指標 |\n"
            md_content += "|------|----------|------|----------|----------|\n"

            for i, entry in enumerate(ranking[:10], 1):  # 只顯示前10名
                algo_name = entry["algorithm"]
                algo_type = entry["type"]
                score = entry["score"]

                if algo_type == "baseline":
                    metrics_summary = f"延遲: {entry['metrics']['avg_latency']:.1f}ms, 成功率: {entry['metrics']['avg_success_rate']:.2%}"
                else:
                    metrics_summary = f"獎勵: {entry['metrics']['avg_reward']:.2f}, 成功率: {entry['metrics']['success_rate']:.2%}"

                md_content += f"| {i} | {algo_name} | {algo_type} | {score:.3f} | {metrics_summary} |\n"

        md_content += """
## 主要發現

"""

        if (
            "overall_comparison" in report
            and "key_insights" in report["overall_comparison"]
        ):
            for insight in report["overall_comparison"]["key_insights"]:
                md_content += f"- {insight}\n"

        md_content += """
## 詳細結果

完整的詳細結果請參考 JSON 報告文件。

---
*此報告由 LEO 衛星切換算法對比系統自動生成*
"""

        # 保存 Markdown 報告
        md_path = (
            self.output_dir
            / f"algorithm_comparison_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        )
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        logger.info(f"Markdown 摘要報告已保存: {md_path}")

    def generate_visualization(self):
        """生成可視化圖表"""
        if not MATPLOTLIB_AVAILABLE:
            logger.warning("matplotlib 不可用，跳過可視化圖表生成")
            return

        if not self.comparison_results:
            logger.warning("無對比結果可供可視化")
            return

        logger.info("生成可視化圖表...")

        try:
            # 創建圖表目錄
            viz_dir = self.output_dir / "visualizations"
            viz_dir.mkdir(exist_ok=True)

            # 生成性能對比圖
            self._plot_performance_comparison(viz_dir)

            # 生成決策時間分布圖
            self._plot_decision_time_distribution(viz_dir)

            # 生成成功率對比圖
            self._plot_success_rate_comparison(viz_dir)

            logger.info(f"可視化圖表已保存到: {viz_dir}")

        except Exception as e:
            logger.error(f"生成可視化圖表失敗: {e}")

    def _plot_performance_comparison(self, output_dir: Path):
        """繪製性能對比圖"""
        if not MATPLOTLIB_AVAILABLE:
            return

        plt.figure(figsize=(12, 8))

        algorithms = []
        latencies = []
        success_rates = []

        # 收集基準算法數據
        if "baseline" in self.comparison_results:
            baseline_data = self.comparison_results["baseline"]
            if "individual_results" in baseline_data:
                for algo_name, data in baseline_data["individual_results"].items():
                    metrics = data.get("metrics", {})
                    algorithms.append(algo_name)
                    latencies.append(metrics.get("average_expected_latency", 0))
                    success_rates.append(
                        metrics.get("average_expected_success_rate", 0)
                    )

        if algorithms:
            x = np.arange(len(algorithms))

            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

            # 延遲對比
            ax1.bar(x, latencies, alpha=0.7, color="skyblue")
            ax1.set_xlabel("算法")
            ax1.set_ylabel("平均延遲 (ms)")
            ax1.set_title("算法延遲性能對比")
            ax1.set_xticks(x)
            ax1.set_xticklabels(algorithms, rotation=45, ha="right")

            # 成功率對比
            ax2.bar(x, success_rates, alpha=0.7, color="lightgreen")
            ax2.set_xlabel("算法")
            ax2.set_ylabel("平均成功率")
            ax2.set_title("算法成功率對比")
            ax2.set_xticks(x)
            ax2.set_xticklabels(algorithms, rotation=45, ha="right")

            plt.tight_layout()
            plt.savefig(
                output_dir / "performance_comparison.png", dpi=300, bbox_inches="tight"
            )
            plt.close()

    def _plot_decision_time_distribution(self, output_dir: Path):
        """繪製決策時間分布圖"""
        if not MATPLOTLIB_AVAILABLE:
            return

        plt.figure(figsize=(10, 6))

        # 收集決策時間數據
        decision_times = {}

        if "baseline" in self.comparison_results:
            baseline_data = self.comparison_results["baseline"]
            if "individual_results" in baseline_data:
                for algo_name, data in baseline_data["individual_results"].items():
                    metrics = data.get("metrics", {})
                    decision_times[algo_name] = metrics.get("average_decision_time", 0)

        if decision_times:
            algorithms = list(decision_times.keys())
            times = list(decision_times.values())

            plt.bar(algorithms, times, alpha=0.7, color="orange")
            plt.xlabel("算法")
            plt.ylabel("平均決策時間 (ms)")
            plt.title("算法決策速度對比")
            plt.xticks(rotation=45, ha="right")

            plt.tight_layout()
            plt.savefig(
                output_dir / "decision_time_comparison.png",
                dpi=300,
                bbox_inches="tight",
            )
            plt.close()

    def _plot_success_rate_comparison(self, output_dir: Path):
        """繪製成功率對比圖"""
        if not MATPLOTLIB_AVAILABLE:
            return

        plt.figure(figsize=(10, 6))

        # 收集所有算法的成功率數據
        all_success_rates = {}

        # 基準算法
        if "baseline" in self.comparison_results:
            baseline_data = self.comparison_results["baseline"]
            if "individual_results" in baseline_data:
                for algo_name, data in baseline_data["individual_results"].items():
                    metrics = data.get("metrics", {})
                    all_success_rates[f"{algo_name} (基準)"] = metrics.get(
                        "average_expected_success_rate", 0
                    )

        # RL 算法
        if "rl" in self.comparison_results:
            rl_data = self.comparison_results["rl"]
            for algo_name, data in rl_data.items():
                if "error" not in data and "detailed_metrics" in data:
                    success_rate = data["detailed_metrics"].get("success_rate", 0)
                    all_success_rates[f"{algo_name} (RL)"] = success_rate

        if all_success_rates:
            algorithms = list(all_success_rates.keys())
            success_rates = list(all_success_rates.values())

            colors = [
                "skyblue" if "(基準)" in algo else "lightcoral" for algo in algorithms
            ]

            plt.bar(algorithms, success_rates, alpha=0.7, color=colors)
            plt.xlabel("算法")
            plt.ylabel("成功率")
            plt.title("所有算法成功率對比")
            plt.xticks(rotation=45, ha="right")
            plt.ylim(0, 1)

            # 添加圖例
            from matplotlib.patches import Patch

            legend_elements = [
                Patch(facecolor="skyblue", label="基準算法"),
                Patch(facecolor="lightcoral", label="RL 算法"),
            ]
            plt.legend(handles=legend_elements)

            plt.tight_layout()
            plt.savefig(
                output_dir / "success_rate_comparison.png", dpi=300, bbox_inches="tight"
            )
            plt.close()

    def run_full_comparison(self):
        """運行完整的算法對比評估"""
        logger.info("開始完整的算法對比評估...")

        try:
            # 1. 設置環境
            if not self.setup_environment():
                raise Exception("環境設置失敗")

            # 2. 註冊基準算法
            baseline_count = self.register_baseline_algorithms()
            logger.info(f"已註冊 {baseline_count} 個基準算法")

            # 3. 載入 RL 模型
            rl_count = self.load_rl_models()
            logger.info(f"已載入 {rl_count} 個 RL 模型")

            # 4. 生成測試場景
            scenario_count = self.generate_test_scenarios(100)
            logger.info(f"已生成 {scenario_count} 個測試場景")

            # 5. 評估基準算法
            baseline_results = self.evaluate_baseline_algorithms()

            # 6. 評估 RL 算法
            rl_results = self.evaluate_rl_algorithms()

            # 7. 生成報告
            report = self.generate_comparison_report()

            # 8. 生成可視化
            self.generate_visualization()

            logger.info("完整的算法對比評估完成！")
            return report

        except Exception as e:
            logger.error(f"算法對比評估失敗: {e}")
            raise


def main():
    """主函數"""
    print("=== LEO 衛星切換算法綜合對比評估 ===")

    # 創建對比評估系統
    comparison_system = ComprehensiveAlgorithmComparison()

    try:
        # 運行完整對比
        results = comparison_system.run_full_comparison()

        print("\n=== 評估完成 ===")
        print(f"結果輸出目錄: {comparison_system.output_dir}")

        # 顯示簡要結果
        if (
            "overall_comparison" in results
            and "performance_ranking" in results["overall_comparison"]
        ):
            print("\n性能排名 (前5名):")
            for i, entry in enumerate(
                results["overall_comparison"]["performance_ranking"][:5], 1
            ):
                print(
                    f"{i}. {entry['algorithm']} ({entry['type']}) - 評分: {entry['score']:.3f}"
                )

    except Exception as e:
        print(f"評估過程中出現錯誤: {e}")
        logger.error(f"評估失敗: {e}", exc_info=True)


if __name__ == "__main__":
    main()
