import { useState, useEffect, useCallback } from 'react';
import { Device } from '../types/device';

interface UseReceiverSelectionProps {
    devices: Device[];
    onSelectedReceiversChange?: (selectedIds: number[]) => void;
}

export const useReceiverSelection = ({
    devices,
    onSelectedReceiversChange,
}: UseReceiverSelectionProps) => {
    const getInitialReceiverIds = useCallback(() => {
        // 防止 devices 為 undefined 的錯誤
        if (!devices || !Array.isArray(devices)) {
            return [];
        }
        return devices
            .filter((device) => device.role === 'receiver' && device.id !== null)
            .map((device) => device.id as number);
    }, [devices]);

    const [selectedReceiverIds, setSelectedReceiverIds] = useState<number[]>(
        getInitialReceiverIds()
    );

    useEffect(() => {
        // This effect synchronizes the selected IDs with the parent component
        // when the component mounts or selectedReceiverIds/onSelectedReceiversChange changes.
        // It was initially in Sidebar, now moved here.
        if (onSelectedReceiversChange) {
            onSelectedReceiversChange(selectedReceiverIds);
        }
    }, [selectedReceiverIds, onSelectedReceiversChange]);

    useEffect(() => {
        // This effect ensures selectedReceiverIds stays in sync with the available devices
        // 並允許全部不選
        if (!devices || !Array.isArray(devices)) {
            return;
        }
        const currentReceiverDeviceIds = devices
            .filter((d) => d.role === 'receiver' && d.id !== null)
            .map((d) => d.id as number);

        setSelectedReceiverIds((prevSelected) => {
            // 僅保留目前還存在的 receiver id
            const newSelected = prevSelected.filter((id) =>
                currentReceiverDeviceIds.includes(id)
            );
            
            // 如果沒有選中任何接收器且有可用接收器，自動選中第一個
            if (newSelected.length === 0 && currentReceiverDeviceIds.length > 0) {
                return [currentReceiverDeviceIds[0]];
            }
            
            return newSelected;
        });
    }, [devices]); // Removed onSelectedReceiversChange from dependencies to avoid potential loop with parent

    const handleBadgeClick = useCallback((deviceId: number | null) => {
        if (deviceId === null) return;

        setSelectedReceiverIds((prevSelected) => {
            const newSelected = prevSelected.includes(deviceId)
                ? prevSelected.filter((id) => id !== deviceId)
                : [...prevSelected, deviceId];
            // The useEffect for [selectedReceiverIds, onSelectedReceiversChange] will notify parent.
            return newSelected;
        });
    }, []); // No dependencies needed if it only calls setSelectedReceiverIds

    return {
        selectedReceiverIds,
        handleBadgeClick,
    };
}; 