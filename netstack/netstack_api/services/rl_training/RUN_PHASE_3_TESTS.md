# Phase 3 決策透明化功能運行指南

## 🚀 立即開始測試 Phase 3 功能

本指南將帶您快速驗證和測試所有 Phase 3 決策透明化與視覺化功能。

---

## 📋 前置要求檢查

### 1. 確認您在正確的目錄
```bash
cd netstack/netstack_api/services/rl_training
pwd  # 應該顯示包含 analytics/ 目錄的路徑
```

### 2. 檢查Python環境
```bash
python --version  # 建議 Python 3.8+
```

### 3. 安裝推薦依賴（可選但建議）
```bash
pip install scipy scikit-learn matplotlib plotly bokeh openpyxl jinja2
```

---

## ⚡ 快速功能驗證（2分鐘）

### 第一步：運行快速驗證腳本
```bash
cd integration
python phase_3_quick_verify.py
```

**預期輸出示例**：
```
🚀 Phase 3 決策透明化與視覺化功能快速驗證
============================================================
🔍 檢查 Phase 3 組件導入...
✅ AdvancedExplainabilityEngine 導入成功
✅ ConvergenceAnalyzer 導入成功
✅ StatisticalTestingEngine 導入成功
✅ AcademicDataExporter 導入成功
✅ VisualizationEngine 導入成功
✅ Phase 3 API 導入成功

🔍 檢查可選依賴項...
✅ SciPy 1.9.0 可用
✅ Scikit-learn 1.1.0 可用
✅ Matplotlib 3.5.0 可用
⚠️  Plotly 不可用 - 互動視覺化受限
...

📊 Phase 3 功能驗證報告
============================================================
⏱️  驗證時間: 1.23 秒
🎯 總體評分: 85.5/100
📊 狀態: GOOD

🎉 Phase 3 功能驗證通過！系統可以開始決策透明化與視覺化工作。
```

---

## 🧪 完整整合測試（5分鐘）

### 第二步：運行完整測試套件
```bash
python phase_3_integration_test.py
```

**測試包含**：
- ✅ 分析組件導入測試
- ✅ 解釋性引擎測試
- ✅ 收斂性分析器測試  
- ✅ 統計測試引擎測試
- ✅ 學術數據匯出器測試
- ✅ 視覺化引擎測試
- ✅ API 整合測試
- ✅ 完整透明化工作流測試

**預期輸出示例**：
```
📋 Phase 3 決策透明化與視覺化整合測試報告
================================================================================
總測試數: 8
通過測試: 7
失敗測試: 1
成功率: 87.5%
總耗時: 4.56 秒

📊 詳細測試結果:
  ✅ _test_analytics_imports (0.12s)
  ✅ _test_explainability_engine (0.45s)
  ✅ _test_convergence_analyzer (0.38s)
  ✅ _test_statistical_testing_engine (0.67s)
  ✅ _test_academic_data_exporter (0.89s)
  ❌ _test_visualization_engine (0.34s)
     錯誤: Matplotlib not available
  ✅ _test_phase3_api_integration (0.23s)
  ✅ _test_complete_transparency_workflow (1.48s)

🎉 Phase 3 基本功能驗證通過！
```

---

## 🌐 API 端點測試（需要啟動NetStack服務）

### 第三步：測試 API 端點

1. **啟動 NetStack API 服務**：
```bash
cd ../../../../  # 回到 netstack 根目錄
python -m netstack_api.main  # 或您的啟動命令
```

2. **測試健康檢查**：
```bash
curl http://localhost:8080/api/v1/rl/phase-3/health
```

3. **測試系統狀態**：
```bash
curl http://localhost:8080/api/v1/rl/phase-3/status
```

4. **測試決策解釋**：
```bash
curl -X POST http://localhost:8080/api/v1/rl/phase-3/explain/decision \
  -H "Content-Type: application/json" \
  -d '{
    "state": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
    "action": 2,
    "q_values": [0.1, 0.3, 0.8, 0.2, 0.4],
    "algorithm": "DQN",
    "episode": 100,
    "step": 50
  }'
```

