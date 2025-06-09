# LEO 衛星網路低延遲換手機制實作計畫書

## 專案背景與現況分析

### 論文核心算法技術
**Fine-Grained Synchronized Algorithm** 的核心創新在於無需 access network 與 core network 間的控制信令交互即可維持嚴格同步。算法採用**二點預測方法**：在時間點 T 和 T+Δt 預測 UE 接入衛星，並使用 **binary search refinement** 將預測誤差迭代減半至低於 RAN 層切換程序時間。

**Fast Access Satellite Prediction Algorithm** 利用 LEO 衛星軌道的可預測性，整合**軌跡計算、天氣資訊和空間分佈優化**。算法通過約束式衛星接入策略顯著降低計算複雜度，同時保持 >95% 的切換觸發時間預測準確率。

### 系統現況評估
**已完成的基礎建設：**
- **3D 可視化系統**：基於 React + Three.js 的完整 3D 渲染引擎
- **地圖場景資源**：4 個真實場景（Lotus、NTPU、NYCU、Nanliao）含高精度建築模型
- **3D 模型資產**：衛星（sat.glb）、UAV（uav.glb）、基站（tower.glb）、干擾源（jam.glb）
- **後端服務架構**：FastAPI + Open5GS + UERANSIM + Skyfield 衛星軌道庫
- **通信協議支援**：完整的 5G NTN 協議棧，包含 N2、N3、Xn 介面

**目前功能過於分散的問題：**
側邊欄擁有 20+ 個功能開關，包含 5 大類別：
1. 基礎控制（自動飛行、UAV 動畫、衛星顯示）
2. 智能分析（AI-RAN 決策、干擾分析、ML 監控等）
3. 網路管理（網狀拓撲、性能監控、故障轉移等）
4. 協調控制（UAV 群集、換手預測、換手決策等）
5. 可視化（SINR 熱力圖、Sionna 3D、測試結果等）

**核心問題識別：**
- 缺乏針對論文算法的專門可視化
- 換手功能散落在多個組件中，缺乏整合
- 過多功能開關導致主要目標失焦
- 未實現論文中的二點預測和同步機制的直觀展示

## 實作計畫三階段詳細規劃

---

## 第一階段：功能整合與核心換手介面建立

### 1.1 前端側邊欄功能精簡重構

**目標**：將現有 20+ 個功能開關精簡為 8 個核心控制項，讓使用者專注於換手機制演示。

**保留的核心功能開關：**
1. **基礎控制**
   - 自動飛行模式
   - UAV 飛行動畫
   - 衛星星座顯示

2. **換手核心功能**
   - 換手預測顯示
   - 換手決策可視化
   - 換手性能監控

3. **干擾與通信品質**
   - SINR 熱力圖
   - 干擾源可視化

4. **網路拓撲**
   - 衛星-UAV 連接狀態

**隱藏的非核心功能：**
- AI 自適應學習系統
- 預測性維護
- 複雜的測試可視化工具
- 詳細的通道分析（CFR、時頻檢視器）
- 智能推薦系統
- 自動化報告生成

**實作步驟：**
```typescript
// 修改 EnhancedSidebar.tsx
const CORE_HANDOVER_FEATURES = {
  basic: ['auto', 'uavAnimation', 'satelliteEnabled'],
  handover: ['handoverPrediction', 'handoverDecision', 'handoverPerformance'],
  quality: ['sinrHeatmap', 'interferenceVisualization'],
  network: ['satelliteUAVConnection']
};

// 隱藏非核心功能
const HIDDEN_FEATURES = [
  'adaptiveLearning', 'predictiveMaintenance', 'testVisualization',
  'intelligentRecommendation', 'automatedReporting', 'cfr', 'timeFrequency'
];
```

### 1.2 換手機制核心可視化組件開發

**1.2.1 二點預測時間軸組件**
- 顯示當前時間 T 和預測時間 T+Δt
- 可視化預測的換手觸發時間 Tp
- 展示 binary search refinement 的迭代過程

