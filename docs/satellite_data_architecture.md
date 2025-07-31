# 🛰️ 衛星數據架構 - 本地化實施方案

**文件版本**: 1.1.0
**最後更新**: 2025-07-30
**狀態**: 正式實施 + 數據格式統一

## 📋 概述

NTN Stack 系統已完全從外部 API 依賴轉換為本地數據架構，確保系統穩定性和數據一致性。

## 🔄 架構轉換

### 轉換前 (已廢棄)
- **數據來源**: Celestrak API 即時調用
- **問題**: IP 封鎖、網絡延遲、服務不穩定
- **啟動時間**: 30+ 秒 (網絡超時)

### 轉換後 (當前架構)
- **數據來源**: Docker Volume 本地數據
- **優勢**: 100% 可靠、快速啟動、無網絡依賴
- **啟動時間**: <5 秒

## 🏗️ 本地數據架構

### 數據流向
```
TLE 數據收集 → Docker Volume → NetStack → SimWorld
     ↓              ↓             ↓         ↓
  手動更新     持久化存儲    數據處理    前端顯示
```

### 核心組件

#### 1. 數據存儲層
- **位置**: Docker Volume `/app/data/`
- **格式**: JSON (預計算軌道數據)
- **持久性**: 容器重啟保持

#### 2. 數據載入層
- **服務**: `LocalTLELoader` (`/netstack/src/services/satellite/local_tle_loader.py`)
- **功能**: 自動選擇最新 TLE 數據
- **Fallback**: 內建衛星數據確保穩定性

#### 3. 數據生成層
- **主要生成器**: `simple_data_generator.py`
- **真實數據生成器**: `build_with_phase0_data.py` (已修復)
- **輸出**: Volume 掛載路徑 `/app/data/`

## 📊 數據格式統一規範 (v1.1.0 新增)

### 問題背景
在系統發展過程中，發現了數據格式不統一的問題：
- **預計算程式** (`build_with_phase0_data.py`) 生成的數據使用 `positions` 數組格式
- **API 端點** (`coordinate_orbit_endpoints.py`) 期望 `visibility_data` 數組格式
- 導致數據不匹配，需要在 API 層進行轉換，增加了複雜度和出錯風險

### 統一決策：採用預計算格式為標準

**理由**：
1. **數據源頭原則**：預計算數據是整個系統的數據源頭，其他模組適配它是最自然的
2. **性能考量**：避免不必要的數據轉換開銷
3. **維護簡化**：統一格式降低維護複雜度
4. **錯誤減少**：避免格式不匹配導致的運行時錯誤

### 標準數據格式

#### 衛星位置數據結構
```json
{
  "positions": [
    {
      "elevation_deg": 83.7,      // 仰角（度）
      "azimuth_deg": 152.6,       // 方位角（度）
      "range_km": 565.9,          // 距離（公里）
      "is_visible": true,         // 是否可見
      "timestamp": "2025-07-30T12:00:00Z"
    }
  ]
}
```

#### 字段標準
- `elevation_deg`: 衛星仰角，範圍 0-90 度
- `azimuth_deg`: 衛星方位角，範圍 0-360 度
- `range_km`: 衛星距離，單位公里
- `is_visible`: 布林值，表示衛星是否在地平線以上且可見
- `timestamp`: ISO 8601 格式的時間戳

### 實施指南

#### 新 API 開發規範
1. **必須使用** 標準的 `positions` 數組格式
2. **禁止創建** 新的數據格式變體
3. **參考實現** 見 `coordinate_orbit_endpoints.py` 中的 `_get_latest_position()` 函數修復版本

#### 現有 API 遷移
- 已修復：`/api/v1/satellites/precomputed/{location}` 端點
- 狀態：✅ 支援統一格式，向後兼容舊格式

