import React, { useState, useEffect, useCallback, useRef } from 'react'
import { ViewerProps } from '../../types/viewer'

// SINR Map 顯示組件
const SINRViewer: React.FC<ViewerProps> = ({
    onReportLastUpdateToNavbar,
    reportRefreshHandlerToNavbar,
    reportIsLoadingToNavbar,
}) => {
    const [isLoading, setIsLoading] = useState(true)
    const [imageUrl, setImageUrl] = useState<string | null>(null)
    const [error, setError] = useState<string | null>(null)
    const [sinrVmin, setSinrVmin] = useState<number>(-40)
    const [sinrVmax, setSinrVmax] = useState<number>(0)
    const [cellSize, setCellSize] = useState<number>(1.0)
    const [samplesPerTx, setSamplesPerTx] = useState<number>(10 ** 7)

    const imageUrlRef = useRef<string | null>(null)
    const API_PATH = '/api/v1/sionna/sinr-map'

    const updateTimestamp = useCallback(() => {
        const now = new Date()
        const timeString = now.toLocaleTimeString()
        onReportLastUpdateToNavbar?.(timeString)
    }, [onReportLastUpdateToNavbar])

    useEffect(() => {
        imageUrlRef.current = imageUrl
    }, [imageUrl])

    const loadSINRMapImage = useCallback(() => {
        setIsLoading(true)
        setError(null)
        const apiUrl = `${API_PATH}?sinr_vmin=${sinrVmin}&sinr_vmax=${sinrVmax}&cell_size=${cellSize}&samples_per_tx=${samplesPerTx}`
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
                if (imageUrlRef.current) {
                    URL.revokeObjectURL(imageUrlRef.current)
                }
                const url = URL.createObjectURL(blob)
                setImageUrl(url)
                setIsLoading(false)
                updateTimestamp()
            })
            .catch((err) => {
                console.error('載入 SINR Map 失敗:', err)
                setError('無法載入 SINR Map: ' + err.message)
                setIsLoading(false)
            })
    }, [sinrVmin, sinrVmax, cellSize, samplesPerTx, updateTimestamp])

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

    const handleSinrVminChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setSinrVmin(Number(e.target.value))
    }
    const handleSinrVmaxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setSinrVmax(Number(e.target.value))
    }
    const handleCellSizeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setCellSize(Number(e.target.value))
    }
    const handleSamplesChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        setSamplesPerTx(Number(e.target.value))
    }

    return (
        <div className="image-viewer sinr-image-container">
            {isLoading && (
                <div className="loading">正在即時運算並生成 SINR Map...</div>
            )}
            {error && <div className="error">{error}</div>}
            {imageUrl && (
                <img
                    src={imageUrl}
                    alt="SINR Map"
                    className="view-image sinr-view-image"
                />
            )}
        </div>
    )
}

export default SINRViewer