**1.2.2 衛星接入狀態指示器**
- 即時顯示 UE 當前接入的衛星（AT）
- 預測下一時段接入衛星（AT+Δt）
- 連線狀態的動畫轉換效果

**1.2.3 手動換手控制面板**
- 簡化的衛星選擇介面
- 手動觸發換手按鈕
- 換手過程狀態顯示（開始→進行中→完成/失敗）

**前端實作結構：**
```tsx
// src/components/handover/HandoverControlPanel.tsx
interface HandoverState {
  currentSatellite: string;    // AT
  predictedSatellite: string;  // AT+Δt
  handoverTime: number;        // Tp
  status: 'idle' | 'predicting' | 'handover' | 'complete';
}

// src/components/handover/TimePredictionTimeline.tsx
// 展示 T, T+Δt, Tp 的時間軸
// src/components/handover/BinarySearchVisualization.tsx
// 可視化 binary search refinement 過程
```

### 1.3 後端換手 API 與資料結構建立

**1.3.1 預測資料表（R 表）實作**
```python
# netstack/netstack_api/models/handover_models.py
@dataclass
class HandoverPredictionRecord:
    ue_id: str
    current_satellite: str      # AT
    predicted_satellite: str    # AT+Δt
    handover_time: Optional[float]  # Tp (timestamp)
    prediction_confidence: float
    last_updated: datetime

class HandoverPredictionTable:
    def __init__(self):
        self.records: Dict[str, HandoverPredictionRecord] = {}
        self.update_interval = 5  # Δt in seconds
    
    async def update_predictions(self):
        """每 Δt 時間更新預測表"""
        pass
    
    async def calculate_handover_time(self, ue_id: str) -> Optional[float]:
        """使用 binary search 計算 Tp"""
        pass
```

**1.3.2 手動換手觸發 API**
```python
# netstack/netstack_api/routers/handover_router.py
@router.post("/handover/manual")
async def trigger_manual_handover(
    ue_id: str,
    target_satellite: str,
    handover_service: HandoverService = Depends()
):
    """觸發手動換手"""
    result = await handover_service.execute_handover(ue_id, target_satellite)
    return {"status": "initiated", "handover_id": result.handover_id}

@router.get("/handover/prediction/{ue_id}")
async def get_handover_prediction(ue_id: str):
    """取得 UE 的換手預測資訊"""
    record = handover_prediction_table.get_record(ue_id)
    return {
        "current_satellite": record.current_satellite,
        "predicted_satellite": record.predicted_satellite,
        "handover_time": record.handover_time,
        "confidence": record.prediction_confidence
    }
```

### 1.4 3D 場景換手動畫實作

**1.4.1 連線狀態可視化**
- UE 與衛星間的連線以 3D 線條表示
- 換手時連線轉移的平滑動畫效果
- 不同狀態使用不同顏色（正常/換手中/異常）

**1.4.2 衛星軌道與覆蓋範圍**
- 即時衛星軌道路徑渲染
- 衛星訊號覆蓋範圍的 3D 錐形投影
- 預測換手時的視覺提示效果

**實作組件：**
```tsx
// src/components/scenes/handover/HandoverConnectionVisualization.tsx
// 負責 UE-衛星連線的 3D 動畫
// src/components/scenes/handover/SatelliteCoverageVisualization.tsx
// 負責衛星覆蓋範圍的可視化
```

**第一階段預期成果：**
- 精簡後的側邊欄只保留 8 個核心功能開關
- 可手動觸發 UE 在兩顆衛星間的換手
- 3D 場景即時反映換手過程，包含連線轉移動畫
- 建立基礎的 R 表資料結構和手動換手 API
- 時間軸組件顯示 T、T+Δt、Tp 等關鍵時間點

---

## 第二階段：同步演算法與自動預測機制實作

### 2.1 Fine-Grained Synchronized Algorithm 核心實作

