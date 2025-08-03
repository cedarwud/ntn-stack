import React, { useState, useCallback } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '../../ui/card'
import { Alert } from '../../ui/alert'
import { ConstellationSelector } from './ConstellationSelector'
import { TimelineControl } from './TimelineControl'
import { SatelliteAnimationViewer } from './SatelliteAnimationViewer'

export const SatelliteAnalysisPage: React.FC = () => {
    const [selectedConstellation, setSelectedConstellation] =
        useState('starlink')
    const [currentTimestamp, setCurrentTimestamp] = useState(Date.now())
    const [playbackSpeed, setPlaybackSpeed] = useState(1)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const handleConstellationChange = useCallback((constellation: string) => {
        setLoading(true)
        setError(null)
        setSelectedConstellation(constellation)

        // 模擬切換延遲
        setTimeout(() => {
            setLoading(false)
        }, 800)
    }, [])

    const handleTimeChange = useCallback((timestamp: number) => {
        setCurrentTimestamp(timestamp)
        setError(null)
    }, [])

    const handlePlaybackSpeedChange = useCallback((speed: number) => {
        setPlaybackSpeed(speed)
    }, [])

    const _handleError = useCallback((errorMessage: string) => {
        setError(errorMessage)
        setLoading(false)
    }, [])

    return (
        <div className="satellite-analysis-page p-6 min-h-screen bg-gray-50">
            <div className="max-w-7xl mx-auto">
                {/* 頁面標題 */}
                <div className="mb-6">
                    <h1 className="text-3xl font-bold text-gray-800 mb-2">
                        🛰️ LEO 衛星星座歷史數據分析平台
                    </h1>
                    <p className="text-gray-600">
                        基於真實 TLE 數據的衛星軌道計算與 Handover
                        事件分析系統，支援 Starlink 和 OneWeb 星座研究
                    </p>
                </div>

                {/* 錯誤提示 */}
                {error && (
                    <Alert className="mb-4 bg-red-50 border-red-200 text-red-800">
                        <div>
                            <strong>系統錯誤:</strong> {error}
                            <button
                                onClick={() => setError(null)}
                                className="ml-2 text-red-600 hover:text-red-800"
                            >
                                [關閉]
                            </button>
                        </div>
                    </Alert>
                )}

                {/* 載入狀態 */}
                {loading && (
                    <div className="fixed inset-0 bg-black bg-opacity-20 flex items-center justify-center z-50">
                        <div className="bg-white p-6 rounded-lg shadow-lg flex items-center space-x-3">
                            <div className="animate-spin h-6 w-6 border-2 border-blue-600 border-t-transparent rounded-full"></div>
                            <span className="text-gray-700">
                                切換星座系統中...
                            </span>
                        </div>
                    </div>
                )}

                <div className="space-y-6">
                    {/* 控制面板區域 */}
                    <Card className="shadow-sm">
                        <CardHeader>
                            <CardTitle>🎮 分析控制台</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                                <div className="lg:col-span-1">
                                    <ConstellationSelector
                                        value={selectedConstellation}
                                        onChange={handleConstellationChange}
                                        disabled={loading}
                                        showComparison={true}
                                    />
                                </div>
                                <div className="lg:col-span-2">
                                    <TimelineControl
                                        constellation={selectedConstellation}
                                        onTimeChange={handleTimeChange}
                                        onPlaybackSpeedChange={
                                            handlePlaybackSpeedChange
                                        }
                                        disabled={loading}
                                        showStatistics={true}
                                    />
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* 數據視覺化區域 */}
                    <div
                        className={
                            loading ? 'opacity-50 pointer-events-none' : ''
                        }
                    >
                        <SatelliteAnimationViewer
                            currentTime={new Date(currentTimestamp)}
                            constellation={selectedConstellation}
                            playbackSpeed={playbackSpeed}
                        />
                    </div>

                    {/* 系統狀態和說明 */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* 系統狀態 */}
                        <Card className="shadow-sm">
                            <CardHeader>
                                <CardTitle>📊 系統狀態</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-3">
                                    <div className="flex justify-between items-center py-2 border-b border-gray-100">
                                        <span className="text-gray-600">
                                            當前星座:
                                        </span>
                                        <span className="font-semibold text-blue-600">
                                            {selectedConstellation ===
                                            'starlink'
                                                ? 'Starlink'
                                                : 'OneWeb'}
                                        </span>
                                    </div>
                                    <div className="flex justify-between items-center py-2 border-b border-gray-100">
                                        <span className="text-gray-600">
                                            分析時間:
                                        </span>
                                        <span className="font-mono text-sm text-gray-800">
                                            {new Date(
                                                currentTimestamp
                                            ).toLocaleString('zh-TW')}
                                        </span>
                                    </div>
                                    <div className="flex justify-between items-center py-2 border-b border-gray-100">
                                        <span className="text-gray-600">
                                            播放速度:
                                        </span>
                                        <span className="font-semibold text-green-600">
                                            {playbackSpeed}x
                                        </span>
                                    </div>
                                    <div className="flex justify-between items-center py-2">
                                        <span className="text-gray-600">
                                            系統狀態:
                                        </span>
                                        <span
                                            className={`font-semibold ${
                                                loading
                                                    ? 'text-orange-500'
                                                    : 'text-green-500'
                                            }`}
                                        >
                                            {loading ? '載入中' : '運行正常'}
                                        </span>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>

                        {/* 使用說明 */}
                        <Card className="shadow-sm">
                            <CardHeader>
                                <CardTitle>📚 使用說明</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="text-sm text-gray-600 space-y-2">
                                    <div className="flex items-start space-x-2">
                                        <span className="font-semibold text-blue-600 w-20 flex-shrink-0">
                                            星座選擇:
                                        </span>
                                        <span>
                                            切換不同 LEO 衛星星座系統進行分析
                                        </span>
                                    </div>
                                    <div className="flex items-start space-x-2">
                                        <span className="font-semibold text-green-600 w-20 flex-shrink-0">
                                            時間控制:
                                        </span>
                                        <span>
                                            支援播放、暫停、倍速和跳轉功能
                                        </span>
                                    </div>
                                    <div className="flex items-start space-x-2">
                                        <span className="font-semibold text-purple-600 w-20 flex-shrink-0">
                                            數據展示:
                                        </span>
                                        <span>
                                            即時顯示衛星位置和 Handover 事件
                                        </span>
                                    </div>
                                    <div className="flex items-start space-x-2">
                                        <span className="font-semibold text-orange-600 w-20 flex-shrink-0">
                                            3GPP符合:
                                        </span>
                                        <span>
                                            自動檢查是否符合 NTN 標準要求
                                        </span>
                                    </div>
                                    <div className="flex items-start space-x-2">
                                        <span className="font-semibold text-red-600 w-20 flex-shrink-0">
                                            研究用途:
                                        </span>
                                        <span>
                                            適用於 LEO 衛星 Handover 論文研究
                                        </span>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                </div>

                {/* 頁腳信息 */}
                <div className="mt-12 text-center text-sm text-gray-500 border-t pt-6">
                    <div className="space-y-1">
                        <div className="font-medium">
                            NTN Stack - LEO 衛星星座分析平台
                        </div>
                        <div className="flex justify-center items-center space-x-4 text-xs">
                            <span>基於真實 TLE 數據</span>
                            <span>•</span>
                            <span>符合 3GPP NTN 標準</span>
                            <span>•</span>
                            <span>支援學術研究</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
