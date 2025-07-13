-- PostgreSQL Initialization Script for RL System
--
-- This script is automatically executed by the official PostgreSQL Docker image
-- when the container starts for the first time. It ensures that the database,
-- user, and tables are created before the FastAPI application attempts to connect.
--
-- For more details on the initialization mechanism, see:
-- https://hub.docker.com/_/postgres (section "Initialization scripts")

-- The 'docker-entrypoint.sh' script in the PostgreSQL image will connect to the
-- database specified by POSTGRES_DB (here: 'rl_db') as the POSTGRES_USER
-- (here: 'rl_user'). Therefore, we don't need to create the database or user here,
-- as Docker Compose's environment variables handle that. We only need to create
-- the schema (tables, indexes, etc.) within the automatically created database.

-- Create the extension required for UUIDs if not already present.
-- This might be useful for future development.
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Study and experiment session table (supports todo.md experiment tracking)
CREATE TABLE IF NOT EXISTS rl_experiment_sessions (
    id BIGSERIAL PRIMARY KEY,
    experiment_name VARCHAR(100) NOT NULL,
    algorithm_type VARCHAR(20) NOT NULL,
    scenario_type VARCHAR(50), -- e.g., urban, suburban, low_latency
    start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP WITH TIME ZONE,
    total_episodes INTEGER DEFAULT 0,
    session_status VARCHAR(20) DEFAULT 'running', -- Changed from "running" to 'running' for SQL standard
    hyperparameters JSONB, -- Complete hyperparameter record
    research_notes TEXT, -- Supports academic research notes
    git_commit_hash VARCHAR(40), -- Track code version for reproducibility
    system_version VARCHAR(20) -- Track system version
);
CREATE INDEX IF NOT EXISTS idx_algorithm_scenario ON rl_experiment_sessions(algorithm_type, scenario_type);
CREATE INDEX IF NOT EXISTS idx_session_status ON rl_experiment_sessions(session_status);


-- Detailed training episode data (supports decision transparency)
CREATE TABLE IF NOT EXISTS rl_training_episodes (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT REFERENCES rl_experiment_sessions(id) ON DELETE CASCADE,
    episode_number INTEGER NOT NULL,
    total_reward FLOAT,
    steps_in_episode INTEGER,
    episode_duration_sec FLOAT,
    success_rate FLOAT, -- This might be better aggregated at the session level
    handover_latency_ms FLOAT, -- Supports todo.md performance analysis
    decision_confidence FLOAT, -- Supports Algorithm Explainability
    final_state_value FLOAT, -- Value function estimate for the final state
    additional_metrics JSONB, -- Flexible field for other metrics
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_episode_session_id ON rl_training_episodes(session_id);


-- Decision analysis data (supports todo.md visualization)
CREATE TABLE IF NOT EXISTS rl_decision_analysis (
    id BIGSERIAL PRIMARY KEY,
    episode_id BIGINT REFERENCES rl_training_episodes(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    state_representation JSONB, -- The state observation given to the agent
    candidate_satellites JSONB, -- All candidate satellite information
    scoring_details JSONB, -- Scoring details for each candidate
    action_taken JSONB, -- The action selected by the agent (can be complex)
    selected_satellite_id VARCHAR(50),
    decision_factors JSONB, -- Decision factor weights
    confidence_level FLOAT,
    reasoning_path JSONB, -- Algorithm Explainability data
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_analysis_episode_id ON rl_decision_analysis(episode_id);

-- Add comments to tables and columns for better documentation in the database.
COMMENT ON TABLE rl_experiment_sessions IS 'Stores high-level information about each research experiment session.';
COMMENT ON COLUMN rl_experiment_sessions.hyperparameters IS 'Stores all hyperparameters for the session, e.g., learning rate, discount factor.';
COMMENT ON TABLE rl_training_episodes IS 'Stores detailed metrics for each episode within an experiment session.';
COMMENT ON COLUMN rl_training_episodes.decision_confidence IS 'A metric representing the agent''s confidence in its decision for this episode.';
COMMENT ON TABLE rl_decision_analysis IS 'Stores fine-grained data for each decision point for explainability and visualization.';
COMMENT ON COLUMN rl_decision_analysis.reasoning_path IS 'Data supporting algorithmic explainability, such as attention weights or feature importance.'; 