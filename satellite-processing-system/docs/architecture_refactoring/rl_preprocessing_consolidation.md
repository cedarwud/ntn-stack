# 🤖 強化學習預處理功能整合計畫 (RL Preprocessing Consolidation Plan)

## 🎯 整合目標

**解決強化學習(RL)預處理功能在多個階段重複實現的問題，建立統一的RL數據流架構，提升衛星換手決策的學習效率。**

### 📊 RL功能分布現狀

| 階段 | RL功能實現 | 實現規模 | 功能重疊度 | 整合優先級 |
|------|-----------|----------|------------|------------|
| **Stage 3** | 信號品質RL預處理 | ~200行 | 🔴 高 (85%) | 🔥 緊急移除 |
| **Stage 4** | 核心RL預處理引擎 | ~400行 | - | ✅ 保留強化 |
| **Stage 6** | 覆蓋優化RL預處理 | ~150行 | 🟡 中 (60%) | 🟡 部分移除 |

---

## 🔍 RL功能重複分析

### Stage 3: 信號分析階段 (🚫 需要移除)

#### 當前RL實現
```python
# 檔案: stage3_signal_analysis_processor.py
class Stage3SignalAnalysisProcessor:
    def _prepare_rl_features(self, signal_data):
        """🚫 移除: RL特徵準備"""
        pass

    def _normalize_rl_data(self, features):
        """🚫 移除: RL數據正規化"""
        pass

    def _create_rl_state_vectors(self, normalized_data):
        """🚫 移除: RL狀態向量建立"""
        pass

    def _export_rl_training_data(self, state_vectors):
        """🚫 移除: RL訓練數據匯出"""
        pass
```

#### 移除原因
- **職責越界**: Stage 3應專注信號分析，不應處理RL預處理
- **功能重複**: 與Stage 4的RL預處理功能85%重疊
- **數據流混亂**: 造成RL訓練數據來源不統一

### Stage 4: 時序預處理階段 (✅ 保留並強化)

#### 核心RL引擎
```python
# 檔案: timeseries_preprocessing_processor.py
class UnifiedRLPreprocessor:
    def preprocess_handover_features(self, signal_analysis_data):
        """✅ 保留: 換手決策RL預處理"""
        return {
            'state_features': self._extract_state_features(signal_analysis_data),
            'action_space': self._define_action_space(),
            'reward_signals': self._prepare_reward_signals(),
            'temporal_sequences': self._build_temporal_sequences()
        }

    def preprocess_coverage_features(self, visibility_data):
        """✅ 新增: 覆蓋優化RL預處理"""
        return {
            'coverage_state': self._extract_coverage_state(visibility_data),
            'satellite_actions': self._define_satellite_actions(),
            'coverage_rewards': self._calculate_coverage_rewards()
        }
```

#### 強化內容
- **標準化介面**: 統一RL預處理入口
- **多場景支持**: 換手決策 + 覆蓋優化
- **高效實現**: 優化數據處理管道

### Stage 6: 動態池規劃階段 (🟡 部分清理)

#### 當前RL實現
```python
# 檔案: stage6_processor.py
class Stage6Processor:
    def _preprocess_for_coverage_rl(self, pool_data):
        """🟡 重構: 改為調用Stage 4統一介面"""
        pass

    def _optimize_satellite_selection_rl(self, preprocessed_data):
        """✅ 保留: Stage 6特有的優化邏輯"""
        pass
```

#### 重構策略
- **移除重複**: 刪除與Stage 4重疊的RL預處理
- **保留特化**: 保留Stage 6特有的動態規劃邏輯
- **介面調用**: 改為調用Stage 4的統一RL預處理

---

## 🛠️ 整合實施方案

### Phase 1: Stage 3 RL功能移除 (1週)

#### Step 1: 移除RL相關方法
```python
# 🚫 完全移除的方法列表
- _prepare_rl_features()           # ~50行
- _normalize_rl_data()            # ~30行
- _create_rl_state_vectors()      # ~40行
- _export_rl_training_data()      # ~25行
- _configure_rl_hyperparameters() # ~35行
- _validate_rl_data_quality()     # ~20行
```

