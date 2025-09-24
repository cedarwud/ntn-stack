"""
Link Feasibility Filter - 鏈路可行性篩選器

根據 stage2-orbital-computing.md 文檔第105-112行定義的功能職責：
- 基礎可見性檢查（幾何可見性）
- 星座特定服務門檻篩選（Starlink: 5°, OneWeb: 10°）
- 鏈路預算約束檢查（距離範圍200-2000km）
- 系統邊界驗證（地理邊界）
- 服務窗口計算（可通訊時間段）

這是Stage 2範圍內的純幾何和系統約束篩選，不涉及信號品質分析。
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from .visibility_filter import VisibilityFilter, VisibilityResult, VisibilityWindow


@dataclass
class LinkFeasibilityResult:
    """鏈路可行性評估結果"""
    satellite_id: str
    is_feasible: bool
    feasibility_score: float  # 0.0-1.0, 基於幾何約束的綜合評分
    service_windows: List[VisibilityWindow]
    constraint_checks: Dict[str, bool]
    quality_grade: str
    total_service_time_minutes: float
    reason: str


class LinkFeasibilityFilter:
    """
    鏈路可行性篩選器

    功能職責：
    - 基礎可見性檢查（幾何可見性）
    - 星座特定服務門檻篩選（Starlink: 5°, OneWeb: 10°）
    - 鏈路預算約束檢查（距離範圍200-2000km）
    - 系統邊界驗證（地理邊界）
    - 服務窗口計算（可通訊時間段）

    注：這是Stage 2範圍內的純幾何約束篩選，不進行信號品質分析
    """

    def __init__(self, observer_location: Dict[str, float], config: Optional[Dict[str, Any]] = None):
        """
        初始化鏈路可行性篩選器

        Args:
            observer_location: 觀測者位置
            config: 篩選配置參數
        """
        self.logger = logging.getLogger(f"{__name__}.LinkFeasibilityFilter")
        self.observer_location = observer_location
        self.config = config or {}

        # 初始化可見性篩選器（重用現有邏輯）
        self.visibility_filter = VisibilityFilter(observer_location, config)

        # 鏈路可行性特定參數
        self.min_service_window_minutes = self.config.get('min_service_window_minutes', 2.0)
        self.min_feasibility_score = self.config.get('min_feasibility_score', 0.6)
        self.quality_thresholds = self.config.get('quality_thresholds', {
            'A': {'min_score': 0.9, 'min_service_time': 30},
            'B': {'min_score': 0.8, 'min_service_time': 20},
            'C': {'min_score': 0.7, 'min_service_time': 10},
            'D': {'min_score': 0.6, 'min_service_time': 5}
        })

        self.logger.info("✅ LinkFeasibilityFilter 初始化完成")
        self.logger.info(f"   最小服務窗口: {self.min_service_window_minutes}分鐘")
        self.logger.info(f"   最小可行性評分: {self.min_feasibility_score}")

    def apply_constellation_elevation_threshold(self, satellites: Dict[str, Any], constellation_map: Dict[str, str]) -> Dict[str, Any]:
        """
        應用星座特定仰角門檻篩選

        Args:
            satellites: 衛星數據字典
            constellation_map: 星座映射

        Returns:
            Dict[str, Any]: 通過仰角篩選的衛星
        """
        # 重用VisibilityFilter的星座特定門檻邏輯
        return self.visibility_filter.batch_analyze_visibility(satellites, constellation_map)

    def apply_link_budget_constraints(self, satellites: Dict[str, VisibilityResult]) -> Dict[str, VisibilityResult]:
        """
        應用鏈路預算約束（距離範圍檢查）

        Args:
            satellites: 可見性分析結果

        Returns:
            Dict[str, VisibilityResult]: 通過鏈路預算約束的衛星
        """
        filtered_satellites = {}
        filtered_count = 0

        for satellite_id, result in satellites.items():
            if not result.is_visible:
                continue

            # 檢查服務窗口中的距離約束
            valid_windows = []
            for window in result.visible_windows:
                valid_positions = []
                for position in window.positions:
                    range_km = position.get('range_km', float('inf'))
                    if (self.visibility_filter.min_distance_km <= range_km <=
                        self.visibility_filter.max_distance_km):
                        valid_positions.append(position)

                # 如果窗口中有足夠的有效位置，保留此窗口
                if len(valid_positions) >= len(window.positions) * 0.8:  # 80%的位置有效
                    # 創建新的窗口對象，包含有效位置
                    from .visibility_filter import VisibilityWindow
                    valid_window = VisibilityWindow(
                        start_time=window.start_time,
                        end_time=window.end_time,
                        duration_minutes=len(valid_positions) * 0.5,  # 重新計算持續時間
                        max_elevation_deg=window.max_elevation_deg,
                        positions=valid_positions
                    )
                    valid_windows.append(valid_window)

            # 如果有有效的服務窗口，保留此衛星
            if valid_windows:
                # 更新結果對象
                updated_result = VisibilityResult(
                    satellite_id=result.satellite_id,
                    is_visible=True,
                    visible_windows=valid_windows,
                    total_visible_time_minutes=sum(w.duration_minutes for w in valid_windows),
                    next_pass_time=valid_windows[0].start_time if valid_windows else None,
                    analysis_successful=result.analysis_successful
                )
                filtered_satellites[satellite_id] = updated_result
            else:
                filtered_count += 1

        self.logger.debug(f"🔗 鏈路預算約束篩選: {len(filtered_satellites)}/{len(satellites)} 通過 (過濾{filtered_count}顆)")
        return filtered_satellites

    def calculate_service_windows(self, satellite_positions: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[VisibilityWindow]]:
        """
        計算服務時間窗口

        Args:
            satellite_positions: 衛星位置數據

        Returns:
            Dict[str, List[VisibilityWindow]]: 每顆衛星的服務窗口
        """
        service_windows = {}

        for satellite_id, positions in satellite_positions.items():
            try:
                # 使用VisibilityFilter計算基礎窗口
                visibility_windows = self.visibility_filter.calculate_visibility_windows(positions)

                # 應用服務窗口篩選
                filtered_windows = self.visibility_filter.filter_service_windows(
                    visibility_windows,
                    self.min_service_window_minutes
                )

                service_windows[satellite_id] = filtered_windows

            except Exception as e:
                self.logger.warning(f"衛星 {satellite_id} 服務窗口計算失敗: {e}")
                service_windows[satellite_id] = []

        return service_windows

    def calculate_feasibility_score(self, result: VisibilityResult, constellation: str = None) -> float:
        """
        計算鏈路可行性評分（基於幾何約束）

        Args:
            result: 可見性分析結果
            constellation: 星座類型

        Returns:
            float: 可行性評分 (0.0-1.0)
        """
        if not result.is_visible or not result.visible_windows:
            return 0.0

        score = 0.0

        # 因子1: 服務時間覆蓋率 (40%)
        service_coverage = min(result.total_visible_time_minutes / 60.0, 1.0)  # 最大1小時為滿分
        score += service_coverage * 0.4

        # 因子2: 服務窗口數量 (20%)
        window_count_score = min(len(result.visible_windows) / 10.0, 1.0)  # 最大10個窗口為滿分
        score += window_count_score * 0.2

        # 因子3: 平均仰角品質 (25%)
        if result.visible_windows:
            avg_elevation = sum(w.max_elevation_deg for w in result.visible_windows) / len(result.visible_windows)
            elevation_score = min(avg_elevation / 45.0, 1.0)  # 45度為滿分
            score += elevation_score * 0.25

        # 因子4: 星座特定加權 (15%)
        constellation_bonus = 0.0
        if constellation == 'starlink':
            constellation_bonus = 0.1  # Starlink LEO有優勢
        elif constellation == 'oneweb':
            constellation_bonus = 0.05  # OneWeb中軌
        score += constellation_bonus * 0.15

        return min(score, 1.0)

    def assess_link_feasibility(self, satellite_id: str, visibility_result: VisibilityResult, constellation: str = None) -> LinkFeasibilityResult:
        """
        評估單顆衛星的鏈路可行性

        Args:
            satellite_id: 衛星ID
            visibility_result: 可見性分析結果
            constellation: 星座類型

        Returns:
            LinkFeasibilityResult: 鏈路可行性評估結果
        """
        try:
            # 計算可行性評分
            feasibility_score = self.calculate_feasibility_score(visibility_result, constellation)

            # 約束檢查
            constraint_checks = {
                'visibility_passed': visibility_result.is_visible,
                'service_windows_exist': len(visibility_result.visible_windows) > 0,
                'minimum_service_time': visibility_result.total_visible_time_minutes >= self.min_service_window_minutes,
                'feasibility_score_passed': feasibility_score >= self.min_feasibility_score
            }

            # 判斷是否可行
            is_feasible = all(constraint_checks.values())

            # 品質評級
            quality_grade = 'F'
            for grade, thresholds in self.quality_thresholds.items():
                if (feasibility_score >= thresholds['min_score'] and
                    visibility_result.total_visible_time_minutes >= thresholds['min_service_time']):
                    quality_grade = grade
                    break

            # 生成原因描述
            if is_feasible:
                reason = f"通過所有約束檢查，評分: {feasibility_score:.2f}"
            else:
                failed_checks = [check for check, passed in constraint_checks.items() if not passed]
                reason = f"未通過約束: {', '.join(failed_checks)}"

            return LinkFeasibilityResult(
                satellite_id=satellite_id,
                is_feasible=is_feasible,
                feasibility_score=feasibility_score,
                service_windows=visibility_result.visible_windows,
                constraint_checks=constraint_checks,
                quality_grade=quality_grade,
                total_service_time_minutes=visibility_result.total_visible_time_minutes,
                reason=reason
            )

        except Exception as e:
            self.logger.error(f"衛星 {satellite_id} 鏈路可行性評估失敗: {e}")
            return LinkFeasibilityResult(
                satellite_id=satellite_id,
                is_feasible=False,
                feasibility_score=0.0,
                service_windows=[],
                constraint_checks={},
                quality_grade='F',
                total_service_time_minutes=0.0,
                reason=f"評估失敗: {str(e)}"
            )

    def batch_assess_link_feasibility(self, visibility_results: Dict[str, VisibilityResult], constellation_map: Dict[str, str] = None) -> Dict[str, LinkFeasibilityResult]:
        """
        批次評估多顆衛星的鏈路可行性

        Args:
            visibility_results: 可見性分析結果
            constellation_map: 星座映射

        Returns:
            Dict[str, LinkFeasibilityResult]: 鏈路可行性評估結果
        """
        self.logger.info(f"🔗 開始批次鏈路可行性評估: {len(visibility_results)} 顆衛星")

        feasibility_results = {}
        feasible_count = 0
        quality_stats = {}

        for satellite_id, visibility_result in visibility_results.items():
            constellation = constellation_map.get(satellite_id, 'other') if constellation_map else 'other'

            # 評估鏈路可行性
            feasibility_result = self.assess_link_feasibility(satellite_id, visibility_result, constellation)
            feasibility_results[satellite_id] = feasibility_result

            if feasibility_result.is_feasible:
                feasible_count += 1

                # 統計品質分布
                grade = feasibility_result.quality_grade
                if grade not in quality_stats:
                    quality_stats[grade] = 0
                quality_stats[grade] += 1

        # 輸出統計信息
        feasibility_rate = (feasible_count / len(visibility_results)) * 100 if visibility_results else 0
        self.logger.info(f"✅ 鏈路可行性評估完成: {feasible_count}/{len(visibility_results)} 顆衛星可行 ({feasibility_rate:.1f}%)")

        if quality_stats:
            quality_summary = ", ".join([f"{grade}級:{count}顆" for grade, count in sorted(quality_stats.items())])
            self.logger.info(f"🏆 可行性品質分布: {quality_summary}")

        return feasibility_results

    def get_feasibility_statistics(self, results: Dict[str, LinkFeasibilityResult]) -> Dict[str, Any]:
        """
        獲取鏈路可行性統計信息

        Args:
            results: 鏈路可行性評估結果

        Returns:
            Dict[str, Any]: 統計信息
        """
        if not results:
            return {
                "total_satellites": 0,
                "feasible_satellites": 0,
                "feasibility_rate": 0.0,
                "average_feasibility_score": 0.0,
                "total_service_time_minutes": 0.0,
                "quality_distribution": {},
                "constraint_failure_analysis": {}
            }

        feasible_satellites = [r for r in results.values() if r.is_feasible]
        total_service_time = sum(r.total_service_time_minutes for r in results.values())
        avg_score = sum(r.feasibility_score for r in results.values()) / len(results)

        # 品質分布統計
        quality_dist = {}
        for result in results.values():
            grade = result.quality_grade
            if grade not in quality_dist:
                quality_dist[grade] = 0
            quality_dist[grade] += 1

        # 約束失敗分析
        constraint_failures = {}
        for result in results.values():
            if not result.is_feasible:
                for constraint, passed in result.constraint_checks.items():
                    if not passed:
                        if constraint not in constraint_failures:
                            constraint_failures[constraint] = 0
                        constraint_failures[constraint] += 1

        return {
            "total_satellites": len(results),
            "feasible_satellites": len(feasible_satellites),
            "feasibility_rate": (len(feasible_satellites) / len(results)) * 100,
            "average_feasibility_score": round(avg_score, 3),
            "total_service_time_minutes": round(total_service_time, 2),
            "quality_distribution": quality_dist,
            "constraint_failure_analysis": constraint_failures
        }