**2.1.1 二點預測機制開發**
```python
# netstack/netstack_api/services/fine_grained_sync_service.py
class FineGrainedSyncService:
    def __init__(self, delta_t: int = 5):
        self.delta_t = delta_t  # 預測時間間隔
        self.prediction_table = HandoverPredictionTable()
    
    async def two_point_prediction(self, ue_id: str) -> Tuple[str, str]:
        """
        實作二點預測方法
        返回: (AT, AT+Δt) - 當前和預測時段的接入衛星
        """
        current_time = time.time()
        future_time = current_time + self.delta_t
        
        # 使用 Skyfield 計算衛星位置
        current_satellite = await self.calculate_best_satellite(ue_id, current_time)
        future_satellite = await self.calculate_best_satellite(ue_id, future_time)
        
        return current_satellite, future_satellite
    
    async def binary_search_refinement(self, ue_id: str, t_start: float, t_end: float) -> float:
        """
        使用 binary search 精確計算換手觸發時間 Tp
        將預測誤差迭代減半至低於 RAN 層切換程序時間
        """
        precision_threshold = 0.1  # 100ms 精度
        
        while (t_end - t_start) > precision_threshold:
            t_mid = (t_start + t_end) / 2
            satellite_mid = await self.calculate_best_satellite(ue_id, t_mid)
            satellite_start = await self.calculate_best_satellite(ue_id, t_start)
            
            if satellite_mid != satellite_start:
                t_end = t_mid
            else:
                t_start = t_mid
        
        return (t_start + t_end) / 2
```

**2.1.2 同步機制實作**
```python
# netstack/netstack_api/services/core_network_sync_service.py
class CoreNetworkSyncService:
    """
    實現核心網路與接入網路的狀態同步
    無需傳統控制面信令，通過數據面資訊達成同步
    """
    
    async def sync_ue_location_via_uplink(self, ue_id: str, gtp_packet: GTPPacket):
        """
        通過上行封包的 GTP-U extension header 同步 UE 位置
        """
        if gtp_packet.has_location_extension():
            new_satellite_id = gtp_packet.get_satellite_id()
            await self.update_ue_satellite_mapping(ue_id, new_satellite_id)
    
    async def maintain_context_without_signaling(self, ue_id: str):
        """
        在無控制信令情況下維持 UE 上下文
        """
        # 通過數據面流量推斷 UE 狀態變化
        pass
```

### 2.2 Fast Access Satellite Prediction Algorithm 實作

**2.2.1 約束式衛星接入策略**
```python
# netstack/netstack_api/services/satellite_prediction_service.py
class SatellitePredictionService:
    def __init__(self):
        self.skyfield_loader = Loader('/var/data/skyfield')
        self.satellites = self.load_satellite_tle_data()
    
    async def constrained_satellite_selection(self, ue_position: Tuple[float, float, float]) -> List[str]:
        """
        約束式衛星選擇策略
        利用空間分佈特性減少候選衛星數量
        """
        # 基於 UE 地理位置劃分區域
        region = self.get_spatial_region(ue_position)
        
        # 只考慮該區域的鄰近衛星
        candidate_satellites = self.get_regional_satellites(region)
        
        # 進一步篩選：仰角 > 最低門檻
        visible_satellites = []
        for sat_id in candidate_satellites:
            elevation = await self.calculate_elevation(sat_id, ue_position)
            if elevation > self.min_elevation_threshold:
                visible_satellites.append(sat_id)
        
        return visible_satellites
    
    async def predict_with_weather_integration(self, ue_id: str) -> Dict:
        """
        整合天氣資訊的預測算法
        考慮大氣條件對信號傳播的影響
        """
        weather_data = await self.get_weather_conditions(ue_id)
        atmospheric_loss = self.calculate_atmospheric_loss(weather_data)
        
        # 調整衛星選擇權重
        satellite_scores = await self.calculate_satellite_scores_with_weather(
            ue_id, atmospheric_loss
        )
        
        return satellite_scores
```

