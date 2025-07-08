"""
候選篩選器主類 - 整合多策略篩選和智能評分

此模組實現候選篩選層的核心協調器，負責：
- 整合多種篩選策略
- 協調評分引擎
- 管理策略動態切換
- 提供統一的篩選接口

主要組件：
- CandidateSelector: 主要篩選協調器
- StrategyManager: 策略管理器
- CandidatePool: 候選池管理
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime

from ..interfaces.candidate_selector import (
    CandidateSelectorInterface,
    Candidate,
    ScoredCandidate,
    SelectionStrategyError,
)
from ..interfaces.event_processor import ProcessedEvent
from .scoring import ScoringEngine
from .strategies.base_strategy import SelectionStrategy
from .strategies.elevation_strategy import ElevationStrategy
from .strategies.signal_strategy import SignalStrategy
from .strategies.load_strategy import LoadStrategy
from .strategies.distance_strategy import DistanceStrategy
from .strategies.visibility_strategy import VisibilityStrategy

logger = logging.getLogger(__name__)


@dataclass
class SelectionMetrics:
    """篩選性能指標"""

    total_satellites: int
    candidates_found: int
    strategies_used: List[str]
    selection_time_ms: float
    scoring_time_ms: float
    filter_time_ms: float
    top_score: float
    average_score: float
    confidence_distribution: Dict[str, int]


class StrategyManager:
    """策略管理器 - 動態管理和切換篩選策略"""

    def __init__(self):
        """初始化策略管理器"""
        self.strategies = self._initialize_strategies()
        self.strategy_performance = {}
        self.active_strategies = set(self.strategies.keys())

    def _initialize_strategies(self) -> Dict[str, SelectionStrategy]:
        """初始化所有可用策略"""
        return {
            "elevation": ElevationStrategy(),
            "signal": SignalStrategy(),
            "load": LoadStrategy(),
            "distance": DistanceStrategy(),
            "visibility": VisibilityStrategy(),
        }

    def get_active_strategies(self) -> Dict[str, SelectionStrategy]:
        """獲取當前活躍的策略"""
        return {
            name: strategy
            for name, strategy in self.strategies.items()
            if name in self.active_strategies
        }

    def enable_strategy(self, strategy_name: str) -> bool:
        """啟用特定策略"""
        if strategy_name in self.strategies:
            self.active_strategies.add(strategy_name)
            logger.info(f"策略已啟用: {strategy_name}")
            return True
        return False

    def disable_strategy(self, strategy_name: str) -> bool:
        """停用特定策略"""
        if strategy_name in self.active_strategies:
            self.active_strategies.discard(strategy_name)
            logger.info(f"策略已停用: {strategy_name}")
            return True
        return False

    def update_strategy_performance(
        self, strategy_name: str, success: bool, execution_time: float
    ):
        """更新策略性能統計"""
        if strategy_name not in self.strategy_performance:
            self.strategy_performance[strategy_name] = {
                "successes": 0,
                "failures": 0,
                "avg_time": 0.0,
                "total_calls": 0,
            }

        perf = self.strategy_performance[strategy_name]
        if success:
            perf["successes"] += 1
        else:
            perf["failures"] += 1

        perf["total_calls"] += 1
        perf["avg_time"] = (
            perf["avg_time"] * (perf["total_calls"] - 1) + execution_time
        ) / perf["total_calls"]


class CandidatePool:
    """候選池管理器 - 管理候選衛星的生命週期"""

    def __init__(self, max_pool_size: int = 50):
        """初始化候選池"""
        self.max_pool_size = max_pool_size
        self.candidates: List[Candidate] = []
        self.candidate_index: Dict[str, int] = {}

    def add_candidates(self, new_candidates: List[Candidate]) -> int:
        """添加候選衛星到池中"""
        added_count = 0
        for candidate in new_candidates:
            if candidate.satellite_id not in self.candidate_index:
                if len(self.candidates) < self.max_pool_size:
                    self.candidate_index[candidate.satellite_id] = len(self.candidates)
                    self.candidates.append(candidate)
                    added_count += 1
                else:
                    # 池已滿，替換評分最低的候選
                    self._replace_lowest_quality_candidate(candidate)
                    added_count += 1

        return added_count

    def _replace_lowest_quality_candidate(self, new_candidate: Candidate):
        """替換質量最低的候選衛星"""
        if not self.candidates:
            return

        # 簡單品質評估 (基於多個因素的綜合評分)
        def calculate_quality(candidate: Candidate) -> float:
            return (
                candidate.elevation / 90.0 * 0.3
                + (candidate.signal_strength + 140) / 40.0 * 0.3  # -140 to -100 dBm
                + (1.0 - candidate.load_factor) * 0.2
                + (candidate.visibility_time / 3600.0) * 0.2
            )  # normalize to hours

        # 找到質量最低的候選
        lowest_index = 0
        lowest_quality = calculate_quality(self.candidates[0])

        for i, candidate in enumerate(self.candidates[1:], 1):
            quality = calculate_quality(candidate)
            if quality < lowest_quality:
                lowest_quality = quality
                lowest_index = i

        # 檢查新候選是否比最低質量候選更好
        new_quality = calculate_quality(new_candidate)
        if new_quality > lowest_quality:
            old_candidate = self.candidates[lowest_index]
            del self.candidate_index[old_candidate.satellite_id]

            self.candidates[lowest_index] = new_candidate
            self.candidate_index[new_candidate.satellite_id] = lowest_index

    def get_candidates(self) -> List[Candidate]:
        """獲取所有候選衛星"""
        return self.candidates.copy()

    def clear(self):
        """清空候選池"""
        self.candidates.clear()
        self.candidate_index.clear()

    def remove_candidate(self, satellite_id: str) -> bool:
        """移除特定候選衛星"""
        if satellite_id in self.candidate_index:
            index = self.candidate_index[satellite_id]
            del self.candidate_index[satellite_id]
            self.candidates.pop(index)

            # 重建索引
            self.candidate_index = {
                candidate.satellite_id: i for i, candidate in enumerate(self.candidates)
            }
            return True
        return False


class CandidateSelector(CandidateSelectorInterface):
    """候選篩選器主類 - 整合多策略篩選和智能評分系統"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化候選篩選器

        Args:
            config: 配置參數，包含篩選閾值、權重等
        """
        self.logger = logging.getLogger(f"{__name__}.CandidateSelector")
        self.config = config or self._default_config()

        # 初始化核心組件
        self.strategy_manager = StrategyManager()
        self.scoring_engine = ScoringEngine()
        self.candidate_pool = CandidatePool(
            max_pool_size=self.config.get("max_pool_size", 50)
        )
        
        # 註冊策略到評分引擎
        for strategy_name, strategy in self.strategy_manager.strategies.items():
            self.scoring_engine.register_strategy(strategy, 1.0)

        # 性能監控
        self.metrics_history: List[SelectionMetrics] = []
        self.selection_count = 0

        self.logger.info(
            f"候選篩選器初始化完成 - 策略: {list(self.strategy_manager.strategies.keys())}, 配置: {self.config}"
        )

    def _default_config(self) -> Dict[str, Any]:
        """默認配置"""
        return {
            "max_candidates": 10,
            "min_elevation": 10.0,  # 度
            "min_signal_strength": -120.0,  # dBm
            "max_load_factor": 0.9,
            "min_visibility_time": 300.0,  # 秒
            "enable_parallel_processing": True,
            "strategy_timeout": 5.0,  # 秒
            "max_pool_size": 50,
            "scoring_weights": {
                "elevation": 0.25,
                "signal_strength": 0.25,
                "load_factor": 0.20,
                "distance": 0.15,
                "visibility_time": 0.15,
            },
        }

    async def select_candidates(
        self, processed_event: ProcessedEvent, satellite_pool: List[Dict]
    ) -> List[Candidate]:
        """
        從衛星池中選擇候選衛星

        Args:
            processed_event: 處理後的事件數據
            satellite_pool: 可用衛星池

        Returns:
            List[Candidate]: 篩選後的候選衛星列表
        """
        start_time = time.time()
        self.selection_count += 1

        try:
            # 清空之前的候選池
            self.candidate_pool.clear()

            # 並行執行所有活躍策略
            if self.config.get("enable_parallel_processing", True):
                candidates = await self._parallel_strategy_execution(
                    processed_event, satellite_pool
                )
            else:
                candidates = await self._sequential_strategy_execution(
                    processed_event, satellite_pool
                )

            # 去重和基本篩選
            unique_candidates = self._deduplicate_and_filter(candidates)

            # 限制候選數量
            max_candidates = self.config.get("max_candidates", 10)
            if len(unique_candidates) > max_candidates:
                # 根據基本品質快速排序
                unique_candidates = self._quick_sort_candidates(unique_candidates)[
                    :max_candidates
                ]

            selection_time = (time.time() - start_time) * 1000

            self.logger.info(
                f"候選篩選完成 - 事件類型: {processed_event.event_type}, 衛星池: {len(satellite_pool)}, "
                f"候選數: {len(unique_candidates)}, 耗時: {selection_time:.2f}ms"
            )

            return unique_candidates

        except Exception as e:
            self.logger.error(
                f"候選篩選失敗 - 事件類型: {processed_event.event_type}, 錯誤: {str(e)}"
            )
            raise SelectionStrategyError(f"候選篩選失敗: {str(e)}")

    async def _parallel_strategy_execution(
        self, processed_event: ProcessedEvent, satellite_pool: List[Dict]
    ) -> List[Candidate]:
        """並行執行策略篩選"""
        tasks = []
        active_strategies = self.strategy_manager.get_active_strategies()

        for strategy_name, strategy in active_strategies.items():
            task = asyncio.create_task(
                self._execute_strategy_with_timeout(
                    strategy, strategy_name, processed_event, satellite_pool
                )
            )
            tasks.append(task)

        # 等待所有策略完成
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 合併結果
        all_candidates = []
        for result in results:
            if isinstance(result, Exception):
                self.logger.warning(f"策略執行異常 - 錯誤: {str(result)}")
                continue
            if isinstance(result, list):
                all_candidates.extend(result)

        return all_candidates

    async def _sequential_strategy_execution(
        self, processed_event: ProcessedEvent, satellite_pool: List[Dict]
    ) -> List[Candidate]:
        """順序執行策略篩選"""
        all_candidates = []
        active_strategies = self.strategy_manager.get_active_strategies()

        for strategy_name, strategy in active_strategies.items():
            try:
                candidates = await self._execute_strategy_with_timeout(
                    strategy, strategy_name, processed_event, satellite_pool
                )
                all_candidates.extend(candidates)
            except Exception as e:
                self.logger.warning(
                    f"策略執行失敗 - 策略: {strategy_name}, 錯誤: {str(e)}"
                )
                continue

        return all_candidates

    async def _execute_strategy_with_timeout(
        self,
        strategy: SelectionStrategy,
        strategy_name: str,
        processed_event: ProcessedEvent,
        satellite_pool: List[Dict],
    ) -> List[Candidate]:
        """帶超時的策略執行"""
        timeout = self.config.get("strategy_timeout", 5.0)
        start_time = time.time()

        try:
            # 轉換衛星池格式
            converted_pool = [
                self._convert_satellite_data(sat) for sat in satellite_pool
            ]

            # 執行策略
            candidates = await asyncio.wait_for(
                asyncio.create_task(
                    strategy.select_candidates(processed_event, converted_pool)
                ),
                timeout=timeout,
            )

            execution_time = (time.time() - start_time) * 1000
            self.strategy_manager.update_strategy_performance(
                strategy_name, True, execution_time
            )

            self.logger.debug(
                f"策略執行成功 - 策略: {strategy_name}, 候選數: {len(candidates)}, 耗時: {execution_time:.2f}ms"
            )

            return candidates

        except asyncio.TimeoutError:
            execution_time = (time.time() - start_time) * 1000
            self.strategy_manager.update_strategy_performance(
                strategy_name, False, execution_time
            )
            self.logger.warning(f"策略執行超時 - 策略: {strategy_name}, 超時: {timeout}s")
            return []
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.strategy_manager.update_strategy_performance(
                strategy_name, False, execution_time
            )
            self.logger.error(f"策略執行異常 - 策略: {strategy_name}, 錯誤: {str(e)}")
            return []

    def _convert_satellite_data(self, satellite_dict: Dict) -> Candidate:
        """轉換衛星數據格式為Candidate對象"""
        return Candidate(
            satellite_id=satellite_dict.get("norad_id", "unknown"),
            elevation=satellite_dict.get("elevation", 0.0),
            signal_strength=satellite_dict.get("signal_strength", -120.0),
            load_factor=satellite_dict.get("load_factor", 0.5),
            distance=satellite_dict.get("distance", 1000.0),
            azimuth=satellite_dict.get("azimuth", 0.0),
            doppler_shift=satellite_dict.get("doppler_shift", 0.0),
            position=satellite_dict.get("position", {"x": 0.0, "y": 0.0, "z": 0.0}),
            velocity=satellite_dict.get("velocity", {"vx": 0.0, "vy": 0.0, "vz": 0.0}),
            visibility_time=satellite_dict.get("visibility_time", 600.0),
        )

    def _deduplicate_and_filter(self, candidates: List[Candidate]) -> List[Candidate]:
        """去重和基本篩選"""
        # 去重 (基於衛星ID)
        seen_ids: Set[str] = set()
        unique_candidates = []

        for candidate in candidates:
            if candidate.satellite_id not in seen_ids:
                seen_ids.add(candidate.satellite_id)
                unique_candidates.append(candidate)

        # 基本篩選
        filtered_candidates = []
        for candidate in unique_candidates:
            if self._meets_basic_criteria(candidate):
                filtered_candidates.append(candidate)

        return filtered_candidates

    def _meets_basic_criteria(self, candidate: Candidate) -> bool:
        """檢查候選是否滿足基本條件"""
        return (
            candidate.elevation >= self.config.get("min_elevation", 10.0)
            and candidate.signal_strength
            >= self.config.get("min_signal_strength", -120.0)
            and candidate.load_factor <= self.config.get("max_load_factor", 0.9)
            and candidate.visibility_time
            >= self.config.get("min_visibility_time", 300.0)
        )

    def _quick_sort_candidates(self, candidates: List[Candidate]) -> List[Candidate]:
        """快速排序候選衛星 (基於簡單評分)"""

        def quick_score(candidate: Candidate) -> float:
            return (
                candidate.elevation / 90.0 * 0.3
                + (candidate.signal_strength + 140) / 40.0 * 0.3
                + (1.0 - candidate.load_factor) * 0.2
                + min(1.0, candidate.visibility_time / 3600.0) * 0.2
            )

        return sorted(candidates, key=quick_score, reverse=True)

    async def score_candidates(
        self, candidates: List[Candidate], context: Dict[str, Any] = None
    ) -> List[ScoredCandidate]:
        """
        對候選衛星進行詳細評分

        Args:
            candidates: 候選衛星列表
            context: 額外上下文信息

        Returns:
            List[ScoredCandidate]: 評分後的候選列表
        """
        start_time = time.time()

        try:
            # 使用評分引擎進行詳細評分
            # 創建虛擬事件用於評分
            dummy_event = ProcessedEvent(
                event_type="scoring",
                timestamp=time.time(),
                confidence=1.0,
                ue_id="scoring_dummy",
                source_cell="dummy",
                target_cells=[],
                event_data=context or {},
                trigger_conditions={},
                measurement_values={}
            )
            
            scoring_result = self.scoring_engine.score_candidates(
                candidates, dummy_event, {}
            )
            
            # 轉換結果格式
            scored_candidates = scoring_result.scored_candidates

            scoring_time = (time.time() - start_time) * 1000

            self.logger.info(
                f"候選評分完成 - 候選數: {len(candidates)}, 評分數: {len(scored_candidates)}, 耗時: {scoring_time:.2f}ms"
            )

            return scored_candidates

        except Exception as e:
            self.logger.error(f"候選評分失敗 - 錯誤: {str(e)}")
            raise SelectionStrategyError(f"候選評分失敗: {str(e)}")

    def filter_candidates(
        self, candidates: List[Candidate], criteria: Dict[str, Any]
    ) -> List[Candidate]:
        """
        根據動態條件篩選候選衛星

        Args:
            candidates: 候選衛星列表
            criteria: 篩選條件

        Returns:
            List[Candidate]: 篩選後的候選列表
        """
        filtered = []

        for candidate in candidates:
            if self._matches_criteria(candidate, criteria):
                filtered.append(candidate)

        self.logger.debug(
            f"動態篩選完成 - 原始: {len(candidates)}, 篩選後: {len(filtered)}, 條件: {criteria}"
        )

        return filtered

    def _matches_criteria(self, candidate: Candidate, criteria: Dict[str, Any]) -> bool:
        """檢查候選是否匹配條件"""
        for key, value in criteria.items():
            if key == "min_elevation" and candidate.elevation < value:
                return False
            elif key == "max_elevation" and candidate.elevation > value:
                return False
            elif key == "min_signal_strength" and candidate.signal_strength < value:
                return False
            elif key == "max_load_factor" and candidate.load_factor > value:
                return False
            elif key == "min_visibility_time" and candidate.visibility_time < value:
                return False
            elif key == "excluded_satellites" and candidate.satellite_id in value:
                return False
            elif key == "preferred_satellites" and candidate.satellite_id not in value:
                return False

        return True

    def get_selection_strategies(self) -> List[str]:
        """獲取可用的篩選策略列表"""
        return list(self.strategy_manager.strategies.keys())

    async def apply_strategy(
        self,
        strategy_name: str,
        candidates: List[Candidate],
        parameters: Dict[str, Any] = None,
    ) -> List[Candidate]:
        """
        應用特定的篩選策略

        Args:
            strategy_name: 策略名稱
            candidates: 候選列表
            parameters: 策略參數

        Returns:
            List[Candidate]: 策略篩選後的候選列表
        """
        if strategy_name not in self.strategy_manager.strategies:
            raise SelectionStrategyError(f"未知策略: {strategy_name}")

        strategy = self.strategy_manager.strategies[strategy_name]

        try:
            # 應用策略特定的篩選
            result = await strategy.apply_advanced_filtering(
                candidates, parameters or {}
            )

            self.logger.debug(
                f"策略應用完成 - 策略: {strategy_name}, 輸入: {len(candidates)}, 輸出: {len(result)}"
            )

            return result

        except Exception as e:
            self.logger.error(f"策略應用失敗 - 策略: {strategy_name}, 錯誤: {str(e)}")
            raise SelectionStrategyError(f"策略 {strategy_name} 應用失敗: {str(e)}")

    def calculate_visibility_window(
        self, candidate: Candidate, user_position: Dict[str, float]
    ) -> float:
        """
        計算候選衛星的可見時間窗口

        Args:
            candidate: 候選衛星
            user_position: 用戶位置

        Returns:
            float: 可見時間 (秒)
        """
        # 這裡可以實現更精確的可見時間計算
        # 目前返回候選自帶的可見時間
        return candidate.visibility_time

    def get_performance_metrics(self) -> Dict[str, Any]:
        """獲取性能指標"""
        strategy_perf = self.strategy_manager.strategy_performance

        return {
            "selection_count": self.selection_count,
            "strategy_performance": strategy_perf,
            "active_strategies": list(self.strategy_manager.active_strategies),
            "candidate_pool_size": len(self.candidate_pool.candidates),
            "recent_metrics": (
                self.metrics_history[-10:] if self.metrics_history else []
            ),
        }

    def update_config(self, new_config: Dict[str, Any]):
        """更新配置"""
        self.config.update(new_config)
        self.logger.info(f"配置已更新: {new_config}")

    def reset_metrics(self):
        """重置性能指標"""
        self.metrics_history.clear()
        self.selection_count = 0
        self.strategy_manager.strategy_performance.clear()
        self.logger.info("性能指標已重置")
