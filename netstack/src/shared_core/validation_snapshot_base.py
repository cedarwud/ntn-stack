#!/usr/bin/env python3
"""
驗證快照基礎類
============================
為六階段數據預處理系統提供統一的驗證和快照機制

Author: NTN Stack Team  
Version: 1.0.0
Date: 2025-09-04
"""

import os
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger(__name__)


class ValidationSnapshotBase(ABC):
    """
    驗證快照基礎類
    
    為每個階段處理器提供統一的驗證快照功能：
    1. 驗證檢查執行
    2. 快照生成和保存
    3. 指標統計和分析
    """
    
    def __init__(self, stage_number: int, stage_name: str, snapshot_dir: str = "/app/data/validation_snapshots"):
        """
        初始化驗證快照基礎
        
        Args:
            stage_number: 階段編號 (1-6)
            stage_name: 階段名稱
            snapshot_dir: 快照保存目錄
        """
        self.stage_number = stage_number
        self.stage_name = stage_name
        
        # 智能選擇數據目錄
        if snapshot_dir.startswith("/app/") and not os.path.exists("/app"):
            # 容器外執行時，使用本地目錄
            base_dir = "/home/sat/ntn-stack/netstack/data"
            snapshot_dir = os.path.join(base_dir, "validation_snapshots")
        
        self.snapshot_dir = Path(snapshot_dir)
        self.snapshot_file = self.snapshot_dir / f"stage{stage_number}_validation.json"
        
        # 確保快照目錄存在
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        # 處理時間追蹤
        self.processing_start_time = None
        self.processing_end_time = None
        self.processing_duration = 0.0
        
        logger.info(f"✅ 初始化 Stage {stage_number} 驗證快照系統: {stage_name}")
    
    def start_processing_timer(self):
        """開始處理計時"""
        self.processing_start_time = datetime.now(timezone.utc)
    
    def end_processing_timer(self):
        """結束處理計時"""
        self.processing_end_time = datetime.now(timezone.utc)
        if self.processing_start_time:
            self.processing_duration = (self.processing_end_time - self.processing_start_time).total_seconds()
    
    @abstractmethod
    def extract_key_metrics(self, processing_results: Dict[str, Any]) -> Dict[str, Union[str, int, float]]:
        """
        提取關鍵指標
        
        Args:
            processing_results: 處理結果數據
            
        Returns:
            關鍵指標字典
        """
        pass
    
    @abstractmethod
    def run_validation_checks(self, processing_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行驗證檢查
        
        Args:
            processing_results: 處理結果數據
            
        Returns:
            驗證結果字典
        """
        pass
    
    def get_next_stage_info(self, expected_input: int) -> Dict[str, Any]:
        """
        獲取下一階段信息
        
        Args:
            expected_input: 預期輸入數量
            
        Returns:
            下一階段信息
        """
        if self.stage_number >= 6:
            return {
                "ready": True,
                "stage": "completed",
                "expectedInput": expected_input,
                "note": "管線處理完成"
            }
        else:
            return {
                "ready": True,
                "stage": self.stage_number + 1,
                "expectedInput": expected_input
            }
    
    def save_validation_snapshot(self, processing_results: Dict[str, Any]) -> bool:
        """
        保存驗證快照
        
        Args:
            processing_results: 處理結果數據
            
        Returns:
            保存是否成功
        """
        try:
            # 結束計時
            if not self.processing_end_time:
                self.end_processing_timer()
            
            # 執行驗證檢查
            validation_results = self.run_validation_checks(processing_results)
            key_metrics = self.extract_key_metrics(processing_results)
            
            # 構建快照數據
            snapshot = {
                "stage": self.stage_number,
                "stageName": self.stage_name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "completed" if validation_results.get("passed", False) else "failed",
                "duration_seconds": round(self.processing_duration, 2),
                "keyMetrics": key_metrics,
                "validation": validation_results,
                "performanceMetrics": {
                    "processingTime": f"{self.processing_duration:.2f}秒",
                    "startTime": self.processing_start_time.isoformat() if self.processing_start_time else None,
                    "endTime": self.processing_end_time.isoformat() if self.processing_end_time else None
                },
                "nextStage": self.get_next_stage_info(
                    processing_results.get("metadata", {}).get("total_satellites", 0)
                ),
                "systemInfo": {
                    "processor_version": "1.0.0",
                    "validation_framework": "validation_snapshot_base",
                    "snapshot_file": str(self.snapshot_file)
                }
            }
            
            # 保存快照檔案 - 使用自定義編碼器處理numpy類型
            import numpy as np
            
            class SafeJSONEncoder(json.JSONEncoder):
                def default(self, obj):
                    if isinstance(obj, np.bool_):
                        return bool(obj)
                    elif isinstance(obj, (np.integer, np.int64, np.int32)):
                        return int(obj)
                    elif isinstance(obj, (np.floating, np.float64, np.float32)):
                        return float(obj)
                    elif hasattr(obj, 'item'):
                        return obj.item()
                    return super().default(obj)
            
            with open(self.snapshot_file, 'w', encoding='utf-8') as f:
                json.dump(snapshot, f, cls=SafeJSONEncoder, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Stage {self.stage_number} 驗證快照已保存: {self.snapshot_file}")
            logger.info(f"   驗證狀態: {'通過' if validation_results.get('passed', False) else '失敗'}")
            logger.info(f"   處理時間: {self.processing_duration:.2f}秒")
            logger.info(f"   關鍵指標: {len(key_metrics)} 項")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Stage {self.stage_number} 驗證快照保存失敗: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def load_validation_snapshot(self) -> Optional[Dict[str, Any]]:
        """
        載入驗證快照
        
        Returns:
            快照數據，如果不存在則返回 None
        """
        try:
            if self.snapshot_file.exists():
                with open(self.snapshot_file, 'r', encoding='utf-8') as f:
                    snapshot = json.load(f)
                logger.info(f"📊 載入 Stage {self.stage_number} 驗證快照成功")
                return snapshot
            else:
                logger.warning(f"⚠️ Stage {self.stage_number} 驗證快照不存在: {self.snapshot_file}")
                return None
        except Exception as e:
            logger.error(f"❌ 載入 Stage {self.stage_number} 驗證快照失敗: {e}")
            return None
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """
        獲取驗證摘要
        
        Returns:
            驗證摘要信息
        """
        snapshot = self.load_validation_snapshot()
        if snapshot:
            return {
                "stage": self.stage_number,
                "status": snapshot.get("status", "unknown"),
                "passed": snapshot.get("validation", {}).get("passed", False),
                "timestamp": snapshot.get("timestamp"),
                "duration": snapshot.get("duration_seconds"),
                "checks_passed": snapshot.get("validation", {}).get("passedChecks", 0),
                "checks_total": snapshot.get("validation", {}).get("totalChecks", 0)
            }
        else:
            return {
                "stage": self.stage_number,
                "status": "not_executed", 
                "passed": False,
                "timestamp": None,
                "duration": 0,
                "checks_passed": 0,
                "checks_total": 0
            }
    
    @staticmethod
    def get_pipeline_validation_summary() -> Dict[str, Any]:
        """
        獲取整個管線的驗證摘要
        
        Returns:
            管線驗證摘要
        """
        # 智能選擇快照目錄
        if not os.path.exists("/app"):
            # 容器外執行時，使用本地目錄
            snapshot_dir = Path("/home/sat/ntn-stack/netstack/data/validation_snapshots")
        else:
            snapshot_dir = Path("/app/data/validation_snapshots")
        stages = []
        
        for stage_num in range(1, 7):
            snapshot_file = snapshot_dir / f"stage{stage_num}_validation.json"
            if snapshot_file.exists():
                try:
                    with open(snapshot_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    stages.append({
                        "stage": stage_num,
                        "status": data.get("status", "unknown"),
                        "passed": data.get("validation", {}).get("passed", False),
                        "timestamp": data.get("timestamp"),
                        "checks_passed": data.get("validation", {}).get("passedChecks", 0),
                        "checks_total": data.get("validation", {}).get("totalChecks", 0)
                    })
                except Exception as e:
                    logger.error(f"❌ 讀取 Stage {stage_num} 快照失敗: {e}")
                    stages.append({
                        "stage": stage_num,
                        "status": "error",
                        "passed": False,
                        "timestamp": None,
                        "checks_passed": 0,
                        "checks_total": 0
                    })
            else:
                stages.append({
                    "stage": stage_num,
                    "status": "not_executed",
                    "passed": False,
                    "timestamp": None,
                    "checks_passed": 0,
                    "checks_total": 0
                })
        
        # 計算管線健康度
        executed_stages = [s for s in stages if s["status"] not in ["not_executed", "error"]]
        successful_stages = [s for s in executed_stages if s["passed"]]
        
        pipeline_health = "healthy"
        if len(executed_stages) == 0:
            pipeline_health = "not_started"
        elif len(successful_stages) < len(executed_stages):
            pipeline_health = "degraded"
        elif len(executed_stages) < 6:
            pipeline_health = "partial"
        
        return {
            "metadata": {
                "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                "analyzer_version": "validation_snapshot_base_v1.0.0"
            },
            "stages": stages,
            "summary": {
                "total_stages": 6,
                "executed_stages": len(executed_stages),
                "successful_stages": len(successful_stages),
                "failed_stages": len(executed_stages) - len(successful_stages),
                "not_executed_stages": 6 - len(executed_stages),
                "pipeline_health": pipeline_health,
                "success_rate": len(successful_stages) / max(len(executed_stages), 1) * 100
            }
        }


class ValidationCheckHelper:
    """驗證檢查輔助工具類"""
    
    @staticmethod
    def check_satellite_count(actual: int, expected_min: int, expected_max: int = None) -> bool:
        """檢查衛星數量是否在預期範圍內"""
        if expected_max:
            return expected_min <= actual <= expected_max
        return actual >= expected_min
    
    @staticmethod
    def check_constellation_presence(constellations: List[str], required: List[str]) -> bool:
        """檢查必需的星座是否存在"""
        return all(req in constellations for req in required)
    
    @staticmethod
    def check_data_completeness(data: Dict[str, Any], required_fields: List[str]) -> bool:
        """檢查數據完整性"""
        return all(field in data for field in required_fields)
    
    @staticmethod
    def check_processing_time(duration: float, max_duration: float) -> bool:
        """檢查處理時間是否在合理範圍內"""
        return duration <= max_duration
    
    @staticmethod
    def check_file_exists(file_path: Union[str, Path]) -> bool:
        """檢查檔案是否存在"""
        return Path(file_path).exists()
    
    @staticmethod
    def calculate_success_rate(passed: int, total: int) -> float:
        """計算成功率"""
        return (passed / max(total, 1)) * 100