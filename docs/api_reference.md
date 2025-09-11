# 🌐 NTN Stack API 參考手冊

**版本**: 3.0.0  
**更新日期**: 2025-08-18  
**專案狀態**: ✅ 生產就緒  
**適用於**: LEO 衛星切換研究系統 - 完整API接口文檔

## 📋 概述

本文檔提供 NTN Stack 系統所有可用 API 端點的完整參考，包括 NetStack 核心API和 SimWorld 仿真API。所有API都經過實際測試並與當前系統實現保持一致。

**📋 相關文檔**：
- **系統架構**：[系統架構總覽](./system_architecture.md) - 服務拓撲和端口配置
- **算法實現**：[算法實現手冊](./algorithms_implementation.md) - API背後的算法邏輯  
- **技術指南**：[技術實施指南](./technical_guide.md) - 部署和故障排除
- **衛星標準**：[衛星換手標準](./satellite_handover_standards.md) - 3GPP標準實現

## 🚀 快速開始

### 服務端點與端口
```yaml
服務配置:
  NetStack API: 
    url: "http://localhost:8080"
    description: "核心換手決策、ML預測、性能監控"
    health_check: "http://localhost:8080/health"
    
  SimWorld Backend:
    url: "http://localhost:8888" 
    description: "衛星數據查詢、軌道計算、時間序列"
    health_check: "http://localhost:8888/api/health"
    
  SimWorld Frontend:
    url: "http://localhost:5173"
    description: "3D可視化界面"
    type: "Web Interface"
```

### 認證與安全
```http
# 開發環境 - 無需認證
GET /api/v1/satellites/health HTTP/1.1
Host: localhost:8888

# 生產環境 (預留) - API Key認證
GET /api/v1/satellites/health HTTP/1.1
Host: production-server
Authorization: Bearer YOUR_API_KEY
X-API-Version: 3.0.0
```

### 統一響應格式
```json
{
  "success": true,
  "data": {
    "result": "實際數據內容",
    "metadata": "額外資訊"
  },
  "message": "操作成功描述",
  "timestamp": "2025-08-18T12:00:00Z",
  "api_version": "3.0.0",
  "request_id": "req_1692345678"
}
```

## 🛰️ 衛星數據API (SimWorld Backend)

### 服務健康檢查
```http
GET /api/health
Host: localhost:8888
```

**響應**:
```json
{
  "status": "healthy",
  "timestamp": "2025-08-18T12:00:00Z", 
  "services": {
    "sgp4_calculator": "operational",
    "tle_data_loader": "ready",
    "orbit_predictor": "active",
    "data_cache": "synchronized"
  },
  "data_freshness": {
    "starlink_tle": "2025-08-18T06:00:00Z",
    "oneweb_tle": "2025-08-18T06:00:00Z",
    "last_orbital_update": "2025-08-18T11:30:00Z"
  }
}
```

### 統一時間序列API

#### 獲取衛星時間序列數據
```http
GET /api/v1/satellites/unified/timeseries
```

**參數**:
- `constellation` (string, required): 星座名稱 (`starlink`, `oneweb`)
- `duration_minutes` (int, optional): 時間範圍，預設120分鐘
- `interval_seconds` (int, optional): 採樣間隔，預設30秒
- `reference_time` (string, optional): 參考時間點，預設使用TLE數據的epoch時間
- `observer_location` (string, optional): 觀測點 "lat,lon,alt"，預設NTPU

**範例請求**:
```bash
curl "http://localhost:8888/api/v1/satellites/unified/timeseries?constellation=starlink&duration_minutes=60&interval_seconds=30"
```

**範例響應**:
```json
{
  "success": true,
  "data": {
    "metadata": {
      "constellation": "starlink",
      "satellites_count": 8,
      "time_points": 120,
      "duration_minutes": 60,
      "interval_seconds": 30,
      "sgp4_mode": "runtime_precision",
      "data_source": "real_tle_data",
      "computation_time": "2025-08-18T12:00:00Z"
    },
    "satellites": [
      {
        "satellite_id": "STARLINK-1007",
        "norad_id": 44714,
        "timeseries": [
          {
            "timestamp": "2025-08-18T12:00:00Z",
            "elevation_deg": 45.7,
            "azimuth_deg": 152.3,
            "range_km": 589.2,
            "latitude": 52.1234,
            "longitude": 10.5678,
            "altitude_km": 550.5,
            "is_visible": true,
            "rsrp_dbm": -78.3
          }
        ]
      }
    ]
  },
  "message": "時間序列數據生成成功",
  "timestamp": "2025-08-18T12:00:00Z"
}
```

