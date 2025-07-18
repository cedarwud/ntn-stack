"""
研究級數據庫服務

專門處理學術研究和訓練追蹤的高級數據操作
支援複雜查詢、統計分析和數據匯出功能
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
import pymongo
from bson import ObjectId
import pandas as pd
import numpy as np
from dataclasses import asdict

from ..models.research_models import (
    RLExperimentSession,
    RLTrainingEpisode, 
    RLDecisionAnalysis,
    RLPerformanceMetrics,
    ResearchDataExport,
    RESEARCH_COLLECTIONS,
    RESEARCH_INDEXES,
    ExperimentStatus,
    AlgorithmType,
    ScenarioType
)

logger = logging.getLogger(__name__)


class ResearchDatabaseService:
    """
    研究級數據庫服務
    
    提供學術研究所需的高級數據管理功能
    """
    
    def __init__(self, mongo_url: str = "mongodb://netstack-mongo:27017", db_name: str = "netstack_research"):
        self.mongo_url = mongo_url
        self.db_name = db_name
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.collections: Dict[str, AsyncIOMotorCollection] = {}
        self.is_connected = False
        
    async def connect(self) -> bool:
        """連接到MongoDB"""
        try:
            self.client = AsyncIOMotorClient(self.mongo_url)
            self.db = self.client[self.db_name]
            
            # 初始化集合
            for collection_name in RESEARCH_COLLECTIONS.keys():
                self.collections[collection_name] = self.db[collection_name]
            
            # 創建索引
            await self._create_indexes()
            
            # 測試連接
            await self.client.admin.command('ping')
            
            self.is_connected = True
            logger.info(f"研究級數據庫連接成功: {self.db_name}")
            return True
            
        except Exception as e:
            logger.error(f"研究級數據庫連接失敗: {e}")
            return False
    
    async def disconnect(self):
        """斷開數據庫連接"""
        if self.client:
            self.client.close()
            self.is_connected = False
            logger.info("研究級數據庫連接已關閉")
    
    async def _create_indexes(self):
        """創建數據庫索引"""
        try:
            for collection_name, indexes in RESEARCH_INDEXES.items():
                collection = self.collections[collection_name]
                for index in indexes:
                    await collection.create_index(list(index.items()))
            
            logger.info("研究級數據庫索引創建完成")
            
        except Exception as e:
            logger.error(f"創建數據庫索引失敗: {e}")
    
    # === 訓練會話管理 ===
    
    async def create_experiment_session(self, session_data: RLExperimentSession) -> str:
        """創建新的訓練會話"""
        try:
            session_dict = session_data.dict()
            session_dict["created_at"] = datetime.now()
            session_dict["updated_at"] = datetime.now()
            
            result = await self.collections["rl_experiment_sessions"].insert_one(session_dict)
            
            logger.info(f"訓練會話創建成功: {session_data.session_id}")
            return session_data.session_id
            
        except Exception as e:
            logger.error(f"創建訓練會話失敗: {e}")
            raise
    
    async def update_experiment_session(self, session_id: str, update_data: Dict[str, Any]) -> bool:
        """更新訓練會話"""
        try:
            update_data["updated_at"] = datetime.now()
            
            result = await self.collections["rl_experiment_sessions"].update_one(
                {"session_id": session_id},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"更新訓練會話失敗: {e}")
            return False
    
    async def get_experiment_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """獲取訓練會話"""
        try:
            session = await self.collections["rl_experiment_sessions"].find_one(
                {"session_id": session_id}
            )
            return session
            
        except Exception as e:
            logger.error(f"獲取訓練會話失敗: {e}")
            return None
    
    async def list_experiment_sessions(
        self, 
        researcher: Optional[str] = None,
        algorithm_type: Optional[AlgorithmType] = None,
        status: Optional[ExperimentStatus] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """列出訓練會話"""
        try:
            query = {}
            if researcher:
                query["research_metadata.researcher"] = researcher
            if algorithm_type:
                query["algorithm_type"] = algorithm_type.value
            if status:
                query["status"] = status.value
            
            cursor = self.collections["rl_experiment_sessions"].find(query).sort("created_at", -1).limit(limit)
            sessions = await cursor.to_list(length=limit)
            
            return sessions
            
        except Exception as e:
            logger.error(f"列出訓練會話失敗: {e}")
            return []
    
    # === Episode 數據管理 ===
    
    async def save_training_episode(self, episode_data: RLTrainingEpisode) -> str:
        """保存訓練 episode 數據"""
        try:
            episode_dict = episode_data.dict()
            episode_dict["timestamp"] = datetime.now()
            
            result = await self.collections["rl_training_episodes"].insert_one(episode_dict)
            
            # 更新會話統計
            await self._update_session_statistics(episode_data.session_id, episode_data)
            
            return episode_data.episode_id
            
        except Exception as e:
            logger.error(f"保存訓練 episode 失敗: {e}")
            raise
    
    async def get_session_episodes(
        self, 
        session_id: str, 
        start_episode: Optional[int] = None,
        end_episode: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """獲取會話的 episode 數據"""
        try:
            query = {"session_id": session_id}
            
            if start_episode is not None or end_episode is not None:
                query["episode_number"] = {}
                if start_episode is not None:
                    query["episode_number"]["$gte"] = start_episode
                if end_episode is not None:
                    query["episode_number"]["$lte"] = end_episode
            
            cursor = self.collections["rl_training_episodes"].find(query).sort("episode_number", 1)
            episodes = await cursor.to_list(length=None)
            
            return episodes
            
        except Exception as e:
            logger.error(f"獲取會話 episodes 失敗: {e}")
            return []
    
    # === 決策分析數據 ===
    
    async def save_decision_analysis(self, decision_data: RLDecisionAnalysis) -> str:
        """保存決策分析數據"""
        try:
            decision_dict = decision_data.dict()
            decision_dict["timestamp"] = datetime.now()
            
            result = await self.collections["rl_decision_analysis"].insert_one(decision_dict)
            
            return decision_data.decision_id
            
        except Exception as e:
            logger.error(f"保存決策分析失敗: {e}")
            raise
    
    async def get_decision_analysis(
        self, 
        session_id: str,
        episode_number: Optional[int] = None,
        confidence_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """獲取決策分析數據"""
        try:
            query = {"session_id": session_id}
            
            if episode_number is not None:
                query["episode_number"] = episode_number
                
            if confidence_threshold is not None:
                query["decision_reasoning.confidence_level"] = {"$gte": confidence_threshold}
            
            cursor = self.collections["rl_decision_analysis"].find(query).sort("timestamp", 1)
            decisions = await cursor.to_list(length=None)
            
            return decisions
            
        except Exception as e:
            logger.error(f"獲取決策分析失敗: {e}")
            return []
    
    # === 性能指標分析 ===
    
    async def calculate_performance_metrics(
        self, 
        session_id: str, 
        window_size: int = 100
    ) -> Optional[RLPerformanceMetrics]:
        """計算性能指標"""
        try:
            # 獲取最近的 episodes
            episodes = await self.get_session_episodes(session_id)
            
            if len(episodes) < window_size:
                window_size = len(episodes)
            
            if window_size == 0:
                return None
            
            recent_episodes = episodes[-window_size:]
            
            # 計算基本統計
            rewards = [ep["total_reward"] for ep in recent_episodes]
            handover_latencies = []
            throughputs = []
            success_rates = []
            
            for ep in recent_episodes:
                if "avg_handover_latency" in ep:
                    handover_latencies.append(ep["avg_handover_latency"])
                if "avg_throughput" in ep:
                    throughputs.append(ep["avg_throughput"])
                if "success_rate" in ep:
                    success_rates.append(ep["success_rate"])
            
            # 創建性能指標對象
            metrics = RLPerformanceMetrics(
                session_id=session_id,
                window_start_episode=recent_episodes[0]["episode_number"],
                window_end_episode=recent_episodes[-1]["episode_number"],
                episodes_in_window=window_size,
                
                # 獎勵統計
                avg_reward=float(np.mean(rewards)),
                reward_std=float(np.std(rewards)),
                max_reward=float(np.max(rewards)),
                min_reward=float(np.min(rewards)),
                
                # 切換性能
                avg_handover_success_rate=float(np.mean(success_rates)) if success_rates else 0.0,
                avg_handover_latency_ms=float(np.mean(handover_latencies)) if handover_latencies else 0.0,
                handover_efficiency_score=float(np.mean(success_rates)) if success_rates else 0.0,
                
                # 網路性能
                avg_throughput_mbps=float(np.mean(throughputs)) if throughputs else 0.0,
                avg_connection_stability=0.8,  # 簡化計算
                network_utilization_efficiency=0.75,  # 簡化計算
                
                # 學習進度
                convergence_indicator=self._calculate_convergence_indicator(rewards),
                learning_stability_score=1.0 / (1.0 + np.std(rewards)) if len(rewards) > 1 else 1.0,
                exploration_exploitation_ratio=0.5,  # 簡化計算
                
                # 改善指標
                improvement_over_random=float(np.mean(rewards)) / 10.0,  # 假設隨機策略平均獎勵為 10
            )
            
            # 保存性能指標
            await self.save_performance_metrics(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"計算性能指標失敗: {e}")
            return None
    
    async def save_performance_metrics(self, metrics: RLPerformanceMetrics) -> str:
        """保存性能指標"""
        try:
            metrics_dict = metrics.dict()
            metrics_dict["calculated_at"] = datetime.now()
            
            result = await self.collections["rl_performance_metrics"].insert_one(metrics_dict)
            
            return metrics.metric_id
            
        except Exception as e:
            logger.error(f"保存性能指標失敗: {e}")
            raise
    
    # === 數據匯出和分析 ===
    
    async def export_session_data(
        self, 
        session_id: str, 
        export_format: str = "JSON",
        include_analysis: bool = True
    ) -> Optional[ResearchDataExport]:
        """匯出會話數據"""
        try:
            # 獲取會話數據
            session = await self.get_experiment_session(session_id)
            if not session:
                return None
            
            # 獲取 episodes
            episodes = await self.get_session_episodes(session_id)
            
            # 獲取決策分析
            decisions = await self.get_decision_analysis(session_id) if include_analysis else []
            
            # 計算數據統計
            export_data = ResearchDataExport(
                session_id=session_id,
                export_format=export_format,
                include_analysis=include_analysis,
                total_episodes=len(episodes),
                total_decisions=len(decisions),
                data_size_mb=0.0,  # 簡化計算
                data_integrity_hash="placeholder_hash"  # 簡化實現
            )
            
            # 保存匯出記錄
            export_dict = export_data.dict()
            await self.collections["research_data_exports"].insert_one(export_dict)
            
            return export_data
            
        except Exception as e:
            logger.error(f"匯出會話數據失敗: {e}")
            return None
    
    async def get_comparative_analysis(
        self, 
        session_ids: List[str], 
        metric: str = "avg_reward"
    ) -> Dict[str, Any]:
        """獲取比較分析"""
        try:
            analysis_results = {}
            
            for session_id in session_ids:
                episodes = await self.get_session_episodes(session_id)
                
                if metric == "avg_reward":
                    values = [ep["total_reward"] for ep in episodes]
                elif metric == "success_rate":
                    values = [ep.get("success_rate", 0.0) for ep in episodes]
                else:
                    values = []
                
                if values:
                    analysis_results[session_id] = {
                        "mean": float(np.mean(values)),
                        "std": float(np.std(values)),
                        "min": float(np.min(values)),
                        "max": float(np.max(values)),
                        "episodes": len(values)
                    }
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"比較分析失敗: {e}")
            return {}
    
    # === 輔助方法 ===
    
    async def _update_session_statistics(self, session_id: str, episode_data: RLTrainingEpisode):
        """更新會話統計信息"""
        try:
            update_data = {
                "completed_episodes": episode_data.episode_number,
                "current_avg_reward": episode_data.total_reward,
                "updated_at": datetime.now()
            }
            
            # 檢查是否是最佳獎勵
            session = await self.get_experiment_session(session_id)
            if session and episode_data.total_reward > session.get("best_avg_reward", float('-inf')):
                update_data["best_avg_reward"] = episode_data.total_reward
            
            await self.update_experiment_session(session_id, update_data)
            
        except Exception as e:
            logger.error(f"更新會話統計失敗: {e}")
    
    def _calculate_convergence_indicator(self, rewards: List[float]) -> float:
        """計算收斂指標"""
        if len(rewards) < 10:
            return 0.0
        
        # 簡單的收斂指標：最近獎勵的標準差
        recent_rewards = rewards[-10:]
        std_dev = np.std(recent_rewards)
        
        # 歸一化到 0-1 範圍
        convergence = max(0.0, 1.0 - (std_dev / 100.0))
        return min(1.0, convergence)
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """獲取數據庫統計信息"""
        try:
            stats = {}
            
            for collection_name, collection in self.collections.items():
                count = await collection.count_documents({})
                stats[collection_name] = {
                    "document_count": count,
                    "estimated_size": await collection.estimated_document_count()
                }
            
            return {
                "collections": stats,
                "database": self.db_name,
                "connected": self.is_connected
            }
            
        except Exception as e:
            logger.error(f"獲取數據庫統計失敗: {e}")
            return {}


# 全局服務實例
_research_db_service = None


async def get_research_database_service() -> ResearchDatabaseService:
    """獲取研究級數據庫服務實例"""
    global _research_db_service
    
    if _research_db_service is None:
        _research_db_service = ResearchDatabaseService()
        await _research_db_service.connect()
    
    return _research_db_service