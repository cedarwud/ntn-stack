#!/usr/bin/env python3
"""
跨階段數據流協議 - 標準化數據傳遞機制

定義階段間數據傳遞的標準協議：
1. 數據格式標準化
2. 階段依賴關係驗證
3. 數據完整性檢查
4. 禁止跨階段文件直讀

作者: Claude & Human
創建日期: 2025年
版本: v1.0 - 架構修正專用
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class StageDataSpec:
    """階段數據規格定義"""
    stage_number: int
    stage_name: str
    required_fields: List[str]
    optional_fields: List[str] = None
    data_types: Dict[str, type] = None

class DataFlowProtocol:
    """
    跨階段數據流協議管理器

    確保所有階段間的數據傳遞都遵循標準化協議：
    - Stage 1 → Stage 2: 軌道計算結果
    - Stage 2 → Stage 3: 可見性篩選結果
    - Stage 3 → Stage 4: 信號分析結果
    - Stage 4 → Stage 5: 時序預處理結果
    - Stage 5 → Stage 6: 數據整合結果
    """

    def __init__(self):
        """初始化數據流協議管理器"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # 定義每個階段的數據規格
        self.stage_specs = self._define_stage_specifications()

        self.logger.info("✅ 跨階段數據流協議管理器初始化")

    def _define_stage_specifications(self) -> Dict[int, StageDataSpec]:
        """定義每個階段的數據規格"""

        return {
            1: StageDataSpec(
                stage_number=1,
                stage_name="orbital_calculation",
                required_fields=[
                    "satellites_orbital_data",
                    "calculation_timestamp",
                    "total_satellites"
                ],
                optional_fields=["tle_epoch_info", "calculation_method"]
            ),

            2: StageDataSpec(
                stage_number=2,
                stage_name="visibility_filtering",
                required_fields=[
                    "visible_satellites",
                    "filtering_criteria",
                    "observer_location"
                ],
                optional_fields=["elevation_thresholds", "filtering_stats"]
            ),

            3: StageDataSpec(
                stage_number=3,
                stage_name="signal_analysis",
                required_fields=[
                    "signal_quality_analysis",
                    "satellite_signal_data",
                    "handover_decisions"
                ],
                optional_fields=["signal_events", "quality_thresholds"]
            ),

            4: StageDataSpec(
                stage_number=4,
                stage_name="timeseries_preprocessing",
                required_fields=[
                    "timeseries_data",
                    "rl_training_features",
                    "temporal_patterns"
                ],
                optional_fields=["signal_predictions", "trend_analysis"]
            ),

            5: StageDataSpec(
                stage_number=5,
                stage_name="data_integration",
                required_fields=[
                    "integrated_satellites",
                    "stage1_orbital_data",
                    "stage2_temporal_spatial_analysis",
                    "stage3_signal_analysis",
                    "stage4_rl_training_data"
                ],
                optional_fields=["integration_metadata", "quality_scores"]
            ),

            6: StageDataSpec(
                stage_number=6,
                stage_name="dynamic_pool_planning",
                required_fields=[
                    "final_dynamic_pool",
                    "optimization_results",
                    "coverage_validation"
                ],
                optional_fields=["pool_alternatives", "performance_metrics"]
            )
        }

    def validate_stage_input(self, stage_number: int, input_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        驗證階段輸入數據是否符合規格

        Args:
            stage_number: 階段編號
            input_data: 輸入數據

        Returns:
            Tuple[bool, List[str]]: (驗證通過, 錯誤訊息列表)
        """

        if stage_number not in self.stage_specs:
            return False, [f"未知的階段編號: {stage_number}"]

        spec = self.stage_specs[stage_number]
        errors = []

        # 檢查輸入數據是否為空
        if not input_data:
            errors.append(f"階段 {stage_number} 輸入數據不得為空")
            return False, errors

        # 檢查必要字段
        for field in spec.required_fields:
            if field not in input_data:
                errors.append(f"階段 {stage_number} 缺少必要字段: {field}")

        # 檢查數據完整性
        if 'metadata' not in input_data:
            errors.append(f"階段 {stage_number} 缺少 metadata 字段")

        # 檢查前階段數據完整性
        if stage_number > 1:
            prev_stage_validation = self._validate_previous_stage_data(stage_number, input_data)
            if not prev_stage_validation[0]:
                errors.extend(prev_stage_validation[1])

        validation_passed = len(errors) == 0

        if validation_passed:
            self.logger.info(f"✅ 階段 {stage_number} 輸入數據驗證通過")
        else:
            self.logger.warning(f"⚠️ 階段 {stage_number} 輸入數據驗證失敗: {errors}")

        return validation_passed, errors

    def validate_stage_output(self, stage_number: int, output_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        驗證階段輸出數據是否符合規格

        Args:
            stage_number: 階段編號
            output_data: 輸出數據

        Returns:
            Tuple[bool, List[str]]: (驗證通過, 錯誤訊息列表)
        """

        if stage_number not in self.stage_specs:
            return False, [f"未知的階段編號: {stage_number}"]

        spec = self.stage_specs[stage_number]
        errors = []

        # 檢查標準輸出格式
        required_output_fields = ['data', 'metadata', 'statistics', 'success', 'status']
        for field in required_output_fields:
            if field not in output_data:
                errors.append(f"階段 {stage_number} 輸出缺少標準字段: {field}")

        # 檢查 metadata 完整性
        if 'metadata' in output_data:
            metadata = output_data['metadata']
            required_metadata = ['stage_number', 'stage_name', 'processing_timestamp']
            for field in required_metadata:
                if field not in metadata:
                    errors.append(f"階段 {stage_number} metadata 缺少字段: {field}")

        # 檢查階段特定的輸出字段
        if 'data' in output_data:
            data = output_data['data']
            for field in spec.required_fields:
                if field not in data:
                    errors.append(f"階段 {stage_number} 輸出數據缺少字段: {field}")

        validation_passed = len(errors) == 0

        if validation_passed:
            self.logger.info(f"✅ 階段 {stage_number} 輸出數據驗證通過")
        else:
            self.logger.warning(f"⚠️ 階段 {stage_number} 輸出數據驗證失敗: {errors}")

        return validation_passed, errors

    def _validate_previous_stage_data(self, stage_number: int, input_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """驗證前階段數據的完整性"""

        errors = []
        previous_stage = stage_number - 1

        # 定義每個階段應該包含的前階段數據
        expected_previous_data = {
            2: ["stage1_orbital_data"],  # Stage 2 需要 Stage 1 的數據
            3: ["stage1_orbital_data", "stage2_visibility_data"],  # Stage 3 需要 Stage 1,2 的數據
            4: ["stage1_orbital_data", "stage2_visibility_data", "stage3_signal_data"],  # 以此類推
            5: ["stage1_orbital_data", "stage2_temporal_spatial_analysis",
                "stage3_signal_analysis", "stage4_rl_training_data"],
            6: ["stage1_orbital_data", "stage2_temporal_spatial_analysis",
                "stage3_signal_analysis", "stage4_rl_training_data", "integrated_satellites"]
        }

        if stage_number in expected_previous_data:
            for prev_data_key in expected_previous_data[stage_number]:
                if prev_data_key not in input_data:
                    errors.append(f"階段 {stage_number} 缺少前階段數據: {prev_data_key}")

        return len(errors) == 0, errors

    def create_stage_interface_adapter(self, stage_number: int) -> 'StageInterfaceAdapter':
        """
        創建階段接口適配器

        Args:
            stage_number: 階段編號

        Returns:
            StageInterfaceAdapter: 適配器實例
        """

        return StageInterfaceAdapter(stage_number, self)

    def get_stage_dependencies(self, stage_number: int) -> List[int]:
        """
        獲取階段依賴關係

        Args:
            stage_number: 階段編號

        Returns:
            List[int]: 依賴的階段列表
        """

        dependencies = {
            1: [],           # Stage 1 不依賴其他階段
            2: [1],          # Stage 2 依賴 Stage 1
            3: [1, 2],       # Stage 3 依賴 Stage 1, 2
            4: [1, 2, 3],    # Stage 4 依賴 Stage 1, 2, 3
            5: [1, 2, 3, 4], # Stage 5 依賴所有前階段
            6: [5]           # Stage 6 只依賴 Stage 5 的整合結果
        }

        return dependencies.get(stage_number, [])

class StageInterfaceAdapter:
    """階段接口適配器 - 為每個階段提供標準化的數據流操作"""

    def __init__(self, stage_number: int, protocol: DataFlowProtocol):
        """初始化適配器"""
        self.stage_number = stage_number
        self.protocol = protocol
        self.logger = logging.getLogger(f"{__name__}.StageInterfaceAdapter.Stage{stage_number}")

    def validate_and_process_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        驗證並處理輸入數據

        Args:
            input_data: 原始輸入數據

        Returns:
            Dict[str, Any]: 驗證後的數據

        Raises:
            ValueError: 當數據驗證失敗時
        """

        # 驗證輸入數據
        validation_passed, errors = self.protocol.validate_stage_input(self.stage_number, input_data)

        if not validation_passed:
            error_msg = f"階段 {self.stage_number} 輸入數據驗證失敗:\n" + "\n".join(f"  - {error}" for error in errors)
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        self.logger.info(f"✅ 階段 {self.stage_number} 輸入數據驗證通過")
        return input_data

    def validate_and_format_output(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        驗證並格式化輸出數據

        Args:
            output_data: 原始輸出數據

        Returns:
            Dict[str, Any]: 驗證後的標準化輸出

        Raises:
            ValueError: 當數據驗證失敗時
        """

        # 驗證輸出數據
        validation_passed, errors = self.protocol.validate_stage_output(self.stage_number, output_data)

        if not validation_passed:
            error_msg = f"階段 {self.stage_number} 輸出數據驗證失敗:\n" + "\n".join(f"  - {error}" for error in errors)
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        self.logger.info(f"✅ 階段 {self.stage_number} 輸出數據驗證通過")
        return output_data