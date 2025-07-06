# Sionna Service 重構計劃

## 🎯 現況分析

### 當前狀態
- **`sionna_service.py` (1726行)**: 完整功能的巨型服務，包含所有 Sionna 模擬功能
- **`sionna_service_refactored.py` (281行)**: 未完成的重構版本，依賴不存在的子服務模組

### ✅ **實際使用中的功能 (不能刪除)**
1. **前端 Navbar 信號分析**: 四個圖表組件被實際使用
   - `SINRViewer.tsx` → SINR MAP 彈窗
   - `CFRViewer.tsx` → Constellation & CFR 彈窗
   - `DelayDopplerViewer.tsx` → Delay–Doppler 彈窗
   - `TimeFrequencyViewer.tsx` → Time-Frequency 彈窗

2. **完整的前後端串接鏈路**:
   ```
   Navbar 按鈕 → Viewer 組件 → simulationApi.ts → API 端點 → sionna_service.py
   ```

3. **跨領域服務依賴**:
   - `SionnaChannelSimulationService` (wireless 領域)
   - `interference_simulation_service.py` (interference 領域)

### ❌ **可以安全刪除的部分**
- `sionna_service_refactored.py` - 未完成的重構文件
- 空的 sionna 相關目錄

### 核心問題
1. **代碼巨大**: 1726行的單一服務違反單一職責原則
2. **難以測試**: 功能耦合過於緊密
3. **維護困難**: 所有功能混在一個文件中
4. **擴展性差**: 新增功能需要修改巨型文件

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

### 🔴 **高風險項目 (會影響用戶功能)**
1. **Navbar 信號分析功能**: 四個圖表彈窗的正常顯示
   - SINR MAP, CFR, Delay-Doppler, Time-Frequency
   - 必須確保 API 接口完全兼容
   
2. **跨領域服務依賴**: 
   - wireless 領域的 `SionnaChannelSimulationService`
   - interference 領域的干擾檢測功能
   
3. **API 回應格式**: 確保重構後圖片生成和回傳格式一致

### 🟡 **中風險項目**
1. **GPU設置依賴**: 確保GPU設置在所有服務中正確共享
2. **檔案路徑處理**: 確保相對/絕對路徑在不同服務間一致
3. **記憶體管理**: pyrender和matplotlib的資源釋放

### 緩解策略
1. **保持 API 接口不變**: 所有公開方法簽名必須完全一致
2. **功能對等測試**: 每個功能都要與原版本對比測試
3. **用戶功能驗證**: 重點測試 navbar 四個圖表的完整流程
4. **版本切換機制**: 提供快速回滾到原始服務的能力
5. **漸進式重構**: 保持原始服務可用，新服務並行開發

## 🧪 **重構驗證計劃**

### 🎯 **必須通過的功能測試**
```bash
# 1. Navbar 功能完整性測試
- 點擊「信號分析」→ SINR MAP 彈窗正常顯示
- 點擊「信號分析」→ Constellation & CFR 彈窗正常顯示  
- 點擊「信號分析」→ Delay–Doppler 彈窗正常顯示
- 點擊「信號分析」→ Time-Frequency 彈窗正常顯示

# 2. API 接口測試
curl http://localhost:8888/api/v1/simulations/cfr-plot
curl http://localhost:8888/api/v1/simulations/sinr-map
curl http://localhost:8888/api/v1/simulations/doppler-plots
curl http://localhost:8888/api/v1/simulations/channel-response

# 3. 跨領域服務測試
- wireless 領域功能正常
- interference 領域功能正常
```

### 📊 **對比測試要求**
- 生成的圖片與原版本像素級一致（允許5%誤差）
- API 回應時間差異 < 10%
- 記憶體使用量差異 < 15%

## 📚 清理計劃

### 立即可清理（低風險）
```bash
# 刪除未完成的重構檔案
rm simworld/backend/app/domains/simulation/services/sionna_service_refactored.py
```

### 重構完成後清理
```bash
# 保留原始檔案作為參考 (建議保留一段時間)
mv sionna_service.py sionna_service_legacy.py

# 將新版本設為主要版本
mv sionna_service_v2.py sionna_service.py
```

---

**目標**: 將1726行的巨型服務重構為高度模組化、可維護、可測試的架構  
**原則**: 功能完全對等，用戶體驗無影響，性能不降低，可維護性大幅提升  
**重點**: 確保 Navbar 信號分析四個圖表功能完全正常  
**時程**: 4週完成，每週一個重要里程碑

## ⚠️ **重要提醒**

**這不是簡單的代碼清理，而是有實際用戶功能依賴的重構！**
- Navbar 的信號分析功能被實際使用
- 任何破壞性改動都會直接影響用戶體驗
- 必須保持 100% 功能對等性
