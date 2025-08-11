# SimWorld Backend 重構路線圖

## 🎯 重構目標

### 主要目標
- **簡化架構**: 移除與 LEO satellite handover 研究無關的功能
- **提升維護性**: 減少技術債務，改善程式碼品質
- **保持功能性**: 確保核心研究功能完整保留
- **支援擴展**: 為未來的 Sionna 物理層模擬和 3D 渲染預留接口

### 量化指標
- 減少檔案數量: 12 個 (-15%)
- 減少程式碼行數: ~2,500 行 (-20%)
- 降低複雜度: 移除 3 個功能域 (-25%)
- 提升測試覆蓋率: 從 60% 提升至 80%

## 🗓️ 分階段執行計劃

### Phase 1: 風險評估與備份 (Week 1)

#### 目標
建立安全的重構環境，確保可以安全回滾

#### 任務清單
- [ ] **完整程式碼備份**
  - 建立重構專用分支 `refactor/simworld-backend-cleanup`
  - 標記當前版本 `v-before-refactor`
  - 建立本地備份目錄

- [ ] **相依性分析**  
  - 使用工具分析模組間依賴關係
  - 識別循環依賴和緊耦合組件
  - 建立相依性圖表

- [ ] **測試基準建立**
  - 執行現有測試套件，建立測試基準
  - 識別缺乏測試覆蓋的關鍵功能
  - 建立效能測試基準

#### 可交付成果
- 完整的程式碼備份
- 相依性分析報告  
- 測試基準報告
- 風險評估文檔

### Phase 2: 低風險組件移除 (Week 2)

#### 目標
移除完全獨立、無依賴的組件，降低系統複雜度

#### 優先移除清單
1. **UAV 追踪模組**
   - `api/routes/uav.py` 
   - 相關數據模型和服務
   - UAV 相關的 API 端點

2. **開發期工具**
   - `services/precision_validator.py`
   - `services/distance_validator.py`  
   - `api/v1/distance_validation.py`

3. **過時遷移代碼**
   - `services/skyfield_migration.py`
   - 相關的相容性代碼

#### 執行步驟
```bash
# 1. 移除 UAV 追踪模組
rm simworld/backend/app/api/routes/uav.py
# 更新路由註冊，移除 UAV 相關端點

# 2. 移除開發期工具
rm simworld/backend/app/services/precision_validator.py
rm simworld/backend/app/services/distance_validator.py
rm simworld/backend/app/api/v1/distance_validation.py

# 3. 移除過時遷移代碼  
rm simworld/backend/app/services/skyfield_migration.py
```

#### 驗證步驟
- [ ] 執行完整測試套件
- [ ] 檢查 API 端點正常運行
- [ ] 驗證衛星相關功能無影響
- [ ] 確認前端正常載入 3D 模型

### Phase 3: 系統監控域移除 (Week 3)

#### 目標
移除系統資源監控功能域，簡化系統架構

#### 移除組件
- `domains/system/` (完整目錄)
- `domains/system/api/system_api.py`
- `domains/system/services/system_resource_service.py`
- `domains/system/models/system_models.py`

#### 執行步驟
```bash
# 1. 移除系統監控域
rm -rf simworld/backend/app/domains/system/

# 2. 更新主路由配置
# 從 main.py 中移除 system API 路由註冊

# 3. 更新依賴注入配置
# 從 dependencies.py 中移除系統監控相關依賴
```

#### 影響評估
- **正面影響**: 減少系統複雜度，降低維護成本
- **風險**: 可能有其他模組依賴系統監控功能
- **緩解措施**: 仔細檢查依賴關係，提供替代方案

### Phase 4: 程式碼重構與優化 (Week 4)

#### 目標
重構重複程式碼，優化現有功能

#### 重構任務

1. **距離計算邏輯合併**
   - 分析 `distance_calculator.py` 和其他距離計算邏輯
   - 建立統一的距離計算接口
   - 移除重複的實現

2. **座標轉換優化**
   - 重構 `coordinate_service.py` 
   - 統一座標系統轉換接口
   - 優化轉換演算法效能

