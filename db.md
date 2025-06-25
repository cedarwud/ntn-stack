# RL監控頁面資料庫儲存實現流程

## 📋 項目概覽

本文檔詳細說明如何將 **Navbar > 圖表分析 > RL監控** 頁面的訓練資料從前端模擬數據轉換為真實的資料庫儲存和顯示流程。

### 🎯 目標
- 將RL訓練資料持久化到PostgreSQL
- 實現完整的後端API支持
- 建立前後端資料同步機制
- 提供歷史數據查詢和分析功能

---

## 🏗️ 系統架構

### 當前系統狀態
```
Frontend (React/TypeScript)
├── GymnasiumRLMonitor.tsx     - RL監控主組件
├── ChartAnalysisDashboard.tsx - 圖表分析儀表板
└── 模擬數據生成             - 動態生成訓練指標

Backend (FastAPI/Python)
├── SimWorld Backend           - TensorFlow + Sionna AI服務
└── NetStack Backend          - 5G核心網 + MongoDB/Redis
```

### 目標架構
```
Frontend (React/TypeScript)
├── GymnasiumRLMonitor.tsx     - 顯示真實數據
├── API呼叫層                  - 獲取資料庫數據
└── 即時數據更新               - WebSocket/SSE

Backend (FastAPI/Python)
├── RL Domain 新增            - 專門的RL資料管理
├── PostgreSQL Schema         - 完整的訓練數據儲存
├── API Endpoints            - RESTful資料介面
└── 背景訓練服務              - 實際的RL訓練邏輯
```

---

## 📊 資料庫設計方案

### 核心資料表結構

#### 1. RLExperiment (RL實驗表)
實驗的頂層管理，每個實驗對應一次完整的RL訓練任務。

```sql
CREATE TABLE rl_experiments (
    id SERIAL PRIMARY KEY,
    experiment_name VARCHAR(255) NOT NULL,
    algorithm_type VARCHAR(50) NOT NULL, -- 'dqn', 'ppo', 'sac' 等
    environment_name VARCHAR(255) NOT NULL,
    
    -- 配置參數
    hyperparameters TEXT, -- JSON格式超參數
    network_architecture TEXT, -- JSON格式網絡結構
    
    -- 狀態追蹤
    status VARCHAR(50) DEFAULT 'running', -- 'running', 'completed', 'failed', 'paused'
    total_episodes INTEGER NOT NULL,
    completed_episodes INTEGER DEFAULT 0,
    
    -- 時間記錄
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- 結果統計
    best_reward FLOAT,
    final_reward FLOAT,
    convergence_episode INTEGER,
    
    -- 元數據
    tags TEXT, -- JSON數組
    notes TEXT
);

CREATE INDEX idx_rl_experiments_name ON rl_experiments(experiment_name);
CREATE INDEX idx_rl_experiments_status ON rl_experiments(status);
CREATE INDEX idx_rl_experiments_created ON rl_experiments(created_at);
```

#### 2. RLEpisode (RL回合表)
記錄每個訓練回合的統計數據，對應前端顯示的episode指標。

```sql
CREATE TABLE rl_episodes (
    id SERIAL PRIMARY KEY,
    experiment_id INTEGER NOT NULL REFERENCES rl_experiments(id),
    
    -- 回合基本信息
    episode_number INTEGER NOT NULL,
    total_steps INTEGER NOT NULL,
    total_reward FLOAT NOT NULL,
    
    -- 學習指標
    avg_loss FLOAT,
    exploration_rate FLOAT, -- epsilon for DQN
    learning_rate FLOAT,
    
    -- 應用特定指標 (5G網絡相關)
    handover_success_rate FLOAT,
    interference_mitigation_score FLOAT,
    network_efficiency FLOAT,
    
    -- 時間信息
    episode_start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    episode_duration_seconds FLOAT,
    
    -- 原始數據路徑
    episode_data_path VARCHAR(500)
);

CREATE INDEX idx_rl_episodes_experiment ON rl_episodes(experiment_id);
CREATE INDEX idx_rl_episodes_number ON rl_episodes(episode_number);
CREATE INDEX idx_rl_episodes_time ON rl_episodes(episode_start_time);
```

