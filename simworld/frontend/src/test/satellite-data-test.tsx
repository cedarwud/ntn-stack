/**
 * 衛星數據測試組件
 * 用於驗證衛星數據是否正確載入
 */
import React, { useState, useEffect } from 'react'
import { ApiRoutes } from '../config/apiRoutes'
import { VisibleSatelliteInfo } from '../types/satellite'

export const SatelliteDataTest: React.FC = () => {
    const [satellites, setSatellites] = useState<VisibleSatelliteInfo[]>([])
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const fetchSatellites = async () => {
        setLoading(true)
        setError(null)
        try {
            const apiUrl = `${ApiRoutes.satelliteOps.getVisibleSatellites}?count=12&min_elevation_deg=5`
            const response = await fetch(apiUrl)

            if (!response.ok) {
                throw new Error(
                    `HTTP ${response.status}: ${response.statusText}`
                )
            }

            const data = await response.json()
            setSatellites(data.satellites || [])

            console.log('🛰️ 衛星數據測試結果:', {
                apiUrl,
                totalSatellites: data.satellites?.length || 0,
                satellites: data.satellites,
            })
        } catch (err) {
            setError(String(err))
            console.error('❌ 衛星數據載入失敗:', err)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchSatellites()
    }, [])

    return (
        <div
            style={{
                padding: '20px',
                backgroundColor: 'rgba(0,0,0,0.8)',
                color: 'white',
                borderRadius: '8px',
                margin: '20px',
            }}
        >
            <h3>🛰️ 衛星數據測試面板</h3>

            <div style={{ marginBottom: '15px' }}>
                <button
                    onClick={fetchSatellites}
                    disabled={loading}
                    style={{
                        padding: '8px 16px',
                        backgroundColor: '#007bff',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: loading ? 'not-allowed' : 'pointer',
                    }}
                >
                    {loading ? '載入中...' : '重新載入衛星數據'}
                </button>
            </div>

            {error && (
                <div style={{ color: '#ff6b6b', marginBottom: '15px' }}>
                    ❌ 錯誤: {error}
                </div>
            )}

            <div style={{ marginBottom: '15px' }}>
                <strong>狀態:</strong>{' '}
                {loading ? '載入中' : `已載入 ${satellites.length} 顆衛星`}
            </div>

            {satellites.length > 0 && (
                <div>
                    <h4>可見衛星列表:</h4>
                    <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                        {satellites.map((sat, index) => {
                            const cleanName = sat.name
                                .replace(' [DTC]', '')
                                .replace('[DTC]', '')
                                .trim()
                            return (
                                <div
                                    key={sat.norad_id}
                                    style={{
                                        padding: '8px',
                                        margin: '4px 0',
                                        backgroundColor:
                                            'rgba(255,255,255,0.1)',
                                        borderRadius: '4px',
                                        fontSize: '14px',
                                    }}
                                >
                                    <div>
                                        <strong>{cleanName}</strong>
                                    </div>
                                    <div>
                                        ID: {sat.norad_id} | 仰角:{' '}
                                        {sat.elevation_deg.toFixed(1)}° | 距離:{' '}
                                        {sat.distance_km.toFixed(0)} km
                                    </div>
                                </div>
                            )
                        })}
                    </div>
                </div>
            )}
        </div>
    )
}