#### 系統狀態查詢
```http
GET /api/v1/satellites/unified/status
```

**響應格式**:
```json
{
  "success": true,
  "data": {
    "service_status": "healthy",
    "data_freshness": "2025-08-18T11:30:00Z",
    "available_constellations": ["starlink", "oneweb"],
    "constellation_stats": {
      "starlink": {
        "total_satellites": 8042,
        "active_satellites": 7896,
        "tle_epoch": "2025-08-18T06:00:00Z"
      },
      "oneweb": {
        "total_satellites": 651,
        "active_satellites": 634,
        "tle_epoch": "2025-08-18T06:00:00Z"
      }
    },
    "processing_status": {
      "preprocess_completed": true,
      "last_update": "2025-08-18T11:30:00Z",
      "next_update_due": "2025-08-18T17:30:00Z"
    }
  }
}
```

### 即時衛星位置查詢

#### 可見衛星查詢
```http
GET /api/v1/satellites/visible_satellites
```

**參數**:
- `count` (int, 1-50): 返回衛星數量，預設10
- `min_elevation_deg` (float, 0-90): 最小仰角，預設5.0
- `observer_lat` (float): 觀測者緯度，預設24.9441667
- `observer_lon` (float): 觀測者經度，預設121.3713889  
- `observer_alt` (float): 觀測者高度(米)，預設24
- `utc_timestamp` (string): 查詢時間點，預設使用TLE數據的epoch時間
- `constellation` (string, optional): 星座過濾
- `global_view` (bool): 全球視野模式，預設false

**範例請求**:
```bash
curl "http://localhost:8888/api/v1/satellites/visible_satellites?count=8&min_elevation_deg=10&constellation=starlink"
```

**範例響應**:
```json
{
  "success": true,
  "data": {
    "satellites": [
      {
        "satellite_id": "STARLINK-1234", 
        "norad_id": 44714,
        "name": "STARLINK-1007",
        "elevation_deg": 67.2,
        "azimuth_deg": 185.4,
        "range_km": 542.8,
        "latitude": 52.1234,
        "longitude": 10.5678,
        "altitude_km": 550.5,
        "is_visible": true,
        "rsrp_dbm": -72.5,
        "doppler_shift_hz": -1234.5,
        "constellation": "starlink"
      }
    ],
    "query_info": {
      "total_count": 8,
      "observer_location": {
        "latitude": 24.9441667,
        "longitude": 121.3713889,
        "altitude_m": 24
      },
      "query_timestamp": "2025-08-18T12:00:00Z",
      "min_elevation_applied": 10.0,
      "global_view": false
    },
    "computation_stats": {
      "query_time_ms": 45,
      "satellites_processed": 8042,
      "sgp4_calculations": 8042
    }
  }
}
```

### 星座資訊查詢

#### 星座統計資訊
```http
GET /api/v1/satellites/constellations/info
```

**範例響應**:
```json
{
  "success": true,
  "data": {
    "constellations": {
      "starlink": {
        "total_satellites": 8042,
        "active_satellites": 7896,
        "orbital_shells": [
          {
            "altitude_km": 550,
            "inclination_deg": 53.0,
            "satellite_count": 4408
          },
          {
            "altitude_km": 570,
            "inclination_deg": 53.0,  
            "satellite_count": 1584
          }
        ],
        "tle_epoch": "2025-08-18T06:00:00Z",
        "data_quality": "excellent"
      },
      "oneweb": {
        "total_satellites": 651,
        "active_satellites": 634,
        "orbital_shells": [
          {
            "altitude_km": 1200,
            "inclination_deg": 87.4,
            "satellite_count": 634
          }
        ],
        "tle_epoch": "2025-08-18T06:00:00Z",
        "data_quality": "good"
      }
    },
    "system_totals": {
      "total_leo_satellites": 8693,
      "active_leo_satellites": 8530
    }
  }
}
```

## 🎯 NetStack 核心API (localhost:8080)

### 系統健康檢查
```http
GET /health
Host: localhost:8080
```

**標準響應**:
```json
{
  "status": "healthy",
  "timestamp": "2025-08-18T12:00:00Z",
  "services": {
    "database": "healthy",
    "redis_cache": "healthy",
    "ml_models": "loaded",
    "handover_engine": "operational",
    "time_sync": "synchronized"
  },
  "system_metrics": {
    "uptime_seconds": 86400,
    "cpu_usage_percent": 15.2,
    "memory_usage_mb": 512.8,
    "active_connections": 12
  },
  "api_version": "3.0.0"
}
```

### 衛星操作API

#### 換手決策評估 (核心API)
```http
POST /api/v1/satellite-ops/evaluate_handover
```

