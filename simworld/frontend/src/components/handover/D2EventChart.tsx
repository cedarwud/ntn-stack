/**
 * D2EventChart - Real-time D2 Event Visualization Component
 * Uses enhanced satellite data with Moving Reference Location (MRL) calculations
 */

import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { useD2EventData } from '../../hooks/useD2EventData';
import './D2EventChart.scss';

interface D2EventChartProps {
    constellation: 'starlink' | 'oneweb';
    currentTime?: Date;
    onTimeSelect?: (time: Date) => void;
    thresholds?: {
        thresh1: number;
        thresh2: number;
        hysteresis: number;
    };
    height?: number;
}

export const D2EventChart: React.FC<D2EventChartProps> = ({
    constellation,
    currentTime,
    onTimeSelect,
    thresholds = { thresh1: 600, thresh2: 400, hysteresis: 20 },
    height = 400
}) => {
    const svgRef = useRef<SVGSVGElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const [dimensions, setDimensions] = useState({ width: 0, height });
    const { data, loading, error } = useD2EventData(constellation);

    // Handle responsive sizing
    useEffect(() => {
        const handleResize = () => {
            if (containerRef.current) {
                const { width } = containerRef.current.getBoundingClientRect();
                setDimensions({ width: Math.max(width, 800), height });
            }
        };

        // Initial sizing - ensure immediate full width
        handleResize();
        
        // Also trigger after a short delay to catch any late layout changes
        const timer = setTimeout(handleResize, 50);
        
        window.addEventListener('resize', handleResize);
        return () => {
            clearTimeout(timer);
            window.removeEventListener('resize', handleResize);
        };
    }, [height]);

    // Additional effect to ensure sizing when component mounts
    useEffect(() => {
        const ensureProperSizing = () => {
            if (containerRef.current) {
                const { width } = containerRef.current.getBoundingClientRect();
                if (width > 0) {
                    setDimensions({ width: Math.max(width, 800), height });
                } else {
                    // Fallback: Use a reasonable default width if container not ready
                    setDimensions({ width: 1200, height });
                }
            }
        };

        // Immediate sizing attempt
        ensureProperSizing();
        
        // Progressive attempts with increasing delays
        const timer1 = setTimeout(ensureProperSizing, 10);
        const timer2 = setTimeout(ensureProperSizing, 50);
        const timer3 = setTimeout(ensureProperSizing, 100);
        const timer4 = setTimeout(ensureProperSizing, 200);
        
        return () => {
            clearTimeout(timer1);
            clearTimeout(timer2);
            clearTimeout(timer3);
            clearTimeout(timer4);
        };
    }, [height]);

    // Force update when data is loaded
    useEffect(() => {
        if (data && containerRef.current) {
            const { width } = containerRef.current.getBoundingClientRect();
            if (width > 0) {
                setDimensions({ width: Math.max(width, 800), height });
            }
        }
    }, [data, height]);

    // Render D3 chart
    useEffect(() => {
        if (!data || !svgRef.current || loading || dimensions.width === 0) return;

        const svg = d3.select(svgRef.current);
        const margin = { top: 20, right: 10, bottom: 50, left: 70 };
        const width = dimensions.width - margin.left - margin.right;
        const height = dimensions.height - margin.top - margin.bottom;

        // Clear previous content
        svg.selectAll('*').remove();

        const g = svg
            .append('g')
            .attr('transform', `translate(${margin.left},${margin.top})`);

        // Extract timestamps from satellite time_series data
        let timestamps: Date[] = [];
        
        // Always extract from satellite time_series as that's where our data is
        if (data.satellites && data.satellites.length > 0 && data.satellites[0].time_series) {
            timestamps = data.satellites[0].time_series
                .map(entry => {
                    const date = new Date(entry.timestamp);
                    return isNaN(date.getTime()) ? null : date;
                })
                .filter(date => date !== null) as Date[];
        } else if (data.timestamps && data.timestamps.length > 0) {
            // Fallback to main timestamps array if available
            timestamps = data.timestamps
                .map(ts => {
                    const date = new Date(ts);
                    return isNaN(date.getTime()) ? null : date;
                })
                .filter(date => date !== null) as Date[];
        }

        // Ensure we have valid timestamps
        if (timestamps.length === 0) {
            g.append('text')
                .attr('x', width / 2)
                .attr('y', height / 2)
                .attr('text-anchor', 'middle')
                .style('fill', '#ccc')
                .text('無有效的時間戳數據');
            return;
        }

        // Find serving and target satellites with valid data
        const satellites = data.satellites.filter(sat => 
            sat.mrl_distances && 
            sat.mrl_distances.length > 0 &&
            sat.mrl_distances.some(d => d != null && !isNaN(d) && isFinite(d))
        );

        if (satellites.length < 2) {
            g.append('text')
                .attr('x', width / 2)
                .attr('y', height / 2)
                .attr('text-anchor', 'middle')
                .style('fill', '#ccc')
                .text('衛星數據不足，無法顯示 D2 可視化');
            return;
        }

        // Use first two satellites as serving/target for demo
        const servingSat = satellites[0];
        const targetSat = satellites[1];

        // Clean and validate satellite data - use null for invalid data instead of 0
        const cleanMrlData = (distances: number[]) => {
            const cleaned = distances.map(d => (d != null && !isNaN(d) && isFinite(d)) ? d : null);
            // Ensure data length matches timestamps
            const expectedLength = timestamps.length;
            if (cleaned.length < expectedLength) {
                // Pad with nulls if too short (gaps in data)
                return [...cleaned, ...Array(expectedLength - cleaned.length).fill(null)];
            } else if (cleaned.length > expectedLength) {
                // Trim if too long
                return cleaned.slice(0, expectedLength);
            }
            return cleaned;
        };

        const cleanServingDistances = cleanMrlData(servingSat.mrl_distances);
        const cleanTargetDistances = cleanMrlData(targetSat.mrl_distances);

        // Scales
        const xScale = d3.scaleTime()
            .domain(d3.extent(timestamps) as [Date, Date])
            .range([0, width]);

        const yScale = d3.scaleLinear()
            .domain([
                0,
                d3.max([
                    ...cleanServingDistances.filter(d => d !== null),
                    ...cleanTargetDistances.filter(d => d !== null),
                    thresholds.thresh1 + 100
                ]) as number
            ])
            .range([height, 0]);

        // Line generators with bounds checking
        const servingLine = d3.line<number>()
            .x((_, i) => {
                if (i >= timestamps.length) return 0;
                const time = timestamps[i];
                const x = xScale(time);
                return isNaN(x) || !isFinite(x) ? 0 : x;
            })
            .y(d => {
                const y = yScale(d);
                return isNaN(y) || !isFinite(y) ? 0 : y;
            })
            .defined(d => d !== null && !isNaN(d) && isFinite(d))
            .curve(d3.curveMonotoneX);

        const targetLine = d3.line<number>()
            .x((_, i) => {
                if (i >= timestamps.length) return 0;
                const time = timestamps[i];
                const x = xScale(time);
                return isNaN(x) || !isFinite(x) ? 0 : x;
            })
            .y(d => {
                const y = yScale(d);
                return isNaN(y) || !isFinite(y) ? 0 : y;
            })
            .defined(d => d !== null && !isNaN(d) && isFinite(d))
            .curve(d3.curveMonotoneX);

        // Draw threshold zones
        // Thresh1 zone (serving satellite threshold)
        g.append('rect')
            .attr('x', 0)
            .attr('y', yScale(thresholds.thresh1 + thresholds.hysteresis))
            .attr('width', width)
            .attr('height', Math.abs(
                yScale(thresholds.thresh1 - thresholds.hysteresis) - 
                yScale(thresholds.thresh1 + thresholds.hysteresis)
            ))
            .attr('fill', '#22c55e')
            .attr('opacity', 0.1);

        g.append('line')
            .attr('x1', 0)
            .attr('x2', width)
            .attr('y1', yScale(thresholds.thresh1))
            .attr('y2', yScale(thresholds.thresh1))
            .attr('stroke', '#22c55e')
            .attr('stroke-dasharray', '5,5')
            .attr('stroke-width', 2);

        // Thresh2 zone (target satellite threshold)
        g.append('rect')
            .attr('x', 0)
            .attr('y', yScale(thresholds.thresh2 + thresholds.hysteresis))
            .attr('width', width)
            .attr('height', Math.abs(
                yScale(thresholds.thresh2 - thresholds.hysteresis) - 
                yScale(thresholds.thresh2 + thresholds.hysteresis)
            ))
            .attr('fill', '#f97316')
            .attr('opacity', 0.1);

        g.append('line')
            .attr('x1', 0)
            .attr('x2', width)
            .attr('y1', yScale(thresholds.thresh2))
            .attr('y2', yScale(thresholds.thresh2))
            .attr('stroke', '#f97316')
            .attr('stroke-dasharray', '5,5')
            .attr('stroke-width', 2);

        // Draw lines
        g.append('path')
            .datum(cleanServingDistances)
            .attr('class', 'line serving')
            .attr('d', servingLine)
            .style('stroke', '#22c55e')
            .style('stroke-width', 2)
            .style('fill', 'none');

        g.append('path')
            .datum(cleanTargetDistances)
            .attr('class', 'line target')
            .attr('d', targetLine)
            .style('stroke', '#f97316')
            .style('stroke-width', 2)
            .style('fill', 'none');

        // Axes
        const xAxis = d3.axisBottom(xScale)
            .tickFormat(d3.timeFormat('%H:%M'));

        const xAxisGroup = g.append('g')
            .attr('transform', `translate(0,${height})`)
            .call(xAxis);
        
        xAxisGroup.selectAll('text')
            .style('font-size', '14px')
            .style('fill', '#ccc');
            
        xAxisGroup.append('text')
            .attr('x', width / 2)
            .attr('y', 40)
            .attr('fill', '#ccc')
            .style('text-anchor', 'middle')
            .style('font-size', '16px')
            .text('時間');

        const yAxis = d3.axisLeft(yScale);

        const yAxisGroup = g.append('g')
            .call(yAxis);
        
        yAxisGroup.selectAll('text')
            .style('font-size', '14px')
            .style('fill', '#ccc');
            
        yAxisGroup.append('text')
            .attr('transform', 'rotate(-90)')
            .attr('y', -50)
            .attr('x', -height / 2)
            .attr('fill', '#ccc')
            .style('text-anchor', 'middle')
            .style('font-size', '16px')
            .text('到 MRL 的距離 (km)');

        // Legend removed from chart area - moved to title area

        // Current time indicator
        if (currentTime) {
            const x = xScale(currentTime);
            
            g.append('line')
                .attr('class', 'time-indicator')
                .attr('x1', x)
                .attr('x2', x)
                .attr('y1', 0)
                .attr('y2', height)
                .style('stroke', '#3b82f6')
                .style('stroke-width', 2)
                .style('stroke-dasharray', '3,3');
        }

        // Interactive overlay
        const bisect = d3.bisector<Date, Date>(d => d).left;

        const focus = g.append('g')
            .style('display', 'none');

        focus.append('circle')
            .attr('class', 'serving-focus')
            .attr('r', 4)
            .style('fill', '#22c55e');

        focus.append('circle')
            .attr('class', 'target-focus')
            .attr('r', 4)
            .style('fill', '#f97316');

        focus.append('line')
            .attr('class', 'focus-line')
            .style('stroke', '#666')
            .style('stroke-dasharray', '3,3')
            .attr('y1', 0)
            .attr('y2', height);

        const tooltip = focus.append('g')
            .attr('class', 'tooltip');

        tooltip.append('rect')
            .attr('width', 140)
            .attr('height', 60)
            .attr('x', -70)
            .attr('y', -70)
            .style('fill', 'white')
            .style('stroke', '#666')
            .style('stroke-width', 1)
            .style('opacity', 0.9);

        tooltip.append('text')
            .attr('class', 'tooltip-text')
            .attr('x', -65)
            .attr('y', -50)
            .style('font-size', '12px');

        g.append('rect')
            .attr('width', width)
            .attr('height', height)
            .style('fill', 'none')
            .style('pointer-events', 'all')
            .on('mouseover', () => focus.style('display', null))
            .on('mouseout', () => focus.style('display', 'none'))
            .on('mousemove', function(event) {
                const [mouseX] = d3.pointer(event);
                const x0 = xScale.invert(mouseX);
                const i = bisect(timestamps, x0, 1);
                
                // Validate bounds and existence of timestamps
                if (i <= 0 || i >= timestamps.length) return;
                
                const d0 = timestamps[i - 1];
                const d1 = timestamps[i];
                
                // Check if both timestamps exist
                if (!d0 || !d1) return;
                
                const d = x0.getTime() - d0.getTime() > d1.getTime() - x0.getTime() ? d1 : d0;
                const idx = timestamps.findIndex(t => t && t.getTime() === d.getTime());

                // Validate index bounds
                if (idx < 0 || idx >= cleanServingDistances.length || idx >= cleanTargetDistances.length) {
                    return;
                }

                const x = xScale(d);
                const servingDistance = cleanServingDistances[idx];
                const targetDistance = cleanTargetDistances[idx];
                
                // Handle null values gracefully
                const y1 = servingDistance !== null ? yScale(servingDistance) : height;
                const y2 = targetDistance !== null ? yScale(targetDistance) : height;

                focus.select('.serving-focus').attr('transform', `translate(${x},${y1})`);
                focus.select('.target-focus').attr('transform', `translate(${x},${y2})`);
                focus.select('.focus-line').attr('x1', x).attr('x2', x);

                tooltip.attr('transform', `translate(${x},${Math.min(y1, y2) - 10})`);
                tooltip.select('.tooltip-text').html(
                    `Time: ${d3.timeFormat('%H:%M:%S')(d)}<tspan x="-65" dy="15">Ml1: ${servingDistance !== null ? servingDistance.toFixed(1) : 'N/A'} km</tspan><tspan x="-65" dy="15">Ml2: ${targetDistance !== null ? targetDistance.toFixed(1) : 'N/A'} km</tspan>`
                );
            })
            .on('click', function(event) {
                const [mouseX] = d3.pointer(event);
                const x0 = xScale.invert(mouseX);
                onTimeSelect?.(x0);
            });

        // D2 event markers removed - deterministic prediction not realistic
        // Real handover decisions should be probabilistic based on multiple factors

    }, [data, dimensions, currentTime, onTimeSelect, thresholds, loading]);

    if (loading) {
        return (
            <div className="d2-event-chart-card">
                <div className="d2-event-chart-content">
                    <div className="loading-container" style={{ height }}>
                        <div className="loading-spinner" />
                        <p>載入衛星數據中...</p>
                    </div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="d2-event-chart-card">
                <div className="d2-event-chart-content">
                    <p className="error-message">載入 D2 事件數據時發生錯誤: {error.message}</p>
                </div>
            </div>
        );
    }

    // Get satellite names for legend
    const servingSatName = data?.satellites?.[0]?.name || 'N/A';
    const targetSatName = data?.satellites?.[1]?.name || 'N/A';

    return (
        <div className="d2-event-chart-card">
            <div className="d2-event-chart-content">
                <h3 className="chart-title">D2 事件圖表 - 真實衛星數據</h3>
                <p className="chart-subtitle">
                    衛星換手檢測的 Moving Reference Location (MRL) 距離
                </p>
                
                {/* Legend moved below title */}
                {data && data.satellites && data.satellites.length >= 2 && (
                    <div className="chart-legend">
                        <div className="legend-item">
                            <div className="legend-line serving"></div>
                            <span>服務衛星: {servingSatName}</span>
                        </div>
                        <div className="legend-item">
                            <div className="legend-line target"></div>
                            <span>目標衛星: {targetSatName}</span>
                        </div>
                    </div>
                )}
                
                <div ref={containerRef} className="chart-container">
                    <svg 
                        ref={svgRef} 
                        width={dimensions.width || 1200} 
                        height={dimensions.height}
                        style={{ width: '100%', height: 'auto' }}
                    />
                </div>
            </div>
        </div>
    );
};

export default D2EventChart;