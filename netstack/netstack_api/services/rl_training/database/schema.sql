-- 🧠 LEO衛星換手決策RL系統 PostgreSQL 資料庫架構
-- 基於學術研究需求的進階資料庫設計

-- 實驗會話主表（支援論文實驗管理）
CREATE TABLE rl_experiment_sessions (
    id BIGSERIAL PRIMARY KEY,
    experiment_name VARCHAR(100) NOT NULL,
    algorithm_type VARCHAR(20) NOT NULL,
    scenario_type VARCHAR(50), -- urban, suburban, low_latency
    paper_reference VARCHAR(200), -- 關聯的baseline論文
    researcher_id VARCHAR(50),
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    total_episodes INTEGER DEFAULT 0,
    session_status VARCHAR(20) DEFAULT 'running',
    config_hash VARCHAR(64),
    hyperparameters JSONB, -- 完整的超參數記錄
    environment_config JSONB, -- 環境配置（可重現性）
    research_notes TEXT, -- 研究筆記
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 建立索引以支援高效查詢
CREATE INDEX idx_algorithm_scenario ON rl_experiment_sessions (algorithm_type, scenario_type);
CREATE INDEX idx_paper_reference ON rl_experiment_sessions (paper_reference);
CREATE INDEX idx_researcher ON rl_experiment_sessions (researcher_id);
CREATE INDEX idx_session_status ON rl_experiment_sessions (session_status);

-- 詳細訓練回合數據（支援深度分析）
CREATE TABLE rl_training_episodes (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT REFERENCES rl_experiment_sessions(id) ON DELETE CASCADE,
    episode_number INTEGER NOT NULL,
    total_reward FLOAT,
    success_rate FLOAT,
    handover_latency_ms FLOAT,
    throughput_mbps FLOAT,
    packet_loss_rate FLOAT,
    convergence_indicator FLOAT, -- 收斂性指標
    exploration_rate FLOAT, -- 探索率
    episode_metadata JSONB, -- 詳細狀態-動作記錄
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(session_id, episode_number)
);

-- 建立索引以支援性能分析
CREATE INDEX idx_episode_performance ON rl_training_episodes (total_reward, success_rate);
CREATE INDEX idx_convergence ON rl_training_episodes (convergence_indicator);
CREATE INDEX idx_episode_timestamp ON rl_training_episodes (created_at);

-- Baseline比較數據表
CREATE TABLE rl_baseline_comparisons (
    id BIGSERIAL PRIMARY KEY,
    experiment_session_id BIGINT REFERENCES rl_experiment_sessions(id),
    baseline_paper_title VARCHAR(200),
    baseline_algorithm VARCHAR(50),
    comparison_metric VARCHAR(50), -- success_rate, latency, throughput
    our_result FLOAT,
    baseline_result FLOAT,
    improvement_percentage FLOAT,
    statistical_significance FLOAT, -- p-value
    test_conditions JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_baseline_comparison ON rl_baseline_comparisons (baseline_algorithm, comparison_metric);

-- 算法性能時間序列（支援趨勢分析）
CREATE TABLE rl_performance_timeseries (
    id BIGSERIAL PRIMARY KEY,
    algorithm_type VARCHAR(20),
    measurement_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success_rate FLOAT,
    average_reward FLOAT,
    response_time_ms FLOAT,
    stability_score FLOAT,
    training_progress_percent FLOAT,
    resource_utilization JSONB, -- CPU, Memory, GPU使用率
    network_metrics JSONB -- 網路相關指標
);

CREATE INDEX idx_timeseries ON rl_performance_timeseries (algorithm_type, measurement_timestamp);
CREATE INDEX idx_performance_trend ON rl_performance_timeseries (success_rate, average_reward);

-- 研究級模型版本管理
CREATE TABLE rl_model_versions (
    id BIGSERIAL PRIMARY KEY,
    algorithm_type VARCHAR(20),
    version_number VARCHAR(20),
    model_file_path VARCHAR(500),
    training_session_id BIGINT REFERENCES rl_experiment_sessions(id),
    validation_score FLOAT,
    test_score FLOAT, -- 獨立測試集分數
    deployment_status VARCHAR(20) DEFAULT 'created',
    paper_published BOOLEAN DEFAULT FALSE,
    benchmark_results JSONB, -- 標準benchmark結果
    model_size_mb FLOAT,
    inference_time_ms FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_model_version ON rl_model_versions (algorithm_type, version_number);
CREATE INDEX idx_model_performance ON rl_model_versions (validation_score, test_score);

-- 論文數據匯出記錄
CREATE TABLE rl_paper_exports (
    id BIGSERIAL PRIMARY KEY,
    export_name VARCHAR(100),
    experiment_session_ids INTEGER[],
    export_type VARCHAR(50), -- figures, tables, raw_data
    export_format VARCHAR(20), -- csv, json, latex
    file_path VARCHAR(500),
    export_config JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_export_type ON rl_paper_exports (export_type, created_at);

-- 研究分析視圖
CREATE VIEW algorithm_comparison_analysis AS
SELECT 
    algorithm_type,
    scenario_type,
    COUNT(*) as experiment_count,
    AVG(total_episodes) as avg_episodes,
    AVG((SELECT AVG(total_reward) FROM rl_training_episodes e WHERE e.session_id = s.id)) as avg_reward,
    AVG((SELECT AVG(success_rate) FROM rl_training_episodes e WHERE e.session_id = s.id)) as avg_success_rate,
    AVG((SELECT AVG(handover_latency_ms) FROM rl_training_episodes e WHERE e.session_id = s.id)) as avg_latency,
    STDDEV((SELECT AVG(total_reward) FROM rl_training_episodes e WHERE e.session_id = s.id)) as reward_std
FROM rl_experiment_sessions s
WHERE session_status = 'completed'
GROUP BY algorithm_type, scenario_type;

-- 收斂性分析視圖
CREATE VIEW convergence_analysis AS
SELECT 
    s.algorithm_type,
    s.scenario_type,
    e.session_id,
    MIN(episode_number) as convergence_episode,
    AVG(total_reward) as converged_reward,
    COUNT(*) as stable_episodes
FROM rl_experiment_sessions s
JOIN rl_training_episodes e ON s.id = e.session_id
WHERE e.convergence_indicator > 0.95
GROUP BY s.algorithm_type, s.scenario_type, e.session_id;

-- 插入一些示例數據用於測試
INSERT INTO rl_experiment_sessions (
    experiment_name, algorithm_type, scenario_type, 
    paper_reference, researcher_id, total_episodes, hyperparameters
) VALUES 
(
    'LEO Handover Optimization - DQN Baseline', 
    'DQN', 
    'urban', 
    'IEEE ComMag 2024', 
    'researcher_001', 
    1000,
    '{"learning_rate": 0.001, "batch_size": 32, "epsilon": 0.1}'::jsonb
),
(
    'LEO Handover Optimization - PPO Advanced', 
    'PPO', 
    'suburban', 
    'IEEE TCOM 2024', 
    'researcher_001', 
    1500,
    '{"learning_rate": 0.0003, "batch_size": 64, "gamma": 0.99}'::jsonb
),
(
    'LEO Handover Optimization - SAC Continuous', 
    'SAC', 
    'low_latency', 
    'IEEE JSAC 2024', 
    'researcher_002', 
    2000,
    '{"learning_rate": 0.0001, "batch_size": 128, "tau": 0.005}'::jsonb
);

COMMENT ON TABLE rl_experiment_sessions IS '實驗會話主表，支援論文級別的實驗管理和追蹤';
COMMENT ON TABLE rl_training_episodes IS '詳細的訓練回合數據，支援深度性能分析';
COMMENT ON TABLE rl_baseline_comparisons IS 'Baseline算法比較數據，支援論文寫作';
COMMENT ON TABLE rl_performance_timeseries IS '性能時間序列數據，支援趨勢分析';
COMMENT ON TABLE rl_model_versions IS '模型版本管理，支援實驗可重現性';
COMMENT ON TABLE rl_paper_exports IS '論文數據匯出記錄，支援學術發表';