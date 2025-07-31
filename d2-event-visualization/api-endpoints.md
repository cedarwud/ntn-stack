# D2 Event API Endpoints Specification

## Overview

This document defines the new API endpoints required to support D2 event visualization with real satellite data.

## Base Configuration

### API Base URLs
```typescript
// NetStack API (Backend)
const NETSTACK_BASE = 'http://localhost:8080/api/v1';

// SimWorld API (3D Engine)
const SIMWORLD_BASE = 'http://localhost:8888/api/v1';
```

## New Endpoints

### 1. D2 Event Time Series Data

#### `GET /satellites/d2/timeseries`

Retrieve preprocessed D2 event data with moving reference locations.

**Request Parameters:**
```typescript
interface D2TimeSeriesRequest {
  constellation: 'starlink' | 'oneweb' | 'all';
  startTime?: string;        // ISO 8601, default: now
  endTime?: string;          // ISO 8601, default: now + 120min
  servingSatellite?: string; // Specific satellite ID
  resolution?: number;       // Seconds between points (default: 10)
}
```

**Response:**
```typescript
interface D2TimeSeriesResponse {
  metadata: {
    constellation: string;
    timeRange: {
      start: string;
      end: string;
    };
    dataPoints: number;
    satellites: {
      serving: string;
      candidates: string[];
    };
  };
  
  timeSeries: {
    timestamps: string[];
    
    servingSatellite: {
      id: string;
      name: string;
      positions: SatellitePosition[];
      mrlDistances: number[];      // Distance to MRL in km
      elevations: number[];        // Elevation angles
    };
    
    targetSatellites: Array<{
      id: string;
      name: string;
      positions: SatellitePosition[];
      mrlDistances: number[];
      elevations: number[];
      handoverScore: number;       // Suitability score 0-100
    }>;
  };
  
  d2Events: D2Event[];
}

interface SatellitePosition {
  lat: number;
  lon: number;
  alt_km: number;
  mrl: {
    lat: number;
    lon: number;
  };
}

interface D2Event {
  id: string;
  timestamp: string;
  type: 'entering' | 'leaving';
  servingSatellite: string;
  targetSatellite: string;
  ml1_km: number;
  ml2_km: number;
  duration_seconds?: number;
  thresholds: {
    thresh1: number;
    thresh2: number;
    hysteresis: number;
  };
}
```

**Example Request:**
```bash
curl -X GET "http://localhost:8080/api/v1/satellites/d2/timeseries?constellation=starlink&resolution=10"
```

### 2. Real-time D2 Event Detection

#### `POST /satellites/d2/detect`

Detect D2 events based on custom thresholds and parameters.

**Request Body:**
```typescript
interface D2DetectionRequest {
  timeRange: {
    start: string;
    end: string;
  };
  
  thresholds: {
    thresh1: number;          // Default: 500 km
    thresh2: number;          // Default: 300 km
    hysteresis: number;       // Default: 20 km
  };
  
  satellites: {
    serving: string;          // Satellite ID
    candidates?: string[];    // Optional: limit target satellites
  };
  
  ueLocation: {
    lat: number;
    lon: number;
    alt_m?: number;
  };
}
```

**Response:**
```typescript
interface D2DetectionResponse {
  detectedEvents: D2Event[];
  
  statistics: {
    totalEvents: number;
    averageDuration: number;
    peakEventTime: string;
    candidateSatellites: number;
  };
  
  recommendations: {
    optimalThresh1: number;
    optimalThresh2: number;
    reason: string;
  };
}
```

### 3. D2 Event Configuration

#### `GET /satellites/d2/config`

Retrieve current D2 event detection configuration.

**Response:**
```typescript
interface D2ConfigResponse {
  defaultThresholds: {
    thresh1: number;
    thresh2: number;
    hysteresis: number;
  };
  
  preprocessingConfig: {
    updateInterval: number;    // Seconds
    lookaheadTime: number;    // Minutes
    mrlCalculation: 'nadir' | 'custom';
  };
  
  supportedConstellations: Array<{
    name: string;
    satelliteCount: number;
    averageAltitude: number;
  }>;
}
```

#### `PUT /satellites/d2/config`

Update D2 event detection configuration.

**Request Body:**
```typescript
interface D2ConfigUpdate {
  thresholds?: {
    thresh1?: number;
    thresh2?: number;
    hysteresis?: number;
  };
  
  preprocessingConfig?: {
    updateInterval?: number;
    lookaheadTime?: number;
  };
}
```

### 4. Moving Reference Location API

#### `GET /satellites/{satelliteId}/mrl`

Get current moving reference location for a specific satellite.

**Response:**
```typescript
interface MRLResponse {
  satelliteId: string;
  timestamp: string;
  
  satellitePosition: {
    lat: number;
    lon: number;
    alt_km: number;
    velocity_kmps: number;
  };
  
  movingReferenceLocation: {
    lat: number;
    lon: number;
    method: 'nadir' | 'projection' | 'custom';
  };
  
  coverage: {
    radius_km: number;
    area_km2: number;
  };
}
```

### 5. Batch D2 Analysis

#### `POST /satellites/d2/analyze`

Perform batch analysis of D2 events for research purposes.

**Request Body:**
```typescript
interface D2AnalysisRequest {
  scenarios: Array<{
    name: string;
    thresholds: {
      thresh1: number;
      thresh2: number;
      hysteresis: number;
    };
  }>;
  
  timeRange: {
    start: string;
    end: string;
  };
  
  metrics: Array<'event_count' | 'avg_duration' | 'coverage_gaps' | 'handover_success_rate'>;
}
```

