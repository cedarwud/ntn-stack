# TLE Data Processing Pipeline - Educational Slides

## Course Overview
**Understanding TLE Data Processing: From Raw Orbital Elements to LEO Satellite Handover Research**

This educational presentation covers the complete pipeline for processing Two-Line Element (TLE) data in the F1 stage, including professional tools, orbital mechanics calculations, and data flow to subsequent processing stages.

---

## Slide Structure Outline

### **Slide 1: Title & Outline**
- Course overview and learning objectives

### **Slide 2: What is TLE Data?**
- TLE format structure and components

### **Slide 3: F1 Pipeline Architecture**
- High-level processing flow diagram

### **Slide 4: Professional Tools & Libraries**
- SGP4, Skyfield, NumPy, coordinate systems

### **Slide 5: TLE Parsing Process**
- Orbital parameter extraction methodology

### **Slide 6: SGP4 Orbital Propagation**
- Core orbital mechanics calculations

### **Slide 7: Coordinate System Transformations**
- ECI → ECEF → Geographic → Observer frames

### **Slide 8: Visibility Calculations**
- Elevation, azimuth, and threshold analysis

### **Slide 9: F1 Output Data Structure**
- Time-series orbital positions and metadata

### **Slide 10: Data Flow to Subsequent Stages**
- F2, F3, A1 processing chain overview

### **Slide 11: Performance & Scalability Metrics**
- Processing statistics and optimization results

### **Slide 12: Real-world Applications**
- LEO satellite handover research use cases

---

## Learning Objectives

By the end of this presentation, students will understand:

1. **TLE Data Structure**: How orbital parameters are encoded in NORAD TLE format
2. **Professional Tools**: Industry-standard libraries and algorithms for orbital mechanics
3. **SGP4 Algorithm**: Core orbital propagation methodology and physical effects
4. **Coordinate Transformations**: Multi-frame coordinate system conversions
5. **Visibility Analysis**: Observer-relative position calculations
6. **Data Pipeline**: How F1 output feeds into subsequent processing stages
7. **Performance Optimization**: Scalability considerations for large satellite constellations
8. **Research Applications**: Real-world use cases in LEO satellite communications

---

## Target Audience
- Engineers and researchers new to satellite data processing
- Software developers working with orbital mechanics
- Students learning LEO constellation systems
- Anyone interested in satellite tracking and handover algorithms

---

## Prerequisites
**None** - All concepts will be explained from fundamental principles

---

---

## **Slide 1: TLE Data Processing Pipeline**

### **Understanding Satellite Tracking: From Raw Data to Real Applications**

**Course Outline:**
- What is TLE Data?
- F1 Processing Architecture  
- Professional Tools Used
- Step-by-Step Processing Flow
- Output Data Structure
- Real-World Applications

**Learning Goals:**
✅ Understand satellite tracking fundamentals
✅ Learn industry-standard tools and methods
✅ See complete data transformation pipeline
✅ Apply to LEO satellite handover research

---

## **Slide 2: What is TLE Data?**

### **Two-Line Element Sets: Satellite Orbital Information**

**TLE Format Example:**
```
STARLINK-1008           ← Satellite Name
1 44714U 19074B   25217.61307579  .00001585  00000+0  12526-3 0  9993 ← Line 1
2 44714  53.0552  76.6258 0001186  97.2887 262.8236 15.06399803316185 ← Line 2
```

**Key Components:**
| Line | Contains | Examples |
|------|----------|----------|
| **Name** | Satellite identifier | STARLINK-1008 |
| **Line 1** | Catalog number, epoch time | 44714, 25217.613... |
| **Line 2** | Orbital parameters | Inclination: 53.0552° |

**Why Important:**
- ✅ Global standard for satellite tracking
- ✅ Updated daily by NORAD/Space Force
- ✅ Enables precise position prediction

---

## **Slide 3: F1 Pipeline Architecture**

### **High-Level Processing Flow**

```
Raw TLE Files (8,735 satellites)
           ↓
    TLE Data Loading
           ↓
   Orbital Parameter Extraction
           ↓
      SGP4 Calculations
           ↓
   Coordinate Transformations
           ↓
    Visibility Analysis
           ↓
Time-Series Position Data
           ↓
   Output to F2 Stage
```

**Processing Scale:**
- **Input**: ~8,735 satellites from Starlink + OneWeb + others
- **Time Range**: 6 hours (360 minutes)
- **Resolution**: 30-second intervals = 720 time points
- **Total Calculations**: 8,735 × 720 = ~6.3 million position calculations

---

## **Slide 4: Professional Tools & Libraries**