#### Step 2: 清理配置參數
```python
# 🚫 移除RL相關配置
self.rl_preprocessing_enabled = config.get('rl_preprocessing', False)
self.rl_feature_dimension = config.get('rl_features', 128)
self.rl_sequence_length = config.get('rl_sequence', 10)
```

#### Step 3: 調整輸出格式
```python
# 🚫 移除RL相關輸出字段
- 'rl_features'           # RL特徵向量
- 'rl_state_vectors'      # RL狀態向量
- 'rl_training_ready'     # RL訓練準備狀態
- 'rl_metadata'           # RL元數據
```

### Phase 2: Stage 4 RL引擎強化 (1週)

#### Step 1: 建立統一RL預處理介面
```python
# ✅ 新增: 統一RL預處理引擎
class UnifiedRLPreprocessor:
    def __init__(self, config):
        self.handover_config = config.get('handover_rl', {})
        self.coverage_config = config.get('coverage_rl', {})

    def preprocess_for_handover(self, stage3_output):
        """換手決策RL預處理"""
        return {
            'states': self._extract_handover_states(stage3_output),
            'actions': self._define_handover_actions(),
            'rewards': self._calculate_handover_rewards(stage3_output),
            'sequences': self._build_temporal_sequences(stage3_output)
        }

    def preprocess_for_coverage(self, stage2_output):
        """覆蓋優化RL預處理"""
        return {
            'states': self._extract_coverage_states(stage2_output),
            'actions': self._define_coverage_actions(),
            'rewards': self._calculate_coverage_rewards(stage2_output),
            'spatial_features': self._extract_spatial_features(stage2_output)
        }
```

#### Step 2: 實現高效數據管道
```python
class RLDataPipeline:
    def __init__(self):
        self.feature_extractors = {
            'signal_quality': SignalQualityExtractor(),
            'spatial_geometry': SpatialGeometryExtractor(),
            'temporal_patterns': TemporalPatternExtractor(),
            'handover_history': HandoverHistoryExtractor()
        }

    def process_batch(self, input_data, target_scenario):
        """批量處理RL數據"""
        extracted_features = {}
        for feature_type, extractor in self.feature_extractors.items():
            extracted_features[feature_type] = extractor.extract(input_data)

        return self._format_for_rl_framework(extracted_features, target_scenario)
```

### Phase 3: Stage 6 RL重複清理 (1週)

#### Step 1: 移除重複的RL預處理
```python
# 🚫 移除重複實現
class Stage6Processor:
    # 刪除這些重複的RL預處理方法
    # def _preprocess_for_coverage_rl(self, pool_data):
    # def _extract_coverage_features(self, data):
    # def _normalize_coverage_data(self, features):
```

#### Step 2: 整合統一介面調用
```python
# ✅ 重構為統一介面調用
class Stage6Processor:
    def __init__(self, config):
        # 引入Stage 4的統一RL預處理器
        from stages.stage4.unified_rl_preprocessor import UnifiedRLPreprocessor
        self.rl_preprocessor = UnifiedRLPreprocessor(config)

    def process_dynamic_pool_planning(self, stage5_output):
        # 調用統一RL預處理
        rl_data = self.rl_preprocessor.preprocess_for_coverage(stage5_output)

        # Stage 6特有的動態規劃邏輯
        optimized_pools = self._optimize_satellite_pools(rl_data)
        return optimized_pools
```

---

## 📊 RL數據流重新設計

### 統一RL數據流架構
```
Stage 2 (可見性數據)
    ↓
Stage 3 (信號品質) → [無RL預處理]
    ↓
Stage 4 (統一RL預處理) → {
    ├── 換手決策RL預處理
    ├── 覆蓋優化RL預處理
    └── RL訓練數據匯出
}
    ↓
Stage 5 (數據整合)
    ↓
Stage 6 (動態規劃) → 調用Stage 4 RL介面
```

