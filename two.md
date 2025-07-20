# NTN-Stack Phase 2 待开发项目清单

## 🎯 总体评估

基于对 `events-improvement-master.md` 中 Phase 2 描述的深度验证，**Phase 2 约 85% 完成**，但存在一些重要的待开发项目需要完成以达到文档声称的 100% 状态。

## ❌ **高优先级待开发项目**

### 1. 缺失的验证测试文件 🔥 **CRITICAL**

#### 1.1 D1 事件验证测试
- **缺失文件**: `test_phase2_2_verification.py`
- **重要性**: 验证 D1 全球化地理坐标和智能卫星选择功能
- **文档声称**: "D1 API 完整功能验证 ✅ 测试通过"
- **实际状况**: 验证测试文件不存在

#### 1.2 A4 事件验证测试  
- **缺失文件**: `test_phase2_4_verification.py`
- **重要性**: 验证 A4 位置补偿算法和触发条件逻辑
- **文档声称**: "A4 API 完整功能验证 ✅ 测试通过"
- **实际状况**: 验证测试文件不存在

### 2. 全球化地理坐标支援不完整 🔥 **HIGH**

#### 2.1 台湾硬编码坐标仍存在
文档声称已"移除台湾地区硬编码限制"，但以下文件仍有硬编码台湾坐标 `25.0173, 121.4695`：

```typescript
❌ 需要修复的文件：
- /simworld/frontend/src/pages/MeasurementEventsPage.tsx
- /simworld/frontend/src/components/domains/measurement/charts/EventD2Viewer.tsx  
- /simworld/frontend/src/components/domains/measurement/charts/PureD2Chart.tsx
- /simworld/frontend/src/components/domains/measurement/charts/EventD1Viewer.tsx
```

#### 2.2 全球化参考位置配置
- **问题**: 虽然有参考位置的 API，但仍默认使用台湾坐标
- **需求**: 实现真正的全球化参考位置默认值和配置界面
- **影响**: 无法在非台湾地区正常使用系统

## ⚠️ **中优先级待开发项目**

### 3. 缺失的事件特定图表组件

#### 3.1 D1EventSpecificChart.tsx
- **发现**: 其他事件都有对应的 EventSpecificChart (A4, D2, T1)，但 D1 缺失
- **现有**: 只有 EnhancedD1Chart.tsx 
- **需求**: 基于统一 SIB19 平台的 D1EventSpecificChart.tsx 组件
- **预期**: 400+ 行，符合统一架构设计

### 4. 文档与实现不一致问题

#### 4.1 EnhancedA4Viewer.tsx 行数错误
- **文档声称**: 36,000 行 (显然错误)
- **实际行数**: 712 行
- **需求**: 修正文档中的明显错误

#### 4.2 其他组件行数轻微差异
```
文档声称 vs 实际：
- EnhancedT1Chart.tsx: 705 行 vs 686 行 (-19 行)
- EnhancedT1Viewer.tsx: 508 行 vs 516 行 (+8 行)
- EnhancedA4Chart.tsx: 625 行 vs 619 行 (-6 行)
```

## 📋 **具体开发任务清单**

### 任务 1: 创建缺失的验证测试文件
```bash
# 需要创建的文件
netstack/test_phase2_2_verification.py  # D1 事件验证
netstack/test_phase2_4_verification.py  # A4 事件验证
```

**验证内容应包含**:
- D1: 卫星选择算法、全球化坐标、距离计算精度
- A4: 位置补偿算法、信号强度测量、触发条件逻辑

### 任务 2: 移除台湾硬编码坐标
```typescript
// 需要修改的文件和位置
MeasurementEventsPage.tsx:
- referenceLocation2: { lat: 25.0173, lon: 121.4695 } // 移除

EventD2Viewer.tsx, EventD1Viewer.tsx:
- lat: 25.0173, lon: 121.4695 // 改为可配置的全球化默认值

PureD2Chart.tsx:
- const _fixedReferenceLocation = { lat: 25.0173, lon: 121.4695 } // 移除硬编码
```

### 任务 3: 创建 D1EventSpecificChart.tsx
```typescript
// 新建文件
/simworld/frontend/src/components/domains/measurement/shared/components/D1EventSpecificChart.tsx

// 功能要求
- 基于统一 SIB19 平台
- 固定参考位置 (referenceLocation) 距离计算展示
- 智能服务卫星选择视觉化
- 400+ 行代码量
```

### 任务 4: 文档修正
```markdown
# events-improvement-master.md 需要修正的内容
- EnhancedA4Viewer.tsx: 36,000行 → 712行
- 其他组件行数微调以符合实际情况
```

## 🔄 **验证标准**

完成上述任务后，Phase 2 应该满足：

1. **验证测试完整性**: 所有事件 (D1, D2, T1, A4) 都有对应的验证测试
2. **全球化支援**: 无硬编码地理坐标，支持任意参考位置
3. **组件架构一致性**: 所有事件都有 EventSpecificChart 组件
4. **文档准确性**: 文档描述与实际实现一致

## 🎯 **预期完成时间**

- **任务 1** (验证测试): 2-3 天
- **任务 2** (全球化支援): 1-2 天  
- **任务 3** (D1 组件): 1 天
- **任务 4** (文档修正): 0.5 天

**总计**: 约 5-6 天可完成 Phase 2 的剩余 15%，达到真正的 100% 完成状态。

## 📊 **影响评估**

**如果不完成这些待开发项目**:
- ❌ 缺乏完整的验证覆盖，系统稳定性无法保证
- ❌ 无法在台湾以外地区正常使用
- ❌ 架构不一致，影响后续维护和扩展
- ❌ 文档错误影响开发者理解和使用

**完成后的价值**:
- ✅ 系统具备完整的测试覆盖和验证机制
- ✅ 真正实现全球化部署能力
- ✅ 架构统一，便于维护和扩展
- ✅ 文档准确，提升开发体验