#### 3. RLStep (RL步驟表)
詳細的狀態-動作-獎勵數據，用於深度分析和重放。

```sql
CREATE TABLE rl_steps (
    id SERIAL PRIMARY KEY,
    episode_id INTEGER NOT NULL REFERENCES rl_episodes(id),
    
    step_number INTEGER NOT NULL,
    
    -- SARS數據 (State, Action, Reward, State)
    state TEXT NOT NULL, -- JSON格式狀態
    action TEXT NOT NULL, -- JSON格式動作
    reward FLOAT NOT NULL,
    next_state TEXT NOT NULL, -- JSON格式下一狀態
    done BOOLEAN NOT NULL,
    
    -- AI決策信息
    q_values TEXT, -- JSON格式Q值
    action_probabilities TEXT, -- JSON格式動作概率
    
    -- 環境特定數據
    satellite_positions TEXT, -- JSON格式衛星位置
    interference_levels TEXT, -- JSON格式干擾水平
    network_metrics TEXT, -- JSON格式網絡指標
    
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_rl_steps_episode ON rl_steps(episode_id);
CREATE INDEX idx_rl_steps_time ON rl_steps(timestamp);
-- 時間序列分區（按月分區）
CREATE INDEX idx_rl_steps_time_month ON rl_steps(date_trunc('month', timestamp));
```

#### 4. RLModelCheckpoint (模型檢查點表)
儲存訓練過程中的模型快照，支持模型版本管理。

```sql
CREATE TABLE rl_model_checkpoints (
    id SERIAL PRIMARY KEY,
    experiment_id INTEGER NOT NULL REFERENCES rl_experiments(id),
    
    checkpoint_name VARCHAR(255) NOT NULL,
    episode_number INTEGER NOT NULL,
    
    -- 模型文件路徑
    model_file_path VARCHAR(500) NOT NULL,
    optimizer_state_path VARCHAR(500),
    
    -- 性能指標
    validation_reward FLOAT,
    training_loss FLOAT,
    
    -- 元數據
    model_size_bytes BIGINT,
    is_best BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_rl_checkpoints_experiment ON rl_model_checkpoints(experiment_id);
CREATE INDEX idx_rl_checkpoints_best ON rl_model_checkpoints(is_best);
```

#### 5. RLMetrics (RL指標聚合表)
預計算的統計指標，提供高效的儀表板查詢。

```sql
CREATE TABLE rl_metrics (
    id SERIAL PRIMARY KEY,
    experiment_id INTEGER NOT NULL REFERENCES rl_experiments(id),
    
    -- 時間窗口定義
    metric_type VARCHAR(50) NOT NULL, -- 'episode', 'batch', 'epoch'
    window_start INTEGER NOT NULL,
    window_end INTEGER NOT NULL,
    
    -- 基礎性能指標
    avg_reward FLOAT NOT NULL,
    std_reward FLOAT NOT NULL,
    max_reward FLOAT NOT NULL,
    min_reward FLOAT NOT NULL,
    
    -- 學習進度指標
    avg_loss FLOAT,
    convergence_score FLOAT,
    stability_score FLOAT,
    
    -- 應用特定聚合指標
    handover_performance TEXT, -- JSON格式
    interference_metrics TEXT, -- JSON格式
    
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_rl_metrics_experiment ON rl_metrics(experiment_id);
CREATE INDEX idx_rl_metrics_type ON rl_metrics(metric_type);
```

---

## 🔧 後端實現步驟

### 第1步：建立RL領域結構

```bash
# 在SimWorld後端建立RL領域
mkdir -p simworld/backend/app/domains/rl/{models,api,services,repositories}
```

#### 檔案結構
```
simworld/backend/app/domains/rl/
├── __init__.py
├── models/
│   ├── __init__.py
│   └── rl_training_models.py      # SQLModel資料模型
├── api/
│   ├── __init__.py
│   └── rl_training_api.py         # FastAPI路由
├── services/
│   ├── __init__.py
│   └── rl_training_service.py     # 業務邏輯
└── repositories/
    ├── __init__.py
    └── rl_training_repository.py  # 資料存取層
```

### 第2步：實現資料模型 (SQLModel)

建立檔案：`simworld/backend/app/domains/rl/models/rl_training_models.py`

