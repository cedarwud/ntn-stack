# 統一單UE重構方針

## 🎯 核心原則
**主要使用單UE場景，保留多UE建立和控制能力，但移除編隊群集協調功能**

## ✅ 保留功能
- **單UE核心功能** - 主要使用模式
- **多UE建立能力** - 可以建立多個UE
- **多UE選擇控制** - 可以選擇和控制多個UE
- **基礎UAV渲染** - UAVFlight.tsx 保留

## ❌ 移除功能  
- **編隊協調邏輯** - V字形、圓形、網格編隊
- **群集協調任務** - 協調任務管理
- **群集指標計算** - 群集統計功能

## 📋 具體執行清單
1. **保留**: `components/domains/device/visualization/UAVFlight.tsx`
2. **保留但簡化**: `components/layout/sidebar/UAVSelectionPanel.tsx` (移除編隊功能)
3. **修改**: `components/domains/simulation/coordination/UAVSwarmCoordination.tsx` (僅保留多UE管理，移除編隊)
4. **保留**: `useReceiverSelection.ts` (多選功能保留)

這樣可以滿足您的需求：既專注單UE研究，又保留多UE擴展能力，但避免過度複雜的編隊協調功能。