#### 數據驗證
```python
def validate_satellite_position(position_data):
    """驗證衛星位置數據格式"""
    required_fields = ['elevation_deg', 'azimuth_deg', 'range_km', 'is_visible']
    for field in required_fields:
        if field not in position_data:
            raise ValueError(f"Missing required field: {field}")

    # 範圍驗證
    if not (0 <= position_data['elevation_deg'] <= 90):
        raise ValueError("elevation_deg must be between 0 and 90")
    if not (0 <= position_data['azimuth_deg'] <= 360):
        raise ValueError("azimuth_deg must be between 0 and 360")
```

## 🔧 實施細節

### 禁用的 API 調用
所有 Celestrak API 調用已完全禁用：

#### 修復的文件
- `tle_data_manager.py` - 檢測 Celestrak URL 並重定向到本地數據
- `satellite_data_manager.py` - 使用 `local://` 協議替代 HTTPS URL
- `satellite_precompute_router.py` - `/tle/download` 端點返回禁用信息
- `satellite_data_router_real.py` - 切換到本地數據源

### 數據新鮮度管理
- **檢查機制**: 容器啟動時自動檢查數據是否超過 7 天
- **實施位置**: `smart-entrypoint.sh`
- **自動更新**: 過期數據觸發重新生成

### 數據同步統一
- **立體圖**: 使用 `useVisibleSatellites()`
- **側邊欄**: 使用相同的 `useVisibleSatellites()`
- **結果**: 完全同步顯示

## 📁 關鍵目錄結構

```
/app/data/                           # Docker Volume 數據目錄
├── phase0_precomputed_orbits.json   # 主要軌道數據
├── layered_phase0/                  # 分層門檻數據
└── .data_ready                      # 數據完成標記

/app/tle_data/                       # TLE 原始數據
├── starlink/
│   ├── tle/                         # TLE 格式數據
│   └── json/                        # JSON 格式數據
└── oneweb/
    ├── tle/
    └── json/
```

## 🚀 性能改善

### 關鍵指標
| 指標 | 改善前 | 改善後 | 提升幅度 |
|------|--------|--------|----------|
| 啟動時間 | 30+秒 | <5秒 | 83% |
| 可用性 | 不穩定 | 100% | 完全穩定 |
| 網絡依賴 | 是 | 否 | 零依賴 |
| 數據一致性 | 不同步 | 同步 | 100% |

## 🔒 安全性

### 網絡隔離
- ✅ 無外部 API 調用
- ✅ 本地數據優先
- ✅ Fallback 機制保障

### 數據完整性
- ✅ 自動新鮮度檢查
- ✅ 文件大小驗證
- ✅ 錯誤處理機制

## 🛠️ 維護操作

### 數據更新流程
```bash
# 1. 每日自動 TLE 數據下載 (推薦)
cd /home/sat/ntn-stack/scripts
./daily_tle_download_enhanced.sh

# 1.1. 強制更新模式 (如需要)
./daily_tle_download_enhanced.sh --force

# 2. 重新建置 Docker 映像檔
docker build -t netstack:latest .

# 3. 重啟容器應用新數據 
make netstack-restart
```

### 健康檢查
```bash
# 檢查數據狀態
curl -s http://localhost:8080/health | jq

# 檢查 Volume 數據
docker exec netstack-api ls -la /app/data/

# 檢查數據新鮮度
docker exec netstack-api cat /app/data/.data_ready
```

## ⚠️ 注意事項

### 重要限制
1. **數據更新頻率**: 每日自動更新 TLE 數據 (使用 `daily_tle_download_enhanced.sh`)
2. **Volume 持久性**: 確保 Docker Volume 正確掛載
3. **Fallback 依賴**: 內建數據僅作緊急備用
4. **軌道計算精度**: 目前使用簡化圓軌道模型，建議升級至 SGP4 以提高精度

### 故障排除
- **數據過期**: 容器會自動重新生成
- **Volume 問題**: 檢查 Docker 掛載配置
- **載入失敗**: 查看 `LocalTLELoader` 日誌

## 🛰️ 軌道計算精度分析

### 當前實施狀況

