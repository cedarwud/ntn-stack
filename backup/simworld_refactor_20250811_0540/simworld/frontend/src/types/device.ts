// frontend/src/types/device.ts

// 前端設備介面 - 與後端保持一致
export interface Device {
    id: number;
    name: string;
    position_x: number;
    position_y: number;
    position_z: number;
    orientation_x?: number;
    orientation_y?: number;
    orientation_z?: number;
    power_dbm?: number;
    active: boolean;
    role: string; // 使用角色字段
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