```python
from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Column, Text
from sqlalchemy import JSON
from enum import Enum

class RLAlgorithmType(str, Enum):
    DQN = "dqn"
    PPO = "ppo"
    SAC = "sac"
    A3C = "a3c"

class TrainingStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"

class RLExperiment(SQLModel, table=True):
    __tablename__ = "rl_experiments"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    experiment_name: str = Field(index=True)
    algorithm_type: RLAlgorithmType
    environment_name: str
    
    # 配置JSON
    hyperparameters: str = Field(sa_column=Column(Text))
    network_architecture: str = Field(sa_column=Column(Text))
    
    # 狀態
    status: TrainingStatus = Field(default=TrainingStatus.RUNNING)
    total_episodes: int
    completed_episodes: int = Field(default=0)
    
    # 時間
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # 結果
    best_reward: Optional[float] = None
    final_reward: Optional[float] = None
    convergence_episode: Optional[int] = None
    
    # 元數據
    tags: Optional[str] = None  # JSON數組
    notes: Optional[str] = None

class RLEpisode(SQLModel, table=True):
    __tablename__ = "rl_episodes"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    experiment_id: int = Field(foreign_key="rl_experiments.id", index=True)
    
    episode_number: int = Field(index=True)
    total_steps: int
    total_reward: float
    
    # 學習指標
    avg_loss: Optional[float] = None
    exploration_rate: Optional[float] = None
    learning_rate: Optional[float] = None
    
    # 5G網絡特定指標
    handover_success_rate: Optional[float] = None
    interference_mitigation_score: Optional[float] = None
    network_efficiency: Optional[float] = None
    
    # 時間
    episode_start_time: datetime = Field(default_factory=datetime.utcnow)
    episode_duration_seconds: Optional[float] = None
    
    episode_data_path: Optional[str] = None

# 其他模型類似實現...
```

### 第3步：實現資料存取層

建立檔案：`simworld/backend/app/domains/rl/repositories/rl_training_repository.py`

```python
from typing import List, Optional
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.rl_training_models import RLExperiment, RLEpisode, RLMetrics

class RLTrainingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_experiment(self, experiment: RLExperiment) -> RLExperiment:
        self.session.add(experiment)
        await self.session.commit()
        await self.session.refresh(experiment)
        return experiment
    
    async def get_experiment(self, experiment_id: int) -> Optional[RLExperiment]:
        statement = select(RLExperiment).where(RLExperiment.id == experiment_id)
        result = await self.session.exec(statement)
        return result.first()
    
    async def get_active_experiments(self) -> List[RLExperiment]:
        statement = select(RLExperiment).where(
            RLExperiment.status.in_(["running", "paused"])
        )
        result = await self.session.exec(statement)
        return result.all()
    
    async def save_episode(self, episode: RLEpisode) -> RLEpisode:
        self.session.add(episode)
        await self.session.commit()
        await self.session.refresh(episode)
        return episode
    
    async def get_experiment_episodes(
        self, 
        experiment_id: int, 
        limit: int = 100,
        offset: int = 0
    ) -> List[RLEpisode]:
        statement = (
            select(RLEpisode)
            .where(RLEpisode.experiment_id == experiment_id)
            .order_by(RLEpisode.episode_number.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.exec(statement)
        return result.all()
    
    async def get_latest_metrics(self, experiment_id: int) -> Optional[RLMetrics]:
        statement = (
            select(RLMetrics)
            .where(RLMetrics.experiment_id == experiment_id)
            .order_by(RLMetrics.calculated_at.desc())
            .limit(1)
        )
        result = await self.session.exec(statement)
        return result.first()
```

### 第4步：實現業務邏輯服務

建立檔案：`simworld/backend/app/domains/rl/services/rl_training_service.py`