**實際實現位置**: `netstack/netstack_api/routers/satellite_ops_router.py`

**參數** (GET查詢參數):
- `serving_satellite_id` (string, required): 當前服務衛星ID
- `count` (int, 1-100): 候選衛星數量，預設10
- `constellation` (string, optional): 星座過濾
- `min_elevation_deg` (float, 0-90): 最小仰角，預設10.0
- `observer_lat` (float): 觀測者緯度，預設24.9441667
- `observer_lon` (float): 觀測者經度，預設121.3713889
- `observer_alt` (float): 觀測者高度，預設24
- `utc_timestamp` (string, optional): 評估時間點

**範例請求**:
```bash
curl -X POST "http://localhost:8080/api/v1/satellite-ops/evaluate_handover" \
  -G \
  -d "serving_satellite_id=44714" \
  -d "count=8" \
  -d "constellation=starlink" \
  -d "min_elevation_deg=10"
```

**範例響應**:
```json
{
  "handover_decision": {
    "should_handover": true,
    "target_satellite_id": "44715",
    "handover_reason": "觸發事件: A4, D2",
    "priority": "MEDIUM",
    "expected_improvement": {
      "rsrp_gain_db": 8.45,
      "distance_reduction_km": 234.67,
      "elevation_improvement_deg": 12.3
    },
    "confidence_score": 0.87,
    "triggered_events": ["A4", "D2"],
    "estimated_handover_time": "2025-08-18T12:00:30Z"
  },
  "serving_satellite": {
    "satellite_id": "44714",
    "name": "STARLINK-1007",
    "rsrp_dbm": -78.23,
    "distance_km": 867.92,
    "elevation_deg": 34.72,
    "azimuth_deg": 145.6,
    "signal_quality_score": 0.73,
    "doppler_shift_hz": -892.1
  },
  "neighbor_satellites": [
    {
      "satellite_id": "44715",
      "name": "STARLINK-1008", 
      "rsrp_dbm": -69.78,
      "distance_km": 633.25,
      "elevation_deg": 47.05,
      "azimuth_deg": 156.8,
      "signal_quality_score": 0.89,
      "handover_benefit_score": 0.91,
      "3gpp_events": ["A4"]
    }
  ],
  "evaluation_context": {
    "total_candidates_evaluated": 25,
    "3gpp_events_summary": {
      "a4_events_triggered": 5,
      "a5_events_triggered": 0,
      "d2_events_triggered": 2
    },
    "evaluation_time_ms": 23.4,
    "algorithm_version": "fine_grained_v2.1"
  }
}
```

#### 可見衛星查詢 (NetStack版本)
```http
GET /api/v1/satellite-ops/visible_satellites
```

**參數** (與SimWorld相同，但支援更多過濾選項):
- 基本參數同SimWorld API
- `signal_threshold_dbm` (float, optional): RSRP門檻過濾
- `handover_suitability` (bool, optional): 僅返回換手適合的衛星
- `include_3gpp_events` (bool, optional): 包含3GPP事件分析

**範例響應**:
```json
{
  "satellites": [
    {
      "satellite_id": "44714",
      "rsrp_dbm": -78.3,
      "elevation_deg": 45.7,
      "azimuth_deg": 152.3,
      "range_km": 589.2,
      "handover_suitability": {
        "suitable": true,
        "score": 0.89,
        "reasons": ["high_elevation", "strong_signal", "low_doppler"]
      },
      "3gpp_events": {
        "a4_triggered": true,
        "a4_threshold_dbm": -100.0,
        "measurement_time": "2025-08-18T12:00:00Z"
      }
    }
  ],
  "total_count": 8,
  "filtering_applied": {
    "min_elevation_deg": 10.0,
    "signal_threshold_dbm": -120.0,
    "handover_suitability_filter": true
  }
}
```

### 換手決策引擎API

#### 候選評估 (詳細分析)
```http
POST /api/v1/handover_decision/evaluate_candidates
```

**請求格式**:
```json
{
  "ue_context": {
    "ue_id": "UE_12345",
    "current_satellite": "STARLINK-1234",
    "location": {
      "latitude": 24.9441667,
      "longitude": 121.3713889,
      "altitude_m": 24
    },
    "service_requirements": {
      "min_throughput_mbps": 10,
      "max_latency_ms": 50
    }
  },
  "candidates": [
    {
      "satellite_id": "STARLINK-5678",
      "signal_strength_dbm": -75.2,
      "elevation_deg": 45.7,
      "azimuth_deg": 180.3,
      "distance_km": 650.4,
      "load_factor": 0.6,
      "beam_id": "beam_01"
    }
  ],
  "decision_criteria": {
    "signal_weight": 0.35,
    "elevation_weight": 0.25,
    "load_weight": 0.20,
    "distance_weight": 0.20
  }
}
```

