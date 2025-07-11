# 🤖 LEO衛星換手決策RL系統架構

## 🎯 設計原則

### SOLID原則完整實現
- **S - 單一職責原則**: 每個類/函數只負責一件事
- **O - 開放封閉原則**: 對擴展開放，對修改封閉
- **L - 里氏替換原則**: 子類可以完全替換父類
- **I - 介面隔離原則**: 依賴具體介面而非大而全的介面
- **D - 依賴反轉原則**: 依賴抽象而非具體實現

### 基礎設計原則
- **DRY (Don't Repeat Yourself)**: 避免重複代碼，提取共用邏輯
- **YAGNI (You Aren't Gonna Need It)**: 不要過度設計，只實現當前需要的功能
- **關注點分離**: 不同關注點應該分離到不同模組
- **組合優於繼承**: 優先使用組合而非繼承來擴展功能

### 衛星系統特殊考量
- **即時性要求**: 切換決策延遲 < 10ms，API 響應時間 < 100ms，強化學習推理 < 1ms
- **高可靠性設計**: Circuit Breaker 模式，Graceful Degradation，健康檢查端點
- **分散式系統**: Service Mesh，Event Sourcing，最終一致性

## 🧩 核心接口設計

### 1. 算法插件接口
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

@dataclass
class TrainingConfig:
    episodes: int
    batch_size: int
    learning_rate: float
    custom_params: Dict[str, Any]

@dataclass
class TrainingResult:
    success: bool
    final_score: float
    episodes_completed: int
    metrics: Dict[str, Any]
    model_path: Optional[str]

class IRLAlgorithm(ABC):
    """RL算法插件接口"""
    
    @abstractmethod
    def get_name(self) -> str:
        """獲取算法名稱"""
        pass
    
    @abstractmethod
    def get_supported_scenarios(self) -> List[str]:
        """獲取支持的場景類型"""
        pass
    
    @abstractmethod
    async def train(self, config: TrainingConfig) -> TrainingResult:
        """執行訓練"""
        pass
    
    @abstractmethod
    async def predict(self, state: Any) -> Any:
        """執行預測"""
        pass
    
    @abstractmethod
    def load_model(self, model_path: str) -> bool:
        """加載模型"""
        pass
    
    @abstractmethod
    def save_model(self, model_path: str) -> bool:
        """保存模型"""
        pass

class ITrainingScheduler(ABC):
    """訓練調度器接口"""
    
    @abstractmethod
    async def schedule_training(self, algorithm: str, config: TrainingConfig) -> bool:
        pass
    
    @abstractmethod
    async def get_training_queue(self) -> List[Dict[str, Any]]:
        pass

class IPerformanceMonitor(ABC):
    """性能監控接口"""
    
    @abstractmethod
    async def record_metrics(self, algorithm: str, metrics: Dict[str, Any]) -> None:
        pass
    
    @abstractmethod
    async def get_performance_summary(self, algorithm: str) -> Dict[str, Any]:
        pass
```

### 2. 算法工廠模式
```python
class AlgorithmFactory:
    """算法工廠 - 負責創建算法實例"""
    
    _registry: Dict[str, type] = {}
    
    @classmethod
    def register_algorithm(cls, name: str, algorithm_class: type) -> None:
        """註冊新算法類型"""
        if not issubclass(algorithm_class, IRLAlgorithm):
            raise ValueError(f"Algorithm {name} must implement IRLAlgorithm interface")
        cls._registry[name] = algorithm_class
    
    @classmethod
    def create_algorithm(cls, name: str, config: Dict[str, Any]) -> IRLAlgorithm:
        """創建算法實例"""
        if name not in cls._registry:
            raise ValueError(f"Unknown algorithm: {name}")
        
        algorithm_class = cls._registry[name]
        return algorithm_class(config)
    
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
```

### 3. 具體算法實現（插件化）
```python
@algorithm_plugin("DQN")
class DQNAlgorithm(IRLAlgorithm):
    """DQN算法插件"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model = None
        self._name = "DQN"
        self._supported_scenarios = ["urban", "suburban", "low_latency"]
    
    def get_name(self) -> str:
        return self._name
    
    def get_supported_scenarios(self) -> List[str]:
        return self._supported_scenarios
    
    async def train(self, config: TrainingConfig) -> TrainingResult:
        """DQN訓練邏輯"""
        try:
            episodes_completed = 0
            final_score = 0.0
            
            for episode in range(config.episodes):
                # 實際訓練邏輯
                episodes_completed += 1
                # 更新final_score
                
            return TrainingResult(
                success=True,
                final_score=final_score,
                episodes_completed=episodes_completed,
                metrics={"convergence_rate": 0.95, "stability": 0.88},
                model_path=f"/models/dqn_model_{episodes_completed}.pth"
            )
        except Exception as e:
            return TrainingResult(
                success=False,
                final_score=0.0,
                episodes_completed=episodes_completed,
                metrics={"error": str(e)},
                model_path=None
            )
    
    async def predict(self, state: Any) -> Any:
        """DQN預測邏輯"""
        pass
    
    def load_model(self, model_path: str) -> bool:
        """加載DQN模型"""
        pass
    
    def save_model(self, model_path: str) -> bool:
        """保存DQN模型"""
        pass

@algorithm_plugin("PPO")
class PPOAlgorithm(IRLAlgorithm):
    """PPO算法插件"""
    # 類似DQN的實現
    pass

@algorithm_plugin("SAC")
class SACAlgorithm(IRLAlgorithm):
    """SAC算法插件"""
    # 類似DQN的實現
    pass
```

### 4. 依賴注入容器
```python
class DIContainer:
    """簡單的依賴注入容器"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, callable] = {}
    
    def register_singleton(self, interface: type, implementation: Any) -> None:
        """註冊單例服務"""
        self._services[interface.__name__] = implementation
    
    def register_factory(self, interface: type, factory: callable) -> None:
        """註冊工廠方法"""
        self._factories[interface.__name__] = factory
    
    def get(self, interface: type) -> Any:
        """獲取服務實例"""
        name = interface.__name__
        
        if name in self._services:
            return self._services[name]
        
        if name in self._factories:
            instance = self._factories[name]()
            self._services[name] = instance  # Cache as singleton
            return instance
        
        raise ValueError(f"Service {name} not registered")

# 配置依賴注入
def setup_di_container() -> DIContainer:
    container = DIContainer()
    
    # 註冊服務
    container.register_factory(
        ITrainingScheduler, 
        lambda: IntelligentTrainingScheduler(
            container.get(IPerformanceMonitor)
        )
    )
    
    container.register_factory(
        IPerformanceMonitor,
        lambda: DatabasePerformanceMonitor()
    )
    
    return container
```

### 5. 配置驅動的算法管理器
```python
class ConfigDrivenAlgorithmManager:
    """配置驅動的算法管理器"""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = {}
        self.algorithms: Dict[str, IRLAlgorithm] = {}
        
    async def initialize(self) -> None:
        """初始化算法管理器"""
        # 加載配置
        await self._load_config()
        
        # 動態加載算法插件
        await self._load_algorithm_plugins()
    
    async def _load_config(self) -> None:
        """加載配置文件"""
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
    
    async def _load_algorithm_plugins(self) -> None:
        """動態加載算法插件"""
        rl_algorithms = self.config.get('handover_algorithms', {}).get('reinforcement_learning', {})
        
        for algo_name, algo_config in rl_algorithms.items():
            if not algo_config.get('enabled', False):
                continue
                
            try:
                # 使用工廠創建算法實例
                algorithm = AlgorithmFactory.create_algorithm(
                    algo_config.get('algorithm_type', algo_name.upper()),
                    algo_config
                )
                self.algorithms[algo_name] = algorithm
                logger.info(f"Successfully loaded algorithm: {algo_name}")
                
            except Exception as e:
                logger.error(f"Failed to load algorithm {algo_name}: {e}")
    
    async def get_algorithm(self, name: str) -> IRLAlgorithm:
        """獲取算法實例"""
        if name not in self.algorithms:
            raise ValueError(f"Algorithm {name} not available")
        return self.algorithms[name]
    
    def get_available_algorithms(self) -> List[str]:
        """獲取可用算法列表"""
        return list(self.algorithms.keys())
```

## 🗄️ 數據庫設計

### 核心訓練數據表
```sql
-- 訓練會話主表
CREATE TABLE rl_training_sessions (
    id BIGSERIAL PRIMARY KEY,
    algorithm_type VARCHAR(20) NOT NULL,
    session_name VARCHAR(100),
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    total_episodes INTEGER DEFAULT 0,
    session_status VARCHAR(20) DEFAULT 'running',
    config_hash VARCHAR(64),
    metadata JSONB,
    INDEX idx_algorithm_type (algorithm_type),
    INDEX idx_session_status (session_status)
);

-- 訓練回合數據
CREATE TABLE rl_training_episodes (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT REFERENCES rl_training_sessions(id) ON DELETE CASCADE,
    episode_number INTEGER NOT NULL,
    total_reward FLOAT,
    success_rate FLOAT,
    episode_metadata JSONB,
    UNIQUE(session_id, episode_number),
    INDEX idx_episode_performance (total_reward, success_rate)
);

-- 算法性能統計
CREATE TABLE rl_algorithm_performance (
    id BIGSERIAL PRIMARY KEY,
    algorithm_type VARCHAR(20),
    evaluation_date DATE,
    average_success_rate FLOAT,
    average_reward FLOAT,
    average_response_time_ms FLOAT,
    stability_score FLOAT,
    UNIQUE(algorithm_type, evaluation_date)
);

-- 模型版本管理
CREATE TABLE rl_model_versions (
    id BIGSERIAL PRIMARY KEY,
    algorithm_type VARCHAR(20),
    version_number VARCHAR(20),
    model_file_path VARCHAR(500),
    training_session_id BIGINT REFERENCES rl_training_sessions(id),
    validation_score FLOAT,
    deployment_status VARCHAR(20) DEFAULT 'created',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_model_version (algorithm_type, version_number)
);
```

## 🎮 前端架構設計

### 1. 漸進式navbar整合
```typescript
// 非侵入式navbar設計
interface RLStatusIndicator {
  algorithms: {
    dqn: 'idle' | 'training' | 'error' | 'completed';
    ppo: 'idle' | 'training' | 'error' | 'completed';
    sac: 'idle' | 'training' | 'error' | 'completed';
  };
  overallStatus: 'healthy' | 'warning' | 'error';
  quickActions: {
    openRLCenter: () => void;
    emergencyStop: () => void;
  };
}

// 在navbar右側增加小型狀態指示器
const RLStatusWidget: React.FC = () => {
  const { algorithms, overallStatus } = useRLStatus();
  
  return (
    <div className="rl-status-widget">
      {/* 三個小型狀態燈 */}
      <div className="algorithm-status-lights">
        <StatusDot algorithm="DQN" status={algorithms.dqn} size="small" />
        <StatusDot algorithm="PPO" status={algorithms.ppo} size="small" />
        <StatusDot algorithm="SAC" status={algorithms.sac} size="small" />
      </div>
      
      {/* 總體狀態指示 */}
      <OverallStatusIcon status={overallStatus} />
      
      {/* 點擊進入完整管理中心 */}
      <IconButton 
        onClick={() => openRLManagementCenter()}
        tooltip="RL訓練管理中心"
        size="small"
      >
        🧠
      </IconButton>
    </div>
  );
};
```

### 2. 模塊化組件設計
```typescript
// 使用React的Provider模式管理RL狀態
interface RLContextType {
  algorithms: AlgorithmStatus[];
  performance: PerformanceMetrics;
  actions: {
    startTraining: (algorithm: string, config: TrainingConfig) => Promise<void>;
    stopTraining: (algorithm: string) => Promise<void>;
    deployModel: (algorithm: string, version: string) => Promise<void>;
  };
}

const RLContext = createContext<RLContextType | null>(null);

// 插件化的算法組件
interface AlgorithmComponentProps {
  algorithm: IRLAlgorithm;
  onConfigChange: (config: TrainingConfig) => void;
}

const AlgorithmComponent: React.FC<AlgorithmComponentProps> = ({ 
  algorithm, 
  onConfigChange 
}) => {
  // 動態渲染基於算法類型的配置界面
  const ConfigComponent = getAlgorithmConfigComponent(algorithm.getName());
  
  return (
    <div className="algorithm-component">
      <AlgorithmHeader algorithm={algorithm} />
      <ConfigComponent 
        algorithm={algorithm}
        onChange={onConfigChange}
      />
      <AlgorithmActions algorithm={algorithm} />
    </div>
  );
};
```

## 🔒 安全性設計

### 安全原則
- **最小權限原則**: 組件只能訪問必要的資源
- **輸入驗證**: 所有外部輸入必須驗證
- **敏感數據加密**: 衛星軌道數據、AI 模型參數
- **審計日誌**: 關鍵操作必須記錄

### 安全檢查清單
- [ ] API 端點有適當的驗證和授權
- [ ] 敏感配置不在代碼中硬編碼
- [ ] 錯誤訊息不洩露系統內部信息
- [ ] 所有用戶輸入都經過驗證和清理

## 🧪 測試策略

### 測試金字塔
```bash
# 單元測試 (70%) - 快速，隔離
npm run test:unit

# 整合測試 (20%) - 組件協作
npm run test:integration  

# E2E 測試 (10%) - 用戶流程
npm run test:e2e
```

### AI 演算法特殊測試
- **確定性測試**: 相同輸入必須產生相同輸出
- **效能基準測試**: DQN 訓練時間、推理延遲
- **論文復現測試**: 確保演算法實現符合論文描述

## 🚀 開發步驟流程

### Phase 1: 基礎設施建立 (1-2週)
**目標**: 建立數據庫、基礎API和項目結構

#### 1.1 數據庫設置
```bash
# 1. 創建數據庫
docker exec -it netstack-postgres createdb rl_training

# 2. 執行SQL腳本
docker exec -i netstack-postgres psql -d rl_training < rl_database_schema.sql

# 3. 驗證表創建
docker exec -it netstack-postgres psql -d rl_training -c "\dt"
```

#### 1.2 後端API框架
```python
# /netstack/backend/rl_system/
├── __init__.py
├── interfaces/
│   ├── __init__.py
│   ├── rl_algorithm.py      # IRLAlgorithm接口
│   ├── training_scheduler.py # ITrainingScheduler接口
│   └── performance_monitor.py # IPerformanceMonitor接口
├── core/
│   ├── __init__.py
│   ├── algorithm_factory.py  # 算法工廠
│   ├── di_container.py      # 依賴注入容器
│   └── config_manager.py    # 配置管理器
├── api/
│   ├── __init__.py
│   ├── training_routes.py   # 訓練API路由
│   └── monitoring_routes.py # 監控API路由
└── models/
    ├── __init__.py
    └── database_models.py   # 數據庫模型
```

#### 1.3 基礎API端點
```python
# /netstack/backend/rl_system/api/training_routes.py
from fastapi import APIRouter, Depends
from ..interfaces.rl_algorithm import TrainingConfig, TrainingResult

router = APIRouter(prefix="/api/rl/training")

@router.post("/start/{algorithm_name}")
async def start_training(algorithm_name: str, config: TrainingConfig):
    """啟動訓練"""
    # 基礎實現
    return {"status": "started", "algorithm": algorithm_name}

@router.get("/status/{algorithm_name}")
async def get_training_status(algorithm_name: str):
    """獲取訓練狀態"""
    # 基礎實現
    return {"status": "idle", "algorithm": algorithm_name}

@router.post("/stop/{algorithm_name}")
async def stop_training(algorithm_name: str):
    """停止訓練"""
    # 基礎實現
    return {"status": "stopped", "algorithm": algorithm_name}
```

**Phase 1 驗收標準：**
- [ ] 數據庫表創建成功
- [ ] 基礎API能夠回應請求
- [ ] 項目結構符合設計規範
- [ ] `curl http://localhost:8080/api/rl/training/status/DQN` 回傳正確響應

---

### Phase 2: 核心算法接口 (1週)
**目標**: 實現算法工廠和插件架構

#### 2.1 實現核心接口
```python
# /netstack/backend/rl_system/interfaces/rl_algorithm.py
# (使用文件中已定義的接口)

# /netstack/backend/rl_system/core/algorithm_factory.py
# (使用文件中已定義的工廠)
```

#### 2.2 實現依賴注入
```python
# /netstack/backend/rl_system/core/di_container.py
# (使用文件中已定義的DI容器)

# /netstack/backend/rl_system/core/config_manager.py
class ConfigManager:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = {}
    
    def load_config(self):
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
    
    def get_rl_algorithms(self):
        return self.config.get('handover_algorithms', {}).get('reinforcement_learning', {})
```

#### 2.3 創建基礎算法插件
```python
# /netstack/backend/rl_system/algorithms/
├── __init__.py
├── base_algorithm.py        # 基礎算法類
├── dqn_algorithm.py         # DQN實現
├── ppo_algorithm.py         # PPO實現
└── sac_algorithm.py         # SAC實現
```

**Phase 2 驗收標準：**
- [ ] 算法工廠能夠註冊和創建算法實例
- [ ] 依賴注入容器正常工作
- [ ] 至少一個算法插件能夠成功註冊
- [ ] 配置管理器能夠讀取配置文件

---

### Phase 3: 基本訓練功能 (2週)
**目標**: 實現完整的DQN訓練流程

#### 3.1 DQN算法實現
```python
# /netstack/backend/rl_system/algorithms/dqn_algorithm.py
@algorithm_plugin("DQN")
class DQNAlgorithm(IRLAlgorithm):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model = self._build_model()
        self.target_model = self._build_model()
        self.memory = deque(maxlen=10000)
        self.epsilon = 1.0
        self.epsilon_decay = 0.995
        self.epsilon_min = 0.01
        
    def _build_model(self):
        """構建DQN神經網絡"""
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(64, activation='relu', input_shape=(state_size,)),
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dense(action_size, activation='linear')
        ])
        model.compile(loss='mse', optimizer='adam')
        return model
    
    async def train(self, config: TrainingConfig) -> TrainingResult:
        """實際的DQN訓練邏輯"""
        try:
            for episode in range(config.episodes):
                # 環境重置
                state = self._reset_environment()
                total_reward = 0
                
                for step in range(max_steps):
                    # 選擇動作
                    action = self._choose_action(state)
                    
                    # 執行動作
                    next_state, reward, done = self._step(action)
                    
                    # 存儲經驗
                    self.memory.append((state, action, reward, next_state, done))
                    
                    # 訓練模型
                    if len(self.memory) > batch_size:
                        self._replay_train(config.batch_size)
                    
                    state = next_state
                    total_reward += reward
                    
                    if done:
                        break
                
                # 更新目標網絡
                if episode % target_update_freq == 0:
                    self.target_model.set_weights(self.model.get_weights())
                
                # 記錄訓練指標
                await self._record_episode_metrics(episode, total_reward)
            
            return TrainingResult(
                success=True,
                final_score=total_reward,
                episodes_completed=config.episodes,
                metrics=self._get_training_metrics(),
                model_path=self._save_model()
            )
            
        except Exception as e:
            return TrainingResult(
                success=False,
                final_score=0.0,
                episodes_completed=0,
                metrics={"error": str(e)},
                model_path=None
            )
```

#### 3.2 環境模擬器
```python
# /netstack/backend/rl_system/environment/
├── __init__.py
├── satellite_env.py         # 衛星環境模擬器
├── handover_simulator.py    # 切換決策模擬器
└── reward_calculator.py     # 獎勵計算器

# /netstack/backend/rl_system/environment/satellite_env.py
class SatelliteHandoverEnvironment:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.current_state = None
        self.satellites = self._initialize_satellites()
        self.user_terminals = self._initialize_terminals()
    
    def reset(self):
        """重置環境"""
        self.current_state = self._generate_initial_state()
        return self.current_state
    
    def step(self, action: int):
        """執行動作並返回新狀態"""
        # 模擬衛星切換決策
        next_state = self._simulate_handover(action)
        reward = self._calculate_reward(action, next_state)
        done = self._is_episode_done(next_state)
        
        self.current_state = next_state
        return next_state, reward, done
    
    def _simulate_handover(self, action: int):
        """模擬切換過程"""
        # 實際的衛星切換邏輯
        pass
    
    def _calculate_reward(self, action: int, next_state):
        """計算獎勵"""
        # 根據切換決策的品質計算獎勵
        pass
```

#### 3.3 訓練數據持久化
```python
# /netstack/backend/rl_system/services/training_service.py
class TrainingService:
    def __init__(self, db_connection, algorithm_manager):
        self.db = db_connection
        self.algorithm_manager = algorithm_manager
    
    async def start_training_session(self, algorithm_name: str, config: TrainingConfig):
        """啟動訓練會話"""
        # 創建訓練會話記錄
        session = await self.db.create_training_session(
            algorithm_type=algorithm_name,
            config=config
        )
        
        # 獲取算法實例
        algorithm = await self.algorithm_manager.get_algorithm(algorithm_name)
        
        # 啟動訓練
        result = await algorithm.train(config)
        
        # 更新會話狀態
        await self.db.update_training_session(session.id, result)
        
        return result
```

**Phase 3 驗收標準：**
- [ ] DQN算法能夠完成完整訓練流程
- [ ] 訓練數據正確保存到數據庫
- [ ] 訓練進度能夠實時查詢
- [ ] 訓練結果符合預期格式

---

### Phase 4: 前端基礎整合 (1週)
**目標**: 實現基本的訓練控制UI

#### 4.1 React組件架構
```tsx
// /simworld/frontend/src/components/rl/
├── RLManagementCenter.tsx    # 主管理中心
├── TrainingControlPanel.tsx  # 訓練控制面板
├── AlgorithmStatusCard.tsx   # 算法狀態卡片
├── TrainingProgressChart.tsx # 訓練進度圖表
└── hooks/
    ├── useRLTraining.ts      # 訓練相關Hook
    └── useRLStatus.ts        # 狀態監控Hook
```

#### 4.2 訓練控制面板
```tsx
// /simworld/frontend/src/components/rl/TrainingControlPanel.tsx
import React, { useState } from 'react';
import { useRLTraining } from './hooks/useRLTraining';

interface TrainingConfig {
  episodes: number;
  batch_size: number;
  learning_rate: number;
}

const TrainingControlPanel: React.FC = () => {
  const [selectedAlgorithm, setSelectedAlgorithm] = useState<string>('DQN');
  const [config, setConfig] = useState<TrainingConfig>({
    episodes: 1000,
    batch_size: 32,
    learning_rate: 0.001
  });
  
  const { 
    startTraining, 
    stopTraining, 
    isTraining, 
    trainingStatus 
  } = useRLTraining();
  
  const handleStartTraining = async () => {
    try {
      await startTraining(selectedAlgorithm, config);
    } catch (error) {
      console.error('訓練啟動失敗:', error);
    }
  };
  
  return (
    <div className="training-control-panel">
      <h3>RL訓練控制</h3>
      
      {/* 算法選擇 */}
      <div className="algorithm-selector">
        <label>選擇算法:</label>
        <select 
          value={selectedAlgorithm} 
          onChange={(e) => setSelectedAlgorithm(e.target.value)}
        >
          <option value="DQN">DQN</option>
          <option value="PPO">PPO</option>
          <option value="SAC">SAC</option>
        </select>
      </div>
      
      {/* 訓練配置 */}
      <div className="training-config">
        <label>訓練回合數:</label>
        <input 
          type="number" 
          value={config.episodes}
          onChange={(e) => setConfig({...config, episodes: parseInt(e.target.value)})}
        />
        
        <label>批次大小:</label>
        <input 
          type="number" 
          value={config.batch_size}
          onChange={(e) => setConfig({...config, batch_size: parseInt(e.target.value)})}
        />
        
        <label>學習率:</label>
        <input 
          type="number" 
          step="0.0001"
          value={config.learning_rate}
          onChange={(e) => setConfig({...config, learning_rate: parseFloat(e.target.value)})}
        />
      </div>
      
      {/* 控制按鈕 */}
      <div className="control-buttons">
        <button 
          onClick={handleStartTraining}
          disabled={isTraining(selectedAlgorithm)}
          className="start-btn"
        >
          {isTraining(selectedAlgorithm) ? '訓練中...' : '開始訓練'}
        </button>
        
        <button 
          onClick={() => stopTraining(selectedAlgorithm)}
          disabled={!isTraining(selectedAlgorithm)}
          className="stop-btn"
        >
          停止訓練
        </button>
      </div>
      
      {/* 狀態顯示 */}
      <div className="status-display">
        <p>當前狀態: {trainingStatus[selectedAlgorithm]?.status || 'idle'}</p>
        <p>已完成回合: {trainingStatus[selectedAlgorithm]?.episodes_completed || 0}</p>
        <p>平均獎勵: {trainingStatus[selectedAlgorithm]?.average_reward || 0}</p>
      </div>
    </div>
  );
};
```

#### 4.3 自定義Hook
```tsx
// /simworld/frontend/src/components/rl/hooks/useRLTraining.ts
import { useState, useEffect } from 'react';
import { netstackFetch } from '../../../config/api-config';

export const useRLTraining = () => {
  const [trainingStatus, setTrainingStatus] = useState<Record<string, any>>({});
  
  const startTraining = async (algorithm: string, config: any) => {
    const response = await netstackFetch(`/api/rl/training/start/${algorithm}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
    
    if (!response.ok) {
      throw new Error('訓練啟動失敗');
    }
    
    return response.json();
  };
  
  const stopTraining = async (algorithm: string) => {
    const response = await netstackFetch(`/api/rl/training/stop/${algorithm}`, {
      method: 'POST'
    });
    
    if (!response.ok) {
      throw new Error('訓練停止失敗');
    }
    
    return response.json();
  };
  
  const isTraining = (algorithm: string) => {
    return trainingStatus[algorithm]?.status === 'training';
  };
  
  // 定期獲取狀態
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const algorithms = ['DQN', 'PPO', 'SAC'];
        const statusPromises = algorithms.map(async (algo) => {
          const response = await netstackFetch(`/api/rl/training/status/${algo}`);
          return { algorithm: algo, status: await response.json() };
        });
        
        const statuses = await Promise.all(statusPromises);
        const newStatus = {};
        statuses.forEach(({ algorithm, status }) => {
          newStatus[algorithm] = status;
        });
        
        setTrainingStatus(newStatus);
      } catch (error) {
        console.error('狀態獲取失敗:', error);
      }
    }, 2000);
    
    return () => clearInterval(interval);
  }, []);
  
  return {
    startTraining,
    stopTraining,
    isTraining,
    trainingStatus
  };
};
```

**Phase 4 驗收標準：**
- [ ] 前端能夠啟動/停止訓練
- [ ] 訓練狀態實時更新
- [ ] 訓練配置能夠正確提交
- [ ] 錯誤處理正常工作

---

### Phase 5: 多算法支持 (1週)
**目標**: 實現PPO和SAC算法

#### 5.1 PPO算法實現
```python
# /netstack/backend/rl_system/algorithms/ppo_algorithm.py
@algorithm_plugin("PPO")
class PPOAlgorithm(IRLAlgorithm):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.actor = self._build_actor()
        self.critic = self._build_critic()
        self.memory = []
        
    def _build_actor(self):
        """構建演員網絡"""
        pass
    
    def _build_critic(self):
        """構建評論家網絡"""
        pass
    
    async def train(self, config: TrainingConfig) -> TrainingResult:
        """PPO訓練邏輯"""
        # 實現PPO特有的訓練邏輯
        pass
