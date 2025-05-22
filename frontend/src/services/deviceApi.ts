import api from './api';
import { Device, DeviceCreate, DeviceUpdate } from '../types/device';
import { ApiRoutes } from '../config/apiRoutes';

// 設備角色枚舉（對應後端的 DeviceRole）
export enum DeviceRole {
  DESIRED = 'desired',
  JAMMER = 'jammer',
  RECEIVER = 'receiver',
}

// 獲取所有設備
export const getDevices = async (role?: string): Promise<Device[]> => {
  let url = `${ApiRoutes.devices.getAll}?limit=100`;
  
  if (role) {
    url += `&role=${role}`;
  }
  
  try {
    const response = await api.get<Device[]>(url);
    return response.data;
  } catch (error) {
    console.error('獲取設備列表失敗:', error);
    throw error;
  }
};

// 根據ID獲取單個設備
export const getDeviceById = async (deviceId: number): Promise<Device> => {
  try {
    const response = await api.get<Device>(ApiRoutes.devices.getById(deviceId.toString()));
    return response.data;
  } catch (error) {
    console.error(`獲取設備ID ${deviceId} 失敗:`, error);
    throw error;
  }
};

// 創建新設備
export const createDevice = async (deviceData: DeviceCreate): Promise<Device> => {
  try {
    const response = await api.post<Device>(ApiRoutes.devices.create, deviceData);
    return response.data;
  } catch (error) {
    console.error('創建設備失敗:', error);
    throw error;
  }
};

// 更新現有設備
export const updateDevice = async (deviceId: number, deviceData: DeviceUpdate): Promise<Device> => {
  try {
    const response = await api.put<Device>(ApiRoutes.devices.update(deviceId.toString()), deviceData);
    return response.data;
  } catch (error) {
    console.error(`更新設備ID ${deviceId} 失敗:`, error);
    throw error;
  }
};

// 刪除設備
export const deleteDevice = async (deviceId: number): Promise<void> => {
  try {
    await api.delete(ApiRoutes.devices.delete(deviceId.toString()));
  } catch (error) {
    console.error(`刪除設備ID ${deviceId} 失敗:`, error);
    throw error;
  }
};

export default {
  getDevices,
  getDeviceById,
  createDevice,
  updateDevice,
  deleteDevice
}; 