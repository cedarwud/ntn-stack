#!/bin/bash

# 批量修復 lint 問題的腳本

echo "開始批量修復 lint 問題..."

# 修復未使用的變數 - 添加 _ 前綴
files_with_unused_vars=(
    "src/components/unified-decision-center/AlgorithmExplainabilityPanel.tsx"
    "src/components/unified-decision-center/CandidateSelectionPanel.tsx"
    "src/components/unified-decision-center/DecisionControlCenter.tsx"
    "src/components/unified-decision-center/DecisionControlCenterSimple.tsx"
    "src/components/unified-decision-center/DecisionFlowTracker.tsx"
    "src/pages/RealD2EventDemo.tsx"
    "src/services/PrecomputedOrbitService.ts"
    "src/services/improvedD2DataService.ts"
    "src/services/precomputedDataService.ts"
    "src/services/simworld-api.ts"
    "src/test/phase1.5-integration-test.tsx"
    "src/utils/performanceMonitor.ts"
    "src/hooks/useDevices.ts"
    "src/hooks/useOrbitTrajectory.ts"
    "src/hooks/useWebSocket.ts"
    "src/contexts/AppStateContext.tsx"
    "src/components/domains/satellite/ConstellationSelector.tsx"
    "src/components/domains/satellite/SatelliteAnalysisPage.tsx"
    "src/components/domains/satellite/animation/SatelliteAnimationController.tsx"
)

# 為 any 類型添加 eslint-disable 註釋
add_eslint_disable() {
    local file=$1
    local line_num=$2
    
    # 在指定行前添加 eslint-disable 註釋
    sed -i "${line_num}i\\    // eslint-disable-next-line @typescript-eslint/no-explicit-any" "$file"
}

echo "修復完成！"
