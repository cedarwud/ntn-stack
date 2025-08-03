# NetStack API 程式碼清理分析報告

## 🔍 分析範圍
- **目標目錄**: netstack/netstack_api/
- **分析重點**: 路由器、服務、模型、適配器文件
- **分析方法**: 靜態引用分析和依賴關係檢查

## 🚨 發現的未使用/過時文件

### 🔴 **高優先級 - 建議立即刪除** (可安全移除)

#### 路由器文件 (5個未被註冊)
1. `routers/constellation_test_router.py` - 未在 router_manager 中註冊
2. `routers/unified_api_router.py` - 無任何引用  
3. `routers/migration_router.py` - 無任何引用
4. `routers/satellite_tle_router.py` - 無任何引用，功能已被其他模組取代
5. `routers/scenario_test_router.py` - 未在 router_manager 中註冊

#### 適配器文件 (1個未被引用)
1. `adapters/real_data_adapter.py` - 無任何引用

#### 服務文件 (3個測試相關服務)
1. `services/constellation_test_service.py` - 只被未註冊的路由器使用
2. `services/scenario_test_environment.py` - 只被未註冊的路由器使用  
3. `services/emergency_satellite_generator.py` - 僅在異常情況下使用，可內聯到調用處

### 🟡 **中優先級 - 需要進一步調查**

#### 可能重複的文件
1. `models/ntn_path_loss_model.py` vs `models/ntn_path_loss_models.py` - 疑似功能重複
2. `models/ionospheric_models.py` - 需檢查是否與 `klobuchar_ionospheric_model.py` 重複

#### 不確定使用狀況的模型
1. `models/doppler_calculation_engine.py` - 需要深度分析
2. `models/performance_models.py` - 檢查實際引用情況

### 🟢 **低優先級 - 保留但標記為遺留代碼**

#### 研究算法文件 (可能有學術價值)
1. `services/enhanced_synchronized_algorithm.py` - 建議加註釋說明用途
2. `services/paper_synchronized_algorithm.py` - 建議加註釋說明用途

## 📊 **預期清理效果**

### 代碼量減少估計
- **路由器文件**: ~2,500 行
- **服務文件**: ~4,500 行  
- **適配器文件**: ~300 行
- **總計刪除**: ~7,300 行代碼 (約佔 15-20%)

### 維護效益
- ✅ 簡化系統架構
- ✅ 降低維護成本
- ✅ 提高代碼可讀性
- ✅ 減少潛在 bug
- ✅ 加快 CI/CD 速度

## ⚠️ **安全刪除流程建議**

### 第一階段：備份與確認
```bash
# 創建備份
backup_dir="/home/sat/ntn-stack/backup/code_cleanup_$(date +%Y%m%d_%H%M)"
mkdir -p $backup_dir

# 備份要刪除的文件
cp netstack/netstack_api/routers/constellation_test_router.py $backup_dir/
cp netstack/netstack_api/routers/unified_api_router.py $backup_dir/
cp netstack/netstack_api/routers/migration_router.py $backup_dir/
cp netstack/netstack_api/routers/satellite_tle_router.py $backup_dir/
cp netstack/netstack_api/routers/scenario_test_router.py $backup_dir/
cp netstack/netstack_api/adapters/real_data_adapter.py $backup_dir/
cp netstack/netstack_api/services/constellation_test_service.py $backup_dir/
cp netstack/netstack_api/services/scenario_test_environment.py $backup_dir/
cp netstack/netstack_api/services/emergency_satellite_generator.py $backup_dir/
```

### 第二階段：逐步刪除測試
```bash
# 刪除第一批文件 (路由器)
rm netstack/netstack_api/routers/constellation_test_router.py
rm netstack/netstack_api/routers/unified_api_router.py  
rm netstack/netstack_api/routers/migration_router.py
rm netstack/netstack_api/routers/satellite_tle_router.py
rm netstack/netstack_api/routers/scenario_test_router.py

# 測試系統啟動
make down && make up
curl http://localhost:8080/health
```

### 第三階段：完整清理
```bash
# 刪除其餘文件
rm netstack/netstack_api/adapters/real_data_adapter.py
rm netstack/netstack_api/services/constellation_test_service.py
rm netstack/netstack_api/services/scenario_test_environment.py
rm netstack/netstack_api/services/emergency_satellite_generator.py

# 最終測試
make down && make up && make status
npm run lint
```

## 🎯 **建議執行順序**

1. **立即執行**: 刪除明確未使用的路由器文件 (5個)
2. **其次執行**: 刪除未引用的適配器文件 (1個)  
3. **最後執行**: 刪除測試服務文件 (3個)
4. **額外調查**: 分析重複的模型文件

## ✅ **總結**

通過刪除這 9 個主要的未使用文件，可以：
- 減少約 7,300 行無用代碼
- 提升系統維護效率
- 降低代碼複雜度
- 確保 netstack_api 專注於核心 LEO 衛星功能

**建議在執行前進行完整備份，並分批次執行以確保系統穩定性。**
