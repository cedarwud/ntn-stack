# D2 Event Chart Implementation Guide

## Overview

This document details the implementation of interactive D2 event charts using real satellite data, replacing the current simulated visualization.

## Chart Requirements

### Visual Elements
1. **Dual Distance Lines**:
   - Green: Serving satellite MRL distance (Ml1)
   - Orange: Target satellite MRL distance (Ml2)

2. **Threshold Indicators**:
   - Horizontal lines for Thresh1 and Thresh2
   - Shaded hysteresis zones

3. **Event Markers**:
   - Vertical lines at handover trigger points
   - Duration indicators for event windows

4. **Interactive Features**:
   - Hover tooltips with exact values
   - Click to select time point
   - Zoom/pan for detailed analysis

## React Component Architecture

### Main Component Structure
```typescript
// D2EventChart.tsx
import React, { useEffect, useState, useRef } from 'react';
import * as d3 from 'd3';
import { useD2EventData } from './hooks/useD2EventData';
import { useTimelineSync } from './hooks/useTimelineSync';

interface D2EventChartProps {
  constellation: 'starlink' | 'oneweb';
  timeRange: { start: Date; end: Date };
  onTimeSelect: (timestamp: Date) => void;
  thresholds?: {
    thresh1: number;
    thresh2: number;
    hysteresis: number;
  };
}

export const D2EventChart: React.FC<D2EventChartProps> = ({
  constellation,
  timeRange,
  onTimeSelect,
  thresholds = { thresh1: 500, thresh2: 300, hysteresis: 20 }
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const { data, loading } = useD2EventData(constellation, timeRange);
  const { currentTime, setCurrentTime } = useTimelineSync();
  
  useEffect(() => {
    if (!data || loading) return;
    
    renderChart(svgRef.current, data, {
      thresholds,
      currentTime,
      onTimeSelect: (time) => {
        setCurrentTime(time);
        onTimeSelect(time);
      }
    });
  }, [data, currentTime, thresholds]);
  
  return (
    <div className="d2-event-chart">
      <svg ref={svgRef} width={800} height={400} />
      {loading && <div className="loading">Loading satellite data...</div>}
    </div>
  );
};
```

