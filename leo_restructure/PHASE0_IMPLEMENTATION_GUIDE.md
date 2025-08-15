# 🔥 Phase 0: 系統替換整合實施指南

**版本**: v1.0  
**更新日期**: 2025-08-15  
**狀態**: 🚀 準備實施  
**優先級**: 🔥 **最高** - 完全替代原6階段系統

## 🎯 Phase 0 總體目標

將 **leo_restructure Phase 1 + Phase 2 架構**完全替代原有的**6階段處理系統**，實現：
- ✅ **零破壞性切換**: 保持所有現有功能和性能
- ✅ **架構升級**: 從複雜6階段 → 簡潔4組件 (F1→F2→F3→A1)
- ✅ **Pure Cron保持**: 維持 < 30秒啟動的核心優勢
- ✅ **舊代碼清理**: 按 `INTEGRATION_TRACKING.md` 清理64個檔案

---

## 📋 Phase 0 執行檢查清單

### P0.1: Docker建構整合 ✅ (1-2天)

#### 🎯 目標: 將 leo_restructure 整合到 Docker 建構流程

- [ ] **修改建構腳本** (`netstack/docker/build_with_phase0_data.py`)
  ```bash
  # 移除原6階段調用
  - 註釋/移除 stage1_tle_processor.py 調用
  - 註釋/移除 stage2_filter_processor.py 調用
  - 註釋/移除 stage3_signal_processor.py 調用
  - 註釋/移除 stage4_timeseries_processor.py 調用
  - 註釋/移除 stage5_integration_processor.py 調用
  - 註釋/移除 stage6_dynamic_pool_planner.py 調用
  
  # 添加 leo_restructure 調用
  + 添加 sys.path.append('/app/src/leo_core')
  + 添加 from leo_core.run_phase1 import main as leo_main
  + 添加 asyncio.run(leo_main(['--output-dir', '/app/data']))
  ```

- [ ] **配置 Pure Cron 驅動**
  ```bash
  # 確保建構階段完成數據預計算
  - 修改 leo_restructure 輸出路徑: /tmp/phase1_outputs/ → /app/data/
  - 保持 < 30秒啟動的數據載入模式
  - 對接 Cron 調度增量更新機制
  ```

- [ ] **Docker Compose 文件更新**
  ```yaml
  # netstack/compose/core.yaml 或 core-simple.yaml
  # 確保 leo_core 目錄正確掛載
  volumes:
    - ../src/leo_core:/app/src/leo_core:ro
  ```

#### ✅ P0.1 驗證標準
- [ ] `docker build` 成功完成，使用 leo_restructure
- [ ] 建構日誌顯示 Phase 1 執行成功
- [ ] `/app/data/` 包含 leo_restructure 輸出檔案
- [ ] 建構時間 ≤ 原系統 + 5分鐘

---

### P0.2: 配置系統統一 ✅ (1天)

#### 🎯 目標: 統一配置管理，避免配置衝突

- [ ] **配置文件整合**
  ```bash
  # 1. 複製配置管理器
  cp leo_restructure/shared_core/config_manager.py netstack/config/leo_config.py
  
  # 2. 修改引用路徑
  # 在 netstack 的相關檔案中引用新配置
  from config.leo_config import create_default_config
  ```

- [ ] **仰角門檻統一**
  ```python
  # 使用現有的 docs/satellite_handover_standards.md 標準
  
  # 分層仰角門檻配置
  ELEVATION_THRESHOLDS = {
      'starlink': {
          'preparation_trigger': 15.0,  # 預備觸發
          'execution_threshold': 10.0,  # 執行門檻  
          'critical_threshold': 5.0     # 臨界門檻
      },
      'oneweb': {
          'preparation_trigger': 20.0,
          'execution_threshold': 15.0,
          'critical_threshold': 10.0
      }
  }
  
  # 環境調整係數
  ENVIRONMENT_FACTORS = {
      'open_area': 1.0,      # 開闊地區
      'urban': 1.1,          # 城市
      'mountain': 1.3,       # 山區  
      'heavy_rain': 1.4      # 強降雨
  }
  ```

- [ ] **環境變數對接**
  ```bash
  # 確保與現有環境變數系統兼容
  
  # NTPU座標 (與現有標準一致)
  OBSERVER_LAT=24.9441667
  OBSERVER_LON=121.3714
  
  # 星座配置
  STARLINK_MIN_ELEVATION=5.0
  ONEWEB_MIN_ELEVATION=10.0
  
  # 計算參數
  TIME_RANGE_MINUTES=200
  TIME_INTERVAL_SECONDS=30
  ```

#### ✅ P0.2 驗證標準
- [ ] 配置統一管理，無配置衝突
- [ ] 仰角門檻與現有標準一致
- [ ] 環境變數正確對接
- [ ] NTPU座標配置正確

---

