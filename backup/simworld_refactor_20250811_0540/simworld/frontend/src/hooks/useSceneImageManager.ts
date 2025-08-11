import { useState, useEffect, useRef, useCallback } from 'react';
import { ApiRoutes } from '../config/apiRoutes';
import { getBackendSceneName, getSceneTextureName } from '../utils/sceneUtils';

const FALLBACK_IMAGE_PATH = '/rendered_images/scene_with_devices.png';

export function useSceneImageManager(sceneName?: string) {
    const [imageUrl, setImageUrl] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const prevImageUrlRef = useRef<string | null>(null);
    const [usingFallback, setUsingFallback] = useState<boolean>(false);
    const [, setRetryCount] = useState<number>(0);
    const [manualRetryMode, setManualRetryMode] = useState<boolean>(false);
    const [imageNaturalSize, setImageNaturalSize] = useState<{
        width: number;
        height: number;
    } | null>(null);

    const imageRefToAttach = useRef<HTMLImageElement>(null);
    const isActiveRef = useRef<boolean>(true);

    const fetchImage = useCallback(
        async (signal: AbortSignal) => {
            // Use scene-specific texture if sceneName is provided
            const rtEndpoint = sceneName 
                ? ApiRoutes.scenes.getSceneTexture(getBackendSceneName(sceneName), getSceneTextureName(sceneName))
                : ApiRoutes.simulations.getSceneImage;
            
            if (isActiveRef.current) {
                setIsLoading(true);
                setError(null);
                setUsingFallback(false);
            }

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
                    } catch { /* Keep original HTTP error */ }
                    throw new Error(errorDetail);
                }

                try {
                    const imageBlob = await response.blob();
                    if (imageBlob.size === 0) {
                        throw new Error('Received empty image blob.');
                    }
                    if (isActiveRef.current) {
                        const newImageUrl = URL.createObjectURL(imageBlob);
                        setImageUrl(newImageUrl);
                        prevImageUrlRef.current = newImageUrl;
                        setRetryCount(0);
                        setManualRetryMode(false);
                    }
                } catch (blobError) {
                    throw new Error(
                        `處理圖像時出錯: ${blobError instanceof Error ? blobError.message : String(blobError)}`
                    );
                }
            } catch (error: unknown) {
                // 只有當 signal 沒有被 abort 時才需要處理錯誤
                // 如果是 AbortError 且是因為組件卸載，這是正常的行為
                if (error.name === 'AbortError') {
                    // 組件卸載導致的請求中止是正常行為，使用 debug 級別日誌
                    console.debug('圖像請求已中止（組件卸載）:', error.message || '組件已卸載');
                } else {
                    // 檢查是否是組件卸載錯誤 - 更全面的檢測
                    const errorString = String(error);
                    const isUnmountError = 
                        (error.message && error.message.includes('Component unmounted')) ||
                        (error.name && error.name.includes('unmount')) ||
                        errorString.includes('Component unmounted') ||
                        errorString.includes('unmount') ||
                        !isActiveRef.current; // 如果組件已經不活躍，就認為是卸載錯誤
                    
                    // 只有當組件仍然活躍且不是卸載錯誤時才記錄錯誤
                    if (isActiveRef.current && !isUnmountError) {
                        console.error('Error fetching image:', error);
                    }
                    // 對於卸載錯誤，完全靜默處理，不記錄任何日誌
                    
                    if (timeoutId !== null) window.clearTimeout(timeoutId);

                    if (!signal.aborted && isActiveRef.current && !isUnmountError) {
                        setError('Error loading image: ' + (error instanceof Error ? error.message : String(error)));
                        setRetryCount((prev) => {
                            const newCount = prev + 1;
                            // If we've tried several times, use fallback
                            if (newCount > 3) {
                                setUsingFallback(true);
                                setImageUrl(FALLBACK_IMAGE_PATH);
                                setManualRetryMode(true);
                                setIsLoading(false);
                                return newCount;
                            }
                            return newCount;
                        });
                    }
                }
            } finally {
                if (timeoutId !== null) window.clearTimeout(timeoutId);
                if (isActiveRef.current) {
                    setIsLoading(false);
                }
            }
        },
        [sceneName]
    );

    const handleImageLoad = useCallback((event: React.SyntheticEvent<HTMLImageElement>) => {
        const img = event.target as HTMLImageElement;
        if (img && img.naturalWidth > 0 && img.naturalHeight > 0) {
            setImageNaturalSize({
                width: img.naturalWidth,
                height: img.naturalHeight
            });
        }
        setIsLoading(false);
    }, []);

    const handleImageError = useCallback((event: React.SyntheticEvent<HTMLImageElement>) => {
        console.error('Image failed to load', event);
        // Only activate fallback after true error (not immediately)
        setUsingFallback(true);
        setImageUrl(FALLBACK_IMAGE_PATH);
        setIsLoading(false);
        setError('無法載入場景圖像，請檢查網路或重試');
    }, []);

    // Load initial image
    useEffect(() => {
        isActiveRef.current = true;
        const abortController = new AbortController();
        
        const loadImage = async () => {
            if (!isActiveRef.current) return;
            try {
                await fetchImage(abortController.signal);
            } catch (error) {
                // 檢查是否是組件卸載錯誤 - 更全面的檢測
                const errorString = String(error);
                const isUnmountError = 
                    (error.message && error.message.includes('Component unmounted')) ||
                    (error.name && error.name.includes('unmount')) ||
                    errorString.includes('Component unmounted') ||
                    errorString.includes('unmount') ||
                    !isActiveRef.current; // 如果組件已經不活躍，就認為是卸載錯誤
                
                if (isActiveRef.current && !abortController.signal.aborted && !isUnmountError) {
                    console.error('Failed to fetch image:', error);
                }
                // 對於卸載錯誤，完全靜默處理，不記錄任何日誌
            }
        };
        
        loadImage();
        
        return () => {
            isActiveRef.current = false;
            // In React 18, we can pass a reason to abort
            try {
                abortController.abort('Component unmounted');
            } catch {
                // Fallback for browsers that don't support abort with reason
                abortController.abort();
            }
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