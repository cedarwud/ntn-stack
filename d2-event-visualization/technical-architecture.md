# D2 Event Visualization Technical Architecture

## System Overview

The D2 Event Visualization system integrates real satellite data processing with interactive visualization components to demonstrate 3GPP D2 handover events.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Data Pipeline                                │
├─────────────────┬──────────────────┬───────────────────────────────┤
│   TLE Source    │   Preprocessing   │    Enhanced Data              │
│                 │                   │                               │
│ ┌─────────────┐ │ ┌───────────────┐ │ ┌───────────────────────────┐ │
│ │Space-Track  │ │ │SGP4 Calculator│ │ │ MRL Calculator          │ │
│ │   TLE API   ├─┼─►  Orbit Prop   ├─┼─► Nadir Projection        │ │
│ └─────────────┘ │ └───────────────┘ │ │ D2 Event Detection      │ │
│                 │                   │ └───────────────────────────┘ │
└─────────────────┴──────────────────┴───────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Storage Layer                                │
├─────────────────┬──────────────────┬───────────────────────────────┤
│  Docker Volume  │   Redis Cache    │    PostgreSQL                 │
│                 │                   │                               │
│ ┌─────────────┐ │ ┌───────────────┐ │ ┌───────────────────────────┐ │
│ │Preprocessed │ │ │Real-time Data │ │ │ Historical Events       │ │
│ │JSON Files   │ │ │MRL Positions  │ │ │ Configuration          │ │
│ └─────────────┘ │ └───────────────┘ │ └───────────────────────────┘ │
└─────────────────┴──────────────────┴───────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         API Layer                                    │
├─────────────────┬──────────────────┬───────────────────────────────┤
│   REST APIs     │   WebSocket      │    GraphQL (Future)          │
│                 │                   │                               │
│ ┌─────────────┐ │ ┌───────────────┐ │ ┌───────────────────────────┐ │
│ │D2 TimeSeries│ │ │Event Stream   │ │ │ Unified Query          │ │
│ │MRL Data     │ │ │Real-time MRL  │ │ │ Subscription           │ │
│ │Config       │ │ │Handover Alert │ │ │                        │ │
│ └─────────────┘ │ └───────────────┘ │ └───────────────────────────┘ │
└─────────────────┴──────────────────┴───────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Frontend Components                             │
├─────────────────┬──────────────────┬───────────────────────────────┤
│  D2 Event Chart │   3D Globe       │    Control Panel              │
│                 │                   │                               │
│ ┌─────────────┐ │ ┌───────────────┐ │ ┌───────────────────────────┐ │
│ │Distance Plot│ │ │Satellite Viz  │ │ │ Timeline Control        │ │
│ │Threshold    │ │ │MRL Markers    │ │ │ Threshold Adjust       │ │
│ │Event Markers│ │ │Handover Anim  │ │ │ Mode Selection         │ │
│ └─────────────┘ │ └───────────────┘ │ └───────────────────────────┘ │
└─────────────────┴──────────────────┴───────────────────────────────┘
```

## Component Details

### 1. Data Processing Pipeline

#### TLE Data Ingestion
```python
# /netstack/src/services/satellite/tle_ingestion.py
class TLEIngestionService:
    def __init__(self):
        self.sources = {
            'spacetrack': SpaceTrackClient(),
            'celestrak': CelestrakClient(),
            'local': LocalTLELoader()
        }
        
    async def fetch_constellation_tle(self, constellation: str) -> List[TLE]:
        """Fetch latest TLE data with fallback strategy"""
        try:
            # Try primary source
            return await self.sources['local'].get_tle_data(constellation)
        except Exception:
            # Fallback to cached data
            return self.load_cached_tle(constellation)
