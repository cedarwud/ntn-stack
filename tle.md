# Outline
- Learning Objectives
- TLE Data Processing Pipeline
- What is TLE Data?
- Professional Tools & Libraries
- TLE Parsing Process
- SGP4 Orbital Propagation
- Coordinate System Transformations
- Visibility Calculations
- Output Data Structure
- Data Flow to Subsequent Stages
- Performance & Scalability Metrics
- Real-world Applications

# Learning Objectives
- TLE Data Structure: How orbital parameters are encoded in NORAD TLE format
- Professional Tools: Industry-standard libraries and algorithms for orbital mechanics
- SGP4 Algorithm: Core orbital propagation methodology and physical effects
- Coordinate Transformations: Multi-frame coordinate system conversions
- Visibility Analysis: Observer-relative position calculations
- Data Pipeline: How F1 output feeds into subsequent processing stages
- Performance Optimization: Scalability considerations for large satellite constellations
- Research Applications: Real-world use cases in LEO satellite communications

# TLE Data Processing Pipeline
- Understanding Satellite Tracking: From Raw Data to Real Applications
- Course Outline:
- What is TLE Data?
- Processing Architecture
- Professional Tools Used
- Step-by-Step Processing Flow
- Output Data Structure
- Real-World Applications
- Learning Goals:
- ✅ Understand satellite tracking fundamentals
- ✅ Learn industry-standard tools and methods
- ✅ See complete data transformation pipeline
- ✅ Apply to LEO satellite handover research

# What is TLE Data?
- Two-Line Element Sets: Satellite Orbital Information
- TLE Format Example:
- STARLINK-1008           ← Satellite Name
- 1 44714U 19074B   25217.61307579  .00001585  00000+0  12526-3 0  9993 ← Line 1
- 2 44714  53.0552  76.6258 0001186  97.2887 262.8236 15.06399803316185 ← Line 2
- Why Important:
- - ✅ Global standard for satellite tracking
- - ✅ Updated daily by NORAD/Space Force
- - ✅ Enables precise position prediction

# Pipeline Architecture
- Processing Scale:
- Input: ~8,735 satellites from Starlink + OneWeb + others
- Time Range: 6 hours (360 minutes)
- Resolution: 30-second intervals = 720 time points
- Total Calculations:
- 8,735 × 720 = ~6.3 million position calculations
- Output to Next Stage
- Time-Series Position Data
- Visibility Analysis
- Coordinate Transformations
- SGP4 Calculations
- Orbital Parameter Extraction
- TLE Data Loading
- Raw TLE Files (8,735 satellites)

# Professional Tools & Libraries
- SGP4 Algorithm Features:
- - ✅ Atmospheric drag effects
- - ✅ Earth's gravity field variations (J2 perturbations)
- - ✅ Solar/lunar gravitational influences
- - ✅ Sub-meter accuracy for LEO satellites
- Why These Tools:
- - ✅ NASA/NORAD approved algorithms
- - ✅ Used by satellite operators worldwide
- - ✅ Proven accuracy and reliability

# TLE Parsing Process
- Extracting Orbital Parameters from TLE Data
- Line 2 Parameter Extraction:
- Calculated Parameters:
- Orbital Period: 24×60 ÷ Mean Motion = 96 minutes
- Altitude: Derived from mean motion using gravitational formulas
- Ground Track: Combination of orbital motion + Earth rotation

# SGP4 Orbital Propagation
- Core Physics Engine for Satellite Position Prediction
- SGP4 Algorithm Steps:
- 1. Initialize orbital elements from TLE
- 2. Apply perturbations (drag, gravity variations)
- 3. Propagate to target time
- 4. Output position and velocity vectors
- Physical Effects Modeled:
- Output Data:
- Position: (X, Y, Z) in Earth-centered coordinates
- Velocity: (VX, VY, VZ) velocity vectors
- Time: Precise timestamp for each calculation

# Coordinate System Transformations
- Converting Between Reference Frames
- Coordinate Systems Explained:
- NTPU Observer Location:
- Latitude: 24.9441667°N
- Longitude: 121.3713889°E
- Altitude: 50 meters
- Observer-Relative
- (Elevation/Azimuth/Distance)
- Geographic
- (Latitude/Longitude/Altitude)
- ECEF (Earth-Centered Earth-Fixed)
- ECI (Earth-Centered Inertial)
- SGP4 Calculation
- TLE Parameters
- Transformation Chain

# Visibility Calculations
- Determining When Satellites Are Observable
- Key Calculations:
- Visibility Thresholds:
- Visibility Analysis:
- Input: Observer position + satellite position
- Output: Boolean visibility + geometric parameters
- Purpose: Filter 8,735 satellites → ~554 viable candidates

# Output Data Structure
- Time-Series Orbital Position Database
- Output Statistics:
- Satellites Processed: ~8,735
- Time Points: 720 (6 hours × 2 per minute)
- Total Data Points: ~6.3 million positions
- File Format: JSON for F2 stage consumption
- Memory Usage: ~500MB structured data
- Data Structure Per Satellite:
- json
- {
- "satellite_id": "starlink_44714",
- "constellation": "starlink",
- "positions": [
- {
- "timestamp": "2025-08-15T12:00:00Z",
- "latitude": 24.95,
- "longitude": 121.37,
- "altitude_km": 550.0,
- "elevation_deg": 15.2,
- "azimuth_deg": 45.8,
- "distance_km": 850.5,
- "velocity_km_s": 7.8,
- "is_visible": true
- }
- // ... 720 time points (30-second intervals)
- ]
- }

# Data Flow to Subsequent Stages
- F1 Output Feeds Complete Processing Pipeline
- Key Design Principle:
- ✅ TLE processed ONCE - F1 only stage that touches raw TLE data
- ✅ Memory passing - No file I/O between stages
- ✅ Data refinement - Each stage adds value to previous output
- F1 → F2 Interface:
- Data type: Structured orbital positions
- No TLE re-parsing required
- Efficient memory transfer
- Benefits:
- Performance: SGP4 calculations done once
- Consistency: All stages use same orbital data
- Scalability: 8,735 satellites processed efficiently
- Processing Chain:

# Performance & Scalability Metrics
- Processing Statistics and Optimization Results
- Performance Benchmarks:
- Scalability Analysis:
- Optimization Techniques:
- - ✅ Async processing for I/O operations
- - ✅ Batch calculations for similar satellites
- - ✅ Memory streaming to avoid storage bottlenecks
- - ✅ Error handling with graceful degradation

# Real-world Applications
- LEO Satellite Handover Research Use Cases
- Research Applications:
- Academic Research:
- PhD Thesis: LEO satellite handover optimization
- Publications: Real orbital data vs. simulated models
- Validation: 45-day historical TLE dataset
- Reproducibility: Standardized processing pipeline

# Handover Simulator
