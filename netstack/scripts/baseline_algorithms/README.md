# LEO 衛星切換基準算法框架

## 概覽

這個目錄包含了用於 LEO 衛星切換優化的基準算法框架，提供標準化的算法接口和全面的性能對比工具。

## 架構組件

### 核心框架

1. **`base_algorithm.py`** - 基準算法抽象基類
   - 定義標準化的算法接口
   - 提供統一的性能統計
   - 包含 `AlgorithmEvaluator` 用於算法對比

2. **`__init__.py`** - 包初始化文件
   - 導出所有算法類別
   - 提供便捷的導入接口

### 基準算法實現

1. **`infocom2024_algorithm.py`** - IEEE INFOCOM 2024 算法適配器
   - 適配現有的論文同步算法
   - 支援增強版算法模式
   - 實現二分搜尋優化時機計算

2. **`simple_threshold_algorithm.py`** - 簡單閾值切換算法
   - 基於固定閾值的切換決策
   - 支援滯後控制防止乒乓效應
   - 可配置的閾值和權重參數

3. **`random_algorithm.py`** - 隨機基準算法
   - 完全隨機的切換決策
   - 提供性能基準的最低參考點
   - 支援確定性模式用於可重現實驗

### 評估工具

1. **`algorithm_comparison.py`** - 綜合算法對比評估系統
   - 支援基準算法與 RL 算法的全面對比
   - 生成詳細的 JSON 和 Markdown 報告
   - 可選的可視化圖表生成

2. **`test_comparison.py`** - 簡化測試腳本
   - 快速驗證所有算法的功能
   - 生成基本的性能對比結果

## 使用方法

### 基本使用

```python
from baseline_algorithms import (
    InfocomAlgorithm, 
    SimpleThresholdAlgorithm, 
    RandomAlgorithm,
    AlgorithmEvaluator
)
import numpy as np

# 創建算法實例
infocom_algo = InfocomAlgorithm({
    'delta_t': 5.0,
    'binary_search_precision': 0.01
})

threshold_algo = SimpleThresholdAlgorithm({
    'handover_threshold': 0.4,
    'emergency_threshold': 0.2
})

random_algo = RandomAlgorithm({
    'handover_probability': 0.2,
    'random_seed': 42
})

# 進行決策
observation = np.random.random(72)  # 環境觀測向量
info = {'active_ue_count': 2, 'active_satellite_count': 5}

result = infocom_algo.make_decision(observation, info)
print(f"決策: {result.handover_decision}, 置信度: {result.confidence}")
```

### 算法對比評估

```python
from baseline_algorithms import AlgorithmEvaluator

# 創建評估器
evaluator = AlgorithmEvaluator()

# 註冊算法
evaluator.register_algorithm(infocom_algo)
evaluator.register_algorithm(threshold_algo)
evaluator.register_algorithm(random_algo)

# 準備測試數據
observations = [np.random.random(72) for _ in range(100)]
infos = [{'active_ue_count': 2, 'active_satellite_count': 5} for _ in range(100)]

# 運行對比
results = evaluator.compare_algorithms(observations, infos)
```

### 完整對比評估

```python
from algorithm_comparison import ComprehensiveAlgorithmComparison

# 創建對比系統
comparison = ComprehensiveAlgorithmComparison()

# 運行完整評估
results = comparison.run_full_comparison()
```

## 算法性能特徵

### IEEE INFOCOM 2024 算法
- **優勢**: 論文驗證的優化性能，智能二分搜尋
- **特點**: 20-40% 延遲減少，2-5% 成功率提升
- **複雜度**: O(log n)

### 簡單閾值算法
- **優勢**: 實現簡單，可預測行為，低計算開銷
- **特點**: 固定閾值決策，滯後控制
- **複雜度**: O(1)

### 隨機基準算法
- **優勢**: 完全無偏見，提供性能底線
- **特點**: 可配置決策機率，支援確定性模式
- **複雜度**: O(1)

## 配置選項

### InfocomAlgorithm 配置
```python
config = {
    'delta_t': 5.0,                    # 週期更新間隔
    'binary_search_precision': 0.01,   # 二分搜尋精度
    'use_enhanced': True               # 是否使用增強版
}
```

### SimpleThresholdAlgorithm 配置
```python
config = {
    'handover_threshold': 0.4,         # 切換閾值
    'emergency_threshold': 0.2,        # 緊急切換閾值
    'hysteresis_margin': 0.1,          # 滯後邊際
    'signal_weight': 0.6,              # 信號強度權重
    'sinr_weight': 0.4                 # SINR 權重
}
```

### RandomAlgorithm 配置
```python
config = {
    'handover_probability': 0.2,       # 觸發切換機率
    'prepare_probability': 0.3,        # 準備切換機率
    'random_seed': 42,                 # 隨機種子
    'satellite_count': 10              # 衛星數量
}
```

## 輸出格式

所有算法返回標準化的 `AlgorithmResult` 對象：

```python
@dataclass
class AlgorithmResult:
    handover_decision: int           # 0: 維持, 1: 切換, 2: 準備
    target_satellite: Optional[int] # 目標衛星 ID
    timing: float                    # 切換時機 (秒)
    confidence: float                # 決策置信度 (0-1)
    decision_time: float             # 決策耗時 (ms)
    expected_latency: float          # 預期延遲 (ms)
    expected_success_rate: float     # 預期成功率 (0-1)
    algorithm_name: str              # 算法名稱
    decision_reason: str             # 決策原因
```

## 測試和驗證

### 運行基本測試
```bash
cd /home/sat/ntn-stack/netstack/scripts/baseline_algorithms
python test_comparison.py
```

### 運行完整對比
```bash
python algorithm_comparison.py
```

## 擴展指南

### 添加新的基準算法

1. 繼承 `BaseAlgorithm` 基類
2. 實現 `_initialize_algorithm()` 方法
3. 實現 `make_decision()` 方法
4. 在 `__init__.py` 中添加導出

示例：
```python
from .base_algorithm import BaseAlgorithm, AlgorithmResult

class CustomAlgorithm(BaseAlgorithm):
    def _initialize_algorithm(self):
        # 初始化算法參數
        pass
    
    def make_decision(self, observation, info):
        # 實現決策邏輯
        return AlgorithmResult(
            handover_decision=0,
            decision_reason="Custom logic"
        )
```

## 性能基準

基於測試結果的典型性能範圍：

| 算法 | 平均決策時間 | 平均延遲 | 成功率 | 切換率 |
|------|-------------|----------|--------|---------|
| INFOCOM 2024 | 1-3 ms | 20-25 ms | 92-95% | 15-25% |
| 簡單閾值 | 0.5-1 ms | 25-35 ms | 85-90% | 20-30% |
| 隨機基準 | 0.1-0.5 ms | 30-50 ms | 70-80% | 20% (可配置) |

## 故障排除

### 常見問題

1. **模組導入錯誤**
   - 確保正確設置 Python 路徑
   - 檢查 `__init__.py` 文件

2. **環境相容性**
   - 在 Docker 容器內運行測試
   - 確保所需依賴已安裝

3. **性能問題**
   - 使用優化版環境
   - 減少測試場景數量

### 日誌配置

```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

## 未來擴展

1. **更多基準算法**：機器學習基準、啟發式算法
2. **高級評估指標**：能耗分析、網路負載影響
3. **即時性能監控**：線上性能追蹤
4. **自動調參**：基於遺傳算法的參數優化

---

*最後更新：2024年12月*