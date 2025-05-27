import { useState, useCallback, useEffect, RefObject } from 'react';
import { Device, DeviceCreate, DeviceUpdate } from '../types/device';
import { createDevice, updateDevice, deleteDevice as apiDeleteDevice } from '../services';
import { generateDeviceName as utilGenerateDeviceName } from '../utils/deviceName';

// Define the NewDevice interface (or import if it's shared)
export interface NewDevice {
    id?: number; // Optional: for existing devices
    name: string;
    position_x: number;
    position_y: number;
    position_z: number;
    orientation_x: number;
    orientation_y: number;
    orientation_z: number;
    power_dbm: number;
    active: boolean;
    role: string;
}

interface UseDevicePopoverManagerProps {
    devices: Device[]; // For checking name conflicts, etc.
    refreshDeviceData: () => void;
    sceneToImageCoords: (sceneX: number, sceneY: number) => { x: number; y: number } | null;
    convertBackendToNewDevice: (backendDevice: Device) => NewDevice;
    imageNaturalSize: { width: number; height: number } | null; // Needed for positioning
    imageRef?: RefObject<HTMLImageElement | null>; // Added for calculating icon click position
}

export const useDevicePopoverManager = ({
    devices,
    refreshDeviceData,
    sceneToImageCoords,
    convertBackendToNewDevice,
    imageNaturalSize,
    imageRef,
}: UseDevicePopoverManagerProps) => {
    const [showPopover, setShowPopover] = useState<boolean>(false);
    const [popoverPosition, setPopoverPosition] = useState<{
        x: number;
        y: number;
        clientX: number; // For Popover component anchor
        clientY: number; // For Popover component anchor
        sceneX?: number; // Scene coordinates for device
        sceneY?: number; // Scene coordinates for device
    } | null>(null);

    const [popoverDevice, setPopoverDevice] = useState<NewDevice>({
        name: '',
        position_x: 0,
        position_y: 0,
        position_z: 40, // Default Z
        orientation_x: 0,
        orientation_y: 0,
        orientation_z: 0,
        power_dbm: 0,
        active: true,
        role: 'receiver', // Default role
    });

    const [isEditing, setIsEditing] = useState<boolean>(false);
    const [editingDeviceId, setEditingDeviceId] = useState<number | null>(null);

    // For Popover's orientation inputs specifically
    const [orientationInputs, setOrientationInputs] = useState<{
        [key: string]: { x: string; y: string; z: string };
    }>({});


    const handlePopoverOpen = useCallback(
        (
            position: { clientX: number; clientY: number; sceneX: number; sceneY: number },
            deviceToEdit?: Device
        ) => {
            const anchorX = position.clientX;
            const anchorY = position.clientY;

            if (deviceToEdit) {
                const newDeviceState = convertBackendToNewDevice(deviceToEdit);
                setPopoverDevice({ ...newDeviceState, id: deviceToEdit.id });
                setIsEditing(true);
                setEditingDeviceId(deviceToEdit.id);
                // Initialize orientation inputs for existing device
                setOrientationInputs({
                    popover: {
                        x: String(newDeviceState.orientation_x),
                        y: String(newDeviceState.orientation_y),
                        z: String(newDeviceState.orientation_z),
                    },
                });
            } else {
                // Name generation for new devices is now handled by the useEffect below
                const newDeviceInitial: NewDevice = {
                    name: '', // Will be set by useEffect if empty
                    position_x: position.sceneX,
                    position_y: position.sceneY,
                    position_z: 40, // Default Z
                    orientation_x: 0,
                    orientation_y: 0,
                    orientation_z: 0,
                    power_dbm: 0,
                    active: true,
                    role: 'receiver',
                };
                setPopoverDevice(newDeviceInitial);
                setIsEditing(false);
                setEditingDeviceId(null);
                // Reset orientation inputs for new device
                setOrientationInputs({
                    popover: { x: '0', y: '0', z: '0' },
                });
            }
            setPopoverPosition({ ...position, x: anchorX, y: anchorY });
            setShowPopover(true);
        },
        [convertBackendToNewDevice]
    );

    // Effect for auto-generating name for new devices
    useEffect(() => {
        if (showPopover && !isEditing && !popoverDevice.name) {
            const newName = utilGenerateDeviceName(
                popoverDevice.role, // Use current role in popover
                devices.map(d => ({ name: d.name })) // Pass existing names
            );
            setPopoverDevice(prev => ({ ...prev, name: newName }));
        }
    }, [showPopover, isEditing, popoverDevice.name, popoverDevice.role, devices]);

    const handlePopoverClose = useCallback(() => {
        setShowPopover(false);
        setPopoverPosition(null);
        setEditingDeviceId(null);
        setIsEditing(false);
        // Optionally reset popoverDevice to defaults if not editing
        // setPopoverDevice({ name: '', ... initial values ... });
        setOrientationInputs({}); // Clear orientation inputs
    }, []);

    const handlePopoverInputChange = useCallback((field: string, value: any) => {
        setPopoverDevice((prev) => ({ ...prev, [field]: value }));
    }, []);

    const handleOrientationChange = useCallback(
        (axis: 'x' | 'y' | 'z', value: string, type: string = 'popover') => {
            setOrientationInputs((prev) => ({
                ...prev,
                [type]: {
                    ...prev[type],
                    [axis]: value,
                },
            }));
            // Also update the main popoverDevice state if the input is valid
            const numericValue = parseFloat(value);
            if (!isNaN(numericValue)) {
                setPopoverDevice((prev) => ({
                    ...prev,
                    [`orientation_${axis}`]: numericValue,
                }));
            }
        },
        []
    );
    
    const handlePopoverRoleChange = useCallback((newRole: string) => {
        // 計算新名稱
        const newName = utilGenerateDeviceName(
            newRole,
            devices.map(d => ({ name: d.name }))
        );
        
        // 更新角色和名稱
        setPopoverDevice(prev => ({ 
            ...prev, 
            role: newRole,
            name: newName
        }));
    }, [devices]);


    const handleApplyPopover = useCallback(async (e: React.FormEvent) => {
        e.preventDefault();
        // Basic validation (example)
        if (!popoverDevice.name.trim()) {
            alert('Device name cannot be empty.');
            return;
        }
        // Check for duplicate names, excluding the current device if editing
        const duplicateNameExists = devices.some(
            (d) => d.name === popoverDevice.name && d.id !== editingDeviceId
        );
        if (duplicateNameExists) {
            alert(`Device name "${popoverDevice.name}" already exists.`);
            return;
        }

        const deviceData: DeviceCreate | DeviceUpdate = {
            ...popoverDevice,
            // Ensure types match backend expectations
            position_z: Number(popoverDevice.position_z) || 0,
            orientation_x: Number(popoverDevice.orientation_x) || 0,
            orientation_y: Number(popoverDevice.orientation_y) || 0,
            orientation_z: Number(popoverDevice.orientation_z) || 0,
            power_dbm: Number(popoverDevice.power_dbm) || 0,
        };

        try {
            if (isEditing && editingDeviceId !== null) {
                await updateDevice(editingDeviceId, deviceData as DeviceUpdate);
                // console.log('Device updated:', editingDeviceId, deviceData);
            } else {
                await createDevice(deviceData as DeviceCreate);
                // console.log('Device created:', deviceData);
            }
            refreshDeviceData();
            handlePopoverClose();
        } catch (error) {
            console.error('Failed to save device:', error);
            alert(`Failed to save device: ${error instanceof Error ? error.message : String(error)}`);
        }
    }, [popoverDevice, isEditing, editingDeviceId, devices, refreshDeviceData, handlePopoverClose]);

    const handleDeleteDevice = useCallback(async () => {
        if (!isEditing || editingDeviceId === null) {
            console.warn('Delete called without a device being edited or no editingDeviceId.');
            alert('Cannot delete: No device selected for editing.');
            return;
        }
        if (window.confirm(`Are you sure you want to delete device "${popoverDevice.name}" (ID: ${editingDeviceId})?`)) {
            try {
                await apiDeleteDevice(editingDeviceId);
                refreshDeviceData();
                handlePopoverClose();
            } catch (error) {
                console.error('Failed to delete device:', error);
                alert(`Failed to delete device: ${error instanceof Error ? error.message : String(error)}`);
            }
        }
    }, [isEditing, editingDeviceId, popoverDevice.name, refreshDeviceData, handlePopoverClose]);

    const openPopoverForDeviceIcon = useCallback(
        (deviceToEdit: Device, event: React.MouseEvent) => {
            if (!imageRef?.current || !sceneToImageCoords) {
                console.warn("Image ref or sceneToImageCoords not available for icon click positioning.");
                // Fallback or simple positioning if ref/coords are not ready
                handlePopoverOpen(
                    { clientX: event.clientX, clientY: event.clientY, sceneX: deviceToEdit.position_x, sceneY: deviceToEdit.position_y },
                    deviceToEdit
                );
                return;
            }
    
            const deviceScreenCoords = sceneToImageCoords(deviceToEdit.position_x, deviceToEdit.position_y);
            let clientX = event.clientX;
            let clientY = event.clientY;
    
            if (deviceScreenCoords) {
                const rect = imageRef.current.getBoundingClientRect();
                clientX = rect.left + deviceScreenCoords.x;
                clientY = rect.top + deviceScreenCoords.y;
            }
            
            handlePopoverOpen(
                { clientX, clientY, sceneX: deviceToEdit.position_x, sceneY: deviceToEdit.position_y },
                deviceToEdit
            );
        },
        [imageRef, sceneToImageCoords, handlePopoverOpen] // Dependencies for this new function
    );

    return {
        showPopover,
        popoverPosition,
        popoverDevice,
        isEditing,
        editingDeviceId, // for UI indication
        orientationInputs,
        handlePopoverOpen,
        openPopoverForDeviceIcon, // New handler for icon clicks
        handlePopoverClose,
        handlePopoverInputChange,
        handleOrientationChange,
        handlePopoverRoleChange,
        handleApplyPopover,
        handleDeleteDevice,
        // Expose setPopoverDevice if direct manipulation is needed from outside,
        // but it's generally better to manage it via specific actions.
        // setPopoverDevice, 
    };
}; 