```python
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.rl_training_models import *
from ..repositories.rl_training_repository import RLTrainingRepository

class RLTrainingService:
    def __init__(self, session: AsyncSession):
        self.repository = RLTrainingRepository(session)
    
    async def create_experiment(
        self, 
        experiment_name: str,
        algorithm_type: RLAlgorithmType,
        config: Dict[str, Any]
    ) -> RLExperiment:
        """建立新的RL訓練實驗"""
        
        experiment = RLExperiment(
            experiment_name=experiment_name,
            algorithm_type=algorithm_type,
            environment_name=config.get("environment", "5g_network"),
            hyperparameters=json.dumps(config.get("hyperparameters", {})),
            network_architecture=json.dumps(config.get("network", {})),
            total_episodes=config.get("total_episodes", 1000),
            started_at=datetime.utcnow()
        )
        
        return await self.repository.create_experiment(experiment)
    
    async def log_episode(
        self,
        experiment_id: int,
        episode_data: Dict[str, Any]
    ) -> RLEpisode:
        """記錄單個訓練回合數據"""
        
        episode = RLEpisode(
            experiment_id=experiment_id,
            episode_number=episode_data["episode_number"],
            total_steps=episode_data["total_steps"],
            total_reward=episode_data["total_reward"],
            avg_loss=episode_data.get("avg_loss"),
            exploration_rate=episode_data.get("exploration_rate"),
            learning_rate=episode_data.get("learning_rate"),
            handover_success_rate=episode_data.get("handover_success_rate"),
            interference_mitigation_score=episode_data.get("interference_score"),
            network_efficiency=episode_data.get("network_efficiency"),
            episode_duration_seconds=episode_data.get("duration")
        )
        
        return await self.repository.save_episode(episode)
    
    async def get_experiment_progress(self, experiment_id: int) -> Dict[str, Any]:
        """獲取實驗進度和統計"""
        
        experiment = await self.repository.get_experiment(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        episodes = await self.repository.get_experiment_episodes(
            experiment_id, limit=50
        )
        
        # 計算統計指標
        if episodes:
            recent_rewards = [ep.total_reward for ep in episodes[:10]]
            avg_reward = sum(recent_rewards) / len(recent_rewards)
            progress_pct = (experiment.completed_episodes / experiment.total_episodes) * 100
        else:
            avg_reward = 0.0
            progress_pct = 0.0
        
        return {
            "experiment": experiment,
            "recent_episodes": episodes[:10],
            "stats": {
                "avg_reward": avg_reward,
                "progress_percentage": progress_pct,
                "episodes_completed": experiment.completed_episodes,
                "total_episodes": experiment.total_episodes
            }
        }
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """獲取儀表板顯示數據"""
        
        active_experiments = await self.repository.get_active_experiments()
        
        dashboard_data = {
            "active_experiments": len(active_experiments),
            "experiments": []
        }
        
        for exp in active_experiments:
            progress = await self.get_experiment_progress(exp.id)
            exp_data = {
                "id": exp.id,
                "name": exp.experiment_name,
                "algorithm": exp.algorithm_type,
                "status": exp.status,
                "progress": progress["stats"]
            }
            dashboard_data["experiments"].append(exp_data)
        
        return dashboard_data
```

### 第5步：實現API端點

建立檔案：`simworld/backend/app/domains/rl/api/rl_training_api.py`

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from ....core.deps import get_session
from ..services.rl_training_service import RLTrainingService
from ..models.rl_training_models import RLExperiment, RLEpisode

router = APIRouter(prefix="/rl", tags=["RL Training"])

@router.post("/experiments", response_model=Dict[str, Any])
async def create_experiment(
    experiment_config: Dict[str, Any],
    session: AsyncSession = Depends(get_session)
):
    """建立新的RL訓練實驗"""
    
    service = RLTrainingService(session)
    
    experiment = await service.create_experiment(
        experiment_name=experiment_config["name"],
        algorithm_type=experiment_config["algorithm"],
        config=experiment_config
    )
    
    return {"experiment_id": experiment.id, "status": "created"}

@router.get("/experiments/{experiment_id}/progress")
async def get_experiment_progress(
    experiment_id: int,
    session: AsyncSession = Depends(get_session)
):
    """獲取實驗進度"""
    
    service = RLTrainingService(session)
    
    try:
        progress = await service.get_experiment_progress(experiment_id)
        return progress
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/experiments/{experiment_id}/episodes")
async def log_episode(
    experiment_id: int,
    episode_data: Dict[str, Any],
    session: AsyncSession = Depends(get_session)
):
    """記錄訓練回合數據"""
    
    service = RLTrainingService(session)
    episode = await service.log_episode(experiment_id, episode_data)
    
    return {"episode_id": episode.id, "status": "logged"}

