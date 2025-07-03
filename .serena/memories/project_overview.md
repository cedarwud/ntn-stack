# NTN Stack 項目概述

## 項目目的
NTN Stack 是一個基於 5G 非地面網路 (Non-Terrestrial Network) 的智能切換系統，專注於衛星通信網路中的先進算法實現。系統採用 Fine-Grained Synchronized Algorithm 和 Fast Access Satellite Prediction Algorithm 等創新技術，實現低延遲、高可靠性的衛星間切換機制。

## 技術棧

### 後端
- **API 框架**: FastAPI (Python)
- **數據庫**: PostgreSQL + Redis
- **容器化**: Docker + Docker Compose
- **機器學習**: XGBoost + scikit-learn + NumPy
- **監控系統**: Prometheus + Grafana

### 前端
- **核心框架**: React 19 + TypeScript
- **3D 渲染**: Three.js + React Three Fiber
- **圖表庫**: Chart.js 4.5 + react-chartjs-2 + chartjs-plugin-annotation 3.1
- **狀態管理**: React Hooks + Context API
- **樣式系統**: SCSS + CSS Modules
- **建構工具**: Vite
- **測試框架**: Vitest + React Testing Library

### 仿真引擎
- **物理層仿真**: Sionna (TensorFlow)
- **網路仿真**: 自研 NTN 協議棧
- **3D 場景**: Blender 建模 + Three.js 渲染

## 項目結構
```
ntn-stack/
├── netstack/          # 後端 API 服務
├── simworld/          # 前端可視化系統
│   ├── frontend/      # React + TypeScript 前端
│   └── backend/       # 後端服務
└── tests/             # 測試套件
```

## 核心功能
- 3D 可視化衛星網路系統
- Fine-Grained Synchronized Algorithm 實現
- Fast Access Satellite Prediction Algorithm
- 測量事件圖表系統 (Event A4, D1, D2, T1)
- 即時性能監控與分析