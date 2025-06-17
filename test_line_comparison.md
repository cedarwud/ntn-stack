# 線條抖動比較測試

## 測試目的
比較原始 Line 組件和改進的 TubeGeometry 實現的渲染效果差異

## 測試設置

### 1. 在 MainScene.tsx 中添加切換開關

```typescript
// 在 MainScene 的 props 中添加
lineRenderingMode?: 'line' | 'tube' | 'both'

// 在渲染部分
{lineRenderingMode === 'line' || lineRenderingMode === 'both' ? (
    <HandoverAnimation3D
        devices={devices}
        enabled={satelliteUavConnectionEnabled && handover3DAnimationEnabled}
        satellitePositions={satellitePositions}
    />
) : null}

{lineRenderingMode === 'tube' || lineRenderingMode === 'both' ? (
    <ImprovedHandoverAnimation3D
        devices={devices}
        enabled={satelliteUavConnectionEnabled && handover3DAnimationEnabled}
        satellitePositions={satellitePositions}
    />
) : null}
```

### 2. 在控制面板中添加切換選項

```typescript
<select onChange={(e) => setLineRenderingMode(e.target.value)}>
    <option value="line">原始 Line</option>
    <option value="tube">改進 Tube</option>
    <option value="both">並排比較</option>
</select>
```

## 測試指標

### 1. 視覺效果
- ✅ 線條平滑度
- ✅ 抖動程度
- ✅ 渲染穩定性
- ✅ 視覺吸引力

### 2. 性能指標
- ⚡ CPU 使用率
- ⚡ GPU 使用率
- ⚡ 幀率穩定性
- ⚡ 內存使用

### 3. 用戶體驗
- 👁️ 視覺舒適度
- 👁️ 連接關係清晰度
- 👁️ 換手動畫效果

## 預期結果

| 特性 | Line 組件 | TubeGeometry |
|------|-----------|--------------|
| 抖動程度 | 高 | 低 |
| 視覺效果 | 基本 | 優秀 |
| 性能開銷 | 低 | 中等 |
| 實現複雜度 | 簡單 | 中等 |

## 進一步優化建議

如果 TubeGeometry 效果良好，可以考慮：

1. **動態寬度**: 根據信號強度調整管道寬度
2. **顏色編碼**: 使用顏色表示連接質量
3. **動畫效果**: 添加流動動畫表示數據傳輸
4. **批量渲染**: 使用 InstancedMesh 優化多條連接的渲染

## 實施步驟

1. 將 ImprovedHandoverAnimation3D 集成到現有系統
2. 添加切換選項進行 A/B 測試
3. 收集性能數據和用戶反饋
4. 決定是否完全替換原實現