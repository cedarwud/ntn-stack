# UPF 擴展模組

這個模組為 Open5GS UPF (User Plane Function) 提供同步演算法整合功能，實現論文中的快速衛星切換機制。

## 📋 功能概述

- **同步演算法整合**: 將 Algorithm 1 和 Algorithm 2 整合到 UPF 中
- **GTP-U 標頭擴展**: 支援衛星識別資訊
- **路由表即時更新**: 基於演算法預測結果更新路由
- **Python-C 橋接**: 提供 Python API 與 UPF C 模組的通信介面

## 🏗️ 架構設計

```
UPF Extension Module
├── sync_algorithm_interface.h    # C 標頭文件
├── sync_algorithm_bridge.c       # C 實作
├── python_upf_bridge.py          # Python 橋接服務
├── gtp_extension.h               # GTP-U 擴展定義
├── routing_table_manager.c       # 路由表管理
└── Makefile                      # 編譯配置
```

## 🔧 編譯與安裝

```bash
# 在 UPF 容器內編譯
cd /home/sat/ntn-stack/netstack/docker/upf-extension
make clean && make install

# 重啟 UPF 服務
docker restart netstack-upf
```

## 🚀 使用方式

1. **啟動同步演算法橋接服務**:
   ```python
   from python_upf_bridge import UPFSyncBridge
   bridge = UPFSyncBridge()
   bridge.start()
   ```

2. **觸發衛星切換**:
   ```python
   bridge.trigger_handover(
       ue_id="12345",
       source_satellite="sat_1", 
       target_satellite="sat_2",
       predicted_time=1640995200.0
   )
   ```

## 📊 效能指標

- **切換延遲**: 目標 < 30ms
- **路由更新時間**: < 10ms
- **CPU 使用率**: < 5% 額外負載
- **記憶體使用**: < 50MB 額外開銷

## 🔗 相關文件

- [UPF 同步演算法設計文檔](./docs/sync_algorithm_design.md)
- [GTP-U 擴展規範](./docs/gtp_extension_spec.md)
- [Python-C 橋接 API](./docs/python_c_bridge_api.md)