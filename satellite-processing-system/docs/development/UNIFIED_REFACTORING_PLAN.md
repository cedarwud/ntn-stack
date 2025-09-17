# 六階段系統統一重構計劃

## 🎯 **重構目標**

將六階段系統優化到與單一檔案計算器相同的精度和性能水準，同時保持後續階段所需的豐富數據結構。

**核心原則**: 使用單一檔案計算器的高精度算法重構六階段系統，而非拋棄六階段架構。

## 📊 **問題根因分析**

### **根本問題**:
1. **Stage 2時間基準失效**: 未正確繼承Stage 1的TLE epoch時間
2. **數據傳遞精度損失**: JSON序列化導致的精度降級
3. **算法實施不一致**: 不同階段使用不同的計算庫和精度標準
4. **性能開銷**: 多層抽象和文件I/O導致的性能損失

### **預期成果**:
- **性能提升**: 執行時間從>2分鐘優化到<30秒
- **精度對齊**: 達到與單一檔案相同的3,240顆衛星識別準確度
- **功能保持**: 維持Stage 3-6所需的所有豐富數據結構

## 🛠️ **四階段重構計劃**

### **🔥 階段1: 時間基準統一 (立即執行)**

#### **1.1 Stage 2時間繼承修復**
**目標**: 確保Stage 2正確使用Stage 1的計算基準時間

**修復步骤**:
```python
# 文件: satellite-processing-system/src/stages/stage2_visibility_filter/orbital_data_loader.py
def extract_stage1_time_base(self, stage1_data: Dict) -> str:
    """從Stage 1 metadata提取計算基準時間"""
    metadata = stage1_data.get("metadata", {})

    # 優先使用TLE epoch時間
    calculation_base_time = metadata.get("calculation_base_time")
    tle_epoch_time = metadata.get("tle_epoch_time")

    if tle_epoch_time:
        self.logger.info(f"🎯 使用Stage 1 TLE epoch時間: {tle_epoch_time}")
        return tle_epoch_time
    elif calculation_base_time:
        self.logger.info(f"🎯 使用Stage 1計算基準時間: {calculation_base_time}")
        return calculation_base_time
    else:
        raise ValueError("Stage 1 metadata缺失時間基準信息")
```

**修復清單**:
- [ ] 修改 `orbital_data_loader.py` - 添加時間基準提取
- [ ] 修改 `satellite_visibility_filter_processor.py` - 使用繼承的時間基準
- [ ] 測試Stage 1→Stage 2時間傳遞
- [ ] 驗證修復後的衛星可見性結果

#### **1.2 時間格式標準化**
**目標**: 統一所有階段的時間格式和精度

**實施**:
```python
# 統一時間格式 - 使用ISO 8601高精度格式
STANDARD_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

def format_high_precision_time(timestamp):
    """統一高精度時間格式"""
    if isinstance(timestamp, datetime):
        return timestamp.strftime(STANDARD_TIME_FORMAT)
    return timestamp
```

### **⚡ 階段2: 算法庫統一 (1週內)**

#### **2.1 Skyfield標準化**
**目標**: 所有階段統一使用Skyfield庫

**統一策略**:
```python
# 文件: satellite-processing-system/src/shared/engines/unified_skyfield_engine.py
class UnifiedSkyfieldEngine:
    """統一的Skyfield計算引擎，供所有階段使用"""

    def __init__(self):
        self.ts = load.timescale()
        self.logger = logging.getLogger(__name__)

    def calculate_precise_orbital_positions(self, tle_data, calculation_base_time):
        """高精度軌道位置計算 - 與單一檔案邏輯一致"""
        # 直接使用單一檔案計算器的成功邏輯
        satellite = EarthSatellite(tle_data['line1'], tle_data['line2'],
                                 tle_data['name'], self.ts)

        # 使用TLE epoch時間作為基準
        base_time = self.ts.ut1_jd(calculation_base_time)

        # 生成時間序列 (與單一檔案相同邏輯)
        time_points = []
        for i in range(192):  # 96分鐘週期，30秒間隔
            offset_minutes = i * 0.5
            time_point = self.ts.ut1_jd(calculation_base_time + offset_minutes / (24 * 60))
            time_points.append(time_point)

        return satellite.at(time_points)
```

#### **2.2 SGP4實施統一**
**目標**: 移除自定義SGP4實施，統一使用Skyfield的標準實作

**修改清單**:
- [ ] Stage 1: 更新 `sgp4_orbital_engine.py` 使用Skyfield
- [ ] Stage 2: 更新座標轉換邏輯使用Skyfield
- [ ] 移除重複的SGP4實施代碼
- [ ] 統一座標系統轉換標準

### **🔧 階段3: 數據傳遞優化 (2週內)**

#### **3.1 高精度數據格式**
**目標**: 消除JSON序列化精度損失

**優化策略**:
```python
# 使用msgpack替代JSON，保持精度
import msgpack

def save_high_precision_data(data, filepath):
    """高精度數據保存"""
    with open(filepath, 'wb') as f:
        msgpack.pack(data, f, use_single_float=False)

def load_high_precision_data(filepath):
    """高精度數據載入"""
    with open(filepath, 'rb') as f:
        return msgpack.unpack(f, raw=False)
```

