// src/components/SceneViewer.tsx
import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import { debounce } from 'lodash' // 需要安裝 lodash 依賴
import CoordinateDisplay from './CoordinateDisplay' // 引入子組件
// 引入 API 函數和類型
import {
    createDevice,
    updateDevice,
    deleteDevice,
    DeviceCreate,
    DeviceUpdate,
    Device as BackendDevice,
    getDeviceById,
} from '../services/api' // <--- 確保只引入需要的內容
import { Device } from '../App' // <--- 從 App 引入前端 Device 介面
import '../styles/Sidebar.css' // 引入 Sidebar.css 以使用相同樣式
import Starfield from './Starfield'
import DeviceOverlaySVG from './DeviceOverlaySVG'
import DevicePopover from './DevicePopover'
import { imageToSceneCoords, sceneToImageCoords } from '../utils/coordinate'
import { generateDeviceName } from '../utils/deviceName'
import OrientationInput from './OrientationInput'
import { useImageLoader } from '../hooks/useImageLoader'

// 定義 Props 接口
interface SceneViewerProps {
    devices: Device[]
    refreshDeviceData: () => void // 添加回調函數 prop
}

// 定義新設備的介面
interface NewDevice {
    name: string
    position_x: number
    position_y: number
    position_z: number
    orientation_x: number
    orientation_y: number
    orientation_z: number
    power_dbm: number
    active: boolean
    role: string
}

// 定義靜態路徑指向後端存儲的最後一次成功渲染的圖像
const FALLBACK_IMAGE_PATH = '/rendered_images/scene_with_devices.png'

// 添加座標轉換常量 - 統一管理座標轉換參數
const COORDINATE_TRANSFORM = {
    offsetX: 579, // X轴偏移量
    offsetY: 511, // Y轴偏移量
    scale: 1.2, // 比例因子
}

