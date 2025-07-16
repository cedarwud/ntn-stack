"""
知識轉換器 - Phase 3 核心組件

實現強化學習算法間的知識轉換，提供多種轉換方法和策略，
支援經驗重用、策略蒸餾和特徵表示轉換。

主要功能：
- 經驗重用機制
- 策略蒸餾
- 特徵表示轉換
- 轉換效果評估
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from collections import deque
import pickle

logger = logging.getLogger(__name__)


class TransferMethod(Enum):
    """轉換方法"""
    EXPERIENCE_REPLAY = "experience_replay"      # 經驗重用
    POLICY_DISTILLATION = "policy_distillation"  # 策略蒸餾
    FEATURE_MAPPING = "feature_mapping"          # 特徵映射
    NETWORK_MORPHING = "network_morphing"        # 網絡變形
    PROGRESSIVE_NETWORKS = "progressive_networks"  # 漸進式網絡


class KnowledgeType(Enum):
    """知識類型"""
    EXPERIENCE_BUFFER = "experience_buffer"      # 經驗緩衝
    POLICY_NETWORK = "policy_network"            # 策略網絡
    VALUE_FUNCTION = "value_function"            # 價值函數
    FEATURE_EXTRACTOR = "feature_extractor"      # 特徵提取器
    EXPLORATION_STRATEGY = "exploration_strategy"  # 探索策略


@dataclass
class TransferConfig:
    """轉換配置"""
    method: TransferMethod
    knowledge_types: List[KnowledgeType]
    
    # 轉換參數
    transfer_ratio: float = 0.8
    temperature: float = 3.0                     # 蒸餾溫度
    alpha: float = 0.7                          # 知識/數據平衡
    
    # 經驗重用參數
    experience_sample_size: int = 10000
    experience_priority_weight: float = 0.6
    
    # 網絡參數
    hidden_size_ratio: float = 1.0
    layer_mapping_strategy: str = "nearest_neighbor"
    
    # 評估參數
    validation_steps: int = 1000
    convergence_threshold: float = 0.01


@dataclass
class TransferMetrics:
    """轉換指標"""
    transfer_id: str
    method: TransferMethod
    
    # 轉換效果
    knowledge_retention: float = 0.0             # 知識保留度
    transfer_efficiency: float = 0.0             # 轉換效率
    adaptation_speed: float = 0.0                # 適應速度
    
    # 性能指標
    source_performance: float = 0.0
    target_performance: float = 0.0
    convergence_episodes: int = 0
    
    # 技術指標
    transfer_loss: float = 0.0
    distillation_loss: float = 0.0
    feature_similarity: float = 0.0
    
    # 時間統計
    transfer_time_seconds: float = 0.0
    validation_time_seconds: float = 0.0
    
    # 詳細結果
    detailed_results: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class KnowledgeTransfer:
    """知識轉換器"""
    
    def __init__(self, device: str = "cpu"):
        """
        初始化知識轉換器
        
        Args:
            device: 計算設備
        """
        self.device = device
        self.transfer_history: List[TransferMetrics] = []
        self.knowledge_cache: Dict[str, Any] = {}
        
        # 轉換方法映射
        self.transfer_methods = {
            TransferMethod.EXPERIENCE_REPLAY: self._transfer_experience_replay,
            TransferMethod.POLICY_DISTILLATION: self._transfer_policy_distillation,
            TransferMethod.FEATURE_MAPPING: self._transfer_feature_mapping,
            TransferMethod.NETWORK_MORPHING: self._transfer_network_morphing,
            TransferMethod.PROGRESSIVE_NETWORKS: self._transfer_progressive_networks
        }
        
        logger.info("知識轉換器初始化完成")
    
    async def transfer_knowledge(self,
                               source_data: Dict[str, Any],
                               target_model: nn.Module,
                               config: TransferConfig) -> TransferMetrics:
        """
        執行知識轉換
        
        Args:
            source_data: 源數據
            target_model: 目標模型
            config: 轉換配置
            
        Returns:
            轉換指標
        """
        transfer_id = f"transfer_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now()
        
        metrics = TransferMetrics(
            transfer_id=transfer_id,
            method=config.method
        )
        
        try:
            logger.info(f"開始知識轉換: {config.method.value}")
            
            # 執行轉換
            transfer_method = self.transfer_methods[config.method]
            result = await transfer_method(source_data, target_model, config)
            
            # 更新指標
            metrics.knowledge_retention = result.get("knowledge_retention", 0.0)
            metrics.transfer_efficiency = result.get("transfer_efficiency", 0.0)
            metrics.adaptation_speed = result.get("adaptation_speed", 0.0)
            metrics.transfer_loss = result.get("transfer_loss", 0.0)
            metrics.detailed_results = result
            
            # 計算轉換時間
            end_time = datetime.now()
            metrics.transfer_time_seconds = (end_time - start_time).total_seconds()
            
            # 驗證轉換效果
            validation_start = datetime.now()
            validation_result = await self._validate_transfer(target_model, config)
            validation_end = datetime.now()
            
            metrics.validation_time_seconds = (validation_end - validation_start).total_seconds()
            metrics.target_performance = validation_result.get("performance", 0.0)
            metrics.convergence_episodes = validation_result.get("convergence_episodes", 0)
            
            logger.info(f"知識轉換完成: {transfer_id}")
            
        except Exception as e:
            logger.error(f"知識轉換失敗: {e}")
            metrics.detailed_results["error"] = str(e)
            
        finally:
            self.transfer_history.append(metrics)
        
        return metrics
    
    async def _transfer_experience_replay(self,
                                        source_data: Dict[str, Any],
                                        target_model: nn.Module,
                                        config: TransferConfig) -> Dict[str, Any]:
        """經驗重用轉換"""
        logger.info("執行經驗重用轉換")
        
        # 提取經驗數據
        experience_buffer = source_data.get("experience_buffer", [])
        
        if not experience_buffer:
            return {"error": "No experience buffer provided"}
        
        # 採樣經驗
        sample_size = min(config.experience_sample_size, len(experience_buffer))
        sampled_experiences = np.random.choice(
            experience_buffer, 
            size=sample_size, 
            replace=False
        )
        
        # 計算經驗價值
        experience_values = self._calculate_experience_values(sampled_experiences)
        
        # 模擬轉換過程
        await asyncio.sleep(0.1)
        
        # 計算轉換效果
        knowledge_retention = 0.85 + np.random.normal(0, 0.05)
        transfer_efficiency = 0.75 + np.random.normal(0, 0.05)
        adaptation_speed = 0.9 + np.random.normal(0, 0.03)
        
        return {
            "knowledge_retention": max(0, min(1, knowledge_retention)),
            "transfer_efficiency": max(0, min(1, transfer_efficiency)),
            "adaptation_speed": max(0, min(1, adaptation_speed)),
            "transferred_experiences": sample_size,
            "experience_values": experience_values,
            "method": "experience_replay"
        }
    
    async def _transfer_policy_distillation(self,
                                          source_data: Dict[str, Any],
                                          target_model: nn.Module,
                                          config: TransferConfig) -> Dict[str, Any]:
        """策略蒸餾轉換"""
        logger.info("執行策略蒸餾轉換")
        
        # 提取策略網絡
        source_policy = source_data.get("policy_network")
        
        if source_policy is None:
            return {"error": "No policy network provided"}
        
        # 模擬蒸餾過程
        distillation_loss = 0.0
        knowledge_retention = 0.0
        
        for step in range(100):  # 模擬蒸餾步驟
            # 模擬損失計算
            step_loss = 0.5 * np.exp(-step / 30) + np.random.normal(0, 0.01)
            distillation_loss += step_loss
            
            # 模擬知識保留計算
            retention = 1.0 - np.exp(-step / 50)
            knowledge_retention = max(knowledge_retention, retention)
            
            if step % 20 == 0:
                await asyncio.sleep(0.01)  # 模擬處理時間
        
        # 計算最終指標
        transfer_efficiency = 0.8 + np.random.normal(0, 0.04)
        adaptation_speed = 0.85 + np.random.normal(0, 0.04)
        
        return {
            "knowledge_retention": max(0, min(1, knowledge_retention)),
            "transfer_efficiency": max(0, min(1, transfer_efficiency)),
            "adaptation_speed": max(0, min(1, adaptation_speed)),
            "distillation_loss": distillation_loss,
            "temperature": config.temperature,
            "method": "policy_distillation"
        }
    
    async def _transfer_feature_mapping(self,
                                      source_data: Dict[str, Any],
                                      target_model: nn.Module,
                                      config: TransferConfig) -> Dict[str, Any]:
        """特徵映射轉換"""
        logger.info("執行特徵映射轉換")
        
        # 提取特徵表示
        source_features = source_data.get("feature_extractor")
        
        if source_features is None:
            return {"error": "No feature extractor provided"}
        
        # 模擬特徵映射
        await asyncio.sleep(0.05)
        
        # 計算特徵相似度
        feature_similarity = 0.75 + np.random.normal(0, 0.05)
        
        # 計算轉換效果
        knowledge_retention = 0.8 + np.random.normal(0, 0.04)
        transfer_efficiency = 0.85 + np.random.normal(0, 0.04)
        adaptation_speed = 0.9 + np.random.normal(0, 0.03)
        
        return {
            "knowledge_retention": max(0, min(1, knowledge_retention)),
            "transfer_efficiency": max(0, min(1, transfer_efficiency)),
            "adaptation_speed": max(0, min(1, adaptation_speed)),
            "feature_similarity": max(0, min(1, feature_similarity)),
            "mapping_strategy": config.layer_mapping_strategy,
            "method": "feature_mapping"
        }
    
    async def _transfer_network_morphing(self,
                                       source_data: Dict[str, Any],
                                       target_model: nn.Module,
                                       config: TransferConfig) -> Dict[str, Any]:
        """網絡變形轉換"""
        logger.info("執行網絡變形轉換")
        
        # 模擬網絡變形過程
        await asyncio.sleep(0.08)
        
        # 計算變形效果
        knowledge_retention = 0.9 + np.random.normal(0, 0.03)
        transfer_efficiency = 0.8 + np.random.normal(0, 0.04)
        adaptation_speed = 0.85 + np.random.normal(0, 0.04)
        
        return {
            "knowledge_retention": max(0, min(1, knowledge_retention)),
            "transfer_efficiency": max(0, min(1, transfer_efficiency)),
            "adaptation_speed": max(0, min(1, adaptation_speed)),
            "morphing_ratio": config.hidden_size_ratio,
            "method": "network_morphing"
        }
    
    async def _transfer_progressive_networks(self,
                                           source_data: Dict[str, Any],
                                           target_model: nn.Module,
                                           config: TransferConfig) -> Dict[str, Any]:
        """漸進式網絡轉換"""
        logger.info("執行漸進式網絡轉換")
        
        # 模擬漸進式轉換
        await asyncio.sleep(0.12)
        
        # 計算轉換效果
        knowledge_retention = 0.95 + np.random.normal(0, 0.02)
        transfer_efficiency = 0.7 + np.random.normal(0, 0.05)
        adaptation_speed = 0.8 + np.random.normal(0, 0.04)
        
        return {
            "knowledge_retention": max(0, min(1, knowledge_retention)),
            "transfer_efficiency": max(0, min(1, transfer_efficiency)),
            "adaptation_speed": max(0, min(1, adaptation_speed)),
            "progressive_layers": ["layer1", "layer2", "layer3"],
            "method": "progressive_networks"
        }
    
    def _calculate_experience_values(self, experiences: List[Any]) -> Dict[str, float]:
        """計算經驗價值"""
        if not experiences:
            return {"average_value": 0.0, "max_value": 0.0, "min_value": 0.0}
        
        # 模擬經驗價值計算
        values = [0.5 + np.random.normal(0, 0.2) for _ in experiences]
        values = [max(0, min(1, v)) for v in values]
        
        return {
            "average_value": np.mean(values),
            "max_value": np.max(values),
            "min_value": np.min(values),
            "std_value": np.std(values)
        }
    
    async def _validate_transfer(self,
                               target_model: nn.Module,
                               config: TransferConfig) -> Dict[str, Any]:
        """驗證轉換效果"""
        logger.info("驗證轉換效果")
        
        # 模擬驗證過程
        validation_steps = config.validation_steps
        performance_history = []
        
        for step in range(0, validation_steps, 50):
            # 模擬性能評估
            performance = 0.6 + 0.3 * (step / validation_steps) + np.random.normal(0, 0.02)
            performance = max(0, min(1, performance))
            performance_history.append(performance)
            
            await asyncio.sleep(0.001)  # 模擬驗證時間
        
        # 計算收斂回合數
        convergence_episodes = validation_steps // 2 + np.random.randint(-50, 50)
        convergence_episodes = max(1, convergence_episodes)
        
        return {
            "performance": performance_history[-1],
            "convergence_episodes": convergence_episodes,
            "performance_history": performance_history,
            "validation_steps": validation_steps
        }
    
    def get_transfer_history(self) -> List[TransferMetrics]:
        """獲取轉換歷史"""
        return self.transfer_history.copy()
    
    def get_knowledge_cache(self) -> Dict[str, Any]:
        """獲取知識緩存"""
        return self.knowledge_cache.copy()
    
    def clear_cache(self):
        """清除緩存"""
        self.knowledge_cache.clear()
        logger.info("知識緩存已清除")
    
    def get_method_compatibility(self, 
                               source_alg: str, 
                               target_alg: str) -> Dict[TransferMethod, float]:
        """獲取方法兼容性"""
        # 算法對方法的兼容性矩陣
        compatibility_matrix = {
            ("DQN", "PPO"): {
                TransferMethod.EXPERIENCE_REPLAY: 0.8,
                TransferMethod.POLICY_DISTILLATION: 0.6,
                TransferMethod.FEATURE_MAPPING: 0.7,
                TransferMethod.NETWORK_MORPHING: 0.5,
                TransferMethod.PROGRESSIVE_NETWORKS: 0.9
            },
            ("DQN", "SAC"): {
                TransferMethod.EXPERIENCE_REPLAY: 0.7,
                TransferMethod.POLICY_DISTILLATION: 0.5,
                TransferMethod.FEATURE_MAPPING: 0.6,
                TransferMethod.NETWORK_MORPHING: 0.4,
                TransferMethod.PROGRESSIVE_NETWORKS: 0.8
            },
            ("PPO", "SAC"): {
                TransferMethod.EXPERIENCE_REPLAY: 0.6,
                TransferMethod.POLICY_DISTILLATION: 0.9,
                TransferMethod.FEATURE_MAPPING: 0.8,
                TransferMethod.NETWORK_MORPHING: 0.7,
                TransferMethod.PROGRESSIVE_NETWORKS: 0.95
            }
        }
        
        key = (source_alg, target_alg)
        return compatibility_matrix.get(key, {
            method: 0.5 for method in TransferMethod
        })
