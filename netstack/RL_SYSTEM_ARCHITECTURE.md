# 🧠 NetStack RL 系統架構文檔

## 概述

本文檔描述了基於世界級 SOLID 原則重新設計的 LEO 衛星強化學習系統架構。該系統支援研究級的算法開發、實驗管理和論文數據生成。

## 🏗️ 架構概覽

### 核心設計原則

1. **單一職責原則 (SRP)** - 每個類只負責一個功能
2. **開放封閉原則 (OCP)** - 對擴展開放，對修改封閉
3. **里氏替換原則 (LSP)** - 子類可以替換父類
4. **介面隔離原則 (ISP)** - 使用多個專門的接口
5. **依賴反轉原則 (DIP)** - 依賴抽象而非具體實現

### 系統層次結構

```
netstack/rl_system/
├── interfaces/           # 核心接口定義
│   ├── rl_algorithm.py         # RL 算法接口
│   ├── training_scheduler.py   # 訓練調度器接口
│   ├── performance_monitor.py  # 性能監控接口
│   ├── data_repository.py      # 數據儲存庫接口
│   └── model_manager.py        # 模型管理器接口
├── core/                # 核心組件
│   ├── algorithm_factory.py    # 算法工廠
│   ├── di_container.py         # 依賴注入容器
│   ├── config_manager.py       # 配置驅動管理器
│   └── service_locator.py      # 服務定位器
├── implementations/     # 具體實現
│   ├── dqn_implementation.py   # DQN 算法實現
│   ├── ppo_implementation.py   # PPO 算法實現
│   └── sac_implementation.py   # SAC 算法實現
├── database/           # 數據庫層
│   └── schema.sql             # PostgreSQL 架構
├── api/               # API 層
│   └── enhanced_rl_router.py  # 增強版 API 路由器
├── config/            # 配置文件
│   └── default_config.yaml   # 預設配置
└── setup.py           # 系統設置腳本
```

## 🚀 快速開始

### 1. 系統初始化

```bash
# 執行系統設置
cd netstack
python rl_system/setup.py --demo

# 或者自定義配置
python rl_system/setup.py --config custom_config.yaml --env production
```

### 2. 基本使用

```python
from rl_system.core.algorithm_factory import AlgorithmFactory
from rl_system.interfaces.rl_algorithm import ScenarioType, TrainingConfig

# 創建算法實例
dqn = AlgorithmFactory.create_algorithm("DQN", scenario_type=ScenarioType.URBAN)

# 配置訓練
config = TrainingConfig(
    episodes=1000,
    batch_size=32,
    learning_rate=0.001,
    scenario_type=ScenarioType.URBAN
)

# 執行訓練
result = await dqn.train(config)
print(f"訓練完成，最終分數: {result.final_score}")
```

### 3. API 使用

```bash
# 啟動 API 服務器
uvicorn rl_system.api.enhanced_rl_router:router --host 0.0.0.0 --port 8000

# 查看 API 文檔
curl http://localhost:8000/api/v1/rl/status
```

## 🧩 核心組件詳解

### 算法工廠 (AlgorithmFactory)

負責算法的註冊、創建和管理：

```python
# 註冊新算法
@algorithm_plugin(
    name="Custom_DQN",
    version="1.0.0",
    supported_scenarios=[ScenarioType.URBAN, ScenarioType.SUBURBAN],
    description="自定義 DQN 實現"
)
class CustomDQNAlgorithm(IRLAlgorithm):
    # 實現接口方法
    pass

# 使用算法
algorithm = AlgorithmFactory.create_algorithm("Custom_DQN")
```

### 依賴注入容器 (DIContainer)

管理服務依賴和生命週期：

```python
from rl_system.core.di_container import DIContainer, ServiceScope

container = DIContainer()

# 註冊服務
container.register_singleton(ITrainingScheduler, ConcreteTrainingScheduler)
container.register_transient(IPerformanceMonitor, ConcretePerformanceMonitor)

# 解析服務
scheduler = container.resolve(ITrainingScheduler)
```

### 配置驅動管理器 (ConfigDrivenAlgorithmManager)

基於 YAML 配置自動管理算法：

```yaml
handover_algorithms:
  reinforcement_learning:
    custom_dqn:
      algorithm_type: "Custom_DQN"
      enabled: true
      scenarios: ["urban", "suburban"]
      hyperparameters:
        learning_rate: 0.001
        batch_size: 32
```

## 📊 數據庫架構

### PostgreSQL 研究級架構

系統使用 PostgreSQL 作為主要數據庫，支援：

- **實驗會話管理** (`rl_experiment_sessions`)
- **訓練回合數據** (`rl_training_episodes`)
- **基準比較** (`rl_baseline_comparisons`)
- **性能時間序列** (`rl_performance_timeseries`)
- **模型版本控制** (`rl_model_versions`)
- **論文數據匯出** (`rl_paper_exports`)

### 關鍵特性

1. **研究級數據追踪** - 支援完整的實驗可重現性
2. **統計分析支援** - 內建視圖用於性能分析
3. **基準比較** - 自動化與baseline算法比較
4. **論文數據生成** - 直接匯出研究數據

## 🔧 配置系統

### 系統配置

```yaml
system:
  environment: "development"
  database_url: "postgresql://postgres:password@localhost:5432/rl_system"
  enable_monitoring: true
  max_concurrent_training: 3

# 算法配置
handover_algorithms:
  reinforcement_learning:
    dqn:
      enabled: true
      scenarios: ["urban", "suburban", "low_latency"]
      hyperparameters:
        learning_rate: 0.001
        batch_size: 32
```

