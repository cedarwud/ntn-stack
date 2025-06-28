import { useState, useEffect, useCallback, useRef } from 'react'
import { ViewerProps } from '../../../../types/viewer'
import { ApiRoutes } from '../../../../config/apiRoutes'

// SINR Map 顯示組件
const SINRViewer: React.FC<ViewerProps> = ({
    onReportLastUpdateToNavbar,
    reportRefreshHandlerToNavbar,
    reportIsLoadingToNavbar,
    currentScene,
}) => {
    const [isLoading, setIsLoading] = useState(true)
    const [imageUrl, setImageUrl] = useState<string | null>(null)
    const [error, setError] = useState<string | null>(null)
    const sinrVmin = -40
    const sinrVmax = 0
    const cellSize = 1.0
    const samplesPerTx = 10 ** 7
    const [retryCount, setRetryCount] = useState(0)
    const maxRetries = 3

    const imageUrlRef = useRef<string | null>(null)
    const API_PATH = ApiRoutes.simulations.getSINRMap

    const updateTimestamp = useCallback(() => {
        const now = new Date()
        const timeString = now.toLocaleTimeString()
        onReportLastUpdateToNavbar?.(timeString)
    }, [onReportLastUpdateToNavbar])

    useEffect(() => {
        imageUrlRef.current = imageUrl
    }, [imageUrl])

    const loadSINRMapImageRef = useRef<() => void>()

    const handleLoadError = useCallback(
        (err: Error | unknown) => {
            if (err instanceof Error && err.message && err.message.includes('404')) {
                setError('圖像文件未找到: 後端可能正在生成圖像，請稍後重試')
            } else if (err instanceof Error) {
                setError('無法載入 SINR Map: ' + err.message)
            } else {
                setError('無法載入 SINR Map: 未知錯誤')
            }

            setIsLoading(false)

            const newRetryCount = retryCount + 1
            setRetryCount(newRetryCount)

            if (newRetryCount < maxRetries) {
                setTimeout(() => {
                    loadSINRMapImageRef.current?.()
                }, 2000)
            }
        },
        [retryCount, maxRetries]
    )

    const loadSINRMapImage = useCallback(async () => {
        setIsLoading(true)
        setError(null)

        try {
            const timestamp = new Date().getTime()
            const apiUrl = `${API_PATH}?scene=${currentScene}&sinr_vmin=${sinrVmin}&sinr_vmax=${sinrVmax}&cell_size=${cellSize}&samples_per_tx=${samplesPerTx}&t=${timestamp}`

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
            console.error('載入 SINR Map 失敗:', err)
            handleLoadError(err as Error)
        }
    }, [
        currentScene,
        sinrVmin,
        sinrVmax,
        cellSize,
        samplesPerTx,
        updateTimestamp,
        API_PATH,
        handleLoadError,
    ])

    useEffect(() => {
        loadSINRMapImageRef.current = loadSINRMapImage
    }, [loadSINRMapImage])

    useEffect(() => {
        reportRefreshHandlerToNavbar(loadSINRMapImage)
    }, [loadSINRMapImage, reportRefreshHandlerToNavbar])

    useEffect(() => {
        reportIsLoadingToNavbar(isLoading)
    }, [isLoading, reportIsLoadingToNavbar])

    useEffect(() => {
        loadSINRMapImage()
        return () => {
            if (imageUrlRef.current) {
                URL.revokeObjectURL(imageUrlRef.current)
            }
        }
    }, [loadSINRMapImage])

    const handleRetryClick = () => {
        setRetryCount(0)
        loadSINRMapImage()
    }

    return (
        <div className="image-viewer sinr-image-container">
            {/* 載入和錯誤狀態 */}
            {isLoading && (
                <div className="loading">正在即時運算並生成 SINR Map...</div>
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

            {/* SINR 圖像顯示 */}
            {imageUrl && (
                <div className="sinr-image-display">
                    <img
                        src={imageUrl}
                        alt="SINR Map"
                        className="view-image sinr-view-image"
                        style={{
                            maxWidth: '100%',
                            height: 'auto',
                            border: '1px solid #ddd',
                        }}
                    />
                </div>
            )}
        </div>
    )
}

export default SINRViewer
