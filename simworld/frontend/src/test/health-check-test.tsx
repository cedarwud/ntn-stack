/**
 * 健康檢查測試組件
 * 用於手動驗證系統健康狀態
 */
import React, { useState } from 'react'
import {
    runSystemTests,
    displayTestSummary,
    SystemTestResults,
} from './test-utils'
import {
    healthDiagnostics,
    SystemDiagnostics,
} from '../utils/health-diagnostics'
import { fetchRealSatelliteData } from '../services/realSatelliteService'
import { ApiRoutes } from '../config/apiRoutes'

export const HealthCheckTest: React.FC = () => {
    const [isTestingBasic, setIsTestingBasic] = useState(false)
    const [isTestingAdvanced, setIsTestingAdvanced] = useState(false)
    const [isTestingSatellites, setIsTestingSatellites] = useState(false)
    const [basicResults, setBasicResults] = useState<SystemTestResults | null>(
        null
    )
    const [advancedResults, setAdvancedResults] =
        useState<SystemDiagnostics | null>(null)
    const [satelliteResults, setSatelliteResults] = useState<any>(null)

    const runBasicTest = async () => {
        setIsTestingBasic(true)
        try {
            console.log('🔍 開始基本系統測試...')
            const results = await runSystemTests(false)
            setBasicResults(results)
            displayTestSummary(results)

            // 檢查是否有先前的錯誤
            if (results.overall_score > 80) {
                console.log('✅ 系統基本功能正常')
            } else {
                console.warn('⚠️ 系統有部分問題，建議查看詳細結果')
            }
        } catch (error) {
            console.error('基本測試失敗:', error)
        } finally {
            setIsTestingBasic(false)
        }
    }

    const runAdvancedTest = async () => {
        setIsTestingAdvanced(true)
        try {
            console.log('🔬 開始進階系統診斷...')
            const results = await healthDiagnostics.runDiagnostics()
            setAdvancedResults(results)

            console.log('📊 診斷結果:', results)

            // 顯示診斷總結
            console.log(`總體健康狀況: ${results.overall_health}`)
            console.log(
                `健康服務: ${results.summary.healthy_count}/${results.summary.total_checks}`
            )

            if (results.summary.error_count > 0) {
                console.warn(
                    `⚠️ 發現 ${results.summary.error_count} 個錯誤需要處理`
                )
                results.diagnostics.forEach((diagnostic) => {
                    if (diagnostic.status === 'error') {
                        console.error(
                            `❌ ${diagnostic.service}: ${diagnostic.message}`
                        )
                        if (diagnostic.fixSuggestions) {
                            console.log(
                                '💡 建議修復方案:',
                                diagnostic.fixSuggestions
                            )
                        }
                    }
                })
            }
        } catch (error) {
            console.error('進階測試失敗:', error)
        } finally {
            setIsTestingAdvanced(false)
        }
    }

    const runSatelliteTest = async () => {
        setIsTestingSatellites(true)
        try {
            console.log('🛰️ 開始衛星數據測試...')

            // 測試 1: 直接 API 調用
            console.log('測試 1: 直接 API 調用')
            const apiUrl = `${ApiRoutes.satelliteOps.getVisibleSatellites}?count=12&min_elevation_deg=5`
            const directResponse = await fetch(apiUrl)
            const directData = await directResponse.json()

            // 測試 2: 通過服務層調用
            console.log('測試 2: 通過服務層調用')
            const serviceData = await fetchRealSatelliteData()

            const results = {
                direct_api: {
                    success: directResponse.ok,
                    satellite_count: directData?.satellites?.length || 0,
                    data: directData,
                },
                service_layer: {
                    success: serviceData?.success || false,
                    satellite_count: serviceData?.results?.total_visible || 0,
                    data: serviceData,
                },
                timestamp: new Date().toISOString(),
            }

            setSatelliteResults(results)

            console.log('🔍 衛星數據測試結果:')
            console.log(
                `直接 API: ${results.direct_api.success ? '✅' : '❌'} - ${
                    results.direct_api.satellite_count
                } 顆衛星`
            )
            console.log(
                `服務層: ${results.service_layer.success ? '✅' : '❌'} - ${
                    results.service_layer.satellite_count
                } 顆衛星`
            )

            if (
                results.direct_api.satellite_count > 0 &&
                results.service_layer.satellite_count === 0
            ) {
                console.warn(
                    '⚠️ API 有數據但服務層無法獲取，可能是數據格式轉換問題'
                )
            } else if (results.service_layer.satellite_count > 0) {
                console.log('✅ 衛星數據服務正常工作')
            }
        } catch (error) {
            console.error('衛星測試失敗:', error)
            setSatelliteResults({
                direct_api: {
                    success: false,
                    satellite_count: 0,
                    error: String(error),
                },
                service_layer: {
                    success: false,
                    satellite_count: 0,
                    error: String(error),
                },
                timestamp: new Date().toISOString(),
            })
        } finally {
            setIsTestingSatellites(false)
        }
    }

    return (
        <div
            style={{
                padding: '20px',
                background: '#1a1a1a',
                color: '#fff',
                borderRadius: '8px',
                margin: '10px',
            }}
        >
            <h3>🔧 系統健康檢查工具</h3>

            <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
                <button
                    onClick={runBasicTest}
                    disabled={isTestingBasic}
                    style={{
                        padding: '10px 20px',
                        background: '#007acc',
                        color: '#fff',
                        border: 'none',
                        borderRadius: '4px',
                    }}
                >
                    {isTestingBasic ? '測試中...' : '基本系統測試'}
                </button>

                <button
                    onClick={runAdvancedTest}
                    disabled={isTestingAdvanced}
                    style={{
                        padding: '10px 20px',
                        background: '#28a745',
                        color: '#fff',
                        border: 'none',
                        borderRadius: '4px',
                    }}
                >
                    {isTestingAdvanced ? '診斷中...' : '進階系統診斷'}
                </button>

                <button
                    onClick={runSatelliteTest}
                    disabled={isTestingSatellites}
                    style={{
                        padding: '10px 20px',
                        background: '#ffc107',
                        color: '#000',
                        border: 'none',
                        borderRadius: '4px',
                    }}
                >
                    {isTestingSatellites ? '測試中...' : '衛星數據測試'}
                </button>
            </div>

            {basicResults && (
                <div
                    style={{
                        marginBottom: '20px',
                        padding: '10px',
                        background: '#2a2a2a',
                        borderRadius: '4px',
                    }}
                >
                    <h4>基本測試結果 (分數: {basicResults.overall_score})</h4>
                    <ul>
                        <li>
                            NetStack 核心同步:{' '}
                            {basicResults.netstack_core_sync.success
                                ? '✅'
                                : '❌'}
                        </li>
                        <li>
                            SimWorld 衛星:{' '}
                            {basicResults.simworld_satellites.success
                                ? '✅'
                                : '❌'}
                        </li>
                        <li>
                            真實連接:{' '}
                            {basicResults.real_connections.success
                                ? '✅'
                                : '❌'}
                        </li>
                        <li>
                            IEEE 算法:{' '}
                            {basicResults.ieee_algorithm.success ? '✅' : '❌'}
                        </li>
                    </ul>
                </div>
            )}

            {advancedResults && (
                <div
                    style={{
                        marginBottom: '20px',
                        padding: '10px',
                        background: '#2a2a2a',
                        borderRadius: '4px',
                    }}
                >
                    <h4>進階診斷結果 ({advancedResults.overall_health})</h4>
                    <p>
                        健康: {advancedResults.summary.healthy_count}, 警告:{' '}
                        {advancedResults.summary.warning_count}, 錯誤:{' '}
                        {advancedResults.summary.error_count}
                    </p>
                    {advancedResults.diagnostics.map((diag, index) => (
                        <div key={index} style={{ margin: '5px 0' }}>
                            {diag.status === 'healthy'
                                ? '✅'
                                : diag.status === 'warning'
                                ? '⚠️'
                                : '❌'}
                            {diag.service}: {diag.message}
                        </div>
                    ))}
                </div>
            )}

            {satelliteResults && (
                <div
                    style={{
                        marginBottom: '20px',
                        padding: '10px',
                        background: '#2a2a2a',
                        borderRadius: '4px',
                    }}
                >
                    <h4>衛星數據測試結果</h4>
                    <div>
                        <p>
                            <strong>直接 API:</strong>{' '}
                            {satelliteResults.direct_api.success ? '✅' : '❌'}{' '}
                            - {satelliteResults.direct_api.satellite_count}{' '}
                            顆衛星
                        </p>
                        <p>
                            <strong>服務層:</strong>{' '}
                            {satelliteResults.service_layer.success
                                ? '✅'
                                : '❌'}{' '}
                            - {satelliteResults.service_layer.satellite_count}{' '}
                            顆衛星
                        </p>
                        {satelliteResults.service_layer.satellite_count > 0 && (
                            <p style={{ color: '#4CAF50' }}>
                                ✅ 衛星數據應該已經修復，請刷新頁面查看效果
                            </p>
                        )}
                    </div>
                </div>
            )}

            <div style={{ fontSize: '12px', color: '#888', marginTop: '10px' }}>
                💡 提示：在瀏覽器開發者工具 Console 中可以看到詳細的測試日誌
            </div>
        </div>
    )
}

export default HealthCheckTest
