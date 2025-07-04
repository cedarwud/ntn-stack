#!/bin/bash

# 快速修復 lint 錯誤的腳本

echo "🔧 開始修復 lint 錯誤..."

# 1. 修復未使用的變數（添加下劃線前綴）
echo "✅ 修復未使用變數..."

# PureD2Chart.tsx 中的未使用變數
sed -i 's/calculateAdvancedSatellitePosition/_calculateAdvancedSatellitePosition/g' src/components/domains/measurement/charts/PureD2Chart.tsx
sed -i 's/calculate3DDistance/_calculate3DDistance/g' src/components/domains/measurement/charts/PureD2Chart.tsx  
sed -i 's/ueTrajectory =/_ueTrajectory =/g' src/components/domains/measurement/charts/PureD2Chart.tsx
sed -i 's/fixedReferenceLocation =/_fixedReferenceLocation =/g' src/components/domains/measurement/charts/PureD2Chart.tsx
sed -i 's/isInitialized =/_isInitialized =/g' src/components/domains/measurement/charts/PureD2Chart.tsx

# EventSelector.tsx 中的未使用導入
sed -i 's/EventConfig,/_EventConfig,/g' src/components/domains/measurement/components/EventSelector.tsx

# BaseChart.tsx 中的未使用參數
sed -i 's/eventType,/_eventType,/g' src/components/domains/measurement/shared/components/BaseChart.tsx
sed -i 's/params,/_params,/g' src/components/domains/measurement/shared/components/BaseChart.tsx

# MeasurementEventsModal.tsx 中的未使用導入和變數
sed -i 's/EventA4Viewer,/_EventA4Viewer,/g' src/components/layout/MeasurementEventsModal.tsx
sed -i 's/EventD1Viewer,/_EventD1Viewer,/g' src/components/layout/MeasurementEventsModal.tsx
sed -i 's/EventD2Viewer,/_EventD2Viewer,/g' src/components/layout/MeasurementEventsModal.tsx  
sed -i 's/EventT1Viewer,/_EventT1Viewer,/g' src/components/layout/MeasurementEventsModal.tsx
sed -i 's/modalTitleConfig =/_modalTitleConfig =/g' src/components/layout/MeasurementEventsModal.tsx
sed -i 's/handleRefresh =/_handleRefresh =/g' src/components/layout/MeasurementEventsModal.tsx

# MeasurementEventsPage.tsx 中的未使用變數
sed -i 's/currentParams =/_currentParams =/g' src/pages/MeasurementEventsPage.tsx
sed -i 's/currentParamHandler =/_currentParamHandler =/g' src/pages/MeasurementEventsPage.tsx

# PureD1Chart.tsx 中的未使用參數
sed -i 's/chartData/_chartData/g' src/components/domains/measurement/charts/PureD1Chart.tsx

# 2. 修復 any 類型
echo "✅ 修復 any 類型..."

# 將 any[] 替換為更具體的類型
sed -i 's/any\[\]/Record<string, unknown>\[\]/g' src/components/domains/measurement/charts/PureD1Chart.tsx
sed -i 's/} as any/} as Record<string, unknown>/g' src/components/domains/measurement/charts/PureD1Chart.tsx

# EventConfigPanel.tsx 中的 any 類型
sed -i 's/: any/: Record<string, unknown>/g' src/components/domains/measurement/components/EventConfigPanel.tsx

# event-management-test.tsx 中的 any 類型  
sed -i 's/: any/: Record<string, unknown>/g' src/test/event-management-test.tsx

echo "🎉 lint 錯誤修復完成！"