-- 🛰️ 衛星軌道數據緩存表 - 統一數據架構
-- 避免數據重複，與 RL 系統共享衛星數據

-- TLE 數據主表
CREATE TABLE IF NOT EXISTS satellite_tle_data (
    id BIGSERIAL PRIMARY KEY,
    satellite_id VARCHAR(50) NOT NULL,
    norad_id INTEGER UNIQUE NOT NULL,
    satellite_name VARCHAR(100) NOT NULL,
    constellation VARCHAR(20) NOT NULL, -- starlink, oneweb, gps, etc.
    line1 TEXT NOT NULL, -- TLE 第一行
    line2 TEXT NOT NULL, -- TLE 第二行
    epoch TIMESTAMP WITH TIME ZONE NOT NULL,
    classification CHAR(1) DEFAULT 'U',
    international_designator VARCHAR(20),
    element_set_number INTEGER,
    mean_motion FLOAT, -- 平均運動 (每日軌道數)
    eccentricity FLOAT, -- 偏心率
    inclination FLOAT, -- 傾斜角 (度)
    raan FLOAT, -- 升交點赤經 (度)
    arg_perigee FLOAT, -- 近地點幅角 (度)
    mean_anomaly FLOAT, -- 平近點角 (度)
    orbital_period FLOAT, -- 軌道週期 (分鐘)
    apogee_altitude FLOAT, -- 遠地點高度 (km)
    perigee_altitude FLOAT, -- 近地點高度 (km)
    is_active BOOLEAN DEFAULT TRUE,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 索引優化
CREATE INDEX IF NOT EXISTS idx_tle_constellation ON satellite_tle_data (constellation, is_active);
CREATE INDEX IF NOT EXISTS idx_tle_norad ON satellite_tle_data (norad_id);
CREATE INDEX IF NOT EXISTS idx_tle_updated ON satellite_tle_data (last_updated);
CREATE INDEX IF NOT EXISTS idx_tle_epoch ON satellite_tle_data (epoch);

-- 衛星軌道位置緩存表 (預計算的軌道數據)
CREATE TABLE IF NOT EXISTS satellite_orbital_cache (
    id BIGSERIAL PRIMARY KEY,
    satellite_id VARCHAR(50) NOT NULL,
    norad_id INTEGER NOT NULL,
    constellation VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    -- ECI 座標 (km)
    position_x FLOAT NOT NULL,
    position_y FLOAT NOT NULL, 
    position_z FLOAT NOT NULL,
    -- 地理座標
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    altitude FLOAT NOT NULL, -- km
    -- 速度向量 (km/s)
    velocity_x FLOAT,
    velocity_y FLOAT,
    velocity_z FLOAT,
    -- 軌道參數
    orbital_period FLOAT, -- 分鐘
    elevation_angle FLOAT, -- 仰角 (相對於地面站)
    azimuth_angle FLOAT, -- 方位角
    range_rate FLOAT, -- 距離變化率 (km/s)
    -- 元數據
    calculation_method VARCHAR(20) DEFAULT 'SGP4',
    data_quality FLOAT DEFAULT 1.0, -- 0-1, 數據質量評分
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- 外鍵約束
    FOREIGN KEY (norad_id) REFERENCES satellite_tle_data(norad_id) ON DELETE CASCADE,
    -- 唯一約束
    UNIQUE(satellite_id, timestamp)
);

-- 軌道緩存索引
CREATE INDEX IF NOT EXISTS idx_orbital_satellite_time ON satellite_orbital_cache (satellite_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_orbital_constellation_time ON satellite_orbital_cache (constellation, timestamp);
CREATE INDEX IF NOT EXISTS idx_orbital_position ON satellite_orbital_cache (latitude, longitude, timestamp);
CREATE INDEX IF NOT EXISTS idx_orbital_quality ON satellite_orbital_cache (data_quality, timestamp);

-- D2 測量事件緩存表
CREATE TABLE IF NOT EXISTS d2_measurement_cache (
    id BIGSERIAL PRIMARY KEY,
    scenario_name VARCHAR(100) NOT NULL,
    scenario_hash VARCHAR(64) NOT NULL, -- 場景參數的 hash，用於快速查找
    -- UE 位置
    ue_latitude FLOAT NOT NULL,
    ue_longitude FLOAT NOT NULL,
    ue_altitude FLOAT NOT NULL,
    -- 參考位置 (固定和移動)
    fixed_ref_latitude FLOAT NOT NULL,
    fixed_ref_longitude FLOAT NOT NULL,
    fixed_ref_altitude FLOAT NOT NULL,
    moving_ref_latitude FLOAT, -- 移動參考位置 (衛星位置)
    moving_ref_longitude FLOAT,
    moving_ref_altitude FLOAT,
    -- 衛星信息
    satellite_id VARCHAR(50) NOT NULL,
    norad_id INTEGER NOT NULL,
    constellation VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    -- D2 測量值
    satellite_distance FLOAT NOT NULL, -- UE 到移動參考位置 (衛星) 的距離 (m)
    ground_distance FLOAT NOT NULL, -- UE 到固定參考位置的距離 (m)
    -- D2 事件參數
    thresh1 FLOAT NOT NULL, -- 閾值1 (m)
    thresh2 FLOAT NOT NULL, -- 閾值2 (m)
    hysteresis FLOAT NOT NULL, -- 滯後值 (m)
    -- D2 事件狀態
    trigger_condition_met BOOLEAN DEFAULT FALSE,
    entering_condition BOOLEAN DEFAULT FALSE, -- 進入條件
    leaving_condition BOOLEAN DEFAULT FALSE, -- 離開條件
    event_type VARCHAR(20), -- 'entering', 'leaving', 'none'
    -- 信號質量指標
    signal_strength FLOAT, -- dBm
    snr FLOAT, -- 信噪比 dB
    -- 元數據
    calculation_time_ms FLOAT, -- 計算耗時
    data_source VARCHAR(20) DEFAULT 'real', -- 'real', 'simulated'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- 外鍵約束 (移除有問題的約束以避免數據插入問題)
    FOREIGN KEY (norad_id) REFERENCES satellite_tle_data(norad_id) ON DELETE CASCADE
    -- 注意：移除了 satellite_orbital_cache 的外鍵約束，因為軌道數據可能不完整
);

-- D2 測量緩存索引
CREATE INDEX IF NOT EXISTS idx_d2_scenario_hash ON d2_measurement_cache (scenario_hash, timestamp);
CREATE INDEX IF NOT EXISTS idx_d2_scenario_name ON d2_measurement_cache (scenario_name, timestamp);
CREATE INDEX IF NOT EXISTS idx_d2_satellite_time ON d2_measurement_cache (satellite_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_d2_trigger_events ON d2_measurement_cache (trigger_condition_met, event_type, timestamp);
CREATE INDEX IF NOT EXISTS idx_d2_constellation ON d2_measurement_cache (constellation, timestamp);

-- 數據預載任務記錄表
CREATE TABLE IF NOT EXISTS satellite_data_preload_jobs (
    id BIGSERIAL PRIMARY KEY,
    job_name VARCHAR(100) NOT NULL,
    job_type VARCHAR(50) NOT NULL, -- 'tle_update', 'orbital_precompute', 'd2_precompute'
    constellation VARCHAR(20),
    time_range_start TIMESTAMP WITH TIME ZONE,
    time_range_end TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed'
    progress_percentage FLOAT DEFAULT 0.0,
    satellites_processed INTEGER DEFAULT 0,
    total_satellites INTEGER DEFAULT 0,
    records_created INTEGER DEFAULT 0,
    error_message TEXT,
    execution_time_ms BIGINT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50) DEFAULT 'system'
);

-- 預載任務索引
CREATE INDEX IF NOT EXISTS idx_preload_status ON satellite_data_preload_jobs (status, job_type);
CREATE INDEX IF NOT EXISTS idx_preload_constellation ON satellite_data_preload_jobs (constellation, status);
CREATE INDEX IF NOT EXISTS idx_preload_time ON satellite_data_preload_jobs (created_at);

-- 視圖：活躍衛星概覽
CREATE OR REPLACE VIEW active_satellites_overview AS
SELECT 
    constellation,
    COUNT(*) as total_satellites,
    COUNT(CASE WHEN is_active THEN 1 END) as active_satellites,
    MAX(last_updated) as latest_update,
    MIN(epoch) as oldest_tle,
    MAX(epoch) as newest_tle,
    AVG(orbital_period) as avg_orbital_period
FROM satellite_tle_data 
GROUP BY constellation;

-- 視圖：D2 事件統計
CREATE OR REPLACE VIEW d2_events_summary AS
SELECT 
    constellation,
    scenario_name,
    DATE(timestamp) as event_date,
    COUNT(*) as total_measurements,
    COUNT(CASE WHEN trigger_condition_met THEN 1 END) as triggered_events,
    COUNT(CASE WHEN event_type = 'entering' THEN 1 END) as entering_events,
    COUNT(CASE WHEN event_type = 'leaving' THEN 1 END) as leaving_events,
    AVG(satellite_distance) as avg_satellite_distance,
    AVG(ground_distance) as avg_ground_distance
FROM d2_measurement_cache 
GROUP BY constellation, scenario_name, DATE(timestamp);

-- 註釋
COMMENT ON TABLE satellite_tle_data IS '衛星 TLE 數據主表，存儲所有星座的軌道要素';
COMMENT ON TABLE satellite_orbital_cache IS '預計算的衛星軌道位置緩存，避免重複 SGP4 計算';
COMMENT ON TABLE d2_measurement_cache IS 'D2 測量事件緩存，支援快速圖表渲染';
COMMENT ON TABLE satellite_data_preload_jobs IS '數據預載任務記錄，支援定期更新和監控';

-- 初始化一些測試數據 (可選)
-- INSERT INTO satellite_tle_data (satellite_id, norad_id, satellite_name, constellation, line1, line2, epoch, orbital_period)
-- VALUES 
-- ('starlink-1', 44713, 'STARLINK-1', 'starlink', 
--  '1 44713U 19074A   24001.00000000  .00000000  00000-0  00000-0 0  9990',
--  '2 44713  53.0000   0.0000 0000000   0.0000   0.0000 15.50000000000000',
--  '2024-01-01 00:00:00+00', 93.0);
