# Sionna Service 重構計劃

## 🎯 現況分析

### 當前狀態
- **`sionna_service.py` (1726行)**: 完整功能的巨型服務，包含所有 Sionna 模擬功能
- **`sionna_service_refactored.py` (281行)**: 未完成的重構版本，依賴不存在的子服務模組

### 核心問題
1. **重構未完成**: `sionna_service_refactored.py` 導入不存在的模組
2. **功能重複**: 兩個版本共存造成維護困惑
3. **代碼巨大**: 1726行的單一服務違反單一職責原則
4. **難以測試**: 功能耦合過於緊密

## 🏗️ 重構策略

### Phase 1: 分析與規劃 (優先級: 🔥 High)

#### 目標: 分析現有功能並設計模組化架構

**步驟 1: 功能模組分析**
```python
# 功能分組分析
CORE_FUNCTIONS = {
    "場景管理": [
        "get_scene_xml_file_path",
        "check_scene_health", 
        "prepare_output_file",
        "verify_output_file"
    ],
    "GPU和環境設置": [
        "_setup_gpu",
        "_clean_output_file",
        "_ensure_output_dir"
    ],
    "3D渲染": [
        "_setup_pyrender_scene_from_glb",
        "_render_crop_and_save",
        "generate_empty_scene_image"
    ],
    "通信模擬": [
        "generate_cfr_plot",
        "generate_sinr_map", 
        "generate_doppler_plots",
        "generate_channel_response_plots"
    ]
}
```

**步驟 2: 依賴關係映射**
```python
# 服務依賴關係
DEPENDENCIES = {
    "SceneManagementService": ["無依賴"],
    "RenderingService": ["SceneManagementService"],
    "CommunicationSimulationService": ["SceneManagementService", "DeviceService"],
    "SionnaSimulationService": ["所有子服務"]
}
```

### Phase 2: 建立基礎服務 (優先級: 🔥 High)

#### 目標: 創建核心的場景管理服務

**步驟 1: SceneManagementService**
```python
# 創建 app/domains/simulation/services/scene/scene_management_service.py
class SceneManagementService:
    """場景管理和檔案處理服務"""
    
    def __init__(self):
        pass
        
    def get_scene_xml_path(self, scene_name: str) -> str:
        """獲取場景XML路徑"""
        
    def check_scene_health(self, scene_name: str, xml_path: str) -> bool:
        """檢查場景健康度"""
        
    def prepare_output_file(self, output_path: str, file_desc: str = "圖檔"):
        """準備輸出檔案"""
        
    def verify_output_file(self, output_path: str) -> bool:
        """驗證輸出檔案"""
        
    def setup_gpu(self) -> bool:
        """設置GPU環境"""
```

**步驟 2: 建立目錄結構**
```bash
# 創建模組化目錄結構
simworld/backend/app/domains/simulation/services/
├── sionna_service.py                    # 原始服務 (保留)
├── sionna_service_refactored.py         # 刪除此檔案
├── scene/
│   ├── __init__.py
│   └── scene_management_service.py      # 場景管理
├── rendering/
│   ├── __init__.py
│   └── rendering_service.py             # 3D渲染
├── communication/
│   ├── __init__.py
│   └── communication_simulation_service.py  # 通信模擬
└── sionna_service_v2.py                 # 新的重構版本
```

### Phase 3: 渲染服務重構 (優先級: 🟡 Medium)

#### 目標: 分離3D渲染功能

**步驟 1: RenderingService**
```python
# 創建 rendering/rendering_service.py
class RenderingService:
    """3D渲染和圖像處理服務"""
    
    def __init__(self, scene_service: SceneManagementService):
        self.scene_service = scene_service
        
    def setup_pyrender_scene_from_glb(self) -> Optional[pyrender.Scene]:
        """設置pyrender場景"""
        
    def render_crop_and_save(
        self, 
        pr_scene: pyrender.Scene,
        output_path: str,
        **kwargs
    ) -> bool:
        """渲染、裁剪並保存圖像"""
        
    def generate_empty_scene_image(self, output_path: str) -> bool:
        """生成空場景圖像"""
```

## 📋 實施時間線

### Week 1: Phase 2 - 場景管理服務
- **Day 1-2**: 分析和提取場景管理功能
- **Day 3-4**: 實現 SceneManagementService
- **Day 5**: 單元測試和驗證

### Week 2: Phase 3 - 渲染服務
- **Day 1-2**: 提取3D渲染功能
- **Day 3-4**: 實現 RenderingService
- **Day 5**: 整合測試

### Week 3: Phase 4 - 通信模擬服務  
- **Day 1-3**: 提取通信模擬功能 (最複雜)
- **Day 4**: 實現 CommunicationSimulationService
- **Day 5**: 功能測試

### Week 4: Phase 5 - 統一接口
- **Day 1-2**: 實現 SionnaSimulationServiceV2
- **Day 3-4**: 功能對等性測試
- **Day 5**: 文檔更新和部署準備

## 🎯 成功指標

### 定量指標
- **代碼行數**: 主服務從1726行減少到~200行 (88%減少)
- **模組數量**: 從1個巨型檔案分解為4個專門服務
- **測試覆蓋率**: >95%
- **功能對等**: 100%功能保持不變

### 定性指標
- **可維護性**: 每個服務單一職責
- **可測試性**: 獨立單元測試
- **可擴展性**: 新增模擬類型無需修改主服務
- **可讀性**: 新人能在15分鐘內理解架構

## 🚨 風險管控

### 高風險項目
1. **GPU設置依賴**: 確保GPU設置在所有服務中正確共享
2. **檔案路徑處理**: 確保相對/絕對路徑在不同服務間一致
3. **記憶體管理**: pyrender和matplotlib的資源釋放

### 緩解策略
1. **漸進式重構**: 保持原始服務可用，新服務並行開發
2. **對比測試**: 每個階段都與原始版本比較輸出
3. **回滾計劃**: 如有問題可快速回退到原始版本

## 📚 清理計劃

### 重構完成後清理
```bash
# 刪除未完成的重構檔案
rm simworld/backend/app/domains/simulation/services/sionna_service_refactored.py

# 保留原始檔案作為參考 (可選)
mv sionna_service.py sionna_service_legacy.py

# 將新版本設為主要版本
mv sionna_service_v2.py sionna_service.py
```

---

**目標**: 將1726行的巨型服務重構為高度模組化、可維護、可測試的架構  
**原則**: 功能完全對等，性能不降低，可維護性大幅提升  
**時程**: 4週完成，每週一個重要里程碑
