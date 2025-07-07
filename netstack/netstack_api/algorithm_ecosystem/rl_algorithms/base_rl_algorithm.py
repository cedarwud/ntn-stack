"""
🤖 基礎強化學習算法

為強化學習換手算法提供通用的基礎實現。
"""

import logging
import numpy as np
from abc import abstractmethod
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import torch
import torch.nn as nn
from pathlib import Path

try:
    import gymnasium as gym
    GYMNASIUM_AVAILABLE = True
except ImportError:
    GYMNASIUM_AVAILABLE = False

from ..interfaces import (
    RLHandoverAlgorithm,
    HandoverContext,
    HandoverDecision,
    AlgorithmInfo,
    AlgorithmType,
    HandoverDecisionType,
    GeoCoordinate,
    SignalMetrics
)

logger = logging.getLogger(__name__)


class BaseRLHandoverAlgorithm(RLHandoverAlgorithm):
    """強化學習換手算法基類
    
    提供 RL 算法的通用功能，包括：
    - 上下文轉換
    - 模型管理
    - 訓練監控
    - 決策後處理
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """初始化 RL 算法
        
        Args:
            name: 算法名稱
            config: 算法配置
        """
        super().__init__(name, config)
        
        # 模型相關
        self.model: Optional[nn.Module] = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_path: Optional[str] = None
        self.is_trained = False
        
        # 訓練相關
        self.training_config = config.get('training_config', {}) if config else {}
        self.inference_config = config.get('inference_config', {}) if config else {}
        
        # 環境適配
        self.observation_dim = config.get('observation_dim', 54) if config else 54  # 預設觀察維度
        self.action_dim = config.get('action_dim', 11) if config else 11  # 預設動作維度
        
        # 性能統計
        self._rl_statistics = {
            'total_predictions': 0,
            'average_confidence': 0.0,
            'model_inference_time': 0.0,
            'last_model_update': None,
            'training_episodes': 0,
            'best_reward': -float('inf')
        }
        
        logger.info(f"RL 算法 '{name}' 初始化完成，設備: {self.device}")
    
    async def _initialize_algorithm(self) -> None:
        """初始化算法特定邏輯"""
        # 創建模型
        await self._create_model()
        
        # 載入預訓練模型（如果存在）
        model_path = self.config.get('model_path')
        if model_path and Path(model_path).exists():
            try:
                await self.load_model(model_path)
                logger.info(f"載入預訓練模型: {model_path}")
            except Exception as e:
                logger.warning(f"載入預訓練模型失敗: {e}")
    
    @abstractmethod
    async def _create_model(self) -> None:
        """創建神經網路模型 - 子類必須實現"""
        pass
    
    @abstractmethod
    async def _forward_pass(self, observation: torch.Tensor) -> torch.Tensor:
        """模型前向傳播 - 子類必須實現
        
        Args:
            observation: 觀察張量
            
        Returns:
            torch.Tensor: 模型輸出
        """
        pass
    
    async def predict_handover(self, context: HandoverContext) -> HandoverDecision:
        """執行換手預測
        
        Args:
            context: 換手上下文
            
        Returns:
            HandoverDecision: 換手決策
        """
        try:
            if not self.model:
                logger.error("模型未初始化")
                return self._create_fallback_decision(context, "Model not initialized")
            
            # 轉換上下文為觀察
            observation = self._context_to_observation(context)
            
            # 執行模型推理
            start_time = datetime.now()
            decision_tensor = await self._forward_pass(observation)
            inference_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # 轉換模型輸出為決策
            decision = self._tensor_to_decision(decision_tensor, context)
            decision.algorithm_name = self.name
            decision.decision_time = inference_time
            
            # 更新統計信息
            self._update_rl_statistics(decision, inference_time)
            
            return decision
            
        except Exception as e:
            logger.error(f"RL 預測失敗: {e}")
            return self._create_fallback_decision(context, f"Prediction error: {str(e)}")
    
    def _context_to_observation(self, context: HandoverContext) -> torch.Tensor:
        """將 HandoverContext 轉換為觀察張量
        
        Args:
            context: 換手上下文
            
        Returns:
            torch.Tensor: 觀察張量
        """
        try:
            # 初始化觀察向量
            observation = np.zeros(self.observation_dim)
            
            # UE 特徵 (位置和速度)
            observation[0] = context.ue_location.latitude / 90.0  # 正規化緯度
            observation[1] = context.ue_location.longitude / 180.0  # 正規化經度
            
            if context.ue_velocity:
                observation[2] = np.clip(context.ue_velocity.latitude / 100.0, -1, 1)  # 速度正規化
                observation[3] = np.clip(context.ue_velocity.longitude / 100.0, -1, 1)
            
            # 當前衛星特徵
            if context.current_satellite and context.current_signal_metrics:
                observation[4] = 1.0  # 有當前衛星
                observation[5] = np.clip(context.current_signal_metrics.rsrp / 50.0 + 2, 0, 1)  # RSRP 正規化
                observation[6] = np.clip(context.current_signal_metrics.rsrq / 20.0 + 1, 0, 1)  # RSRQ 正規化
                observation[7] = np.clip(context.current_signal_metrics.sinr / 30.0, 0, 1)  # SINR 正規化
                observation[8] = np.clip(context.current_signal_metrics.throughput / 1000.0, 0, 1)  # 吞吐量正規化
                observation[9] = np.clip(1.0 - context.current_signal_metrics.latency / 1000.0, 0, 1)  # 延遲正規化（反向）
            
            # 候選衛星特徵 (最多 10 個衛星)
            max_satellites = min(len(context.candidate_satellites), 10)
            for i, satellite in enumerate(context.candidate_satellites[:max_satellites]):
                start_idx = 10 + i * 4
                
                observation[start_idx] = 1.0  # 衛星存在
                observation[start_idx + 1] = satellite.position.latitude / 90.0
                observation[start_idx + 2] = satellite.position.longitude / 180.0
                
                if satellite.signal_metrics:
                    observation[start_idx + 3] = np.clip(satellite.signal_metrics.sinr / 30.0, 0, 1)
            
            # 網路狀態特徵
            network_start = 50
            network_state = context.network_state or {}
            observation[network_start] = np.clip(network_state.get('network_load', 0.0), 0, 1)
            observation[network_start + 1] = np.clip(network_state.get('interference_level', 0.0), 0, 1)
            observation[network_start + 2] = np.clip(network_state.get('total_ues', 0) / 1000.0, 0, 1)
            observation[network_start + 3] = np.clip(network_state.get('active_satellites', 0) / 20.0, 0, 1)
            
            # 轉換為 PyTorch 張量
            return torch.FloatTensor(observation).unsqueeze(0).to(self.device)
            
        except Exception as e:
            logger.error(f"上下文轉換失敗: {e}")
            # 返回零向量
            return torch.zeros((1, self.observation_dim)).to(self.device)
    
    def _tensor_to_decision(self, tensor: torch.Tensor, context: HandoverContext) -> HandoverDecision:
        """將模型輸出張量轉換為 HandoverDecision
        
        Args:
            tensor: 模型輸出張量
            context: 原始上下文
            
        Returns:
            HandoverDecision: 換手決策
        """
        try:
            # 假設模型輸出是 [no_handover, immediate_handover, prepare_handover, satellite_probs...]
            output = tensor.cpu().numpy().flatten()
            
            # 決策類型概率
            decision_probs = output[:3]
            decision_type_idx = np.argmax(decision_probs)
            confidence = float(np.max(decision_probs))
            
            # 映射決策類型
            decision_type_map = {
                0: HandoverDecisionType.NO_HANDOVER,
                1: HandoverDecisionType.IMMEDIATE_HANDOVER,
                2: HandoverDecisionType.PREPARE_HANDOVER
            }
            decision_type = decision_type_map.get(decision_type_idx, HandoverDecisionType.NO_HANDOVER)
            
            # 如果需要換手，選擇目標衛星
            target_satellite = None
            if decision_type != HandoverDecisionType.NO_HANDOVER and context.candidate_satellites:
                if len(output) > 3:
                    # 使用模型輸出的衛星概率
                    satellite_probs = output[3:3+len(context.candidate_satellites)]
                    best_satellite_idx = np.argmax(satellite_probs)
                    target_satellite = context.candidate_satellites[best_satellite_idx].satellite_id
                else:
                    # 使用信號強度選擇最佳衛星
                    best_satellite = max(
                        context.candidate_satellites,
                        key=lambda s: s.signal_metrics.sinr if s.signal_metrics else -float('inf')
                    )
                    target_satellite = best_satellite.satellite_id
            
            return HandoverDecision(
                target_satellite=target_satellite,
                handover_decision=decision_type,
                confidence=confidence,
                timing=datetime.now() if decision_type != HandoverDecisionType.NO_HANDOVER else None,
                decision_reason=f"RL decision: {decision_type.name} (confidence: {confidence:.3f})",
                algorithm_name=self.name,
                decision_time=0.0,  # 將由調用者設置
                metadata={
                    'decision_probs': decision_probs.tolist(),
                    'model_output_shape': tensor.shape,
                    'device': str(self.device)
                }
            )
            
        except Exception as e:
            logger.error(f"張量轉決策失敗: {e}")
            return self._create_fallback_decision(context, f"Tensor conversion error: {str(e)}")
    
    def _create_fallback_decision(self, context: HandoverContext, reason: str) -> HandoverDecision:
        """創建回退決策
        
        Args:
            context: 上下文
            reason: 回退原因
            
        Returns:
            HandoverDecision: 回退決策
        """
        return HandoverDecision(
            target_satellite=None,
            handover_decision=HandoverDecisionType.NO_HANDOVER,
            confidence=0.1,
            timing=None,
            decision_reason=f"Fallback: {reason}",
            algorithm_name=self.name,
            decision_time=0.0,
            metadata={'fallback': True, 'error': reason}
        )
    
    def _update_rl_statistics(self, decision: HandoverDecision, inference_time: float) -> None:
        """更新 RL 統計信息
        
        Args:
            decision: 決策結果
            inference_time: 推理時間
        """
        self._rl_statistics['total_predictions'] += 1
        
        # 更新平均信心度
        total_predictions = self._rl_statistics['total_predictions']
        prev_avg_confidence = self._rl_statistics['average_confidence']
        self._rl_statistics['average_confidence'] = (
            (prev_avg_confidence * (total_predictions - 1) + decision.confidence) / total_predictions
        )
        
        # 更新推理時間
        self._rl_statistics['model_inference_time'] = inference_time
    
    async def load_model(self, model_path: str) -> None:
        """載入訓練好的模型
        
        Args:
            model_path: 模型檔案路徑
        """
        try:
            if not self.model:
                await self._create_model()
            
            checkpoint = torch.load(model_path, map_location=self.device)
            
            if isinstance(checkpoint, dict):
                if 'model_state_dict' in checkpoint:
                    self.model.load_state_dict(checkpoint['model_state_dict'])
                    self._rl_statistics['training_episodes'] = checkpoint.get('episodes', 0)
                    self._rl_statistics['best_reward'] = checkpoint.get('best_reward', -float('inf'))
                else:
                    self.model.load_state_dict(checkpoint)
            else:
                self.model.load_state_dict(checkpoint)
            
            self.model.eval()
            self.model_path = model_path
            self.is_trained = True
            self._rl_statistics['last_model_update'] = datetime.now().isoformat()
            
            logger.info(f"模型載入成功: {model_path}")
            
        except Exception as e:
            logger.error(f"模型載入失敗: {e}")
            raise
    
    async def save_model(self, model_path: str) -> None:
        """保存模型
        
        Args:
            model_path: 模型保存路徑
        """
        try:
            if not self.model:
                raise ValueError("模型未初始化")
            
            # 確保目錄存在
            Path(model_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 保存模型和訓練信息
            checkpoint = {
                'model_state_dict': self.model.state_dict(),
                'episodes': self._rl_statistics['training_episodes'],
                'best_reward': self._rl_statistics['best_reward'],
                'config': self.config,
                'algorithm_name': self.name,
                'saved_at': datetime.now().isoformat()
            }
            
            torch.save(checkpoint, model_path)
            self.model_path = model_path
            self._rl_statistics['last_model_update'] = datetime.now().isoformat()
            
            logger.info(f"模型保存成功: {model_path}")
            
        except Exception as e:
            logger.error(f"模型保存失敗: {e}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """獲取模型信息
        
        Returns:
            Dict[str, Any]: 模型元數據
        """
        model_info = {
            'model_type': self.__class__.__name__,
            'device': str(self.device),
            'is_trained': self.is_trained,
            'model_path': self.model_path,
            'observation_dim': self.observation_dim,
            'action_dim': self.action_dim,
            'parameters_count': sum(p.numel() for p in self.model.parameters()) if self.model else 0,
            'training_config': self.training_config,
            'inference_config': self.inference_config,
            'statistics': self._rl_statistics
        }
        
        if self.model:
            model_info['model_architecture'] = str(self.model)
        
        return model_info
    
    def get_algorithm_info(self) -> AlgorithmInfo:
        """獲取算法信息"""
        return AlgorithmInfo(
            name=self.name,
            version="1.0.0-rl",
            algorithm_type=AlgorithmType.REINFORCEMENT_LEARNING,
            description=f"強化學習換手算法: {self.__class__.__name__}",
            parameters={
                **self.config,
                'model_info': self.get_model_info()
            },
            author="RL Implementation",
            created_at=datetime.now(),
            performance_metrics={
                'average_confidence': self._rl_statistics['average_confidence'],
                'total_predictions': self._rl_statistics['total_predictions'],
                'model_inference_time_ms': self._rl_statistics['model_inference_time']
            },
            supported_scenarios=["urban", "suburban", "complex", "dynamic"]
        )