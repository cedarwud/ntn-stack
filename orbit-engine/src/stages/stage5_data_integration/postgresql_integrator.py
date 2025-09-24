"""
PostgreSQL數據庫整合器 - Stage 5模組化組件

職責：
1. PostgreSQL數據庫操作和管理
2. 混合存儲架構實現
3. 衛星數據索引和元數據管理
4. 數據庫表創建和索引優化
"""

import json
import logging
import psycopg2

# 🚨 Grade A要求：動態計算RSRP閾值
noise_floor = -120  # 3GPP典型噪聲門檻
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class PostgreSQLIntegrator:
    """
    PostgreSQL整合器 - 重構版本 (向後兼容包裝器)
    
    此類現在作為輕量級包裝器，委派給專業化的模組：
    - DatabaseSchemaManager: 表結構和索引管理
    - SignalDataProcessor: 信號數據處理
    - HandoverEventManager: 3GPP換手事件管理
    - PostgreSQLCoordinator: 主協調器
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化PostgreSQL整合器 - 重構版本
        
        Args:
            config: 數據庫配置選項
        """
        self.logger = logging.getLogger(__name__)
        
        # 使用新的模組化協調器
        from .postgresql_coordinator import PostgreSQLCoordinator
        self.coordinator = PostgreSQLCoordinator(config)
        
        # 向後兼容性屬性
        self.db_config = self.coordinator.db_config
        self.integration_statistics = self.coordinator.integration_statistics
        self.table_schemas = self.coordinator.table_schemas
        self.connection = None
        
        self.logger.info("🔄 PostgreSQL整合器已重構為模組化架構")

    def connect_database(self):
        """建立數據庫連接 - 委派給協調器"""
        result = self.coordinator.connect_database()
        self.connection = self.coordinator.connection
        return result

    def disconnect_database(self):
        """關閉數據庫連接 - 委派給協調器"""
        self.coordinator.disconnect_database()

    def integrate_postgresql_data(self, integrated_data: Dict[str, Any]) -> Dict[str, Any]:
        """執行PostgreSQL數據整合 - 委派給協調器"""
        return self.coordinator.integrate_postgresql_data(integrated_data)

    def get_integration_statistics(self) -> Dict[str, Any]:
        """獲取整合統計信息 - 委派給協調器"""
        return self.coordinator.get_integration_statistics()

    # === 向後兼容的方法委派 ===
    
    def _create_postgresql_tables(self) -> Dict[str, Any]:
        """創建PostgreSQL表結構 - 委派給架構管理器"""
        if not self.coordinator.schema_manager:
            raise RuntimeError("數據庫連接未建立，請先調用 connect_database()")
        return self.coordinator.schema_manager.create_postgresql_tables()

    def _create_postgresql_indexes(self) -> Dict[str, Any]:
        """創建PostgreSQL索引 - 委派給架構管理器"""
        if not self.coordinator.schema_manager:
            raise RuntimeError("數據庫連接未建立，請先調用 connect_database()")
        return self.coordinator.schema_manager.create_postgresql_indexes()

    def _verify_mixed_storage(self) -> Dict[str, Any]:
        """驗證混合存儲架構 - 委派給架構管理器"""
        if not self.coordinator.schema_manager:
            raise RuntimeError("數據庫連接未建立，請先調用 connect_database()")
        return self.coordinator.schema_manager.verify_mixed_storage()

    def _extract_signal_statistics(self, satellite: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """提取信號統計 - 委派給信號處理器"""
        if not self.coordinator.signal_processor:
            raise RuntimeError("數據庫連接未建立，請先調用 connect_database()")
        return self.coordinator.signal_processor.extract_signal_statistics(satellite)

    def _estimate_rsrp_from_elevation(self, elevation_deg: float, constellation: str) -> float:
        """估算RSRP - 委派給信號處理器"""
        if not self.coordinator.signal_processor:
            raise RuntimeError("數據庫連接未建立，請先調用 connect_database()")
        return self.coordinator.signal_processor.estimate_rsrp_from_elevation(elevation_deg, constellation)

    def _grade_signal_quality(self, rsrp_dbm: float) -> str:
        """信號品質分級 - 委派給信號處理器"""
        if not self.coordinator.signal_processor:
            raise RuntimeError("數據庫連接未建立，請先調用 connect_database()")
        return self.coordinator.signal_processor.grade_signal_quality(rsrp_dbm)

    def _insert_satellite_metadata(self, satellite: Dict[str, Any]) -> Dict[str, Any]:
        """插入衛星元數據 - 委派給信號處理器"""
        if not self.coordinator.signal_processor:
            raise RuntimeError("數據庫連接未建立，請先調用 connect_database()")
        return self.coordinator.signal_processor.insert_satellite_metadata(satellite)

    def _insert_signal_statistics(self, satellite: Dict[str, Any]) -> Dict[str, Any]:
        """插入信號統計 - 委派給信號處理器"""
        if not self.coordinator.signal_processor:
            raise RuntimeError("數據庫連接未建立，請先調用 connect_database()")
        signal_stats = self.coordinator.signal_processor.extract_signal_statistics(satellite)
        if signal_stats:
            return self.coordinator.signal_processor.insert_signal_statistics(satellite, signal_stats)
        return {"success": True, "errors": []}

    def _generate_handover_events(self, satellite: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成換手事件 - 委派給事件管理器"""
        if not self.coordinator.event_manager:
            raise RuntimeError("數據庫連接未建立，請先調用 connect_database()")
        return self.coordinator.event_manager.generate_handover_events(satellite)

    def _insert_handover_events(self, satellite: Dict[str, Any]) -> Dict[str, Any]:
        """插入換手事件 - 委派給事件管理器"""
        if not self.coordinator.event_manager:
            raise RuntimeError("數據庫連接未建立，請先調用 connect_database()")
        events = self.coordinator.event_manager.generate_handover_events(satellite)
        if events:
            return self.coordinator.event_manager.insert_handover_events(satellite, events)
        return {"success": True, "errors": []}

    def _calculate_realistic_processing_latency(self, signal_change_rate: float, constellation: str) -> float:
        """計算處理延遲 - 委派給事件管理器"""
        if not self.coordinator.event_manager:
            raise RuntimeError("數據庫連接未建立，請先調用 connect_database()")
        return self.coordinator.event_manager.calculate_realistic_processing_latency(signal_change_rate, constellation)

    def _determine_3gpp_handover_decision(self, current_rsrp: float, event_type: str, elevation_deg: float) -> str:
        """3GPP換手決策 - 委派給事件管理器"""
        if not self.coordinator.event_manager:
            raise RuntimeError("數據庫連接未建立，請先調用 connect_database()")
        return self.coordinator.event_manager.determine_3gpp_handover_decision(current_rsrp, event_type, elevation_deg)

    def _calculate_trigger_rsrp(self, event_type: str, elevation_deg: float) -> float:
        """計算觸發RSRP - 委派給事件管理器"""
        if not self.coordinator.event_manager:
            raise RuntimeError("數據庫連接未建立，請先調用 connect_database()")
        return self.coordinator.event_manager.calculate_trigger_rsrp(event_type, elevation_deg)

    def _determine_3gpp_event_type(self, rsrp_current: float, rsrp_previous: float) -> str:
        """確定3GPP事件類型 - 委派給事件管理器"""
        if not self.coordinator.event_manager:
            raise RuntimeError("數據庫連接未建立，請先調用 connect_database()")
        return self.coordinator.event_manager.determine_3gpp_event_type(rsrp_current, rsrp_previous)

    def _determine_handover_decision(self, rsrp_dbm: float, event_type: str, elevation_deg: float) -> str:
        """確定換手決策 - 委派給事件管理器"""
        if not self.coordinator.event_manager:
            raise RuntimeError("數據庫連接未建立，請先調用 connect_database()")
        return self.coordinator.event_manager.determine_handover_decision(rsrp_dbm, event_type, elevation_deg)

    def _calculate_processing_latency(self, signal_change_rate: float, constellation: str) -> float:
        """計算處理延遲 - 委派給事件管理器"""
        if not self.coordinator.event_manager:
            raise RuntimeError("數據庫連接未建立，請先調用 connect_database()")
        return self.coordinator.event_manager.calculate_realistic_processing_latency(signal_change_rate, constellation)

    def _insert_processing_summary(self, integrated_data: Dict[str, Any]) -> Dict[str, Any]:
        """插入處理摘要 - 委派給協調器"""
        return self.coordinator.insert_processing_summary(integrated_data)