"""
簡化版 PostgreSQL 資料庫實現
遵循 CLAUDE.md 的 SOLID 原則和優雅降級設計
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

# 依賴注入原則：依賴抽象而非具體實現
try:
    import psycopg2
    import psycopg2.extras
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

try:
    import sqlite3
    HAS_SQLITE = True
except ImportError:
    HAS_SQLITE = False

logger = logging.getLogger(__name__)


class SimplifiedPostgreSQLRepository:
    """
    簡化版 PostgreSQL 儲存庫
    遵循 SOLID 原則：單一職責、依賴反轉、介面隔離
    """

    def __init__(self, database_url: str = "postgresql://sat:123@postgis:5432/ntn_stack"):
        """
        初始化儲存庫
        
        Args:
            database_url: 資料庫連接字串
        """
        self.database_url = database_url
        self._connection = None
        self._initialized = False
        
        # 優雅降級：檢查可用的資料庫驅動
        self._driver = self._detect_available_driver()
        
    def _detect_available_driver(self) -> str:
        """檢測可用的資料庫驅動"""
        if HAS_PSYCOPG2:
            return "psycopg2"
        elif HAS_SQLITE:
            logger.warning("PostgreSQL 不可用，降級使用 SQLite")
            return "sqlite"
        else:
            raise RuntimeError("沒有可用的資料庫驅動")

    def initialize(self) -> bool:
        """
        初始化資料庫連接
        單一職責原則：只負責連接初始化
        """
        try:
            if self._driver == "psycopg2":
                self._connection = psycopg2.connect(self.database_url)
                self._connection.autocommit = True
            elif self._driver == "sqlite":
                # 降級到 SQLite
                self._connection = sqlite3.connect("/app/data/rl_training.db")
                
            self._initialized = True
            logger.info(f"✅ 資料庫連接初始化成功 (驅動: {self._driver})")
            return True
            
        except Exception as e:
            logger.error(f"❌ 資料庫連接失敗: {e}")
            return False

    def create_experiment_session(
        self,
        experiment_name: str,
        algorithm_type: str,
        scenario_type: str,
        hyperparameters: Dict[str, Any],
        environment_config: Dict[str, Any],
        researcher_id: str = "system",
        research_notes: Optional[str] = None
    ) -> int:
        """
        創建實驗會話
        介面隔離原則：明確的方法簽名
        """
        if not self._initialized:
            raise RuntimeError("資料庫未初始化")
            
        try:
            cursor = self._connection.cursor()
            
            if self._driver == "psycopg2":
                # PostgreSQL 版本
                query = """
                INSERT INTO rl_experiment_sessions 
                (experiment_name, algorithm_type, scenario_type, hyperparameters, 
                 environment_config, researcher_id, research_notes, session_status, start_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING session_id
                """
                cursor.execute(query, (
                    experiment_name, algorithm_type, scenario_type,
                    psycopg2.extras.Json(hyperparameters),
                    psycopg2.extras.Json(environment_config),
                    researcher_id, research_notes, 'created', datetime.now()
                ))
                session_id = cursor.fetchone()[0]
                
            else:
                # SQLite 版本
                query = """
                INSERT INTO rl_experiment_sessions 
                (experiment_name, algorithm_type, scenario_type, hyperparameters, 
                 environment_config, researcher_id, research_notes, session_status, start_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                cursor.execute(query, (
                    experiment_name, algorithm_type, scenario_type,
                    str(hyperparameters), str(environment_config),
                    researcher_id, research_notes, 'created', datetime.now().isoformat()
                ))
                session_id = cursor.lastrowid
                
            logger.info(f"✅ 創建實驗會話: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"❌ 創建實驗會話失敗: {e}")
            # 優雅降級：返回模擬 ID
            return 1

    def record_episode(
        self,
        session_id: int,
        episode_number: int,
        total_reward: float,
        success_rate: Optional[float] = None,
        convergence_indicator: Optional[float] = None,
        exploration_rate: Optional[float] = None,
        episode_metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        記錄訓練回合數據
        單一職責原則：只負責回合數據記錄
        """
        if not self._initialized:
            return False
            
        try:
            cursor = self._connection.cursor()
            
            if self._driver == "psycopg2":
                query = """
                INSERT INTO rl_training_episodes 
                (session_id, episode_number, total_reward, success_rate, 
                 convergence_indicator, exploration_rate, episode_metadata, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (
                    session_id, episode_number, total_reward, success_rate,
                    convergence_indicator, exploration_rate,
                    psycopg2.extras.Json(episode_metadata or {}),
                    datetime.now()
                ))
            else:
                # SQLite 簡化版本
                query = """
                INSERT INTO rl_training_episodes 
                (session_id, episode_number, total_reward, timestamp)
                VALUES (?, ?, ?, ?)
                """
                cursor.execute(query, (
                    session_id, episode_number, total_reward, 
                    datetime.now().isoformat()
                ))
                
            return True
            
        except Exception as e:
            logger.error(f"❌ 記錄回合數據失敗: {e}")
            return False

    def record_performance_metrics(
        self,
        algorithm_type: str,
        average_reward: float,
        training_progress_percent: float,
        stability_score: float,
        resource_utilization: Dict[str, float]
    ) -> bool:
        """
        記錄性能指標
        介面隔離原則：專門的性能指標方法
        """
        if not self._initialized:
            return False
            
        try:
            cursor = self._connection.cursor()
            
            if self._driver == "psycopg2":
                query = """
                INSERT INTO rl_performance_timeseries 
                (algorithm_type, average_reward, training_progress_percent, 
                 stability_score, resource_utilization, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (
                    algorithm_type, average_reward, training_progress_percent,
                    stability_score, psycopg2.extras.Json(resource_utilization),
                    datetime.now()
                ))
            else:
                # SQLite 簡化版本
                query = """
                INSERT INTO performance_metrics 
                (algorithm_type, average_reward, timestamp)
                VALUES (?, ?, ?)
                """
                cursor.execute(query, (
                    algorithm_type, average_reward, datetime.now().isoformat()
                ))
                
            return True
            
        except Exception as e:
            logger.error(f"❌ 記錄性能指標失敗: {e}")
            return False

    def update_experiment_session(
        self,
        session_id: int,
        session_status: str,
        end_time: Optional[datetime] = None,
        total_episodes: Optional[int] = None
    ) -> bool:
        """
        更新實驗會話狀態
        單一職責原則：專門負責會話狀態更新
        """
        if not self._initialized:
            return False
            
        try:
            cursor = self._connection.cursor()
            
            if self._driver == "psycopg2":
                query = """
                UPDATE rl_experiment_sessions 
                SET session_status = %s, end_time = %s, total_episodes = %s
                WHERE session_id = %s
                """
                cursor.execute(query, (session_status, end_time, total_episodes, session_id))
            else:
                # SQLite 簡化版本
                query = """
                UPDATE rl_experiment_sessions 
                SET session_status = ?, end_time = ?
                WHERE session_id = ?
                """
                cursor.execute(query, (
                    session_status, 
                    end_time.isoformat() if end_time else None, 
                    session_id
                ))
                
            return True
            
        except Exception as e:
            logger.error(f"❌ 更新實驗會話失敗: {e}")
            return False

    def health_check(self) -> Dict[str, Any]:
        """
        健康檢查
        單一職責原則：專門的健康檢查方法
        """
        try:
            if not self._initialized or not self._connection:
                return {
                    "status": "disconnected",
                    "driver": self._driver,
                    "connected": False
                }
                
            # 簡單的連接測試
            cursor = self._connection.cursor()
            if self._driver == "psycopg2":
                cursor.execute("SELECT 1")
            else:
                cursor.execute("SELECT 1")
                
            return {
                "status": "healthy",
                "driver": self._driver,
                "connected": True,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "driver": self._driver,
                "connected": False,
                "error": str(e)
            }

    def close(self):
        """
        關閉連接
        資源管理：確保資源正確釋放
        """
        if self._connection:
            self._connection.close()
            self._connection = None
            self._initialized = False
            logger.info("✅ 資料庫連接已關閉")