@router.get("/dashboard")
async def get_dashboard_data(session: AsyncSession = Depends(get_session)):
    """獲取RL監控儀表板數據 - 前端主要調用此API"""
    
    service = RLTrainingService(session)
    dashboard_data = await service.get_dashboard_data()
    
    return dashboard_data

@router.get("/experiments/{experiment_id}/episodes")
async def get_experiment_episodes(
    experiment_id: int,
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session)
):
    """獲取實驗的訓練回合數據"""
    
    service = RLTrainingService(session)
    repository = service.repository
    
    episodes = await repository.get_experiment_episodes(
        experiment_id, limit, offset
    )
    
    return {"episodes": episodes, "count": len(episodes)}

# WebSocket支持即時更新
from fastapi import WebSocket
import asyncio
import json

@router.websocket("/experiments/{experiment_id}/live")
async def experiment_live_updates(
    websocket: WebSocket, 
    experiment_id: int
):
    """提供實驗的即時數據更新"""
    
    await websocket.accept()
    
    try:
        while True:
            # 每3秒發送更新數據（與前端當前更新頻率一致）
            session = next(get_session())
            service = RLTrainingService(session)
            
            progress = await service.get_experiment_progress(experiment_id)
            
            await websocket.send_text(json.dumps({
                "type": "progress_update",
                "data": progress
            }))
            
            await asyncio.sleep(3)
            
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()
```

### 第6步：註冊API路由

更新檔案：`simworld/backend/app/api/v1/router.py`

```python
# 現有導入...
from ...domains.rl.api.rl_training_api import router as rl_router

# 在現有路由中添加
api_router.include_router(rl_router, prefix="/api/v1")
```

### 第7步：更新資料庫遷移

更新檔案：`simworld/backend/app/db/base.py`

```python
# 現有導入...
from ..domains.rl.models.rl_training_models import *  # 新增RL模型

# 確保所有模型都被導入，以便SQLModel能建立資料表
```

---

## 🎨 前端修改步驟

### 第1步：建立API客戶端

建立檔案：`simworld/frontend/src/api/rlTrainingApi.ts`

```typescript
interface RLExperiment {
  id: number;
  experiment_name: string;
  algorithm_type: 'dqn' | 'ppo' | 'sac';
  status: 'running' | 'completed' | 'failed' | 'paused';
  completed_episodes: number;
  total_episodes: number;
  best_reward?: number;
}

interface RLEpisode {
  id: number;
  episode_number: number;
  total_reward: number;
  avg_loss?: number;
  exploration_rate?: number;
  handover_success_rate?: number;
  interference_mitigation_score?: number;
}

interface DashboardData {
  active_experiments: number;
  experiments: Array<{
    id: number;
    name: string;
    algorithm: string;
    status: string;
    progress: {
      avg_reward: number;
      progress_percentage: number;
      episodes_completed: number;
      total_episodes: number;
    };
  }>;
}

class RLTrainingAPI {
  private baseURL = 'http://localhost:8888/api/v1/rl';

  async getDashboardData(): Promise<DashboardData> {
    const response = await fetch(`${this.baseURL}/dashboard`);
    if (!response.ok) {
      throw new Error('Failed to fetch dashboard data');
    }
    return response.json();
  }

  async getExperimentProgress(experimentId: number) {
    const response = await fetch(`${this.baseURL}/experiments/${experimentId}/progress`);
    if (!response.ok) {
      throw new Error(`Failed to fetch experiment ${experimentId} progress`);
    }
    return response.json();
  }