**Response:**
```typescript
interface D2AnalysisResponse {
  results: Array<{
    scenario: string;
    metrics: {
      eventCount: number;
      averageDuration: number;
      coverageGaps: Array<{
        start: string;
        end: string;
        duration_seconds: number;
      }>;
      handoverSuccessRate: number;
    };
    
    visualization: {
      chartData: any;         // Pre-formatted for charts
      heatmapData: any;      // Geographic distribution
    };
  }>;
  
  comparison: {
    optimal: string;          // Best scenario name
    reasoning: string;
  };
}
```

## WebSocket Endpoints

### Real-time D2 Event Stream

#### `WS /satellites/d2/stream`

Stream real-time D2 events as they occur.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8080/api/v1/satellites/d2/stream');

// Subscribe to specific satellites
ws.send(JSON.stringify({
  action: 'subscribe',
  satellites: ['starlink-1234', 'starlink-5678'],
  thresholds: {
    thresh1: 500,
    thresh2: 300,
    hysteresis: 20
  }
}));
```

**Message Format:**
```typescript
interface D2StreamMessage {
  type: 'event' | 'update' | 'status';
  timestamp: string;
  
  // For type: 'event'
  event?: D2Event;
  
  // For type: 'update'
  update?: {
    satelliteId: string;
    ml_km: number;
    mrl: { lat: number; lon: number };
  };
  
  // For type: 'status'
  status?: {
    connected: boolean;
    subscribedSatellites: string[];
  };
}
```

## Frontend API Client

### TypeScript API Client Implementation

```typescript
// api/d2EventApi.ts
import { ApiClient } from '../utils/apiClient';

export class D2EventApi {
  private client: ApiClient;
  
  constructor(baseUrl: string) {
    this.client = new ApiClient(baseUrl);
  }
  
  async getTimeSeries(params: D2TimeSeriesRequest): Promise<D2TimeSeriesResponse> {
    return this.client.get('/satellites/d2/timeseries', { params });
  }
  
  async detectEvents(request: D2DetectionRequest): Promise<D2DetectionResponse> {
    return this.client.post('/satellites/d2/detect', request);
  }
  
  async getConfig(): Promise<D2ConfigResponse> {
    return this.client.get('/satellites/d2/config');
  }
  
  async updateConfig(config: D2ConfigUpdate): Promise<void> {
    return this.client.put('/satellites/d2/config', config);
  }
  
  async getMRL(satelliteId: string): Promise<MRLResponse> {
    return this.client.get(`/satellites/${satelliteId}/mrl`);
  }
  
  async analyzeScenarios(request: D2AnalysisRequest): Promise<D2AnalysisResponse> {
    return this.client.post('/satellites/d2/analyze', request);
  }
  
  connectToStream(onMessage: (msg: D2StreamMessage) => void): WebSocket {
    const ws = new WebSocket(`${this.client.wsUrl}/satellites/d2/stream`);
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data) as D2StreamMessage;
      onMessage(message);
    };
    
    return ws;
  }
}

// Usage
const d2Api = new D2EventApi(NETSTACK_BASE);
const timeSeries = await d2Api.getTimeSeries({
  constellation: 'starlink',
  resolution: 10
});
```

## Error Handling

### Standard Error Response
```typescript
interface ApiError {
  error: {
    code: string;
    message: string;
    details?: any;
  };
  timestamp: string;
  path: string;
}
```

### Common Error Codes
- `D2_001`: Invalid threshold parameters
- `D2_002`: No satellites found for given criteria
- `D2_003`: Time range exceeds maximum allowed (24 hours)
- `D2_004`: Preprocessing data not available
- `D2_005`: Invalid satellite ID

## Performance Considerations

### Caching Strategy
```typescript
// Cache preprocessed data for 5 minutes
app.get('/satellites/d2/timeseries', 
  cache('5 minutes'),
  async (req, res) => {
    // Handler implementation
  }
);
```

### Rate Limiting
```typescript
// Limit analysis endpoints to prevent abuse
const analysisLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 10 // limit each IP to 10 requests per window
});

app.post('/satellites/d2/analyze', analysisLimiter, handler);
```

### Pagination
```typescript
// For large result sets
interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    pageSize: number;
    totalItems: number;
    totalPages: number;
  };
}
```

## Migration Plan

### Phase 1: Deploy new endpoints alongside existing
- Add D2-specific endpoints
- Keep existing endpoints unchanged
- Test with limited users

### Phase 2: Frontend integration
- Update frontend to use new endpoints
- Add feature flags for gradual rollout
- Monitor performance metrics

### Phase 3: Deprecate old endpoints
- Mark old endpoints as deprecated
- Provide migration guide
- Set sunset date

## Testing Strategy

### Unit Tests
```typescript
describe('D2 Event API', () => {
  it('should detect D2 events correctly', async () => {
    const result = await request(app)
      .post('/api/v1/satellites/d2/detect')
      .send({
        thresholds: { thresh1: 500, thresh2: 300, hysteresis: 20 },
        // ... other params
      });
      
    expect(result.status).toBe(200);
    expect(result.body.detectedEvents).toHaveLength(3);
  });
});
```

### Integration Tests
- Test with real preprocessed data
- Verify WebSocket streaming
- Check cache behavior
- Validate error scenarios

## Next Steps

1. Implement core D2 timeseries endpoint
2. Add MRL calculation to existing services
3. Create WebSocket streaming infrastructure
4. Build frontend API client
5. Add comprehensive logging
6. Deploy to staging environment