# 🛰️ 3D衛星軌跡動畫優化方案

## 🔍 現狀分析

### 當前實現問題
- **移動速度**: 硬編碼，未使用 `velocity_km_s` 真實數據
- **軌跡路徑**: 簡化半圓弧，與真實橢圓軌道差異巨大  
- **仰角變化**: 固定三角函數，無法反映真實仰角變化
- **過境時間**: 隨機化，不符合軌道力學

### 對換手模擬的影響
- ❌ 換手時機不準確
- ❌ 信號強度變化失真
- ❌ 多衛星相對位置錯誤
- ❌ 速度不一致性

## 🚀 Phase 1 優化方案 (建議採用)

### 核心改進策略
基於現有NetStack API數據，最小化修改3D渲染器，直接使用真實軌道參數。

### 具體實施步驟

#### 1️⃣ 修改 calculateOrbitPosition 函數
```typescript
const calculateOrbitPosition = (
    currentTime: number,
    orbit: SatelliteOrbit,
    speedMultiplier: number
): { position: [number, number, number]; isVisible: boolean } => {
    // ✅ 使用真實數據優先
    if (orbit.realData) {
        const realPos = orbit.realData.position;
        
        // 基於真實仰角計算3D位置
        const elevation = realPos.elevation * Math.PI / 180;
        const azimuth = realPos.azimuth * Math.PI / 180;
        const range = realPos.range || 1000; // km
        
        // 3D球面座標轉換
        const x = range * Math.cos(elevation) * Math.sin(azimuth);
        const z = range * Math.cos(elevation) * Math.cos(azimuth);  
        const y = Math.max(15, range * Math.sin(elevation) / 10); // 縮放到合適高度
        
        return {
            position: [x, y, z],
            isVisible: realPos.elevation > 0 // 基於真實仰角判定可見性
        };
    }
    
    // Fallback 到原本邏輯
    // ... 現有代碼
};
```

#### 2️⃣ 整合真實速度控制
```typescript
// 在 useFrame 中使用真實速度
useFrame(() => {
    if (!enabled) return

    setOrbits((prevOrbits) => {
        return prevOrbits.map((orbit) => {
            // ✅ 基於真實速度調整時間步長
            const realVelocity = orbit.realData?.position.velocity || 7.5; // km/s
            const timeStep = speedMultiplier * realVelocity / 7500; // 標準化速度
            
            const state = calculateOrbitPosition(
                timeRef.current + timeStep,
                orbit,
                speedMultiplier
            );
            
            return {
                ...orbit,
                currentPosition: state.position,
                isVisible: state.isVisible,
            };
        });
    });
});
```

#### 3️⃣ 動態數據更新機制
```typescript
// 增強 RealSatelliteDataManager 更新頻率
const updateInterval: number = 5000 // 5秒更新，提高軌跡精確度

// 在數據更新時觸發軌跡重算
useEffect(() => {
    if (realSatelliteMapping.size > 0) {
        // 立即更新所有軌道的真實數據
        setOrbits(prevOrbits => 
            prevOrbits.map(orbit => ({
                ...orbit,
                realData: realSatelliteMapping.get(orbit.id) || orbit.realData
            }))
        );
    }
}, [realSatelliteMapping]);
```

### 💡 Phase 1 預期效果

#### 立即改善
- ✅ **真實仰角**: 衛星高度變化符合真實軌道
- ✅ **正確方位**: 衛星出現/消失方向準確
- ✅ **實際速度**: 不同衛星有不同移動速度
- ✅ **精確可見性**: 基於真實仰角判定

#### 換手模擬改善  
- ✅ **準確時機**: 換手觸發時間與實際軌道一致
- ✅ **真實信號**: 信號強度變化符合物理規律
- ✅ **正確候選**: 多衛星相對位置準確

## 📊 實施優先級

### 🔥 高優先級 (立即實施)
- [x] 真實仰角/方位角整合
- [x] 基於真實數據的可見性判定
- [x] 動態數據更新機制

### 🚀 中優先級 (後續優化)
- [ ] 真實速度差異化
- [ ] 軌跡插值平滑化
- [ ] 換手事件視覺化同步

### 💎 低優先級 (研究完成後)
- [ ] 完整SGP4前端整合
- [ ] 軌跡預測功能
- [ ] 高精度動畫系統

## 🎯 成功指標

### 量化目標
- **位置誤差**: < 5% (相對於真實軌道位置)
- **速度一致性**: ±10% (與真實衛星速度)
- **可見性準確率**: > 95% (與NetStack計算結果)

### 質化目標
- 換手動畫時機與算法決策完全同步
- 衛星移動軌跡符合軌道力學原理
- 論文演示時具備完整的技術可信度

---

**結論**: Phase 1方案能以最小成本達成最大效益，完美平衡學術要求與開發效率。