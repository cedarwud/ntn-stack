# 🏋️ Gymnasium 環境測試

本目錄包含 NTN Stack 專案中所有 Gymnasium 強化學習環境的測試腳本。

## 📁 檔案結構

```
tests/gymnasium/
├── README.md                        # 本文件
└── test_leo_handover_permanent.py   # LEO 衛星切換環境完整測試
```

## 🧪 測試說明

### LEO 衛星切換環境測試

**檔案**: `test_leo_handover_permanent.py`

**功能**: 對 LEO 衛星切換 Gymnasium 環境進行全面測試

**測試項目**:
- ✅ 基本功能測試 (環境創建、重置、步驟)
- ✅ 完整回合測試 (多步驟執行)
- ✅ 不同場景測試 (單UE vs 多UE)
- ✅ 獎勵函數測試 (不同動作的獎勵)
- ✅ 觀測空間測試 (維度、範圍、穩定性)
- ✅ 性能基準測試 (FPS、記憶體使用)

## 🚀 執行方式

### 在容器內執行

```bash
# 直接在 NetStack 容器內執行
docker exec netstack-api python /app/../tests/gymnasium/test_leo_handover_permanent.py
```

### 本地執行

```bash
# 在專案根目錄執行
cd /home/sat/ntn-stack
python tests/gymnasium/test_leo_handover_permanent.py
```

## 📊 測試結果解讀

### 成功標準

所有測試應該通過 (6/6)：
- 基本功能 ✅
- 完整回合 ✅  
- 不同場景 ✅
- 獎勵函數 ✅
- 觀測空間 ✅
- 性能基準 ✅

### 性能基準

**預期結果**:
- 重置時間: < 0.001s
- 步驟時間: < 0.0001s
- FPS: > 10,000
- 觀測維度: 正確 (依配置而定)

### 獎勵函數驗證

**預期行為**:
- 不切換: 獲得維持獎勵 (~1-3)
- 成功切換: 獲得延遲相關獎勵 (~3-10)
- 失敗切換: 獲得懲罰 (~-10)

## 🔧 故障排除

### 常見問題

1. **容器未啟動**
   ```bash
   make netstack-status  # 檢查容器狀態
   make netstack-start   # 啟動容器
   ```

2. **環境未註冊**
   ```bash
   docker exec netstack-api python -c "
   import netstack_api.envs
   import gymnasium as gym
   print('已註冊環境:', list(gym.envs.registry.env_specs.keys()))
   "
   ```

3. **權限問題**
   ```bash
   chmod +x tests/gymnasium/test_leo_handover_permanent.py
   ```

### 調試模式

啟用詳細日誌：

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 然後執行測試
```

## 📝 新增測試

### 創建新測試檔案

1. **命名規範**: `test_[environment_name].py`
2. **結構規範**: 參考現有測試檔案
3. **測試涵蓋**: 確保覆蓋所有核心功能

### 測試模板

```python
#!/usr/bin/env python3
"""
[環境名稱] Gymnasium 環境測試

測試 [環境描述] 的所有功能
"""

import sys
import gymnasium as gym
import numpy as np

def test_basic_functionality():
    """測試基本功能"""
    env = gym.make('[環境ID]')
    obs, info = env.reset()
    action = env.action_space.sample()
    obs, reward, term, trunc, info = env.step(action)
    env.close()
    return True

def main():
    """主測試函數"""
    tests = [
        ("基本功能", test_basic_functionality),
        # 添加更多測試...
    ]
    
    passed = 0
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
                print(f"✅ {test_name} 通過")
            else:
                print(f"❌ {test_name} 失敗")
        except Exception as e:
            print(f"❌ {test_name} 異常: {e}")
    
    return passed == len(tests)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
```

## 🔗 相關文檔

- **環境使用指南**: `/gymnasium.md`
- **NetStack API 文檔**: `/netstack/README.md`
- **專案整體測試**: `/tests/README.md`

## 📅 更新歷史

| 日期 | 版本 | 更新內容 |
|------|------|----------|
| 2025-06-23 | v1.0 | 初版：LEO 衛星切換環境測試 |

---

**最後更新**: 2025年6月23日