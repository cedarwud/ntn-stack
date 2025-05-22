import axios from 'axios';
import ApiRoutes from '../config/apiRoutes';

// 網路平台相關類型定義
interface Subscriber {
  id: string;
  imsi: string;
  msisdn: string;
  status: 'active' | 'inactive' | 'suspended';
  created_at: string;
  updated_at?: string;
}

interface GNodeB {
  id: string;
  name: string;
  tac: string;
  mcc: string;
  mnc: string;
  status: 'active' | 'inactive';
  created_at: string;
  updated_at?: string;
}

interface UE {
  id: string;
  subscriber_id: string;
  imei: string;
  msisdn: string;
  status: 'connected' | 'disconnected' | 'idle';
  connected_gnb_id?: string;
  created_at: string;
  updated_at?: string;
}

// 訂閱者(Subscriber) API
export const getAllSubscribers = async (): Promise<Subscriber[]> => {
  try {
    const response = await axios.get<Subscriber[]>(ApiRoutes.network.subscribers.getAll);
    return response.data;
  } catch (error) {
    console.error('獲取訂閱者列表失敗:', error);
    throw error;
  }
};

export const getSubscriberById = async (id: string): Promise<Subscriber> => {
  try {
    const response = await axios.get<Subscriber>(ApiRoutes.network.subscribers.getById(id));
    return response.data;
  } catch (error) {
    console.error(`獲取訂閱者 ${id} 失敗:`, error);
    throw error;
  }
};

export const createSubscriber = async (subscriberData: Omit<Subscriber, 'id' | 'created_at' | 'updated_at'>): Promise<Subscriber> => {
  try {
    const response = await axios.post<Subscriber>(ApiRoutes.network.subscribers.create, subscriberData);
    return response.data;
  } catch (error) {
    console.error('創建訂閱者失敗:', error);
    throw error;
  }
};

export const updateSubscriber = async (id: string, subscriberData: Partial<Subscriber>): Promise<Subscriber> => {
  try {
    const response = await axios.put<Subscriber>(ApiRoutes.network.subscribers.update(id), subscriberData);
    return response.data;
  } catch (error) {
    console.error(`更新訂閱者 ${id} 失敗:`, error);
    throw error;
  }
};

export const deleteSubscriber = async (id: string): Promise<void> => {
  try {
    await axios.delete(ApiRoutes.network.subscribers.delete(id));
  } catch (error) {
    console.error(`刪除訂閱者 ${id} 失敗:`, error);
    throw error;
  }
};

// gNodeB API
export const getAllGNodeBs = async (): Promise<GNodeB[]> => {
  try {
    const response = await axios.get<GNodeB[]>(ApiRoutes.network.gNodeBs.getAll);
    return response.data;
  } catch (error) {
    console.error('獲取gNodeB列表失敗:', error);
    throw error;
  }
};

export const getGNodeBById = async (id: string): Promise<GNodeB> => {
  try {
    const response = await axios.get<GNodeB>(ApiRoutes.network.gNodeBs.getById(id));
    return response.data;
  } catch (error) {
    console.error(`獲取gNodeB ${id} 失敗:`, error);
    throw error;
  }
};

export const getGNodeBStatus = async (): Promise<{[key: string]: string}> => {
  try {
    const response = await axios.get<{[key: string]: string}>(ApiRoutes.network.gNodeBs.status);
    return response.data;
  } catch (error) {
    console.error('獲取gNodeB狀態失敗:', error);
    throw error;
  }
};

// UE API
export const getAllUEs = async (): Promise<UE[]> => {
  try {
    const response = await axios.get<UE[]>(ApiRoutes.network.ues.getAll);
    return response.data;
  } catch (error) {
    console.error('獲取UE列表失敗:', error);
    throw error;
  }
};

export const getUEById = async (id: string): Promise<UE> => {
  try {
    const response = await axios.get<UE>(ApiRoutes.network.ues.getById(id));
    return response.data;
  } catch (error) {
    console.error(`獲取UE ${id} 失敗:`, error);
    throw error;
  }
};

export const getUEStatus = async (): Promise<{[key: string]: string}> => {
  try {
    const response = await axios.get<{[key: string]: string}>(ApiRoutes.network.ues.status);
    return response.data;
  } catch (error) {
    console.error('獲取UE狀態失敗:', error);
    throw error;
  }
};

export default {
  // Subscribers
  getAllSubscribers,
  getSubscriberById,
  createSubscriber,
  updateSubscriber,
  deleteSubscriber,
  
  // GNodeBs
  getAllGNodeBs,
  getGNodeBById,
  getGNodeBStatus,
  
  // UEs
  getAllUEs,
  getUEById,
  getUEStatus
}; 