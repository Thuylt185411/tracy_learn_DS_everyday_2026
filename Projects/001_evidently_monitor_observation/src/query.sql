-- Create monitoring schema
CREATE SCHEMA IF NOT EXISTS monitoring;

-- Main metrics log table
CREATE TABLE monitoring.metrics_log (
    id SERIAL PRIMARY KEY,
    snapshot_date DATE NOT NULL,
    snapshot_hour INT,
    data_reference_id VARCHAR(100),
    data_current_id VARCHAR(100),
    metric_category VARCHAR(50),  -- 'drift' | 'performance' | 'quality'
    metric_name VARCHAR(100),
    metric_value FLOAT,
    threshold FLOAT,
    status VARCHAR(20),  -- 'PASS' | 'WARN' | 'FAIL'
    reference_period_value FLOAT,
    change_pct FLOAT,
    execution_time_sec FLOAT,
    execution_memory_mb FLOAT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(snapshot_date, metric_name, data_current_id)
);

-- Feature-level metrics
CREATE TABLE monitoring.feature_metrics (
    id SERIAL PRIMARY KEY,
    snapshot_date DATE NOT NULL,
    data_reference_id VARCHAR(100),
    data_current_id VARCHAR(100),
    feature_name VARCHAR(100),
    feature_type VARCHAR(20),  -- 'numerical' | 'categorical' | 'text'
    psi FLOAT,
    iv_reference FLOAT,
    iv_current FLOAT,
    woe_monotonic BOOLEAN,
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Insert monitoring results
INSERT INTO monitoring.metrics_log (
    snapshot_date, data_reference_id, data_current_id,
    metric_category, metric_name, metric_value, threshold, status,
    reference_period_value, change_pct, execution_time_sec
) VALUES (
    '2025-01-05', 'ASSET_NM_20241201', 'ASSET_NM_20250101',
    'drift', 'PSI_Score', 0.18, 0.25, 'PASS',
    0.08, 125.0, 2.34
);

-- Query historical trends
SELECT 
    snapshot_date,
    metric_name,
    metric_value,
    AVG(metric_value) OVER (
        PARTITION BY metric_name 
        ORDER BY snapshot_date 
        ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
    ) AS moving_avg_12m
FROM monitoring.metrics_log
WHERE metric_name = 'AUC_ROC'
ORDER BY snapshot_date DESC;