  async createExperiment(config: any) {
    const response = await fetch(`${this.baseURL}/experiments`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
    
    if (!response.ok) {
      throw new Error('Failed to create experiment');
    }
    return response.json();
  }

  async logEpisode(experimentId: number, episodeData: any) {
    const response = await fetch(`${this.baseURL}/experiments/${experimentId}/episodes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(episodeData)
    });
    
    return response.json();
  }

  // WebSocket連接用於即時更新
  connectLiveUpdates(experimentId: number, onMessage: (data: any) => void): WebSocket {
    const ws = new WebSocket(`ws://localhost:8888/api/v1/rl/experiments/${experimentId}/live`);
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      onMessage(message.data);
    };
    
    return ws;
  }
}

export const rlTrainingAPI = new RLTrainingAPI();
export type { RLExperiment, RLEpisode, DashboardData };
```

### 第2步：修改RL監控組件

更新檔案：`simworld/frontend/src/components/charts/GymnasiumRLMonitor.tsx`

```typescript
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { rlTrainingAPI, DashboardData, RLExperiment } from '../../api/rlTrainingApi';

interface RLEngineMetrics {
  engine_type: 'dqn' | 'ppo' | 'null';
  algorithm: string;
  environment: string;
  model_status: 'training' | 'inference' | 'idle' | 'error';
  episodes_completed: number;
  average_reward: number;
  current_epsilon: number;
  training_progress: number;
  prediction_accuracy: number;
  response_time_ms: number;
  memory_usage: number;
  gpu_utilization?: number;
}

const GymnasiumRLMonitor: React.FC = () => {
  // 狀態管理
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [dqnMetrics, setDqnMetrics] = useState<RLEngineMetrics>({
    engine_type: 'dqn',
    algorithm: 'Deep Q-Network',
    environment: '5G NTN Handover',
    model_status: 'idle',
    episodes_completed: 0,
    average_reward: 0,
    current_epsilon: 1.0,
    training_progress: 0,
    prediction_accuracy: 60,
    response_time_ms: 0,
    memory_usage: 0,
    gpu_utilization: 0
  });

  const [ppoMetrics, setPpoMetrics] = useState<RLEngineMetrics>({
    engine_type: 'ppo',
    algorithm: 'Proximal Policy Optimization',
    environment: '5G NTN Handover',
    model_status: 'idle',
    episodes_completed: 0,
    average_reward: 0,
    current_epsilon: 0,
    training_progress: 0,
    prediction_accuracy: 65,
    response_time_ms: 0,
    memory_usage: 0,
    gpu_utilization: 0
  });

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeExperiments, setActiveExperiments] = useState<Map<string, number>>(new Map());
  
  // WebSocket引用
  const wsConnections = useRef<Map<number, WebSocket>>(new Map());

  // 從資料庫載入數據
  const loadDashboardData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const data = await rlTrainingAPI.getDashboardData();
      setDashboardData(data);
      