### D3.js Chart Rendering
```typescript
// chartRenderer.ts
import * as d3 from 'd3';

interface ChartData {
  timestamps: Date[];
  servingDistances: number[];
  targetDistances: number[];
  events: D2Event[];
}

export function renderChart(
  svg: SVGSVGElement,
  data: ChartData,
  options: ChartOptions
) {
  const margin = { top: 20, right: 80, bottom: 50, left: 70 };
  const width = 800 - margin.left - margin.right;
  const height = 400 - margin.top - margin.bottom;
  
  // Clear previous content
  d3.select(svg).selectAll("*").remove();
  
  const g = d3.select(svg)
    .append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);
  
  // Scales
  const xScale = d3.scaleTime()
    .domain(d3.extent(data.timestamps) as [Date, Date])
    .range([0, width]);
    
  const yScale = d3.scaleLinear()
    .domain([0, d3.max([
      ...data.servingDistances,
      ...data.targetDistances
    ]) as number * 1.1])
    .range([height, 0]);
  
  // Line generators
  const servingLine = d3.line<number>()
    .x((_, i) => xScale(data.timestamps[i]))
    .y(d => yScale(d))
    .curve(d3.curveMonotoneX);
    
  const targetLine = d3.line<number>()
    .x((_, i) => xScale(data.timestamps[i]))
    .y(d => yScale(d))
    .curve(d3.curveMonotoneX);
  
  // Draw threshold zones
  drawThresholdZones(g, xScale, yScale, width, options.thresholds);
  
  // Draw lines
  g.append("path")
    .datum(data.servingDistances)
    .attr("class", "line serving")
    .attr("d", servingLine)
    .style("stroke", "#22c55e")
    .style("stroke-width", 2)
    .style("fill", "none");
    
  g.append("path")
    .datum(data.targetDistances)
    .attr("class", "line target")
    .attr("d", targetLine)
    .style("stroke", "#f97316")
    .style("stroke-width", 2)
    .style("fill", "none");
  
  // Draw D2 events
  drawD2Events(g, data.events, xScale, yScale, height);
  
  // Add interactive elements
  addInteractivity(g, data, xScale, yScale, options);
  
  // Axes
  g.append("g")
    .attr("transform", `translate(0,${height})`)
    .call(d3.axisBottom(xScale).tickFormat(d3.timeFormat("%H:%M")));
    
  g.append("g")
    .call(d3.axisLeft(yScale));
  
  // Labels
  addLabels(g, width, height);
}

function drawThresholdZones(g, xScale, yScale, width, thresholds) {
  const { thresh1, thresh2, hysteresis } = thresholds;
  
  // Thresh1 zone (serving satellite)
  g.append("rect")
    .attr("x", 0)
    .attr("y", yScale(thresh1 + hysteresis))
    .attr("width", width)
    .attr("height", yScale(thresh1 - hysteresis) - yScale(thresh1 + hysteresis))
    .attr("fill", "#22c55e")
    .attr("opacity", 0.1);
    
  g.append("line")
    .attr("x1", 0)
    .attr("x2", width)
    .attr("y1", yScale(thresh1))
    .attr("y2", yScale(thresh1))
    .attr("stroke", "#22c55e")
    .attr("stroke-dasharray", "5,5");
    
  // Thresh2 zone (target satellite)
  g.append("rect")
    .attr("x", 0)
    .attr("y", yScale(thresh2 + hysteresis))
    .attr("width", width)
    .attr("height", yScale(thresh2 - hysteresis) - yScale(thresh2 + hysteresis))
    .attr("fill", "#f97316")
    .attr("opacity", 0.1);
}

function drawD2Events(g, events, xScale, yScale, height) {
  events.forEach(event => {
    const x = xScale(new Date(event.timestamp));
    
    // Event marker line
    g.append("line")
      .attr("x1", x)
      .attr("x2", x)
      .attr("y1", 0)
      .attr("y2", height)
      .attr("stroke", "#ef4444")
      .attr("stroke-width", 2)
      .attr("opacity", 0.7);
      
    // Event label
    g.append("text")
      .attr("x", x)
      .attr("y", -5)
      .attr("text-anchor", "middle")
      .attr("font-size", "12px")
      .attr("fill", "#ef4444")
      .text("D2");
  });
}
```

### Data Hook Implementation
```typescript
// hooks/useD2EventData.ts
import { useState, useEffect } from 'react';
import { fetchD2EventData } from '../api/d2EventApi';

export function useD2EventData(constellation: string, timeRange: TimeRange) {
  const [data, setData] = useState<D2EventData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const response = await fetchD2EventData({
          constellation,
          startTime: timeRange.start,
          endTime: timeRange.end
        });
        
        // Transform data for chart
        const chartData = transformForChart(response);
        setData(chartData);
      } catch (err) {
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    };
    
    loadData();
  }, [constellation, timeRange]);
  
  return { data, loading, error };
}

function transformForChart(rawData: any): D2EventData {
  // Extract serving and target satellite data
  const servingSat = rawData.satellites.find(s => s.role === 'serving');
  const targetSat = rawData.satellites.find(s => s.role === 'target');
  
  return {
    timestamps: rawData.timestamps.map(t => new Date(t)),
    servingDistances: servingSat.mrl_distances,
    targetDistances: targetSat.mrl_distances,
    events: rawData.d2_events
  };
}
```

### Timeline Synchronization Hook
```typescript
// hooks/useTimelineSync.ts
import { useContext } from 'react';
import { TimelineContext } from '../contexts/TimelineContext';

export function useTimelineSync() {
  const context = useContext(TimelineContext);
  
  if (!context) {
    throw new Error('useTimelineSync must be used within TimelineProvider');
  }
  
  return {
    currentTime: context.currentTime,
    setCurrentTime: context.setCurrentTime,
    isPlaying: context.isPlaying,
    playbackSpeed: context.playbackSpeed
  };
}
```

## Styling and Animations

