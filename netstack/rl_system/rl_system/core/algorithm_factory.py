from typing import Dict, Any, List, Type
import logging
from ..interfaces.rl_algorithm import IRLAlgorithm

logger = logging.getLogger(__name__)


class AlgorithmFactory:
    """算法工廠 - 負責創建算法實例"""

    _registry: Dict[str, Type[IRLAlgorithm]] = {}

    @classmethod
    def register_algorithm(cls, name: str, algorithm_class: Type[IRLAlgorithm]) -> None:
        """註冊新算法類型"""
        if not issubclass(algorithm_class, IRLAlgorithm):
            raise ValueError(f"Algorithm {name} must implement IRLAlgorithm interface")
        if name in cls._registry:
            logger.warning(f"Algorithm '{name}' is already registered. Overwriting.")
        cls._registry[name] = algorithm_class
        logger.info(f"Algorithm '{name}' registered successfully.")

    @classmethod
    def create_algorithm(cls, name: str, config: Dict[str, Any]) -> IRLAlgorithm:
        """創建算法實例"""
        logger.info(f"Attempting to create algorithm '{name}'...")
        if name not in cls._registry:
            logger.error(
                f"Unknown algorithm: {name}. Available: {list(cls._registry.keys())}"
            )
            raise ValueError(f"Unknown algorithm: {name}")

        algorithm_class = cls._registry[name]
        instance = algorithm_class(config)
        logger.info(f"Successfully created instance of algorithm '{name}'.")
        return instance

    @classmethod
    def get_available_algorithms(cls) -> List[str]:
        """獲取所有可用算法"""
        return list(cls._registry.keys())


# 自動註冊裝飾器
def algorithm_plugin(name: str):
    """算法插件註冊裝飾器"""

    def decorator(cls):
        AlgorithmFactory.register_algorithm(name, cls)
        return cls

    return decorator
