// src/contexts/DeviceContext.tsx
import { createContext, useContext, ReactNode } from 'react';
import { useDevices } from '../hooks/useDevices';
import { Device } from '../types/device';

interface DeviceContextType {
    tempDevices: Device[];
    loading: boolean;
    apiStatus: 'disconnected' | 'connected' | 'error';
    hasTempDevices: boolean;
    fetchDevices: () => Promise<void>;
    applyDeviceChanges: () => Promise<void>;
    deleteDeviceById: (id: number) => Promise<void>;
    addNewDevice: () => Promise<void>;
    updateDeviceField: (id: number, field: keyof Device, value: unknown) => void;
    cancelDeviceChanges: () => void;
    updateDevicePositionFromUAV: (deviceId: number, pos: [number, number, number]) => void;
}

const DeviceContext = createContext<DeviceContextType | undefined>(undefined);

export const DeviceProvider = ({ children }: { children: ReactNode }) => {
    const deviceState = useDevices();
    return (
        <DeviceContext.Provider value={deviceState}>
            {children}
        </DeviceContext.Provider>
    );
};

export const useDeviceContext = () => {
    const context = useContext(DeviceContext);
    if (context === undefined) {
        throw new Error('useDeviceContext must be used within a DeviceProvider');
    }
    return context;
};
