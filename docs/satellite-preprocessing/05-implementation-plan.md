# 📅 實施計畫

**文檔編號**: 05  
**主題**: 分階段開發步驟與時程規劃

## 1. 實施概覽

### 1.1 開發原則
- **基於現有系統**: 最大化利用已完成組件
- **漸進式改進**: 分階段實施，每階段可獨立驗證
- **最小破壞性**: 保持現有功能正常運作
- **可回滾設計**: 每個改動都可安全回滾

### 1.2 時程預估
| 階段 | 工作內容 | 預估時間 | 優先級 |
|------|---------|----------|--------|
| Phase 1 | 衛星篩選邏輯 | 3-4 天 | 高 |
| Phase 2 | API 參數優化 | 2-3 天 | 高 |
| Phase 3 | 事件檢測整合 | 4-5 天 | 中 |
| Phase 4 | 數據預計算 | 3-4 天 | 中 |
| Phase 5 | 前端整合 | 2-3 天 | 低 |
| **總計** | - | **14-19 天** | - |

## 2. Phase 1: 衛星篩選邏輯實現 (Day 1-4)

### 2.1 工作項目
```bash
# 創建衛星篩選模組
netstack/src/services/satellite/preprocessing/
├── __init__.py
├── satellite_selector.py      # 核心選擇邏輯
├── orbital_grouping.py       # 軌道分群
├── phase_distribution.py     # 相位分散
└── visibility_scoring.py     # 可見性評分
```

### 2.2 實施步驟
```python
# Day 1: 基礎架構
class SatelliteSelector:
    def __init__(self, config):
        self.config = config
        self.target_count = {
            'starlink': 120,
            'oneweb': 80
        }
    
    def select_subset(self, all_satellites):
        # 實現基本篩選邏輯
        pass

# Day 2: 軌道分群
def group_by_orbital_plane(satellites):
    # 按 RAAN 和 inclination 分群
    # Starlink: 72 個平面，每平面選 2-3 顆
    # OneWeb: 18 個平面，每平面選 4-5 顆
    pass

# Day 3: 相位分散
def ensure_phase_distribution(orbital_groups):
    # Mean Anomaly 間隔 > 15°
    # 升起時間錯開 15-30 秒
    pass

# Day 4: 整合測試
def validate_selection():
    # 驗證 8-12 顆同時可見
    # 檢查相位分散效果
    pass
```

### 2.3 驗收標準
- [ ] 從 8000+ 顆衛星中選出 120 顆 Starlink
- [ ] 從 600+ 顆衛星中選出 80 顆 OneWeb
- [ ] 任意時刻 8-12 顆可見（>95% 時間）
- [ ] 衛星升起時間錯開 > 15 秒

## 3. Phase 2: API 參數優化 (Day 5-7)

### 3.1 修改清單
```javascript
// simworld/frontend/src/services/simworld-api.ts
const API_PARAMS = {
    // OLD
    count: 20,
    min_elevation_deg: 5,
    utc_timestamp: "2025-07-26T00:00:00Z",
    
    // NEW
    count: 30,  // 或動態調整
    min_elevation_deg: 10,
    utc_timestamp: getDynamicTimestamp(),
    selection_mode: "research"  // 新增參數
}
```

### 3.2 後端支援
```python
# netstack/netstack_api/routers/satellite_ops_router.py

@router.get("/optimal_time_window")
async def get_optimal_time_window(
    constellation: str = "starlink",
    target_date: str = None
):
    """返回最佳觀測時間窗口"""
    
    # Day 5: 實現時間窗口搜尋
    window = find_optimal_window(constellation, target_date)
    
    # Day 6: 驗證窗口品質
    quality = validate_window_quality(window)
    
    # Day 7: 返回結果
    return {
        "window": window,
        "quality": quality
    }
```

### 3.3 驗收標準
- [ ] API 支援動態時間戳
- [ ] 返回最佳觀測窗口
- [ ] 前端正確使用新參數
- [ ] 衛星不再同時消失

## 4. Phase 3: 事件檢測整合 (Day 8-12)

### 4.1 事件引擎開發
```python
# Day 8-9: 基礎事件檢測
class EventDetectionEngine:
    def __init__(self):
        self.event_a4 = EventA4()
        self.event_a5 = EventA5()
        self.event_d2 = EventD2()
    
    def detect_events(self, satellite_states):
        # 實現三種事件檢測
        pass

# Day 10-11: 事件時間線
class EventTimeline:
    def generate_timeline(self, time_window):
        # 生成完整事件序列
        pass

# Day 12: API 整合
@router.get("/handover/events")
async def get_handover_events(
    start_time: str,
    end_time: str
):
    # 返回事件列表
    pass
```

### 4.2 數據結構擴展
```python
# 在時間序列中嵌入事件
timeseries_with_events = {
    "frames": [
        {
            "timestamp": "2025-01-23T10:00:00Z",
            "satellites": [...],
            "events": [
                {
                    "type": "A4",
                    "serving": "SAT-1234",
                    "candidate": "SAT-5678",
                    "rsrp_diff": 5.2
                }
            ]
        }
    ]
}
```

### 4.3 驗收標準
- [ ] A4 事件正確觸發（RSRP > -95 dBm）
- [ ] A5 事件雙門檻檢測
- [ ] D2 仰角事件識別
- [ ] 事件時間線完整生成

## 5. Phase 4: 數據預計算優化 (Day 13-16)