```

#### SGP4 Orbit Propagation
```python
# /simworld/backend/app/services/sgp4_calculator.py
class EnhancedSGP4Calculator:
    def propagate_with_mrl(self, tle: TLE, timestamp: datetime) -> dict:
        """Propagate orbit and calculate MRL"""
        # Standard SGP4 propagation
        position, velocity = self.propagate_sgp4(tle, timestamp)
        
        # Calculate nadir point (MRL)
        mrl = self.calculate_nadir_point(position)
        
        # Additional calculations for D2
        coverage_radius = self.calculate_coverage_radius(position.altitude)
        doppler_shift = self.calculate_doppler(velocity, position)
        
        return {
            'position': position,
            'velocity': velocity,
            'mrl': mrl,
            'coverage_radius': coverage_radius,
            'doppler_shift': doppler_shift
        }
```

#### D2 Event Detection Engine
```python
# /netstack/src/services/d2_event_detector.py
class D2EventDetector:
    def __init__(self, thresholds: D2Thresholds):
        self.thresholds = thresholds
        self.state_machine = D2StateMachine()
        
    def detect_events(self, 
                     time_series: TimeSeries,
                     serving: Satellite,
                     candidates: List[Satellite]) -> List[D2Event]:
        """Detect D2 events in time series data"""
        events = []
        
        for timestamp, data in time_series:
            # Calculate distances to MRL
            ml1 = self.calculate_mrl_distance(serving, data.ue_position)
            
            for target in candidates:
                ml2 = self.calculate_mrl_distance(target, data.ue_position)
                
                # Check D2 conditions
                event = self.state_machine.process(
                    timestamp, ml1, ml2, 
                    serving.id, target.id
                )
                
                if event:
                    events.append(event)
                    
        return events
```

### 2. State Management

#### Global Timeline State
```typescript
// /simworld/frontend/src/stores/timelineStore.ts
interface TimelineState {
  currentTime: Date;
  startTime: Date;
  endTime: Date;
  playbackSpeed: number;
  isPlaying: boolean;
  events: D2Event[];
}

export const timelineStore = create<TimelineState>((set, get) => ({
  currentTime: new Date(),
  startTime: new Date(),
  endTime: new Date(Date.now() + 120 * 60 * 1000),
  playbackSpeed: 1,
  isPlaying: false,
  events: [],
  
  setTime: (time: Date) => {
    set({ currentTime: time });
    // Notify all subscribers
    eventBus.emit('timeChanged', time);
  },
  
  play: () => {
    set({ isPlaying: true });
    startPlaybackLoop(get);
  },
  
  pause: () => {
    set({ isPlaying: false });
  }
}));
```

#### D2 Visualization State
```typescript
// /simworld/frontend/src/stores/d2VisualizationStore.ts
interface D2VisualizationState {
  mode: 'real' | 'simulated' | 'hybrid';
  selectedSatellites: {
    serving: string | null;
    target: string | null;
  };
  thresholds: {
    thresh1: number;
    thresh2: number;
    hysteresis: number;
  };
  activeEvent: D2Event | null;
  chartConfig: ChartConfiguration;
  globeConfig: GlobeConfiguration;
}
```

### 3. Real-time Data Flow

#### WebSocket Architecture
```typescript
// /simworld/backend/websocket/d2_stream.ts
export class D2StreamManager {
  private connections: Map<string, WebSocket> = new Map();
  private updateInterval: NodeJS.Timer;
  
  constructor(private dataService: D2DataService) {
    this.startUpdateLoop();
  }
  
  handleConnection(ws: WebSocket, clientId: string) {
    this.connections.set(clientId, ws);
    
    ws.on('message', (msg) => {
      const request = JSON.parse(msg);
      this.handleClientRequest(clientId, request);
    });
    
    ws.on('close', () => {
      this.connections.delete(clientId);
    });
  }
  
  private startUpdateLoop() {
    this.updateInterval = setInterval(() => {
      this.broadcastUpdates();
    }, 100); // 10Hz updates
  }
  
