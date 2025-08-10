# Phase 2.5 架構重構計劃

> **項目**: NetStack LEO 衛星換手研究系統  
> **版本**: v1.0.0  
> **建立日期**: 2025-08-10  
> **預估工時**: 15-19 小時  

## 📋 總體目標

解決雙重篩選架構矛盾，建立統一配置管理系統，實現清晰的職責分離。

### 🎯 核心問題
- **配置分散化**: 衛星配置散佈在多個文件中
- **雙重篩選邏輯矛盾**: 建構時和運行時都在做篩選，造成邏輯衝突
- **職責不清**: 數據準備和業務邏輯混雜

### ✅ 期望成果
- 統一配置管理系統
- 清晰的建構時/運行時職責分離
- 消除配置重複和邏輯矛盾
- 保持 API 向後兼容性

## 🏗️ 架構設計

### 現有架構問題分析

```
❌ 舊架構 (問題):
┌─ 建構時 (build_with_phase0_data.py) ─┐
│  • 智能篩選: 8000+ → 555/134 顆      │
│  • max_display_starlink = 555        │ ← 配置1
└───────────────────────────────────────┘
            ↓ (數據傳遞)
┌─ 運行時 (satellite_selector.py) ────┐ 
│  • 再次篩選: 555/134 → 15/8 顆      │
│  • starlink_target = 555             │ ← 配置2 (重複!)
└───────────────────────────────────────┘

問題: 雙重篩選 + 配置重複 + 邏輯矛盾
```

### 新架構設計

```
✅ 新架構 (解決方案):
┌─ 統一配置系統 ─────────────────────┐
│  UnifiedSatelliteConfig             │ ← 單一配置源
│  • starlink: pool=555, target=15    │
│  • oneweb: pool=134, target=8       │
└─────────────────────────────────────┘
            ↓ (配置注入)
┌─ 建構時: 數據池準備 ─────────────────┐
│  SatelliteDataPoolBuilder           │
│  • 基礎篩選: 8000+ → 555/134 池     │
│  • 多樣性採樣，無智能篩選            │
└─────────────────────────────────────┘
            ↓ (充足數據池)
┌─ 運行時: 智能選擇 ───────────────────┐
│  IntelligentSatelliteSelector       │
│  • 智能選擇: 555/134 池 → 15/8 顆   │
│  • 所有智能算法集中在此              │
└─────────────────────────────────────┘

優勢: 職責清晰 + 配置統一 + 邏輯一致
```

## ⏱️ 實施階段

### 📊 階段1: 統一配置系統建立 (5-6小時)

**目標**: 建立單一配置源，消除配置分散問題

#### 任務清單
- [ ] **創建配置系統架構**
  - [ ] `netstack/config/unified_satellite_config.py` 
  - [ ] 實現 `ObserverLocation` 類
  - [ ] 實現 `ConstellationConfig` 類
  - [ ] 實現 `UnifiedSatelliteConfig` 主類

- [ ] **配置管理功能**
  - [ ] 配置驗證機制 (`validate_config()`)
  - [ ] 配置加載工具 (`load_from_file()`)
  - [ ] 環境配置支持 (dev/test/prod)

- [ ] **遷移支持**
  - [ ] 創建配置遷移腳本
  - [ ] 舊配置兼容性檢查
  - [ ] 配置對比工具

#### 技術規格

```python
# netstack/config/unified_satellite_config.py

@dataclass
class ObserverLocation:
    """觀測點配置"""
    name: str = "NTPU"
    latitude: float = 24.9441667
    longitude: float = 121.3713889
    altitude_m: float = 50.0

@dataclass  
class ConstellationConfig:
    """單個星座配置"""
    name: str
    total_satellites: int      # 建構時準備的衛星池大小
    target_satellites: int     # 運行時選擇的目標數量
    min_elevation: float       # 最小仰角門檻
    selection_strategy: str    # 篩選策略

@dataclass
class UnifiedSatelliteConfig:
    """統一衛星配置管理系統 v5.0.0"""
    
    # 版本資訊
    version: str = "5.0.0"
    config_name: str = "unified_555_134_standard"
    
    # 觀測點
    observer: ObserverLocation = field(default_factory=ObserverLocation)
    
    # 星座配置 - 555/134 統一標準
    constellations: Dict[str, ConstellationConfig] = field(default_factory=lambda: {
        "starlink": ConstellationConfig(
            name="starlink",
            total_satellites=555,      # 建構時衛星池
            target_satellites=15,      # 運行時目標
            min_elevation=10.0,
            selection_strategy="dynamic_optimal"
        ),
        "oneweb": ConstellationConfig(
            name="oneweb", 
            total_satellites=134,      # 建構時衛星池
            target_satellites=8,       # 運行時目標
            min_elevation=8.0,
            selection_strategy="coverage_optimal"
        )
    })
    
    def validate(self) -> ValidationResult:
        """配置驗證 - 確保所有配置的一致性和合理性"""
        pass
        
    def get_build_config(self) -> BuildTimeConfig:
        """獲取建構時配置"""
        pass
        
    def get_runtime_config(self) -> RuntimeConfig:  
        """獲取運行時配置"""
        pass
```