```

#### 5.2 SAC算法實現
```python
# /netstack/backend/rl_system/algorithms/sac_algorithm.py
@algorithm_plugin("SAC")
class SACAlgorithm(IRLAlgorithm):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.actor = self._build_actor()
        self.critic1 = self._build_critic()
        self.critic2 = self._build_critic()
        self.target_critic1 = self._build_critic()
        self.target_critic2 = self._build_critic()
        
    async def train(self, config: TrainingConfig) -> TrainingResult:
        """SAC訓練邏輯"""
        # 實現SAC特有的訓練邏輯
        pass
```

**Phase 5 驗收標準：**
- [ ] 三個算法都能獨立訓練
- [ ] 算法工廠能夠正確創建所有算法
- [ ] 前端能夠選擇和控制所有算法
- [ ] 訓練數據正確區分不同算法

---

### Phase 6: 性能監控 (1週)
**目標**: 實現完整的性能監控和指標展示

#### 6.1 性能監控服務
```python
# /netstack/backend/rl_system/services/performance_monitor.py
class PerformanceMonitor(IPerformanceMonitor):
    def __init__(self, db_connection):
        self.db = db_connection
    
    async def record_metrics(self, algorithm: str, metrics: Dict[str, Any]) -> None:
        """記錄性能指標"""
        await self.db.insert_performance_metrics(algorithm, metrics)
    
    async def get_performance_summary(self, algorithm: str) -> Dict[str, Any]:
        """獲取性能摘要"""
        return await self.db.get_algorithm_performance_summary(algorithm)
    
    async def get_real_time_metrics(self, algorithm: str) -> Dict[str, Any]:
        """獲取實時指標"""
        return await self.db.get_latest_training_metrics(algorithm)
