# 3D View Integration with D2 Event Visualization

## Overview

This document details the synchronization between D2 event charts and the 3D satellite visualization, creating a unified experience for understanding handover events.

## Architecture

### Shared State Management
```typescript
// contexts/D2VisualizationContext.tsx
interface D2VisualizationState {
  currentTime: Date;
  selectedSatellites: {
    serving: string | null;
    target: string | null;
  };
  d2Event: D2Event | null;
  playbackState: {
    isPlaying: boolean;
    speed: number;
  };
  viewSync: {
    chartFocus: TimeRange;
    globeFocus: GeoLocation;
  };
}

export const D2VisualizationProvider: React.FC = ({ children }) => {
  const [state, dispatch] = useReducer(d2Reducer, initialState);
  
  // Sync with global timeline
  useEffect(() => {
    const unsubscribe = timelineStore.subscribe((time) => {
      dispatch({ type: 'SET_TIME', payload: time });
    });
    return unsubscribe;
  }, []);
  
  return (
    <D2VisualizationContext.Provider value={{ state, dispatch }}>
      {children}
    </D2VisualizationContext.Provider>
  );
};
```

## 3D Globe Enhancement

### Satellite Highlighting System
```typescript
// Globe3D/SatelliteHighlighter.tsx
export class SatelliteHighlighter {
  private scene: THREE.Scene;
  private servingHighlight: THREE.Mesh | null = null;
  private targetHighlight: THREE.Mesh | null = null;
  
  highlightD2Satellites(serving: string, target: string) {
    // Clear previous highlights
    this.clearHighlights();
    
    // Create glowing effect for serving satellite
    const servingSat = this.scene.getObjectByName(serving);
    if (servingSat) {
      this.servingHighlight = this.createGlowEffect(
        servingSat.position,
        0x22c55e, // Green
        2.0 // Intensity
      );
      this.scene.add(this.servingHighlight);
    }
    
    // Create glowing effect for target satellite
    const targetSat = this.scene.getObjectByName(target);
    if (targetSat) {
      this.targetHighlight = this.createGlowEffect(
        targetSat.position,
        0xf97316, // Orange
        2.0
      );
      this.scene.add(this.targetHighlight);
    }
  }
  
  private createGlowEffect(position: THREE.Vector3, color: number, intensity: number) {
    const geometry = new THREE.SphereGeometry(5, 32, 32);
    const material = new THREE.ShaderMaterial({
      uniforms: {
        glowColor: { value: new THREE.Color(color) },
        intensity: { value: intensity },
        time: { value: 0 }
      },
      vertexShader: glowVertexShader,
      fragmentShader: glowFragmentShader,
      transparent: true,
      blending: THREE.AdditiveBlending
    });
    
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.copy(position);
    return mesh;
  }
}
```

### Moving Reference Location Visualization
```typescript
// Globe3D/MovingReferenceLocation.tsx
export class MRLVisualizer {
  private mrlMarkers: Map<string, THREE.Object3D> = new Map();
  
  updateMRLPositions(satellites: SatelliteData[]) {
    satellites.forEach(sat => {
      let marker = this.mrlMarkers.get(sat.id);
      
      if (!marker) {
        // Create cone pointing from satellite to nadir
        marker = this.createMRLMarker(sat.color);
        this.mrlMarkers.set(sat.id, marker);
        this.scene.add(marker);
      }
      
      // Update position and orientation
      const satPos = new THREE.Vector3(...sat.position);
      const mrlPos = new THREE.Vector3(...sat.mrlPosition);
      
      marker.position.copy(mrlPos);
      marker.lookAt(satPos);
    });
  }
  
  private createMRLMarker(color: number): THREE.Object3D {
    const group = new THREE.Group();
    
    // Ground marker circle
    const circleGeometry = new THREE.RingGeometry(10, 12, 32);
    const circleMaterial = new THREE.MeshBasicMaterial({
      color,
      opacity: 0.6,
      transparent: true
    });
    const circle = new THREE.Mesh(circleGeometry, circleMaterial);
    circle.rotation.x = -Math.PI / 2;
    
    // Connection line
    const lineGeometry = new THREE.BufferGeometry();
    const lineMaterial = new THREE.LineBasicMaterial({
      color,
      opacity: 0.3,
      transparent: true
    });
    const line = new THREE.Line(lineGeometry, lineMaterial);
    
    group.add(circle);
    group.add(line);
    
    return group;
  }
}
```