#### 驗收標準
- ✅ 所有衛星配置統一管理
- ✅ 配置驗證機制正常工作
- ✅ 支持環境特定配置
- ✅ 與現有系統兼容

---

### 🏗️ 階段2: 重構建構時預處理 (4-5小時)

**目標**: 簡化建構邏輯，專注於數據池準備

#### 任務清單
- [ ] **重構 build_with_phase0_data.py**
  - [ ] 移除 `apply_constellation_separated_filtering` 智能篩選邏輯
  - [ ] 改為基礎數據池準備邏輯
  - [ ] 集成 `UnifiedSatelliteConfig`
  - [ ] 移除硬編碼配置參數

- [ ] **創建數據池準備器**
  - [ ] 實現 `SatelliteDataPoolBuilder` 類
  - [ ] 實現多樣性採樣算法
  - [ ] 基礎有效性檢查 (TLE格式、軌道合理性)

- [ ] **更新建構流程**
  - [ ] 修改 Docker 建構腳本
  - [ ] 更新數據格式標準
  - [ ] 確保數據池完整性

#### 技術規格

```python
# 重構後的 build_with_phase0_data.py

class SatelliteDataPoolBuilder:
    """建構階段：準備充足的衛星數據池"""
    
    def __init__(self, config: UnifiedSatelliteConfig):
        self.config = config
        
    def build_satellite_pools(self) -> Dict[str, List[SatelliteData]]:
        """為每個星座準備充足的衛星池"""
        pools = {}
        
        for constellation_name, constellation_config in self.config.constellations.items():
            # 基礎篩選：只保留基本有效的衛星
            basic_filtered = self._basic_filter_satellites(constellation_name)
            
            # 多樣性採樣：確保衛星池的空間和時間多樣性
            pool = self._diverse_sampling(
                basic_filtered, 
                constellation_config.total_satellites
            )
            
            pools[constellation_name] = pool
            
        return pools
    
    def _basic_filter_satellites(self, constellation: str) -> List[SatelliteData]:
        """基礎篩選 - 只檢查數據有效性，不做智能選擇"""
        # 1. TLE 格式檢查
        # 2. 軌道參數合理性檢查  
        # 3. 覆蓋範圍基礎檢查
        pass
    
    def _diverse_sampling(self, satellites: List[SatelliteData], target_count: int) -> List[SatelliteData]:
        """多樣性採樣 - 確保衛星池的多樣性"""
        # 1. 軌道平面分散
        # 2. 相位角分散  
        # 3. 隨機採樣確保無偏
        pass
```

#### 驗收標準
- ✅ 建構時提供充足的555/134衛星池
- ✅ 移除所有智能篩選邏輯
- ✅ 數據格式標準化
- ✅ 建構時間保持在5分鐘內

---

### 🚀 階段3: 重構運行時選擇器 (3-4小時)

**目標**: 加強智能選擇，消除配置重複

#### 任務清單
- [ ] **重構 satellite_selector.py**
  - [ ] 移除內建 `SatelliteSelectionConfig`
  - [ ] 使用 `UnifiedSatelliteConfig`
  - [ ] 加強智能選擇算法
  - [ ] 優化選擇邏輯性能

- [ ] **實現新的選擇策略**
  - [ ] `dynamic_optimal` 策略 (Starlink)
  - [ ] `coverage_optimal` 策略 (OneWeb)
  - [ ] 選擇結果驗證機制

