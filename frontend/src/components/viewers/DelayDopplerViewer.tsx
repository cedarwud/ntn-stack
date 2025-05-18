import React, { useState, useEffect, useCallback, useRef } from 'react'
import { ViewerProps } from '../../types/viewer'

// Delay-Doppler 顯示組件
const DelayDopplerViewer: React.FC<ViewerProps> = ({
    onReportLastUpdateToNavbar,
    reportRefreshHandlerToNavbar,
    reportIsLoadingToNavbar,
}) => {
    const [isLoading, setIsLoading] = useState(true)
    const [imageUrl, setImageUrl] = useState<string | null>(null)
    const [error, setError] = useState<string | null>(null)

    const imageUrlRef = useRef<string | null>(null)

    const updateTimestamp = useCallback(() => {
        const now = new Date()
        const timeString = now.toLocaleTimeString()
        onReportLastUpdateToNavbar?.(timeString)
    }, [onReportLastUpdateToNavbar])

    useEffect(() => {
        imageUrlRef.current = imageUrl
    }, [imageUrl])

    const loadDopplerImage = useCallback(() => {
        setIsLoading(true)
        setError(null)
        fetch('/api/v1/sionna/doppler-plots')
            .then((response) => {
                if (!response.ok) {
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
                console.error('載入延遲多普勒圖失敗:', err)
                setError('無法載入延遲多普勒圖: ' + err.message)
                setIsLoading(false)
            })
    }, [updateTimestamp])

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

    return (
        <div className="image-viewer">
            {isLoading && (
                <div className="loading">
                    正在即時運算並生成 Delay-Doppler...
                </div>
            )}
            {error && <div className="error">{error}</div>}
            <div className="delay-doppler-container">
                {imageUrl && (
                    <div className="image-item doppler-image-v2">
                        <img
                            src={imageUrl}
                            alt="Delay-Doppler Plot"
                            className="view-image doppler-image-v2"
                        />
                    </div>
                )}
            </div>
        </div>
    )
}

export default DelayDopplerViewer
