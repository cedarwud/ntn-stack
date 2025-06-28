import { useState, useEffect, useCallback, useRef } from 'react'
import { ViewerProps } from '../../../../types/viewer'
import { ApiRoutes } from '../../../../config/apiRoutes'

// Delay-Doppler 顯示組件
const DelayDopplerViewer: React.FC<ViewerProps> = ({
    onReportLastUpdateToNavbar,
    reportRefreshHandlerToNavbar,
    reportIsLoadingToNavbar,
    currentScene,
}) => {
    const [isLoading, setIsLoading] = useState(true)
    const [imageUrl, setImageUrl] = useState<string | null>(null)
    const [error, setError] = useState<string | null>(null)
    const [retryCount, setRetryCount] = useState(0)
    const maxRetries = 3

    // 高級配置選項（固定值）
    const maxDelayNs = 500
    const maxDopplerHz = 1000
    const resolutionLevel = 'medium'
    const enablePhaseInfo = false

    const imageUrlRef = useRef<string | null>(null)
    // 使用ApiRoutes中定義的路徑
    const API_PATH = ApiRoutes.simulations.getDopplerMap

    const updateTimestamp = useCallback(() => {
        const now = new Date()
        const timeString = now.toLocaleTimeString()
        onReportLastUpdateToNavbar?.(timeString)
    }, [onReportLastUpdateToNavbar])

    useEffect(() => {
        imageUrlRef.current = imageUrl
    }, [imageUrl])

    const loadDopplerImage = useCallback(async () => {
        setIsLoading(true)
        setError(null)

        try {
            const timestamp = new Date().getTime()
            const resolutionMap = { low: 64, medium: 128, high: 256 }
            const apiUrl = `${API_PATH}?scene=${currentScene}&max_delay_ns=${maxDelayNs}&max_doppler_hz=${maxDopplerHz}&resolution=${resolutionMap[resolutionLevel]}&enable_phase=${enablePhaseInfo}&t=${timestamp}`

            const response = await fetch(apiUrl)

            if (response.ok) {
                const blob = await response.blob()
                if (blob.size === 0) {
                    throw new Error('接收到空的圖像數據')
                }

                if (imageUrlRef.current) {
                    URL.revokeObjectURL(imageUrlRef.current)
                }
                const url = URL.createObjectURL(blob)
                setImageUrl(url)
                setRetryCount(0)
                setIsLoading(false)
                updateTimestamp()
            } else {
                throw new Error(
                    `API 請求失敗: ${response.status} ${response.statusText}`
                )
            }
        } catch (err: unknown) {
            console.error('載入延遲多普勒圖失敗:', err)
            handleLoadError(err)
        }
    }, [
        API_PATH,
        currentScene,
        updateTimestamp,
        maxDelayNs,
        maxDopplerHz,
        resolutionLevel,
        enablePhaseInfo,
        handleLoadError,
    ])

    // 錯誤處理函數
    const handleLoadError = useCallback(
        (err: unknown) => {
            if (err instanceof Error && err.message.includes('404')) {
                setError('圖像文件未找到: 後端可能正在生成圖像，請稍後重試')
            } else {
                setError('無法載入延遲多普勒圖: ' + (err instanceof Error ? err.message : String(err)))
            }

            setIsLoading(false)

            const newRetryCount = retryCount + 1
            setRetryCount(newRetryCount)

            if (newRetryCount < maxRetries) {
                setTimeout(() => {
                    loadDopplerImage()
                }, 2000)
            }
        },
        [retryCount, maxRetries, loadDopplerImage]
    )

    useEffect(() => {
        reportRefreshHandlerToNavbar(loadDopplerImage)
    }, [loadDopplerImage, reportRefreshHandlerToNavbar])

    useEffect(() => {
        reportIsLoadingToNavbar(isLoading)
    }, [isLoading, reportIsLoadingToNavbar])

    useEffect(() => {
        loadDopplerImage()
        return () => {
            if (imageUrlRef.current) {
                URL.revokeObjectURL(imageUrlRef.current)
            }
        }
    }, [loadDopplerImage])

    const handleRetryClick = () => {
        setRetryCount(0)
        loadDopplerImage()
    }

    return (
        <div className="image-viewer delay-doppler-container">
            {/* 載入和錯誤狀態 */}
            {isLoading && (
                <div className="loading">
                    正在即時運算並生成 Delay-Doppler...
                </div>
            )}

            {error && (
                <div className="error">
                    {error}
                    <button
                        onClick={handleRetryClick}
                        style={{
                            marginLeft: '10px',
                            padding: '5px 10px',
                            background: '#4285f4',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                        }}
                    >
                        重試
                    </button>
                </div>
            )}

            {/* Delay-Doppler 圖像顯示 */}
            <div className="delay-doppler-image-container">
                {imageUrl && (
                    <div className="image-item doppler-image-v2">
                        <img
                            src={imageUrl}
                            alt="Delay-Doppler Plot"
                            className="view-image doppler-image-v2"
                            style={{
                                maxWidth: '100%',
                                height: 'auto',
                                border: '1px solid #ddd',
                            }}
                        />
                    </div>
                )}
            </div>
        </div>
    )
}

export default DelayDopplerViewer
