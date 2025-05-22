/**
 * API路由配置
 * 集中管理所有後端API路徑，便於維護和更新
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export const ApiRoutes = {
  // 設備領域API
  devices: {
    base: `${API_BASE_URL}/devices`,
    getAll: `${API_BASE_URL}/devices`,
    getById: (id: string) => `${API_BASE_URL}/devices/${id}`,
    create: `${API_BASE_URL}/devices`,
    update: (id: string) => `${API_BASE_URL}/devices/${id}`,
    delete: (id: string) => `${API_BASE_URL}/devices/${id}`,
  },
  
  // 座標領域API
  coordinates: {
    base: `${API_BASE_URL}/coordinates`,
    convert: `${API_BASE_URL}/coordinates/convert`,
    validate: `${API_BASE_URL}/coordinates/validate`,
  },
  
  // 衛星領域API (已從 /satellite-ops 更改為 /satellites)
  satellites: {
    base: `${API_BASE_URL}/satellites`,
    getAll: `${API_BASE_URL}/satellites`,
    getById: (id: string) => `${API_BASE_URL}/satellites/${id}`,
    getTLE: (id: string) => `${API_BASE_URL}/satellites/${id}/tle`,
    getPasses: (id: string) => `${API_BASE_URL}/satellites/${id}/passes`,
    getVisibility: `${API_BASE_URL}/satellites/visibility`,
    getOrbit: (id: string) => `${API_BASE_URL}/satellites/${id}/orbit`,
  },
  
  // 模擬領域API (已從 /sionna 更改為 /simulations)
  simulations: {
    base: `${API_BASE_URL}/simulations`,
    createSimulation: `${API_BASE_URL}/simulations/run`,
    getCFRMap: `${API_BASE_URL}/simulations/cfr-map`,
    getSINRMap: `${API_BASE_URL}/simulations/sinr-map`,
    getDopplerMap: `${API_BASE_URL}/simulations/doppler-map`,
    getResults: (id: string) => `${API_BASE_URL}/simulations/${id}/results`,
  },
  
  // 網路平台API (已從 /platform 更改為 /network)
  network: {
    base: `${API_BASE_URL}/network`,
    subscribers: {
      getAll: `${API_BASE_URL}/network/subscribers`,
      getById: (id: string) => `${API_BASE_URL}/network/subscribers/${id}`,
      create: `${API_BASE_URL}/network/subscribers`,
      update: (id: string) => `${API_BASE_URL}/network/subscribers/${id}`,
      delete: (id: string) => `${API_BASE_URL}/network/subscribers/${id}`,
    },
    gNodeBs: {
      getAll: `${API_BASE_URL}/network/gnodeb`,
      getById: (id: string) => `${API_BASE_URL}/network/gnodeb/${id}`,
      status: `${API_BASE_URL}/network/gnodeb/status`,
    },
    ues: {
      getAll: `${API_BASE_URL}/network/ue`,
      getById: (id: string) => `${API_BASE_URL}/network/ue/${id}`,
      status: `${API_BASE_URL}/network/ue/status`,
    },
  },
};

export default ApiRoutes; 