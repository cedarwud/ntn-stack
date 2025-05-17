import axios from 'axios';

// 後端API的基礎URL - 根據環境動態設置
// 在開發模式下使用 localhost，在生產環境中使用真實 IP
const isLocalDevelopment = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const API_BASE_URL = isLocalDevelopment 
  ? 'http://localhost:8000/api/v1'
  : `http://${window.location.hostname}:8000/api/v1`;

// 設備角色枚舉（對應後端的 DeviceRole）
export enum DeviceRole {
  DESIRED = 'desired',
  JAMMER = 'jammer',
  RECEIVER = 'receiver',
}

// 設備介面（對應後端的 Device schema）
export interface Device {
  id: number;
  name: string;
  position_x: number;
  position_y: number;
  position_z: number;
  orientation_x?: number;
  orientation_y?: number;
  orientation_z?: number;
  role: string; // DeviceRole 的字串值
  power_dbm?: number;
  active: boolean;
}

// 用於創建設備的介面
export interface DeviceCreate {
  name: string;
  position_x: number;
  position_y: number;
  position_z: number;
  orientation_x?: number;
  orientation_y?: number;
  orientation_z?: number;
  role: string;
  power_dbm?: number;
  active: boolean;
}

// 用於更新設備的介面
export interface DeviceUpdate {
  name?: string;
  position_x?: number;
  position_y?: number;
  position_z?: number;
  orientation_x?: number;
  orientation_y?: number;
  orientation_z?: number;
  role?: string;
  power_dbm?: number;
  active?: boolean;
}

// 獲取所有設備
export const getDevices = async (role?: string): Promise<Device[]> => {
  let url = `${API_BASE_URL}/devices/?limit=100`;
  
  if (role) {
    url += `&role=${role}`;
  }
  
  try {
    const response = await axios.get<Device[]>(url);
    return response.data;
  } catch (error) {
    console.error('獲取設備列表失敗:', error);
    throw error;
  }
};

// 獲取特定類型的設備（便捷方法）
export const getJammers = async (): Promise<Device[]> => {
  try {
    const response = await axios.get<Device[]>(`${API_BASE_URL}/devices/jammers`);
    return response.data;
  } catch (error) {
    console.error('獲取干擾器列表失敗:', error);
    throw error;
  }
};

export const getReceivers = async (): Promise<Device[]> => {
  try {
    const response = await axios.get<Device[]>(`${API_BASE_URL}/devices/receivers`);
    return response.data;
  } catch (error) {
    console.error('獲取接收器列表失敗:', error);
    throw error;
  }
};

// 根據ID獲取單個設備
export const getDeviceById = async (deviceId: number): Promise<Device> => {
  try {
    const response = await axios.get<Device>(`${API_BASE_URL}/devices/${deviceId}`);
    return response.data;
  } catch (error) {
    console.error(`獲取設備ID ${deviceId} 失敗:`, error);
    throw error;
  }
};

// 創建新設備
export const createDevice = async (deviceData: DeviceCreate): Promise<Device> => {
  try {
    const response = await axios.post<Device>(`${API_BASE_URL}/devices/`, deviceData);
    return response.data;
  } catch (error) {
    console.error('創建設備失敗:', error);
    throw error;
  }
};

// 更新現有設備
export const updateDevice = async (deviceId: number, deviceData: DeviceUpdate): Promise<Device> => {
  try {
    const response = await axios.put<Device>(`${API_BASE_URL}/devices/${deviceId}`, deviceData);
    return response.data;
  } catch (error) {
    console.error(`更新設備ID ${deviceId} 失敗:`, error);
    throw error;
  }
};

// 刪除設備
export const deleteDevice = async (deviceId: number): Promise<void> => {
  try {
    await axios.delete(`${API_BASE_URL}/devices/${deviceId}`);
  } catch (error) {
    console.error(`刪除設備ID ${deviceId} 失敗:`, error);
    throw error;
  }
}; 