  private async broadcastUpdates() {
    const updates = await this.dataService.getLatestUpdates();
    
    for (const [clientId, ws] of this.connections) {
      const clientData = this.filterForClient(updates, clientId);
      ws.send(JSON.stringify(clientData));
    }
  }
}
```

### 4. Performance Optimization

#### Data Caching Strategy
```typescript
// /simworld/backend/cache/d2_cache.ts
export class D2DataCache {
  private redis: Redis;
  private memoryCache: LRUCache<string, any>;
  
  constructor() {
    this.redis = new Redis(config.redis);
    this.memoryCache = new LRUCache({
      max: 100,
      ttl: 1000 * 60 * 5 // 5 minutes
    });
  }
  
  async get(key: string): Promise<any> {
    // L1: Memory cache
    const memResult = this.memoryCache.get(key);
    if (memResult) return memResult;
    
    // L2: Redis cache
    const redisResult = await this.redis.get(key);
    if (redisResult) {
      const data = JSON.parse(redisResult);
      this.memoryCache.set(key, data);
      return data;
    }
    
    return null;
  }
  
  async set(key: string, value: any, ttl: number = 300) {
    this.memoryCache.set(key, value);
    await this.redis.setex(key, ttl, JSON.stringify(value));
  }
}
```

#### Batch Processing
```python
# /simworld/backend/batch/d2_batch_processor.py
class D2BatchProcessor:
    def __init__(self, worker_count: int = 4):
        self.executor = ProcessPoolExecutor(max_workers=worker_count)
        self.queue = asyncio.Queue()
        
    async def process_constellation(self, constellation: str):
        """Process entire constellation in parallel"""
        satellites = await self.get_satellites(constellation)
        
        # Split into chunks for parallel processing
        chunks = [satellites[i:i+10] for i in range(0, len(satellites), 10)]
        
        # Process chunks in parallel
        futures = []
        for chunk in chunks:
            future = self.executor.submit(
                self.process_satellite_chunk, chunk
            )
            futures.append(future)
            
        # Collect results
        results = []
        for future in as_completed(futures):
            chunk_result = future.result()
            results.extend(chunk_result)
            
        return self.merge_results(results)
```

### 5. Frontend Architecture

#### Component Hierarchy
```
App
├── D2VisualizationLayout
│   ├── Header
│   │   └── ModeSelector
│   ├── MainView
│   │   ├── Globe3D
│   │   │   ├── SatelliteRenderer
│   │   │   ├── MRLRenderer
│   │   │   └── HandoverAnimator
│   │   └── D2EventChart
│   │       ├── DistanceLines
│   │       ├── ThresholdZones
│   │       └── EventMarkers
│   ├── Timeline
│   │   ├── PlaybackControls
│   │   ├── Scrubber
│   │   └── EventIndicators
│   └── SidePanel
│       ├── ThresholdControls
│       ├── SatelliteSelector
│       └── EventLog
```

#### Render Optimization
```typescript
// /simworld/frontend/src/hooks/useOptimizedRender.ts
export function useOptimizedRender<T>(
  data: T[],
  renderFn: (item: T) => void,
  options: RenderOptions = {}
) {
  const frameRef = useRef<number>();
  
  useEffect(() => {
    let index = 0;
    const batchSize = options.batchSize || 10;
    
    const renderBatch = () => {
      const batch = data.slice(index, index + batchSize);
      batch.forEach(renderFn);
      
      index += batchSize;
      
      if (index < data.length) {
        frameRef.current = requestAnimationFrame(renderBatch);
      }
    };
    
    renderBatch();
    
    return () => {
      if (frameRef.current) {
        cancelAnimationFrame(frameRef.current);
      }
    };
  }, [data]);
}
```

### 6. Deployment Architecture

#### Container Structure
```yaml
# docker-compose.yml
version: '3.8'

