# 衛星模型與線條抖動差異分析報告

## 問題概述

在 NTN Stack 3D 仿真系統中，衛星模型渲染平滑穩定，但連接線條存在抖動問題。本報告深入分析兩者的渲染機制差異，並提出解決方案。

## 技術架構分析

### 1. 衛星模型渲染機制 (DynamicSatelliteRenderer)

#### 1.1 渲染方式
- **GLB 3D 模型**: 使用 `StaticModel` 組件渲染 GLB 格式的 3D 衛星模型
- **GPU 優化**: GLB 模型由 GPU 直接處理，具有內建的插值和渲染優化
- **材質系統**: 使用 Three.js 的 MeshStandardMaterial，支持光照和陰影

#### 1.2 位置更新機制
```typescript
useFrame(() => {
    if (!enabled) return
    timeRef.current += speedMultiplier / 60
    
    setOrbits((prevOrbits) => {
        const updatedOrbits = prevOrbits.map((orbit) => {
            const state = calculateOrbitPosition(
                timeRef.current,
                orbit,
                speedMultiplier
            )
            return {
                ...orbit,
                currentPosition: state.position,
                isVisible: state.isVisible,
            }
        })
        return updatedOrbits
    })
})
```

**關鍵特點:**
- **60 FPS 更新**: 使用 `useFrame` 每幀更新位置
- **平滑插值**: `calculateOrbitPosition` 使用數學函數計算連續位置
- **GPU 渲染**: 3D 模型由 Three.js 在 GPU 上進行插值渲染

### 2. 線條渲染機制 (HandoverAnimation3D)

#### 2.1 渲染方式
- **Line 幾何體**: 使用 `@react-three/drei` 的 `Line` 組件
- **基於頂點**: 線條是通過兩個 3D 點定義的幾何體
- **即時重繪**: 每次位置變化都需要重新生成幾何體

#### 2.2 位置更新機制
```typescript
useFrame((state, delta) => {
    if (!enabled) return
    
    // 位置平滑處理
    if (satellitePositions) {
        const smoothingFactor = Math.min(delta * 8.0, 1.0)
        
        for (const [satId, targetPos] of satellitePositions.entries()) {
            const currentSmoothed = smoothedPositionsRef.current.get(satId)
            
            if (!currentSmoothed) {
                smoothedPositionsRef.current.set(satId, targetPos)
            } else {
                const smoothedPos = lerpPosition(currentSmoothed, targetPos, smoothingFactor)
                smoothedPositionsRef.current.set(satId, smoothedPos)
            }
        }
    }
})
```

## 根本原因分析

### 1. 渲染管線差異

| 特性 | 衛星模型 (GLB) | 線條 (Line) |
|------|----------------|-------------|
| **渲染類型** | 3D Mesh | 2D/3D Line |
| **GPU 處理** | 完全由 GPU 處理 | CPU 計算 + GPU 渲染 |
| **插值** | 內建硬體插值 | 需要手動插值 |
| **幾何體** | 複雜網格，不易變形 | 簡單線段，易受影響 |
| **更新成本** | 僅更新變換矩陣 | 重新生成幾何體 |

### 2. 位置更新頻率差異

#### 衛星位置更新
```typescript
// 定時器更新（100ms 間隔）
const updatePositions = () => {
    // 只在位置有顯著變化時才調用回調
    if (hasChanges) {
        onSatellitePositions(positionMap)
    }
}
const interval = setInterval(updatePositions, 100)
```

#### 線條渲染頻率
```typescript
// 每幀更新（60 FPS）
useFrame((state, delta) => {
    // 每幀都可能重新計算線條位置
    const smoothedPos = lerpPosition(currentSmoothed, targetPos, smoothingFactor)
})
```

### 3. 座標系和精度問題

- **浮點精度**: 線條端點計算涉及更多浮點運算
- **座標轉換**: 衛星到 UAV 的座標轉換可能引入誤差
- **更新同步**: 衛星位置和線條位置更新不完全同步

## 技術限制分析

### 1. Three.js Line 組件限制