```

#### 6.2 前端性能圖表
```tsx
// /simworld/frontend/src/components/rl/TrainingProgressChart.tsx
import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import { useRLMetrics } from './hooks/useRLMetrics';

const TrainingProgressChart: React.FC<{ algorithm: string }> = ({ algorithm }) => {
  const { metrics, loading } = useRLMetrics(algorithm);
  
  if (loading) return <div>載入中...</div>;
  
  return (
    <div className="training-progress-chart">
      <h4>{algorithm} 訓練進度</h4>
      <LineChart width={600} height={300} data={metrics}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="episode" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="reward" stroke="#8884d8" name="獎勵" />
        <Line type="monotone" dataKey="success_rate" stroke="#82ca9d" name="成功率" />
        <Line type="monotone" dataKey="loss" stroke="#ffc658" name="損失" />
      </LineChart>
    </div>
  );
};
```

**Phase 6 驗收標準：**
- [ ] 性能指標能夠實時收集和存儲
- [ ] 前端圖表正確顯示訓練進度
- [ ] 能夠比較不同算法的性能
- [ ] 歷史數據查詢功能正常

---

## 🎯 實施檢查清單

### 功能完整性
- [ ] 三種RL算法能夠獨立訓練和部署
- [ ] 訓練數據完整持久化到PostgreSQL
- [ ] 前端UI能夠完整控制訓練流程
- [ ] 性能監控和指標收集正常工作

### 性能指標
- **訓練效率**: 單回合訓練時間 < 100ms
- **響應時間**: API響應時間 < 50ms
- **並發處理**: 支持3個算法同時訓練
- **記憶體使用率**: < 80%

### 代碼審查清單
- [ ] 符合 SOLID 原則
- [ ] 無重複代碼 (DRY)
- [ ] 函數職責單一
- [ ] 依賴通過注入管理
- [ ] 有適當的單元測試
- [ ] 性能符合 KPI 要求
- [ ] 安全性要求滿足

### 每階段驗證命令
```bash
# Phase 1 驗證
curl http://localhost:8080/api/rl/training/status/DQN