services:
  d2-preprocessor:
    build: ./d2-preprocessor
    volumes:
      - satellite-data:/app/data
    environment:
      - REDIS_URL=redis://redis:6379
      - UPDATE_INTERVAL=300
    depends_on:
      - redis
      
  d2-api:
    build: ./d2-api
    ports:
      - "8081:8080"
    volumes:
      - satellite-data:/app/data:ro
    environment:
      - DATABASE_URL=postgresql://...
      - CACHE_URL=redis://redis:6379
      
  d2-frontend:
    build: ./d2-frontend
    ports:
      - "3001:3000"
    environment:
      - REACT_APP_API_URL=http://d2-api:8080
      - REACT_APP_WS_URL=ws://d2-api:8080
      
  redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data
      
volumes:
  satellite-data:
  redis-data:
```

#### Scaling Strategy
```yaml
# kubernetes/d2-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: d2-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: d2-api
  template:
    spec:
      containers:
      - name: d2-api
        image: ntn-stack/d2-api:latest
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        env:
        - name: WORKER_PROCESSES
          value: "4"
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: d2-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: d2-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### 7. Monitoring and Observability

#### Metrics Collection
```typescript
// /simworld/backend/monitoring/metrics.ts
import { Counter, Histogram, register } from 'prom-client';

export const d2Metrics = {
  eventsDetected: new Counter({
    name: 'd2_events_detected_total',
    help: 'Total number of D2 events detected',
    labelNames: ['constellation', 'event_type']
  }),
  
  processingDuration: new Histogram({
    name: 'd2_processing_duration_seconds',
    help: 'D2 event processing duration',
    buckets: [0.1, 0.5, 1, 2, 5]
  }),
  
  apiLatency: new Histogram({
    name: 'd2_api_latency_seconds',
    help: 'API endpoint latency',
    labelNames: ['method', 'endpoint'],
    buckets: [0.01, 0.05, 0.1, 0.5, 1]
  })
};

// Register all metrics
Object.values(d2Metrics).forEach(metric => register.registerMetric(metric));
```

#### Logging Strategy
```python
# /netstack/src/utils/d2_logger.py
import structlog

logger = structlog.get_logger()

class D2Logger:
    @staticmethod
    def log_event_detection(event: D2Event, context: dict):
        logger.info(
            "d2_event_detected",
            event_id=event.id,
            timestamp=event.timestamp,
            serving_satellite=event.serving,
            target_satellite=event.target,
            ml1=event.ml1,
            ml2=event.ml2,
            duration=event.duration,
            **context
        )
        
    @staticmethod
    def log_performance(operation: str, duration: float, details: dict):
        logger.info(
            "performance_metric",
            operation=operation,
            duration_ms=duration * 1000,
            **details
        )
```

## Security Considerations

### API Security
```typescript
// Authentication middleware
export const authenticateD2Api = async (req, res, next) => {
  const token = req.headers.authorization?.split(' ')[1];
  
  if (!token) {
    return res.status(401).json({ error: 'Unauthorized' });
  }
  
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    req.user = decoded;
    next();
  } catch (error) {
    return res.status(403).json({ error: 'Invalid token' });
  }
};

// Rate limiting
export const d2RateLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 100,
  message: 'Too many requests from this IP'
});
```

## Integration Points

### Existing System Integration
1. **NetStack API**: Extend existing satellite endpoints
2. **SimWorld Frontend**: Add D2 visualization components
3. **Data Pipeline**: Enhance preprocessing with MRL calculation
4. **Authentication**: Use existing JWT system
5. **Monitoring**: Integrate with Prometheus/Grafana

### Future Extensions
1. **Machine Learning**: Predict D2 events
2. **Multi-constellation**: Cross-constellation handovers
3. **Network Simulation**: Full protocol stack simulation
4. **VR Support**: Immersive visualization
5. **Edge Computing**: Distributed processing

## Conclusion

This architecture provides a scalable, performant foundation for D2 event visualization that integrates seamlessly with the existing NTN Stack while adding significant new capabilities for research and education.