import React from 'react'

export interface DeviceOverlaySVGProps {
    devices: any[]
    imageRef: React.RefObject<HTMLImageElement | null>
    imageNaturalSize: { width: number; height: number } | null
    sceneToImageCoords: (
        x: number,
        y: number
    ) => { x: number; y: number } | null
    hoveredDeviceId: number | null
    onNodeClick?: (deviceId: number, e: React.MouseEvent) => void
}

const DeviceOverlaySVG: React.FC<DeviceOverlaySVGProps> = ({
    devices,
    imageRef,
    imageNaturalSize,
    sceneToImageCoords,
    hoveredDeviceId,
    onNodeClick,
}) => {
    if (!imageRef.current || !imageNaturalSize) return null
    return (
        <svg
            style={{
                position: 'absolute',
                left: 0,
                top: 0,
                pointerEvents: 'none',
                width: imageRef.current.offsetWidth,
                height: imageRef.current.offsetHeight,
                zIndex: 10,
            }}
            width={imageRef.current.offsetWidth}
            height={imageRef.current.offsetHeight}
        >
            {devices.map((device) => {
                const coords = sceneToImageCoords(
                    device.position_x,
                    device.position_y
                )
                if (!coords) return null
                let fillColor = '#ff2196F3'
                let strokeColor = '#fff'
                if (device.role === 'jammer') {
                    fillColor = '#E53935'
                } else if (device.role === 'desired') {
                    fillColor = '#222'
                    strokeColor = 'yellow'
                } else if (device.role === 'receiver') {
                    fillColor = '#FFA500'
                }
                const isHovered = hoveredDeviceId === device.id
                return (
                    <circle
                        key={device.id}
                        cx={coords.x}
                        cy={coords.y}
                        r={10}
                        fill={fillColor}
                        stroke={strokeColor}
                        strokeWidth={isHovered ? 3 : 1.5}
                        style={{
                            opacity: 0.95,
                            cursor: onNodeClick ? 'pointer' : undefined,
                            pointerEvents: onNodeClick ? 'auto' : 'none',
                        }}
                        onClick={
                            onNodeClick
                                ? (e) => onNodeClick(device.id, e)
                                : undefined
                        }
                    />
                )
            })}
        </svg>
    )
}

export default DeviceOverlaySVG
