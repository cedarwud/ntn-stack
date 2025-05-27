import React, { useState, useEffect, useCallback, useRef } from 'react'
import { ViewerProps } from '../../types/viewer'
import { ApiRoutes } from '../../config/apiRoutes'

// Constellation & CFR 顯示組件
const CFRViewer: React.FC<ViewerProps> = ({
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

    const imageUrlRef = useRef<string | null>(null)
    // 使用ApiRoutes中定義的路徑
    const API_PATH = ApiRoutes.simulations.getCFRMap

    const updateTimestamp = useCallback(() => {
        const now = new Date()
        const timeString = now.toLocaleTimeString()
        onReportLastUpdateToNavbar?.(timeString)
    }, [onReportLastUpdateToNavbar])

    useEffect(() => {
        imageUrlRef.current = imageUrl
    }, [imageUrl])

    const loadCFRImage = useCallback(() => {
        setIsLoading(true)
        setError(null)

        // 添加timestamp參數防止緩存，並添加 scene 參數
        const apiUrl = `${API_PATH}?scene=${currentScene}&t=${new Date().getTime()}`

        fetch(apiUrl)
            .then((response) => {
                if (!response.ok) {
                    throw new Error(
                        `API 請求失敗: ${response.status} ${response.statusText}`
                    )
                }
                return response.blob()
            })
            .then((blob) => {
                // 檢查是否收到了有效的圖片數據
                if (blob.size === 0) {
                    throw new Error('接收到空的圖像數據')
                }

                if (imageUrlRef.current) {
                    URL.revokeObjectURL(imageUrlRef.current)
                }
                const url = URL.createObjectURL(blob)
                setImageUrl(url)
                setIsLoading(false)
                setRetryCount(0) // 重置重試次數
                updateTimestamp()
            })
            .catch((err) => {
                console.error('載入 Constellation & CFR 失敗:', err)

                // 處理可能的FileNotFoundError情況
                if (err.message && err.message.includes('404')) {
                    setError('圖像文件未找到: 後端可能正在生成圖像，請稍後重試')
                } else {
                    setError('無法載入 Constellation & CFR: ' + err.message)
                }

                setIsLoading(false)

                // 實現自動重試機制
                const newRetryCount = retryCount + 1
                setRetryCount(newRetryCount)

                if (newRetryCount < maxRetries) {
                    setTimeout(() => {
                        loadCFRImage()
                    }, 2000) // 2秒後重試
                }
            })
    }, [updateTimestamp, retryCount, currentScene])

    useEffect(() => {
        reportRefreshHandlerToNavbar(loadCFRImage)
    }, [loadCFRImage, reportRefreshHandlerToNavbar])

    useEffect(() => {
        reportIsLoadingToNavbar(isLoading)
    }, [isLoading, reportIsLoadingToNavbar])

    useEffect(() => {
        loadCFRImage()
        return () => {
            if (imageUrlRef.current) {
                URL.revokeObjectURL(imageUrlRef.current)
            }
        }
    }, [loadCFRImage])

    const handleRetryClick = () => {
        setRetryCount(0)
        loadCFRImage()
    }

    return (
        <div className="image-viewer">
            {isLoading && (
                <div className="loading">
                    正在即時運算並生成 Constellation & CFR...
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
            {imageUrl && (
                <img
                    src={imageUrl}
                    alt="Constellation & CFR Magnitude"
                    className="view-image"
                />
            )}
        </div>
    )
}

export default CFRViewer
