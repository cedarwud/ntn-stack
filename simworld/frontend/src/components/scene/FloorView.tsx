// src/components/SceneViewer.tsx
import React, { useCallback } from 'react'
import CoordinateDisplay from '../ui/CoordinateDisplay'
import { Device } from '../../types/device'
import '../../styles/Sidebar.scss'
import Starfield from '../ui/Starfield'
import DeviceOverlaySVG from './DeviceOverlaySVG'
import DevicePopover from '../devices/DevicePopover'
import { useSceneImageManager } from '../../hooks/useSceneImageManager'
import {
    useDevicePopoverManager,
    NewDevice,
} from '../../hooks/useDevicePopoverManager'
import { useFloorMouseInteractions } from '../../hooks/useFloorMouseInteractions'
import {
    imageToSceneCoords as utilImageToSceneCoords,
    sceneToImageCoords as utilSceneToImageCoords,
} from '../../utils/coordinate'
import { getSceneCoordinateTransform } from '../../utils/sceneUtils'

interface SceneViewerProps {
    devices: Device[]
    refreshDeviceData: () => void
    sceneName: string // 新增場景名稱參數
}

const SceneViewer: React.FC<SceneViewerProps> = React.memo(
    ({ devices: propDevices, refreshDeviceData, sceneName }) => {
        // 獲取場景特定的座標轉換參數
        const sceneCoordinateTransform = getSceneCoordinateTransform(sceneName)

        const {
            imageUrl,
            imageRefToAttach,
            isLoading,
            error: imageLoadingError,
            imageNaturalSize,
            retryLoad,
            handleImageLoad,
            handleImageError,
        } = useSceneImageManager(sceneName)

        const imageToSceneCoords = useCallback(
            (
                mouseX: number,
                mouseY: number,
                renderedWidth: number,
                renderedHeight: number,
                naturalWidth: number,
                naturalHeight: number
            ): { x: number; y: number } | null => {
                return utilImageToSceneCoords(
                    mouseX,
                    mouseY,
                    renderedWidth,
                    renderedHeight,
                    naturalWidth,
                    naturalHeight,
                    sceneCoordinateTransform
                )
            },
            [sceneCoordinateTransform]
        )

        const sceneToImageCoords = useCallback(
            (
                sceneX: number,
                sceneY: number
            ): { x: number; y: number } | null => {
                if (!imageRefToAttach.current || !imageNaturalSize) return null
                return utilSceneToImageCoords(
                    sceneX,
                    sceneY,
                    imageRefToAttach.current,
                    imageNaturalSize,
                    sceneCoordinateTransform
                )
            },
            [imageRefToAttach, imageNaturalSize, sceneCoordinateTransform]
        )

        const convertBackendToNewDevice = useCallback(
            (backendDevice: Device): NewDevice => ({
                id: backendDevice.id,
                name: backendDevice.name,
                position_x: backendDevice.position_x,
                position_y: backendDevice.position_y,
                position_z: backendDevice.position_z || 0,
                orientation_x: backendDevice.orientation_x || 0,
                orientation_y: backendDevice.orientation_y || 0,
                orientation_z: backendDevice.orientation_z || 0,
                power_dbm: backendDevice.power_dbm || 0,
                active: backendDevice.active,
                role: backendDevice.role,
            }),
            []
        )

        const {
            showPopover,
            popoverPosition,
            popoverDevice,
            isEditing,
            orientationInputs,
            handlePopoverOpen, // For floor clicks (via useFloorMouseInteractions)
            openPopoverForDeviceIcon, // For icon clicks (directly to DeviceOverlaySVG)
            handlePopoverClose, // For right clicks (via useFloorMouseInteractions) & Popover itself
            handlePopoverInputChange,
            handleOrientationChange,
            handlePopoverRoleChange,
            handleApplyPopover,
            handleDeleteDevice,
        } = useDevicePopoverManager({
            devices: propDevices,
            refreshDeviceData,
            sceneToImageCoords,
            convertBackendToNewDevice,
            imageNaturalSize,
            imageRef: imageRefToAttach, // Pass imageRef here
        })

        const {
            mousePositionForDisplay,
            hoveredDeviceId,
            cursorStyle,
            handleMouseMove,
            handleMouseLeave,
            handleFloorClick,
            handleRightClick,
        } = useFloorMouseInteractions({
            imageRef: imageRefToAttach,
            imageNaturalSize,
            devices: propDevices,
            imageToSceneCoords,
            sceneToImageCoords,
            onOpenPopover: handlePopoverOpen,
            onClosePopover: handlePopoverClose,
            isPopoverShown: showPopover,
        })

        if (imageLoadingError) {
            return (
                <div className="scene-container error-container">
                    <p>Error loading image: {imageLoadingError}</p>
                    <button onClick={retryLoad}>Retry</button>
                </div>
            )
        }

        return (
            <div className="scene-container" onContextMenu={handleRightClick}>
                <Starfield />
                <div className="scrollable-content">
                    {isLoading && (
                        <div className="loading-indicator">
                            Loading scene...
                        </div>
                    )}
                    <div
                        className="image-container"
                        style={{ cursor: cursorStyle }}
                    >
                        {imageUrl && (
                            <img
                                ref={imageRefToAttach}
                                src={imageUrl}
                                alt="Scene"
                                className="scene-image"
                                onLoad={handleImageLoad}
                                onError={handleImageError}
                                style={{
                                    display: isLoading ? 'none' : 'block',
                                }}
                                onMouseMove={handleMouseMove}
                                onMouseLeave={handleMouseLeave}
                                onClick={handleFloorClick}
                            />
                        )}
                        {!isLoading &&
                            imageUrl &&
                            imageRefToAttach.current &&
                            imageNaturalSize && (
                                <DeviceOverlaySVG
                                    devices={propDevices}
                                    imageRef={imageRefToAttach}
                                    imageNaturalSize={imageNaturalSize}
                                    sceneToImageCoords={sceneToImageCoords}
                                    hoveredDeviceId={hoveredDeviceId}
                                    onNodeClick={(deviceId, event) =>
                                        openPopoverForDeviceIcon(
                                            propDevices.find(
                                                (d) => d.id === deviceId
                                            )!,
                                            event
                                        )
                                    }
                                />
                            )}
                    </div>

                    {mousePositionForDisplay && (
                        <CoordinateDisplay position={mousePositionForDisplay} />
                    )}

                    {showPopover && popoverPosition && (
                        <DevicePopover
                            show={showPopover}
                            position={popoverPosition}
                            device={popoverDevice}
                            isEditing={isEditing}
                            onChange={handlePopoverInputChange}
                            onOrientationInput={(
                                axis: 'x' | 'y' | 'z',
                                value: string
                            ) =>
                                handleOrientationChange(axis, value, 'popover')
                            }
                            orientationInputs={orientationInputs}
                            onApply={handleApplyPopover}
                            onDelete={handleDeleteDevice}
                            onClose={handlePopoverClose}
                            onRoleChange={handlePopoverRoleChange}
                        />
                    )}
                </div>
            </div>
        )
    }
)

export default SceneViewer