## Timeline Synchronization

### Unified Timeline Controller
```typescript
// components/UnifiedTimeline.tsx
export const UnifiedTimeline: React.FC = () => {
  const { state, dispatch } = useD2Visualization();
  const [isDragging, setIsDragging] = useState(false);
  
  const handleTimeChange = (newTime: Date) => {
    dispatch({ type: 'SET_TIME', payload: newTime });
    
    // Update all synchronized views
    updateChartTime(newTime);
    update3DTime(newTime);
    updateEventPanel(newTime);
  };
  
  return (
    <div className="unified-timeline">
      <PlaybackControls
        isPlaying={state.playbackState.isPlaying}
        speed={state.playbackState.speed}
        onPlayPause={() => dispatch({ type: 'TOGGLE_PLAY' })}
        onSpeedChange={(speed) => dispatch({ type: 'SET_SPEED', payload: speed })}
      />
      
      <TimelineScrubber
        currentTime={state.currentTime}
        duration={120 * 60 * 1000} // 120 minutes
        onTimeChange={handleTimeChange}
        markers={state.d2Events}
      />
      
      <TimeDisplay currentTime={state.currentTime} />
    </div>
  );
};
```

### Smooth Animation System
```typescript
// hooks/useAnimationFrame.ts
export function useAnimationFrame(callback: (deltaTime: number) => void) {
  const requestRef = useRef<number>();
  const previousTimeRef = useRef<number>();
  
  const animate = (time: number) => {
    if (previousTimeRef.current !== undefined) {
      const deltaTime = time - previousTimeRef.current;
      callback(deltaTime);
    }
    previousTimeRef.current = time;
    requestRef.current = requestAnimationFrame(animate);
  };
  
  useEffect(() => {
    requestRef.current = requestAnimationFrame(animate);
    return () => {
      if (requestRef.current) {
        cancelAnimationFrame(requestRef.current);
      }
    };
  }, []);
}

// Usage in 3D view
useAnimationFrame((deltaTime) => {
  if (state.playbackState.isPlaying) {
    const newTime = new Date(
      state.currentTime.getTime() + 
      deltaTime * state.playbackState.speed
    );
    dispatch({ type: 'SET_TIME', payload: newTime });
  }
});
```

## Event Visualization

### D2 Event Animation
```typescript
// Globe3D/D2EventAnimation.tsx
export class D2EventAnimation {
  private particleSystem: THREE.Points;
  private handoverPath: THREE.CatmullRomCurve3;
  
  animateHandover(event: D2Event, progress: number) {
    // Create particle stream from serving to target
    const particles = this.createParticleStream(
      event.servingPosition,
      event.targetPosition,
      progress
    );
    
    // Pulse effect at threshold crossing
    if (progress > 0.48 && progress < 0.52) {
      this.createPulseEffect(event.crossingPoint);
    }
    
    // Update info panel
    this.updateHandoverInfo(event, progress);
  }
  
  private createParticleStream(from: Vector3, to: Vector3, progress: number) {
    const curve = new THREE.CatmullRomCurve3([from, to]);
    const points = curve.getPoints(100);
    
    // Create glowing particles along path
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(points.length * 3);
    const colors = new Float32Array(points.length * 3);
    
    points.forEach((point, i) => {
      const idx = i * 3;
      positions[idx] = point.x;
      positions[idx + 1] = point.y;
      positions[idx + 2] = point.z;
      
      // Gradient from green to orange
      const t = i / points.length;
      colors[idx] = 0.13 + t * 0.84; // R
      colors[idx + 1] = 0.77 - t * 0.47; // G
      colors[idx + 2] = 0.34 - t * 0.25; // B
    });
    
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    
    return new THREE.Points(geometry, particleMaterial);
  }
}
```

