"""
手換算法服務
實現 IEEE INFOCOM 2024 論文的核心算法邏輯
包含 Fine-Grained Synchronized Algorithm 和 Binary Search Refinement
"""

import logging
import uuid
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timedelta

from app.domains.handover.models.handover_models import (
    HandoverPredictionRecord,
    HandoverPredictionRequest,
    HandoverPredictionResponse,
    BinarySearchIteration,
    HandoverStatus,
    HandoverTriggerType,
)
from app.domains.satellite.services.orbit_service import OrbitService
from app.domains.coordinates.models.coordinate_model import GeoCoordinate

logger = logging.getLogger(__name__)


class HandoverAlgorithmService:
    """
    核心換手算法服務
    實現二點預測算法和二分搜索精化
    """

    def __init__(self, orbit_service: OrbitService):
        self.orbit_service = orbit_service

    async def perform_two_point_prediction(
        self, request: HandoverPredictionRequest, ue_location: GeoCoordinate
    ) -> HandoverPredictionResponse:
        """
        執行二點預測算法 - Fine-Grained Synchronized Algorithm

        Args:
            request: 預測請求
            ue_location: UE 位置座標

        Returns:
            HandoverPredictionResponse: 預測結果
        """
        logger.info(f"開始二點預測算法，UE ID: {request.ue_id}")

        prediction_id = str(uuid.uuid4())
        current_time = datetime.utcnow()
        future_time = current_time + timedelta(seconds=request.delta_t_seconds)

        try:
            # 第一步：獲取當前時間 T 的最佳衛星 AT
            current_best_satellite = await self._select_best_satellite(
                current_time, ue_location
            )

            # 第二步：獲取未來時間 T+Δt 的最佳衛星 AT+Δt
            future_best_satellite = await self._select_best_satellite(
                future_time, ue_location
            )

            logger.info(f"當前最佳衛星: {current_best_satellite['satellite_id']}")
            logger.info(f"預測最佳衛星: {future_best_satellite['satellite_id']}")

            # 第三步：判斷是否需要換手
            handover_required = (
                current_best_satellite["satellite_id"]
                != future_best_satellite["satellite_id"]
            )

            handover_trigger_time = None
            binary_search_result = None

            if handover_required:
                logger.info("檢測到換手需求，開始 Binary Search Refinement")
                # 第四步：Binary Search Refinement 計算精確換手時間 Tp
                handover_trigger_time, binary_search_result = (
                    await self._binary_search_refinement(
                        current_time,
                        future_time,
                        ue_location,
                        request.precision_threshold,
                    )
                )

            # 計算預測信賴水準
            prediction_confidence = await self._calculate_prediction_confidence(
                current_best_satellite, future_best_satellite, request.delta_t_seconds
            )

            # 構建響應
            response = HandoverPredictionResponse(
                prediction_id=prediction_id,
                ue_id=request.ue_id,
                handover_required=handover_required,
                current_best_satellite_id=current_best_satellite["satellite_id"],
                predicted_best_satellite_id=future_best_satellite["satellite_id"],
                handover_trigger_time=handover_trigger_time,
                prediction_confidence=prediction_confidence,
                delta_t_seconds=request.delta_t_seconds,
                precision_threshold=request.precision_threshold,
                binary_search_iterations=binary_search_result.iterations if binary_search_result else 0,
                binary_search_convergence_time=binary_search_result.convergence_time if binary_search_result else None,
                algorithm_version="INFOCOM2024_v1.0",
                prediction_timestamp=current_time,
            )

            logger.info(f"二點預測算法完成，預測 ID: {prediction_id}")
            return response

        except Exception as e:
            logger.error(f"二點預測算法執行失敗: {str(e)}")
            raise

    async def _select_best_satellite(
        self, timestamp: datetime, ue_location: GeoCoordinate
    ) -> Dict[str, Any]:
        """
        選擇指定時間和位置的最佳衛星

        Args:
            timestamp: 目標時間
            ue_location: UE 位置

        Returns:
            Dict: 最佳衛星信息
        """
        try:
            # 獲取所有可見衛星
            visible_satellites = await self.orbit_service.get_visible_satellites(
                timestamp, ue_location.latitude, ue_location.longitude
            )

            if not visible_satellites:
                raise ValueError("沒有可見的衛星")

            # 選擇最佳衛星（這裡簡化為選擇仰角最高的）
            best_satellite = max(visible_satellites, key=lambda s: s.get("elevation", 0))

            return {
                "satellite_id": best_satellite["satellite_id"],
                "elevation": best_satellite["elevation"],
                "azimuth": best_satellite["azimuth"],
                "distance": best_satellite["distance"],
                "snr": best_satellite.get("snr", 0),
                "timestamp": timestamp,
            }

        except Exception as e:
            logger.error(f"選擇最佳衛星失敗: {str(e)}")
            raise

    async def _binary_search_refinement(
        self,
        start_time: datetime,
        end_time: datetime,
        ue_location: GeoCoordinate,
        precision_threshold: float,
    ) -> Tuple[datetime, Any]:
        """
        二分搜索精化算法
        在 [start_time, end_time] 區間內精確定位換手時間點

        Args:
            start_time: 開始時間
            end_time: 結束時間
            ue_location: UE 位置
            precision_threshold: 精度閾值（秒）

        Returns:
            Tuple[datetime, BinarySearchResult]: 精確換手時間和搜索結果
        """
        logger.info("開始 Binary Search Refinement")

        iterations = []
        current_start = start_time
        current_end = end_time
        iteration_count = 0
        max_iterations = 20  # 防止無限循環

        # 獲取初始邊界的最佳衛星
        start_satellite = await self._select_best_satellite(current_start, ue_location)
        end_satellite = await self._select_best_satellite(current_end, ue_location)

        while (current_end - current_start).total_seconds() > precision_threshold:
            iteration_count += 1
            if iteration_count > max_iterations:
                logger.warning("二分搜索達到最大迭代次數")
                break

            # 計算中點時間
            mid_time = current_start + (current_end - current_start) / 2
            mid_satellite = await self._select_best_satellite(mid_time, ue_location)

            iteration = BinarySearchIteration(
                iteration_number=iteration_count,
                start_time=current_start,
                end_time=current_end,
                mid_time=mid_time,
                start_satellite_id=start_satellite["satellite_id"],
                end_satellite_id=end_satellite["satellite_id"],
                mid_satellite_id=mid_satellite["satellite_id"],
                interval_seconds=(current_end - current_start).total_seconds(),
            )
            iterations.append(iteration)

            # 判斷換手點在哪個區間
            if start_satellite["satellite_id"] == mid_satellite["satellite_id"]:
                # 換手點在右半區間
                current_start = mid_time
                start_satellite = mid_satellite
            else:
                # 換手點在左半區間
                current_end = mid_time
                end_satellite = mid_satellite

            logger.debug(
                f"迭代 {iteration_count}: 區間 [{current_start}, {current_end}], "
                f"長度 {(current_end - current_start).total_seconds():.2f}s"
            )

        # 返回精確的換手時間（取中點）
        precise_handover_time = current_start + (current_end - current_start) / 2

        # 創建搜索結果
        binary_search_result = type('BinarySearchResult', (), {
            'iterations': iterations,
            'convergence_time': precise_handover_time,
            'final_precision': (current_end - current_start).total_seconds(),
            'iteration_count': iteration_count
        })()

        logger.info(
            f"Binary Search 完成: 精確換手時間 {precise_handover_time}, "
            f"迭代次數 {iteration_count}, 最終精度 {(current_end - current_start).total_seconds():.3f}s"
        )

        return precise_handover_time, binary_search_result

    async def _calculate_prediction_confidence(
        self,
        current_satellite: Dict[str, Any],
        future_satellite: Dict[str, Any],
        delta_t_seconds: float,
    ) -> float:
        """
        計算預測信賴水準

        Args:
            current_satellite: 當前衛星信息
            future_satellite: 預測衛星信息
            delta_t_seconds: 預測時間間隔

        Returns:
            float: 信賴水準 (0-1)
        """
        try:
            # 基礎信賴度（根據衛星信號品質）
            current_snr = current_satellite.get("snr", 0)
            future_snr = future_satellite.get("snr", 0)
            base_confidence = (current_snr + future_snr) / 200.0  # 假設最大 SNR 為 100

            # 時間因子（預測時間越短，信賴度越高）
            time_factor = max(0.5, 1.0 - (delta_t_seconds / 300.0))  # 5分鐘衰減

            # 仰角因子（仰角越高，信賴度越高）
            current_elevation = current_satellite.get("elevation", 0)
            future_elevation = future_satellite.get("elevation", 0)
            elevation_factor = (current_elevation + future_elevation) / 180.0

            # 綜合信賴度
            confidence = min(1.0, (base_confidence + time_factor + elevation_factor) / 3.0)

            return round(confidence, 3)

        except Exception as e:
            logger.error(f"計算預測信賴水準失敗: {str(e)}")
            return 0.5  # 默認中等信賴度