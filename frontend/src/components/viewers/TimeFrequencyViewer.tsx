import React, { useState, useEffect, useCallback, useRef } from 'react'
import { ViewerProps } from '../../types/viewer'

// Time-Frequency 顯示組件
const TimeFrequencyViewer: React.FC<ViewerProps> = ({
    onReportLastUpdateToNavbar,
    reportRefreshHandlerToNavbar,
    reportIsLoadingToNavbar,
}) => {
    const [isLoading, setIsLoading] = useState(true)
    const [imageUrl, setImageUrl] = useState<string | null>(null)
    const [error, setError] = useState<string | null>(null)

    const imageUrlRef = useRef<string | null>(null)
    const API_PATH = '/api/v1/sionna/channel-response-plots'

    const updateTimestamp = useCallback(() => {
        const now = new Date()
        const timeString = now.toLocaleTimeString()
        onReportLastUpdateToNavbar?.(timeString)
    }, [onReportLastUpdateToNavbar])

    useEffect(() => {
        imageUrlRef.current = imageUrl
    }, [imageUrl])

    const loadChannelResponseImage = useCallback(() => {
        setIsLoading(true)
        setError(null)
        fetch(API_PATH)
            .then((response) => {
                if (!response.ok) {
                    if (response.status === 400) {
                        return response.json().then((data) => {
                            throw new Error(
                                data.detail ||
                                    '需要至少一個活動的發射器和接收器'
                            )
                        })
                    }
                    throw new Error(
                        `API 請求失敗: ${response.status} ${response.statusText}`
                    )
                }
                return response.blob()
            })
            .then((blob) => {
                if (imageUrlRef.current) {
                    URL.revokeObjectURL(imageUrlRef.current)
                }
                const url = URL.createObjectURL(blob)
                setImageUrl(url)
                setIsLoading(false)
                updateTimestamp()
            })
            .catch((err) => {
                console.error('載入通道響應圖失敗:', err)
                setError('無法載入通道響應圖: ' + err.message)
                setIsLoading(false)
            })
    }, [updateTimestamp])

    useEffect(() => {
        reportRefreshHandlerToNavbar(loadChannelResponseImage)
    }, [loadChannelResponseImage, reportRefreshHandlerToNavbar])

    useEffect(() => {
        reportIsLoadingToNavbar(isLoading)
    }, [isLoading, reportIsLoadingToNavbar])

    useEffect(() => {
        loadChannelResponseImage()
        return () => {
            if (imageUrlRef.current) {
                URL.revokeObjectURL(imageUrlRef.current)
            }
        }
    }, [loadChannelResponseImage])

    return (
        <div className="image-viewer">
            {isLoading && (
                <div className="loading">
                    正在即時運算並生成 Time-Frequency...
                </div>
            )}
            {error && <div className="error">{error}</div>}
            {imageUrl && (
                <img
                    src={imageUrl}
                    alt="Time-Frequency"
                    className="view-image"
                />
            )}
        </div>
    )
}

export default TimeFrequencyViewer