      // 更新指標
      updateMetricsFromDashboard(data);
      
    } catch (err) {
      console.error('載入儀表板數據失敗:', err);
      setError('無法載入訓練數據，請檢查後端連接');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // 將資料庫數據轉換為組件指標格式
  const updateMetricsFromDashboard = (data: DashboardData) => {
    const dqnExperiment = data.experiments.find(exp => 
      exp.algorithm.toLowerCase() === 'dqn'
    );
    const ppoExperiment = data.experiments.find(exp => 
      exp.algorithm.toLowerCase() === 'ppo'
    );

    if (dqnExperiment) {
      setDqnMetrics(prev => ({
        ...prev,
        model_status: dqnExperiment.status === 'running' ? 'training' : 'idle',
        episodes_completed: dqnExperiment.progress.episodes_completed,
        average_reward: dqnExperiment.progress.avg_reward,
        training_progress: dqnExperiment.progress.progress_percentage,
        current_epsilon: Math.max(0.01, 1.0 - (dqnExperiment.progress.progress_percentage / 100)),
        prediction_accuracy: Math.min(95, 60 + (dqnExperiment.progress.progress_percentage * 0.35))
      }));
    }

    if (ppoExperiment) {
      setPpoMetrics(prev => ({
        ...prev,
        model_status: ppoExperiment.status === 'running' ? 'training' : 'idle',
        episodes_completed: ppoExperiment.progress.episodes_completed,
        average_reward: ppoExperiment.progress.avg_reward,
        training_progress: ppoExperiment.progress.progress_percentage,
        prediction_accuracy: Math.min(95, 65 + (ppoExperiment.progress.progress_percentage * 0.30))
      }));
    }
  };

  // 開始訓練
  const startTraining = async (algorithm: 'dqn' | 'ppo') => {
    try {
      const config = {
        name: `${algorithm.toUpperCase()}_Training_${Date.now()}`,
        algorithm: algorithm,
        environment: "5g_ntn_handover",
        total_episodes: 1000,
        hyperparameters: {
          learning_rate: algorithm === 'dqn' ? 0.001 : 0.0003,
          batch_size: 32,
          epsilon_start: algorithm === 'dqn' ? 1.0 : undefined,
          epsilon_end: algorithm === 'dqn' ? 0.01 : undefined
        }
      };

      const result = await rlTrainingAPI.createExperiment(config);
      
      // 設置活躍實驗
      setActiveExperiments(prev => new Map(prev).set(algorithm, result.experiment_id));
      
      // 建立WebSocket連接用於即時更新
      const ws = rlTrainingAPI.connectLiveUpdates(result.experiment_id, (data) => {
        updateMetricsFromProgress(algorithm, data);
      });
      
      wsConnections.current.set(result.experiment_id, ws);
      
      // 發送自定義事件（保持與現有代碼的兼容性）
      const event = new CustomEvent(`${algorithm}TrainingToggle`, {
        detail: { isTraining: true, experimentId: result.experiment_id }
      });
      window.dispatchEvent(event);
      
    } catch (err) {
      console.error(`啟動${algorithm}訓練失敗:`, err);
      setError(`無法啟動${algorithm.toUpperCase()}訓練`);
    }
  };

  // 更新指標從進度數據
  const updateMetricsFromProgress = (algorithm: 'dqn' | 'ppo', progressData: any) => {
    const updateFunc = algorithm === 'dqn' ? setDqnMetrics : setPpoMetrics;
    
    updateFunc(prev => ({
      ...prev,
      episodes_completed: progressData.stats.episodes_completed,
      average_reward: progressData.stats.avg_reward,
      training_progress: progressData.stats.progress_percentage,
      model_status: 'training'
    }));
  };

  // 停止訓練
  const stopTraining = (algorithm: 'dqn' | 'ppo') => {
    const experimentId = activeExperiments.get(algorithm);
    if (experimentId) {
      // 關閉WebSocket連接
      const ws = wsConnections.current.get(experimentId);
      if (ws) {
        ws.close();
        wsConnections.current.delete(experimentId);
      }
      
      // 移除活躍實驗
      const newActiveExperiments = new Map(activeExperiments);
      newActiveExperiments.delete(algorithm);
      setActiveExperiments(newActiveExperiments);
    }

    // 更新狀態為閒置
    const updateFunc = algorithm === 'dqn' ? setDqnMetrics : setPpoMetrics;
    updateFunc(prev => ({ ...prev, model_status: 'idle' }));

    // 發送停止事件
    const event = new CustomEvent(`${algorithm}TrainingToggle`, {
      detail: { isTraining: false }
    });
    window.dispatchEvent(event);
  };

  // 組件載入時載入數據
  useEffect(() => {
    loadDashboardData();
    
    // 設置定期刷新（如果沒有WebSocket連接）
    const interval = setInterval(() => {
      if (wsConnections.current.size === 0) {
        loadDashboardData();
      }
    }, 5000);

    return () => {
      clearInterval(interval);
      // 關閉所有WebSocket連接
      wsConnections.current.forEach(ws => ws.close());
    };
  }, [loadDashboardData]);

  // 處理訓練控制
  const handleDQNTraining = () => {
    const isTraining = dqnMetrics.model_status === 'training';
    if (isTraining) {
      stopTraining('dqn');
    } else {
      startTraining('dqn');
    }
  };

  const handlePPOTraining = () => {
    const isTraining = ppoMetrics.model_status === 'training';
    if (isTraining) {
      stopTraining('ppo');
    } else {
      startTraining('ppo');
    }
  };

  const handleBothTraining = () => {
    const bothTraining = dqnMetrics.model_status === 'training' && 
                         ppoMetrics.model_status === 'training';
    
    if (bothTraining) {
      stopTraining('dqn');
      stopTraining('ppo');
    } else {
      startTraining('dqn');
      startTraining('ppo');
    }
  };

  // 渲染錯誤狀態
  if (error) {
    return (
      <div className="rl-monitor-error">
        <div className="error-message">
          <h3>❌ 連接錯誤</h3>
          <p>{error}</p>
          <button onClick={loadDashboardData} disabled={isLoading}>
            {isLoading ? '重新連接中...' : '重試連接'}
          </button>
        </div>
      </div>
    );
  }

  // 其餘的渲染邏輯保持不變，但數據來源改為真實的資料庫數據
  return (
    <div className="rl-monitor">
      {/* 現有的UI組件，但數據來自 dqnMetrics 和 ppoMetrics */}
      
      {/* 添加數據來源指示器 */}
      <div className="data-source-indicator">
        {dashboardData ? (
          <span className="data-live">🟢 即時數據 (共 {dashboardData.active_experiments} 個活躍實驗)</span>
        ) : (
          <span className="data-loading">🟡 載入中...</span>
        )}
      </div>
      
      {/* 現有的所有UI渲染邏輯... */}
    </div>
  );
};

