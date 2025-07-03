# Event Viewers 標題底線統一更新

## 更新日期
2024-12-19

## 問題描述
需要讓 Event D1、D2 左側每個標題都像 Event A4 一樣有底線，統一所有事件查看器的標題樣式。

## 解決方案

### 更新的樣式類別
1. `.control-section__title` (3個位置)
2. `.spec-title` (1個位置需要新增底線)

### 添加的CSS屬性
```scss
border-bottom: 2px solid rgba(52, 152, 219, 0.3) !important;
padding-bottom: 10px !important;
```

## 具體變更

### EventA4Viewer.scss
**位置1: 第389行左右的 control-section__title**
- 新增底線樣式：`border-bottom: 2px solid rgba(52, 152, 219, 0.3) !important;`
- 新增底部填充：`padding-bottom: 10px !important;`

**位置2: 第867行左右的 control-section__title (D1樣式區塊)**
- 新增底線樣式：`border-bottom: 2px solid rgba(52, 152, 219, 0.3) !important;`
- 新增底部填充：`padding-bottom: 10px !important;`

**位置3: 第1271行左右的 control-section__title (D2樣式區塊)**
- 新增底線樣式：`border-bottom: 2px solid rgba(52, 152, 219, 0.3) !important;`
- 新增底部填充：`padding-bottom: 10px !important;`

**位置4: 第403行左右的 spec-title**
- 新增底線樣式：`border-bottom: 2px solid rgba(52, 152, 219, 0.3) !important;`
- 新增底部填充：`padding-bottom: 10px !important;`

## 樣式說明

### 底線設計
- **顏色**：`rgba(52, 152, 219, 0.3)` - 與標題文字顏色 `#3498db` 相對應的半透明藍色
- **粗細**：`2px` - 與現有 spec-title 主標題一致
- **樣式**：`solid` - 實線
- **位置**：`border-bottom` - 底邊框

### 間距調整
- **底部填充**：`padding-bottom: 10px` - 確保文字與底線有適當間距
- **!important**：確保樣式優先級，覆蓋可能的衝突樣式

## 影響範圍
1. **Event A4 Viewer** - 左側控制面板所有標題
2. **Event D1 Viewer** - 左側控制面板所有標題
3. **Event D2 Viewer** - 左側控制面板所有標題

## 測試結果
- ✅ 前端構建成功
- ✅ 所有事件查看器標題現在都有一致的底線樣式
- ✅ 底線顏色與標題文字顏色協調
- ✅ 間距適當，視覺效果良好

## 統一性確認
- 所有 Event Viewer (A4/D1/D2) 的標題樣式現在完全一致
- 底線顏色、粗細、間距都統一
- 與整體設計風格保持一致性

## 相關文件
- `/src/components/domains/measurement/charts/EventA4Viewer.scss`

## 注意事項
- 此變更不影響現有功能
- 僅為視覺樣式的統一調整
- 保持了所有現有的樣式特性