**範例響應**:
```json
{
  "success": true,
  "data": {
    "recommended_satellite": "STARLINK-5678",
    "decision_score": 87.3,
    "decision_factors": {
      "signal_strength": {
        "score": 0.89,
        "weight": 0.35,
        "contribution": 31.15
      },
      "elevation_angle": {
        "score": 0.76,
        "weight": 0.25,
        "contribution": 19.00
      },
      "load_balancing": {
        "score": 0.92,
        "weight": 0.20,
        "contribution": 18.40
      },
      "distance_optimization": {
        "score": 0.84,
        "weight": 0.20,
        "contribution": 16.80
      }
    },
    "execution_time_ms": 28.7,
    "confidence_level": "high",
    "alternative_candidates": [
      {
        "satellite_id": "STARLINK-9012",
        "decision_score": 82.1,
        "primary_advantage": "lower_load"
      }
    ]
  }
}
```

#### 換手歷史查詢
```http
GET /api/v1/handover_decision/history/{ue_id}
```

**參數**:
- `limit` (int, optional): 返回記錄數，預設50
- `start_time` (string, optional): 開始時間 (ISO 8601)
- `end_time` (string, optional): 結束時間 (ISO 8601)
- `success_only` (bool, optional): 僅成功的換手記錄

**範例響應**:
```json
{
  "success": true,
  "data": {
    "ue_id": "UE_12345",
    "handover_history": [
      {
        "timestamp": "2025-08-18T12:00:00Z",
        "source_satellite": "STARLINK-1234",
        "target_satellite": "STARLINK-5678",
        "decision_score": 87.3,
        "trigger_events": ["A4", "D2"],
        "success": true,
        "actual_latency_ms": 32.4,
        "signal_improvement_db": 8.2,
        "handover_duration_ms": 156
      }
    ],
    "statistics": {
      "total_handovers": 156,
      "successful_handovers": 149,
      "success_rate": 0.955,
      "average_latency_ms": 28.7,
      "average_signal_improvement_db": 6.8
    },
    "query_period": {
      "start": "2025-08-17T12:00:00Z",
      "end": "2025-08-18T12:00:00Z",
      "duration_hours": 24
    }
  }
}
```

### ML預測API

#### 換手預測
```http
POST /api/v1/ml_prediction/predict_handover
```

**請求格式**:
```json
{
  "ue_context": {
    "ue_id": "UE_12345",
    "current_satellite": "STARLINK-1234",
    "trajectory": [
      {
        "timestamp": "2025-08-18T12:00:00Z",
        "latitude": 24.9441667,
        "longitude": 121.3713889,
        "velocity_ms": 15.6,
        "heading_deg": 45.0
      }
    ],
    "service_history": {
      "recent_handovers": 3,
      "average_session_duration_minutes": 8.5
    }
  },
  "prediction_config": {
    "horizon_minutes": 10,
    "model_type": "lstm_transformer_ensemble",
    "confidence_threshold": 0.75
  }
}
```

**範例響應**:
```json
{
  "success": true,
  "data": {
    "predicted_handovers": [
      {
        "predicted_time": "2025-08-18T12:05:30Z",
        "source_satellite": "STARLINK-1234",
        "target_satellite": "STARLINK-5678",
        "confidence": 0.92,
        "trigger_reason": "elevation_degradation",
        "predicted_improvement": {
          "signal_gain_db": 7.3,
          "elevation_gain_deg": 15.2
        }
      }
    ],
    "model_performance": {
      "ensemble_accuracy": 0.94,
      "lstm_confidence": 0.91,
      "transformer_confidence": 0.96,
      "prediction_time_ms": 67.8
    },
    "risk_assessment": {
      "handover_complexity": "medium",
      "success_probability": 0.89,
      "potential_service_interruption_ms": 45
    }
  }
}
```

#### ML模型性能監控
```http
GET /api/v1/ml_prediction/model_performance
```

**範例響應**:
```json
{
  "success": true,
  "data": {
    "models": {
      "lstm_predictor": {
        "accuracy": 0.91,
        "precision": 0.89,
        "recall": 0.93,
        "f1_score": 0.91,
        "training_data_points": 15420,
        "last_trained": "2025-08-18T08:00:00Z",
        "model_version": "v2.1.3"
      },
      "transformer_predictor": {
        "accuracy": 0.96,
        "precision": 0.94,
        "recall": 0.97,
        "f1_score": 0.96,
        "training_data_points": 15420,
        "last_trained": "2025-08-18T07:30:00Z",
        "model_version": "v1.2.1"
      },
      "ensemble_model": {
        "accuracy": 0.94,
        "ensemble_weights": [0.6, 0.4],
        "prediction_latency_ms": 23.4
      }
    },
    "training_metrics": {
      "total_training_sessions": 24,
      "last_evaluation": "2025-08-18T09:00:00Z",
      "next_retraining_due": "2025-08-19T08:00:00Z"
    }
  }
}
```

