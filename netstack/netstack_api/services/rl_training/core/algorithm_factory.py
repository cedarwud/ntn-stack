"""
🧠 算法工廠模式實現

基於工廠模式的算法創建和管理，支援：
- 動態算法註冊
- 插件化架構
- 配置驅動實例化
- 生命週期管理
"""

import logging
from typing import Dict, Type, Any, List, Optional
from datetime import datetime
from ..interfaces.rl_algorithm import IRLAlgorithm, ScenarioType
# 違規算法已刪除 - 違反 CLAUDE.md 核心原則
# from ..algorithms.dqn_algorithm import DQNAlgorithm
# from ..algorithms.ppo_algorithm import PPOAlgorithm
# from ..algorithms.sac_algorithm import SACAlgorithm

logger = logging.getLogger(__name__)

# 演算法外掛程式註冊表
# 將演算法名稱映射到其對應的類別
# 違規算法已移除 - 遵循 CLAUDE.md 核心原則禁止模擬算法
algorithm_plugins: Dict[str, Type[IRLAlgorithm]] = {
    # DQN, PPO, SAC 算法已刪除 - 因使用模擬數據違反 CLAUDE.md 原則
    # Phase 2 將實現真實的 RL 算法
}


class AlgorithmInfo:
    """算法資訊類"""
    def __init__(self, name: str, algorithm_class: Type[IRLAlgorithm]):
        self.name = name
        self.algorithm_class = algorithm_class
        self.version = "1.0.0"
        self.description = f"{name.upper()} algorithm for LEO satellite handover decisions"
        self.author = "NTN Stack Team"
        self.supported_scenarios = [ScenarioType.URBAN, ScenarioType.SUBURBAN, ScenarioType.LOW_LATENCY]
        self.default_config = {
            "learning_rate": 0.001,
            "batch_size": 32,
            "episodes": 1000,
            "max_steps_per_episode": 1000
        }


class AlgorithmFactory:
    """算法工廠類 - 提供靜態方法來管理算法"""
    
    _algorithms_registry: Dict[str, AlgorithmInfo] = {}
    _initialized = False
    
    @classmethod
    def initialize(cls) -> None:
        """初始化算法工廠"""
        if cls._initialized:
            return
            
        try:
            # 註冊內建算法
            for name, algorithm_class in algorithm_plugins.items():
                cls._algorithms_registry[name] = AlgorithmInfo(name, algorithm_class)
            
            cls._initialized = True
            logger.info(f"AlgorithmFactory 初始化完成，註冊了 {len(cls._algorithms_registry)} 個算法")
            
        except Exception as e:
            logger.error(f"AlgorithmFactory 初始化失敗: {e}")
            raise
    
    @classmethod
    def get_available_algorithms(cls) -> List[str]:
        """獲取所有可用算法列表"""
        cls.initialize()  # 確保已初始化
        return list(cls._algorithms_registry.keys())
    
    @classmethod
    def get_algorithm_info(cls, algorithm_name: str) -> Optional[AlgorithmInfo]:
        """獲取算法詳細資訊"""
        cls.initialize()
        return cls._algorithms_registry.get(algorithm_name.lower())
    
    @classmethod
    def create_algorithm(cls, algorithm_name: str, scenario_type: ScenarioType, config: Optional[Dict[str, Any]] = None) -> IRLAlgorithm:
        """創建算法實例"""
        cls.initialize()
        
        algorithm_info = cls.get_algorithm_info(algorithm_name)
        if not algorithm_info:
            raise ValueError(f"未知的演算法: {algorithm_name}")
        
        # 使用預設配置
        default_config = algorithm_info.default_config.copy()
        if config:
            default_config.update(config)
        
        # 創建算法實例
        try:
            # 使用標準的 Gymnasium 環境名稱，而不是場景類型
            # 對於 LEO 衛星系統，我們使用一個通用的環境名稱
            env_name = "CartPole-v1"  # 使用標準環境作為占位符
            
            return algorithm_info.algorithm_class(
                env_name=env_name,
                config=default_config
            )
        except Exception as e:
            logger.error(f"創建算法 {algorithm_name} 失敗: {e}")
            raise
    
    @classmethod
    def get_algorithms_by_scenario(cls, scenario_type: ScenarioType) -> List[str]:
        """根據場景類型獲取支援的算法"""
        cls.initialize()
        supported_algorithms = []
        
        for name, info in cls._algorithms_registry.items():
            if scenario_type in info.supported_scenarios:
                supported_algorithms.append(name)
        
        return supported_algorithms
    
    @classmethod
    def get_registry_stats(cls) -> Dict[str, Any]:
        """獲取註冊中心統計資訊"""
        cls.initialize()
        
        return {
            "total_algorithms": len(cls._algorithms_registry),
            "available_algorithms": list(cls._algorithms_registry.keys()),
            "initialization_time": datetime.now().isoformat(),
            "status": "healthy" if cls._initialized else "uninitialized"
        }


# 向後兼容：保留舊的變數名
algorithm_plugin = algorithm_plugins

# 向後兼容的函數
def get_algorithm(name: str, env_name: Optional[str] = None, config: Optional[Dict[str, Any]] = None, 
                 scenario_type: Optional[ScenarioType] = None, use_singleton: bool = False, **kwargs) -> IRLAlgorithm:
    """
    演算法工廠函數。根據名稱獲取並初始化一個演算法實例。
    
    這是向後兼容的函數，內部使用 AlgorithmFactory 類
    
    Args:
        name: 算法名稱
        env_name: 環境名稱 (向後兼容)
        config: 算法配置
        scenario_type: 場景類型 (新參數)
        use_singleton: 是否使用單例模式 (新參數，目前忽略)
        **kwargs: 其他參數
    """
    # 確定場景類型
    if scenario_type is not None:
        final_scenario_type = scenario_type
    elif env_name is not None:
        try:
            final_scenario_type = ScenarioType(env_name.lower())
        except ValueError:
            final_scenario_type = ScenarioType.URBAN
    else:
        final_scenario_type = ScenarioType.URBAN
    
    # 確定配置
    final_config = config or {}
    
    return AlgorithmFactory.create_algorithm(name, final_scenario_type, final_config)