**2.2.2 預測準確率優化**
```python
# netstack/netstack_api/services/prediction_optimizer.py
class PredictionOptimizer:
    def __init__(self):
        self.accuracy_target = 0.95  # >95% 準確率目標
        self.prediction_history = []
    
    async def adaptive_delta_t_adjustment(self):
        """
        根據預測準確率動態調整 Δt 時間間隔
        """
        recent_accuracy = self.calculate_recent_accuracy()
        
        if recent_accuracy < self.accuracy_target:
            # 準確率低時縮短預測間隔
            self.delta_t = max(3, self.delta_t - 1)
        elif recent_accuracy > 0.98:
            # 準確率很高時可以延長間隔以節省計算資源
            self.delta_t = min(10, self.delta_t + 1)
    
    async def machine_learning_enhancement(self):
        """
        使用機器學習提升預測準確率
        """
        # 使用歷史數據訓練預測模型
        features = self.extract_features_from_history()
        model = self.train_prediction_model(features)
        
        return model
```

### 2.3 前端演算法可視化強化

**2.3.1 同步演算法流程動畫**
```tsx
// src/components/handover/SynchronizedAlgorithmVisualization.tsx
interface AlgorithmStep {
  step: 'two_point_prediction' | 'binary_search' | 'sync_check' | 'handover_trigger';
  timestamp: number;
  data: any;
  status: 'running' | 'completed' | 'error';
}

const SynchronizedAlgorithmVisualization: React.FC = () => {
  const [algorithmSteps, setAlgorithmSteps] = useState<AlgorithmStep[]>([]);
  const [currentStep, setCurrentStep] = useState<string>('');
  
  // 顯示算法執行的即時狀態
  return (
    <div className="algorithm-visualization">
      <Timeline steps={algorithmSteps} />
      <BinarySearchProgress iterations={binarySearchIterations} />
      <SyncStatusIndicator syncAccuracy={syncAccuracy} />
    </div>
  );
};
```

**2.3.2 預測精度可視化**
```tsx
// src/components/handover/PredictionAccuracyDashboard.tsx
const PredictionAccuracyDashboard: React.FC = () => {
  const [accuracyHistory, setAccuracyHistory] = useState<number[]>([]);
  const [currentAccuracy, setCurrentAccuracy] = useState<number>(0);
  
  return (
    <div className="prediction-dashboard">
      <AccuracyGauge current={currentAccuracy} target={0.95} />
      <AccuracyTrendChart history={accuracyHistory} />
      <PredictionConfidenceMap satellites={visibleSatellites} />
    </div>
  );
};
```

**2.3.3 3D 空間中的預測路徑視覺化**
```tsx
// src/components/scenes/PredictionPathVisualization.tsx
const PredictionPathVisualization: React.FC = () => {
  return (
    <group>
      {/* 顯示 UE 未來軌跡預測路徑 */}
      <PredictedTrajectory path={predictedPath} />
      
      {/* 顯示可能接入的衛星群組 */}
      <CandidateSatellites 
        satellites={candidateSatellites}
        selectedSatellite={predictedSatellite}
      />
      
      {/* 顯示預測的切換點 */}
      <HandoverPointMarker 
        position={handoverPosition}
        time={handoverTime}
      />
    </group>
  );
};
```

**第二階段預期成果：**
- 完整實作二點預測機制和 binary search refinement
- 建立約束式衛星選擇策略，顯著減少計算複雜度
- 實現 >95% 的換手觸發時間預測準確率
- 自動化換手流程，無需人工干預
- 3D 場景中可視化預測算法的執行過程
- 即時顯示預測精度和算法性能指標

---

## 第三階段：異常處理機制與性能驗證展示

### 3.1 異常換手回退機制實作

