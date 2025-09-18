from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime, timezone
import logging
import json
import asyncio
import os

class BaseStageProcessor(ABC):
    """所有階段處理器的基礎抽象類"""
    
    def __init__(self, stage_number: int, stage_name: str, config: Optional[Dict] = None):
        """
        初始化基礎處理器
        
        Args:
            stage_number: 階段編號 (1-6)
            stage_name: 階段名稱
            config: 配置參數
        """
        self.stage_number = stage_number
        self.stage_name = stage_name
        self.config = config or {}
        
        # 處理時間追蹤
        self.processing_start_time: Optional[datetime] = None
        self.processing_end_time: Optional[datetime] = None
        self.processing_duration: float = 0.0
        
        # 統一日誌
        self.logger = logging.getLogger(f"stage{stage_number}_{stage_name}")
        
        # 🚨 重要：強制容器內執行 - 統一執行環境
        # 架構決策：只支援容器執行，避免路徑和環境不一致問題
        if not Path("/satellite-processing").exists():
            raise RuntimeError(
                "🚫 satellite-processing-system 必須在容器內執行！\n"
                "正確執行方式：\n"
                "  docker exec satellite-dev bash\n"
                "  cd /satellite-processing && python scripts/run_six_stages_with_validation.py\n"
                "\n"
                "原因：\n"
                "- 確保執行環境一致性\n"
                "- 避免路徑混亂和數據分散\n"
                "- 簡化維護和除錯複雜度"
            )
        
        # 容器環境 - 統一執行路徑（與Volume映射一致）
        self.output_dir = Path(f"/satellite-processing/data/outputs/stage{stage_number}")
        # 🎯 用戶要求：驗證快照輸出到 NetStack 目錄
        self.validation_dir = Path("/netstack/src/services/satellite/data/validation_snapshots")
        self.logger.info(f"🐳 容器執行確認 - 輸出路徑: {self.output_dir}")
        self.logger.info(f"📂 Volume映射: 容器{self.output_dir} → 主機./data/outputs/stage{stage_number}")
        
        self._initialize_directories()
        self._load_configuration()
    
    def _initialize_directories(self) -> None:
        """初始化輸出目錄"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.validation_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_configuration(self) -> None:
        """載入配置參數"""
        # 從配置文件或環境變量載入參數
        pass
    
    # ===== 核心處理流程方法 =====
    
    @abstractmethod
    def validate_input(self, input_data: Any) -> bool:
        """
        驗證輸入數據的有效性
        
        Args:
            input_data: 輸入數據
            
        Returns:
            bool: 驗證是否通過
            
        Raises:
            ValidationError: 輸入數據無效
        """
        pass
    
    @abstractmethod
    def process(self, input_data: Any) -> Dict[str, Any]:
        """
        執行階段的核心處理邏輯
        
        Args:
            input_data: 輸入數據
            
        Returns:
            Dict[str, Any]: 處理結果，包含 data 和 metadata
            
        Raises:
            ProcessingError: 處理過程中發生錯誤
        """
        pass
    
    @abstractmethod
    def validate_output(self, output_data: Dict[str, Any]) -> bool:
        """
        驗證輸出數據的有效性
        
        Args:
            output_data: 輸出數據
            
        Returns:
            bool: 驗證是否通過
            
        Raises:
            ValidationError: 輸出數據無效
        """
        pass
    
    @abstractmethod
    def save_results(self, results: Dict[str, Any]) -> str:
        """
        保存處理結果到文件
        
        Args:
            results: 處理結果
            
        Returns:
            str: 保存的文件路徑
            
        Raises:
            IOError: 文件保存失敗
        """
        pass
    
    # ===== 統一的執行流程 =====
    
    def execute(self, input_data: Any = None) -> Dict[str, Any]:
        """
        執行完整的階段處理流程 (含TDD整合自動化 Phase 5.0)
        
        Args:
            input_data: 輸入數據
            
        Returns:
            Dict[str, Any]: 處理結果
        """
        self.logger.info(f"開始執行 Stage {self.stage_number}: {self.stage_name}")

        try:
            # 0. 🚨 自動清理舊輸出 - 確保每次執行都從乾淨狀態開始
            self.logger.info("🧹 執行階段前自動清理...")
            self.cleanup_previous_output()

            # 1. 開始計時
            self.start_processing_timer()

            # 2. 載入輸入數據（如果未提供）
            if input_data is None:
                input_data = self.load_input_data()
            
            # 3. 驗證輸入
            if not self.validate_input(input_data):
                raise ValueError("輸入數據驗證失敗")
            
            # 4. 執行處理
            results = self.process(input_data)
            
            # 5. 驗證輸出
            if not self.validate_output(results):
                raise ValueError("輸出數據驗證失敗")
            
            # 6. 保存結果
            output_path = self.save_results(results)
            results['metadata']['output_file'] = output_path
            
            # 7. 結束計時
            self.end_processing_timer()
            results['metadata']['processing_duration'] = self.processing_duration
            
            # 8. 生成驗證快照 (原有)
            snapshot_success = self.save_validation_snapshot(results)
            
            # 9. 🆕 後置鉤子：自動觸發TDD整合測試 (Phase 5.0)
            if snapshot_success:
                enhanced_snapshot = self._trigger_tdd_integration_if_enabled(results)
                if enhanced_snapshot:
                    # 更新驗證快照包含TDD結果
                    self._update_validation_snapshot_with_tdd(enhanced_snapshot)
            
            self.logger.info(f"Stage {self.stage_number} 執行完成，耗時 {self.processing_duration:.2f}秒")
            return results
            
        except Exception as e:
            self.logger.error(f"Stage {self.stage_number} 執行失敗: {e}")
            self.end_processing_timer()
            raise
    
    # ===== 時間管理 =====
    
    def start_processing_timer(self) -> None:
        """開始處理計時"""
        self.processing_start_time = datetime.now(timezone.utc)
    
    def end_processing_timer(self) -> None:
        """結束處理計時"""
        self.processing_end_time = datetime.now(timezone.utc)
        if self.processing_start_time:
            self.processing_duration = (
                self.processing_end_time - self.processing_start_time
            ).total_seconds()
    
    # ===== 數據載入和保存 =====
    
    def load_input_data(self) -> Any:
        """
        載入輸入數據（從前一階段的輸出）
        
        Returns:
            Any: 輸入數據
        """
        if self.stage_number == 1:
            # Stage 1 沒有前置依賴，直接載入原始數據
            return None
        
        # 其他階段從前一階段載入數據
        prev_stage_output = self.output_dir.parent / f"stage{self.stage_number-1}_outputs"
        # 實施載入邏輯
        pass
    
    def save_validation_snapshot(self, results: Dict[str, Any]) -> bool:
        """
        保存驗證快照
        
        Args:
            results: 處理結果
            
        Returns:
            bool: 保存是否成功
        """
        try:
            snapshot = {
                "stage": self.stage_number,
                "stageName": self.stage_name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "completed",
                "duration_seconds": round(self.processing_duration, 2),
                "keyMetrics": self.extract_key_metrics(results),
                "validation": self.run_validation_checks(results),
                "systemInfo": {
                    "processor_version": "2.0.0",
                    "validation_framework": "unified_pipeline_v2"
                }
            }
            
            # 使用自定義JSON編碼器處理datetime和numpy類型
            import numpy as np
            from decimal import Decimal
            
            class SafeJSONEncoder(json.JSONEncoder):
                def default(self, obj):
                    if isinstance(obj, datetime):
                        return obj.isoformat()
                    elif isinstance(obj, bool):  # Handle Python bool first
                        return str(obj).lower()  # True -> "true", False -> "false"
                    elif isinstance(obj, np.bool_):
                        return str(bool(obj)).lower()  # Convert numpy bool -> Python bool -> string
                    elif isinstance(obj, (np.integer, np.int64, np.int32)):
                        return int(obj)
                    elif isinstance(obj, (np.floating, np.float64, np.float32)):
                        return float(obj)
                    elif isinstance(obj, Decimal):
                        return float(obj)
                    elif isinstance(obj, (set, frozenset)):
                        return list(obj)
                    elif hasattr(obj, 'item'):
                        return obj.item()
                    elif hasattr(obj, 'tolist'):
                        return obj.tolist()
                    return super().default(obj)
            
            snapshot_file = self.validation_dir / f"stage{self.stage_number}_validation.json"
            with open(snapshot_file, 'w', encoding='utf-8') as f:
                json.dump(snapshot, f, cls=SafeJSONEncoder, ensure_ascii=False, indent=2)
            
            self.logger.info(f"驗證快照已保存: {snapshot_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存驗證快照失敗: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    # ===== 抽象方法 - 子類必須實施 =====
    
    @abstractmethod
    def extract_key_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取關鍵指標
        
        Args:
            results: 處理結果
            
        Returns:
            Dict[str, Any]: 關鍵指標
        """
        pass
    
    @abstractmethod
    def run_validation_checks(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行驗證檢查
        
        Args:
            results: 處理結果
            
        Returns:
            Dict[str, Any]: 驗證結果
        """
        pass
    
    # ===== 可選覆寫方法 =====
    
    def cleanup_previous_output(self) -> None:
        """
        完全清理整個階段的輸出資料夾和對應的驗證快照
        
        🎯 策略：完全移除整個 stageX 資料夾再重新創建，確保徹底清理
        """
        cleaned_items = 0
        
        # 1. 🗑️ 完全移除整個階段輸出資料夾 (例如: data/outputs/stage1)
        if self.output_dir.exists():
            import shutil
            shutil.rmtree(self.output_dir)
            cleaned_items += 1
            self.logger.info(f"🗑️ 已完全移除整個階段資料夾: {self.output_dir}")
        
        # 2. 🗑️ 同步清理對應的驗證快照文件
        validation_file = self.validation_dir / f"stage{self.stage_number}_validation.json"
        if validation_file.exists():
            validation_file.unlink()
            cleaned_items += 1
            self.logger.info(f"🗑️ 已同步清理驗證快照: {validation_file}")
        
        # 3. 📁 重新創建乾淨的階段資料夾結構
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.validation_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"📁 已重新創建乾淨的階段資料夾: {self.output_dir}")
        
        # 4. 記錄清理統計
        if cleaned_items > 0:
            self.logger.info(f"✅ Stage {self.stage_number} 完全清理完成: 移除整個階段資料夾並重建")
        else:
            self.logger.info(f"ℹ️ Stage {self.stage_number} 無需清理 (階段資料夾不存在)")
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """
        獲取處理統計信息
        
        Returns:
            Dict[str, Any]: 統計信息
        """
        return {
            "stage_number": self.stage_number,
            "stage_name": self.stage_name,
            "processing_duration": self.processing_duration,
            "start_time": self.processing_start_time.isoformat() if self.processing_start_time else None,
            "end_time": self.processing_end_time.isoformat() if self.processing_end_time else None,
        }

    # ===== TDD整合自動化方法 (Phase 5.0) =====
    
    def _trigger_tdd_integration_if_enabled(self, stage_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        觸發TDD整合測試（如果啟用）- 修復版本
        
        Args:
            stage_results: 階段處理結果
            
        Returns:
            Optional[Dict[str, Any]]: 增強的驗證快照，如果TDD被禁用則返回None
        """
        try:
            # 動態導入TDD整合協調器，避免循環導入
            from .tdd_integration_coordinator import get_tdd_coordinator
            
            coordinator = get_tdd_coordinator()
            
            # 檢查TDD是否啟用
            if not coordinator.config_manager.is_enabled(f"stage{self.stage_number}"):
                self.logger.info(f"Stage {self.stage_number} TDD整合已禁用，跳過")
                return None
            
            # 讀取當前驗證快照
            original_snapshot = self._load_current_validation_snapshot()
            if not original_snapshot:
                self.logger.warning("無法載入驗證快照，TDD整合跳過")
                return None
            
            # 獲取執行環境
            environment = self._detect_execution_environment()
            
            # 異步執行TDD測試
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                tdd_results = loop.run_until_complete(
                    coordinator.execute_post_hook_tests(
                        f"stage{self.stage_number}",
                        stage_results,
                        original_snapshot,
                        environment
                    )
                )
                
                # 增強驗證快照
                enhanced_snapshot = coordinator.enhance_validation_snapshot(
                    original_snapshot, tdd_results
                )
                
                # 🔧 修復：只有在有嚴重問題且失敗處理設為"error"時才停止
                if tdd_results.critical_issues:
                    stage_config = coordinator.config_manager.get_stage_config(f"stage{self.stage_number}")
                    failure_handling = stage_config.get("failure_handling", "warning")
                    
                    if failure_handling == "error":
                        failure_action = coordinator.handle_test_failures(
                            tdd_results, {"stage": self.stage_number}
                        )
                        self._handle_tdd_failure_action(failure_action)
                    else:
                        # 記錄警告但不停止執行
                        self.logger.warning(
                            f"TDD測試發現 {len(tdd_results.critical_issues)} 個問題，"
                            f"但失敗處理設為 '{failure_handling}'，繼續執行"
                        )
                
                self.logger.info(
                    f"TDD整合完成 - Stage {self.stage_number}, "
                    f"品質分數: {tdd_results.overall_quality_score:.2f}, "
                    f"執行時間: {tdd_results.total_execution_time_ms}ms"
                )
                
                return enhanced_snapshot
                
            finally:
                loop.close()
                
        except Exception as e:
            self.logger.error(f"TDD整合執行失敗: {e}")
            # TDD整合失敗不應該影響主要處理流程
            return None
    
    def _load_current_validation_snapshot(self) -> Optional[Dict[str, Any]]:
        """載入當前階段的驗證快照"""
        try:
            snapshot_file = self.validation_dir / f"stage{self.stage_number}_validation.json"
            if snapshot_file.exists():
                with open(snapshot_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"載入驗證快照失敗: {e}")
        
        return None
    
    def _detect_execution_environment(self) -> str:
        """檢測當前執行環境"""
        # 檢測環境變數
        env = os.getenv('TDD_ENVIRONMENT', '').lower()
        if env in ['development', 'testing', 'production']:
            return env
        
        # 檢測Docker環境
        if Path('/.dockerenv').exists():
            return 'production'
        
        # 檢測開發環境標誌
        if os.getenv('DEBUG') == '1' or os.getenv('DEVELOPMENT') == '1':
            return 'development'
        
        # 預設為開發環境
        return 'development'
    
    def _update_validation_snapshot_with_tdd(self, enhanced_snapshot: Dict[str, Any]) -> None:
        """更新驗證快照包含TDD結果"""
        try:
            snapshot_file = self.validation_dir / f"stage{self.stage_number}_validation.json"
            with open(snapshot_file, 'w', encoding='utf-8') as f:
                json.dump(enhanced_snapshot, f, cls=SafeJSONEncoder, ensure_ascii=False, indent=2)
            
            self.logger.info(f"驗證快照已更新包含TDD結果: {snapshot_file}")
            
        except Exception as e:
            self.logger.error(f"更新TDD驗證快照失敗: {e}")
    
    def _handle_tdd_failure_action(self, failure_action: Dict[str, Any]) -> None:
        """處理TDD失敗動作"""
        action = failure_action.get('action', 'continue')
        reason = failure_action.get('reason', '')
        suggestions = failure_action.get('recovery_suggestions', [])
        
        if action == 'stop_pipeline':
            self.logger.error(f"TDD關鍵失敗，停止管道執行: {reason}")
            for suggestion in suggestions:
                self.logger.error(f"  建議: {suggestion}")
            
            # 根據配置決定是否真正停止
            # 在開發環境可能只記錄警告，在生產環境則停止
            environment = self._detect_execution_environment()
            if environment == 'production':
                raise RuntimeError(f"TDD關鍵失敗: {reason}")
        
        elif action == 'continue_with_warning':
            self.logger.warning(f"TDD警告: {reason}")
            for suggestion in suggestions:
                self.logger.warning(f"  建議: {suggestion}")
        
        else:  # continue
            self.logger.info(f"TDD輕微問題: {reason}")
    
    def is_tdd_integration_enabled(self) -> bool:
        """檢查當前階段是否啟用TDD整合"""
        try:
            from .tdd_integration_coordinator import get_tdd_coordinator
            coordinator = get_tdd_coordinator()
            return coordinator.config_manager.is_enabled(f"stage{self.stage_number}")
        except Exception:
            return False
    
    def get_tdd_integration_status(self) -> Dict[str, Any]:
        """獲取TDD整合狀態資訊"""
        try:
            from .tdd_integration_coordinator import get_tdd_coordinator
            coordinator = get_tdd_coordinator()
            
            stage_config = coordinator.config_manager.get_stage_config(f"stage{self.stage_number}")
            environment = self._detect_execution_environment()
            execution_mode = coordinator.config_manager.get_execution_mode(environment)
            
            return {
                'enabled': coordinator.config_manager.is_enabled(f"stage{self.stage_number}"),
                'environment': environment,
                'execution_mode': execution_mode.value,
                'enabled_tests': stage_config.get('tests', []),
                'timeout': stage_config.get('timeout', 30),
                'async_execution': stage_config.get('async_execution', False)
            }
        except Exception as e:
            return {
                'enabled': False,
                'error': str(e)
            }
