import React, { useState, useEffect, useCallback, useRef } from 'react'
import { ViewerProps } from '../../types/viewer'

// Constellation & CFR 顯示組件
const CFRViewer: React.FC<ViewerProps> = ({
    onReportLastUpdateToNavbar,
    reportRefreshHandlerToNavbar,
    reportIsLoadingToNavbar,
}) => {
    const [isLoading, setIsLoading] = useState(true)
    const [imageUrl, setImageUrl] = useState<string | null>(null)
    const [error, setError] = useState<string | null>(null)

    const imageUrlRef = useRef<string | null>(null)
    const API_PATH = '/api/v1/sionna/cfr-plot'

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
        fetch(API_PATH)
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
                console.error('載入 Constellation & CFR 失敗:', err)
                setError('無法載入 Constellation & CFR: ' + err.message)
                setIsLoading(false)
            })
    }, [updateTimestamp])

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

    return (
        <div className="image-viewer">
            {isLoading && (
                <div className="loading">
                    正在即時運算並生成 Constellation & CFR...
                </div>
            )}
            {error && <div className="error">{error}</div>}
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