**3.1.1 異常檢測與分類**
```python
# netstack/netstack_api/services/handover_fault_tolerance_service.py
class HandoverFaultToleranceService:
    def __init__(self):
        self.timeout_threshold = 5.0  # 5秒超時門檻
        self.retry_attempts = 3
        
    async def detect_handover_anomaly(self, handover_id: str) -> Optional[HandoverAnomaly]:
        """
        檢測換手異常情況
        """
        handover = await self.get_handover_status(handover_id)
        
        if handover.elapsed_time > self.timeout_threshold:
            return HandoverAnomaly(
                type='TIMEOUT',
                severity='HIGH',
                description=f'換手超時 {handover.elapsed_time}s'
            )
        
        if handover.signal_quality < self.min_signal_threshold:
            return HandoverAnomaly(
                type='SIGNAL_DEGRADATION',
                severity='MEDIUM',
                description='目標衛星信號品質不足'
            )
        
        if not handover.target_satellite_available:
            return HandoverAnomaly(
                type='TARGET_UNAVAILABLE',
                severity='HIGH',
                description='目標衛星不可用'
            )
        
        return None
    
    async def execute_fallback_strategy(self, anomaly: HandoverAnomaly, ue_id: str):
        """
        執行回退策略
        """
        if anomaly.type == 'TIMEOUT':
            # 策略1: 回滾到前一顆衛星
            await self.rollback_to_previous_satellite(ue_id)
            
        elif anomaly.type == 'TARGET_UNAVAILABLE':
            # 策略2: 選擇替代衛星
            alternative_satellite = await self.find_alternative_satellite(ue_id)
            if alternative_satellite:
                await self.redirect_handover(ue_id, alternative_satellite)
            else:
                await self.rollback_to_previous_satellite(ue_id)
        
        elif anomaly.type == 'SIGNAL_DEGRADATION':
            # 策略3: 延遲換手，等待信號改善
            await self.delay_handover(ue_id, delay_seconds=2)
```

**3.1.2 智能回退決策引擎**
```python
# netstack/netstack_api/services/intelligent_fallback_service.py
class IntelligentFallbackService:
    def __init__(self):
        self.decision_tree = self.build_fallback_decision_tree()
    
    async def make_fallback_decision(self, context: HandoverContext) -> FallbackAction:
        """
        基於當前環境狀況智能選擇回退策略
        """
        # 評估回退選項
        options = await self.evaluate_fallback_options(context)
        
        # 選擇最佳策略
        best_option = self.select_optimal_fallback(options)
        
        return FallbackAction(
            strategy=best_option.strategy,
            target=best_option.target,
            estimated_recovery_time=best_option.recovery_time,
            confidence=best_option.confidence
        )
    
    async def learn_from_fallback_experience(self, fallback_result: FallbackResult):
        """
        從回退經驗中學習，改進未來決策
        """
        # 更新決策模型
        self.update_decision_model(fallback_result)
```

### 3.2 多場景測試環境建立

**3.2.1 使用者移動模式模擬**
```python
# netstack/netstack_api/services/mobility_simulation_service.py
class MobilitySimulationService:
    def __init__(self):
        self.mobility_patterns = {
            'stationary': StatinaryPattern(),
            'linear': LinearMotionPattern(),
            'random_walk': RandomWalkPattern(),
            'circular': CircularMotionPattern(),
            'highway': HighwayPattern(),
            'urban': UrbanMobilityPattern()
        }
    
    async def simulate_ue_movement(self, pattern: str, duration: int) -> List[Position]:
        """
        模擬不同移動模式下的 UE 軌跡
        """
        mobility_model = self.mobility_patterns[pattern]
        return await mobility_model.generate_trajectory(duration)
    
    async def test_handover_under_mobility(self, pattern: str):
        """
        測試特定移動模式下的換手性能
        """
        trajectory = await self.simulate_ue_movement(pattern, duration=300)
        handover_results = []
        
        for position in trajectory:
            result = await self.handover_service.handle_position_update(position)
            handover_results.append(result)
        
        return self.analyze_handover_performance(handover_results)
```