### P0.3: 輸出格式對接 ✅ (1天)

#### 🎯 目標: 確保前端立體圖和API完全兼容

- [ ] **JSON格式統一**
  ```python
  # 創建 leo_restructure/shared_core/output_formatter.py
  
  class FrontendCompatibleFormatter:
      """前端兼容的輸出格式化器"""
      
      def format_for_frontend(self, satellite_pools):
          """格式化為前端需要的格式"""
          return {
              "satellites": self._format_satellites(satellite_pools),
              "timeline": self._format_timeline(satellite_pools),
              "handover_events": self._format_handover_events(satellite_pools)
          }
      
      def _format_timeline(self, pools):
          """生成200個時間點，30秒間隔的時間軸"""
          # 與原系統 stage4_timeseries_processor.py 輸出格式一致
          pass
  ```

- [ ] **API接口兼容**
  ```python
  # 確保現有API端點數據源切換到 leo_restructure
  
  # /api/v1/satellites/positions
  # 數據源: /app/data/phase1_final_report.json
  
  # /api/v1/satellites/constellations/info  
  # 數據源: leo_restructure 星座統計
  
  # 響應時間要求: < 100ms
  ```

- [ ] **立體圖數據格式**
  ```json
  // 確保與前端期望格式一致
  {
    "satellites": [
      {
        "id": "starlink_12345",
        "constellation": "starlink", 
        "positions": [
          {
            "timestamp": "2025-08-15T12:00:00Z",
            "elevation": 45.2,
            "azimuth": 123.5,
            "distance": 550.8,
            "coordinates_3d": [x, y, z]
          }
        ]
      }
    ],
    "handover_events": [
      {
        "timestamp": "2025-08-15T12:05:30Z",
        "event_type": "A4",
        "source_satellite": "starlink_12345",
        "target_satellite": "starlink_67890"
      }
    ]
  }
  ```

#### ✅ P0.3 驗證標準
- [ ] JSON 格式與前端期望完全一致
- [ ] API 響應時間 < 100ms
- [ ] 立體圖動畫數據正確
- [ ] 換手事件標記正確

---

### P0.4: 系統替換與驗證 🔥 (2-3天)

#### 🎯 目標: 完全切換到新系統，全面驗證功能

#### Day 1: 系統切換

- [ ] **備份舊系統**
  ```bash
  # 完整備份所有舊代碼
  
  # 1. 備份 stages 目錄
  mkdir -p netstack/src/stages_backup/$(date +%Y%m%d_%H%M)
  cp -r netstack/src/stages/ netstack/src/stages_backup/$(date +%Y%m%d_%H%M)/
  
  # 2. 備份相關服務檔案
  mkdir -p netstack/src/services_backup/$(date +%Y%m%d_%H%M)
  cp -r netstack/src/services/satellite/ netstack/src/services_backup/$(date +%Y%m%d_%H%M)/
  
  # 3. 備份根目錄舊pipeline檔案
  mkdir -p /home/sat/ntn-stack/old_pipeline_backup/$(date +%Y%m%d_%H%M)
  cp run_stage6_independent.py /home/sat/ntn-stack/old_pipeline_backup/$(date +%Y%m%d_%H%M)/ 2>/dev/null || true
  cp verify_complete_pipeline.py /home/sat/ntn-stack/old_pipeline_backup/$(date +%Y%m%d_%H%M)/ 2>/dev/null || true
  # ... 其他舊檔案
  ```

- [ ] **部署新系統**
  ```bash
  # 1. 移除舊系統 (已備份)
  rm -rf netstack/src/stages/
  
  # 2. 部署 leo_restructure
  cp -r leo_restructure/ netstack/src/leo_core/
  
  # 3. 修改相關引用
  # 更新所有引用 stages/ 的程式碼改為引用 leo_core/
  ```

- [ ] **更新 Makefile**
  ```makefile
  # 修改 /home/sat/ntn-stack/Makefile
  
  netstack-build-leo: ## 使用leo_restructure建構NetStack
      @echo "🛰️ 使用LEO重構系統建構NetStack..."
      @cd netstack && docker compose -f compose/core.yaml build
      @echo "✅ LEO重構系統建構完成"
  
  # 將預設的 netstack-build 指向新系統
  netstack-build: netstack-build-leo
  ```

#### Day 2: 全面測試

- [ ] **建構測試**
  ```bash
  # 完整建構流程測試
  make down-v  # 清理舊數據
  make build-n # 使用新系統建構
  
  # 驗證點:
  # - 建構成功完成
  # - 無錯誤或警告
  # - leo_restructure 日誌正常
  # - /app/data/ 有正確輸出
  ```

- [ ] **啟動測試**
  ```bash
  # 系統啟動測試
  make up
  
  # 驗證點:
  # - 啟動時間 < 30秒
  # - 所有容器健康
  # - 無啟動錯誤
  ```