### Camera Focus Management
```typescript
// Globe3D/CameraController.tsx
export class CameraController {
  focusOnD2Event(event: D2Event, camera: THREE.Camera, controls: OrbitControls) {
    const servingPos = new THREE.Vector3(...event.servingPosition);
    const targetPos = new THREE.Vector3(...event.targetPosition);
    
    // Calculate optimal camera position
    const center = servingPos.clone().add(targetPos).multiplyScalar(0.5);
    const distance = servingPos.distanceTo(targetPos);
    
    // Smooth camera transition
    gsap.to(camera.position, {
      x: center.x + distance,
      y: center.y + distance * 0.5,
      z: center.z + distance,
      duration: 2,
      ease: "power2.inOut",
      onUpdate: () => controls.update()
    });
    
    gsap.to(controls.target, {
      x: center.x,
      y: center.y,
      z: center.z,
      duration: 2,
      ease: "power2.inOut"
    });
  }
}
```

## Layout Integration

### Split View Layout
```typescript
// layouts/D2VisualizationLayout.tsx
export const D2VisualizationLayout: React.FC = () => {
  const [viewMode, setViewMode] = useState<'split' | 'chart' | '3d'>('split');
  
  return (
    <div className="d2-visualization-layout">
      <ViewModeSelector mode={viewMode} onChange={setViewMode} />
      
      <div className={`view-container ${viewMode}`}>
        {(viewMode === 'split' || viewMode === '3d') && (
          <div className="globe-container">
            <Globe3D />
            <SatelliteInfoOverlay />
          </div>
        )}
        
        {(viewMode === 'split' || viewMode === 'chart') && (
          <div className="chart-container">
            <D2EventChart />
            <ThresholdControls />
          </div>
        )}
      </div>
      
      <UnifiedTimeline />
      
      <div className="side-panel">
        <D2EventDetails />
        <HandoverStatistics />
      </div>
    </div>
  );
};
```

### Responsive Styling
```scss
// D2VisualizationLayout.scss
.d2-visualization-layout {
  height: 100vh;
  display: grid;
  grid-template-rows: auto 1fr auto;
  grid-template-columns: 1fr 300px;
  gap: 1rem;
  
  .view-container {
    display: grid;
    
    &.split {
      grid-template-columns: 1fr 1fr;
      gap: 1rem;
    }
    
    &.chart, &.3d {
      grid-template-columns: 1fr;
    }
  }
  
  .globe-container {
    position: relative;
    background: #0f172a;
    border-radius: 8px;
    overflow: hidden;
  }
  
  .chart-container {
    background: #1f2937;
    border-radius: 8px;
    padding: 1rem;
  }
  
  // Mobile responsive
  @media (max-width: 1024px) {
    grid-template-columns: 1fr;
    
    .side-panel {
      display: none;
    }
    
    .view-container.split {
      grid-template-columns: 1fr;
      grid-template-rows: 1fr 1fr;
    }
  }
}
```

## Performance Optimization

### Level of Detail (LOD) System
```typescript
// Globe3D/LODManager.tsx
export class LODManager {
  updateSatelliteLOD(satellites: Satellite[], cameraDistance: number) {
    satellites.forEach(sat => {
      const distance = sat.position.distanceTo(camera.position);
      
      if (distance < 1000) {
        // High detail: show MRL, orbit trace, info
        sat.setLOD('high');
      } else if (distance < 5000) {
        // Medium detail: basic model, no trace
        sat.setLOD('medium');
      } else {
        // Low detail: simple dot
        sat.setLOD('low');
      }
    });
  }
}
```

### Frame Rate Management
```typescript
// Adaptive quality based on performance
const performanceMonitor = new PerformanceMonitor();

performanceMonitor.onFrameRateDrop((fps) => {
  if (fps < 30) {
    // Reduce quality
    renderer.setPixelRatio(1);
    scene.fog = new THREE.Fog(0x000000, 1000, 10000);
  } else if (fps > 50) {
    // Increase quality
    renderer.setPixelRatio(window.devicePixelRatio);
    scene.fog = null;
  }
});
```

## Integration Checklist

- [ ] Create shared D2 visualization context
- [ ] Implement satellite highlighting in 3D
- [ ] Add MRL visualization on globe
- [ ] Synchronize timeline controls
- [ ] Create handover animation effects
- [ ] Implement camera focus transitions
- [ ] Design responsive split-view layout
- [ ] Add performance monitoring
- [ ] Test cross-component synchronization
- [ ] Optimize for mobile devices

## Next Steps

1. Prototype shared state management
2. Enhance 3D globe with D2-specific features
3. Implement smooth animation system
4. Create unified timeline component
5. Test synchronization performance
6. Document API for future extensions