### RL預處理標準化輸出
```json
{
  "rl_preprocessing_results": {
    "handover_rl": {
      "states": [...],
      "actions": [...],
      "rewards": [...],
      "temporal_sequences": [...],
      "feature_dimensions": 256,
      "sequence_length": 20
    },
    "coverage_rl": {
      "states": [...],
      "actions": [...],
      "rewards": [...],
      "spatial_features": [...],
      "coverage_metrics": {...}
    },
    "metadata": {
      "preprocessing_timestamp": "2025-09-18T08:55:13Z",
      "data_source_stages": ["stage2", "stage3"],
      "rl_framework_ready": true,
      "export_formats": ["tensorflow", "pytorch", "numpy"]
    }
  }
}
```

---

## 🧪 RL整合驗證標準

### 功能完整性驗證
```python
# ✅ RL預處理驗證項目
- 換手決策RL數據完整性 ✓
- 覆蓋優化RL數據完整性 ✓
- 特徵向量維度一致性 ✓
- 時序數據連續性 ✓
- RL框架兼容性測試 ✓
```

### 性能基準測試
```bash
# 整合前基準 (分散實現)
RL預處理時間: 45秒 (Stage 3: 15s + Stage 4: 20s + Stage 6: 10s)
記憶體峰值: ~1.2GB
特徵維度一致性: 70% (不同階段維度不一致)

# 整合後目標 (統一實現)
RL預處理時間: <25秒 (統一Stage 4: 25s)
記憶體峰值: <800MB
特徵維度一致性: 100% (統一標準)
```

### RL訓練效果驗證
```python
# ✅ RL模型訓練驗證
- 換手決策準確率: 目標提升15%
- 覆蓋優化效率: 目標提升20%
- 訓練收斂速度: 目標提升30%
- 模型可重現性: 100%一致
```

---

## 🛡️ 風險控制措施

### RL整合風險評估
- **🔴 高風險**: 可能影響RL模型訓練效果
- **🟡 中風險**: 需要重新訓練現有RL模型
- **🟢 低風險**: 預處理介面統一，模型框架不變

### 風險緩解策略
1. **逐步遷移**: 先建立統一介面，再逐步移除重複
2. **模型備份**: 保留現有RL模型權重和訓練歷史
3. **A/B測試**: 新舊RL預處理並行驗證效果
4. **回退機制**: 保留快速回退到原實現的能力

### RL品質保證檢查點
- [ ] Phase 1完成: Stage 3 RL移除無錯誤
- [ ] Phase 2完成: Stage 4 RL引擎強化成功
- [ ] Phase 3完成: Stage 6 RL重複清理
- [ ] 訓練驗證: RL模型效果不回歸
- [ ] 性能達標: RL預處理時間<25秒

---

## 📈 整合後預期效果

### RL架構清晰度
- **統一入口**: 所有RL預處理統一到Stage 4
- **標準介面**: 一致的RL數據格式和API
- **功能專精**: 每個階段專注核心職責

### RL訓練效率提升
- **數據品質**: 統一預處理提升數據一致性
- **特徵工程**: 標準化特徵提取和正規化
- **批量處理**: 高效的批量RL數據處理管道

### 維護成本降低
- **單一維護**: 只需維護Stage 4的RL預處理邏輯
- **版本統一**: 避免多個階段RL版本不一致問題
- **測試簡化**: 集中的RL功能測試

---

## 🔄 RL演進策略

### 支持多種RL框架
```python
class RLFrameworkAdapter:
    """支持多種RL框架的適配器"""

    def export_tensorflow_format(self, rl_data):
        """TensorFlow格式匯出"""
        pass

    def export_pytorch_format(self, rl_data):
        """PyTorch格式匯出"""
        pass

    def export_stable_baselines_format(self, rl_data):
        """Stable Baselines格式匯出"""
        pass
```

### RL模型版本管理
```python
class RLModelVersionManager:
    """RL模型版本和實驗管理"""

    def track_preprocessing_version(self, version, config):
        """追蹤預處理版本"""
        pass

    def compare_model_performance(self, baseline, current):
        """比較模型性能"""
        pass
```

---

**下一步**: 開始Phase 1 Stage 3 RL功能移除
**相關文檔**: [跨階段功能清理](./cross_stage_function_cleanup.md)

---
**文檔版本**: v1.0
**最後更新**: 2025-09-18
**狀態**: 待執行