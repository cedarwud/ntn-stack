export interface VisibleSatelliteInfo {
    norad_id: number;
    name: string;
    elevation_deg: number;
    azimuth_deg: number;
    distance_km: number;
    line1: string; // TLE line 1
    line2: string; // TLE line 2
    ecef_x_km?: number | null;
    ecef_y_km?: number | null;
    ecef_z_km?: number | null;
} 