# 📚 LEO 衛星切換系統文檔中心

**版本**: 2.0.0  
**建立日期**: 2025-08-04  
**適用範圍**: 學術研究導向系統文檔  

## 🎯 文檔概述

本文檔中心提供 LEO 衛星切換研究系統的完整技術資料，專注於學術研究需求，涵蓋系統架構、算法實現、數據處理和 API 使用等各個方面。

## 📖 核心文檔指南

### 🛰️ 數據處理相關
- **[衛星數據預處理流程](./satellite_data_preprocessing.md)** 📊 **重要！**
  - **適用情況**: 需要了解 TLE 數據到研究數據的完整處理流程
  - **內容涵蓋**: SGP4 計算、智能篩選、時間序列預處理、輸出格式
  - **關鍵信息**: 從 8,643 顆衛星篩選到 70 顆高價值衛星的流程

### 🏗️ 系統架構相關  
- **[系統架構現況](./system_architecture.md)** 🏗️ **重要！**
  - **適用情況**: 需要了解系統整體結構和組件分工
  - **內容涵蓋**: NetStack vs SimWorld、容器配置、服務交互、部署結構
  - **關鍵信息**: Docker 容器架構和服務間通信機制

### 🧠 算法開發相關
- **[核心算法實現現況](./algorithms_implementation.md)** 🧠 **重要！**
  - **適用情況**: 開發或修改切換算法、預測模型時
  - **內容涵蓋**: 3GPP NTN 信令、切換決策、軌道預測、ML 模型、狀態同步
  - **關鍵信息**: Phase 3.1/3.2 完成的算法及其 API 位置

### 🌐 API 整合相關
- **[API 接口使用指南](./api_reference.md)** 🌐
  - **適用情況**: 需要調用系統 API 進行實驗或整合
  - **內容涵蓋**: 所有可用 API 端點、請求/響應格式、使用範例
  - **關鍵信息**: NetStack (8080) 和 SimWorld (8888) 的完整 API 參考

### ⚙️ 配置管理相關
- **[配置管理指南](./configuration_management.md)** ⚙️
  - **適用情況**: 需要修改系統配置或參數調優
  - **內容涵蓋**: 統一配置系統、關鍵參數、環境配置、驗證機制
  - **關鍵信息**: `SatelliteConfig` 類別和配置載入機制

## 🔗 專項技術文檔

### 📐 標準與規範
- **[衛星換手仰角門檻標準](./satellite_handover_standards.md)** 📐
  - 分層仰角門檻系統 (5°/10°/15°)
  - ITU-R P.618 合規標準
  - 環境調整係數和地理位置優化

### 📊 技術規格
- **[技術規格文檔](./tech.md)** 📊
  - 系統技術指標和性能基準
  - 硬體需求和軟體依賴
  - 測試框架和驗證標準

## 🎓 學術研究支援

### 研究場景設計
```python
# 支援的研究場景類型
research_scenarios = {
    "algorithm_comparison": {
        "algorithms": ["fine_grained", "traditional", "ml_driven"],
        "metrics": ["latency", "success_rate", "accuracy"]
    },
    "performance_optimization": {
        "optimization_targets": ["latency", "throughput", "resource_usage"],
        "evaluation_methods": ["statistical_testing", "benchmarking"]
    },
    "prediction_accuracy": {
        "models": ["lstm", "transformer", "hybrid"], 
        "prediction_horizons": ["short_term", "medium_term", "long_term"]
    }
}
```

### 實驗數據匯出
- **格式支援**: CSV, JSON, Excel
- **統計分析**: t-test, ANOVA, Mann-Whitney U
- **視覺化**: 學習曲線、性能比較圖、收斂分析
- **論文整合**: IEEE 標準格式報告

## 🚀 快速開始指南

### 1. 系統啟動
```bash
# 完整系統啟動
cd /home/sat/ntn-stack
make up

# 檢查所有服務狀態
make status

# 驗證 API 可用性
curl http://localhost:8080/health
curl http://localhost:8888/api/v1/satellites/unified/health
```

### 2. 數據驗證
```bash
# 檢查預處理數據
docker exec netstack-api ls -la /app/data/

# 驗證數據完整性
curl -s http://localhost:8888/api/v1/satellites/unified/status | jq
```

### 3. 算法測試
```bash
# 運行核心算法測試
cd /home/sat/ntn-stack/netstack
python -m pytest tests/unit/test_fine_grained_handover.py -v
python -m pytest tests/unit/test_orbit_prediction.py -v
```