**3.2.2 衛星星座配置測試**
```python
# netstack/netstack_api/services/constellation_test_service.py
class ConstellationTestService:
    def __init__(self):
        self.constellation_configs = {
            'starlink': StarLinkConstellation(),
            'oneweb': OneWebConstellation(),
            'custom_leo': CustomLEOConstellation(),
            'mixed': MixedConstellation()
        }
    
    async def test_algorithm_with_constellation(self, constellation: str):
        """
        測試不同衛星星座配置下的算法性能
        """
        config = self.constellation_configs[constellation]
        
        # 載入星座 TLE 數據
        await self.load_constellation_data(config)
        
        # 執行測試情境
        test_results = await self.run_handover_test_suite(config)
        
        return {
            'constellation': constellation,
            'satellite_count': config.satellite_count,
            'handover_frequency': test_results.handover_frequency,
            'average_latency': test_results.average_latency,
            'success_rate': test_results.success_rate
        }
```

### 3.3 前端異常處理可視化

**3.3.1 異常事件即時提示系統**
```tsx
// src/components/handover/AnomalyAlertSystem.tsx
interface HandoverAnomaly {
  id: string;
  type: 'timeout' | 'signal_degradation' | 'target_unavailable';
  severity: 'low' | 'medium' | 'high';
  timestamp: number;
  ue_id: string;
  description: string;
  fallback_action?: FallbackAction;
}

const AnomalyAlertSystem: React.FC = () => {
  const [anomalies, setAnomalies] = useState<HandoverAnomaly[]>([]);
  
  return (
    <div className="anomaly-alert-system">
      <AnomalyNotificationBanner anomalies={anomalies} />
      <AnomalyHistoryTimeline history={anomalies} />
      <FallbackActionIndicator currentAction={currentFallbackAction} />
    </div>
  );
};
```

**3.3.2 3D 場景中的異常可視化**
```tsx
// src/components/scenes/handover/HandoverAnomalyVisualization.tsx
const HandoverAnomalyVisualization: React.FC = () => {
  return (
    <group>
      {/* 異常 UE 的紅色警示效果 */}
      <AnomalousUEIndicator 
        ue={anomalousUE}
        anomalyType={anomalyType}
      />
      
      {/* 回退路徑的可視化 */}
      <FallbackPathVisualization 
        originalPath={originalHandoverPath}
        fallbackPath={fallbackPath}
      />
      
      {/* 替代衛星的高亮顯示 */}
      <AlternativeSatelliteHighlight 
        satellites={alternativeSatellites}
        selected={selectedAlternative}
      />
    </group>
  );
};
```

### 3.4 性能對比與效果展示

**3.4.1 傳統 vs. 加速換手對比系統**
```tsx
// src/components/dashboard/HandoverComparisonDashboard.tsx
const HandoverComparisonDashboard: React.FC = () => {
  const [traditionalResults, setTraditionalResults] = useState<HandoverMetrics>();
  const [acceleratedResults, setAcceleratedResults] = useState<HandoverMetrics>();
  
  return (
    <div className="comparison-dashboard">
      <PerformanceComparisonChart 
        traditional={traditionalResults}
        accelerated={acceleratedResults}
      />
      
      <MetricsTable>
        <MetricRow 
          metric="平均換手延遲"
          traditional="150ms"
          accelerated="15ms"
          improvement="10x"
        />
        <MetricRow 
          metric="成功率"
          traditional="97.3%"
          accelerated="99.6%"
          improvement="+2.3%"
        />
        <MetricRow 
          metric="預測準確率"
          traditional="N/A"
          accelerated="96.8%"
          improvement="新功能"
        />
      </MetricsTable>
    </div>
  );
};
```

