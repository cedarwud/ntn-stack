import { useState, useRef, useCallback } from 'react'

export interface UseImageLoaderResult {
    imageUrl: string | null
    isLoading: boolean
    error: string | null
    fetchImage: (signal: AbortSignal) => Promise<void>
    usingFallback: boolean
    retryCount: number
    manualRetryMode: boolean
    setManualRetryMode: (v: boolean) => void
    setRetryCount: (v: number) => void
    setImageUrl: (v: string | null) => void
}

export function useImageLoader(rtEndpoint: string, fallbackPath: string): UseImageLoaderResult {
    const [imageUrl, setImageUrl] = useState<string | null>(null)
    const [isLoading, setIsLoading] = useState<boolean>(true)
    const [error, setError] = useState<string | null>(null)
    const prevImageUrlRef = useRef<string | null>(null)
    const [usingFallback, setUsingFallback] = useState<boolean>(false)
    const [retryCount, setRetryCount] = useState<number>(0)
    const [manualRetryMode, setManualRetryMode] = useState<boolean>(false)

    const fetchImage = useCallback(
        async (signal: AbortSignal) => {
            setIsLoading(true)
            setError(null)
            setUsingFallback(false)
            if (prevImageUrlRef.current) {
                URL.revokeObjectURL(prevImageUrlRef.current)
                prevImageUrlRef.current = null
            }
            const endpointWithCacheBuster = `${rtEndpoint}?t=${new Date().getTime()}`
            let timeoutId: number | null = null
            try {
                timeoutId = window.setTimeout(() => {}, 15000)
                const response = await fetch(endpointWithCacheBuster, {
                    signal,
                    cache: 'no-cache',
                    headers: {
                        Pragma: 'no-cache',
                        'Cache-Control': 'no-cache',
                    },
                })
                if (timeoutId !== null) window.clearTimeout(timeoutId)
                if (!response.ok) {
                    let errorDetail = `HTTP error! status: ${response.status}`
                    try {
                        const errorJson = await response.json()
                        errorDetail = errorJson.detail || errorDetail
                    } catch {}
                    throw new Error(errorDetail)
                }
                try {
                    const imageBlob = await response.blob()
                    if (imageBlob.size === 0) {
                        throw new Error('Received empty image blob.')
                    }
                    const newImageUrl = URL.createObjectURL(imageBlob)
                    setImageUrl(newImageUrl)
                    prevImageUrlRef.current = newImageUrl
                    setRetryCount(0)
                    setManualRetryMode(false)
                } catch (blobError) {
                    throw new Error(
                        `處理圖像時出錯: ${blobError instanceof Error ? blobError.message : String(blobError)}`
                    )
                }
            } catch (error) {
                if (timeoutId !== null) window.clearTimeout(timeoutId)
                if ((error as Error).name !== 'AbortError') {
                    try {
                        const fallbackResponse = await fetch(fallbackPath, {
                            cache: 'no-cache',
                            headers: {
                                Pragma: 'no-cache',
                                'Cache-Control': 'no-cache',
                            },
                        })
                        if (fallbackResponse.ok) {
                            const fallbackBlob = await fallbackResponse.blob()
                            if (fallbackBlob.size > 0) {
                                const fallbackUrl = URL.createObjectURL(fallbackBlob)
                                setImageUrl(fallbackUrl)
                                prevImageUrlRef.current = fallbackUrl
                                setUsingFallback(true)
                                setError(
                                    `使用備用圖像: ${
                                        error instanceof Error ? error.message : '未知錯誤'
                                    }`
                                )
                            } else {
                                throw new Error('備用圖像 blob 為空')
                            }
                        } else {
                            throw new Error(`備用圖像請求失敗: ${fallbackResponse.status}`)
                        }
                    } catch (fallbackError) {
                        setImageUrl(fallbackPath)
                        setUsingFallback(true)
                        setError(
                            `圖像載入失敗: ${
                                error instanceof Error ? error.message : '未知錯誤'
                            }`
                        )
                    }
                }
                const currentRetryCount = retryCount + 1
                setRetryCount(currentRetryCount)
                if (currentRetryCount >= 3) {
                    setManualRetryMode(true)
                } else {
                    setTimeout(() => {
                        fetchImage(new AbortController().signal)
                    }, 5000)
                }
            } finally {
                if (timeoutId !== null) window.clearTimeout(timeoutId)
                setIsLoading(false)
            }
        }, [rtEndpoint, fallbackPath, retryCount])

    return {
        imageUrl,
        isLoading,
        error,
        fetchImage,
        usingFallback,
        retryCount,
        manualRetryMode,
        setManualRetryMode,
        setRetryCount,
        setImageUrl,
    }
} 