#### **3.2 內存傳遞優先**
**目標**: 最大化使用內存傳遞，減少文件I/O

**實施方案**:
```python
# 文件: satellite-processing-system/src/shared/memory_pipeline.py
class MemoryPipeline:
    """記憶體管道，支援階段間高效數據傳遞"""

    def __init__(self):
        self.stage_data = {}
        self.precision_mode = "high"

    def pass_data(self, from_stage: int, to_stage: int, data: Any):
        """階段間數據傳遞，保持內存精度"""
        self.stage_data[f"stage{from_stage}_to_stage{to_stage}"] = data
        self.logger.info(f"📡 Stage {from_stage} → Stage {to_stage} 數據傳遞完成")

    def get_data(self, from_stage: int, to_stage: int) -> Any:
        """獲取階段間數據"""
        key = f"stage{from_stage}_to_stage{to_stage}"
        return self.stage_data.get(key)
```

### **🚀 階段4: 性能優化 (3週內)**

#### **4.1 批次處理優化**
**目標**: 移除不必要的循環，使用向量化操作

**優化技術**:
```python
import numpy as np

def vectorized_satellite_calculation(satellites_data):
    """向量化衛星計算，提升性能"""
    # 批次處理所有衛星的軌道計算
    positions = []
    for batch in np.array_split(satellites_data, 10):  # 分批處理
        batch_positions = calculate_batch_orbits(batch)
        positions.extend(batch_positions)
    return positions
```

#### **4.2 智能緩存機制**
**目標**: 避免重複計算，提升執行效率

**緩存策略**:
```python
# 文件: satellite-processing-system/src/shared/computation_cache.py
class ComputationCache:
    """計算結果緩存，避免重複計算"""

    def __init__(self):
        self.orbital_cache = {}
        self.visibility_cache = {}

    def cache_orbital_result(self, tle_hash: str, result: Any):
        """緩存軌道計算結果"""
        self.orbital_cache[tle_hash] = {
            'result': result,
            'timestamp': datetime.now(),
            'ttl': timedelta(hours=1)  # 1小時過期
        }

    def get_cached_orbital_result(self, tle_hash: str) -> Optional[Any]:
        """獲取緩存的軌道計算結果"""
        cached = self.orbital_cache.get(tle_hash)
        if cached and datetime.now() - cached['timestamp'] < cached['ttl']:
            return cached['result']
        return None
```

## 📋 **實施排程**

### **Week 1: 時間基準統一**
**Day 1-2**: Stage 2時間繼承修復
**Day 3-4**: 時間格式標準化
**Day 5**: 測試和驗證
**里程碑**: Stage 1+2時間基準一致性達成

### **Week 2: 算法庫統一**
**Day 1-3**: Skyfield標準化實施
**Day 4-5**: SGP4實施統一
**里程碑**: 所有階段使用統一計算引擎

### **Week 3: 數據傳遞優化**
**Day 1-2**: 高精度數據格式實施
**Day 3-4**: 內存傳遞優先
**Day 5**: 精度測試
**里程碑**: 數據傳遞精度損失消除

### **Week 4: 性能優化**
**Day 1-2**: 批次處理優化
**Day 3-4**: 緩存機制實施
**Day 5**: 性能基準測試
**里程碑**: 性能達到單一檔案水準

## ✅ **成功驗證標準**

### **定量指標**:
1. **執行時間**: Stage 1+2 < 30秒 (當前>2分鐘)
2. **精度對齊**: 衛星識別數量 ≈ 3,240顆 (單一檔案水準)
3. **記憶體效率**: 記憶體使用 < 2GB
4. **數據完整性**: 後續階段(3-6)正常運行

### **定性指標**:
1. **學術合規性**: Grade A標準合規
2. **代碼品質**: 統一編碼標準
3. **維護性**: 統一架構和接口
4. **文檔同步**: 程式與文檔完全一致

## 🚨 **風險評估和緩解**

### **高風險項目**:
1. **時間基準修復**: 可能影響後續階段
   - **緩解**: 充分測試，保持向後兼容
2. **算法庫替換**: 可能改變計算結果
   - **緩解**: 逐步替換，對比驗證

### **中風險項目**:
1. **數據格式變更**: 可能影響序列化
   - **緩解**: 保持格式兼容性
2. **性能優化**: 可能引入新bug
   - **緩解**: 增量優化，充分測試

## 📚 **文檔更新計劃**

### **需要更新的文檔**:
1. `docs/data_processing_flow.md` - 反映新的高精度流程
2. `docs/stages/stage1-tle-loading.md` - 更新算法實施說明
3. `docs/stages/stage2-filtering.md` - 更新時間基準繼承邏輯
4. `docs/academic_data_standards.md` - 強化時間基準要求
5. `docs/shared_core_architecture.md` - 添加統一引擎說明

### **新增文檔**:
1. `UNIFIED_REFACTORING_GUIDE.md` - 重構指導手冊
2. `PRECISION_VERIFICATION_REPORT.md` - 精度驗證報告
3. `PERFORMANCE_OPTIMIZATION_GUIDE.md` - 性能優化指南

---

**下一步行動**: 開始執行階段1的Stage 2時間基準修復
**預計完成時間**: 4週
**成功標準**: 六階段系統達到單一檔案計算器的精度和性能水準