#### Day 3: API與前端測試

- [ ] **API測試**
  ```bash
  # 健康檢查
  curl -s http://localhost:8080/health | jq .status
  # 期望: "healthy"
  
  # 衛星位置API
  curl -s http://localhost:8080/api/v1/satellites/positions | jq .total_count
  # 期望: > 0
  
  # 星座信息API  
  curl -s http://localhost:8080/api/v1/satellites/constellations/info | jq .starlink.count
  # 期望: > 0
  
  # 響應時間測試
  time curl -s http://localhost:8080/api/v1/satellites/positions > /dev/null
  # 期望: < 100ms
  ```

- [ ] **前端測試**
  ```bash
  # 前端訪問測試
  curl -s http://localhost:5173 > /dev/null
  # 期望: HTTP 200
  
  # 立體圖數據測試
  # 手動檢查: 瀏覽器訪問 http://localhost:5173
  # 驗證點:
  # - 立體圖正常載入
  # - 衛星動畫正常
  # - 時間軸控制正常
  # - 換手事件標記正常
  ```

- [ ] **性能驗證**
  ```bash
  # 啟動時間驗證
  start_time=$(date +%s)
  make up
  # 等待健康檢查通過
  while ! curl -s http://localhost:8080/health > /dev/null 2>&1; do sleep 1; done
  end_time=$(date +%s)
  startup_time=$((end_time - start_time))
  echo "啟動時間: ${startup_time}秒"
  # 期望: < 30秒
  
  # 記憶體使用驗證
  docker stats --no-stream --format "table {{.Container}}\t{{.MemUsage}}"
  # 期望: 總計 < 2GB
  ```

#### ✅ P0.4 驗證標準
- [ ] 所有舊代碼已安全備份
- [ ] 新系統完全部署成功
- [ ] 建構、啟動、API、前端全部測試通過
- [ ] 性能指標達到要求

---

## 🚨 Phase 0 緊急回退計劃

### ⚠️ 回退觸發條件
1. 建構失敗且無法在2小時內修復
2. 啟動時間 > 60秒
3. 關鍵API響應異常
4. 前端立體圖完全無法使用

### 🔄 15分鐘快速回退流程
```bash
#!/bin/bash
# Phase0 緊急回退腳本

echo "🚨 啟動 Phase 0 緊急回退..."

# 1. 停止所有服務
make down

# 2. 移除新系統
rm -rf netstack/src/leo_core/

# 3. 恢復舊系統 
backup_dir=$(ls -td netstack/src/stages_backup/*/ | head -1)
cp -r "${backup_dir}" netstack/src/stages/

# 4. 恢復舊建構腳本 (如果有修改)
git checkout netstack/docker/build_with_phase0_data.py

# 5. 重新建構啟動
make build-n && make up

echo "✅ 回退完成，系統已恢復到舊版本"
```

---

## 📊 Phase 0 成功度量指標

### 🎯 系統替換度量
- **舊系統依賴**: 0% (完全不使用 stages/)
- **新系統使用**: 100% (完全使用 leo_core/)
- **功能覆蓋率**: 100% (所有原功能正常)

### ⚡ 性能度量
- **啟動時間**: < 30秒 ✅
- **API響應時間**: < 100ms ✅  
- **建構時間**: ≤ 原系統 + 10% ✅
- **記憶體使用**: < 2GB ✅

### 🧹 清理度量
- **檔案清理**: 64個舊檔案清理狀態追蹤
- **程式碼減少**: 預期減少 30-40% 複雜程式碼
- **配置統一**: 單一配置管理系統

---

## 🏁 Phase 0 完成檢查清單

### ✅ 必須完成項目
- [ ] P0.1: Docker建構整合 - 100%完成
- [ ] P0.2: 配置系統統一 - 100%完成  
- [ ] P0.3: 輸出格式對接 - 100%完成
- [ ] P0.4: 系統替換與驗證 - 100%完成

### ✅ 驗證檢查項目
- [ ] 建構測試: `make build-n` 成功
- [ ] 啟動測試: `make up` < 30秒
- [ ] API測試: 所有端點正常響應
- [ ] 前端測試: 立體圖動畫正常
- [ ] 性能測試: 所有指標達標

### ✅ 清理檢查項目
- [ ] 舊代碼備份: 完整且可回退
- [ ] 新系統部署: 完全替換成功
- [ ] 配置衝突: 已解決所有衝突
- [ ] 文檔更新: INTEGRATION_TRACKING.md 已更新

---

**🎉 Phase 0 完成後，系統將完全使用 leo_restructure 架構，為 Phase 1 和 Phase 2 的進一步優化奠定基礎！**

---

**實施準備日期**: 2025-08-15  
**預計完成日期**: 2025-08-22 (7天內)  
**負責執行**: LEO重構團隊