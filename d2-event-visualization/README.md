# D2 Event Visualization Development Plan

## Project Overview

This project implements **3GPP D2 event visualization** using real historical satellite data from the NTN Stack system. The D2 event triggers handover when:
- Distance between UE and serving satellite's moving reference location > Threshold 1
- Distance between UE and target satellite's moving reference location < Threshold 2

## Current Status Analysis

### ✅ Available Data
- **SGP4 Orbit Calculations**: High-precision satellite positions
- **120-minute Preprocessed Data**: 10-second intervals, 70 satellites
- **Intelligent Selection**: 40 Starlink + 30 OneWeb satellites
- **Position Data**: elevation_deg, azimuth_deg, range_km, is_visible

### ❌ Missing for D2 Event
- **Moving Reference Location**: Satellite nadir point calculation
- **Multi-satellite Distance Tracking**: Simultaneous serving/target monitoring
- **D2 Event Detection Logic**: Threshold-based handover triggers
- **Timeline Synchronization**: Chart-3D view coordination

## Implementation Phases

### Phase 1: Data Preprocessing Enhancement (Days 1-2)
- Enhance preprocessing to calculate moving reference locations
- Add nadir point projection for each satellite position
- Implement D2 event detection algorithm
- Details: [data-preprocessing.md](./data-preprocessing.md)

### Phase 2: Chart Implementation (Days 3-5)
- Develop D2 distance chart component
- Integrate real satellite data
- Add threshold visualization and event markers
- Details: [chart-implementation.md](./chart-implementation.md)

### Phase 3: 3D Integration (Days 6-8)
- Synchronize timeline between chart and 3D view
- Highlight handover events in both views
- Add smooth animation transitions
- Details: [3d-integration.md](./3d-integration.md)

### Phase 4: Educational Enhancement (Days 9-10)
- Add parameter adjustment controls
- Create scenario templates
- Implement comparison mode (real vs simulated)
- Details: [comparison-analysis.md](./comparison-analysis.md)

## Key Benefits

### Research Value
- **Real TLE Data**: Authentic orbital dynamics
- **SGP4 Accuracy**: Research-grade calculations
- **Reproducible Results**: Based on historical data

### Educational Value
- **Visual Learning**: Combined chart + 3D visualization
- **Interactive Exploration**: Timeline scrubbing
- **Scenario Comparison**: Real vs idealized cases

## Quick Start

```bash
# 1. Enhance preprocessing (add moving reference locations)
cd /home/sat/ntn-stack/simworld/backend
python enhance_d2_preprocessing.py

# 2. Start services
make up

# 3. Access D2 visualization
http://localhost:5173/handover/d2-events
```

## Architecture Overview
```
Real TLE Data → SGP4 → Enhanced Preprocessing → D2 Event Detection
                          ↓                          ↓
                    Moving Reference            Chart + 3D View
                      Locations                 Synchronized
```

## Documentation Index

1. **[Data Preprocessing](./data-preprocessing.md)** - Enhanced satellite data processing
2. **[Chart Implementation](./chart-implementation.md)** - D2 event chart development
3. **[3D Integration](./3d-integration.md)** - Timeline synchronization details
4. **[API Endpoints](./api-endpoints.md)** - Backend service specifications
5. **[Comparison Analysis](./comparison-analysis.md)** - Real vs simulated evaluation
6. **[Technical Architecture](./technical-architecture.md)** - System design details

## Success Metrics

- ✅ Accurate moving reference location calculation
- ✅ Real-time D2 event detection
- ✅ Synchronized chart-3D visualization
- ✅ < 100ms timeline update latency
- ✅ Support for 70+ satellites
- ✅ Educational scenario templates

## Next Steps

1. Review current preprocessing code for extension points
2. Design enhanced data schema for D2 events
3. Prototype chart component with mock data
4. Test SGP4 nadir point calculations

---

**Project Status**: 🚀 Ready for Development  
**Estimated Duration**: 10 working days  
**Priority**: High (Research Paper Dependency)