3. **API 路由重組**
   - 重新組織 API 路由結構
   - 統一錯誤處理機制
   - 改善 API 文檔

#### 程式碼品質改善
```bash
# 1. 執行程式碼格式化
black simworld/backend/app/
isort simworld/backend/app/

# 2. 執行程式碼品質檢查
flake8 simworld/backend/app/
pylint simworld/backend/app/

# 3. 執行型別檢查  
mypy simworld/backend/app/
```

### Phase 5: 測試完善與文檔更新 (Week 5)

#### 目標
完善測試覆蓋，更新相關文檔

#### 測試任務
- [ ] **單元測試完善**
  - 為核心衛星功能新增單元測試
  - 達到 80% 測試覆蓋率目標
  - 新增邊界條件測試

- [ ] **整合測試更新**
  - 更新 API 整合測試
  - 新增端到端測試場景
  - 驗證前後端整合

- [ ] **效能測試**
  - 測試軌道計算效能
  - 測試 API 響應時間
  - 驗證記憶體使用優化

#### 文檔更新
- [ ] 更新 API 文檔
- [ ] 更新架構設計文檔  
- [ ] 更新部署指南
- [ ] 新增重構變更說明

## 🛡️ 風險管理策略

### 高風險場景及應對

#### 場景1: 隱藏依賴導致系統故障
**風險**: 移除組件後發現有隱藏依賴
**機率**: 中等
**影響**: 高
**應對策略**:
- 使用自動化工具分析依賴關係
- 階段性移除，每階段後完整測試
- 準備快速回滾機制

#### 場景2: 前端功能受影響
**風險**: API 變更影響前端功能
**機率**: 低
**影響**: 中等  
**應對策略**:
- 保持 API 向後相容
- 與前端團隊密切協調
- 建立 API 版本控制

#### 場景3: 效能回歸
**風險**: 重構導致效能下降
**機率**: 低
**影響**: 中等
**應對策略**:
- 建立效能基準測試
- 重構過程中持續效能監控
- 準備效能優化方案

### 回滾策略

#### 快速回滾程序
1. **即時回滾**: 發現嚴重問題時
   ```bash
   git checkout main
   git reset --hard v-before-refactor
   ```

2. **部分回滾**: 針對特定功能問題
   ```bash
   git revert <specific-commit>
   ```

3. **段階回滚**: 回滚到特定階段
   ```bash
   git checkout phase-2-backup
   ```

## 📊 進度追蹤機制

### 每週進度檢查點
- **Week 1**: 備份完成，依賴分析完成
- **Week 2**: 低風險組件移除完成，測試通過  
- **Week 3**: 系統監控域移除完成，無功能回歸
- **Week 4**: 程式碼重構完成，程式碼品質提升
- **Week 5**: 測試完善，文檔更新，重構完成

### 品質門檻
每階段必須通過以下檢查：
- [ ] 所有現有測試通過
- [ ] API 健康檢查正常
- [ ] 前端載入正常
- [ ] 記憶體使用無異常增長
- [ ] 響應時間無顯著變化

### 成功標準
重構完成後需達到：
- [ ] 移除目標組件完成 (12個檔案)
- [ ] 測試覆蓋率 ≥ 80%
- [ ] API 響應時間 ≤ 100ms (90th percentile)  
- [ ] 記憶體使用減少 ≥ 15%
- [ ] 程式碼品質評分 ≥ 8.5/10

## 🚀 後續規劃

### 短期目標 (1-2個月)
- 監控重構後系統穩定性
- 收集使用者反饋並優化
- 建立持續整合的程式碼品質檢查

### 中期目標 (3-6個月)  
- 基於簡化架構開發新的 handover 算法
- 深度整合 Sionna 物理層模擬
- 優化 3D 渲染效能

### 長期目標 (6-12個月)
- 建立模組化的衛星通訊仿真平台
- 支援多種 LEO 星座的 handover 研究
- 開發自動化的系統優化工具

---

**重構原則**: 每個階段都要確保系統的核心功能完整，漸進式改進，確保研究工作不受影響。
EOF < /dev/null