// 使用 React.memo 包裝組件以避免不必要的重新渲染
const SceneViewer: React.FC<SceneViewerProps> = React.memo(
    ({ devices: propDevices, refreshDeviceData }) => {
        // console.log('--- SceneViewer Component Rendered ---')

        // --- Start: Move helper functions inside component scope ---
        // 轉換後端設備到前端 NewDevice (用於 Popover)
        const convertBackendToNewDevice = useCallback(
            (backendDevice: BackendDevice): NewDevice => {
                return {
                    name: backendDevice.name,
                    position_x: backendDevice.position_x,
                    position_y: backendDevice.position_y,
                    position_z: backendDevice.position_z,
                    orientation_x: backendDevice.orientation_x || 0, // 提供預設值
                    orientation_y: backendDevice.orientation_y || 0, // 提供預設值
                    orientation_z: backendDevice.orientation_z || 0, // 提供預設值
                    power_dbm: backendDevice.power_dbm || 0, // 提供預設值
                    active: backendDevice.active,
                    role: backendDevice.role, // 使用 role 而非 type
                }
            },
            []
        )
        // --- End: Move helper functions inside component scope ---

        const [imageUrl, setImageUrl] = useState<string | null>(null)
        const [isLoading, setIsLoading] = useState<boolean>(true)
        const [error, setError] = useState<string | null>(null)
        const prevImageUrlRef = useRef<string | null>(null) // 使用 ref 存儲上一個 URL
        const [usingFallback, setUsingFallback] = useState<boolean>(false)
        const [retryCount, setRetryCount] = useState<number>(0)
        const [manualRetryMode, setManualRetryMode] = useState<boolean>(false)
        const [imageNaturalSize, setImageNaturalSize] = useState<{
            width: number
            height: number
        } | null>(null)

        // 新增滑鼠座標狀態 - 移除 mousePositionRef
        const [mousePositionForDisplay, setMousePositionForDisplay] = useState<{
            x: number
            y: number
            clientX: number
            clientY: number
            sceneX?: number
            sceneY?: number
        } | null>(null) // 專門用於傳遞給 CoordinateDisplay 的狀態

        const imageRef = useRef<HTMLImageElement>(
            null
        ) as React.RefObject<HTMLImageElement>

        // 新增彈出視窗相關狀態
        const [showPopover, setShowPopover] = useState<boolean>(false)
        const [popoverPosition, setPopoverPosition] = useState<{
            x: number
            y: number
            clientX: number
            clientY: number
            sceneX?: number
            sceneY?: number
        } | null>(null)
        const [popoverDevice, setPopoverDevice] = useState<NewDevice>({
            name: '',
            position_x: 0,
            position_y: 0,
            position_z: 40,
            orientation_x: 0,
            orientation_y: 0,
            orientation_z: 0,
            power_dbm: 0,
            active: true,
            role: 'receiver',
        })
        const [isEditing, setIsEditing] = useState<boolean>(false)
        const [editingDeviceId, setEditingDeviceId] = useState<number | null>(
            null
        )
        const [hoveredDeviceId, setHoveredDeviceId] = useState<number | null>(
            null
        )
        const [cursorStyle, setCursorStyle] = useState<string>('crosshair')

        // 新增方向輸入本地狀態
        const [orientationInputs, setOrientationInputs] = useState<{
            [key: string]: { x: string; y: string; z: string }
        }>({})

        // 輔助函數：將圖像座標轉換為場景座標
        const imageToSceneCoords = useCallback(
            (
                mouseX: number, // Mouse X relative to img element
                mouseY: number, // Mouse Y relative to img element
                renderedWidth: number,
                renderedHeight: number,
                naturalWidth: number,
                naturalHeight: number
            ): { x: number; y: number } | null => {
                if (naturalWidth === 0 || naturalHeight === 0) return null // Avoid division by zero

                // Calculate the scale factor applied by 'object-fit: contain'
                const ratioX = renderedWidth / naturalWidth
                const ratioY = renderedHeight / naturalHeight
                const actualScale = Math.min(ratioX, ratioY)

                // Calculate the dimensions of the image as displayed within the element
                const displayedImageWidth = naturalWidth * actualScale
                const displayedImageHeight = naturalHeight * actualScale

                // Calculate the offset of the displayed image within the element (due to centering)
                const offsetX_render = (renderedWidth - displayedImageWidth) / 2
                const offsetY_render =
                    (renderedHeight - displayedImageHeight) / 2

                // Adjust mouse coordinates to be relative to the actual displayed image area
                const mouseXinDisplayed = mouseX - offsetX_render
                const mouseYinDisplayed = mouseY - offsetY_render

                // Check if the mouse is outside the actual image area
                if (
                    mouseXinDisplayed < 0 ||
                    mouseXinDisplayed > displayedImageWidth ||
                    mouseYinDisplayed < 0 ||
                    mouseYinDisplayed > displayedImageHeight
                ) {
                    return null // Mouse is not over the actual image content
                }

                // Convert coordinates relative to the displayed image to coordinates relative to the original image
                const originalImageX = mouseXinDisplayed / actualScale
                const originalImageY = mouseYinDisplayed / actualScale

                // Apply the fixed transformation from original image coordinates to scene coordinates
                const sceneX = Math.round(
                    (originalImageX - COORDINATE_TRANSFORM.offsetX) /
                        COORDINATE_TRANSFORM.scale
                )
                const sceneY = Math.round(
                    (originalImageY - COORDINATE_TRANSFORM.offsetY) /
                        COORDINATE_TRANSFORM.scale
                ) // Maintain original calculation

                return { x: sceneX, y: sceneY }
            },
            [] // COORDINATE_TRANSFORM is constant
        )

        // 輔助函數：將場景座標轉換為圖像座標
        const sceneToImageCoords = useCallback(
            (
                sceneX: number,
                sceneY: number
            ): { x: number; y: number } | null => {
                if (!imageRef.current || !imageNaturalSize) return null // Check for natural size

                const { width: naturalWidth, height: naturalHeight } =
                    imageNaturalSize
                const renderedWidth = imageRef.current.offsetWidth
                const renderedHeight = imageRef.current.offsetHeight

                if (naturalWidth === 0 || naturalHeight === 0) return null

                // Inverse transformation: Scene -> Original Image Coords
                const originalImageX =
                    sceneX * COORDINATE_TRANSFORM.scale +
                    COORDINATE_TRANSFORM.offsetX
                const originalImageY =
                    sceneY * COORDINATE_TRANSFORM.scale +
                    COORDINATE_TRANSFORM.offsetY

                // Calculate the scale factor and offsets used for rendering ('object-fit: contain')
                const ratioX = renderedWidth / naturalWidth
                const ratioY = renderedHeight / naturalHeight
                const actualScale = Math.min(ratioX, ratioY)
                const displayedImageWidth = naturalWidth * actualScale
                const displayedImageHeight = naturalHeight * actualScale
                const offsetX_render = (renderedWidth - displayedImageWidth) / 2
                const offsetY_render =
                    (renderedHeight - displayedImageHeight) / 2

                // Convert original image coords to coordinates relative to the *displayed* image area
                const mouseXinDisplayed = originalImageX * actualScale
                const mouseYinDisplayed = originalImageY * actualScale

                // Convert coordinates relative to the displayed image area to coordinates relative to the *img element*
                const imageElementX = Math.round(
                    mouseXinDisplayed + offsetX_render
                )
                const imageElementY = Math.round(
                    mouseYinDisplayed + offsetY_render
                )

                return { x: imageElementX, y: imageElementY }
            },
            [imageNaturalSize] // Add imageNaturalSize as dependency
        )

        // 獲取現有設備列表的函數 - 現在直接使用 props
        // const fetchExistingDevices = ... (移除)

        // 生成新設備名稱的函數 - 需要調整以使用 props 中的 devices
        const generateDeviceName = useCallback(
            (role: string, currentDevices: Device[]) => {
                const prefix =
                    role === 'desired'
                        ? 'tx'
                        : role === 'receiver'
                        ? 'rx'
                        : 'jam'
                const typeDevices = currentDevices.filter((d) =>
                    d.name.startsWith(prefix)
                )
                let maxNum = 0
                typeDevices.forEach((device) => {
                    const numPart = device.name.replace(prefix, '')
                    const num = parseInt(numPart, 10)
                    if (!isNaN(num) && num > maxNum) {
                        maxNum = num
                    }
                })
                return `${prefix}${maxNum + 1}`
            },
            []
        )

        // 主效果 - 初始載入 - 僅執行一次
        useEffect(() => {
            console.log('--- SceneViewer useEffect triggered for mount ---')

            // 將 AbortController 移入 useEffect
            const controller = new AbortController()
            // 將 fetchImage 的調用也放入 useEffect，並傳遞 controller
            const fetchData = async () => {
                await fetchImage(controller.signal)
            }

            fetchData()

            // 清理函數
            return () => {
                console.log('--- SceneViewer useEffect cleanup ---')
                controller.abort() // 中斷與此 useEffect 實例相關的請求
                if (prevImageUrlRef.current) {
                    URL.revokeObjectURL(prevImageUrlRef.current)
                    console.log(
                        'Cleaned up object URL on unmount:',
                        prevImageUrlRef.current
                    )
                    prevImageUrlRef.current = null
                }
            }
        }, [])

        // 封裝 fetchImage 函數，接收 AbortSignal
        const fetchImage = useCallback(
            async (signal: AbortSignal) => {
                const rtEndpoint = '/api/v1/sionna/scene-image-devices'

                setIsLoading(true)
                setError(null)
                setUsingFallback(false)

                // 清理上一個 createObjectURL (從 ref 中讀取)
                if (prevImageUrlRef.current) {
                    URL.revokeObjectURL(prevImageUrlRef.current)
                    prevImageUrlRef.current = null // 清理 ref
                    console.log('Revoked previous object URL from ref')
                }

                const endpointWithCacheBuster = `${rtEndpoint}?t=${new Date().getTime()}`
                console.log(`Fetching image from: ${endpointWithCacheBuster}`)

                let timeoutId: number | null = null

                try {
                    // 設置超時計時器
                    timeoutId = window.setTimeout(() => {
                        console.warn(
                            `Fetch image request timed out after 15s for ${endpointWithCacheBuster}`
                        )
                    }, 15000)

                    const response = await fetch(endpointWithCacheBuster, {
                        signal, // 使用傳入的 signal
                        cache: 'no-cache',
                        headers: {
                            Pragma: 'no-cache',
                            'Cache-Control': 'no-cache',
                        },
                    })

                    // 如果請求成功或失敗（非超時中止），清除超時計時器
                    if (timeoutId !== null) window.clearTimeout(timeoutId)

                    if (!response.ok) {
                        // 嘗試讀取錯誤訊息 (如果後端返回 JSON)
                        let errorDetail = `HTTP error! status: ${response.status}`
                        try {
                            const errorJson = await response.json()
                            errorDetail = errorJson.detail || errorDetail // 使用後端提供的 detail
                        } catch (jsonError) {
                            // 如果回應不是 JSON 或解析失敗，保持原始 HTTP 錯誤
                        }
                        throw new Error(errorDetail)
                    }

                    // 使用嘗試-捕獲塊來處理響應內容
                    try {
                        // 假設後端直接返回圖片 blob
                        const imageBlob = await response.blob()

                        // 檢查 blob 是否有效 (例如，大小 > 0)
                        if (imageBlob.size === 0) {
                            throw new Error('Received empty image blob.')
                        }

                        const newImageUrl = URL.createObjectURL(imageBlob)
                        console.log('Created new object URL:', newImageUrl)
                        setImageUrl(newImageUrl) // 設定新的圖片 URL
                        prevImageUrlRef.current = newImageUrl // 儲存這次的 URL 到 ref
                        setRetryCount(0) // 重置重試計數
                        setManualRetryMode(false) // 重置手動重試模式
                    } catch (blobError) {
                        console.error('Error processing image blob:', blobError)
                        throw new Error(
                            `處理圖像時出錯: ${
                                blobError instanceof Error
                                    ? blobError.message
                                    : String(blobError)
                            }`
                        )
                    }
                } catch (error) {
                    // 如果請求被中止，也清除超時
                    if (timeoutId !== null) window.clearTimeout(timeoutId)

                    // 只在錯誤不是 AbortError 時才記錄為失敗 (AbortError 在 StrictMode 下是預期行為)
                    if ((error as Error).name !== 'AbortError') {
                        console.error(
                            `Failed to fetch image from ${rtEndpoint}:`,
                            error
                        )
                        // 嘗試使用備用圖像 - 但改為通過 fetch API 載入，而不是直接使用路徑
                        try {
                            console.log(
                                'Trying to fetch fallback image as blob...'
                            )
                            const fallbackResponse = await fetch(
                                FALLBACK_IMAGE_PATH,
                                {
                                    cache: 'no-cache',
                                    headers: {
                                        Pragma: 'no-cache',
                                        'Cache-Control': 'no-cache',
                                    },
                                }
                            )

                            if (fallbackResponse.ok) {
                                const fallbackBlob =
                                    await fallbackResponse.blob()
                                if (fallbackBlob.size > 0) {
                                    const fallbackUrl =
                                        URL.createObjectURL(fallbackBlob)
                                    setImageUrl(fallbackUrl)
                                    prevImageUrlRef.current = fallbackUrl // 更新 ref
                                    setUsingFallback(true)
                                    setError(
                                        `使用備用圖像: ${
                                            error instanceof Error
                                                ? error.message
                                                : '未知錯誤'
                                        }`
                                    )
                                    console.log(
                                        'Successfully loaded fallback image as blob'
                                    )
                                } else {
                                    throw new Error('備用圖像 blob 為空')
                                }
                            } else {
                                throw new Error(
                                    `備用圖像請求失敗: ${fallbackResponse.status}`
                                )
                            }
                        } catch (fallbackError) {
                            console.error(
                                'Fallback image loading failed:',
                                fallbackError
                            )
                            // 最後的備用：使用直接 URL (可能會導致 404 或內容長度問題，但至少我們嘗試了)
                            setImageUrl(FALLBACK_IMAGE_PATH)
                            setUsingFallback(true)
                            setError(
                                `圖像載入失敗: ${
                                    error instanceof Error
                                        ? error.message
                                        : '未知錯誤'
                                }`
                            )
                        }
                    } else {
                        console.log(
                            'Fetch aborted (likely due to StrictMode or component unmount), ignoring error.'
                        )
                    }

                    // 增加重試計數
                    const currentRetryCount = retryCount + 1
                    setRetryCount(currentRetryCount)

                    // 如果重試超過3次，進入手動重試模式
                    if (currentRetryCount >= 3) {
                        // 這裡直接使用計算後的值
                        setManualRetryMode(true)
                    } else {
                        // 否則自動重試一次，但延長間隔
                        console.log(`自動重試 (${currentRetryCount}/3)...`)
                        // 設定較長的重試間隔
                        setTimeout(() => {
                            fetchImage(new AbortController().signal) // 在 setTimeout 內部調用 fetchImage
                        }, 5000) // 增加到5秒
                    }
                } finally {
                    // 確保 timeoutId 被清除
                    if (timeoutId !== null) window.clearTimeout(timeoutId)
                    setIsLoading(false)
                }
            },
            [retryCount]
        )

        const handleImageLoad = useCallback(() => {
            console.log(`Image element loaded successfully: ${imageUrl}`)
            if (imageRef.current) {
                // <-- Get natural dimensions on load
                setImageNaturalSize({
                    width: imageRef.current.naturalWidth,
                    height: imageRef.current.naturalHeight,
                })
                console.log(
                    `Natural image size: ${imageRef.current.naturalWidth}x${imageRef.current.naturalHeight}`
                )
            }
            setIsLoading(false) // 圖片成功顯示後，確認 loading 結束
            if (!usingFallback) {
                setError(null) // 只有非備用圖像時才清除錯誤
            }
        }, [imageUrl, usingFallback])

        const handleImageError = useCallback(
            (e: React.SyntheticEvent<HTMLImageElement, Event>) => {
                // 這個錯誤通常表示圖片 URL 有問題或圖片本身損壞
                console.error(
                    `Image element failed to load src: ${imageUrl}`,
                    e
                )

                // 如果是備用圖像也載入失敗，那麼顯示錯誤訊息
                if (usingFallback || imageUrl === FALLBACK_IMAGE_PATH) {
                    setError(`備用圖片也無法載入，請檢查網絡連接`)
                } else {
                    // 嘗試使用備用圖像
                    console.log(
                        'Regular image failed, trying fallback:',
                        FALLBACK_IMAGE_PATH
                    )
                    setImageUrl(FALLBACK_IMAGE_PATH)
                    setUsingFallback(true)
                    setError(`使用最後一次成功的圖像 (無法連接後端服務)`)
                }

                setIsLoading(false) // 確保 loading 結束
            },
            [imageUrl, usingFallback]
        )

        // 處理滑鼠移動事件 - 使用防抖動更新顯示狀態
        const updateMousePositionForDisplay = useMemo(
            () =>
                debounce(
                    (
                        newPosition: {
                            x: number
                            y: number
                            clientX: number
                            clientY: number
                        } | null
                    ) => {
                        setMousePositionForDisplay(newPosition)
                    },
                    50
                ),
            []
        )

        const handleMouseMove = useCallback(
            (e: React.MouseEvent<HTMLImageElement>) => {
                if (imageRef.current && imageNaturalSize) {
                    // Ensure natural size is available
                    const rect = imageRef.current.getBoundingClientRect()
                    const mouseX = Math.round(e.clientX - rect.left) // Relative to element
                    const mouseY = Math.round(e.clientY - rect.top) // Relative to element

                    // Calculate scene coordinates using the new logic
                    const sceneCoords = imageToSceneCoords(
                        mouseX,
                        mouseY,
                        rect.width, // Rendered width
                        rect.height, // Rendered height
                        imageNaturalSize.width, // Natural width
                        imageNaturalSize.height // Natural height
                    )

                    // Update display coordinates (only if sceneCoords is not null)
                    const newDisplayPosition = sceneCoords
                        ? {
                              x: mouseX, // Keep element-relative coords for potential debugging
                              y: mouseY,
                              clientX: e.clientX,
                              clientY: e.clientY,
                              sceneX: sceneCoords.x, // Use the calculated scene coords
                              sceneY: sceneCoords.y,
                          }
                        : null // Don't show coordinates if mouse is outside image content
                    updateMousePositionForDisplay(newDisplayPosition)

                    // --- Hover check ---
                    // Use updated sceneToImageCoords for checking device proximity
                    let foundHoveredDeviceId: number | null = null
                    if (sceneCoords) {
                        // Only check hover if mouse is over image content
                        for (const device of propDevices) {
                            const deviceImageCoords = sceneToImageCoords(
                                device.position_x,
                                device.position_y
                            )
                            if (deviceImageCoords) {
                                // Check distance in screen pixels relative to the element
                                const distanceX = Math.abs(
                                    mouseX - deviceImageCoords.x
                                )
                                const distanceY = Math.abs(
                                    mouseY - deviceImageCoords.y
                                )
                                // Keep the tolerance in screen pixels for now
                                if (distanceX <= 5 && distanceY <= 5) {
                                    foundHoveredDeviceId = device.id
                                    break // Found the first one
                                }
                            }
                        }
                    }

                    // Update hover state and cursor style
                    setHoveredDeviceId(foundHoveredDeviceId)
                    setCursorStyle(
                        foundHoveredDeviceId !== null
                            ? 'pointer'
                            : sceneCoords
                            ? 'crosshair'
                            : 'default'
                    ) // Change cursor based on image content hover
                } else {
                    // If imageRef or natural size isn't ready, clear display position and hover state
                    updateMousePositionForDisplay(null)
                    setHoveredDeviceId(null)
                    setCursorStyle('default') // Use default cursor if not over image or image not ready
                }
            },
            [
                propDevices,
                updateMousePositionForDisplay,
                sceneToImageCoords, // Now depends on imageNaturalSize
                imageToSceneCoords, // New dependency
                imageNaturalSize, // New dependency
            ]
        )

        // 處理滑鼠離開事件
        const handleMouseLeave = useCallback(() => {
            updateMousePositionForDisplay(null)
            setHoveredDeviceId(null)
            setCursorStyle('crosshair') // Reset to default crosshair when leaving element
        }, [updateMousePositionForDisplay])

        // 關閉彈出視窗 - 移到 handleImageClick 和 handleMouseMove 之前，因為它們可能依賴它
        const handleClosePopover = useCallback(() => {
            setShowPopover(false)
            setPopoverPosition(null)
            setIsEditing(false)
            setEditingDeviceId(null)
        }, [])

        // 處理圖片點擊事件 - 修改以處理編輯和新增
        const handleImageClick = useCallback(
            async (e: React.MouseEvent<HTMLImageElement>) => {
                if (imageRef.current && imageNaturalSize) {
                    // Ensure natural size available
                    // 如果點擊時 popover 已開啟，則關閉
                    if (showPopover) {
                        handleClosePopover() // Use the dedicated close handler
                        return
                    }

                    const rect = imageRef.current.getBoundingClientRect()
                    const clickX = Math.round(e.clientX - rect.left) // Relative to element
                    const clickY = Math.round(e.clientY - rect.top) // Relative to element

                    // Calculate scene coordinates using the new logic
                    const sceneCoords = imageToSceneCoords(
                        clickX,
                        clickY,
                        rect.width,
                        rect.height,
                        imageNaturalSize.width,
                        imageNaturalSize.height
                    )

                    // Only proceed if the click was inside the actual image content
                    if (!sceneCoords) {
                        // Click was outside the image content (in the letterboxed area)
                        // Do nothing or optionally close popover if desired
                        return
                    }

                    // 檢查是否點擊在懸停的設備上 (hoveredDeviceId is reliable now)
                    if (hoveredDeviceId !== null) {
                        // --- 編輯模式 ---
                        setIsEditing(true)
                        setEditingDeviceId(hoveredDeviceId)

                        try {
                            // 從 API 獲取最新的設備數據
                            const deviceToEdit = await getDeviceById(
                                hoveredDeviceId
                            )
                            const initialPopoverData =
                                convertBackendToNewDevice(deviceToEdit)
                            setPopoverDevice(initialPopoverData)

                            // 設置 popover 位置靠近設備圖標 - use updated sceneToImageCoords
                            const deviceCoords = sceneToImageCoords(
                                deviceToEdit.position_x,
                                deviceToEdit.position_y
                            )

                            // Position relative to client, potentially adjusted by device image coords
                            const popoverClientX = deviceCoords
                                ? rect.left + deviceCoords.x
                                : e.clientX
                            const popoverClientY = deviceCoords
                                ? rect.top + deviceCoords.y
                                : e.clientY

                            setPopoverPosition({
                                x: clickX, // Store element-relative click coords
                                y: clickY,
                                clientX: popoverClientX, // Use client coords for positioning
                                clientY: popoverClientY + 10, // Offset below cursor/device
                                sceneX: deviceToEdit.position_x, // Store actual scene coords
                                sceneY: deviceToEdit.position_y,
                            })
                            setShowPopover(true)
                        } catch (error) {
                            console.error(
                                `獲取設備 ${hoveredDeviceId} 數據失敗:`,
                                error
                            )
                            alert(
                                `無法加載設備數據: ${
                                    error instanceof Error
                                        ? error.message
                                        : '未知錯誤'
                                }`
                            )
                            setIsEditing(false)
                            setEditingDeviceId(null)
                        }
                    } else {
                        // --- 新增模式 ---
                        setIsEditing(false)
                        setEditingDeviceId(null)

                        // Position popover based on click location
                        setPopoverPosition({
                            x: clickX,
                            y: clickY,
                            clientX: e.clientX, // Use direct click client coords
                            clientY: e.clientY + 10, // Offset below cursor
                            sceneX: sceneCoords.x, // Use calculated scene coords
                            sceneY: sceneCoords.y,
                        })

                        // 生成名稱並設置初始 popover 數據 using calculated sceneCoords
                        const initialDevice = {
                            position_z: 40, // 修改：預設 Z 軸值為 40
                            orientation_x: popoverDevice.orientation_x,
                            orientation_y: popoverDevice.orientation_y,
                            orientation_z: popoverDevice.orientation_z,
                            power_dbm: popoverDevice.power_dbm,
                            active: popoverDevice.active,
                            role: popoverDevice.role,
                            position_x: sceneCoords.x, // Use correct scene coords
                            position_y: sceneCoords.y, // Use correct scene coords
                            name: generateDeviceName(
                                popoverDevice.role,
                                propDevices
                            ),
                        }
                        setPopoverDevice(initialDevice)
                        setShowPopover(true)
                    }
                }
            },
            [
                showPopover, // Existing
                hoveredDeviceId, // Existing
                propDevices, // Existing
                generateDeviceName, // Existing
                popoverDevice.position_z, // Existing (for default values)
                popoverDevice.active, // Existing (for default values)
                popoverDevice.role, // Existing (for default values)
                sceneToImageCoords, // Updated
                imageToSceneCoords, // Updated
                imageNaturalSize, // New
                handleClosePopover, // Existing
                convertBackendToNewDevice, // Existing
                getDeviceById, // Added missing dependency
            ]
        )

        // 處理 Popover 內設備屬性變更
        const handlePopoverInputChange = (field: string, value: any) => {
            const updatedDevice = { ...popoverDevice }
            if (field === 'role') {
                const newRole = value as string
                if (
                    newRole === 'desired' ||
                    newRole === 'receiver' ||
                    newRole === 'jammer'
                ) {
                    updatedDevice.role = newRole
                }
            } else if (field === 'name') {
                updatedDevice.name = value
            } else if (field === 'position_x') {
                updatedDevice.position_x = Math.round(value)
            } else if (field === 'position_y') {
                updatedDevice.position_y = Math.round(value)
            } else if (field === 'position_z') {
                updatedDevice.position_z = parseFloat(
                    parseFloat(value).toFixed(1)
                )
            } else if (field === 'orientation_x') {
                updatedDevice.orientation_x = parseFloat(
                    parseFloat(value).toFixed(1)
                )
            } else if (field === 'orientation_y') {
                updatedDevice.orientation_y = parseFloat(
                    parseFloat(value).toFixed(1)
                )
            } else if (field === 'orientation_z') {
                updatedDevice.orientation_z = parseFloat(
                    parseFloat(value).toFixed(1)
                )
            } else if (field === 'power_dbm') {
                updatedDevice.power_dbm = parseInt(value)
            } else if (field === 'active') {
                updatedDevice.active = value
            }
            setPopoverDevice(updatedDevice)
        }

        // 處理方向輸入的變化
        const handleOrientationInput = useCallback(
            (axis: 'x' | 'y' | 'z', value: string) => {
                // 更新本地狀態
                setOrientationInputs((prev) => ({
                    ...prev,
                    ['popover']: {
                        ...(prev['popover'] || { x: '0', y: '0', z: '0' }),
                        [axis]: value,
                    },
                }))

                // 檢查輸入是否包含分數格式
                if (value.includes('/')) {
                    const parts = value.split('/')
                    if (parts.length === 2) {
                        const numerator = parseFloat(parts[0])
                        const denominator = parseFloat(parts[1])
                        if (
                            !isNaN(numerator) &&
                            !isNaN(denominator) &&
                            denominator !== 0
                        ) {
                            // 計算分數值並乘以 π
                            const calculatedValue =
                                (numerator / denominator) * Math.PI
                            // 更新設備狀態
                            const orientationKey = `orientation_${axis}`
                            // 更新 popoverDevice 狀態
                            setPopoverDevice((prev) => ({
                                ...prev,
                                [orientationKey]: calculatedValue,
                            }))
                        }
                    }
                } else {
                    // 嘗試將值解析為數字
                    const numValue = parseFloat(value)
                    if (!isNaN(numValue)) {
                        const orientationKey = `orientation_${axis}`
                        // 更新 popoverDevice 狀態
                        setPopoverDevice((prev) => ({
                            ...prev,
                            [orientationKey]: numValue,
                        }))
                    }
                }
            },
            []
        )

        // 當編輯的設備改變時，初始化方向輸入狀態
        useEffect(() => {
            if (popoverDevice) {
                setOrientationInputs({
                    popover: {
                        x: popoverDevice.orientation_x?.toString() || '0',
                        y: popoverDevice.orientation_y?.toString() || '0',
                        z: popoverDevice.orientation_z?.toString() || '0',
                    },
                })
            }
        }, [popoverDevice.name]) // 當設備名稱改變時觸發，表示切換了設備

        // 修復 handleApplyPopover 函數
        const handleApplyPopover = async (e: React.FormEvent) => {
            e.preventDefault()

            if (isEditing && editingDeviceId) {
                // 更新現有設備
                handleUpdateDevice(e)
            } else {
                // 創建新設備
                handleCreateNewDevice(e)
            }
        }

        // 新增：處理刪除設備
        const handleDeleteDevice = useCallback(async () => {
            if (!isEditing || editingDeviceId === null) {
                console.warn('Delete called without editing context')
                return
            }

            if (
                !window.confirm(`確定要刪除設備 "${popoverDevice.name}" 嗎？`)
            ) {
                return
            }

            try {
                console.log(`Calling deleteDevice for ID: ${editingDeviceId}`)
                await deleteDevice(editingDeviceId)
                console.log('Device deleted successfully')

                handleClosePopover()
                fetchImage(new AbortController().signal) // 更新場景圖
                refreshDeviceData() // 更新 App 狀態
            } catch (error: any) {
                console.error(
                    `Failed to delete device ${editingDeviceId}:`,
                    error
                )
                let errorMessage = '刪除設備失敗'
                if (error.response?.data?.detail) {
                    errorMessage += ': ' + error.response.data.detail
                } else if (error.message) {
                    errorMessage += ': ' + error.message
                }
                alert(errorMessage)
            }
        }, [
            isEditing,
            editingDeviceId,
            popoverDevice.name,
            fetchImage,
            refreshDeviceData,
            handleClosePopover,
        ])

        // 使用固定標題
        const title = 'NYCU Scene'

        const [maxImageHeight, setMaxImageHeight] = useState<string>('auto') // 新增狀態儲存最大高度

        // Effect to calculate and update max image height
        useEffect(() => {
            const calculateHeight = () => {
                const navbarHeight = 60 // Navbar height in pixels
                const availableHeight = window.innerHeight - navbarHeight
                setMaxImageHeight(`${availableHeight}px`)
            }

            calculateHeight() // Initial calculation
            window.addEventListener('resize', calculateHeight) // Update on resize

            // Cleanup listener on component unmount
            return () => window.removeEventListener('resize', calculateHeight)
        }, []) // Empty dependency array means this runs once on mount and cleans up on unmount

        // 修改 handleNodeClick 函數，添加 orientation 和 power_dbm
        const handleNodeClick = useCallback(
            async (deviceId: number, e: React.MouseEvent) => {
                e.stopPropagation() // 防止冒泡到圖像的點擊處理

                try {
                    // const backendDevice = await getDeviceById(deviceId)
                    const device = propDevices.find((d) => d.id === deviceId)
                    if (!device) {
                        // 新增日誌，檢查是否因為找不到裝置而提前返回
                        console.warn(
                            `[SceneViewer] Device not found in propDevices. ID: ${deviceId}`,
                            'Current propDevices:',
                            propDevices
                        )
                        return // 防止錯誤
                    }

                    const { position_x, position_y } = device

                    // 獲取元素位置
                    const rect = e.currentTarget.getBoundingClientRect()
                    const clientX = rect.left + rect.width / 2 // 中心點 X
                    const clientY = rect.top + rect.height / 2 // 中心點 Y

                    // 更新編輯相關狀態
                    setIsEditing(true)
                    setEditingDeviceId(deviceId)

                    const newPopoverPosition = {
                        x: position_x,
                        y: position_y,
                        clientX,
                        clientY,
                        sceneX: position_x,
                        sceneY: position_y,
                    }

                    setPopoverPosition(newPopoverPosition)

                    // 更新 popoverDevice 狀態
                    const newPopoverDevice = {
                        name: device.name,
                        position_x: device.position_x,
                        position_y: device.position_y,
                        position_z: device.position_z,
                        orientation_x: device.orientation_x || 0,
                        orientation_y: device.orientation_y || 0,
                        orientation_z: device.orientation_z || 0,
                        power_dbm: device.power_dbm || 0,
                        active: device.active,
                        role: device.role,
                    }

                    setPopoverDevice(newPopoverDevice)
                    setShowPopover(true)
                } catch (error) {
                    console.error(
                        `[SceneViewer] Error in handleNodeClick for device ID ${deviceId}:`,
                        error
                    )
                    // 發生錯誤時，確保彈窗是關閉的
                    setShowPopover(false)
                    setIsEditing(false)
                    setEditingDeviceId(null)
                }
            },
            [propDevices]
        )

        // 添加創建設備函數
        const handleCreateNewDevice = async (e: React.FormEvent) => {
            e.preventDefault()
            if (!popoverPosition) return

            try {
                // 準備設備資料
                const backendData: DeviceCreate = {
                    name: popoverDevice.name,
                    position_x: popoverDevice.position_x,
                    position_y: popoverDevice.position_y,
                    position_z: popoverDevice.position_z,
                    orientation_x: popoverDevice.orientation_x,
                    orientation_y: popoverDevice.orientation_y,
                    orientation_z: popoverDevice.orientation_z,
                    power_dbm: popoverDevice.power_dbm,
                    active: popoverDevice.active,
                    role: popoverDevice.role, // 使用前端的 role 填充後端的 role
                }

                // 呼叫 API
                const createdDevice = await createDevice(backendData)
                console.log('設備創建成功:', createdDevice)

                // 清理狀態
                setShowPopover(false)
                setPopoverPosition(null)
                setPopoverDevice({
                    name: '',
                    position_x: 0,
                    position_y: 0,
                    position_z: 0,
                    orientation_x: 0,
                    orientation_y: 0,
                    orientation_z: 0,
                    power_dbm: 0,
                    active: true,
                    role: 'receiver',
                })

                // 重新獲取所有設備
                refreshDeviceData()
            } catch (error) {
                console.error('創建設備失敗:', error)
                // 可以額外添加錯誤處理邏輯
            }
        }

        // 添加更新設備函數
        const handleUpdateDevice = async (e: React.FormEvent) => {
            e.preventDefault()
            if (!editingDeviceId) return

            try {
                // 準備更新資料
                const updateData: DeviceUpdate = {
                    name: popoverDevice.name,
                    position_x: popoverDevice.position_x,
                    position_y: popoverDevice.position_y,
                    position_z: popoverDevice.position_z,
                    orientation_x: popoverDevice.orientation_x,
                    orientation_y: popoverDevice.orientation_y,
                    orientation_z: popoverDevice.orientation_z,
                    power_dbm: popoverDevice.power_dbm,
                    active: popoverDevice.active,
                    role: popoverDevice.role, // 使用前端的 role 填充後端的 role
                }

                // 呼叫 API
                await updateDevice(editingDeviceId, updateData)
                console.log(`設備 ID: ${editingDeviceId} 更新成功`)

                // 清理狀態
                setShowPopover(false)
                setPopoverPosition(null)
                setIsEditing(false)
                setEditingDeviceId(null)

                // 重新獲取所有設備
                refreshDeviceData()
            } catch (error) {
                console.error(`更新設備 ID: ${editingDeviceId} 失敗:`, error)
                // 可以額外添加錯誤處理邏輯
            }
        }

        // 彈窗內 role select onChange 時自動更新 name
        const handlePopoverRoleChange = (newRole: string) => {
            setPopoverDevice((prev) => ({
                ...prev,
                role: newRole,
                name: generateDeviceName(newRole, propDevices),
            }))
        }

        return (
            <div
                style={{
                    position: 'relative',
                    minHeight: '100vh',
                    background:
                        'radial-gradient(ellipse at bottom, #1b2735 0%, #090a0f 100%)',
                    overflow: 'hidden',
                }}
            >
                {/* 星空星點層（在最底層，不影響互動） */}
                <Starfield starCount={180} />
                {/* 其餘內容照舊，zIndex > 0 的內容會蓋在星空上 */}
                {isLoading && <p>Loading...</p>}
                {/* 只有在 imageUrl 存在且 loading 完成後才顯示 img，或在 loading 時顯示佔位符 */}
                <div style={{ position: 'relative' }}>
                    {imageUrl && (
                        <img
                            ref={imageRef}
                            key={imageUrl}
                            src={imageUrl}
                            alt={title}
                            onLoad={handleImageLoad}
                            onError={handleImageError}
                            onMouseMove={handleMouseMove}
                            onMouseLeave={handleMouseLeave}
                            onClick={handleImageClick}
                            style={{
                                maxWidth: '100%',
                                maxHeight: maxImageHeight, // 使用計算後的最大高度
                                display: isLoading ? 'none' : 'block',
                                cursor: cursorStyle,
                                objectFit: 'contain',
                                margin: '0 auto', // 水平置中
                            }}
                        />
                    )}

                    {/* 節點 SVG 覆蓋層 */}
                    {imageUrl && imageNaturalSize && imageRef.current && (
                        <DeviceOverlaySVG
                            devices={propDevices}
                            imageRef={imageRef}
                            imageNaturalSize={imageNaturalSize}
                            sceneToImageCoords={sceneToImageCoords}
                            hoveredDeviceId={hoveredDeviceId}
                            onNodeClick={handleNodeClick}
                        />
                    )}

                    {/* 座標顯示 - 使用獨立組件，並且只在 popover 不顯示時渲染 */}
                    {!showPopover && (
                        <CoordinateDisplay position={mousePositionForDisplay} />
                    )}

                    {/* 新增設備彈出視窗 - 更新為與 Sidebar 一致的樣式 */}
                    {showPopover && popoverPosition && (
                        <DevicePopover
                            show={showPopover}
                            position={popoverPosition}
                            device={popoverDevice}
                            isEditing={isEditing}
                            onChange={handlePopoverInputChange}
                            onRoleChange={handlePopoverRoleChange}
                            onApply={handleApplyPopover}
                            onDelete={handleDeleteDevice}
                            onClose={handleClosePopover}
                            onOrientationInput={handleOrientationInput}
                            orientationInputs={orientationInputs}
                        />
                    )}
                </div>
            </div>
        )
    }
)

export default SceneViewer
