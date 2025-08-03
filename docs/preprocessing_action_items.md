# 衛星預處理系統改進行動項目

**建立日期**: 2025-08-03
**優先級**: 高

## 🚨 立即行動 (本週內)

### 1. 統一候選衛星數量配置
**問題**: 不同模組使用不同的衛星數量限制 (8/30/40/50)
**行動**:
```python
# 建議創建全局配置文件: /netstack/config/satellite_config.py
MAX_CANDIDATE_SATELLITES = 8  # SIB19 規範
MAX_PREPROCESS_SATELLITES = 40  # 預處理優化
MAX_BATCH_COMPUTE_SATELLITES = 50  # 批次計算
```

### 2. 預處理計算精度一致性
**問題**: 建置階段使用簡化模型，運行時使用 SGP4
**行動**:
- 評估 SGP4 在建置階段的性能影響
- 如果可接受 (< 5分鐘)，統一使用 SGP4
- 否則，在輸出元數據中明確標註計算方法

## 📋 中期改進 (本月內)

### 3. 文檔更新
**需要更新**:
- `docs/tech.md` - 增加智能篩選機制說明
- `docs/data.md` - 已更新，需持續維護
- 創建配置說明文檔

### 4. 自動化測試
**建立測試**:
```bash
# 預處理數據驗證測試
python tests/test_preprocessing_accuracy.py

# SGP4 vs 簡化模型對比測試  
python tests/test_orbital_model_comparison.py
```

## 🔄 長期優化 (季度計畫)

### 5. 性能優化
- 並行化 SGP4 計算
- 使用 Cython/Numba 加速關鍵路徑
- 考慮 GPU 加速可能性

### 6. 強化學習整合準備
- 確保預處理數據格式支援 RL 訓練
- 建立數據管道接口
- 準備狀態空間定義

## 📝 程式碼修改建議

### 修改 1: preprocess_120min_timeseries.py
```python
# 第 139-142 行
# 原始:
satellite_timeseries = await self._calculate_simplified_satellite_timeseries(
    sat_data, start_time
)

# 建議:
if self.use_sgp4_in_build:  # 新增配置選項
    satellite_timeseries = await self._calculate_sgp4_satellite_timeseries(
        sat_data, start_time
    )
else:
    satellite_timeseries = await self._calculate_simplified_satellite_timeseries(
        sat_data, start_time
    )
    # 添加元數據標記
    satellite_timeseries['metadata']['calculation_method'] = 'simplified'
```

### 修改 2: sib19_unified_platform.py
```python
# 添加配置驗證
def validate_candidate_count(self, count: int) -> int:
    """確保候選衛星數量符合 SIB19 規範"""
    if count > self.max_tracked_satellites:
        logger.warning(
            f"候選衛星數量 {count} 超過 SIB19 限制 {self.max_tracked_satellites}，"
            f"將截斷至 {self.max_tracked_satellites}"
        )
        return self.max_tracked_satellites
    return count
```

## ✅ 驗證檢查清單

完成修改後，執行以下驗證:

- [ ] 所有測試通過
- [ ] 預處理數據大小 < 100MB
- [ ] Docker 建置時間 < 10分鐘
- [ ] 運行時 API 響應 < 100ms
- [ ] 文檔已更新
- [ ] 代碼審查通過

## 📞 聯絡人

- 技術問題: 系統架構師
- 規範確認: 研究團隊
- 測試驗證: QA 團隊

---

**注意**: 這些改進項目旨在提升系統符合規範的程度，同時保持現有的性能優勢。