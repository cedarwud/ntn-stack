"""
依賴注入模組 - 從 algorithm_ecosystem_router.py 中提取的依賴注入邏輯
清晰分離關注點，便於測試和維護
"""

from typing import Optional
import logging

from ...algorithm_ecosystem import AlgorithmRegistry, EnvironmentManager
from ...algorithm_ecosystem.adapters import (
    InfocomAlgorithmAdapter,
    SimpleThresholdAlgorithmAdapter,
    RandomAlgorithmAdapter,
)

logger = logging.getLogger(__name__)

# 全局實例
_algorithm_registry: Optional[AlgorithmRegistry] = None
_environment_manager: Optional[EnvironmentManager] = None


async def initialize_algorithm_ecosystem():
    """初始化算法生態系統組件"""
    global _algorithm_registry, _environment_manager

    try:
        # 初始化算法註冊中心
        _algorithm_registry = AlgorithmRegistry()

        # 註冊內建算法
        await _register_builtin_algorithms()

        # 初始化環境管理器
        _environment_manager = EnvironmentManager()
        await _environment_manager.initialize()

        logger.info("算法生態系統初始化完成")

    except Exception as e:
        logger.error(f"算法生態系統初始化失敗: {e}")
        raise


async def _register_builtin_algorithms():
    """註冊內建算法"""
    registered_count = 0

    try:
        # 嘗試註冊Infocom 算法
        try:
            infocom_adapter = InfocomAlgorithmAdapter()
            await _algorithm_registry.register_algorithm(
                name="ieee_infocom_2024",
                algorithm=infocom_adapter,
                config={},
                enabled=True,
                priority=20,
            )
            registered_count += 1
            logger.info("✅ Infocom算法註冊成功")
        except ImportError as e:
            logger.warning(f"⚠️ Infocom算法註冊跳過: {e}")

        # 嘗試註冊簡單閾值算法
        try:
            threshold_adapter = SimpleThresholdAlgorithmAdapter()
            await _algorithm_registry.register_algorithm(
                name="simple_threshold",
                algorithm=threshold_adapter,
                config={},
                enabled=True,
                priority=15,
            )
            registered_count += 1
            logger.info("✅ 簡單閾值算法註冊成功")
        except ImportError as e:
            logger.warning(f"⚠️ 簡單閾值算法註冊跳過: {e}")

        # 嘗試註冊隨機算法
        try:
            random_adapter = RandomAlgorithmAdapter()
            await _algorithm_registry.register_algorithm(
                name="random_algorithm",
                algorithm=random_adapter,
                config={},
                enabled=True,
                priority=5,
            )
            registered_count += 1
            logger.info("✅ 隨機算法註冊成功")
        except ImportError as e:
            logger.warning(f"⚠️ 隨機算法註冊跳過: {e}")

        logger.info(f"內建算法註冊完成 ({registered_count}/3 個算法可用)")

    except Exception as e:
        logger.error(f"內建算法註冊過程中發生錯誤: {e}")
        # 不再拋出異常，讓系統能夠繼續啟動


async def cleanup_algorithm_ecosystem():
    """清理算法生態系統資源"""
    global _algorithm_registry, _environment_manager

    try:
        if _environment_manager:
            await _environment_manager.cleanup()
            _environment_manager = None

        if _algorithm_registry:
            _algorithm_registry = None

        logger.info("算法生態系統資源清理完成")

    except Exception as e:
        logger.error(f"算法生態系統資源清理失敗: {e}")


# === 依賴注入函數 ===


def get_algorithm_registry() -> AlgorithmRegistry:
    """獲取算法註冊中心實例"""
    if _algorithm_registry is None:
        raise RuntimeError("算法註冊中心未初始化")
    return _algorithm_registry


def get_environment_manager() -> EnvironmentManager:
    """獲取環境管理器實例"""
    if _environment_manager is None:
        raise RuntimeError("環境管理器未初始化")
    return _environment_manager


# === 健康檢查依賴 ===


def check_services_health() -> dict:
    """檢查各服務健康狀態"""
    health_status = {
        "algorithm_registry": _algorithm_registry is not None,
        "environment_manager": _environment_manager is not None,
    }

    return {"overall_healthy": all(health_status.values()), "services": health_status}


# === 生命週期管理 ===


class LifecycleManager:
    """生命週期管理器"""

    @staticmethod
    async def startup():
        """啟動事件處理"""
        await initialize_algorithm_ecosystem()
        logger.info("算法生態系統啟動完成")

    @staticmethod
    async def shutdown():
        """關閉事件處理"""
        await cleanup_algorithm_ecosystem()
        logger.info("算法生態系統關閉完成")


# === 配置管理依賴 ===


def validate_orchestrator_config(config: dict) -> bool:
    """驗證協調器配置"""
    required_fields = ["mode", "decision_strategy"]
    return all(field in config for field in required_fields)
