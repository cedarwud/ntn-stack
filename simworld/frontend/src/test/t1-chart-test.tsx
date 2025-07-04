/**
 * T1 Chart Test - 測試重新設計的 CondEvent T1 圖表
 * 驗證狀態型矩形脈衝圖表、時間窗口條件和動畫功能
 */

import React from 'react'
import { EventT1Viewer } from '../components/domains/measurement/charts/EventT1Viewer'

export const T1ChartTest: React.FC = () => {
    return (
        <div style={{ padding: '20px', backgroundColor: '#1a1a1a', minHeight: '100vh' }}>
            <h1 style={{ color: 'white', marginBottom: '20px' }}>
                T1 Chart Test - 條件事件 T1 重新設計測試
            </h1>
            
            <div style={{ marginBottom: '20px', color: '#ccc' }}>
                <h3>測試重點：</h3>
                <ul>
                    <li>✓ 矩形脈衝狀態曲線 (0/1 狀態)</li>
                    <li>✓ 時間窗口條件 (Mt &gt; Thresh1 和 Mt &gt; Thresh1+Duration)</li>
                    <li>✓ 垂直參考線 (進入/離開時間點)</li>
                    <li>✓ 動畫控制和當前時間游標</li>
                    <li>✓ 3GPP TS 38.331 規範合規性</li>
                </ul>
            </div>

            <EventT1Viewer 
                isDarkTheme={true}
                initialParams={{
                    t1Threshold: 5,    // 5 秒門檻
                    timeToTrigger: 0,
                    reportAmount: 1,
                    reportInterval: 1,
                    reportOnLeave: true
                }}
            />

            <div style={{ marginTop: '20px', color: '#ccc' }}>
                <h3>驗證要點：</h3>
                <ol>
                    <li><strong>狀態曲線：</strong> 應顯示矩形脈衝，在 5-15 秒區間內為 1 (激活)，其餘為 0 (未激活)</li>
                    <li><strong>垂直線：</strong> 5 秒處應有進入線，15 秒處應有離開線</li>
                    <li><strong>時間窗口：</strong> 5-15 秒區間應有半透明綠色背景</li>
                    <li><strong>動畫控制：</strong> 紅色虛線游標應可控制當前時間 Mt</li>
                    <li><strong>狀態邏輯：</strong> 當 Mt 在 [5000, 15000] 範圍內時事件激活</li>
                    <li><strong>🆕 浮動視窗：</strong> 動畫解說面板應為可拖動的浮動視窗，與 A4 事件相同</li>
                    <li><strong>🆕 拖拽功能：</strong> 可以拖動解說面板到螢幕任意位置</li>
                    <li><strong>🆕 透明度控制：</strong> 可以調整面板透明度 (0.3-1.0)</li>
                    <li><strong>🆕 面板控制：</strong> 包含最小化、展開/收起、技術細節切換、關閉等按鈕</li>
                </ol>
            </div>
        </div>
    )
}

export default T1ChartTest