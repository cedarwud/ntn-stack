# NetStack 數據同步解決方案

## 問題背景

原先的實現中，前端 EventD2Viewer 在切換到"真實"數據模式時，嘗試通過 `/netstack/data/` 路徑訪問預計算數據文件，但遇到以下問題：

1. **404 錯誤**: Vite 代理配置將路徑重寫，netstack-api 不提供靜態文件服務
2. **JSON 解析錯誤**: 大文件 (1.1GB) 在網絡傳輸中可能被截斷
3. **數據分散**: 預計算數據只存在於 NetStack 容器中，前端無法直接訪問

## 解決方案架構

### 1. 統一數據同步策略

```
NetStack 建置階段
      ↓
  生成預計算數據
      ↓
  自動同步到前端
      ↓
  前端直接訪問靜態文件
```

### 2. 核心組件

#### A. 數據同步腳本 (`scripts/sync-netstack-data.sh`)
- 統一管理所有 NetStack 數據同步
- 支持批量文件和目錄同步
- 提供同步結果驗證

#### B. 前端預計算數據服務 (`precomputedDataService.ts`)
- 直接從 `/data/` 路徑訪問靜態文件
- 支持大文件流式解析
- 完整的錯誤處理和降級機制

#### C. 自動化建置集成
- NetStack 建置完成後自動觸發數據同步
- 確保數據更新時前端同步獲得最新版本

## 實現細節

### 1. 文件結構

```
@netstack/data/                          # 源數據目錄
├── phase0_precomputed_orbits.json       # 預計算軌道數據 (1.1GB)
├── phase0_data_summary.json             # 數據摘要
├── phase0_rl_dataset_metadata.json      # RL 數據集元數據
├── phase0_build_config.json             # 建置配置
└── layered_phase0/                      # 分層分析數據
    ├── layered_analysis_20250727.json
    ├── layered_analysis_20250728.json
    └── layered_phase0_summary.json

@simworld/frontend/public/data/          # 前端靜態文件目錄
├── phase0_precomputed_orbits.json       # ← 同步後的數據
├── phase0_data_summary.json
├── phase0_rl_dataset_metadata.json
├── phase0_build_config.json
└── layered_phase0/
    ├── layered_analysis_20250727.json
    ├── layered_analysis_20250728.json
    └── layered_phase0_summary.json
```

### 2. 數據訪問路徑

**原先 (有問題):**
```
前端請求: /netstack/data/phase0_precomputed_orbits.json
Vite 代理: → http://netstack-api:8080/data/phase0_precomputed_orbits.json
結果: 404 (netstack-api 不提供靜態文件服務)
```

**現在 (已修復):**
```
前端請求: /data/phase0_precomputed_orbits.json
Vite 靜態服務: → public/data/phase0_precomputed_orbits.json
結果: 200 OK (直接提供靜態文件)
```

### 3. 數據同步流程

#### 手動同步
```bash
# 執行統一同步腳本
./scripts/sync-netstack-data.sh
```

#### 自動同步 (建置集成)
```python
# build_with_phase0_data.py 中的自動同步邏輯
sync_script = Path(__file__).parent.parent / 'scripts' / 'sync-netstack-data.sh'
if sync_script.exists():
    subprocess.run([str(sync_script)], timeout=30)
```

### 4. 前端實現改進

#### A. 智能文件載入
```typescript
// 優先載入測試文件，失敗時載入完整文件
let response = await fetch('/data/phase0_precomputed_orbits_test.json')
if (!response.ok) {
    response = await fetch('/data/phase0_precomputed_orbits.json')
}
```

#### B. 大文件處理優化
```typescript
// 使用流式解析處理大 JSON 文件
const text = await response.text()
const data = JSON.parse(text) as PrecomputedOrbitData
```

#### C. 完整錯誤處理
```typescript
try {
    // 文件載入邏輯
} catch (error) {
    console.error('預計算數據載入失敗:', error)
    // 降級到其他數據源或顯示錯誤狀態
}
```

## 使用指南

### 1. 開發環境設置

1. **初次設置**:
   ```bash
   # 同步現有數據
   ./scripts/sync-netstack-data.sh
   ```

2. **數據更新後**:
   ```bash
   # NetStack 重新建置後自動同步
   # 或手動執行同步
   ./scripts/sync-netstack-data.sh
   ```

### 2. 前端使用

用戶在 navbar > 換手事件 > d2 分頁中：
1. 點擊圖表左上方的 toggle
2. 從"模擬"切換到"真實"
3. 系統自動載入預計算軌道數據
4. 圖表顯示基於真實 TLE + SGP4 計算的衛星軌道

### 3. 故障排除

#### 問題：404 錯誤
```bash
# 檢查文件是否存在
ls -la /home/sat/ntn-stack/simworld/frontend/public/data/
# 重新同步
./scripts/sync-netstack-data.sh
```

#### 問題：JSON 解析錯誤
```bash
# 驗證文件完整性
python3 -c "import json; json.load(open('/home/sat/ntn-stack/simworld/frontend/public/data/phase0_precomputed_orbits.json')); print('JSON 格式正確')"
```

#### 問題：數據過期
```bash
# 檢查數據時間戳
cat /home/sat/ntn-stack/netstack/data/phase0_data_summary.json
# 重新建置 NetStack 數據
cd /home/sat/ntn-stack/netstack && python build_with_phase0_data.py
```

## 技術優勢

### 1. 性能優化
- **直接靜態文件服務**: 避免 API 調用開銷
- **本地文件訪問**: 消除網絡延遲
- **Vite 內建優化**: 利用 HTTP 緩存和壓縮

### 2. 可靠性提升
- **消除 API 依賴**: 減少單點故障
- **文件完整性**: 避免網絡傳輸截斷
- **降級機制**: 測試文件 → 完整文件 → 錯誤處理

### 3. 維護便利
- **統一同步腳本**: 一鍵同步所有數據
- **自動化集成**: 建置後自動同步
- **清晰的文件結構**: 易於理解和維護

## 擴展性考慮

### 1. 支持更多數據源
可以輕鬆添加其他預計算數據文件到同步列表中。

### 2. 支持增量同步
未來可以實現基於時間戳的增量同步機制。

### 3. 支持多環境
可以針對開發、測試、生產環境配置不同的同步策略。

## 結論

這個解決方案徹底解決了原有的 404 錯誤和 JSON 解析問題，並建立了一個可擴展、可維護的數據同步架構。前端現在可以穩定地訪問 NetStack 預計算數據，為 D2 事件圖表提供真實的衛星軌道數據支撐。