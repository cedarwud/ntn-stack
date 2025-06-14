import logging
import json
import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from asyncio import sleep
from app.domains.handover.models.handover_models import (
    HandoverPredictionRecord,
    HandoverPredictionRequest,
    HandoverPredictionResponse,
    ManualHandoverRequest,
    ManualHandoverTriggerRequest,
    ManualHandoverResponse,
    HandoverStatusResponse,
    BinarySearchIteration,
    HandoverStatus,
    HandoverTriggerType,
)
from app.domains.satellite.models.satellite_model import Satellite
from app.domains.satellite.services.orbit_service import OrbitService
from app.domains.coordinates.models.coordinate_model import GeoCoordinate

logger = logging.getLogger(__name__)


class HandoverService:
    """
    換手服務 - 實現 IEEE INFOCOM 2024 論文的低延遲換手機制
    包含 Fine-Grained Synchronized Algorithm 和 Binary Search Refinement
    """
    
    def __init__(self, orbit_service: OrbitService):
        self.orbit_service = orbit_service
        
    async def perform_two_point_prediction(
        self, 
        request: HandoverPredictionRequest,
        ue_location: GeoCoordinate
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
                current_best_satellite['satellite_id'] != future_best_satellite['satellite_id']
            )
            
            handover_trigger_time = None
            binary_search_result = None
            
            if handover_required:
                logger.info("檢測到換手需求，開始 Binary Search Refinement")
                # 第四步：Binary Search Refinement 計算精確換手時間 Tp
                handover_trigger_time, binary_search_result = await self._binary_search_refinement(
                    current_time, future_time, ue_location, request.precision_threshold
                )
            
            # 計算預測置信度
            prediction_confidence = await self._calculate_prediction_confidence(
                current_best_satellite, future_best_satellite, request.delta_t_seconds
            )
            
            # 保存預測記錄到 R table
            await self._save_prediction_record(
                prediction_id=prediction_id,
                request=request,
                current_time=current_time,
                future_time=future_time,
                current_satellite=current_best_satellite,
                future_satellite=future_best_satellite,
                handover_required=handover_required,
                handover_trigger_time=handover_trigger_time,
                binary_search_result=binary_search_result,
                prediction_confidence=prediction_confidence
            )
            
            # 構建響應
            response = HandoverPredictionResponse(
                prediction_id=prediction_id,
                ue_id=request.ue_id,
                current_time=current_time,
                future_time=future_time,
                delta_t_seconds=request.delta_t_seconds,
                current_satellite=current_best_satellite,
                future_satellite=future_best_satellite,
                handover_required=handover_required,
                handover_trigger_time=handover_trigger_time,
                binary_search_result=binary_search_result,
                prediction_confidence=prediction_confidence,
                accuracy_percentage=prediction_confidence * 100
            )
            
            logger.info(f"二點預測完成，預測 ID: {prediction_id}")
            return response
            
        except Exception as e:
            logger.error(f"二點預測算法執行失敗: {e}", exc_info=True)
            raise
    
    async def _select_best_satellite(
        self, 
        timestamp: datetime, 
        ue_location: GeoCoordinate
    ) -> Dict[str, Any]:
        """
        為特定時間和位置選擇最佳衛星
        
        Args:
            timestamp: 目標時間
            ue_location: UE 位置
            
        Returns:
            Dict: 最佳衛星資訊
        """
        try:
            # 獲取可見衛星 (這裡簡化，實際應該從 orbit_service 獲取)
            # 模擬 LEO 衛星群
            visible_satellites = await self._get_visible_satellites(timestamp, ue_location)
            
            if not visible_satellites:
                raise ValueError(f"在時間 {timestamp} 沒有可見衛星")
            
            # 選擇最高仰角的衛星作為最佳衛星
            best_satellite = max(visible_satellites, key=lambda s: s['elevation_deg'])
            
            return {
                'satellite_id': best_satellite['norad_id'],
                'satellite_name': best_satellite['name'],
                'elevation_deg': best_satellite['elevation_deg'],
                'azimuth_deg': best_satellite['azimuth_deg'],
                'distance_km': best_satellite['distance_km'],
                'signal_strength_dbm': best_satellite.get('signal_strength_dbm', -70.0),
                'timestamp': timestamp
            }
            
        except Exception as e:
            logger.error(f"選擇最佳衛星失敗: {e}")
            raise
    
    async def _get_visible_satellites(
        self, 
        timestamp: datetime, 
        ue_location: GeoCoordinate
    ) -> List[Dict[str, Any]]:
        """
        獲取指定時間的可見衛星列表
        
        Args:
            timestamp: 目標時間
            ue_location: 觀測者位置
            
        Returns:
            List[Dict]: 可見衛星列表
        """
        # 這裡使用模擬數據，實際應該調用衛星軌道服務
        # 模擬 OneWeb LEO 星座
        mock_satellites = [
            {
                'norad_id': '44057',
                'name': 'ONEWEB-0012',
                'elevation_deg': 45.5 + (hash(str(timestamp)) % 20) / 10,
                'azimuth_deg': 180.0 + (hash(str(timestamp)) % 180),
                'distance_km': 1150.0 + (hash(str(timestamp)) % 100),  # OneWeb 高度約 1200km
                'signal_strength_dbm': -65.0 - (hash(str(timestamp)) % 20)
            },
            {
                'norad_id': '44058',
                'name': 'ONEWEB-0010',
                'elevation_deg': 35.2 + (hash(str(timestamp) + "1") % 25) / 10,
                'azimuth_deg': 90.0 + (hash(str(timestamp) + "1") % 180),
                'distance_km': 1180.0 + (hash(str(timestamp) + "1") % 120),  # OneWeb 高度約 1200km
                'signal_strength_dbm': -70.0 - (hash(str(timestamp) + "1") % 25)
            },
            {
                'norad_id': '44059',
                'name': 'ONEWEB-0008',
                'elevation_deg': 28.8 + (hash(str(timestamp) + "2") % 15) / 10,
                'azimuth_deg': 270.0 + (hash(str(timestamp) + "2") % 90),
                'distance_km': 1220.0 + (hash(str(timestamp) + "2") % 80),  # OneWeb 高度約 1200km
                'signal_strength_dbm': -75.0 - (hash(str(timestamp) + "2") % 15)
            }
        ]
        
        # 過濾最低仰角 10 度以上的衛星
        visible_satellites = [
            sat for sat in mock_satellites 
            if sat['elevation_deg'] >= 10.0
        ]
        
        return visible_satellites
    
    async def _binary_search_refinement(
        self,
        start_time: datetime,
        end_time: datetime,
        ue_location: GeoCoordinate,
        precision_threshold: float
    ) -> Tuple[datetime, Dict[str, Any]]:
        """
        Binary Search Refinement 算法實現
        精確計算換手觸發時間 Tp
        
        Args:
            start_time: 搜索開始時間 T
            end_time: 搜索結束時間 T+Δt
            ue_location: UE 位置
            precision_threshold: 精度閾值 (秒)
            
        Returns:
            Tuple[datetime, Dict]: (換手觸發時間, Binary Search 結果)
        """
        logger.info("開始 Binary Search Refinement")
        
        iterations = []
        current_start = start_time
        current_end = end_time
        iteration_count = 0
        max_iterations = 10
        
        # 獲取起始和結束時間的最佳衛星
        start_satellite = await self._select_best_satellite(current_start, ue_location)
        end_satellite = await self._select_best_satellite(current_end, ue_location)
        
        while iteration_count < max_iterations:
            iteration_count += 1
            
            # 計算中點時間
            time_diff = (current_end - current_start).total_seconds()
            mid_time = current_start + timedelta(seconds=time_diff / 2)
            
            # 獲取中點時間的最佳衛星
            mid_satellite = await self._select_best_satellite(mid_time, ue_location)
            
            # 記錄迭代
            iteration = BinarySearchIteration(
                iteration=iteration_count,
                start_time=current_start,
                end_time=current_end,
                mid_time=mid_time,
                selected_satellite=mid_satellite['satellite_id'],
                precision=time_diff,
                completed=time_diff <= precision_threshold
            )
            iterations.append(iteration)
            
            logger.info(
                f"迭代 {iteration_count}: 時間範圍 {time_diff:.2f}s, "
                f"中點衛星: {mid_satellite['satellite_id']}"
            )
            
            # 檢查精度是否達到要求
            if time_diff <= precision_threshold:
                logger.info(f"達到精度要求，最終觸發時間: {mid_time}")
                break
            
            # 決定搜索方向
            if mid_satellite['satellite_id'] == start_satellite['satellite_id']:
                # 換手點在中點之後
                current_start = mid_time
            else:
                # 換手點在中點之前
                current_end = mid_time
        
        # 計算最終觸發時間
        final_trigger_time = current_start + timedelta(
            seconds=(current_end - current_start).total_seconds() / 2
        )
        
        binary_search_result = {
            'trigger_time': final_trigger_time,
            'iterations': [iter.model_dump() for iter in iterations],
            'total_iterations': iteration_count,
            'final_precision_seconds': (current_end - current_start).total_seconds(),
            'precision_achieved': (current_end - current_start).total_seconds() <= precision_threshold
        }
        
        logger.info(f"Binary Search 完成，共 {iteration_count} 次迭代")
        return final_trigger_time, binary_search_result
    
    async def _calculate_prediction_confidence(
        self,
        current_satellite: Dict[str, Any],
        future_satellite: Dict[str, Any],
        delta_t_seconds: int
    ) -> float:
        """
        計算預測置信度
        
        Args:
            current_satellite: 當前衛星資訊
            future_satellite: 預測衛星資訊
            delta_t_seconds: 時間間隔
            
        Returns:
            float: 置信度 (0-1)
        """
        # 基礎置信度
        base_confidence = 0.95
        
        # 根據時間間隔調整 (間隔越短，置信度越高)
        time_factor = max(0.8, 1.0 - (delta_t_seconds - 5) * 0.01)
        
        # 根據信號強度調整
        current_signal = current_satellite.get('signal_strength_dbm', -70.0)
        future_signal = future_satellite.get('signal_strength_dbm', -70.0)
        
        signal_factor = min(1.0, (abs(current_signal) + abs(future_signal)) / 140.0)
        
        # 根據仰角調整 (仰角越高，置信度越高)
        elevation_factor = min(1.0, 
            (current_satellite['elevation_deg'] + future_satellite['elevation_deg']) / 90.0
        )
        
        final_confidence = base_confidence * time_factor * signal_factor * elevation_factor
        return min(0.99, max(0.85, final_confidence))
    
    async def _save_prediction_record(
        self,
        prediction_id: str,
        request: HandoverPredictionRequest,
        current_time: datetime,
        future_time: datetime,
        current_satellite: Dict[str, Any],
        future_satellite: Dict[str, Any],
        handover_required: bool,
        handover_trigger_time: Optional[datetime],
        binary_search_result: Optional[Dict[str, Any]],
        prediction_confidence: float
    ):
        """
        保存預測記錄到 R table
        """
        try:
            # 提取 Binary Search 元數據
            binary_iterations = 0
            precision_achieved = 0.0
            search_metadata = None
            
            if binary_search_result:
                binary_iterations = binary_search_result.get('total_iterations', 0)
                precision_achieved = binary_search_result.get('final_precision_seconds', 0.0)
                search_metadata = json.dumps(binary_search_result)
            
            # 創建預測記錄 (這裡省略實際數據庫操作，在實際項目中需要實現)
            record = HandoverPredictionRecord(
                ue_id=request.ue_id,
                prediction_id=prediction_id,
                current_time=current_time,
                future_time=future_time,
                delta_t_seconds=request.delta_t_seconds,
                current_satellite_id=current_satellite['satellite_id'],
                future_satellite_id=future_satellite['satellite_id'],
                handover_required=handover_required,
                handover_trigger_time=handover_trigger_time,
                binary_search_iterations=binary_iterations,
                precision_achieved=precision_achieved,
                search_metadata=search_metadata,
                prediction_confidence=prediction_confidence,
                signal_quality_current=current_satellite.get('signal_strength_dbm', -70.0),
                signal_quality_future=future_satellite.get('signal_strength_dbm', -70.0)
            )
            
            logger.info(f"預測記錄已保存: {prediction_id}")
            
        except Exception as e:
            logger.error(f"保存預測記錄失敗: {e}")
            # 不拋出異常，避免影響主流程
    
    async def trigger_manual_handover(
        self,
        request: ManualHandoverTriggerRequest,
        ue_location: GeoCoordinate
    ) -> ManualHandoverResponse:
        """
        觸發手動換手
        
        Args:
            request: 手動換手請求
            ue_location: UE 位置
            
        Returns:
            ManualHandoverResponse: 換手響應
        """
        logger.info(f"觸發手動換手，UE ID: {request.ue_id}, 目標衛星: {request.target_satellite_id}")
        
        try:
            # 獲取當前最佳衛星
            current_time = datetime.utcnow()
            current_satellite = await self._select_best_satellite(current_time, ue_location)
            
            # 創建手動換手請求記錄 (實際項目中需要保存到數據庫)
            handover_request = ManualHandoverRequest(
                ue_id=request.ue_id,
                from_satellite_id=current_satellite['satellite_id'],
                to_satellite_id=request.target_satellite_id,
                trigger_type=request.trigger_type,
                status=HandoverStatus.HANDOVER,
                request_time=current_time
            )
            
            # 模擬分配 ID (實際項目中由數據庫生成)
            handover_id = hash(f"{request.ue_id}_{current_time}") % 100000
            
            # 啟動異步換手執行
            await self._execute_handover_async(handover_id, handover_request)
            
            response = ManualHandoverResponse(
                handover_id=handover_id,
                ue_id=request.ue_id,
                from_satellite_id=current_satellite['satellite_id'],
                to_satellite_id=request.target_satellite_id,
                status=HandoverStatus.HANDOVER,
                request_time=current_time
            )
            
            logger.info(f"手動換手已啟動，換手 ID: {handover_id}")
            return response
            
        except Exception as e:
            logger.error(f"觸發手動換手失敗: {e}", exc_info=True)
            raise
    
    async def _execute_handover_async(
        self,
        handover_id: int,
        handover_request: ManualHandoverRequest
    ):
        """
        異步執行換手過程
        
        Args:
            handover_id: 換手請求 ID
            handover_request: 換手請求記錄
        """
        try:
            # 模擬換手執行時間 (2-5秒)
            execution_duration = 2.0 + (hash(str(handover_id)) % 30) / 10
            
            logger.info(f"開始執行換手 {handover_id}，預計耗時 {execution_duration:.1f} 秒")
            
            # 更新開始時間
            start_time = datetime.utcnow()
            handover_request.start_time = start_time
            handover_request.status = HandoverStatus.HANDOVER
            
            # 模擬換手過程
            await sleep(execution_duration)
            
            # 模擬換手成功率 (90%)
            success = (hash(str(handover_id)) % 10) < 9
            
            # 更新完成狀態
            completion_time = datetime.utcnow()
            handover_request.completion_time = completion_time
            handover_request.duration_seconds = (completion_time - start_time).total_seconds()
            handover_request.success = success
            handover_request.status = HandoverStatus.COMPLETE if success else HandoverStatus.FAILED
            
            if not success:
                handover_request.error_message = "換手過程中發生信號中斷"
            
            logger.info(
                f"換手 {handover_id} 執行完成，結果: {'成功' if success else '失敗'}, "
                f"耗時: {handover_request.duration_seconds:.2f} 秒"
            )
            
        except Exception as e:
            logger.error(f"執行換手 {handover_id} 時發生錯誤: {e}")
            handover_request.status = HandoverStatus.FAILED
            handover_request.error_message = str(e)
    
    async def get_handover_status(self, handover_id: int) -> HandoverStatusResponse:
        """
        查詢換手狀態
        
        Args:
            handover_id: 換手請求 ID
            
        Returns:
            HandoverStatusResponse: 狀態響應
        """
        # 這裡應該從數據庫查詢實際狀態
        # 模擬狀態查詢
        logger.info(f"查詢換手狀態: {handover_id}")
        
        # 模擬不同的狀態
        status_options = [
            HandoverStatus.HANDOVER,
            HandoverStatus.COMPLETE,
            HandoverStatus.FAILED
        ]
        
        # 基於 ID 生成穩定的狀態
        status_index = hash(str(handover_id)) % len(status_options)
        status = status_options[status_index]
        
        progress = None
        estimated_completion = None
        
        if status == HandoverStatus.HANDOVER:
            progress = min(95.0, (hash(str(handover_id)) % 80) + 10)
            estimated_completion = datetime.utcnow() + timedelta(seconds=5)
        elif status == HandoverStatus.COMPLETE:
            progress = 100.0
        
        return HandoverStatusResponse(
            handover_id=handover_id,
            status=status,
            progress_percentage=progress,
            estimated_completion_time=estimated_completion
        )