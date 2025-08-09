# 架構重構步驟計劃

## 🎯 Step 1: 統一配置管理 (Priority 1)

### 任務描述
創建單一配置源，解決配置分散和重複定義問題

### 具體步驟
1. **創建統一配置文件**
   ```bash
   mkdir -p /home/sat/ntn-stack/netstack/config/
   touch /home/sat/ntn-stack/netstack/config/satellite_config.yaml
   ```

2. **定義配置結構**
   ```yaml
   # satellite_config.yaml
   satellite:
     constellations:
       starlink:
         target_count: 150
         min_elevation_deg: 10.0
         frequency_ghz: 20.0
       oneweb:
         target_count: 50
         min_elevation_deg: 10.0
         frequency_ghz: 18.0
     
     observer:
       location:
         latitude: 24.9441667   # NTPU
         longitude: 121.3713889
         altitude_m: 50
       
     processing:
       time_step_seconds: 30
       orbital_period_minutes: 96
       safety_factor: 1.5
   ```

3. **創建配置管理模塊**
   ```python
   # /netstack/src/config/satellite_config_manager.py
   class SatelliteConfigManager:
       @staticmethod
       def load_config() -> Dict[str, Any]:
           # 從統一配置文件載入
       
       @staticmethod  
       def validate_config(config: Dict) -> bool:
           # 驗證配置完整性
   ```

4. **更新使用配置的模塊**
   - 修改 `satellite_selector.py` 移除硬編碼配置
   - 修改 `build_with_phase0_data.py` 使用統一配置
   - 更新所有相關模塊

### 驗收標準
- [ ] 所有配置從單一文件讀取
- [ ] 配置驗證機制正常運作
- [ ] 無硬編碼配置殘留
- [ ] 系統功能保持不變

### 預計時間：2 天

---

## 🧹 Step 2: 清理冗余代碼 (Priority 1)

### 任務描述
移除所有註釋掉的功能和未使用的代碼

### 具體步驟
1. **移除註釋掉的 AI 服務**
   - `main.py` line 42: AI 決策路由導入
   - `main.py` line 151: AI 服務初始化
   - `main.py` line 191: AI 服務關閉

2. **移除註釋掉的 RL 引擎**
   - `main.py` line 153-158: RLTrainingEngine 相關代碼

3. **移除註釋掉的數據庫初始化**
   - `main.py` line 160-169: 數據庫初始化邏輯

4. **清理 satellite_selector.py**
   - 評估 ITU-R P.618 計算的實際需求
   - 保留核心功能，移除過度複雜的部分
   - 移除 numpy mock 代碼（修復依賴問題）

5. **清理未使用的導入和模塊**
   ```bash
   # 使用工具檢查未使用的導入
   autoflake --remove-all-unused-imports --recursive netstack/
   ```

### 驗收標準
- [ ] 無註釋掉的代碼塊
- [ ] 所有導入都被使用
- [ ] 核心功能保持完整
- [ ] 代碼行數減少 20%+

### 預計時間：1 天

---

## 🔧 Step 3: 服務邊界重構 (Priority 2)

### 任務描述
分離 API 層、業務邏輯層和背景任務

### 具體步驟
1. **創建清晰的目錄結構**
   ```
   netstack/
   ├── api/                 # API 層
   │   ├── routers/
   │   ├── middleware/
   │   └── main.py
   ├── core/                # 核心業務邏輯
   │   ├── satellite/
   │   ├── algorithms/
   │   └── services/
   ├── background/          # 背景任務
   │   ├── data_loader/
   │   ├── preprocessor/
   │   └── scheduler/
   └── config/              # 配置管理
   ```

2. **重構 main.py**
   - 簡化到只負責 API 服務啟動
   - 移除複雜的 Manager 模式
   - 分離背景任務邏輯

3. **創建獨立的背景任務服務**
   ```python
   # background/satellite_background_service.py
   class SatelliteBackgroundService:
       async def start_data_initialization(self):
           # 數據初始化邏輯
       
       async def start_preprocessing(self):
           # 預處理邏輯
   ```

4. **重構 Manager 架構**
   - 保留必要的 AdapterManager
   - 簡化 ServiceManager
   - 移除過度複雜的管理層

### 驗收標準
- [ ] API 層只負責請求處理
- [ ] 核心邏輯獨立於 API
- [ ] 背景任務可獨立運行
- [ ] 清晰的服務邊界

### 預計時間：3 天

---

## 📊 Step 4: 數據流優化 (Priority 3)

### 任務描述
統一數據存儲和狀態管理邏輯

### 具體步驟
1. **統一數據流設計**
   ```
   Configuration → Core Logic → Data Storage → API Response
        ↓              ↓              ↓            ↓
   YAML Config → Processing → PostgreSQL → JSON API
   ```

2. **創建數據訪問層 (DAL)**
   ```python
   # core/data/satellite_dal.py
   class SatelliteDataAccessLayer:
       async def save_preprocessing_results(self, data):
       async def load_satellite_config(self):
       async def get_satellite_positions(self, timestamp):
   ```

3. **統一狀態管理**
   - 使用 Redis 作為狀態緩存
   - 創建狀態同步機制
   - 實施數據一致性檢查

### 驗收標準
- [ ] 數據流路徑清晰
- [ ] 統一的數據訪問接口
- [ ] 狀態一致性保證
- [ ] 緩存機制有效

### 預計時間：4 天

---

## ✅ 重構完成檢查清單

### 架構清晰度
- [ ] 服務職責單一且明確
- [ ] 依賴關係簡潔
- [ ] 代碼組織邏輯清晰

### 配置管理
- [ ] 單一配置源
- [ ] 配置驗證機制
- [ ] 環境特定配置支援

### 代碼品質
- [ ] 無冗余或註釋掉的代碼
- [ ] 導入和依賴清理完成
- [ ] 核心功能保持完整

### 性能改善
- [ ] 啟動時間 < 30 秒
- [ ] 內存使用優化
- [ ] CPU 使用率降低

### 維護性
- [ ] 新開發者能快速理解架構
- [ ] 單元測試覆蓋率 > 70%
- [ ] 文檔更新完整

---

## 🚨 風險控制

### 回滾方案
每個重構步驟前備份：
```bash
# 創建備份
cp -r netstack/ netstack_backup_$(date +%Y%m%d_%H%M%S)/
```

### 測試驗證
每步完成後執行：
```bash
# 功能測試
curl -f http://localhost:8080/health
curl -f http://localhost:8080/api/v1/satellites/positions

# 配置驗證
python -c "from config.satellite_config_manager import SatelliteConfigManager; print(SatelliteConfigManager.validate_config())"
```

### 漸進式部署
- 使用藍綠部署策略
- 保持向後兼容性
- 逐步遷移流量

---
*計劃制定時間: 2025-08-09*
*預計總完成時間: 10 工作天*
*風險等級: 中等*