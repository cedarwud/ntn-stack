import { useState, useEffect, useRef, useCallback } from 'react';

const FALLBACK_IMAGE_PATH = '/rendered_images/scene_with_devices.png';

export function useSceneImageManager() {
    const [imageUrl, setImageUrl] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const prevImageUrlRef = useRef<string | null>(null);
    const [usingFallback, setUsingFallback] = useState<boolean>(false);
    const [retryCount, setRetryCount] = useState<number>(0);
    const [manualRetryMode, setManualRetryMode] = useState<boolean>(false);
    const [imageNaturalSize, setImageNaturalSize] = useState<{
        width: number;
        height: number;
    } | null>(null);

    const imageRefToAttach = useRef<HTMLImageElement>(null);

    const fetchImage = useCallback(
        async (signal: AbortSignal) => {
            const rtEndpoint = '/api/v1/sionna/scene-image-devices';
            setIsLoading(true);
            setError(null);
            setUsingFallback(false);

            if (prevImageUrlRef.current) {
                URL.revokeObjectURL(prevImageUrlRef.current);
                prevImageUrlRef.current = null;
            }

            const endpointWithCacheBuster = `${rtEndpoint}?t=${new Date().getTime()}`;
            let timeoutId: number | null = null;

            try {
                timeoutId = window.setTimeout(() => {
                    // console.warn(`Fetch image request timed out after 15s for ${endpointWithCacheBuster}`);
                }, 15000);

                const response = await fetch(endpointWithCacheBuster, {
                    signal,
                    cache: 'no-cache',
                    headers: { Pragma: 'no-cache', 'Cache-Control': 'no-cache' },
                });

                if (timeoutId !== null) window.clearTimeout(timeoutId);

                if (!response.ok) {
                    let errorDetail = `HTTP error! status: ${response.status}`;
                    try {
                        const errorJson = await response.json();
                        errorDetail = errorJson.detail || errorDetail;
                    } catch (jsonError) { /* Keep original HTTP error */ }
                    throw new Error(errorDetail);
                }

                try {
                    const imageBlob = await response.blob();
                    if (imageBlob.size === 0) {
                        throw new Error('Received empty image blob.');
                    }
                    const newImageUrl = URL.createObjectURL(imageBlob);
                    setImageUrl(newImageUrl);
                    prevImageUrlRef.current = newImageUrl;
                    setRetryCount(0);
                    setManualRetryMode(false);
                } catch (blobError) {
                    throw new Error(
                        `處理圖像時出錯: ${blobError instanceof Error ? blobError.message : String(blobError)}`
                    );
                }
            } catch (err) {
                if (timeoutId !== null) window.clearTimeout(timeoutId);
                const typedError = err as Error;
                if (typedError.name !== 'AbortError') {
                    // console.error(`Failed to fetch image from ${rtEndpoint}:`, typedError);
                    try {
                        const fallbackResponse = await fetch(FALLBACK_IMAGE_PATH, {
                            cache: 'no-cache',
                            headers: { Pragma: 'no-cache', 'Cache-Control': 'no-cache' },
                        });
                        if (fallbackResponse.ok) {
                            const fallbackBlob = await fallbackResponse.blob();
                            if (fallbackBlob.size > 0) {
                                const fallbackUrl = URL.createObjectURL(fallbackBlob);
                                setImageUrl(fallbackUrl);
                                prevImageUrlRef.current = fallbackUrl;
                                setUsingFallback(true);
                                setError(`使用備用圖像: ${typedError.message}`);
                            } else { throw new Error('備用圖像 blob 為空'); }
                        } else { throw new Error(`備用圖像請求失敗: ${fallbackResponse.status}`); }
                    } catch (fallbackErr) {
                        // console.error('Fallback image loading failed:', fallbackErr);
                        setImageUrl(FALLBACK_IMAGE_PATH); // Last resort
                        setUsingFallback(true);
                        setError(`圖像載入失敗: ${typedError.message}`);
                    }
                } else {
                    // console.log('Fetch aborted, ignoring error.');
                }
                
                const currentRetry = retryCount + 1;
                setRetryCount(currentRetry);
                if (currentRetry >= 3) {
                    setManualRetryMode(true);
                } else {
                    // console.log(`自動重試 (${currentRetry}/3)...`);
                    setTimeout(() => {
                         if (!signal.aborted) fetchImage(new AbortController().signal);
                    }, 5000);
                }
            } finally {
                if (timeoutId !== null) window.clearTimeout(timeoutId);
                setIsLoading(false);
            }
        },
        [retryCount]
    );

    const handleImageLoad = useCallback(() => {
        if (imageRefToAttach.current) {
            setImageNaturalSize({
                width: imageRefToAttach.current.naturalWidth,
                height: imageRefToAttach.current.naturalHeight,
            });
        }
        setIsLoading(false);
        if (!usingFallback) {
            setError(null);
        }
    }, [usingFallback]);

    const handleImageError = useCallback(
        (e: React.SyntheticEvent<HTMLImageElement, Event>) => {
            // console.error(`Image element failed to load src: ${imageUrl}`, e);
            if (usingFallback || imageUrl === FALLBACK_IMAGE_PATH) {
                setError(`備用圖片也無法載入，請檢查網絡連接`);
            } else {
                setImageUrl(FALLBACK_IMAGE_PATH);
                setUsingFallback(true);
                setError(`使用最後一次成功的圖像 (無法連接後端服務)`);
            }
            setIsLoading(false);
        },
        [imageUrl, usingFallback]
    );

    useEffect(() => {
        const controller = new AbortController();
        fetchImage(controller.signal);
        return () => {
            controller.abort();
            if (prevImageUrlRef.current) {
                URL.revokeObjectURL(prevImageUrlRef.current);
                prevImageUrlRef.current = null;
            }
        };
    }, [fetchImage]);

    return {
        imageUrl,
        imageRefToAttach,
        isLoading,
        error,
        usingFallback,
        manualRetryMode,
        imageNaturalSize,
        retryLoad: () => fetchImage(new AbortController().signal),
        handleImageLoad,
        handleImageError,
    };
} 