# Phase 2 驗證
docker exec simworld_backend python -c "
from rl_system.core.algorithm_factory import AlgorithmFactory
print(AlgorithmFactory.get_available_algorithms())
"

# Phase 3 驗證
curl -X POST http://localhost:8080/api/rl/training/start/DQN \
  -H "Content-Type: application/json" \
  -d '{"episodes": 10, "batch_size": 32, "learning_rate": 0.001}'

# Phase 4 驗證
# 打開前端 http://localhost:5173 檢查RL控制面板

# Phase 5 驗證
curl http://localhost:8080/api/rl/training/status/PPO
curl http://localhost:8080/api/rl/training/status/SAC

# Phase 6 驗證
curl http://localhost:8080/api/rl/monitoring/metrics/DQN
```

## ✅ 架構優勢

### 1. 完美的擴展性
```python
# ✅ 新增算法只需要：
@algorithm_plugin("新算法名")
class NewAlgorithm(IRLAlgorithm):
    # 實現接口方法即可
    pass

# 配置文件中添加：
# new_algorithm:
#   algorithm_type: "新算法名"
#   enabled: true
```

### 2. 低耦合設計
- 組件通過接口交互，不依賴具體實現
- 使用依賴注入，便於測試和替換
- 配置驅動，避免硬編碼

### 3. 符合軟體開發規範
- 完整的SOLID原則實現
- 豐富的設計模式使用
- 高測試覆蓋率的友好設計
- 清晰的分層架構

### 4. 漸進式UI整合
- 非侵入式的navbar設計
- 保持現有用戶體驗
- 專業功能不影響主流程
- 可配置的顯示選項

---

**🎯 目標：建立世界級的LEO衛星RL決策系統，實現完全透明化的AI決策過程**

**遵循原則：簡化問題，而非複雜化解決方案**