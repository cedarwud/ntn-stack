# Phase 3: 基礎架構開發與 API 整合

## 目標
建立支援 D2/A4/A5 事件的基礎 API 架構，為未來的強化學習整合預留介面，現階段專注於 NTPU 場景的規則式換手決策。

## 現階段實現重點

### 3.1 規則式換手決策引擎

基於 D2/A4/A5 事件的決策邏輯：

```python
class RuleBasedHandoverEngine:
    def __init__(self):
        self.current_serving = None
        self.event_queue = []
        self.handover_in_progress = False
        
    def process_event(self, event):
        """處理換手事件"""
        if event['type'] == 'd2':
            # D2: 緊急換手
            if event['time_to_los'] < 30:  # 30秒內將失去連線
                return self.execute_emergency_handover(event)
                
        elif event['type'] == 'a4':
            # A4: 機會性換手
            if not self.handover_in_progress:
                return self.evaluate_a4_handover(event)
                
        elif event['type'] == 'a5':
            # A5: 品質驅動換手
            if event['urgency'] == 'high':
                return self.execute_quality_handover(event)
                
        return None
    
    def execute_emergency_handover(self, d2_event):
        """執行緊急換手"""
        target = d2_event['recommended_target']
        return {
            'action': 'EXECUTE_HO',
            'target_satellite': target,
            'reason': 'd2_emergency',
            'expected_interruption': 50  # ms
        }
```

### 3.2 API 端點設計

```python
# FastAPI 實現
from fastapi import FastAPI, WebSocket
from typing import Optional

app = FastAPI()

@app.get("/api/v1/handover/status")
async def get_handover_status():
    """獲取當前換手狀態"""
    return {
        "serving_satellite": engine.current_serving,
        "pending_events": len(engine.event_queue),
        "handover_in_progress": engine.handover_in_progress,
        "scene": "ntpu"
    }

@app.post("/api/v1/handover/event")
async def process_handover_event(event: HandoverEvent):
    """處理換手事件"""
    decision = engine.process_event(event.dict())
    
    if decision:
        # 執行換手動作
        result = await execute_handover(decision)
        return {
            "status": "executed",
            "decision": decision,
            "result": result
        }
    
    return {"status": "no_action_required"}

@app.websocket("/ws/handover/stream")
async def handover_event_stream(websocket: WebSocket):
    """即時事件串流"""
    await websocket.accept()
    
    while True:
        # 從預計算資料讀取下一個事件
        event = await get_next_event()
        
        if event:
            # 處理事件並發送決策
            decision = engine.process_event(event)
            await websocket.send_json({
                "event": event,
                "decision": decision,
                "timestamp": datetime.now().isoformat()
            })
        
        await asyncio.sleep(0.1)  # 100ms 更新頻率
```

### 3.3 資料存取層

```python
class HandoverDataAccess:
    def __init__(self, data_dir="/app/data"):
        self.data_dir = Path(data_dir)
        self._load_precomputed_data()
        
    def _load_precomputed_data(self):
        """載入預計算資料"""
        # 軌道資料
        orbit_file = self.data_dir / "phase0_precomputed_orbits.json"
        self.orbit_data = json.load(open(orbit_file))
        
        # 事件資料 (如果已生成)
        event_file = self.data_dir / "events" / "ntpu_handover_events.json"
        if event_file.exists():
            self.event_data = json.load(open(event_file))
        else:
            # 即時生成事件
            self.event_data = self._generate_events_from_orbits()
    
    def get_visible_satellites(self, timestamp):
        """獲取特定時刻的可見衛星"""
        visible = []
        
        for constellation in ['starlink', 'oneweb']:
            satellites = self.orbit_data['constellations'][constellation]['satellites']
            
            for sat_id, sat_data in satellites.items():
                # 找到最接近的時間點
                position = self._find_position_at_time(
                    sat_data['positions'], timestamp
                )
                
                if position and position['is_visible']:
                    visible.append({
                        'id': sat_id,
                        'name': sat_data['name'],
                        'elevation': position['elevation_deg'],
                        'azimuth': position['azimuth_deg']
                    })
        
        return sorted(visible, key=lambda x: x['elevation'], reverse=True)
```

### 3.4 監控與分析

```python
class HandoverMetrics:
    def __init__(self):
        self.metrics = {
            'total_handovers': 0,
            'successful_handovers': 0,
            'failed_handovers': 0,
            'avg_interruption_time': 0,
            'service_availability': 100.0
        }
        
    def record_handover(self, result):
        """記錄換手結果"""
        self.metrics['total_handovers'] += 1
        
        if result['success']:
            self.metrics['successful_handovers'] += 1
            # 更新平均中斷時間
            self.update_avg_interruption(result['interruption_ms'])
        else:
            self.metrics['failed_handovers'] += 1
            
    def get_kpis(self):
        """獲取關鍵績效指標"""
        success_rate = (
            self.metrics['successful_handovers'] / 
            max(self.metrics['total_handovers'], 1) * 100
        )
        
        return {
            'handover_success_rate': success_rate,
            'avg_interruption_time_ms': self.metrics['avg_interruption_time'],
            'service_availability_percent': self.metrics['service_availability'],
            'total_handovers_24h': self.metrics['total_handovers']
        }
```

### 3.5 與前端整合

```typescript
// React 組件範例
interface HandoverEvent {
  type: 'd2' | 'a4' | 'a5';
  timestamp: string;
  satelliteId: string;
  elevation: number;
}

const HandoverMonitor: React.FC = () => {
  const [events, setEvents] = useState<HandoverEvent[]>([]);
  const [metrics, setMetrics] = useState<any>({});
  
  useEffect(() => {
    // 建立 WebSocket 連接
    const ws = new WebSocket('ws://localhost:8080/ws/handover/stream');
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setEvents(prev => [...prev.slice(-100), data.event]);
      
      // 更新決策視覺化
      if (data.decision) {
        updateDecisionVisualization(data.decision);
      }
    };
    
    // 定期獲取 KPI
    const interval = setInterval(async () => {
      const response = await fetch('/api/v1/handover/metrics');
      const kpis = await response.json();
      setMetrics(kpis);
    }, 5000);
    
    return () => {
      ws.close();
      clearInterval(interval);
    };
  }, []);
  
  return (
    <div className="handover-monitor">
      <MetricsPanel metrics={metrics} />
      <EventTimeline events={events} />
      <DecisionVisualizer />
    </div>
  );
};
```

## 預期成果 (Phase 3)

- **API 響應時間**：< 10ms (基於預計算資料)
- **事件處理延遲**：< 50ms
- **決策準確性**：> 90% (規則式)
- **系統可用性**：> 99.5%

## 為 RL 預留的介面

```python
class HandoverDecisionInterface:
    """統一決策介面，支援規則式和 RL"""
    
    def make_decision(self, state, method='rule'):
        if method == 'rule':
            return self.rule_based_decision(state)
        elif method == 'rl':
            # 預留給未來 RL 模型
            return self.rl_based_decision(state)
            
    def rl_based_decision(self, state):
        """預留給 Phase 5 實現"""
        raise NotImplementedError("RL decision making coming in Phase 5")
```