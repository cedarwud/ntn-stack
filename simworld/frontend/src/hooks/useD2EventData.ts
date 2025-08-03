/**
 * useD2EventData - Hook for fetching and managing D2 event data
 */

import { useState, useEffect } from 'react';

interface D2EventData {
    metadata: {
        constellation: string;
        time_span_minutes: number;
        d2_enhancement?: {
            thresholds: {
                thresh1: number;
                thresh2: number;
                hysteresis: number;
            };
        };
    };
    satellites: Array<{
        norad_id: number;
        name: string;
        constellation: string;
        mrl_distances: number[];
        moving_reference_locations: Array<{
            lat: number;
            lon: number;
        }>;
        positions: Array<{
            elevation_deg: number;
            azimuth_deg: number;
            range_km: number;
            is_visible: boolean;
            timestamp: string;
        }>;
        time_series?: Array<{
            timestamp: string;
            time_offset_seconds: number;
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            position: any;
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            observation: any;
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            handover_metrics: any;
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            measurement_events: any;
        }>;
    }>;
    timestamps: string[];
    d2_events: Array<{
        id: string;
        timestamp_start: string;
        timestamp_end: string;
        serving_satellite: {
            name: string;
            id: string;
        };
        target_satellite: {
            name: string;
            id: string;
        };
        ml1_start: number;
        ml1_end: number;
        ml2_start: number;
        ml2_end: number;
        duration_seconds: number;
    }>;
}

export function useD2EventData(constellation: 'starlink' | 'oneweb') {
    const [data, setData] = useState<D2EventData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<Error | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                setError(null);

                // Fetch from API endpoint
                const response = await fetch(`/api/v1/d2-events/data/${constellation}`);
                
                if (!response.ok) {
                    throw new Error(`Failed to fetch D2 data: ${response.statusText}`);
                }

                const jsonData = await response.json();
                setData(jsonData);
            } catch (err) {
                console.error('Error fetching D2 event data:', err);
                setError(err as Error);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [constellation]);

    return { data, loading, error };
}