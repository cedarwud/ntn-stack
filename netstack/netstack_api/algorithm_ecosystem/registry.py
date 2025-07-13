"""
🏭 算法註冊中心

動態算法管理系統，支持算法的註冊、發現、載入和配置管理。
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Type
from dataclasses import asdict
import importlib
import inspect
from pathlib import Path
import yaml
import json
from datetime import datetime

from .interfaces import (
    HandoverAlgorithm,
    RLHandoverAlgorithm,
    AlgorithmInfo,
    AlgorithmType,
)

logger = logging.getLogger(__name__)


class AlgorithmLoadError(Exception):
    """算法加載錯誤"""

    pass


class AlgorithmRegistry:
    """算法註冊中心

    管理所有可用的換手算法，支持動態註冊、發現和配置管理。
    """

    def __init__(self, config_path: Optional[str] = None):
        """初始化註冊中心

        Args:
            config_path: 算法配置文件路徑
        """
        self._algorithms: Dict[str, HandoverAlgorithm] = {}
        self._algorithm_configs: Dict[str, Dict[str, Any]] = {}
        self._algorithm_classes: Dict[str, Type[HandoverAlgorithm]] = {}
        self._enabled_algorithms: Dict[str, bool] = {}
        self._algorithm_priorities: Dict[str, int] = {}
        self._config_path = config_path
        self._initialized = False

        # 算法統計信息
        self._algorithm_stats: Dict[str, Dict[str, Any]] = {}

        logger.info(f"算法註冊中心初始化，配置路徑: {config_path}")

    async def initialize(self) -> None:
        """初始化註冊中心"""
        if self._initialized:
            return

        logger.info("開始初始化算法註冊中心...")

        # 載入配置文件
        if self._config_path and Path(self._config_path).exists():
            await self._load_config_file()

        # 自動發現算法
        await self._discover_algorithms()

        self._initialized = True
        logger.info(f"算法註冊中心初始化完成，已註冊 {len(self._algorithms)} 個算法")

    async def register_algorithm(
        self,
        name: str,
        algorithm: HandoverAlgorithm,
        config: Optional[Dict[str, Any]] = None,
        enabled: bool = True,
        priority: int = 10,
    ) -> None:
        """註冊算法

        Args:
            name: 算法名稱
            algorithm: 算法實例
            config: 算法配置
            enabled: 是否啟用
            priority: 優先級 (數字越大優先級越高)
        """
        try:
            # 驗證算法實例
            if not isinstance(algorithm, HandoverAlgorithm):
                raise ValueError(f"算法 {name} 必須繼承 HandoverAlgorithm")

            # 初始化算法
            if config:
                await algorithm.initialize(config)
            elif not algorithm.is_initialized:
                await algorithm.initialize()

            # 註冊算法
            self._algorithms[name] = algorithm
            self._algorithm_configs[name] = config or {}
            self._enabled_algorithms[name] = enabled
            self._algorithm_priorities[name] = priority
            self._algorithm_stats[name] = {
                "registered_at": datetime.now().isoformat(),
                "total_calls": 0,
                "total_execution_time": 0.0,
                "last_used": None,
                "error_count": 0,
            }

            # 記錄算法類型
            algorithm_info = algorithm.get_algorithm_info()
            self._algorithm_classes[name] = type(algorithm)

            logger.info(
                f"算法 '{name}' 註冊成功 (類型: {algorithm_info.algorithm_type.value}, 優先級: {priority})"
            )

        except Exception as e:
            logger.error(f"註冊算法 '{name}' 失敗: {e}")
            raise AlgorithmLoadError(f"Failed to register algorithm '{name}': {e}")

    async def register_algorithm_class(
        self,
        name: str,
        algorithm_class: Type[HandoverAlgorithm],
        config: Optional[Dict[str, Any]] = None,
        enabled: bool = True,
        priority: int = 10,
    ) -> None:
        """註冊算法類

        Args:
            name: 算法名稱
            algorithm_class: 算法類
            config: 算法配置
            enabled: 是否啟用
            priority: 優先級
        """
        try:
            # 創建算法實例
            algorithm = algorithm_class(name, config)
            await self.register_algorithm(name, algorithm, config, enabled, priority)

        except Exception as e:
            logger.error(f"註冊算法類 '{name}' 失敗: {e}")
            raise AlgorithmLoadError(
                f"Failed to register algorithm class '{name}': {e}"
            )

    def get_algorithm(self, name: str) -> Optional[HandoverAlgorithm]:
        """獲取算法實例

        Args:
            name: 算法名稱

        Returns:
            HandoverAlgorithm: 算法實例，如果不存在返回 None
        """
        if name not in self._algorithms:
            logger.warning(f"算法 '{name}' 不存在")
            return None

        if not self._enabled_algorithms.get(name, False):
            logger.warning(f"算法 '{name}' 已禁用")
            return None

        # 更新統計信息
        self._algorithm_stats[name]["total_calls"] += 1
        self._algorithm_stats[name]["last_used"] = datetime.now().isoformat()

        return self._algorithms[name]

    def list_algorithms(self) -> List[AlgorithmInfo]:
        """列出所有可用算法

        Returns:
            List[AlgorithmInfo]: 算法信息列表
        """
        algorithms = []
        for name, algorithm in self._algorithms.items():
            try:
                info = algorithm.get_algorithm_info()
                # 添加註冊中心的額外信息
                info.parameters.update(
                    {
                        "enabled": self._enabled_algorithms.get(name, False),
                        "priority": self._algorithm_priorities.get(name, 0),
                        "statistics": self._algorithm_stats.get(name, {}),
                    }
                )
                algorithms.append(info)
            except Exception as e:
                logger.error(f"獲取算法 '{name}' 信息失敗: {e}")

        # 按優先級排序
        algorithms.sort(key=lambda x: x.parameters.get("priority", 0), reverse=True)
        return algorithms

    def list_enabled_algorithms(self) -> List[str]:
        """列出所有啟用的算法名稱

        Returns:
            List[str]: 已啟用的算法名稱列表
        """
        return [name for name, enabled in self._enabled_algorithms.items() if enabled]

    def get_registered_algorithms(self) -> Dict[str, HandoverAlgorithm]:
        """獲取所有已註冊的算法

        Returns:
            Dict[str, HandoverAlgorithm]: 已註冊算法的字典
        """
        return self._algorithms.copy()

    def is_registered(self, name: str) -> bool:
        """檢查算法是否已註冊

        Args:
            name: 算法名稱

        Returns:
            bool: 是否已註冊
        """
        return name in self._algorithms

    def get_algorithm_by_type(
        self, algorithm_type: AlgorithmType
    ) -> List[HandoverAlgorithm]:
        """根據類型獲取算法

        Args:
            algorithm_type: 算法類型

        Returns:
            List[HandoverAlgorithm]: 匹配類型的算法列表
        """
        algorithms = []
        for name, algorithm in self._algorithms.items():
            if not self._enabled_algorithms.get(name, False):
                continue

            try:
                info = algorithm.get_algorithm_info()
                if info.algorithm_type == algorithm_type:
                    algorithms.append(algorithm)
            except Exception as e:
                logger.error(f"檢查算法 '{name}' 類型失敗: {e}")

        return algorithms

    def get_best_algorithm(
        self, criteria: str = "priority"
    ) -> Optional[HandoverAlgorithm]:
        """獲取最佳算法

        Args:
            criteria: 選擇標準 ('priority', 'performance', 'reliability')

        Returns:
            HandoverAlgorithm: 最佳算法實例
        """
        enabled_algorithms = [
            (name, algo)
            for name, algo in self._algorithms.items()
            if self._enabled_algorithms.get(name, False)
        ]

        if not enabled_algorithms:
            return None

        if criteria == "priority":
            # 按優先級選擇
            best_name = max(
                enabled_algorithms,
                key=lambda x: self._algorithm_priorities.get(x[0], 0),
            )[0]
            return self._algorithms[best_name]

        elif criteria == "performance":
            # 按平均執行時間選擇
            best_name = min(
                enabled_algorithms,
                key=lambda x: self._algorithm_stats.get(x[0], {}).get(
                    "total_execution_time", float("inf")
                ),
            )[0]
            return self._algorithms[best_name]

        elif criteria == "reliability":
            # 按錯誤率選擇
            best_name = min(
                enabled_algorithms,
                key=lambda x: self._algorithm_stats.get(x[0], {}).get(
                    "error_count", float("inf")
                ),
            )[0]
            return self._algorithms[best_name]

        else:
            logger.warning(f"未知的選擇標準: {criteria}，使用優先級")
            return self.get_best_algorithm("priority")

    async def enable_algorithm(self, name: str) -> bool:
        """啟用算法

        Args:
            name: 算法名稱

        Returns:
            bool: 是否成功
        """
        if name not in self._algorithms:
            logger.error(f"算法 '{name}' 不存在")
            return False

        self._enabled_algorithms[name] = True
        logger.info(f"算法 '{name}' 已啟用")
        return True

    async def disable_algorithm(self, name: str) -> bool:
        """禁用算法

        Args:
            name: 算法名稱

        Returns:
            bool: 是否成功
        """
        if name not in self._algorithms:
            logger.error(f"算法 '{name}' 不存在")
            return False

        self._enabled_algorithms[name] = False
        logger.info(f"算法 '{name}' 已禁用")
        return True

    async def update_algorithm_config(self, name: str, config: Dict[str, Any]) -> bool:
        """更新算法配置

        Args:
            name: 算法名稱
            config: 新配置

        Returns:
            bool: 是否成功
        """
        if name not in self._algorithms:
            logger.error(f"算法 '{name}' 不存在")
            return False

        try:
            # 更新算法配置
            self._algorithms[name].update_config(config)
            self._algorithm_configs[name].update(config)

            logger.info(f"算法 '{name}' 配置更新成功")
            return True

        except Exception as e:
            logger.error(f"更新算法 '{name}' 配置失敗: {e}")
            return False

    async def reload_algorithm(self, name: str) -> bool:
        """重新載入算法

        Args:
            name: 算法名稱

        Returns:
            bool: 是否成功
        """
        if name not in self._algorithms:
            logger.error(f"算法 '{name}' 不存在")
            return False

        try:
            # 保存原有配置
            config = self._algorithm_configs.get(name, {})
            enabled = self._enabled_algorithms.get(name, False)
            priority = self._algorithm_priorities.get(name, 10)
            algorithm_class = self._algorithm_classes.get(name)

            if not algorithm_class:
                logger.error(f"無法重新載入算法 '{name}'：找不到算法類")
                return False

            # 移除舊實例
            await self.unregister_algorithm(name)

            # 重新註冊
            await self.register_algorithm_class(
                name, algorithm_class, config, enabled, priority
            )

            logger.info(f"算法 '{name}' 重新載入成功")
            return True

        except Exception as e:
            logger.error(f"重新載入算法 '{name}' 失敗: {e}")
            return False

    async def unregister_algorithm(self, name: str) -> bool:
        """註銷算法

        Args:
            name: 算法名稱

        Returns:
            bool: 是否成功
        """
        if name not in self._algorithms:
            logger.warning(f"算法 '{name}' 不存在，無需註銷")
            return False

        try:
            # 清理資源
            algorithm = self._algorithms[name]
            if hasattr(algorithm, "cleanup"):
                await algorithm.cleanup()

            # 移除記錄
            del self._algorithms[name]
            del self._algorithm_configs[name]
            del self._enabled_algorithms[name]
            del self._algorithm_priorities[name]
            del self._algorithm_stats[name]

            if name in self._algorithm_classes:
                del self._algorithm_classes[name]

            logger.info(f"算法 '{name}' 註銷成功")
            return True

        except Exception as e:
            logger.error(f"註銷算法 '{name}' 失敗: {e}")
            return False

    def get_registry_stats(self) -> Dict[str, Any]:
        """獲取註冊中心統計信息

        Returns:
            Dict[str, Any]: 統計信息
        """
        total_algorithms = len(self._algorithms)
        enabled_algorithms = len(
            [name for name, enabled in self._enabled_algorithms.items() if enabled]
        )

        algorithm_types = {}
        for algorithm in self._algorithms.values():
            try:
                info = algorithm.get_algorithm_info()
                algorithm_type = info.algorithm_type.value
                algorithm_types[algorithm_type] = (
                    algorithm_types.get(algorithm_type, 0) + 1
                )
            except Exception:
                pass

        return {
            "total_algorithms": total_algorithms,
            "enabled_algorithms": enabled_algorithms,
            "disabled_algorithms": total_algorithms - enabled_algorithms,
            "algorithm_types": algorithm_types,
            "algorithm_stats": self._algorithm_stats,
            "initialized": self._initialized,
        }

    async def _load_config_file(self) -> None:
        """載入配置文件"""
        try:
            config_path = Path(self._config_path)

            if config_path.suffix.lower() in [".yml", ".yaml"]:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
            elif config_path.suffix.lower() == ".json":
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
            else:
                logger.error(f"不支持的配置文件格式: {config_path.suffix}")
                return

            # 處理配置
            handover_algorithms = config.get("handover_algorithms", {})

            for category, algorithms in handover_algorithms.items():
                for algo_name, algo_config in algorithms.items():
                    if algo_config.get("enabled", True):
                        await self._load_algorithm_from_config(algo_name, algo_config)

            logger.info(f"配置文件載入完成: {config_path}")

        except Exception as e:
            logger.error(f"載入配置文件失敗: {e}")

    async def _load_algorithm_from_config(
        self, name: str, config: Dict[str, Any]
    ) -> None:
        """從配置載入算法"""
        try:
            class_path = config.get("class")
            if not class_path:
                logger.error(f"算法 '{name}' 缺少 class 配置")
                return

            # 動態導入算法類
            module_path, class_name = class_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            algorithm_class = getattr(module, class_name)

            # 驗證算法類
            if not issubclass(algorithm_class, HandoverAlgorithm):
                logger.error(f"算法類 '{class_path}' 必須繼承 HandoverAlgorithm")
                return

            # 註冊算法
            algorithm_config = config.get("config", {})
            enabled = config.get("enabled", True)
            priority = config.get("priority", 10)

            await self.register_algorithm_class(
                name, algorithm_class, algorithm_config, enabled, priority
            )

        except Exception as e:
            logger.error(f"從配置載入算法 '{name}' 失敗: {e}")

    async def _discover_algorithms(self) -> None:
        """自動發現算法"""
        try:
            # 這裡可以實現自動發現邏輯
            # 掃描特定目錄下的算法模組
            logger.info("自動發現算法功能待實現")

        except Exception as e:
            logger.error(f"自動發現算法失敗: {e}")

    async def cleanup(self) -> None:
        """清理資源"""
        logger.info("開始清理算法註冊中心...")

        for name in list(self._algorithms.keys()):
            await self.unregister_algorithm(name)

        self._initialized = False
        logger.info("算法註冊中心清理完成")