### 時間同步API

#### 同步狀態查詢
```http
GET /api/v1/time_sync/status
```

**範例響應**:
```json
{
  "success": true,
  "data": {
    "sync_status": "synchronized",
    "time_accuracy_us": 0.85,
    "frequency_stability_ppb": 0.05,
    "reference_sources": [
      {
        "source": "gps",
        "status": "active",
        "accuracy_us": 0.1,
        "last_sync": "2025-08-18T11:59:45Z",
        "signal_strength": "excellent"
      },
      {
        "source": "ntp_pool",
        "status": "backup",
        "accuracy_us": 2.5,
        "servers": ["time.google.com", "pool.ntp.org"],
        "last_sync": "2025-08-18T11:58:30Z"
      },
      {
        "source": "ptp",
        "status": "standby",
        "accuracy_us": 0.01,
        "master_clock": "192.168.1.100"
      }
    ],
    "synchronization_history": {
      "last_calibration": "2025-08-18T11:45:00Z",
      "calibration_success_rate": 0.99,
      "average_drift_correction_us": 1.2
    }
  }
}
```

#### 都卜勒頻率補償
```http
GET /api/v1/time_sync/doppler_compensation/{satellite_id}
```

**參數**:
- `ue_location` (string, required): UE位置 "lat,lon,alt"
- `timestamp` (string, optional): 計算時間點
- `frequency_mhz` (float, optional): 載波頻率，預設12000 (Ku頻段)

**範例請求**:
```bash
curl "http://localhost:8080/api/v1/time_sync/doppler_compensation/STARLINK-1234?ue_location=24.9441,121.3714,24&frequency_mhz=12000"
```

**範例響應**:
```json
{
  "success": true,
  "data": {
    "satellite_id": "STARLINK-1234",
    "satellite_name": "STARLINK-1007",
    "doppler_analysis": {
      "doppler_shift_hz": -1250.3,
      "frequency_correction_hz": 1250.3,
      "relative_velocity_ms": -7234.5,
      "radial_acceleration_ms2": -0.85
    },
    "geometry": {
      "satellite_elevation_deg": 45.7,
      "satellite_azimuth_deg": 152.3,
      "slant_range_km": 589.2,
      "range_rate_ms": -7234.5
    },
    "frequency_compensation": {
      "original_frequency_mhz": 12000.0,
      "compensated_frequency_mhz": 11998.75,
      "correction_ppm": -1.04
    },
    "calculation_metadata": {
      "timestamp": "2025-08-18T12:00:00Z",
      "calculation_accuracy": "high",
      "sgp4_precision": "full_model"
    }
  }
}
```

### 狀態同步API

#### 分散式狀態創建
```http
POST /api/v1/state_sync/create_state
```

**請求格式**:
```json
{
  "state_id": "ue_context_12345",
  "state_type": "user_context",
  "data": {
    "ue_id": "UE_12345",
    "current_satellite": "STARLINK-1234",
    "session_info": {
      "start_time": "2025-08-18T11:30:00Z",
      "service_class": "enhanced_mobile_broadband",
      "qos_requirements": {
        "min_throughput_mbps": 10,
        "max_latency_ms": 50
      }
    },
    "handover_history": [],
    "location_track": []
  },
  "consistency_level": "eventual",
  "ttl_seconds": 3600,
  "replication_factor": 3
}
```

#### 狀態查詢
```http
GET /api/v1/state_sync/get_state/{state_id}
```

**範例響應**:
```json
{
  "success": true,
  "data": {
    "state_id": "ue_context_12345",
    "state_type": "user_context",
    "data": {
      "ue_id": "UE_12345",
      "current_satellite": "STARLINK-1234",
      "session_info": {...}
    },
    "metadata": {
      "version": 7,
      "last_updated": "2025-08-18T12:00:00Z",
      "consistency_level": "eventual",
      "replication_status": {
        "total_nodes": 3,
        "synchronized_nodes": 3,
        "sync_percentage": 100.0
      }
    },
    "cluster_info": {
      "primary_node": "node_1",
      "replica_nodes": ["node_2", "node_3"],
      "last_consensus": "2025-08-18T11:59:58Z"
    }
  }
}
```