---

## 💻 程式化使用示例

### 第四步：直接使用 Analytics 組件

創建測試腳本 `test_phase3_usage.py`：

```python
#!/usr/bin/env python3
"""
Phase 3 組件使用示例
"""
import sys
import numpy as np
from datetime import datetime

# 添加路徑
sys.path.append('../')

def test_explainability():
    """測試決策解釋功能"""
    print("🧠 測試決策解釋功能...")
    
    try:
        from analytics import AdvancedExplainabilityEngine
        
        engine = AdvancedExplainabilityEngine({
            "explainability_level": "detailed",
            "enable_feature_importance": True,
        })
        
        # 模擬決策數據
        decision_data = {
            "state": np.random.rand(10).tolist(),
            "action": 2,
            "q_values": np.random.rand(5).tolist(),
            "algorithm": "DQN",
            "episode": 100,
            "step": 50,
            "scenario_context": {
                "satellite_candidates": [
                    {"id": "sat_1", "signal_strength": 0.8},
                    {"id": "sat_2", "signal_strength": 0.6},
                    {"id": "sat_3", "signal_strength": 0.9},
                ]
            }
        }
        
        explanation = engine.explain_decision(decision_data)
        
        if explanation:
            print("✅ 決策解釋成功生成")
            print(f"   置信度: {explanation.get('confidence_score', 'N/A')}")
            print(f"   決策因子: {len(explanation.get('decision_factors', []))}")
            return True
        else:
            print("❌ 決策解釋生成失敗")
            return False
            
    except Exception as e:
        print(f"❌ 決策解釋測試失敗: {e}")
        return False

def test_convergence_analysis():
    """測試收斂性分析"""
    print("\n📈 測試收斂性分析...")
    
    try:
        from analytics import ConvergenceAnalyzer
        
        analyzer = ConvergenceAnalyzer({
            "smoothing_window": 10,
            "convergence_threshold": 0.01,
        })
        
        # 生成模擬學習曲線
        episodes = 200
        exploration = np.random.normal(-50, 20, 50)
        learning = np.linspace(-30, 40, 100) + np.random.normal(0, 10, 100)
        convergence = np.random.normal(45, 5, 50)
        rewards = np.concatenate([exploration, learning, convergence])
        
        analysis = analyzer.analyze_learning_curve(
            rewards.tolist(), 
            metric_name="total_reward"
        )
        
        if analysis:
            print("✅ 收斂性分析成功")
            print(f"   分析的episodes: {episodes}")
            print(f"   趨勢類型: {analysis.get('trend_type', 'N/A')}")
            return True
        else:
            print("❌ 收斂性分析失敗")
            return False
            
    except Exception as e:
        print(f"❌ 收斂性分析測試失敗: {e}")
        return False

def test_statistical_testing():
    """測試統計測試"""
    print("\n🔬 測試統計測試...")
    
    try:
        from analytics import StatisticalTestingEngine
        
        engine = StatisticalTestingEngine({
            "significance_level": 0.05,
            "enable_effect_size": True,
        })
        
        # 生成兩組算法性能數據
        dqn_rewards = np.random.normal(45, 10, 100)
        ppo_rewards = np.random.normal(50, 10, 100)
        
        result = engine.perform_t_test(
            dqn_rewards, 
            ppo_rewards,
            test_name="DQN_vs_PPO_comparison"
        )
        
        if result and "p_value" in result:
            print("✅ 統計測試成功")
            print(f"   p值: {result['p_value']:.4f}")
            print(f"   統計顯著: {result.get('significant', False)}")
            return True
        else:
            print("❌ 統計測試失敗")
            return False
            
    except Exception as e:
        print(f"❌ 統計測試失敗: {e}")
        return False

def test_visualization():
    """測試視覺化"""
    print("\n🎨 測試視覺化...")
    
    try:
        from analytics import VisualizationEngine
        import tempfile
        
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = VisualizationEngine({
                "output_directory": temp_dir,
                "default_theme": "academic",
            })
            
            # 生成測試數據
            episodes = list(range(100))
            dqn_rewards = np.linspace(-30, 45, 100) + np.random.normal(0, 5, 100)
            
            viz_data = {
                "episodes": episodes,
                "DQN": dqn_rewards.tolist(),
            }
            
            result = engine.create_learning_curve_plot(
                viz_data,
                title="DQN Learning Curve",
                filename="test_learning_curve"
            )
            
            if result and result.get("success", False):
                print("✅ 視覺化生成成功")
                print(f"   輸出文件: {result.get('output_path', 'N/A')}")
                return True
            else:
                print("❌ 視覺化生成失敗")
                return False
                
    except Exception as e:
        print(f"❌ 視覺化測試失敗: {e}")
        return False

def test_academic_export():
    """測試學術數據匯出"""
    print("\n📚 測試學術數據匯出...")
    
    try:
        from analytics import AcademicDataExporter
        import tempfile
        
        with tempfile.TemporaryDirectory() as temp_dir:
            exporter = AcademicDataExporter({
                "export_directory": temp_dir,
                "default_format": "json",
            })
            
            # 測試研究數據
            research_data = {
                "experiment_metadata": {
                    "title": "LEO Satellite Handover RL Algorithm Test",
                    "date": datetime.now().isoformat(),
                    "algorithms": ["DQN", "PPO", "SAC"],
                },
                "results": {
                    "DQN": {
                        "mean_reward": 45.2,
                        "std_reward": 10.1,
                        "episodes": 1000,
                    },
                    "PPO": {
                        "mean_reward": 50.8,
                        "std_reward": 8.7,
                        "episodes": 1000,
                    }
                }
            }
            
            result = exporter.export_to_json(
                research_data,
                filename="test_research_export.json"
            )
            
            if result and result.get("success", False):
                print("✅ 學術數據匯出成功")
                print(f"   匯出文件: {result.get('output_path', 'N/A')}")
                return True
            else:
                print("❌ 學術數據匯出失敗")
                return False
                
    except Exception as e:
        print(f"❌ 學術數據匯出測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 Phase 3 組件使用示例測試")
    print("=" * 50)
    
    tests = [
        test_explainability,
        test_convergence_analysis,
        test_statistical_testing,
        test_visualization,
        test_academic_export,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ 測試異常: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 測試結果: {passed}/{total} 通過")
    
    if passed >= total * 0.8:  # 80% 通過率
        print("🎉 Phase 3 組件基本功能正常！")
        return 0
    else:
        print("⚠️  部分 Phase 3 組件存在問題")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
```