- [ ] **API 接口更新**
  - [ ] 保持向後兼容性
  - [ ] 更新方法簽名使用統一配置
  - [ ] 添加選擇過程追蹤

#### 技術規格

```python
# 重構後的 satellite_selector.py

class IntelligentSatelliteSelector:
    """運行階段：從衛星池中智能選擇最終配置"""
    
    def __init__(self, config: UnifiedSatelliteConfig):
        self.config = config
        
    def select_optimal_satellites(self, satellite_pools: Dict[str, List[SatelliteData]]) -> Dict[str, List[SatelliteData]]:
        """從衛星池中選擇最佳配置"""
        selected = {}
        
        for constellation_name, pool in satellite_pools.items():
            constellation_config = self.config.constellations[constellation_name]
            
            # 應用智能篩選算法
            optimal_satellites = self._intelligent_selection(
                pool,
                constellation_config.target_satellites,
                constellation_config.selection_strategy
            )
            
            selected[constellation_name] = optimal_satellites
            logger.info(f"選擇 {constellation_name}: {len(optimal_satellites)}/{len(pool)} 顆衛星")
            
        return selected
    
    def _intelligent_selection(self, satellite_pool: List[SatelliteData], target_count: int, strategy: str) -> List[SatelliteData]:
        """智能選擇算法 - 集中所有智能篩選邏輯"""
        if strategy == "dynamic_optimal":
            return self._dynamic_optimal_selection(satellite_pool, target_count)
        elif strategy == "coverage_optimal":
            return self._coverage_optimal_selection(satellite_pool, target_count)
        else:
            raise ValueError(f"未知選擇策略: {strategy}")
```

#### 驗收標準
- ✅ 從衛星池中選擇最佳15/8顆配置
- ✅ 移除所有重複配置
- ✅ 選擇算法性能優化 (≤2秒)
- ✅ API接口保持兼容

---

### 🧪 階段4: 測試和驗證 (3-4小時)

**目標**: 確保新架構正確性和性能

#### 任務清單
- [ ] **創建測試套件**
  - [ ] 統一配置系統測試
  - [ ] 數據池準備器測試  
  - [ ] 智能選擇器測試
  - [ ] 端到端集成測試

- [ ] **新舊架構對比**
  - [ ] 行為一致性測試
  - [ ] 性能基準對比
  - [ ] 配置正確性驗證

- [ ] **文檔和部署**
  - [ ] 更新技術文檔
  - [ ] 創建遷移指南
  - [ ] 部署驗證流程

#### 測試規格

```python
# tests/test_phase25_refactor.py

class TestUnifiedConfig:
    """統一配置系統測試"""
    
    def test_config_validation(self):
        """測試配置驗證機制"""
        pass
    
    def test_config_loading(self):
        """測試配置加載"""
        pass

class TestArchitectureConsistency:
    """架構一致性測試"""
    
    def test_build_runtime_consistency(self):
        """測試建構時和運行時的一致性"""
        # 確保建構時提供的數據池滿足運行時需求
        pass
    
    def test_satellite_count_consistency(self):
        """測試衛星數量一致性"""
        # 確保各個階段的衛星數量符合配置
        pass

class TestPerformanceBenchmark:
    """性能基準測試"""
    
    def test_build_time_performance(self):
        """建構時性能測試"""
        assert build_time <= 300  # 5分鐘
    
    def test_runtime_selection_performance(self):
        """運行時選擇性能測試"""
        assert selection_time <= 2  # 2秒
```

#### 驗收標準
- ✅ 所有測試通過 (覆蓋率 ≥ 90%)
- ✅ 性能不降低 (基準測試通過)
- ✅ 行為一致性驗證 (新舊架構結果一致)
- ✅ 文檔完整更新

## 📊 風險評估與管理

### 風險矩陣

| 風險項目 | 影響度 | 可能性 | 風險等級 | 緩解措施 |
|---------|-------|-------|----------|----------|
| **配置遷移錯誤** | 🔴 高 | 🟡 中 | 🔴 高風險 | • 創建詳細遷移腳本<br>• 多層驗證機制<br>• 回滾計劃 |
| **性能降低** | 🟡 中 | 🟢 低 | 🟢 低風險 | • 性能基準測試<br>• 算法優化<br>• 監控指標 |
| **API不兼容** | 🔴 高 | 🟢 低 | 🟡 中風險 | • 向後兼容設計<br>• API版本管理<br>• 漸進式遷移 |
| **測試覆蓋不足** | 🟡 中 | 🟡 中 | 🟡 中風險 | • 完整測試計劃<br>• 自動化測試<br>• 代碼審查 |
| **開發時間超預期** | 🟡 中 | 🟡 中 | 🟡 中風險 | • 分階段實施<br>• 里程碑檢查<br>• 範圍調整 |