### **Industry-Standard Software Stack**

| Tool | Purpose | Key Capabilities |
|------|---------|------------------|
| **SGP4** | Orbital propagation | Standard algorithm for satellite tracking |
| **Skyfield** | Astronomical calculations | High-precision orbital mechanics |
| **NumPy** | Mathematical operations | Vector/matrix calculations |
| **Python asyncio** | Parallel processing | Handle 8,735 satellites efficiently |

**SGP4 Algorithm Features:**
- ✅ **Atmospheric drag** effects
- ✅ **Earth's gravity field** variations (J2 perturbations)
- ✅ **Solar/lunar** gravitational influences
- ✅ **Sub-meter accuracy** for LEO satellites

**Why These Tools:**
- ✅ NASA/NORAD approved algorithms
- ✅ Used by satellite operators worldwide
- ✅ Proven accuracy and reliability

---

## **Slide 5: TLE Parsing Process**

### **Extracting Orbital Parameters from TLE Data**

**Line 2 Parameter Extraction:**
| Parameter | Position | Value Example | Meaning |
|-----------|----------|---------------|---------|
| **Inclination** | Chars 8-16 | 53.0552° | Orbital tilt relative to equator |
| **RAAN** | Chars 17-25 | 76.6258° | Right Ascension of Ascending Node |
| **Eccentricity** | Chars 26-33 | 0.0001186 | Orbit shape (0=circle, 1=parabola) |
| **Argument of Perigee** | Chars 34-42 | 97.2887° | Orientation of orbit |
| **Mean Anomaly** | Chars 43-51 | 262.8236° | Satellite position in orbit |
| **Mean Motion** | Chars 52-63 | 15.06399803 | Revolutions per day |

**Calculated Parameters:**
- **Orbital Period**: 24×60 ÷ Mean Motion = 96 minutes
- **Altitude**: Derived from mean motion using gravitational formulas
- **Ground Track**: Combination of orbital motion + Earth rotation

---

## **Slide 6: SGP4 Orbital Propagation**

### **Core Physics Engine for Satellite Position Prediction**

**SGP4 Algorithm Steps:**
1. **Initialize** orbital elements from TLE
2. **Apply perturbations** (drag, gravity variations)
3. **Propagate** to target time
4. **Output** position and velocity vectors

**Physical Effects Modeled:**

| Effect | Impact | Example |
|--------|---------|---------|
| **Atmospheric Drag** | Orbital decay | Satellite slows down, altitude decreases |
| **J2 Perturbation** | Precession | Orbit plane slowly rotates |
| **Solar Pressure** | Minor drift | Small push from sunlight |
| **Lunar/Solar Gravity** | Long-term changes | Gradual orbital modifications |

**Output Data:**
- **Position**: (X, Y, Z) in Earth-centered coordinates
- **Velocity**: (VX, VY, VZ) velocity vectors
- **Time**: Precise timestamp for each calculation

---

## **Slide 7: Coordinate System Transformations**

### **Converting Between Reference Frames**

**Transformation Chain:**

```
TLE Parameters
     ↓
SGP4 Calculation
     ↓
ECI (Earth-Centered Inertial)
     ↓
ECEF (Earth-Centered Earth-Fixed)
     ↓
Geographic (Latitude/Longitude/Altitude)
     ↓
Observer-Relative (Elevation/Azimuth/Distance)
```

**Coordinate Systems Explained:**

| System | Description | Use Case |
|--------|-------------|----------|
| **ECI** | Fixed to stars, doesn't rotate | Orbital calculations |
| **ECEF** | Rotates with Earth | GPS positioning |
| **Geographic** | Lat/Lon/Alt on Earth surface | Mapping applications |
| **Observer** | Relative to ground station | Antenna pointing |

**NTPU Observer Location:**
- **Latitude**: 24.9441667°N
- **Longitude**: 121.3713889°E
- **Altitude**: 50 meters

---

## **Slide 8: Visibility Calculations**

### **Determining When Satellites Are Observable**

**Key Calculations:**

| Measurement | Formula Basis | Purpose |
|-------------|---------------|---------|
| **Elevation Angle** | arctan(altitude/distance) | Height above horizon |
| **Azimuth Angle** | arctan2(east, north) | Compass direction |
| **Range Distance** | √(Δx² + Δy² + Δz²) | Distance to satellite |

**Visibility Thresholds:**

| Constellation | Elevation Threshold | Reasoning |
|---------------|-------------------|-----------|
| **Starlink** | ≥ 5° | Lower altitude, more frequent passes |
| **OneWeb** | ≥ 10° | Higher altitude, stronger signals |
| **Others** | ≥ 10° | Conservative default |