然後運行：
```bash
cd integration
python test_phase3_usage.py
```

---

## 📊 預期結果判斷

### ✅ **成功指標**
- 快速驗證總體評分 > 70
- 整合測試成功率 > 80%
- API 健康檢查返回 "healthy"
- 所有核心組件可導入和初始化

### ⚠️ **常見問題**
- **依賴項缺失**: 安裝可選依賴項可提升功能完整性
- **API 無法訪問**: 確認 NetStack 服務已啟動
- **文件權限**: 確保有寫入 /tmp 目錄的權限

### 🔧 **故障排除**
1. **導入錯誤**: 檢查 Python 路徑和模組安裝
2. **依賴項問題**: 運行 `pip install scipy matplotlib plotly`
3. **權限問題**: 使用 `sudo` 或更改輸出目錄權限

---

## 🎯 下一步：Phase 4 整合

當 Phase 3 測試全部通過後，您就可以開始 Phase 4：

```bash
# 標記 Phase 3 完成
echo "Phase 3 測試通過，準備開始 Phase 4..." 

# Phase 4 將整合到前端系統
# 提供完整的決策透明化用戶介面
```

---

## 📞 需要幫助？

如果遇到任何問題：

1. **檢查日誌**: 查看詳細錯誤信息
2. **重新安裝依賴**: `pip install --upgrade scipy matplotlib plotly`
3. **檢查權限**: 確保可以寫入臨時目錄
4. **查看文檔**: 閱讀 `PHASE_3_COMPLETION_SUMMARY.md`

**現在就開始測試 Phase 3 功能吧！** 🚀