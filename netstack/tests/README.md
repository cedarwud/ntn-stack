# NetStack 測試結構

## 測試分類

### 單元測試 (/tests/unit/)
- **ai_decision_integration/** - AI 決策整合組件測試
- **rl_training/** - 強化學習組件已移除
- **test_*.py** - 其他單元測試

### 整合測試 (/tests/integration/)  
- **phase_2_3_integration_test.py** - Phase 2.3 整合測試
- **phase_3_integration_test.py** - Phase 3 整合測試

### 端到端測試 (/tests/e2e/)
- **test_rl_integration_e2e.py** - 強化學習測試已移除

## 執行測試

```bash
# 執行所有測試
python -m pytest tests/

# 執行單元測試
python -m pytest tests/unit/

# 執行整合測試
python -m pytest tests/integration/

# 執行端到端測試
python -m pytest tests/e2e/
```

## 測試原則

1. **單元測試** - 測試單一函數或類的功能
2. **整合測試** - 測試多個組件協作
3. **端到端測試** - 測試完整用戶流程

按功能分組，避免重複，統一測試框架。

