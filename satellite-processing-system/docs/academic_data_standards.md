# LEO衛星換手研究：學術級數據使用標準

## 📚 文檔目的

本文檔制定了LEO衛星換手研究中的數據使用標準，確保研究成果符合頂級學術會議和期刊的同行評審要求。

## 🎯 核心原則

**基本準則**：對於影響LEO Satellite Handover論文研究的所有數據，必須使用真實數據或基於物理原理的標準模型，絕對禁止使用任意假設值或未經驗證的簡化演算法。

## 📊 數據分級標準

### 🟢 Grade A：必須使用真實數據 (絕不妥協)

#### 軌道動力學數據
- **TLE數據源**: Space-Track.org (https://www.space-track.org/)
  - 數據更新頻率：每日更新
  - 歷史數據：可回溯30天
  - 格式標準：NORAD兩行軌道根數
  
- **軌道計算算法**:
  - **SGP4**: 適用於低軌衛星 (<2000km)
  - **SDP4**: 適用於高軌衛星 (>2000km)
  - **實施標準**: AIAA 2006-6753標準
  
- **時間標準**:
  - **GPS時間**: 精確到微秒級
  - **UTC時間**: 用於用戶介面顯示
  - **時間同步**: NTP伺服器同步

#### 🚨 時間基準嚴格要求 (絕對強制)
- **SGP4軌道計算**: 必須使用 **TLE 數據的 epoch 時間** 作為計算基準
  - ❌ **絕對禁止**: 使用當前系統時間 (`datetime.now()`) 進行軌道計算
  - ❌ **絕對禁止**: 混用不同時間基準導致預測失準
  - ✅ **正確做法**: 從TLE數據提取epoch時間 (`tle_epoch_year + tle_epoch_day`)
  - ⚠️ **計算基準風險**: 使用當前系統時間替代TLE epoch時間會導致軌道計算完全錯誤

- **時間基準一致性檢查**:
  ```python
  # ✅ 正確實施
  calculation_base_time = tle_epoch_datetime  # 使用TLE epoch時間
  orbit_result = orbit_engine.compute_96min_orbital_cycle(tle_data, calculation_base_time)
  
  # ❌ 嚴格禁止
  current_time = datetime.now()  # 當前系統時間
  orbit_result = orbit_engine.compute_96min_orbital_cycle(tle_data, current_time)  # 錯誤！
  ```

- **實例教訓**:
  - **問題**: 8000+顆衛星計算結果顯示0顆可見 → 原因：使用當前時間進行軌道計算
  - **解決方案**: v6.0重構確保Stage 2正確繼承Stage 1的TLE epoch時間
  - **驗證**: 單一檔案計算器使用正確時間基準達到3,240顆衛星識別準確度

## 🚨 v6.0 重構：時間基準統一要求

### **六階段系統時間基準一致性**
- **Stage 1**: 必須使用TLE epoch時間作為`calculation_base_time`
- **Stage 2**: 必須從Stage 1 metadata正確繼承`calculation_base_time`
- **Stage 3-6**: 必須使用前級階段傳遞的時間基準，不得重新計算
- **驗證**: 所有階段metadata中的`calculation_base_time`必須一致

### **時間基準傳遞檢查清單**
```python
# ✅ Stage 1輸出檢查
assert "calculation_base_time" in stage1_metadata
assert "tle_epoch_time" in stage1_metadata

# ✅ Stage 2輸入檢查
stage1_time = extract_stage1_time_base(stage1_data)
assert stage2_time_base == stage1_time

# ✅ 後續階段檢查
assert all_stages_use_same_time_base()
```
  - **根本錯誤**: 計算基準時間設置錯誤，與TLE epoch時間不一致
  - **修復**: 強制使用 `calculation_base_time = tle_epoch_time` 進行軌道計算

#### 基礎物理計算
- **路徑損耗**:
  ```
  PL(dB) = 20log₁₀(4πd/λ)
  其中：d = 衛星-地面距離（精確計算）
       λ = 載波波長
  ```

- **都卜勒頻移**:
  ```
  Δf = (v_rel × f_c) / c
  其中：v_rel = 相對速度向量投影
       f_c = 載波頻率
       c = 光速
  ```

- **幾何計算**:
  - **球面三角學**: 精確的大圓距離計算
  - **仰角計算**: 考慮地球橢球體模型
  - **方位角計算**: 真北方位角計算

### 🟡 Grade B：基於標準模型 (可接受)

#### 信號傳播模型
- **大氣衰減**: ITU-R P.618-13標準
  - 氧氣衰減：ITU-R P.676
  - 水蒸氣衰減：ITU-R P.676
  - 雲霧衰減：ITU-R P.840

- **降雨衰減**: ITU-R P.837-7標準
  - 降雨強度統計：全球降雨區域圖
  - 頻率依賴係數：ITU-R P.838
  - 路徑長度修正：ITU-R P.618

#### 系統技術參數
- **3GPP NTN標準**: 3GPP TS 38.821
  - 頻段配置：n255, n256, n257, n258
  - 功率控制：3GPP TS 38.213
  - 同步程序：3GPP TS 38.331

- **衛星EIRP**: 製造商公開技術規格
  - **Starlink**: 37.5 dBW (公開FCC文件)
  - **OneWeb**: 40.0 dBW (公開ITU文件)
  - **Amazon Kuiper**: 預估值需註明

- **用戶設備**: 實際硬體規格
  - **接收機靈敏度**: 實測數據或規格書
  - **天線增益**: 實際天線模式測量
  - **雜訊係數**: 硬體規格書數據

### 🔴 Grade C：嚴格禁止 (零容忍)

#### 禁止使用的數據類型
- **固定假設值**:
  - ❌ 固定RSRP值 (如-85dBm)
  - ❌ 固定RSRQ值 (如-10dB)
  - ❌ 固定SINR值 (如15dB)
  
- **隨機產生數據**:
  - ❌ 隨機衛星位置
  - ❌ 隨機軌道參數
  - ❌ 隨機信號強度

- **未經驗證的簡化**:
  - ❌ 線性路徑損耗近似
  - ❌ 忽略都卜勒效應
  - ❌ 固定軌道週期假設

- **回退機制**:
  - ❌ "預設值"回退
  - ❌ "無數據時假設可見"
  - ❌ "錯誤時使用估算值"

## 🚨 實施檢查清單

### 開發前檢查
- [ ] 確認所有數據來源都有明確出處和文獻支持
- [ ] 驗證沒有使用任何"假設值"、"模擬值"、"預設值"
- [ ] 確認所有物理公式都有標準依據 (ITU-R、3GPP、IEEE)
- [ ] 檢查實施能通過同行評審的嚴格檢驗

### 代碼審查檢查
- [ ] 搜尋代碼中的關鍵字："假設", "模擬", "預設", "mock", "simulate"
- [ ] 檢查是否有魔術數字 (Magic Numbers) 沒有文獻支持
- [ ] 驗證所有常數都有物理意義和標準來源
- [ ] 確認錯誤處理不會回退到假設值

### 學術寫作檢查
- [ ] 所有使用的模型都有標準文獻引用
- [ ] 明確區分"實測數據"與"標準模型計算"
- [ ] 詳細說明所有假設的物理依據
- [ ] 提供模型驗證的比較基準

## 📖 參考文獻與標準

### 軌道力學標準
- AIAA 2006-6753: "Revisiting Spacetrack Report #3"
- NASA/TP-2010-216239: "SGP4 Orbit Determination"
- IERS Conventions (2010): 地球參考框架

### 無線通信標準  
- ITU-R P.618-13: "Earth-space path attenuation"
- ITU-R P.676-12: "Attenuation by atmospheric gases"
- 3GPP TS 38.821: "Solutions for NR to support non-terrestrial networks"

### 衛星系統文獻
- FCC IBFS File: Starlink系統技術參數
- ITU BR IFIC: OneWeb頻率協調文件
- IEEE 802.11 Working Group: WiFi衛星整合標準

## 🔄 標準更新機制

1. **季度審查**: 每季度檢查新發佈的標準更新
2. **文獻追蹤**: 追蹤頂級會議 (ICC, Globecom, VTC) 最新研究
3. **同行反饋**: 整合審稿人和同行的建議
4. **版本控制**: 所有變更都有明確的版本記錄

---

**版本**: v1.0  
**最後更新**: 2025-09-08  
**負責人**: NTN Stack研究團隊