- **WebGL 限制**: WebGL 1.0 對線條寬度支持有限
- **重繪開銷**: 每次位置更新都需要重建幾何體
- **抗鋸齒**: 線條抗鋸齒效果不如 3D 模型

### 2. React Three Fiber 更新機制

- **狀態更新**: React 狀態更新可能不夠平滑
- **重渲染**: 組件重渲染會導致線條閃爍
- **內存分配**: 頻繁創建/銷毀幾何體對象

## 解決方案建議

### 1. 立即可行方案

#### 1.1 優化平滑插值
```typescript
// 增加平滑因子，減少抖動
const smoothingFactor = Math.min(delta * 4.0, 1.0) // 降低到 4.0

// 添加位置變化閾值
const positionChangeThreshold = 0.5 // 只有變化超過 0.5 單位才更新
```

#### 1.2 使用 TubeGeometry 替代 Line
```typescript
// 使用管道幾何體替代線條
<mesh>
    <tubeGeometry args={[curve, 64, 0.5, 8, false]} />
    <meshBasicMaterial color="#00ff00" transparent opacity={0.8} />
</mesh>
```

### 2. 中期改進方案

#### 2.1 軌跡系統 (Trail System)
```typescript
// 創建軌跡效果，減少線條重繪
const TrailEffect = ({ points, maxLength = 50 }) => {
    const [trailPoints, setTrailPoints] = useState([])
    
    useFrame(() => {
        setTrailPoints(prev => {
            const newPoints = [...prev, currentPosition].slice(-maxLength)
            return newPoints
        })
    })
    
    return <TrailGeometry points={trailPoints} />
}
```

#### 2.2 批量更新機制
```typescript
// 批量更新多條線條
const BatchedLineRenderer = ({ connections }) => {
    const geometryRef = useRef()
    
    useFrame(() => {
        if (geometryRef.current) {
            // 批量更新所有線條的頂點
            updateBatchedGeometry(geometryRef.current, connections)
        }
    })
}
```

### 3. 長期優化方案

#### 3.1 自定義 Shader 材質
```glsl
// 自定義頂點著色器實現平滑插值
vertex shader:
attribute vec3 targetPosition;
uniform float interpolationFactor;

void main() {
    vec3 interpolatedPosition = mix(position, targetPosition, interpolationFactor);
    gl_Position = projectionMatrix * modelViewMatrix * vec4(interpolatedPosition, 1.0);
}
```

#### 3.2 WebGL Instance 渲染
```typescript
// 使用實例化渲染減少 draw call
const InstancedLineRenderer = ({ lines }) => {
    return (
        <instancedMesh ref={meshRef} args={[null, null, lines.length]}>
            <cylinderGeometry args={[0.1, 0.1, 1, 8]} />
            <meshBasicMaterial color="#00ff00" />
        </instancedMesh>
    )
}
```

## 效能比較

| 方案 | CPU 使用 | GPU 使用 | 平滑度 | 實現複雜度 |
|------|----------|----------|--------|------------|
| 當前 Line | 高 | 中 | 低 | 低 |
| TubeGeometry | 中 | 高 | 高 | 中 |
| Trail System | 中 | 中 | 高 | 中 |
| Custom Shader | 低 | 高 | 很高 | 高 |
| Instanced Rendering | 低 | 高 | 很高 | 高 |

## 建議實施順序

1. **第一階段**: 優化現有平滑插值參數，降低更新頻率
2. **第二階段**: 實現 TubeGeometry 替代方案
3. **第三階段**: 開發軌跡系統增強視覺效果
4. **第四階段**: 考慮自定義 Shader 或實例化渲染

## 結論

衛星模型沒有抖動而線條抖動的根本原因是：

1. **渲染機制差異**: GLB 模型由 GPU 硬體插值，線條需要 CPU 計算
2. **更新頻率不匹配**: 衛星位置更新較慢，線條渲染較快
3. **幾何體類型**: 3D 模型穩定性高，線條幾何體易變形
4. **WebGL 限制**: 線條渲染在 WebGL 中本身就有限制

建議優先實施 TubeGeometry 替代方案，可以在保持現有架構的同時顯著改善視覺效果。