### 5.1 批量計算實現
```python
# Day 13: 並行計算框架
async def batch_calculate_trajectories(satellites, time_window):
    # 使用 asyncio 並行計算
    tasks = []
    for sat in satellites:
        task = calculate_single_trajectory(sat, time_window)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    return results

# Day 14: 快取策略
def setup_caching():
    # PostgreSQL 時間序列表
    # Redis 熱數據快取
    pass

# Day 15-16: 性能優化
def optimize_calculations():
    # 向量化計算
    # 空間索引
    # 增量更新
    pass
```

### 5.2 存儲優化
```sql
-- 預計算數據表
CREATE TABLE satellite_timeseries_optimized (
    satellite_id VARCHAR(50),
    time_bucket TIMESTAMP,  -- 30秒桶
    positions JSONB,        -- 批量存儲
    events JSONB,
    PRIMARY KEY (satellite_id, time_bucket)
) PARTITION BY RANGE (time_bucket);
```

### 5.3 驗收標準
- [ ] 24小時數據預計算 < 5 分鐘
- [ ] 查詢響應時間 < 50ms
- [ ] 記憶體使用 < 500MB
- [ ] 支援增量更新

## 6. Phase 5: 前端整合優化 (Day 17-19)

### 6.1 數據同步優化
```typescript
// Day 17: DataSyncContext 擴展
class EnhancedDataSync {
    // 預載入機制
    preloadNextSegment()
    
    // 事件訂閱
    subscribeToEvents()
    
    // 智能更新
    updateOnlyChanged()
}

// Day 18: 渲染優化
class OptimizedRenderer {
    // LOD 系統
    // 批量更新
    // 視錐裁剪
}

// Day 19: 整合測試
function integrationTest() {
    // 端到端測試
    // 性能測試
    // 壓力測試
}
```

### 6.2 驗收標準
- [ ] 預載入無縫切換
- [ ] 事件即時響應
- [ ] 60 FPS 渲染
- [ ] 記憶體穩定

## 7. 測試計畫

### 7.1 單元測試
```python
# 衛星選擇測試
def test_satellite_selection():
    selector = SatelliteSelector()
    result = selector.select_subset(all_satellites)
    assert 115 <= len(result) <= 125  # 容許誤差

# 事件檢測測試
def test_event_detection():
    engine = EventDetectionEngine()
    events = engine.detect_events(test_states)
    assert 'A4' in [e.type for e in events]
```

### 7.2 整合測試
```bash
# API 整合測試
curl http://localhost:8080/api/v1/satellite-ops/preprocessed_pool

# 前端整合測試
npm run test:integration

# 端到端測試
python -m pytest tests/e2e/test_satellite_preprocessing.py
```

### 7.3 性能測試
```python
performance_targets = {
    "selection_time": "< 2 seconds",
    "api_response": "< 100ms",
    "event_detection": "< 50ms/frame",
    "memory_usage": "< 1GB",
    "cpu_usage": "< 50%"
}
```

## 8. 部署計畫

### 8.1 部署步驟
```bash
# Step 1: 備份現有系統
make backup

# Step 2: 部署後端更新
docker-compose up -d netstack-api

# Step 3: 運行遷移腳本
python scripts/migrate_satellite_data.py

# Step 4: 部署前端更新
docker-compose up -d simworld-frontend

# Step 5: 驗證
make verify-deployment
```

### 8.2 回滾計畫
```bash
# 如果出現問題
make rollback-to-previous

# 恢復數據
make restore-backup

# 驗證回滾
make verify-rollback
```

## 9. 監控與維護

### 9.1 監控指標
```python
monitoring_dashboard = {
    "實時指標": [
        "可見衛星數量",
        "事件觸發率",
        "API 響應時間",
        "記憶體使用"
    ],
    "日常指標": [
        "數據更新成功率",
        "TLE 年齡",
        "預計算覆蓋率"
    ],
    "告警設置": [
        "可見衛星 < 6",
        "API 延遲 > 500ms",
        "事件檢測失敗"
    ]
}
```

### 9.2 維護任務
```bash
# 每日任務
0 2 * * * /scripts/update_tle_data.sh
0 3 * * * /scripts/precompute_trajectories.sh

# 每週任務
0 0 * * 0 /scripts/validate_satellite_pool.sh
0 1 * * 0 /scripts/cleanup_old_data.sh

# 每月任務
0 0 1 * * /scripts/full_system_validation.sh
```

## 10. 風險管理

### 10.1 技術風險
| 風險 | 可能性 | 影響 | 緩解措施 |
|-----|--------|------|----------|
| TLE 數據過期 | 中 | 高 | 多源備份、緩存機制 |
| 計算性能不足 | 低 | 高 | 預計算、批量處理 |
| 事件檢測錯誤 | 中 | 中 | 充分測試、降級機制 |
| 前端渲染瓶頸 | 低 | 中 | LOD、視錐裁剪 |

### 10.2 時程風險
- **延遲風險**: 保留 20% 緩衝時間
- **依賴風險**: 確認外部 API 可用性
- **資源風險**: 預留計算資源

---

## 總結

本實施計畫基於現有系統架構，通過 5 個階段逐步實現衛星資料預處理優化。重點在於：

1. **智能篩選**: 從海量衛星中選出研究級子集
2. **事件整合**: A4/A5/D2 事件檢測與觸發
3. **性能優化**: 預計算和快取策略
4. **無縫整合**: 最小化對現有系統的影響

預計 **3 週內完成**所有開發工作，實現穩定的 8-12 顆衛星連續可見展示。