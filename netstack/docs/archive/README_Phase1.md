# 🤖 LEO衛星換手決策RL系統 - Phase 1 實施指南

## 🎯 Phase 1 目標：真實 PostgreSQL 數據庫儲存

### ✅ 已完成功能

- **真實 PostgreSQL 數據庫**: 完全摒棄 MockRepository，使用研究級數據庫
- **自動數據庫初始化**: 一鍵創建數據庫表結構和示例數據
- **完整訓練管理**: 支援論文級別的訓練會話追蹤
- **詳細訓練記錄**: 每個 episode 的完整性能指標
- **算法比較分析**: 支援多算法性能比較
- **模型版本管理**: 完整的模型生命周期管理

### 🏗️ 系統架構

```
LEO RL System (Phase 1)
├── 🗄️ PostgreSQL 數據庫
│   ├── rl_experiment_sessions    # 訓練會話
│   ├── rl_training_episodes      # 訓練回合
│   ├── rl_performance_timeseries # 性能指標
│   ├── rl_baseline_comparisons   # Baseline 比較
│   └── rl_model_versions         # 模型版本
├── 🔌 API 層
│   ├── 訓練管理 API
│   ├── 性能監控 API
│   └── 健康檢查 API
└── 🧠 算法層
    ├── DQN 算法
    ├── PPO 算法
    └── SAC 算法
```

## 🚀 快速開始

### 1. 安裝依賴項
```bash
cd netstack/rl_system
make install
```

### 2. 設置 PostgreSQL
```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql

# macOS
brew install postgresql
brew services start postgresql

# Docker
docker run --name postgres-rl -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres
```

### 3. 配置環境變量
```bash
cp .env.example .env
# 編輯 .env 文件，設置數據庫連接信息
```

### 4. 初始化數據庫
```bash
make init-db
```

### 5. 測試連接
```bash
make test-db
```

### 6. 啟動系統
```bash
make start
```

## 🔧 詳細設置

### 環境變量配置

編輯 `.env` 文件：

```env
# 數據庫連接
DATABASE_URL=postgresql://rl_user:rl_password@localhost:5432/rl_research_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=rl_user
POSTGRES_PASSWORD=rl_password
POSTGRES_DATABASE=rl_research_db

# 管理員賬戶（用於初始化）
POSTGRES_ADMIN_USER=postgres
POSTGRES_ADMIN_PASSWORD=postgres

# 應用程式配置
ENV=development
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000
```

### 數據庫表結構

Phase 1 創建以下研究級數據表：

1. **rl_experiment_sessions**: 訓練會話管理
2. **rl_training_episodes**: 詳細訓練回合數據
3. **rl_performance_timeseries**: 性能指標時間序列
4. **rl_baseline_comparisons**: Baseline 算法比較
5. **rl_model_versions**: 模型版本管理
6. **rl_paper_exports**: 論文數據匯出記錄

## 📊 API 使用

### 啟動訓練

```bash
curl -X POST "http://localhost:8000/api/rl/start/dqn" \
  -H "Content-Type: application/json" \
  -d '{
    "total_episodes": 100,
    "step_time": 0.1,
    "experiment_name": "DQN_LEO_Test",
    "scenario_type": "urban",
    "researcher_id": "researcher_001",
    "research_notes": "測試 DQN 算法在城市場景中的表現"
  }'
```

### 查看訓練狀態

```bash
curl -X GET "http://localhost:8000/api/rl/status/dqn"
```

### 停止訓練

```bash
curl -X POST "http://localhost:8000/api/rl/stop/dqn"
```

### 健康檢查

```bash
curl -X GET "http://localhost:8000/api/rl/health"
```

## 🧪 測試

### 數據庫連接測試
```bash
python -m database.init_database
```

### API 測試
```bash
# 安裝測試依賴
pip install pytest pytest-asyncio httpx

# 運行測試
pytest tests/
```

## 📈 性能監控

### 查看訓練會話
```sql
SELECT * FROM rl_experiment_sessions 
WHERE algorithm_type = 'DQN' 
ORDER BY created_at DESC;
```

### 查看訓練進度
```sql
SELECT episode_number, total_reward, success_rate, handover_latency_ms
FROM rl_training_episodes 
WHERE session_id = 1 
ORDER BY episode_number;
```

### 算法比較分析
```sql
SELECT * FROM algorithm_comparison_analysis 
WHERE scenario_type = 'urban';
```

## 🔍 故障排除

### 1. 數據庫連接失敗
```bash
# 檢查 PostgreSQL 服務狀態
sudo systemctl status postgresql

# 檢查數據庫是否存在
psql -U postgres -c "\l"

# 重新初始化數據庫
make init-db
```

### 2. API 啟動失敗
```bash
# 檢查端口是否被占用
lsof -i :8000

# 檢查環境變量
echo $DATABASE_URL

# 查看詳細日誌
python start_system.py
```

### 3. 訓練失敗
```bash
# 檢查算法是否可用
python -c "from core.algorithm_factory import get_algorithm; print(get_algorithm('dqn', 'CartPole-v1', {}))"

# 查看詳細錯誤
curl -X GET "http://localhost:8000/api/rl/status/dqn"
```

## 📋 Phase 1 完成檢查清單

### ✅ 必須完成項目
- [x] PostgreSQL 數據庫創建和初始化
- [x] 真實數據庫儲存庫實現
- [x] 摒棄 MockRepository
- [x] 完整的訓練會話管理
- [x] 詳細的訓練回合記錄
- [x] 性能指標時間序列
- [x] 數據庫健康檢查
- [x] 自動數據庫初始化
- [x] 環境變量配置
- [x] 完整的 API 文檔

### ✅ 研究級功能
- [x] 論文級別的訓練追蹤
- [x] Baseline 算法比較
- [x] 模型版本管理
- [x] 統計分析視圖
- [x] 數據匯出功能
- [x] 完整的元數據記錄

## 🎯 Phase 2 預覽

Phase 1 完成後，系統將支援：
- 真實神經網路訓練（取代時間延遲模擬）
- LEO 衛星環境模擬器
- 完整的 DQN/PPO/SAC 實現
- 決策分析和透明化
- Algorithm Explainability

## 📞 支援

如果遇到問題：
1. 檢查 [故障排除](#故障排除) 部分
2. 查看系統日誌
3. 運行部署檢查：`make deploy-check`
4. 檢查環境變量設置

---

**🎉 Phase 1 讓 LEO RL 系統邁向真正的研究級數據管理！**