### CSS Styles
```scss
// D2EventChart.scss
.d2-event-chart {
  position: relative;
  background: #1f2937;
  border-radius: 8px;
  padding: 20px;
  
  svg {
    width: 100%;
    height: auto;
  }
  
  .loading {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    color: #9ca3af;
  }
  
  // Animated current time indicator
  .time-indicator {
    transition: transform 0.1s ease-out;
    
    line {
      stroke: #3b82f6;
      stroke-width: 2;
    }
  }
  
  // Tooltip styles
  .tooltip {
    position: absolute;
    background: rgba(0, 0, 0, 0.9);
    color: white;
    padding: 8px 12px;
    border-radius: 4px;
    font-size: 12px;
    pointer-events: none;
    
    &::after {
      content: '';
      position: absolute;
      bottom: -4px;
      left: 50%;
      transform: translateX(-50%);
      border-style: solid;
      border-width: 4px 4px 0 4px;
      border-color: rgba(0, 0, 0, 0.9) transparent transparent transparent;
    }
  }
}
```

### Smooth Animations
```typescript
// Add to chartRenderer.ts
function animateTimeIndicator(g, xScale, currentTime) {
  const x = xScale(currentTime);
  
  let indicator = g.select('.time-indicator');
  
  if (indicator.empty()) {
    indicator = g.append('g')
      .attr('class', 'time-indicator');
      
    indicator.append('line')
      .attr('y1', 0)
      .attr('y2', height);
  }
  
  indicator
    .transition()
    .duration(100)
    .attr('transform', `translate(${x}, 0)`);
}
```

## Performance Optimizations

### 1. Data Decimation
```typescript
function decimateData(data: number[], targetPoints: number): number[] {
  if (data.length <= targetPoints) return data;
  
  const ratio = Math.floor(data.length / targetPoints);
  return data.filter((_, i) => i % ratio === 0);
}
```

### 2. Virtual Scrolling for Long Time Series
```typescript
function getVisibleDataWindow(
  fullData: ChartData,
  visibleTimeRange: [Date, Date]
): ChartData {
  const startIdx = d3.bisectLeft(fullData.timestamps, visibleTimeRange[0]);
  const endIdx = d3.bisectRight(fullData.timestamps, visibleTimeRange[1]);
  
  return {
    timestamps: fullData.timestamps.slice(startIdx, endIdx),
    servingDistances: fullData.servingDistances.slice(startIdx, endIdx),
    targetDistances: fullData.targetDistances.slice(startIdx, endIdx),
    events: fullData.events.filter(e => 
      e.timestamp >= visibleTimeRange[0] && 
      e.timestamp <= visibleTimeRange[1]
    )
  };
}
```

### 3. WebGL Rendering for Large Datasets
```typescript
// For 70+ satellites, consider WebGL
import { WebGLRenderer } from './webgl/WebGLRenderer';

function renderLargeDataset(canvas: HTMLCanvasElement, data: LargeDataset) {
  const renderer = new WebGLRenderer(canvas);
  renderer.renderLines(data);
}
```

## Integration with Existing System

### 1. Update D2DataProcessingDemo.tsx
```typescript
import { D2EventChart } from './components/D2EventChart';

// Replace mock chart with real data chart
<D2EventChart
  constellation="starlink"
  timeRange={selectedTimeRange}
  onTimeSelect={handleTimeSelect}
  thresholds={d2Thresholds}
/>
```

### 2. Add to Handover Events Page
```typescript
// Add tab for real vs simulated comparison
<Tabs>
  <TabPanel label="Real Data">
    <D2EventChart constellation={selectedConstellation} />
  </TabPanel>
  <TabPanel label="Simulated">
    <MockD2Chart />
  </TabPanel>
  <TabPanel label="Comparison">
    <D2ComparisonView />
  </TabPanel>
</Tabs>
```

## Testing Strategy

### Unit Tests
```typescript
describe('D2EventChart', () => {
  it('renders distance lines correctly', () => {
    const { container } = render(
      <D2EventChart constellation="starlink" timeRange={testRange} />
    );
    
    expect(container.querySelector('.line.serving')).toBeInTheDocument();
    expect(container.querySelector('.line.target')).toBeInTheDocument();
  });
  
  it('highlights D2 events', () => {
    // Test event markers appear at correct timestamps
  });
  
  it('synchronizes with timeline', () => {
    // Test time indicator moves with global timeline
  });
});
```

### Performance Tests
- Render 120 minutes of data (720 points) < 100ms
- Smooth 60fps animation during playback
- Memory usage < 50MB for full dataset

## Next Steps

1. Implement base chart component
2. Connect to enhanced preprocessing API
3. Add interactive features
4. Integrate with timeline system
5. Performance optimization
6. User testing and refinement