**目前使用**: 簡化圓軌道模型
- **優點**: 計算速度快、資源消耗低
- **缺點**: 精度有限，可能影響換手決策準確性
- **實施位置**: `/simworld/backend/app/services/local_volume_data_service.py`

### SGP4 精確軌道計算建議

**SGP4 模型優勢**:
1. **高精度**: 考慮地球扁率、大氣阻力、重力攝動等因素
2. **標準化**: 國際通用的衛星軌道計算標準
3. **LEO 優化**: 特別適合 LEO 衛星的軌道預測
4. **研究價值**: 提高換手研究的學術價值和實用性

**對換手研究的影響**:
- **位置精度**: 提升至米級精度 (vs. 簡化模型的公里級)
- **時序準確性**: 精確的衛星可見時間預測
- **換手決策**: 更準確的信號強度和距離計算
- **覆蓋分析**: 真實的星座覆蓋模式

### 實施建議

**階段式升級方案**:

1. **Phase 1 - 混合模式** (短期):
   - 關鍵換手計算使用 SGP4
   - 一般顯示保持簡化模型
   - 性能與精度平衡

2. **Phase 2 - 完整 SGP4** (中期):
   - 全面使用 SGP4 計算
   - 預計算並快取軌道數據
   - 提升整體系統精度

3. **Phase 3 - 高級功能** (長期):
   - 軌道攝動補償
   - 多體重力場效應
   - 大氣密度變化修正

**實施成本評估**:
- **開發時間**: 2-3 週 (Phase 1), 4-6 週 (Phase 2)
- **計算資源**: 增加 20-30% CPU 使用率
- **記憶體需求**: 增加 15-25% 記憶體使用
- **論文價值**: 顯著提升研究成果的學術價值

## 📅 TLE 數據更新機制

### 自動化數據更新系統

**當前實施**: `daily_tle_download_enhanced.sh`
- **頻率**: 每日自動檢查並更新
- **智能更新**: 比較檔案修改時間和大小
- **備份機制**: 7天滾動備份，防止數據遺失
- **驗證功能**: 自動驗證下載數據的完整性

**更新流程**:
```bash
# 日常更新 (自動檢查)
./daily_tle_download_enhanced.sh

# 強制更新 (忽略快取)
./daily_tle_download_enhanced.sh --force

# 跳過更新檢查 (離線模式)
./daily_tle_download_enhanced.sh --no-update-check
```

**數據新鮮度保證**:
- **Epoch 檢查**: 驗證 TLE 數據時間戳
- **衛星數量驗證**: 確保星座完整性
- **格式驗證**: JSON 和 TLE 格式完整性檢查
- **異常處理**: 下載失敗時保持現有數據

### 定期維護建議

**每日監控**:
- 檢查 TLE 下載日誌: `/home/sat/ntn-stack/logs/tle_download.log`
- 驗證數據新鮮度: `docker exec netstack-api cat /app/data/.data_ready`

**每週維護**:
- 清理過期備份 (自動執行，保留7天)
- 檢查磁碟空間使用情況
- 驗證系統健康狀態

**每月審查**:
- 評估數據品質和覆蓋範圍
- 更新星座配置 (如有新衛星)
- 性能調優和系統優化

## 📚 相關文檔

### 技術實施
- [衛星換手仰角門檻標準](./satellite_handover_standards.md)
- [技術文檔中心](./README.md)

### 程式碼位置
- `/netstack/src/services/satellite/local_tle_loader.py` - 本地數據載入器
- `/netstack/docker/smart-entrypoint.sh` - 容器啟動腳本
- `/netstack/simple_data_generator.py` - 數據生成器
- `/scripts/daily_tle_download_enhanced.sh` - 增強版 TLE 自動下載腳本
- `/simworld/backend/app/services/local_volume_data_service.py` - 本地數據服務 (包含軌道計算)

---

**本文檔記錄 NTN Stack 衛星數據架構的重大轉換，確保系統穩定可靠運行。建議優先考慮 SGP4 升級以提升換手研究的學術價值和實用性。**