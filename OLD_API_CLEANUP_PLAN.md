# 🧹 舊API邏輯清理計畫

## 📋 需要移除的舊邏輯：

### 1. 過時的外部API調用
- **檔案**: `satellite_ops_router.py`
- **功能**: `_call_simworld_satellites_api()` (141行)
- **問題**: 調用外部SimWorld API而非內建預處理系統
- **移除**: 整個函數 (lines 1032-1173)

### 2. 過時的服務依賴
- **檔案**: `satellite_ops_router.py`  
- **功能**: `SimWorldTLEBridgeService` 依賴注入
- **問題**: 不需要外部bridge，應使用內建預處理服務
- **移除**: 所有 `SimWorldTLEBridgeService` 相關導入和依賴

### 3. 過時的API端點邏輯
- **檔案**: `satellite_ops_router.py`
- **功能**: `get_visible_satellites` 主邏輯 (lines 252-396)  
- **問題**: 整個邏輯基於外部API，需要重寫為使用預處理系統
- **動作**: 完全重寫端點實現

## 🎯 替換目標：

### 新的API端點邏輯：
```python
@router.get("/visible_satellites")
async def get_visible_satellites(
    count: int = Query(10, ge=1, le=200),
    constellation: str = Query("starlink"),
    preprocessing_service = Depends(get_preprocessing_service)
):
    # 調用智能預處理系統
    request = PreprocessingRequest(
        constellation=constellation,
        target_count=120 if constellation=='starlink' else 80
    )
    
    result = await preprocessing_service.preprocess_satellite_pool(request, all_satellites)
    return VisibleSatellitesResponse(
        satellites=result.selected_satellites[:count],
        total_count=len(result.selected_satellites)
    )
```

## ⚠️ 風險評估：
- **高風險**: 完全重寫API端點邏輯
- **中風險**: 移除外部API依賴
- **低風險**: 更新文檔和測試

## 🔧 執行順序：
1. 備份現有API邏輯
2. 移除過時的外部API調用
3. 重寫API端點使用預處理系統  
4. 測試新API功能
5. 更新前端調用（如有必要）

**預估時間**: 2-3小時完整重構

