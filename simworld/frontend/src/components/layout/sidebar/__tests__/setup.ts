// Test setup for sidebar modules
export const mockDevice = {
    id: 1,
    name: 'Test Device',
    role: 'receiver' as const,
    position_x: 0,
    position_y: 0,
    position_z: 0,
    orientation_x: 0,
    orientation_y: 0,
    orientation_z: 0,
    power_dbm: -10,
    active: true
}

export const mockSatellite = {
    norad_id: 12345,
    name: 'Test Satellite',
    elevation_deg: 45,
    azimuth_deg: 180,
    distance_km: 500,
    line1: '1 12345U 20001001.00000000  .00000000  00000-0  00000-0 0  9999',
    line2: '2 12345  53.0000   0.0000 0000000   0.0000   0.0000 15.50000000000000',
    constellation: 'TEST' as const
}

export const mockFeatureToggle = {
    id: 'test-toggle',
    label: 'Test Toggle',
    category: 'uav' as const,
    enabled: false,
    onToggle: jest.fn(),
    icon: '🧪',
    description: 'Test toggle description'
}