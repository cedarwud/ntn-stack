import React, { useState, useCallback, useMemo, RefObject } from 'react';
import { debounce } from 'lodash';
import { Device } from '../types/device'; // Assuming Device type is needed

interface FloorMouseInteractionsProps {
    imageRef: RefObject<HTMLImageElement | null>;
    imageNaturalSize: { width: number; height: number } | null;
    devices: Device[];
    imageToSceneCoords: (
        mouseX: number, mouseY: number,
        renderedWidth: number, renderedHeight: number,
        naturalWidth: number, naturalHeight: number
    ) => { x: number; y: number } | null;
    sceneToImageCoords: (sceneX: number, sceneY: number) => { x: number; y: number } | null;
    onOpenPopover: (
        position: { clientX: number; clientY: number; sceneX: number; sceneY: number },
        deviceToEdit?: Device
    ) => void;
    onClosePopover?: () => void; // Optional, if right click always closes
    isPopoverShown?: boolean; // Optional, if right click depends on this
}

export const useFloorMouseInteractions = ({
    imageRef,
    imageNaturalSize,
    devices,
    imageToSceneCoords,
    sceneToImageCoords,
    onOpenPopover,
    onClosePopover,
    isPopoverShown,
}: FloorMouseInteractionsProps) => {
    const [mousePositionForDisplay, setMousePositionForDisplay] = useState<{
        x: number; y: number; clientX: number; clientY: number;
        sceneX?: number; sceneY?: number;
    } | null>(null);
    const [hoveredDeviceId, setHoveredDeviceId] = useState<number | null>(null);
    const [cursorStyle, setCursorStyle] = useState<string>('crosshair');

    const updateMousePositionForDisplay = useMemo(
        () =>
            debounce((newPosition: typeof mousePositionForDisplay) => {
                setMousePositionForDisplay(newPosition);
            }, 50),
        []
    );

    const handleMouseMove = useCallback(
        (e: React.MouseEvent<HTMLImageElement>) => {
            if (imageRef.current && imageNaturalSize) {
                const rect = imageRef.current.getBoundingClientRect();
                const mouseX = Math.round(e.clientX - rect.left);
                const mouseY = Math.round(e.clientY - rect.top);

                const sceneCoords = imageToSceneCoords(
                    mouseX, mouseY,
                    rect.width, rect.height,
                    imageNaturalSize.width, imageNaturalSize.height
                );

                const newDisplayPosition = sceneCoords
                    ? { x: mouseX, y: mouseY, clientX: e.clientX, clientY: e.clientY, sceneX: sceneCoords.x, sceneY: sceneCoords.y }
                    : null;
                updateMousePositionForDisplay(newDisplayPosition);

                let foundHoveredDeviceId: number | null = null;
                if (sceneCoords && imageRef.current) { // Check imageRef.current again for safety
                    for (const device of devices) {
                        const deviceImgCoords = sceneToImageCoords(device.position_x, device.position_y);
                        if (deviceImgCoords) {
                            const distance = Math.sqrt(
                                Math.pow(mouseX - deviceImgCoords.x, 2) +
                                Math.pow(mouseY - deviceImgCoords.y, 2)
                            );
                            if (distance < 10) { // 10px hover radius
                                foundHoveredDeviceId = device.id;
                                break;
                            }
                        }
                    }
                }
                setHoveredDeviceId(foundHoveredDeviceId);
                setCursorStyle(foundHoveredDeviceId ? 'pointer' : 'crosshair');
            } else {
                updateMousePositionForDisplay(null);
                setHoveredDeviceId(null);
                setCursorStyle('crosshair');
            }
        },
        [imageRef, imageNaturalSize, devices, imageToSceneCoords, sceneToImageCoords, updateMousePositionForDisplay]
    );

    const handleMouseLeave = useCallback(() => {
        updateMousePositionForDisplay(null);
        setHoveredDeviceId(null);
        setCursorStyle('crosshair');
    }, [updateMousePositionForDisplay]);

    const handleFloorClick = useCallback(
        (e: React.MouseEvent<HTMLImageElement>) => {
            if (e.button !== 0) return; // Only left click

            if (imageRef.current && imageNaturalSize) {
                const rect = imageRef.current.getBoundingClientRect();
                const mouseX = Math.round(e.clientX - rect.left);
                const mouseY = Math.round(e.clientY - rect.top);

                const sceneCoords = imageToSceneCoords(
                    mouseX, mouseY, rect.width, rect.height,
                    imageNaturalSize.width, imageNaturalSize.height
                );

                if (sceneCoords) {
                    let clickedExistingDevice: Device | undefined = undefined;
                    for (const device of devices) {
                        const deviceImgCoords = sceneToImageCoords(device.position_x, device.position_y);
                        if (deviceImgCoords) {
                            const distance = Math.sqrt(
                                Math.pow(mouseX - deviceImgCoords.x, 2) +
                                Math.pow(mouseY - deviceImgCoords.y, 2)
                            );
                            if (distance < 10) { // 10px click radius
                                clickedExistingDevice = device;
                                break;
                            }
                        }
                    }

                    if (clickedExistingDevice) {
                        onOpenPopover(
                            { clientX: e.clientX, clientY: e.clientY, sceneX: clickedExistingDevice.position_x, sceneY: clickedExistingDevice.position_y },
                            clickedExistingDevice
                        );
                    } else {
                        // Open popover for new device at click location
                        onOpenPopover(
                            { clientX: e.clientX, clientY: e.clientY, sceneX: sceneCoords.x, sceneY: sceneCoords.y }
                        );
                    }
                }
            }
        },
        [imageRef, imageNaturalSize, devices, imageToSceneCoords, sceneToImageCoords, onOpenPopover]
    );

    const handleRightClick = useCallback(
        (e: React.MouseEvent<HTMLDivElement>) => {
            e.preventDefault();
            if (isPopoverShown && onClosePopover) {
                onClosePopover();
            }
        },
        [isPopoverShown, onClosePopover]
    );

    return {
        mousePositionForDisplay,
        hoveredDeviceId,
        cursorStyle,
        handleMouseMove,
        handleMouseLeave,
        handleFloorClick,
        handleRightClick,
    };
}; 