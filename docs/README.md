# 📚 LEO 衛星切換系統文檔中心

**版本**: 4.0.0  
**建立日期**: 2025-08-04  
**更新日期**: 2025-08-06  
**適用範圍**: 學術研究導向系統 - 文檔導航中心

## 🎯 系統概述

本系統專注於 **LEO 衛星切換優化研究**，使用完整 SGP4 算法和真實 TLE 數據，絕不使用簡化算法或模擬數據。支援 8,042 顆 Starlink 和 651 顆 OneWeb 衛星的真實軌道計算與換手決策研究。

## 📖 核心文檔導航

### 🔧 **[技術實現指南](./technical_guide.md)** - **新整合！** ⭐
**一站式技術文檔** - 包含：
- 完整 SGP4 算法實現與 Pure Cron 驅動架構  
- 3GPP NTN 信令系統與精細化切換決策
- ML 預測模型與狀態同步機制
- 統一配置管理與性能監控

### 🌐 **[API 接口使用指南](./api_reference.md)**
完整 API 參考 - NetStack (8080) 和 SimWorld (8888) 端點、格式、範例

### 🏗️ **[系統架構現況](./system_architecture.md)**
系統組件分工、容器配置、服務交互機制

### 📐 **[衛星換手仰角門檻標準](./satellite_handover_standards.md)**
分層仰角門檻系統 (5°/10°/15°)、ITU-R P.618 合規、環境調整係數

## 📂 參考資料

### 🛰️ 衛星數據分析 ⭐ **v4.0.0 重大更新**
- **[衛星數據預處理流程](./satellite_data_preprocessing.md)** - ⭐ **新增完整軌道週期分析** - Pure Cron 驅動 + 651+301顆衛星池配置
- **[核心算法實現現況](./algorithms_implementation.md)** - 算法實現細節和API位置  

### 📎 附錄資料
- **[附錄：詳細分析報告](./appendix/)** - 低頻參考資料和詳細分析文檔

## 🚀 快速開始

### 1. 系統啟動
```bash
cd /home/sat/ntn-stack
make up                                    # 啟動完整系統
make status                                # 檢查服務狀態
```

### 2. 健康檢查
```bash
curl http://localhost:8080/health | jq                              # NetStack API
curl http://localhost:8888/api/v1/satellites/unified/health | jq    # SimWorld API
```

### 3. 基礎測試
```bash
# 測試衛星時間序列數據
curl "http://localhost:8888/api/v1/satellites/unified/timeseries?constellation=starlink&duration_minutes=5" | jq

# 測試切換決策 API
curl http://localhost:8080/api/v1/handover_decision/performance_metrics | jq
```

## 📊 系統指標

### 技術規格
- **衛星數量**: 8,042 顆 Starlink + 651 顆 OneWeb (2025年實際數據)
- **算法精度**: 完整 SGP4，位置精度 < 100m，預測準確率 > 94%
- **API 響應**: < 50ms (衛星位置查詢)，< 100ms (切換決策)
- **系統啟動**: < 30秒 (Pure Cron 驅動架構)

### 研究能力
- **算法比較**: Fine-Grained vs Traditional vs ML-Driven
- **性能指標**: 延遲、成功率、準確性、資源使用
- **數據匯出**: CSV, JSON, Excel，支援 IEEE 標準格式
- **統計分析**: t-test, ANOVA, Mann-Whitney U

## 🔧 維護指令

```bash
# 日常監控
make status                               # 系統狀態
docker logs netstack-api | grep ERROR    # 錯誤日誌檢查
tail -f /tmp/tle_download.log            # TLE 更新日誌

# 性能測試  
cd /home/sat/ntn-stack/netstack
python -m pytest tests/unit/test_fine_grained_handover.py -v
python -m pytest tests/unit/test_orbit_prediction.py -v
```

## 🎓 學術研究支援

### 實驗場景
- **多算法並行比較**：同時運行不同切換算法進行性能對比
- **參數敏感性分析**：仰角門檻、權重配置的影響研究
- **預測模型評估**：LSTM、Transformer、混合模型準確性比較

### 論文數據產出
- **IEEE 標準報告**：自動生成符合學術發表要求的數據格式
- **統計顯著性**：支援 t-test、ANOVA 等統計檢驗
- **可重現性**：完整的實驗配置和數據版本控制

---

## 🔗 相關連結

- **GitHub Issues**: 問題回報和功能請求
- **技術支援**: 查看 [technical_guide.md](./technical_guide.md) 故障排除章節
- **貢獻指南**: 代碼規範和測試要求請參考各技術文檔

---

**本文檔中心為 LEO 衛星切換研究提供完整的導航和快速開始支援，確保研究工作的高效進行。**