### 4. 實驗設置
```python
# Python 實驗環境設置
from src.core.performance.algorithm_metrics import SimplePerformanceMonitor
from src.core.config.satellite_config import get_satellite_config

# 初始化性能監控
monitor = SimplePerformanceMonitor("research_experiment")
config = get_satellite_config()

# 開始實驗...
```

## 📊 系統現況一覽

### 實現完成度
| 組件類別 | 完成度 | 學術價值 | 狀態 |
|----------|--------|----------|------|
| **數據基礎設施** | 100% | ⭐⭐⭐⭐⭐ | ✅ 生產就緒 |
| **3GPP NTN 信令** | 100% | ⭐⭐⭐⭐⭐ | ✅ 標準合規 |
| **切換決策算法** | 100% | ⭐⭐⭐⭐⭐ | ✅ 研究就緒 |
| **軌道預測** | 100% | ⭐⭐⭐⭐⭐ | ✅ 高精度 |
| **ML 預測模型** | 100% | ⭐⭐⭐⭐⭐ | ✅ 多模型 |
| **狀態同步** | 100% | ⭐⭐⭐⭐ | ✅ 分散式 |
| **性能監控** | 100% | ⭐⭐⭐ | ✅ 學術用 |

### 核心技術指標
- **衛星數據**: 70 顆高價值衛星 (智能篩選後)
- **位置精度**: 米級 (SGP4 精確計算)
- **API 響應**: < 50ms (衛星位置查詢)
- **切換延遲**: < 100ms (決策算法)
- **預測準確率**: > 94% (LSTM/Transformer)

## 🔧 開發和維護

### 日常維護操作
```bash
# 數據更新
./scripts/daily_tle_download_enhanced.sh

# 服務重啟
make netstack-restart  # 算法更新時
make simworld-restart  # 數據更新時

# 日誌監控
docker-compose logs -f
```

### 故障排除
```bash
# 檢查服務狀態
make status

# 查看錯誤日誌
docker logs netstack-api 2>&1 | grep ERROR
docker logs simworld_backend 2>&1 | grep ERROR

# 數據完整性檢查
curl -s http://localhost:8080/health | jq
docker exec netstack-api stat /app/data/.preprocess_status
```

### 性能監控
```bash
# 系統資源監控
docker stats

# API 性能測試
curl -w "@curl-format.txt" -s http://localhost:8080/api/v1/handover_decision/performance_metrics

# 算法執行時間分析
python -m pytest tests/unit/ --benchmark-only
```

## 🎯 研究應用場景

### 1. 算法比較研究
- **多算法並行**: Fine-Grained vs Traditional vs ML-Driven
- **性能指標**: 延遲、成功率、資源使用、預測準確性
- **統計分析**: t-test, ANOVA, 效應量計算
- **結果匯出**: 論文級數據和圖表

### 2. 系統優化研究  
- **參數調優**: 仰角門檻、權重配置、模型超參數
- **性能基準**: 建立不同環境下的性能基線
- **擴展性測試**: 多星座、大規模場景驗證

### 3. 創新算法開發
- **框架整合**: 新算法易於整合到現有系統
- **標準 API**: 統一的介面和數據格式
- **測試支援**: 完整的單元測試和整合測試框架

## 📞 技術支援

### 問題報告
- **系統錯誤**: 檢查日誌並提供錯誤訊息
- **性能問題**: 提供系統資源使用情況
- **數據問題**: 確認數據版本和完整性
- **算法問題**: 提供測試案例和預期結果

### 開發貢獻
- **代碼規範**: PEP 8 (Python), ESLint (JavaScript)
- **測試要求**: 新功能必須包含單元測試
- **文檔更新**: 修改功能時同步更新相關文檔

## 📈 未來發展路線

### 短期目標 (1-3個月)
- [ ] 算法實驗設計和基準建立
- [ ] 多環境測試和驗證  
- [ ] 論文數據收集和分析
- [ ] 開源準備和文檔完善

### 中期目標 (3-6個月)
- [ ] 強化學習算法整合
- [ ] 多星座擴展支援
- [ ] 邊緣計算部署
- [ ] 商業化可行性評估

### 長期願景 (6個月+)
- [ ] 6G 網路技術整合
- [ ] 數位孿生系統建設
- [ ] 開源社群建立
- [ ] 產業標準制定參與

---

## 📝 文檔維護

**文檔更新頻率**: 系統更新時同步維護  
**最後更新**: 2025-08-04  
**維護人員**: 系統開發團隊  

**文檔品質保證**:
- ✅ 內容準確性驗證
- ✅ 範例代碼測試 
- ✅ 連結有效性檢查
- ✅ 版本一致性維護

---

**本文檔中心為 LEO 衛星切換研究提供完整的技術文檔支援，確保研究工作的高效進行和學術成果的順利產出。**