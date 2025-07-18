/**
 * API 連接診斷工具
 * 用於測試和診斷 NetStack API 連接問題
 */

import React, { useState, useCallback } from 'react'
import { netstackFetch } from '../../../config/api-config'

const APIConnectionTest: React.FC = () => {
    const [testResults, setTestResults] = useState<Record<string, any>>({})
    const [isRunning, setIsRunning] = useState(false)

    // API 端點測試列表 (使用正確的 NetStack 端點)
    const apiEndpoints = [
        // 基本健康檢查
        { name: '健康檢查', method: 'GET', url: '/health' },
        { name: 'API 根路徑', method: 'GET', url: '/' },

        // RL 訓練相關端點
        { name: 'RL 健康檢查', method: 'GET', url: '/api/v1/rl/health' },
        { name: 'RL 狀態', method: 'GET', url: '/api/v1/rl/status' },
        { name: '可用算法', method: 'GET', url: '/api/v1/rl/algorithms' },
        {
            name: '訓練狀態 (DQN)',
            method: 'GET',
            url: '/api/v1/rl/training/status/dqn',
        },
        {
            name: '訓練狀態 (PPO)',
            method: 'GET',
            url: '/api/v1/rl/training/status/ppo',
        },
        {
            name: '訓練狀態 (SAC)',
            method: 'GET',
            url: '/api/v1/rl/training/status/sac',
        },

        // 訓練控制端點
        {
            name: '啟動訓練 (DQN)',
            method: 'POST',
            url: '/api/v1/rl/training/start/dqn',
        },
        {
            name: '停止訓練 (DQN)',
            method: 'POST',
            url: '/api/v1/rl/training/stop-by-algorithm/dqn',
        },
        {
            name: '增強啟動 (DQN)',
            method: 'POST',
            url: '/api/v1/rl/enhanced/start/dqn',
        },
        {
            name: '增強停止 (DQN)',
            method: 'POST',
            url: '/api/v1/rl/enhanced/stop/dqn',
        },

        // Phase 2-3 端點
        {
            name: 'Phase 2-3 健康',
            method: 'GET',
            url: '/api/v1/rl/phase-2-3/health',
        },
        {
            name: 'Phase 2-3 系統狀態',
            method: 'GET',
            url: '/api/v1/rl/phase-2-3/system/status',
        },
        {
            name: 'Phase 2-3 啟動訓練',
            method: 'POST',
            url: '/api/v1/rl/phase-2-3/training/start',
        },

        // WebSocket 端點
        {
            name: 'WebSocket 監控',
            method: 'WS',
            url: '/api/v1/rl/phase-2-3/ws/monitoring',
        },
    ]

    // 執行單個 API 測試
    const testSingleEndpoint = async (endpoint: any) => {
        const startTime = Date.now()

        try {
            if (endpoint.method === 'WS') {
                // WebSocket 測試
                return new Promise((resolve) => {
                    const wsUrl = `ws://localhost:8080${endpoint.url}`
                    const ws = new WebSocket(wsUrl)

                    const timeout = setTimeout(() => {
                        ws.close()
                        resolve({
                            success: false,
                            error: 'WebSocket 連接超時',
                            responseTime: Date.now() - startTime,
                        })
                    }, 5000)

                    ws.onopen = () => {
                        clearTimeout(timeout)
                        ws.close()
                        resolve({
                            success: true,
                            status: 'Connected',
                            responseTime: Date.now() - startTime,
                        })
                    }

                    ws.onerror = (error) => {
                        clearTimeout(timeout)
                        resolve({
                            success: false,
                            error: 'WebSocket 連接失敗',
                            responseTime: Date.now() - startTime,
                        })
                    }
                })
            } else {
                // HTTP API 測試
                const options: any = { method: endpoint.method }

                if (endpoint.method === 'POST') {
                    options.headers = { 'Content-Type': 'application/json' }
                    options.body = JSON.stringify({
                        algorithm: 'dqn',
                        total_episodes: 100,
                        learning_rate: 0.001,
                    })
                }

                const response = await netstackFetch(endpoint.url, options)
                const responseTime = Date.now() - startTime

                if (response.ok) {
                    let data = null
                    try {
                        data = await response.json()
                    } catch (e) {
                        data = await response.text()
                    }

                    return {
                        success: true,
                        status: response.status,
                        statusText: response.statusText,
                        data: data,
                        responseTime,
                    }
                } else {
                    return {
                        success: false,
                        status: response.status,
                        statusText: response.statusText,
                        error: `HTTP ${response.status}: ${response.statusText}`,
                        responseTime,
                    }
                }
            }
        } catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : String(error),
                responseTime: Date.now() - startTime,
            }
        }
    }

    // 執行所有 API 測試
    const runAllTests = useCallback(async () => {
        setIsRunning(true)
        setTestResults({})

        console.log('🔍 開始 API 連接診斷...')

        for (const endpoint of apiEndpoints) {
            console.log(`📡 測試端點: ${endpoint.method} ${endpoint.url}`)

            const result = await testSingleEndpoint(endpoint)

            setTestResults((prev) => ({
                ...prev,
                [endpoint.name]: result,
            }))

            // 短暫延遲避免過於頻繁的請求
            await new Promise((resolve) => setTimeout(resolve, 500))
        }

        setIsRunning(false)
        console.log('✅ API 連接診斷完成')
    }, [])

    // 獲取結果狀態圖標
    const getStatusIcon = (result: any) => {
        if (!result) return '⏳'
        if (result.success) return '✅'
        return '❌'
    }

    // 獲取結果顏色
    const getStatusColor = (result: any) => {
        if (!result) return '#6b7280'
        if (result.success) return '#10b981'
        return '#ef4444'
    }

    return (
        <div
            style={{
                padding: '20px',
                minHeight: '100vh',
                background: '#1a1a1a',
                color: '#e5e7eb',
            }}
        >
            <div style={{ marginBottom: '30px' }}>
                <h1>🔧 API 連接診斷工具</h1>
                <p>診斷 NetStack API 連接狀況，幫助解決訓練控制問題</p>
            </div>

            {/* 控制面板 */}
            <div
                style={{
                    background: '#2a2a2a',
                    padding: '20px',
                    borderRadius: '8px',
                    marginBottom: '30px',
                    border: '1px solid #444',
                }}
            >
                <h2>🚀 診斷控制</h2>
                <button
                    onClick={runAllTests}
                    disabled={isRunning}
                    style={{
                        padding: '12px 24px',
                        background: isRunning ? '#6b7280' : '#4fc3f7',
                        color: 'white',
                        border: 'none',
                        borderRadius: '6px',
                        cursor: isRunning ? 'not-allowed' : 'pointer',
                        fontSize: '1rem',
                        fontWeight: '500',
                    }}
                >
                    {isRunning ? '🔄 診斷進行中...' : '▶️ 開始診斷'}
                </button>
            </div>

            {/* 測試結果 */}
            <div
                style={{
                    background: '#2a2a2a',
                    padding: '20px',
                    borderRadius: '8px',
                    border: '1px solid #444',
                }}
            >
                <h2>📊 診斷結果</h2>
                <div style={{ display: 'grid', gap: '15px' }}>
                    {apiEndpoints.map((endpoint) => {
                        const result = testResults[endpoint.name]
                        return (
                            <div
                                key={endpoint.name}
                                style={{
                                    padding: '15px',
                                    background: '#374151',
                                    borderRadius: '6px',
                                    border: '1px solid #4b5563',
                                }}
                            >
                                <div
                                    style={{
                                        display: 'flex',
                                        justifyContent: 'space-between',
                                        alignItems: 'center',
                                        marginBottom: '10px',
                                    }}
                                >
                                    <h4
                                        style={{
                                            margin: 0,
                                            color: getStatusColor(result),
                                        }}
                                    >
                                        {getStatusIcon(result)} {endpoint.name}
                                    </h4>
                                    <span
                                        style={{
                                            fontSize: '0.9rem',
                                            color: '#9ca3af',
                                            fontFamily: 'monospace',
                                        }}
                                    >
                                        {endpoint.method} {endpoint.url}
                                    </span>
                                </div>

                                {result && (
                                    <div
                                        style={{
                                            fontSize: '0.9rem',
                                            color: '#d1d5db',
                                        }}
                                    >
                                        <div style={{ marginBottom: '5px' }}>
                                            <strong>狀態:</strong>{' '}
                                            {result.success ? '成功' : '失敗'}
                                        </div>
                                        <div style={{ marginBottom: '5px' }}>
                                            <strong>響應時間:</strong>{' '}
                                            {result.responseTime}ms
                                        </div>
                                        {result.status && (
                                            <div
                                                style={{ marginBottom: '5px' }}
                                            >
                                                <strong>HTTP 狀態:</strong>{' '}
                                                {result.status}{' '}
                                                {result.statusText}
                                            </div>
                                        )}
                                        {result.error && (
                                            <div
                                                style={{
                                                    marginBottom: '5px',
                                                    color: '#ef4444',
                                                }}
                                            >
                                                <strong>錯誤:</strong>{' '}
                                                {result.error}
                                            </div>
                                        )}
                                        {result.data && (
                                            <details
                                                style={{ marginTop: '10px' }}
                                            >
                                                <summary
                                                    style={{
                                                        cursor: 'pointer',
                                                        color: '#4fc3f7',
                                                    }}
                                                >
                                                    查看響應數據
                                                </summary>
                                                <pre
                                                    style={{
                                                        marginTop: '10px',
                                                        padding: '10px',
                                                        background: '#1f2937',
                                                        borderRadius: '4px',
                                                        fontSize: '0.8rem',
                                                        overflow: 'auto',
                                                        maxHeight: '200px',
                                                    }}
                                                >
                                                    {typeof result.data ===
                                                    'string'
                                                        ? result.data
                                                        : JSON.stringify(
                                                              result.data,
                                                              null,
                                                              2
                                                          )}
                                                </pre>
                                            </details>
                                        )}
                                    </div>
                                )}
                            </div>
                        )
                    })}
                </div>
            </div>

            {/* 診斷建議 */}
            <div
                style={{
                    background: '#2a2a2a',
                    padding: '20px',
                    borderRadius: '8px',
                    marginTop: '30px',
                    border: '1px solid #444',
                }}
            >
                <h2>💡 診斷建議</h2>
                <div style={{ fontSize: '0.9rem', lineHeight: '1.6' }}>
                    <h3 style={{ color: '#4fc3f7' }}>常見問題解決方案：</h3>
                    <ul>
                        <li>
                            <strong>500 內部服務器錯誤:</strong> 檢查 NetStack
                            服務是否正常運行
                        </li>
                        <li>
                            <strong>404 未找到:</strong> API
                            端點路徑可能不正確，嘗試其他版本的端點
                        </li>
                        <li>
                            <strong>連接超時:</strong> 檢查網絡連接和服務器狀態
                        </li>
                        <li>
                            <strong>CORS 錯誤:</strong> 檢查跨域配置
                        </li>
                        <li>
                            <strong>WebSocket 連接失敗:</strong> 檢查 WebSocket
                            服務是否啟用
                        </li>
                    </ul>

                    <h3 style={{ color: '#4fc3f7' }}>建議的調試步驟：</h3>
                    <ol>
                        <li>確認 NetStack 服務在 localhost:8080 上運行</li>
                        <li>檢查服務日誌中的錯誤信息</li>
                        <li>嘗試直接訪問 API 端點 (如 curl 或 Postman)</li>
                        <li>檢查防火牆和網絡配置</li>
                        <li>如果所有端點都失敗，系統會自動切換到模擬模式</li>
                    </ol>
                </div>
            </div>
        </div>
    )
}

export default APIConnectionTest
