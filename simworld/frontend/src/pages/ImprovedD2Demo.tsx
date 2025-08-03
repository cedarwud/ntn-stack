/**
 * ImprovedD2Demo - 改進版 D2 事件演示頁面
 *
 * 展示功能：
 * 1. 改進版 D2 圖表與數據平滑化效果
 * 2. 觸發時機清晰標示和換手預測
 * 3. 與立體圖的時間同步演示
 * 4. 數據品質分析和性能指標
 */

import React, { useState, useCallback } from 'react'
// SynchronizedD2Dashboard removed - using simplified implementation
// import SynchronizedD2Dashboard from '../components/domains/measurement/charts/SynchronizedD2Dashboard'
// import {
//     HandoverEvent,
//     DataQualityMetrics,
//     TimeSync
// } from '../components/domains/measurement/charts/SynchronizedD2Dashboard'
import {
    DEFAULT_D2_TRIGGER_CONFIG,
    DEFAULT_SMOOTHING_CONFIG,
} from '../services/improvedD2DataService'

const ImprovedD2Demo: React.FC = () => {
    // 狀態管理
    const [useTestData, setUseTestData] = useState(true)
    const [showRawData, setShowRawData] = useState(false)
    const [dataQuality, setDataQuality] = useState<DataQualityMetrics | null>(
        null
    )
    const [detectedEvents, setDetectedEvents] = useState<HandoverEvent[]>([])
    const [currentTimeSync, setCurrentTimeSync] = useState<TimeSync | null>(
        null
    )
    const [logs, setLogs] = useState<string[]>([])

    // 添加日誌
    const addLog = useCallback((message: string) => {
        const timestamp = new Date().toLocaleTimeString()
        setLogs((prev) => [`[${timestamp}] ${message}`, ...prev.slice(0, 19)]) // 保留最新20條
    }, [])

    // 換手事件檢測回調
    const handleHandoverEvent = useCallback(
        (event: HandoverEvent) => {
            setDetectedEvents((prev) => [...prev, event])
            addLog(
                `🚀 檢測到換手事件: ${event.startTime}s-${event.endTime}s (${event.handoverLikelihood}可能性)`
            )
        },
        [addLog]
    )

    // 數據品質變化回調
    const handleDataQualityChange = useCallback(
        (metrics: DataQualityMetrics) => {
            setDataQuality(metrics)
            addLog(
                `📊 數據品質更新: 信噪比 ${metrics.signalToNoiseRatio.toFixed(
                    1
                )}, 平滑效果 ${(metrics.smoothingEffectiveness * 100).toFixed(
                    1
                )}%`
            )
        },
        [addLog]
    )

    // 時間同步回調
    const handleTimeSync = useCallback((timeSync: TimeSync) => {
        setCurrentTimeSync(timeSync)
    }, [])

    return (
        <div
            style={{
                minHeight: '100vh',
                backgroundColor: '#0f0f0f',
                color: '#ffffff',
                padding: '20px',
            }}
        >
            {/* 頁面標題 */}
            <div
                style={{
                    textAlign: 'center',
                    marginBottom: '30px',
                }}
            >
                <h1
                    style={{
                        fontSize: '32px',
                        fontWeight: 'bold',
                        marginBottom: '10px',
                        background: 'linear-gradient(45deg, #00D2FF, #FF6B35)',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent',
                    }}
                >
                    改進版 D2 事件分析系統
                </h1>
                <p
                    style={{
                        fontSize: '16px',
                        opacity: 0.8,
                        maxWidth: '800px',
                        margin: '0 auto',
                    }}
                >
                    基於 SGP4 精確軌道計算的衛星換手觸發時機分析 |
                    智能數據平滑化 | 立體圖時間同步
                </p>
            </div>

            {/* 控制面板 */}
            <div
                style={{
                    display: 'flex',
                    justifyContent: 'center',
                    gap: '20px',
                    marginBottom: '30px',
                    flexWrap: 'wrap',
                }}
            >
                <div
                    style={{
                        padding: '16px',
                        backgroundColor: '#1e293b',
                        borderRadius: '12px',
                        border: '2px solid #374151',
                    }}
                >
                    <h3 style={{ marginBottom: '12px', fontSize: '16px' }}>
                        數據源設定
                    </h3>
                    <label
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            cursor: 'pointer',
                        }}
                    >
                        <input
                            type="checkbox"
                            checked={useTestData}
                            onChange={(e) => setUseTestData(e.target.checked)}
                            style={{ marginRight: '8px' }}
                        />
                        使用模擬測試數據
                    </label>
                </div>

                <div
                    style={{
                        padding: '16px',
                        backgroundColor: '#1e293b',
                        borderRadius: '12px',
                        border: '2px solid #374151',
                    }}
                >
                    <h3 style={{ marginBottom: '12px', fontSize: '16px' }}>
                        顯示選項
                    </h3>
                    <label
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            cursor: 'pointer',
                        }}
                    >
                        <input
                            type="checkbox"
                            checked={showRawData}
                            onChange={(e) => setShowRawData(e.target.checked)}
                            style={{ marginRight: '8px' }}
                        />
                        顯示原始高頻數據
                    </label>
                </div>

                {/* 數據品質指標 */}
                {dataQuality && (
                    <div
                        style={{
                            padding: '16px',
                            backgroundColor: '#1e293b',
                            borderRadius: '12px',
                            border: '2px solid #374151',
                            minWidth: '200px',
                        }}
                    >
                        <h3 style={{ marginBottom: '12px', fontSize: '16px' }}>
                            即時品質指標
                        </h3>
                        <div
                            style={{
                                fontSize: '13px',
                                display: 'flex',
                                flexDirection: 'column',
                                gap: '4px',
                            }}
                        >
                            <div>📊 總數據點: {dataQuality.totalPoints}</div>
                            <div>
                                🔊 信噪比:{' '}
                                {dataQuality.signalToNoiseRatio.toFixed(1)}
                            </div>
                            <div>
                                ✨ 平滑效果:{' '}
                                {(
                                    dataQuality.smoothingEffectiveness * 100
                                ).toFixed(1)}
                                %
                            </div>
                            <div>
                                🎯 觸發準確度:{' '}
                                {(dataQuality.triggerAccuracy * 100).toFixed(1)}
                                %
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* 主要儀表板 */}
            <div
                style={{
                    display: 'flex',
                    gap: '20px',
                    flexWrap: 'wrap',
                }}
            >
                {/* D2 圖表儀表板 */}
                <div style={{ flex: '2', minWidth: '800px' }}>
                    {/* SynchronizedD2Dashboard removed - using placeholder */}
                    <div
                        style={{
                            width: '100%',
                            height: '500px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            backgroundColor: '#1a1a1a',
                            color: '#ffffff',
                            border: '1px solid #333',
                            borderRadius: '8px',
                        }}
                    >
                        <div style={{ textAlign: 'center' }}>
                            <h3>Improved D2 Dashboard</h3>
                            <p>SynchronizedD2Dashboard component removed</p>
                            <p style={{ fontSize: '0.9em', opacity: 0.7 }}>
                                Use EventD2Viewer for D2 event visualization
                            </p>
                        </div>
                    </div>
                </div>

                {/* 側邊信息面板 */}
                <div
                    style={{
                        flex: '1',
                        minWidth: '300px',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '20px',
                    }}
                >
                    {/* 換手事件統計 */}
                    <div
                        style={{
                            padding: '16px',
                            backgroundColor: '#1e293b',
                            borderRadius: '12px',
                            border: '2px solid #374151',
                        }}
                    >
                        <h3 style={{ marginBottom: '12px', fontSize: '16px' }}>
                            🚀 換手事件統計
                        </h3>
                        <div
                            style={{
                                fontSize: '14px',
                                display: 'flex',
                                flexDirection: 'column',
                                gap: '8px',
                            }}
                        >
                            <div>總事件數: {detectedEvents.length}</div>
                            <div style={{ color: '#ef4444' }}>
                                高可能性:{' '}
                                {
                                    detectedEvents.filter(
                                        (e) => e.handoverLikelihood === 'high'
                                    ).length
                                }
                            </div>
                            <div style={{ color: '#f97316' }}>
                                中等可能性:{' '}
                                {
                                    detectedEvents.filter(
                                        (e) => e.handoverLikelihood === 'medium'
                                    ).length
                                }
                            </div>
                            <div style={{ color: '#eab308' }}>
                                低可能性:{' '}
                                {
                                    detectedEvents.filter(
                                        (e) => e.handoverLikelihood === 'low'
                                    ).length
                                }
                            </div>
                        </div>

                        {/* 最近事件列表 */}
                        {detectedEvents.length > 0 && (
                            <div style={{ marginTop: '12px' }}>
                                <h4
                                    style={{
                                        fontSize: '14px',
                                        marginBottom: '8px',
                                    }}
                                >
                                    最近事件:
                                </h4>
                                <div
                                    style={{
                                        maxHeight: '150px',
                                        overflowY: 'auto',
                                    }}
                                >
                                    {detectedEvents
                                        .slice(-5)
                                        .reverse()
                                        .map((event, index) => (
                                            <div
                                                key={index}
                                                style={{
                                                    padding: '6px 8px',
                                                    backgroundColor: '#374151',
                                                    borderRadius: '4px',
                                                    marginBottom: '4px',
                                                    fontSize: '12px',
                                                }}
                                            >
                                                <div>
                                                    {event.startTime}s -{' '}
                                                    {event.endTime}s
                                                </div>
                                                <div
                                                    style={{
                                                        color:
                                                            event.handoverLikelihood ===
                                                            'high'
                                                                ? '#ef4444'
                                                                : event.handoverLikelihood ===
                                                                  'medium'
                                                                ? '#f97316'
                                                                : '#eab308',
                                                    }}
                                                >
                                                    {event.handoverLikelihood}{' '}
                                                    可能性 (強度:{' '}
                                                    {(
                                                        event.triggerStrength *
                                                        100
                                                    ).toFixed(0)}
                                                    %)
                                                </div>
                                            </div>
                                        ))}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* 時間同步狀態 */}
                    {currentTimeSync && (
                        <div
                            style={{
                                padding: '16px',
                                backgroundColor: '#1e293b',
                                borderRadius: '12px',
                                border: '2px solid #374151',
                            }}
                        >
                            <h3
                                style={{
                                    marginBottom: '12px',
                                    fontSize: '16px',
                                }}
                            >
                                ⏰ 時間同步狀態
                            </h3>
                            <div
                                style={{
                                    fontSize: '14px',
                                    display: 'flex',
                                    flexDirection: 'column',
                                    gap: '6px',
                                }}
                            >
                                <div>
                                    當前時間:{' '}
                                    {currentTimeSync.currentTime.toFixed(1)}s
                                </div>
                                <div>
                                    播放狀態:{' '}
                                    {currentTimeSync.isPlaying
                                        ? '🎬 播放中'
                                        : '⏸️ 已暫停'}
                                </div>
                                <div>
                                    播放速度: {currentTimeSync.playbackSpeed}x
                                </div>
                                <div>
                                    總時長: {currentTimeSync.totalDuration}s
                                </div>
                                <div
                                    style={{
                                        marginTop: '8px',
                                        height: '4px',
                                        backgroundColor: '#374151',
                                        borderRadius: '2px',
                                        overflow: 'hidden',
                                    }}
                                >
                                    <div
                                        style={{
                                            height: '100%',
                                            width: `${
                                                (currentTimeSync.currentTime /
                                                    currentTimeSync.totalDuration) *
                                                100
                                            }%`,
                                            backgroundColor: '#00D2FF',
                                            transition: 'width 0.3s',
                                        }}
                                    />
                                </div>
                            </div>
                        </div>
                    )}

                    {/* 系統日誌 */}
                    <div
                        style={{
                            padding: '16px',
                            backgroundColor: '#1e293b',
                            borderRadius: '12px',
                            border: '2px solid #374151',
                            flex: '1',
                        }}
                    >
                        <h3 style={{ marginBottom: '12px', fontSize: '16px' }}>
                            📝 系統日誌
                        </h3>
                        <div
                            style={{
                                maxHeight: '200px',
                                overflowY: 'auto',
                                fontSize: '12px',
                                fontFamily: 'monospace',
                            }}
                        >
                            {logs.length === 0 ? (
                                <div style={{ opacity: 0.6 }}>等待事件...</div>
                            ) : (
                                logs.map((log, index) => (
                                    <div
                                        key={index}
                                        style={{
                                            marginBottom: '4px',
                                            padding: '2px 4px',
                                            backgroundColor:
                                                index === 0
                                                    ? '#374151'
                                                    : 'transparent',
                                            borderRadius: '2px',
                                            opacity: Math.max(
                                                0.4,
                                                1 - index * 0.1
                                            ),
                                        }}
                                    >
                                        {log}
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* 使用說明 */}
            <div
                style={{
                    marginTop: '30px',
                    padding: '20px',
                    backgroundColor: '#1e293b',
                    borderRadius: '12px',
                    border: '2px solid #374151',
                }}
            >
                <h3 style={{ marginBottom: '16px', fontSize: '18px' }}>
                    📖 使用說明
                </h3>
                <div
                    style={{
                        display: 'grid',
                        gridTemplateColumns:
                            'repeat(auto-fit, minmax(300px, 1fr))',
                        gap: '16px',
                        fontSize: '14px',
                    }}
                >
                    <div>
                        <h4 style={{ color: '#00D2FF', marginBottom: '8px' }}>
                            🎯 觸發時機識別
                        </h4>
                        <ul style={{ paddingLeft: '20px', lineHeight: '1.6' }}>
                            <li>綠色區塊：高可能性換手時機</li>
                            <li>橙色區塊：中等可能性換手時機</li>
                            <li>黃色區塊：低可能性換手時機</li>
                            <li>紅色閾值線：D2 觸發條件邊界</li>
                        </ul>
                    </div>

                    <div>
                        <h4 style={{ color: '#FF6B35', marginBottom: '8px' }}>
                            📊 數據平滑化
                        </h4>
                        <ul style={{ paddingLeft: '20px', lineHeight: '1.6' }}>
                            <li>粗線：平滑後的清晰趨勢</li>
                            <li>細線：原始SGP4高頻數據</li>
                            <li>自動去除噪聲，突出換手模式</li>
                            <li>保留重要的軌道動態特徵</li>
                        </ul>
                    </div>

                    <div>
                        <h4 style={{ color: '#28a745', marginBottom: '8px' }}>
                            ⏰ 時間同步
                        </h4>
                        <ul style={{ paddingLeft: '20px', lineHeight: '1.6' }}>
                            <li>點擊圖表可跳轉到指定時間</li>
                            <li>播放控制與立體圖同步</li>
                            <li>換手事件按鈕快速定位</li>
                            <li>橙色時間線表示當前位置</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default ImprovedD2Demo