### 場景配置

支援多種 LEO 衛星場景：

- **urban** - 城市密集網路
- **suburban** - 郊區穩定網路  
- **low_latency** - 低延遲關鍵應用
- **high_mobility** - 高速移動場景
- **dense_network** - 密集網路覆蓋

## 📡 API 端點

### 核心端點

| 端點 | 方法 | 描述 |
|------|------|------|
| `/api/v1/rl/status` | GET | 系統狀態 |
| `/api/v1/rl/algorithms` | GET | 可用算法列表 |
| `/api/v1/rl/training/start` | POST | 開始訓練 |
| `/api/v1/rl/prediction` | POST | 換手決策預測 |
| `/api/v1/rl/performance/{algorithm}` | GET | 算法性能指標 |

### 使用示例

```bash
# 獲取系統狀態
curl http://localhost:8000/api/v1/rl/status

# 開始訓練
curl -X POST http://localhost:8000/api/v1/rl/training/start \
  -H "Content-Type: application/json" \
  -d '{
    "algorithm_name": "DQN",
    "scenario_type": "urban",
    "episodes": 1000
  }'

# 執行預測
curl -X POST http://localhost:8000/api/v1/rl/prediction \
  -H "Content-Type: application/json" \
  -d '{
    "algorithm_name": "DQN",
    "scenario_type": "urban",
    "ue_position": {"lat": 40.7128, "lon": -74.0060},
    "current_serving_satellite": 1,
    "candidate_satellites": [1, 2, 3]
  }'
```

## 🧪 測試和驗證

### 單元測試

```python
import pytest
from rl_system.core.algorithm_factory import AlgorithmFactory

def test_algorithm_registration():
    algorithms = AlgorithmFactory.get_available_algorithms()
    assert "DQN" in algorithms

def test_algorithm_creation():
    dqn = AlgorithmFactory.create_algorithm("DQN")
    assert dqn.get_name() == "DQN"
    assert dqn.validate_scenario(ScenarioType.URBAN)
```

### 集成測試

```bash
# 運行完整測試套件
python -m pytest rl_system/tests/

# 運行特定測試
python -m pytest rl_system/tests/test_algorithm_factory.py
```

## 📈 性能監控

### 實時指標

系統自動收集和分析：

- **訓練指標** - 獎勵、收斂時間、成功率
- **性能指標** - 延遲、吞吐量、換手成功率
- **系統指標** - CPU、記憶體、GPU 使用率
- **業務指標** - 用戶體驗、網路質量

### 統計分析

- **基準比較** - 與傳統算法對比
- **收斂性分析** - 算法收斂特性
- **趨勢分析** - 長期性能趨勢
- **A/B 測試** - 算法版本比較

## 📝 研究功能

### 論文數據生成

```python
# 匯出研究數據
performance_monitor = ServiceLocator.get_performance_monitor()

# 生成 LaTeX 表格
latex_data = await performance_monitor.export_metrics_for_paper(
    algorithm_names=["DQN", "PPO", "SAC"],
    metric_types=[MetricType.REWARD, MetricType.LATENCY],
    format_type="latex",
    include_statistical_tests=True
)
```

### 實驗管理

- **版本控制** - 模型和實驗版本追踪
- **可重現性** - 完整的實驗配置記錄
- **協作支援** - 多研究員協作環境
- **基準庫** - 標準化基準算法

## 🔒 安全和部署

### 生產部署

```yaml
system:
  environment: "production"
  log_level: "WARNING"
  
security:
  api_key_required: true
  encryption_enabled: true
  
deployment:
  auto_scaling: true
  health_checks: true
  backup_enabled: true
```

### 安全特性

- **API 金鑰認證**
- **數據加密**
- **訪問控制**
- **審計日誌**

## 🛠️ 擴展指南

### 添加新算法

1. **實現接口**
```python
from rl_system.interfaces.rl_algorithm import IRLAlgorithm

class NewAlgorithm(IRLAlgorithm):
    # 實現所有必需方法
    pass
```

2. **註冊算法**
```python
@algorithm_plugin(name="NewAlgorithm", version="1.0.0")
class NewAlgorithm(IRLAlgorithm):
    pass
```

3. **配置算法**
```yaml
handover_algorithms:
  reinforcement_learning:
    new_algorithm:
      algorithm_type: "NewAlgorithm"
      enabled: true
```

### 添加新服務

1. **定義接口**
2. **實現服務**
3. **註冊到 DI 容器**
4. **更新配置**

## 📚 參考資料

### 設計模式

- **工廠模式** - 算法創建
- **觀察者模式** - 事件通知
- **策略模式** - 算法切換
- **依賴注入** - 解耦組件

### 技術棧

- **後端**: FastAPI, Python 3.8+
- **數據庫**: PostgreSQL, Redis
- **機器學習**: PyTorch, Gymnasium
- **監控**: Prometheus, Grafana
- **配置**: YAML, Pydantic

## 🤝 貢獻指南

1. **Fork 專案**
2. **創建功能分支**
3. **實現功能並測試**
4. **提交 Pull Request**

### 代碼規範

- 遵循 PEP 8
- 添加類型提示
- 編寫測試用例
- 更新文檔

## 📞 支援

- **文檔**: [完整文檔連結]
- **問題追踪**: GitHub Issues
- **討論**: GitHub Discussions
- **郵件**: netstack-support@example.com

---

*NetStack RL 系統 - 世界級 LEO 衛星強化學習研究平台*