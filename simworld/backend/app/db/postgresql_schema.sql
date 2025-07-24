-- SimWorld PostgreSQL Schema
-- 設備和地面站表結構，用於替代 MongoDB 存儲

-- 設備表 (替代 MongoDB devices collection)
CREATE TABLE IF NOT EXISTS devices (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    position_x FLOAT NOT NULL,
    position_y FLOAT NOT NULL,
    position_z FLOAT NOT NULL,
    orientation_x FLOAT NOT NULL,
    orientation_y FLOAT NOT NULL,
    orientation_z FLOAT NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('desired', 'jammer', 'receiver')),
    power_dbm FLOAT NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 地面站表 (替代 MongoDB ground_stations collection)  
CREATE TABLE IF NOT EXISTS ground_stations (
    id SERIAL PRIMARY KEY,
    station_identifier VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    latitude_deg FLOAT NOT NULL CHECK (latitude_deg >= -90 AND latitude_deg <= 90),
    longitude_deg FLOAT NOT NULL CHECK (longitude_deg >= -180 AND longitude_deg <= 180),
    altitude_m FLOAT NOT NULL DEFAULT 0.0,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 添加索引以提升查詢性能
CREATE INDEX IF NOT EXISTS idx_devices_active ON devices(active);
CREATE INDEX IF NOT EXISTS idx_devices_role ON devices(role);
CREATE INDEX IF NOT EXISTS idx_ground_stations_identifier ON ground_stations(station_identifier);
CREATE INDEX IF NOT EXISTS idx_ground_stations_location ON ground_stations(latitude_deg, longitude_deg);

-- 創建更新時間觸發器函數
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 為設備表添加更新時間觸發器
DROP TRIGGER IF EXISTS update_devices_updated_at ON devices;
CREATE TRIGGER update_devices_updated_at 
    BEFORE UPDATE ON devices 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 為地面站表添加更新時間觸發器  
DROP TRIGGER IF EXISTS update_ground_stations_updated_at ON ground_stations;
CREATE TRIGGER update_ground_stations_updated_at 
    BEFORE UPDATE ON ground_stations 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();