**Visibility Analysis:**
- **Input**: Observer position + satellite position
- **Output**: Boolean visibility + geometric parameters
- **Purpose**: Filter 8,735 satellites → ~554 viable candidates

---

## **Slide 9: F1 Output Data Structure**

### **Time-Series Orbital Position Database**

**Data Structure Per Satellite:**
```json
{
  "satellite_id": "starlink_44714",
  "constellation": "starlink",
  "positions": [
    {
      "timestamp": "2025-08-15T12:00:00Z",
      "latitude": 24.95,
      "longitude": 121.37,
      "altitude_km": 550.0,
      "elevation_deg": 15.2,
      "azimuth_deg": 45.8,
      "distance_km": 850.5,
      "velocity_km_s": 7.8,
      "is_visible": true
    }
    // ... 720 time points (30-second intervals)
  ]
}
```

**Output Statistics:**
- **Satellites Processed**: ~8,735
- **Time Points**: 720 (6 hours × 2 per minute)
- **Total Data Points**: ~6.3 million positions
- **File Format**: JSON for F2 stage consumption
- **Memory Usage**: ~500MB structured data

---

## **Slide 10: Data Flow to Subsequent Stages**

### **F1 Output Feeds Complete Processing Pipeline**

**Processing Chain:**

| Stage | Input | Processing | Output |
|-------|-------|------------|--------|
| **F1** | TLE files | SGP4 + visibility | Position time-series |
| **F2** | F1 positions | Satellite filtering | ~554 candidates |
| **F3** | F2 candidates | Signal analysis | A4/A5/D2 events |
| **A1** | F3 events | Dynamic planning | Final satellite pools |

**Key Design Principle:**
✅ **TLE processed ONCE** - F1 only stage that touches raw TLE data
✅ **Memory passing** - No file I/O between stages
✅ **Data refinement** - Each stage adds value to previous output

**F1 → F2 Interface:**
- **Data type**: Structured orbital positions
- **No TLE re-parsing** required
- **Efficient memory transfer**

**Benefits:**
- **Performance**: SGP4 calculations done once
- **Consistency**: All stages use same orbital data
- **Scalability**: 8,735 satellites processed efficiently

---

## **Slide 11: Performance & Scalability Metrics**

### **Processing Statistics and Optimization Results**

**Performance Benchmarks:**

| Metric | Value | Optimization |
|--------|-------|--------------|
| **TLE Loading** | ~30 seconds | Parallel constellation loading |
| **SGP4 Calculations** | ~2 minutes | Async batch processing |
| **Coordinate Transform** | ~15 seconds | Vectorized operations |
| **Total F1 Runtime** | **~3 minutes** | End-to-end processing |

**Scalability Analysis:**

| Constellation | Satellites | Processing Time | Memory Usage |
|---------------|------------|-----------------|--------------|
| **Starlink** | ~5,000 | 105 seconds | 300MB |
| **OneWeb** | ~800 | 18 seconds | 50MB |
| **Others** | ~2,935 | 62 seconds | 150MB |
| **Total** | **8,735** | **185 seconds** | **500MB** |

**Optimization Techniques:**
- ✅ **Async processing** for I/O operations
- ✅ **Batch calculations** for similar satellites
- ✅ **Memory streaming** to avoid storage bottlenecks
- ✅ **Error handling** with graceful degradation

---

## **Slide 12: Real-world Applications**

### **LEO Satellite Handover Research Use Cases**

**Research Applications:**

| Application | F1 Data Usage | Research Value |
|-------------|---------------|----------------|
| **Handover Timing** | Satellite visibility windows | Optimize switching decisions |
| **Signal Prediction** | Distance/elevation data | Calculate link quality |
| **Coverage Analysis** | Multi-satellite positions | Ensure continuous service |
| **Constellation Comparison** | Starlink vs OneWeb tracking | Performance benchmarking |

**Academic Research:**
- **PhD Thesis**: LEO satellite handover optimization
- **Publications**: Real orbital data vs. simulated models
- **Validation**: 45-day historical TLE dataset
- **Reproducibility**: Standardized processing pipeline

**Industry Applications:**
- **Satellite Operators**: Constellation management
- **Ground Stations**: Antenna tracking systems
- **Mobile Networks**: 5G NTN integration
- **IoT Devices**: Satellite connectivity planning

**Future Expansion:**
- **Machine Learning**: Train on F1 orbital patterns
- **Real-time Systems**: Live TLE data integration
- **Global Coverage**: Multi-observer locations
- **Advanced Physics**: Higher-order orbital perturbations

---

*End of Presentation*