# Phase 0 → Phase 1 統一重構計劃

## 🎯 核心問題
系統中存在混淆的命名：實際的 Phase 1 功能卻使用 phase0 命名，造成架構不清晰。

## 📊 Phase 0 命名現況分析

### 🔍 發現的 Phase 0 相關文件
根據系統掃描，發現以下需要重構的文件：

#### 核心處理器文件
```bash
# 主要處理器
netstack/docker/build_with_phase0_data_refactored.py  # 核心數據處理器
netstack/src/services/satellite/phase0_integration.py # 衛星整合服務
netstack/generate_layered_phase0_data.py             # 分層數據生成器

# 數據配置文件
netstack/data/phase0.env                             # 環境配置
netstack/data/phase0_rl_dataset_metadata.json       # RL數據集元數據
netstack/data/phase0_data_summary.json              # 數據摘要
netstack/data/phase0_build_config.json              # 建構配置
```

#### API 和服務引用
```bash
# API路由器中的引用
netstack/netstack_api/routers/coordinate_orbit_endpoints.py  # 多處 phase0 引用
netstack/netstack_api/routers/simple_satellite_router.py     # get_phase0_satellite_data()
netstack/netstack_api/services/orbit_calculation_engine.py   # phase0_precomputed_orbits.json

# 配置管理
netstack/netstack_api/app/core/config_manager.py            # phase0_data_dir 配置
```

#### 數據路徑引用
```bash
# 常見的數據文件路徑
/app/data/phase0_precomputed_orbits.json    # 預計算軌道數據
/app/data/phase0_data_summary.json          # 數據摘要
/app/data/phase0_build_config.json          # 建構配置
/app/data/layered_phase0/                   # 分層數據目錄
```

## 🔄 重構策略

### 階段 1: 文件重命名
| 原始文件名 | 目標文件名 | 影響範圍 |
|------------|------------|----------|
| `build_with_phase0_data_refactored.py` | `build_with_phase1_data.py` | 核心處理器 |
| `phase0_integration.py` | `phase1_integration.py` | 衛星服務 |
| `generate_layered_phase0_data.py` | `generate_layered_phase1_data.py` | 數據生成 |
| `phase0_precomputed_orbits.json` | `phase1_precomputed_orbits.json` | 數據文件 |
| `layered_phase0/` | `layered_phase1/` | 數據目錄 |

### 階段 2: 代碼引用更新
```python
# 類名和變數名統一更新
Phase0Integration → Phase1Integration
phase0_loader → phase1_loader
get_phase0_satellite_data() → get_phase1_satellite_data()
phase0_data_dir → phase1_data_dir
```

### 階段 3: 配置和路徑更新
- 環境變數中的 `phase0` → `phase1`
- API 端點路徑統一
- Docker Volume 掛載路徑更新
- 文檔引用更新

## 🎯 重構完成後的架構

### 統一的 Phase 1 架構
```
Phase 1: TLE數據載入與SGP4精確軌道計算
├── 核心處理器: netstack/docker/build_with_phase1_data.py
├── 衛星服務: netstack/src/services/satellite/phase1_integration.py  
├── 數據文件: /app/data/phase1_precomputed_orbits.json
├── 分層數據: /app/data/layered_phase1/
└── API服務: phase1_* 統一命名
```

## ✅ 重構效益

### 1. **架構清晰性**
- 消除 phase0/phase1 命名混淆
- 統一的概念模型
- 符合文檔中的 Phase 1 定義

### 2. **維護便利性**
- 一致性命名降低認知負擔
- 減少開發者困惑
- 提高代碼可讀性

### 3. **文檔一致性**
- 與技術文檔中的 Phase 1 概念對齊
- 消除文檔與實現的不一致

## 🚀 實施計劃

### Step 1: 備份當前系統
```bash
# 創建備份
git branch backup-before-phase0-to-phase1-refactor
```

### Step 2: 文件重命名
```bash
# 核心文件重命名
mv netstack/docker/build_with_phase0_data_refactored.py \
   netstack/docker/build_with_phase1_data.py
```

### Step 3: 代碼更新
- 批量更新所有 Python 文件中的引用
- 更新 import 語句
- 更新類名和函數名

### Step 4: 配置更新
- Docker compose 配置更新
- 環境變數更新
- API 路由更新

### Step 5: 測試驗證
- 功能測試確保系統正常運作
- API 測試確保端點正常
- 數據完整性驗證

## ⚠️ 風險控制

### 高風險項目
- **核心處理器重命名**：可能影響整個數據處理流程
- **數據文件路徑變更**：需要確保所有引用同步更新

### 緩解措施
- 階段性實施，每步驗證
- 保留原始備份
- 詳細的回滾計劃

## 📋 驗證清單

- [ ] 所有 phase0 文件成功重命名為 phase1
- [ ] Python 代碼中無 phase0 殘留引用
- [ ] API 端點正常響應
- [ ] 數據處理流程正常運作
- [ ] 文檔更新完成
- [ ] 測試全部通過

---

**本計劃將徹底解決 phase0/phase1 命名混淆問題，實現清晰統一的架構。**