### 緩解策略

#### 配置遷移安全措施
```bash
# 配置遷移安全檢查清單
1. 備份現有配置
2. 運行配置驗證工具
3. 執行遷移腳本
4. 對比新舊配置結果
5. 運行一致性測試
6. 準備回滾方案
```

#### 性能監控指標
- 建構時間: ≤ 5分鐘
- 運行時選擇: ≤ 2秒  
- 記憶體使用: 無明顯增加
- API 響應時間: 保持不變

## 🎯 成功指標

### 技術指標
- ✅ **配置統一**: 0個重複配置定義
- ✅ **架構簡化**: 消除雙重篩選邏輯矛盾
- ✅ **職責清晰**: 建構/運行時職責完全分離
- ✅ **可維護性**: 單一配置源，便於修改

### 性能指標  
- ✅ **建構效能**: 建構時間 ≤ 5分鐘
- ✅ **運行效能**: 衛星選擇 ≤ 2秒
- ✅ **資源使用**: 記憶體使用不增加
- ✅ **API性能**: 響應時間保持穩定

### 質量指標
- ✅ **測試覆蓋**: 測試覆蓋率 ≥ 90%
- ✅ **配置正確**: 配置驗證 100% 通過  
- ✅ **API兼容**: API兼容性 100% 保持
- ✅ **行為一致**: 新舊架構結果一致

## 📅 實施時間表

### 總體時間規劃

| 階段 | 任務 | 預估時間 | 累計時間 | 關鍵里程碑 |
|------|------|----------|----------|------------|
| **階段1** | 統一配置系統 | 5-6小時 | 5-6小時 | 配置系統可用 |
| **階段2** | 重構建構預處理 | 4-5小時 | 9-11小時 | 數據池準備就緒 |
| **階段3** | 重構運行選擇器 | 3-4小時 | 12-15小時 | 智能選擇優化 |
| **階段4** | 測試和驗證 | 3-4小時 | 15-19小時 | 完整驗證通過 |

### 里程碑檢查點

**🎯 里程碑1** (6小時後): 統一配置系統驗收
- 配置類架構完成
- 基礎驗證機制工作
- 配置加載測試通過

**🎯 里程碑2** (11小時後): 建構時重構驗收  
- 數據池準備器工作正常
- 建構流程無錯誤
- 數據格式驗證通過

**🎯 里程碑3** (15小時後): 運行時重構驗收
- 智能選擇算法優化
- API接口兼容性確認
- 選擇結果正確性驗證

**🎯 最終里程碑** (19小時後): 完整系統驗收
- 所有測試通過
- 性能基準達標  
- 文檔更新完成
- 部署驗證成功

## 🛠️ 實施準備

### 前置條件檢查

- [ ] **環境準備**
  - [ ] 開發環境穩定運行
  - [ ] 所有依賴套件安裝
  - [ ] Git 分支策略確定

- [ ] **備份準備**
  - [ ] 現有配置文件備份
  - [ ] 代碼倉庫備份  
  - [ ] 測試數據備份

- [ ] **工具準備**
  - [ ] 測試框架準備
  - [ ] 性能監控工具
  - [ ] 配置對比工具

### 執行準備

**建議執行時間**: 連續的工作時段，避免中斷
**建議執行環境**: 獨立的開發分支
**建議驗證策略**: 每階段完成後進行驗收測試

---

## 📞 執行確認

**Phase 2.5 架構重構計劃已完整準備就緒**

**計劃特點**:
- ✅ 詳細的技術規格和實施步驟
- ✅ 完整的風險評估和緩解措施  
- ✅ 明確的驗收標準和成功指標
- ✅ 實際可執行的時間規劃

**下一步行動**:
1. 審查確認計劃內容
2. 選擇合適的執行時機
3. 開始階段1：統一配置系統建立

---

*文檔版本: v1.0.0*  
*最後更新: 2025-08-10*  
*預估工時: 15-19 小時*