#### 狀態列表查詢
```http
GET /api/v1/state_sync/list_states
```

**參數**:
- `state_type` (string, optional): 狀態類型過濾
- `limit` (int, optional): 返回數量限制
- `include_data` (bool, optional): 是否包含狀態數據

**範例響應**:
```json
{
  "success": true,
  "data": {
    "states": [
      {
        "state_id": "ue_context_12345",
        "state_type": "user_context",
        "version": 7,
        "last_updated": "2025-08-18T12:00:00Z",
        "size_bytes": 2048,
        "sync_status": "synchronized"
      }
    ],
    "total_states": 156,
    "cluster_statistics": {
      "total_memory_mb": 45.6,
      "states_per_type": {
        "user_context": 89,
        "satellite_state": 45,
        "network_topology": 22
      }
    }
  }
}
```

### 性能監控API

#### 算法性能指標
```http
GET /api/v1/performance/algorithm_metrics
```

**參數**:
- `algorithm` (string, optional): 算法名稱過濾
- `start_time` (string, optional): 開始時間
- `end_time` (string, optional): 結束時間
- `granularity` (string, optional): 數據粒度 ("1m", "5m", "1h")

**範例響應**:
```json
{
  "success": true,
  "data": {
    "handover_performance": {
      "decision_latency": {
        "average_ms": 28.7,
        "median_ms": 25.3,
        "p95_ms": 45.2,
        "p99_ms": 67.8,
        "sample_count": 2456
      },
      "success_metrics": {
        "total_handovers": 2456,
        "successful_handovers": 2398,
        "success_rate": 0.976,
        "failure_reasons": {
          "signal_degradation": 23,
          "network_congestion": 18,
          "timeout": 17
        }
      }
    },
    "ml_prediction_performance": {
      "models": {
        "lstm_predictor": {
          "accuracy": 0.94,
          "prediction_latency_ms": 15.6,
          "memory_usage_mb": 128.5
        },
        "transformer_predictor": {
          "accuracy": 0.96,
          "prediction_latency_ms": 23.4,
          "memory_usage_mb": 256.8
        }
      }
    },
    "system_resources": {
      "cpu_usage_percent": 18.7,
      "memory_usage_mb": 1024.3,
      "disk_io_mbps": 15.6,
      "network_throughput_mbps": 45.2,
      "active_connections": 23
    },
    "time_window": {
      "start": "2025-08-18T11:00:00Z",
      "end": "2025-08-18T12:00:00Z",
      "duration_minutes": 60
    }
  }
}
```

#### 研究數據匯出
```http
POST /api/v1/performance/export_research_data
```

**請求格式**:
```json
{
  "experiment_config": {
    "experiment_name": "handover_algorithm_comparison_v3",
    "description": "Compare fine-grained vs traditional handover algorithms",
    "researcher": "Dr. Smith",
    "institution": "NTPU"
  },
  "data_selection": {
    "start_time": "2025-08-18T10:00:00Z",
    "end_time": "2025-08-18T14:00:00Z",
    "metrics": [
      "handover_latency",
      "success_rate", 
      "prediction_accuracy",
      "signal_quality_improvements"
    ],
    "algorithms": ["fine_grained", "traditional", "ml_driven"]
  },
  "export_format": {
    "format": "csv",
    "include_metadata": true,
    "statistical_summary": true,
    "visualization_charts": false
  }
}
```

**範例響應**:
```json
{
  "success": true,
  "data": {
    "export_job_id": "exp_67890",
    "status": "completed",
    "file_info": {
      "filename": "handover_algorithm_comparison_v3_20250818.csv",
      "file_size_mb": 12.5,
      "record_count": 45600,
      "download_url": "/api/v1/performance/download/exp_67890",
      "expires_at": "2025-08-25T12:00:00Z"
    },
    "data_summary": {
      "algorithms_compared": 3,
      "total_handovers": 15200,
      "time_span_hours": 4,
      "statistical_tests": ["t-test", "ANOVA", "Mann-Whitney U"]
    },
    "export_metadata": {
      "export_time": "2025-08-18T12:00:00Z",
      "data_integrity_hash": "sha256:abc123...",
      "ieee_compliance": true
    }
  }
}
```

## 🚨 錯誤處理與狀態碼

### HTTP狀態碼對應
```http
200 OK                    # 請求成功
201 Created               # 資源創建成功  
400 Bad Request           # 請求參數錯誤
401 Unauthorized          # 認證失敗 (生產環境)
403 Forbidden             # 權限不足
404 Not Found             # 資源不存在
422 Unprocessable Entity  # 請求格式正確但邏輯錯誤
425 Too Early             # 數據尚未準備完成
500 Internal Server Error # 服務器內部錯誤
503 Service Unavailable   # 服務暫時不可用
```