**3.4.2 即時性能監控儀表板**
```tsx
// src/components/dashboard/RealtimePerformanceMonitor.tsx
const RealtimePerformanceMonitor: React.FC = () => {
  const [liveMetrics, setLiveMetrics] = useState<LiveMetrics>();
  
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/metrics');
    ws.onmessage = (event) => {
      const metrics = JSON.parse(event.data);
      setLiveMetrics(metrics);
    };
  }, []);
  
  return (
    <div className="realtime-monitor">
      <GaugeChart 
        title="當前換手延遲"
        value={liveMetrics?.currentLatency}
        max={200}
        target={50}
      />
      
      <TrendChart 
        title="換手成功率趨勢"
        data={liveMetrics?.successRateTrend}
      />
      
      <AlertPanel alerts={liveMetrics?.alerts} />
    </div>
  );
};
```

### 3.5 場景測試與驗證

**3.5.1 四場景換手測試**
利用現有的四個真實場景進行測試：
- **Lotus 場景**：校園環境，中等密度建築
- **NTPU 場景**：都市環境，高密度建築  
- **NYCU 場景**：科技園區，現代化建築
- **Nanliao 場景**：郊區環境，低密度建築

**3.5.2 多元化測試情境**
```python
# 測試矩陣
test_scenarios = [
    {
        'scene': 'Lotus',
        'mobility': 'stationary',
        'constellation': 'starlink',
        'weather': 'clear'
    },
    {
        'scene': 'NTPU', 
        'mobility': 'urban',
        'constellation': 'oneweb',
        'weather': 'rainy'
    },
    {
        'scene': 'NYCU',
        'mobility': 'linear',
        'constellation': 'mixed',
        'weather': 'cloudy'
    },
    {
        'scene': 'Nanliao',
        'mobility': 'random_walk',
        'constellation': 'custom_leo',
        'weather': 'clear'
    }
]
```

**第三階段預期成果：**
- 完善的異常檢測和智能回退機制
- 支援多種使用者移動模式和衛星星座配置測試
- 即時異常提示和 3D 可視化
- 傳統換手 vs. 加速換手的性能對比展示
- 四個真實場景下的完整測試驗證
- 系統在各種非理想情境下的穩健運行能力

---

## 計畫實施時程與里程碑

### 時程規劃（預估 12 週完成）

**第一階段（週 1-4）**
- 週 1-2：側邊欄功能精簡和重構
- 週 3：換手核心 UI 組件開發  
- 週 4：手動換手 API 和基礎動畫實作

**第二階段（週 5-8）**
- 週 5-6：二點預測和 binary search 算法實作
- 週 7：約束式衛星選擇策略開發
- 週 8：自動化換手流程和可視化整合

**第三階段（週 9-12）**
- 週 9-10：異常處理機制和回退策略實作
- 週 11：多場景測試環境建立
- 週 12：性能驗證和最終展示準備

### 關鍵成功指標

**技術指標：**
- 換手延遲 < 50ms（目標：論文中的 10 倍改善）
- 預測準確率 > 95%
- 系統可用性 > 99%
- 異常回退成功率 > 98%

**使用者體驗指標：**
- 側邊欄功能控制精簡至 8 個核心開關
- 換手過程 3D 可視化流暢度 > 60 FPS
- 異常情況回復時間 < 3 秒

**展示效果指標：**
- 支援 4 個場景的完整測試
- 傳統 vs. 加速換手對比明確可見
- 演算法過程視覺化清晰易懂

## 總結

本計畫書通過三個遞進階段，將現有的 NTN Stack 系統改造為專門展示 IEEE INFOCOM 2024 論文換手機制的演示平台。第一階段聚焦於介面精簡和核心功能建立；第二階段實現論文的核心算法；第三階段確保系統穩健性和展示效果。

整個計畫充分利用現有的 3D 可視化基礎設施、地圖場景資源和後端服務架構，避免重複開發，專注於論文算法的實現和可視化。最終將交付一個功能聚焦、視覺直觀、技術先進的衛星換手機制演示系統。