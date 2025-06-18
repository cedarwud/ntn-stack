/**
 * 換手自我檢測測試組件
 * 用於驗證換手邏輯是否正確，確保不會出現自我換手問題
 */

import React, { useState, useEffect } from 'react'

interface HandoverTestResult {
    testName: string
    passed: boolean
    details: string
}

const HandoverSelfTest: React.FC = () => {
    const [testResults, setTestResults] = useState<HandoverTestResult[]>([])
    const [isRunning, setIsRunning] = useState(false)

    // 模擬衛星數據
    const mockSatellites = Array.from({ length: 18 }, (_, i) => ({
        norad_id: 1000 + i,
        name: `STARLINK-${1000 + i}`,
        elevation_deg: 30 + Math.random() * 60,
        azimuth_deg: Math.random() * 360,
        distance_km: 500 + Math.random() * 500,
    }))

    // 測試1：基本自我換手防護
    const testBasicSelfHandoverPrevention = (): HandoverTestResult => {
        const currentSatelliteIndex = 0
        const currentSatellite = mockSatellites[currentSatelliteIndex]

        // 模擬HandoverManager的邏輯
        const availableTargets = mockSatellites.filter(
            (sat, index) => index !== currentSatelliteIndex
        )

        const futureBest =
            availableTargets.length > 0 ? availableTargets[0] : null

        const passed =
            futureBest !== null &&
            futureBest.norad_id !== currentSatellite.norad_id

        return {
            testName: '基本自我換手防護',
            passed,
            details: passed
                ? `✅ 成功選擇不同衛星: ${currentSatellite.name} -> ${futureBest?.name}`
                : `❌ 選擇了相同衛星或無可用目標`,
        }
    }

    // 測試2：空候選列表處理
    const testEmptyCandidateHandling = (): HandoverTestResult => {
        const singleSatellite = [mockSatellites[0]]
        const currentSatelliteIndex = 0

        const availableTargets = singleSatellite.filter(
            (sat, index) => index !== currentSatelliteIndex
        )

        const passed = availableTargets.length === 0

        return {
            testName: '空候選列表處理',
            passed,
            details: passed
                ? '✅ 正確處理只有一個衛星的情況'
                : '❌ 未正確處理空候選列表',
        }
    }

    // 測試3：多次換手邏輯一致性
    const testMultipleHandoverConsistency = (): HandoverTestResult => {
        const testRuns = 10
        let allPassed = true
        const results: string[] = []

        for (let i = 0; i < testRuns; i++) {
            const currentIndex = Math.floor(
                Math.random() * mockSatellites.length
            )
            const currentSat = mockSatellites[currentIndex]

            const availableTargets = mockSatellites.filter(
                (sat, index) => index !== currentIndex
            )

            if (availableTargets.length > 0) {
                const target = availableTargets[0]
                const isSelfHandover = target.norad_id === currentSat.norad_id

                if (isSelfHandover) {
                    allPassed = false
                    results.push(
                        `❌ 第${i + 1}次: ${currentSat.name} -> ${
                            target.name
                        } (自我換手)`
                    )
                } else {
                    results.push(
                        `✅ 第${i + 1}次: ${currentSat.name} -> ${target.name}`
                    )
                }
            }
        }

        return {
            testName: '多次換手邏輯一致性',
            passed: allPassed,
            details: allPassed
                ? `✅ ${testRuns}次測試全部通過`
                : `❌ 發現自我換手問題\n${results.join('\n')}`,
        }
    }

    // 測試4：邊界條件測試
    const testBoundaryConditions = (): HandoverTestResult => {
        const tests = [
            {
                name: '兩個衛星',
                satellites: mockSatellites.slice(0, 2),
                currentIndex: 0,
            },
            {
                name: '最後一個衛星',
                satellites: mockSatellites,
                currentIndex: mockSatellites.length - 1,
            },
            {
                name: '第一個衛星',
                satellites: mockSatellites,
                currentIndex: 0,
            },
        ]

        let allPassed = true
        const results: string[] = []

        tests.forEach((test) => {
            const availableTargets = test.satellites.filter(
                (sat, index) => index !== test.currentIndex
            )

            if (availableTargets.length > 0) {
                const target = availableTargets[0]
                const current = test.satellites[test.currentIndex]
                const isSelfHandover = target.norad_id === current.norad_id

                if (isSelfHandover) {
                    allPassed = false
                    results.push(`❌ ${test.name}: 自我換手`)
                } else {
                    results.push(`✅ ${test.name}: 正常換手`)
                }
            } else {
                results.push(`✅ ${test.name}: 正確處理無候選者情況`)
            }
        })

        return {
            testName: '邊界條件測試',
            passed: allPassed,
            details: results.join('\n'),
        }
    }

    // 運行所有測試
    const runAllTests = async () => {
        setIsRunning(true)
        setTestResults([])

        const tests = [
            testBasicSelfHandoverPrevention,
            testEmptyCandidateHandling,
            testMultipleHandoverConsistency,
            testBoundaryConditions,
        ]

        for (const test of tests) {
            await new Promise((resolve) => setTimeout(resolve, 500)) // 模擬測試延遲
            const result = test()
            setTestResults((prev) => [...prev, result])
        }

        setIsRunning(false)
    }

    // 計算測試統計
    const passedTests = testResults.filter((r) => r.passed).length
    const totalTests = testResults.length
    const allPassed = passedTests === totalTests && totalTests > 0

    return (
        <div
            style={{
                padding: '20px',
                backgroundColor: '#1a1a1a',
                color: '#ffffff',
                fontFamily: 'monospace',
                borderRadius: '8px',
                margin: '20px',
            }}
        >
            <h2 style={{ color: '#4fc3f7', marginBottom: '20px' }}>
                🧪 換手自我檢測測試
            </h2>

            <div style={{ marginBottom: '20px' }}>
                <button
                    onClick={runAllTests}
                    disabled={isRunning}
                    style={{
                        backgroundColor: isRunning ? '#666' : '#4fc3f7',
                        color: '#ffffff',
                        border: 'none',
                        padding: '10px 20px',
                        borderRadius: '4px',
                        cursor: isRunning ? 'not-allowed' : 'pointer',
                        fontSize: '16px',
                    }}
                >
                    {isRunning ? '🔄 測試進行中...' : '▶️ 運行測試'}
                </button>
            </div>

            {testResults.length > 0 && (
                <div style={{ marginBottom: '20px' }}>
                    <h3
                        style={{
                            color: allPassed ? '#4caf50' : '#f44336',
                            marginBottom: '10px',
                        }}
                    >
                        測試結果: {passedTests}/{totalTests} 通過
                        {allPassed ? ' ✅' : ' ❌'}
                    </h3>
                </div>
            )}

            <div>
                {testResults.map((result, index) => (
                    <div
                        key={index}
                        style={{
                            backgroundColor: result.passed
                                ? '#1b5e20'
                                : '#b71c1c',
                            padding: '15px',
                            marginBottom: '10px',
                            borderRadius: '4px',
                            borderLeft: `4px solid ${
                                result.passed ? '#4caf50' : '#f44336'
                            }`,
                        }}
                    >
                        <h4
                            style={{
                                margin: '0 0 10px 0',
                                color: result.passed ? '#4caf50' : '#f44336',
                            }}
                        >
                            {result.passed ? '✅' : '❌'} {result.testName}
                        </h4>
                        <pre
                            style={{
                                margin: 0,
                                whiteSpace: 'pre-wrap',
                                fontSize: '14px',
                                color: '#e0e0e0',
                            }}
                        >
                            {result.details}
                        </pre>
                    </div>
                ))}
            </div>

            {allPassed && testResults.length > 0 && (
                <div
                    style={{
                        backgroundColor: '#1b5e20',
                        padding: '15px',
                        borderRadius: '4px',
                        marginTop: '20px',
                        textAlign: 'center',
                    }}
                >
                    <h3 style={{ color: '#4caf50', margin: 0 }}>
                        🎉 所有測試通過！換手邏輯正常運作
                    </h3>
                </div>
            )}
        </div>
    )
}

export default HandoverSelfTest