### 標準錯誤響應格式
```json
{
  "success": false,
  "error": {
    "code": "INVALID_SATELLITE_ID",
    "message": "提供的衛星ID不存在或格式錯誤",
    "details": {
      "parameter": "satellite_id",
      "provided_value": "INVALID-9999",
      "expected_format": "NORAD ID (integer) or STARLINK-XXXX format",
      "valid_range": "1-99999 for NORAD ID"
    },
    "suggestion": "請檢查衛星ID格式，或使用 /api/v1/satellites/constellations/info 查看可用衛星"
  },
  "timestamp": "2025-08-18T12:00:00Z",
  "request_id": "req_1692345678",
  "api_version": "3.0.0"
}
```

### 常見錯誤碼參考
| 錯誤碼 | HTTP狀態 | 說明 | 解決方案 |
|--------|----------|------|----------|
| `INVALID_PARAMETERS` | 400 | 請求參數無效或缺失 | 檢查API文檔中的必填參數 |
| `SATELLITE_NOT_FOUND` | 404 | 指定衛星ID不存在 | 使用星座信息API查詢有效衛星 |
| `CONSTELLATION_INVALID` | 400 | 星座名稱無效 | 支援的值: "starlink", "oneweb" |
| `ELEVATION_OUT_OF_RANGE` | 400 | 仰角參數超出範圍 | 有效範圍: 0-90度 |
| `TIMESTAMP_FORMAT_ERROR` | 400 | 時間戳格式錯誤 | 使用ISO 8601格式 |
| `SERVICE_UNAVAILABLE` | 503 | 後端服務不可用 | 檢查服務健康狀態或稍後重試 |
| `CALCULATION_TIMEOUT` | 500 | 軌道計算超時 | 減少查詢範圍或聯繫系統管理員 |
| `ML_MODEL_NOT_READY` | 425 | ML模型尚未完成載入 | 等待模型初始化完成 |
| `DATA_NOT_FRESH` | 425 | TLE數據過舊 | 等待數據更新或檢查Cron調度 |

## 🔧 API使用最佳實踐

### 1. 錯誤重試策略
```python
import time
import requests
from typing import Optional

class NTNStackAPIClient:
    def __init__(self, netstack_url="http://localhost:8080", simworld_url="http://localhost:8888"):
        self.netstack_url = netstack_url
        self.simworld_url = simworld_url
    
    def api_call_with_retry(self, url: str, max_retries: int = 3, backoff_factor: float = 1.0) -> Optional[dict]:
        """帶指數退避的API調用重試"""
        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise e
                
                wait_time = backoff_factor * (2 ** attempt)
                print(f"API調用失敗，{wait_time}秒後重試... (嘗試 {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
        
        return None
```

### 2. 批次查詢優化
```python
async def batch_satellite_queries(timestamps: list, constellation: str = "starlink"):
    """異步批次查詢多個時間點的衛星數據"""
    import asyncio
    import aiohttp
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for timestamp in timestamps:
            url = f"http://localhost:8888/api/v1/satellites/visible_satellites"
            params = {
                "utc_timestamp": timestamp,
                "constellation": constellation,
                "count": 10,
                "min_elevation_deg": 10.0
            }
            task = fetch_satellite_data(session, url, params)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

async def fetch_satellite_data(session, url, params):
    async with session.get(url, params=params) as response:
        if response.status == 200:
            return await response.json()
        else:
            return {"error": f"HTTP {response.status}"}
```

### 3. 響應時間監控
```python
import time
import logging
from functools import wraps

def monitor_api_performance(func):
    """API性能監控裝飾器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # 記錄正常調用
            logging.info(f"{func.__name__} 執行時間: {execution_time:.3f}秒")
            
            # 性能警告門檻
            if execution_time > 5.0:
                logging.warning(f"{func.__name__} 響應時間過長: {execution_time:.3f}秒")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logging.error(f"{func.__name__} 執行失敗 (耗時 {execution_time:.3f}秒): {e}")
            raise
    
    return wrapper

@monitor_api_performance
def get_handover_decision(serving_satellite_id: str, constellation: str = "starlink"):
    """監控換手決策API調用性能"""
    url = f"http://localhost:8080/api/v1/satellite-ops/evaluate_handover"
    params = {
        "serving_satellite_id": serving_satellite_id,
        "constellation": constellation,
        "count": 8,
        "min_elevation_deg": 10.0
    }
    response = requests.post(url, params=params)
    return response.json()
```