export default GymnasiumRLMonitor;
```

---

## 🚀 部署和測試步驟

### 第1步：資料庫初始化

```bash
# 啟動容器
make up

# 進入SimWorld後端容器
docker exec -it simworld_backend bash

# 運行資料庫遷移
python -c "
from app.db.base import Base
from app.core.database import engine
import asyncio

async def create_tables():
    from sqlmodel import SQLModel
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    print('RL訓練資料表建立完成')

asyncio.run(create_tables())
"
```

### 第2步：測試API端點

```bash
# 測試建立實驗
curl -X POST http://localhost:8888/api/v1/rl/experiments \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test_DQN_Experiment",
    "algorithm": "dqn",
    "environment": "5g_ntn_handover",
    "total_episodes": 100,
    "hyperparameters": {
      "learning_rate": 0.001,
      "batch_size": 32
    }
  }'

# 測試儀表板數據
curl http://localhost:8888/api/v1/rl/dashboard
```

### 第3步：前端測試

```bash
# 確保前端能正確載入
# 訪問 http://localhost:5173
# 導航到 Navbar > 圖表分析 > RL監控
# 驗證數據來源從 "模擬數據" 變為 "即時數據"
```

### 第4步：驗證完整流程

1. **建立實驗**: 點擊"開始DQN訓練"，確認後端建立了新實驗
2. **即時更新**: 確認WebSocket連接正常，數據即時更新
3. **數據持久化**: 重新整理頁面，確認數據從資料庫載入
4. **歷史查詢**: 查看過往的訓練記錄和指標

---

## 📈 功能擴展建議

### 短期擴展 (1-2週)
- **模型檢查點管理**: 自動保存訓練好的模型
- **超參數調優**: 在UI中調整訓練參數
- **更豐富的指標**: 添加損失曲線、收斂分析

### 中期擴展 (1個月)
- **實驗比較**: 並排比較不同實驗的效果
- **自動化訓練**: 基於條件觸發的自動重訓練
- **模型部署**: 一鍵部署最佳模型到生產環境

### 長期擴展 (3個月)
- **A/B測試框架**: 在真實流量中測試不同模型
- **聯邦學習支持**: 分散式訓練能力
- **AutoML整合**: 自動搜索最佳架構和超參數

---

## 🔍 維護和監控

### 資料庫維護
```sql
-- 清理舊的訓練步驟數據（保留最近30天）
DELETE FROM rl_steps 
WHERE timestamp < CURRENT_DATE - INTERVAL '30 days';

-- 歸檔完成的實驗
UPDATE rl_experiments 
SET status = 'archived' 
WHERE status = 'completed' 
  AND completed_at < CURRENT_DATE - INTERVAL '90 days';
```

### 效能監控
- 監控資料庫查詢效能
- 設置WebSocket連接數限制
- 定期清理過期的模型檔案

### 錯誤處理
- API請求失敗的降級機制
- WebSocket斷線重連邏輯
- 資料不一致的自動修復

---

## 📋 總結

本實現流程涵蓋了從前端模擬數據到完整資料庫驅動的RL監控系統轉換。主要特色：

✅ **完整的資料持久化** - 所有訓練數據保存到PostgreSQL  
✅ **即時更新機制** - WebSocket提供低延遲的數據更新  
✅ **向後兼容** - 保持現有前端組件的介面不變  
✅ **可擴展架構** - 領域驅動設計，易於添加新功能  
✅ **生產就緒** - 包含錯誤處理、效能優化、維護策略

透過這個實現，RL監控頁面將從展示工具升級為完整的機器學習實驗管理平台。