### 4. 數據緩存策略
```python
import time
from typing import Dict, Any
import hashlib
import json

class APIResponseCache:
    """API響應緩存系統"""
    
    def __init__(self, ttl_seconds: int = 300):  # 5分鐘TTL
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl_seconds = ttl_seconds
    
    def _generate_cache_key(self, url: str, params: Dict) -> str:
        """生成緩存鍵"""
        cache_data = {"url": url, "params": sorted(params.items())}
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def get(self, url: str, params: Dict) -> Optional[Dict]:
        """從緩存獲取數據"""
        key = self._generate_cache_key(url, params)
        
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry["timestamp"] < self.ttl_seconds:
                return entry["data"]
            else:
                # 過期數據清理
                del self.cache[key]
        
        return None
    
    def set(self, url: str, params: Dict, data: Dict):
        """設置緩存數據"""
        key = self._generate_cache_key(url, params)
        self.cache[key] = {
            "data": data,
            "timestamp": time.time()
        }
    
    def clear_expired(self):
        """清理過期緩存"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time - entry["timestamp"] >= self.ttl_seconds
        ]
        
        for key in expired_keys:
            del self.cache[key]

# 使用範例
cache = APIResponseCache(ttl_seconds=300)

def cached_api_call(url: str, params: Dict) -> Dict:
    """帶緩存的API調用"""
    # 先嘗試從緩存獲取
    cached_result = cache.get(url, params)
    if cached_result:
        return cached_result
    
    # 緩存未命中，調用實際API
    response = requests.get(url, params=params)
    result = response.json()
    
    # 成功響應才緩存
    if response.status_code == 200 and result.get("success"):
        cache.set(url, params, result)
    
    return result
```

## 📚 SDK與開發工具

### Python SDK設計 (概念)
```python
from typing import List, Dict, Optional
import requests

class NTNStackSDK:
    """NTN Stack Python SDK"""
    
    def __init__(self, netstack_url="http://localhost:8080", simworld_url="http://localhost:8888"):
        self.netstack = NetStackClient(netstack_url)
        self.simworld = SimWorldClient(simworld_url)
    
    # 高層API設計
    def get_handover_recommendation(self, ue_id: str, current_satellite: str) -> Dict:
        """獲取換手建議的高層API"""
        return self.netstack.evaluate_handover(
            serving_satellite_id=current_satellite,
            count=8,
            min_elevation_deg=10.0
        )
    
    def get_visible_satellites(self, constellation: str = "starlink", count: int = 10) -> List[Dict]:
        """獲取可見衛星的便捷方法"""
        response = self.simworld.get_satellites(
            constellation=constellation,
            count=count,
            min_elevation_deg=5.0
        )
        return response.get("data", {}).get("satellites", [])
    
    def monitor_handover_performance(self, duration_hours: int = 1) -> Dict:
        """監控換手性能指標"""
        return self.netstack.get_performance_metrics(
            start_time=datetime.utcnow() - timedelta(hours=duration_hours),
            end_time=datetime.utcnow()
        )

class NetStackClient:
    """NetStack API 客戶端"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
    
    def evaluate_handover(self, serving_satellite_id: str, **kwargs) -> Dict:
        """換手評估API封裝"""
        url = f"{self.base_url}/api/v1/satellite-ops/evaluate_handover"
        params = {"serving_satellite_id": serving_satellite_id, **kwargs}
        
        response = requests.post(url, params=params)
        response.raise_for_status()
        return response.json()

class SimWorldClient:
    """SimWorld API 客戶端"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
    
    def get_satellites(self, **kwargs) -> Dict:
        """衛星查詢API封裝"""
        url = f"{self.base_url}/api/v1/satellites/visible_satellites"
        
        response = requests.get(url, params=kwargs)
        response.raise_for_status()
        return response.json()
```

### 命令列工具設計 (概念)
```bash
# CLI工具使用範例
ntn-cli --help
# NTN Stack Command Line Interface v3.0.0

# 衛星查詢
ntn-cli satellites list --constellation starlink --count 10 --min-elevation 10

# 換手評估  
ntn-cli handover evaluate --serving-satellite STARLINK-1234 --constellation starlink

# 性能監控
ntn-cli performance report --duration 1h --algorithm handover_decision

# 系統健康檢查
ntn-cli health check --services all

# 數據匯出
ntn-cli export research --experiment "algorithm_comparison" --format csv --start "2025-08-18T10:00:00Z"
```

---

**本API參考手冊提供了NTN Stack系統的完整API接口文檔，確保研究實驗和系統整合的技術基礎支援。**

*最後更新：2025-08-18 | API參考手冊版本 3.0.0*