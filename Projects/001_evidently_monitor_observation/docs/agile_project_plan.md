# AGILE PROJECT PLAN: Customer Churn Prediction Monitoring System
## Sprint-Based Breakdown with Detailed Tasks & Outputs

---

## PROJECT OVERVIEW

**Objective:** Build production-ready ML monitoring system for churn prediction model

**Duration:** 12 Weeks (3 Sprints × 4 weeks)

**Team:** 1 ML Engineer + 1 Data Engineer + 1 DevOps Engineer (part-time)

**Primary Tool:** Evidently AI (with optional Arize integration in Phase 3)

**Key Success Criteria:**
- ✅ Daily automated monitoring reports
- ✅ Drift detection alerts within 1 hour of anomaly
- ✅ Root cause analysis dashboard
- ✅ Performance tracking by customer segment
- ✅ Zero manual intervention required for monitoring

---

## PHASE 1: EXPLORATION & SETUP (Weeks 1-4)
### Sprint 1: Library Evaluation & Environment Setup

---

### WEEK 1: Library Research & Comparison

#### **Task 1.1.1: Evidently AI Deep Dive**
**Duration:** 2 days | **Owner:** ML Engineer

**Activities:**
- [ ] Install Evidently (latest version)
- [ ] Read official documentation (2 hours)
- [ ] Run basic tutorial with sample data (2 hours)
- [ ] Test data drift detection (PSI calculation)
- [ ] Test classification metrics calculation
- [ ] Evaluate HTML report generation
- [ ] Check JSON output structure
- [ ] Test custom metric implementation

**Output:**
```
📄 research_output/evidently_evaluation.md
├── Installation steps
├── API exploration notes
├── Metric capabilities tested
├── Code snippets for common tasks
├── Pros/cons assessment
└── Limitation findings

📊 research_output/evidently_test_report.html
└── Sample monitoring report from test data
```

**Deliverable Quality:** PASS/FAIL decision on Evidently for project

---

#### **Task 1.1.2: Arize AI Research (Optional Path)**
**Duration:** 1 day | **Owner:** ML Engineer | **Optional**

**Activities:**
- [ ] Review Arize documentation
- [ ] Compare features vs Evidently
- [ ] Check pricing (if applicable)
- [ ] Test free tier demo
- [ ] Evaluate integration complexity

**Output:**
```
📄 research_output/arize_evaluation.md
└── Feature comparison matrix vs Evidently
```

**Decision Point:** Proceed with Evidently only? OR Plan Arize integration later?

---

#### **Task 1.1.3: Create Metrics Specification Document**
**Duration:** 1 day | **Owner:** ML Engineer + Product

**Activities:**
- [ ] Define 10 key monitoring metrics
- [ ] Set thresholds for each metric
- [ ] Define alert severity levels
- [ ] Document business rationale for each metric
- [ ] Identify data dependencies

**Output:**
```
📄 documentation/METRICS_SPECIFICATION.md

## Monitoring Metrics for Churn Prediction

### 1. Recall (Performance - CRITICAL)
- Definition: TP / (TP + FN)
- Baseline: 82% (from validation set)
- Warning Threshold: 75% (↓7%)
- Alert Threshold: 70% (↓12%)
- Frequency: Daily
- Rationale: Catching actual churners is business-critical

### 2. PSI - account_age (Data Drift)
- Definition: Population Stability Index
- Baseline: 0.08 (from training period)
- Warning Threshold: 0.15
- Alert Threshold: 0.25
- Frequency: Daily
- Rationale: Sudden shifts indicate customer demographic change

### 3. Default Rate (Concept Drift)
- Definition: Actual churn rate in cohort
- Baseline: 26.5% (from validation)
- Warning Threshold: ±5%
- Alert Threshold: ±10%
- Frequency: Daily (after sufficient labels available)
- Rationale: Business environment changes

... (7 more metrics with same detail level)

## Alert Configuration
- HIGH: Recall < 70% OR PSI_Score > 0.25 OR Default Rate change > 10%
- MEDIUM: Recall < 75% OR PSI_Score > 0.15 OR Default Rate change > 5%
- LOW: Recall < 80% OR Any feature PSI > 0.1
```

---

#### **Task 1.1.4: Data Requirements Assessment**
**Duration:** 1 day | **Owner:** Data Engineer

**Activities:**
- [ ] List all required input columns
- [ ] Define data types and ranges
- [ ] Check data availability in source systems
- [ ] Identify label availability lag
- [ ] Map data lineage
- [ ] Create data dictionary

**Output:**
```
📄 documentation/DATA_REQUIREMENTS.md

## Input Data Schema

### Features (Must match training data exactly)
- customer_id: VARCHAR, PK, unique identifier
- account_age: INT, range [1, 120] (months)
- monthly_charges: DECIMAL(7,2), range [18.00, 250.00]
- contract_type: VARCHAR, values: ['Month-to-month', 'One year', 'Two year']
- ... (25 features total)

### Predictions
- prediction_timestamp: TIMESTAMP
- churn_class: INT (0=retain, 1=churn)
- churn_probability: DECIMAL(5,4), range [0, 1]

### Ground Truth (Labels)
- churn_actual: INT (0=stayed, 1=churned)
- label_effective_date: DATE
- Label Lag: 60 days (determined at end of billing cycle)

## Data Quality Checks
- No nulls in: customer_id, prediction_timestamp, churn_class, churn_probability
- Max nulls in features: 2% per column
- No duplicate customer_ids per day
```

---

### WEEK 2: Environment Setup & Integration Planning

#### **Task 1.2.1: Development Environment Setup**
**Duration:** 1.5 days | **Owner:** DevOps Engineer

**Activities:**
- [ ] Create Python virtual environment
- [ ] Install dependencies (Evidently, pandas, numpy, scikit-learn, etc.)
- [ ] Setup version control repository
- [ ] Configure pre-commit hooks
- [ ] Setup CI/CD pipeline (GitHub Actions / GitLab CI)
- [ ] Create project directory structure

**Output:**
```
📁 project_directory/
├── requirements.txt (with all dependencies pinned)
├── .github/workflows/
│   ├── tests.yml
│   └── monitoring.yml
├── src/
│   ├── monitoring/
│   ├── metrics/
│   └── utils/
├── tests/
├── data/
│   ├── reference/
│   └── current/
├── reports/
├── config/
│   └── monitoring_config.yaml
└── README.md (setup instructions)

✅ All libraries installed and tested
✅ CI/CD pipeline functional
✅ Pre-commit checks passing
```

---

#### **Task 1.2.2: Data Pipeline Assessment**
**Duration:** 1.5 days | **Owner:** Data Engineer

**Activities:**
- [ ] Map data flow from prediction system to monitoring
- [ ] Identify data storage (DB, data warehouse, API)
- [ ] Plan data extraction queries/APIs
- [ ] Design buffering/batching strategy
- [ ] Plan label matching logic (by customer_id + date)
- [ ] Document SLAs (update frequency, latency tolerance)

**Output:**
```
📄 documentation/DATA_PIPELINE_DESIGN.md

## Data Flow Architecture

┌─────────────────────┐
│ Production ML Model │
└──────────┬──────────┘
           │ (predictions daily at 2AM UTC)
           ↓
┌─────────────────────────────────────────┐
│ Predictions Table (Data Warehouse)      │
│ - prediction_timestamp                  │
│ - prediction_id                         │
│ - customer_id                           │
│ - churn_probability, churn_class        │
│ - all 25 input features                 │
└──────────┬──────────────────────────────┘
           │ (extract daily at 3AM UTC)
           ↓
┌─────────────────────────────────────────┐
│ Monitoring System (Evidently)           │
│ - Load current day predictions          │
│ - Compare with reference baseline       │
│ - Calculate metrics                     │
└──────────┬──────────────────────────────┘
           │ (outputs at 4AM UTC)
           ↓
┌─────────────────────────────────────────┐
│ Results Storage                         │
│ - JSON snapshots (S3/GCS)               │
│ - Metrics table (PostgreSQL)            │
│ - HTML reports (S3)                     │
└─────────────────────────────────────────┘
           │
           ↓
┌─────────────────────────────────────────┐
│ Visualization & Alerting                │
│ - Slack notifications                   │
│ - Email summaries                       │
│ - Dashboard links                       │
└─────────────────────────────────────────┘

## SLAs
- Monitoring latency: <1 hour from prediction generation
- Alert delivery: <5 minutes of threshold breach
- Report availability: by 5AM UTC daily
```

---

#### **Task 1.2.3: Reference Data Preparation**
**Duration:** 1 day | **Owner:** Data Engineer

**Activities:**
- [ ] Extract historical data for reference period (validation set)
- [ ] Verify data quality and completeness
- [ ] Document data filters applied
- [ ] Save reference data snapshot
- [ ] Create reference data documentation

**Output:**
```
📁 data/reference/
├── reference_data_2024_11_01_to_2024_12_31.csv
│   └── (10,000 rows × 27 columns)
└── REFERENCE_DATA_INFO.json
    {
      "period": "2024-11-01 to 2024-12-31",
      "row_count": 10000,
      "feature_count": 25,
      "target_count": 10000,
      "churn_rate": 0.265,
      "null_statistics": {...},
      "performance_baseline": {
        "accuracy": 0.859,
        "precision": 0.765,
        "recall": 0.821,
        "auc_roc": 0.924
      },
      "created_timestamp": "2025-01-05T10:30:00Z"
    }
```

---

### WEEK 3: Core Implementation - Phase 1

#### **Task 1.3.1: Build Basic Monitoring Pipeline (Evidently)**
**Duration:** 2 days | **Owner:** ML Engineer

**Activities:**
- [ ] Create data loading module
- [ ] Implement drift detection reports (PSI, KS, Chi-squared)
- [ ] Implement performance metrics calculation
- [ ] Implement data quality checks
- [ ] Generate HTML reports
- [ ] Save JSON snapshots

**Output:**
```python
# src/monitoring/pipeline.py (MAIN MONITORING EXECUTABLE)

from evidently.report import Report
from evidently.metric_preset import (
    DataDriftPreset,
    DataQualityPreset,
    ClassificationPreset
)

class ChurnMonitoringPipeline:
    def __init__(self, reference_data_path, config_path):
        self.reference_data = pd.read_csv(reference_data_path)
        self.config = load_yaml(config_path)
    
    def run(self, current_data_path):
        # Load current data
        current_data = pd.read_csv(current_data_path)
        
        # Generate reports
        drift_report = Report(metrics=[DataDriftPreset()])
        drift_report.run(
            reference_data=self.reference_data,
            current_data=current_data,
            column_mapping=self.config['column_mapping']
        )
        
        performance_report = Report(metrics=[ClassificationPreset()])
        performance_report.run(
            reference_data=self.reference_data,
            current_data=current_data,
            column_mapping=self.config['column_mapping']
        )
        
        # Save outputs
        drift_report.save_html(f"reports/drift_{datetime.now().date()}.html")
        drift_report.save_json(f"snapshots/drift_{datetime.now().date()}.json")
        
        return {
            'drift_report': drift_report,
            'performance_report': performance_report
        }

# Usage
if __name__ == "__main__":
    pipeline = ChurnMonitoringPipeline(
        'data/reference/reference_data.csv',
        'config/monitoring_config.yaml'
    )
    results = pipeline.run('data/current/predictions_2025_01_05.csv')
```

**Output Files:**
```
📁 reports/
├── drift_2025_01_05.html
├── performance_2025_01_05.html
└── data_quality_2025_01_05.html

📁 snapshots/
├── drift_2025_01_05.json
├── performance_2025_01_05.json
└── data_quality_2025_01_05.json
```

---

#### **Task 1.3.2: Metrics Extraction & Storage**
**Duration:** 1 day | **Owner:** ML Engineer

**Activities:**
- [ ] Create metrics extraction from Evidently reports
- [ ] Implement metrics table schema (PostgreSQL)
- [ ] Create database insert logic
- [ ] Implement CSV export functionality
- [ ] Add data validation checks

**Output:**
```python
# src/monitoring/metrics_extractor.py

class MetricsExtractor:
    def extract_from_reports(self, drift_report, perf_report, quality_report):
        """Extract key metrics and normalize to table format"""
        
        metrics = []
        
        # Drift metrics
        for col_name, col_metrics in drift_report['metrics'][0]['result']['metrics'].items():
            metrics.append({
                'snapshot_date': datetime.now().date(),
                'metric_category': 'drift',
                'metric_name': f'PSI_{col_name}',
                'metric_value': col_metrics['statistic'],
                'threshold': self.config['thresholds']['psi'],
                'status': 'PASS' if col_metrics['statistic'] < 0.25 else 'FAIL'
            })
        
        # Performance metrics
        perf_results = perf_report['metrics'][0]['result']
        metrics.append({
            'snapshot_date': datetime.now().date(),
            'metric_category': 'performance',
            'metric_name': 'Recall',
            'metric_value': perf_results['current']['recall'],
            'threshold': 0.80,
            'status': 'PASS' if perf_results['current']['recall'] >= 0.80 else 'FAIL'
        })
        # ... more performance metrics
        
        return pd.DataFrame(metrics)
    
    def save_to_database(self, metrics_df):
        """Insert metrics into PostgreSQL"""
        with psycopg2.connect(self.db_config) as conn:
            for _, row in metrics_df.iterrows():
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO monitoring.metrics_log 
                    (snapshot_date, metric_category, metric_name, 
                     metric_value, threshold, status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, tuple(row))
            conn.commit()
    
    def save_to_csv(self, metrics_df, filepath):
        """Export to CSV for BI tools"""
        metrics_df.to_csv(filepath, index=False)
        return filepath

# Output files
📁 data/metrics/
├── metrics_log_2025_01_05.csv (appended daily)
└── metrics_summary_2025_01_05.csv (summary version)

# Database table
monitoring.metrics_log
├── snapshot_date: DATE
├── metric_category: VARCHAR
├── metric_name: VARCHAR
├── metric_value: DECIMAL
├── threshold: DECIMAL
├── status: VARCHAR
└── created_at: TIMESTAMP
```

---

#### **Task 1.3.3: Alert Configuration & Testing**
**Duration:** 1 day | **Owner:** ML Engineer + DevOps

**Activities:**
- [ ] Define alert rules from thresholds
- [ ] Implement alert generation logic
- [ ] Setup Slack webhook integration
- [ ] Test alert delivery
- [ ] Create alert logging

**Output:**
```python
# src/alerts/alert_manager.py

class AlertManager:
    ALERT_RULES = {
        'high_severity': [
            {'metric': 'Recall', 'condition': '<', 'threshold': 0.70},
            {'metric': 'PSI_monthly_charges', 'condition': '>', 'threshold': 0.25},
        ],
        'medium_severity': [
            {'metric': 'Recall', 'condition': '<', 'threshold': 0.75},
            {'metric': 'PSI_account_age', 'condition': '>', 'threshold': 0.15},
        ],
        'low_severity': [
            {'metric': 'Recall', 'condition': '<', 'threshold': 0.80},
        ]
    }
    
    def generate_alerts(self, metrics_df):
        """Check metrics against rules, return triggered alerts"""
        alerts = []
        
        for severity, rules in self.ALERT_RULES.items():
            for rule in rules:
                metric_val = metrics_df[metrics_df['metric_name'] == rule['metric']]['metric_value'].iloc[0]
                threshold = rule['threshold']
                
                if rule['condition'] == '<' and metric_val < threshold:
                    alerts.append({
                        'severity': severity,
                        'metric': rule['metric'],
                        'current_value': metric_val,
                        'threshold': threshold,
                        'timestamp': datetime.now(),
                        'message': f"{rule['metric']} is {metric_val}, below threshold {threshold}"
                    })
        
        return alerts
    
    def send_slack_alert(self, alert):
        """Send alert to Slack"""
        webhook_url = self.config['slack_webhook']
        color_map = {'high_severity': 'danger', 'medium_severity': 'warning', 'low_severity': '#36a64f'}
        
        slack_message = {
            "attachments": [{
                "color": color_map[alert['severity']],
                "title": f"🚨 {alert['severity'].upper()}: {alert['metric']}",
                "text": alert['message'],
                "fields": [
                    {"title": "Current Value", "value": str(alert['current_value']), "short": True},
                    {"title": "Threshold", "value": str(alert['threshold']), "short": True}
                ],
                "ts": int(alert['timestamp'].timestamp())
            }]
        }
        
        requests.post(webhook_url, json=slack_message)

# Output files
📁 logs/
├── alerts_log_2025_01_05.csv
│   └── timestamp | severity | metric | value | threshold | action_taken
└── alert_summary_2025_01_05.json
```

---

### WEEK 4: Testing & Documentation

#### **Task 1.4.1: Unit Tests & Integration Tests**
**Duration:** 1 day | **Owner:** ML Engineer

**Activities:**
- [ ] Write unit tests for metrics extraction
- [ ] Write integration tests for full pipeline
- [ ] Test with sample data
- [ ] Achieve 80%+ code coverage
- [ ] Test error handling

**Output:**
```python
# tests/test_monitoring_pipeline.py

import pytest
import pandas as pd

class TestChurnMonitoringPipeline:
    
    @pytest.fixture
    def sample_reference_data(self):
        return pd.read_csv('data/reference/reference_data.csv')
    
    @pytest.fixture
    def sample_current_data(self):
        return pd.read_csv('data/test/test_current_data.csv')
    
    def test_pipeline_runs_successfully(self, sample_reference_data, sample_current_data):
        pipeline = ChurnMonitoringPipeline('config/monitoring_config.yaml')
        results = pipeline.run(sample_reference_data, sample_current_data)
        
        assert 'drift_report' in results
        assert 'performance_report' in results
    
    def test_metrics_extraction(self, sample_reference_data):
        extractor = MetricsExtractor('config/monitoring_config.yaml')
        metrics_df = extractor.extract_metrics(sample_reference_data)
        
        assert len(metrics_df) > 0
        assert 'metric_name' in metrics_df.columns
        assert 'metric_value' in metrics_df.columns
    
    def test_alert_generation(self):
        metrics = pd.DataFrame({
            'metric_name': ['Recall', 'PSI_account_age'],
            'metric_value': [0.68, 0.30]  # Both will trigger alerts
        })
        
        alert_manager = AlertManager('config/monitoring_config.yaml')
        alerts = alert_manager.generate_alerts(metrics)
        
        assert len(alerts) == 2
        assert any(a['severity'] == 'high_severity' for a in alerts)

✅ All tests passing
✅ Coverage: 87%
```

---

#### **Task 1.4.2: Documentation & Handoff**
**Duration:** 1 day | **Owner:** ML Engineer + Data Engineer

**Activities:**
- [ ] Write system architecture document
- [ ] Create operational runbook
- [ ] Document all configuration options
- [ ] Create troubleshooting guide
- [ ] Record demo video

**Output:**
```
📄 documentation/SYSTEM_ARCHITECTURE.md
- High-level overview
- Data flow diagram
- Component descriptions
- Technology stack

📄 documentation/OPERATIONAL_RUNBOOK.md
- Daily operation steps
- Manual monitoring trigger
- Troubleshooting common issues
- Contact escalation

📄 documentation/CONFIGURATION_GUIDE.md
- All config parameters
- Examples
- How to adjust thresholds

📄 documentation/TROUBLESHOOTING_GUIDE.md
- Common errors
- Root cause analysis
- Resolution steps

📹 demo_video_phase1.mp4 (10 minutes)
- System walkthrough
- Running monitoring
- Interpreting reports
```

---

## SUMMARY: PHASE 1 OUTPUTS

**Total Effort:** 4 weeks | **Completeness:** 100%

### Key Deliverables:
✅ Monitoring pipeline (fully functional)
✅ Data loading & preprocessing
✅ Metrics calculation (drift, performance, data quality)
✅ Alert system (Slack integration)
✅ HTML reports + JSON snapshots
✅ Metrics database schema
✅ Unit & integration tests
✅ Complete documentation

### Key Files Created:
- `src/monitoring/pipeline.py` (Main executable)
- `src/monitoring/metrics_extractor.py` (Metrics storage)
- `src/alerts/alert_manager.py` (Alerting system)
- `config/monitoring_config.yaml` (All configuration)
- `data/reference/` (Baseline data)
- `reports/`, `snapshots/`, `logs/` (Output directories)

### Success Criteria Met:
✅ Evidently library fully evaluated & integrated
✅ Daily monitoring reports generated
✅ Metrics extracted to database
✅ Alerts functional (Slack delivery)
✅ Code tested & documented

### Handoff to Phase 2:
- All code versioned in Git
- CI/CD pipeline ready
- Documentation complete
- Ready for pilot testing on production data

---

## PHASE 2: PILOT & OPTIMIZATION (Weeks 5-8)
### Sprint 2: Production Pilot & Performance Tuning

---

### WEEK 5: Production Data Integration & Pilot

#### **Task 2.1.1: Production Data Connection Setup**
**Duration:** 2 days | **Owner:** Data Engineer + DevOps

**Activities:**
- [ ] Connect to production data warehouse
- [ ] Implement credentials management (AWS Secrets, Azure Key Vault)
- [ ] Create data extraction queries/APIs
- [ ] Implement error handling & retries
- [ ] Test data freshness & completeness

**Output:**
```python
# src/data/production_loader.py

class ProductionDataLoader:
    def __init__(self, db_config):
        self.db_config = db_config
        self.connection_pool = self._init_connection_pool()
    
    def fetch_current_predictions(self, date, batch_size=10000):
        """Extract predictions from DW for monitoring date"""
        query = """
            SELECT 
                customer_id,
                prediction_timestamp,
                churn_probability,
                churn_class,
                account_age,
                monthly_charges,
                contract_type,
                ... (25 features)
            FROM feature_store.churn_predictions
            WHERE DATE(prediction_timestamp) = %s
                AND is_valid = TRUE
        """
        
        with self.connection_pool.getconn() as conn:
            df = pd.read_sql(query, conn, params=[date])
        
        # Validation
        assert len(df) > 0, "No predictions found for date"
        assert not df.isnull().any().any(), "Null values detected"
        
        return df
    
    def fetch_labels(self, date, lookback_days=60):
        """Fetch actual churn labels (with lag)"""
        label_date = date - timedelta(days=lookback_days)
        
        query = """
            SELECT 
                customer_id,
                churn_actual,
                label_effective_date
            FROM fact_customer_churn
            WHERE DATE(label_effective_date) = %s
        """
        
        with self.connection_pool.getconn() as conn:
            df = pd.read_sql(query, conn, params=[label_date])
        
        return df

# Usage
loader = ProductionDataLoader(db_config)
predictions_df = loader.fetch_current_predictions('2025-01-05')
labels_df = loader.fetch_labels('2025-01-05')

✅ Connected to production DW
✅ Data extraction working
✅ Latency: <2 minutes for 100K records
```

---

#### **Task 2.1.2: Pilot Run #1 - Historical Data**
**Duration:** 1 day | **Owner:** ML Engineer

**Activities:**
- [ ] Run monitoring on last 7 days of production data
- [ ] Verify metrics calculation correctness
- [ ] Check report generation
- [ ] Validate alert triggering
- [ ] Compare metrics with manual validation

**Output:**
```
📊 pilot_results/week1_summary.md

## Pilot Run #1 Results (Historical 7-day Backtest)

### Data Summary
- Period: 2024-12-29 to 2025-01-05
- Total records: 700,000
- Missing predictions: 245 (0.035%) ← Expected, handled
- Churn rate: 26.2% ± 0.8%

### Metrics Stability
| Metric | Min | Max | Std Dev | Status |
|--------|-----|-----|---------|--------|
| Recall | 0.78 | 0.84 | 0.02 | ✅ STABLE |
| Precision | 0.72 | 0.79 | 0.02 | ✅ STABLE |
| PSI_account_age | 0.03 | 0.12 | 0.03 | ✅ NO DRIFT |
| PSI_monthly_charges | 0.04 | 0.08 | 0.02 | ✅ NO DRIFT |

### Alerts Generated
- HIGH alerts: 0 (good, no false alarms)
- MEDIUM alerts: 1 on 2025-01-03 (PSI_contract_type = 0.18, transient)
- LOW alerts: 3 (expected baseline noise)

### Key Finding
- All metrics within expected ranges
- No concerning drift patterns detected
- Alert thresholds appear well-calibrated

### Recommendation
✅ PROCEED TO LIVE PILOT
```

---

#### **Task 2.1.3: Setup Automated Daily Execution**
**Duration:** 1 day | **Owner:** DevOps Engineer

**Activities:**
- [ ] Create daily scheduler (Airflow DAG, cron, or cloud scheduler)
- [ ] Setup log collection
- [ ] Configure error notifications
- [ ] Test dry run

**Output:**
```python
# dags/churn_monitoring_dag.py (Apache Airflow DAG)

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'ml_team',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'email': ['ml-alerts@company.com'],
    'email_on_failure': True,
}

dag = DAG(
    'churn_model_monitoring',
    default_args=default_args,
    schedule_interval='0 4 * * *',  # 4 AM UTC daily
    start_date=datetime(2025, 1, 5),
)

def fetch_data(execution_date):
    from src.data.production_loader import ProductionDataLoader
    loader = ProductionDataLoader()
    return loader.fetch_current_predictions(execution_date)

def run_monitoring(ti):
    from src.monitoring.pipeline import ChurnMonitoringPipeline
    
    predictions_df = ti.xcom_pull(task_ids='fetch_data')
    
    pipeline = ChurnMonitoringPipeline('config/monitoring_config.yaml')
    results = pipeline.run(predictions_df)
    
    return results

def generate_alerts(ti):
    from src.alerts.alert_manager import AlertManager
    
    reports = ti.xcom_pull(task_ids='run_monitoring')
    alert_manager = AlertManager()
    alerts = alert_manager.generate_alerts(reports)
    
    for alert in alerts:
        alert_manager.send_slack_alert(alert)
    
    return len(alerts)

task_fetch = PythonOperator(
    task_id='fetch_data',
    python_callable=fetch_data,
    op_kwargs={'execution_date': '{{ ds }}'},
    dag=dag,
)

task_monitor = PythonOperator(
    task_id='run_monitoring',
    python_callable=run_monitoring,
    dag=dag,
)

task_alert = PythonOperator(
    task_id='generate_alerts',
    python_callable=generate_alerts,
    dag=dag,
)

task_fetch >> task_monitor >> task_alert

✅ Airflow DAG deployed
✅ First successful run: 2025-01-06
✅ Execution time: 3.2 minutes
✅ All tasks passing
```

---

### WEEK 6: Performance Analysis & Root Cause

#### **Task 2.2.1: Build Root Cause Analysis Dashboard**
**Duration:** 2 days | **Owner:** ML Engineer

**Activities:**
- [ ] Implement feature drift correlation analysis
- [ ] Build segment performance analysis (by contract_type, etc.)
- [ ] Create drill-down capability (from metric → features → examples)
- [ ] Implement anomaly detection for unexpected patterns
- [ ] Add visualization for trend analysis

**Output:**
```python
# src/analysis/root_cause_analysis.py

class RootCauseAnalyzer:
    def correlate_drift_with_performance(self, current_data, reference_data, performance_drop):
        """
        When performance drops, identify which features drifted most
        Example: Recall dropped 5% → Which features changed?
        """
        
        # Calculate feature PSIs
        feature_psis = {}
        for col in self.numeric_features:
            psi = calculate_psi(reference_data[col], current_data[col])
            feature_psis[col] = psi
        
        # Rank by drift
        top_drifted = sorted(feature_psis.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Correlate with performance drop
        analysis = {
            'performance_drop': performance_drop,
            'top_drifted_features': top_drifted,
            'hypothesis': f"Feature '{top_drifted[0][0]}' drifted (PSI={top_drifted[0][1]:.3f}), "
                         f"likely cause of performance degradation",
        }
        
        return analysis
    
    def analyze_by_segment(self, current_data, predictions, actuals):
        """Performance analysis by customer segments"""
        
        segments = {
            'by_contract_type': current_data.groupby('contract_type'),
            'by_tenure_band': current_data.groupby(
                pd.cut(current_data['account_age'], bins=[0, 12, 24, 48, 120])
            ),
            'by_charge_band': current_data.groupby(
                pd.cut(current_data['monthly_charges'], bins=[0, 50, 100, 150, 300])
            ),
        }
        
        segment_metrics = {}
        for segment_name, group_data in segments['by_contract_type'].items():
            group_indices = group_data.index
            
            segment_metrics[segment_name] = {
                'recall': recall_score(actuals[group_indices], predictions[group_indices]),
                'precision': precision_score(actuals[group_indices], predictions[group_indices]),
                'count': len(group_indices),
                'churn_rate': actuals[group_indices].mean(),
            }
        
        return segment_metrics

# HTML Dashboard Output
📊 analysis/root_cause_dashboard_2025_01_05.html
├── Section 1: Performance Summary
│   └── Overall Recall: 81.5% (↓0.5% from previous day)
├── Section 2: Feature Drift Ranking
│   └── Top 3 Drifted Features:
│       1. monthly_charges (PSI=0.18)
│       2. account_age (PSI=0.12)
│       3. total_charges (PSI=0.10)
├── Section 3: Segment Performance
│   └── By Contract Type:
│       - Month-to-month: Recall=77%, Precision=71%
│       - Annual: Recall=86%, Precision=81%
│       - Two-year: Recall=89%, Precision=83%
│       → Insight: Month-to-month customers harder to predict?
└── Section 4: Recommendations
    └── Investigate increased churn in month-to-month segment
        Collect customer feedback, check for competitive actions
```

---

#### **Task 2.2.2: Feature Importance Monitoring (Manual)**
**Duration:** 1.5 days | **Owner:** ML Engineer

**Activities:**
- [ ] Implement WoE (Weight of Evidence) calculation
- [ ] Implement IV (Information Value) calculation
- [ ] Track WoE trends over time
- [ ] Monitor for WoE sign changes (indicates model relationship flip)
- [ ] Monitor IV decreases >15%

**Output:**
```python
# src/analysis/feature_importance.py

class FeatureImportanceMonitor:
    def calculate_woe_iv(self, data, target, feature):
        """Calculate WoE and IV for a feature"""
        
        # Bin continuous features
        if pd.api.types.is_numeric_dtype(data[feature]):
            bins = pd.qcut(data[feature], q=10, duplicates='drop')
        else:
            bins = data[feature]
        
        # Crosstab
        distribution = pd.crosstab(bins, data[target], margins=True)
        distribution.columns = ['good', 'bad', 'total']
        
        # Calculate percentages
        distribution['good_pct'] = distribution['good'] / distribution['good'].sum()
        distribution['bad_pct'] = distribution['bad'] / distribution['bad'].sum()
        
        # WoE and IV
        distribution['woe'] = np.log(distribution['good_pct'] / distribution['bad_pct'])
        distribution['iv_component'] = (distribution['good_pct'] - distribution['bad_pct']) * distribution['woe']
        
        iv = distribution['iv_component'].sum()
        
        return {
            'feature': feature,
            'iv': iv,
            'woe': distribution['woe'].values,
            'monotonic': self._check_monotonicity(distribution['woe'].values),
        }
    
    def monitor_feature_importance(self, current_data, reference_data, target):
        """Compare feature importance between periods"""
        
        importance_changes = {}
        
        for feature in self.important_features:  # Top 10 features from model
            current_iv = self.calculate_woe_iv(current_data, target, feature)['iv']
            reference_iv = self.calculate_woe_iv(reference_data, target, feature)['iv']
            
            change_pct = (current_iv - reference_iv) / reference_iv * 100
            
            importance_changes[feature] = {
                'reference_iv': reference_iv,
                'current_iv': current_iv,
                'change_pct': change_pct,
                'alert': 'YES' if abs(change_pct) > 15 else 'NO',
            }
        
        return pd.DataFrame(importance_changes).T

# Output: CSV Report
📄 analysis/feature_importance_2025_01_05.csv

| feature | reference_iv | current_iv | change_pct | alert |
|---------|--------------|-----------|-----------|-------|
| tenure_months | 0.486 | 0.472 | -2.88% | NO |
| monthly_charges | 0.412 | 0.398 | -3.40% | NO |
| contract_type | 0.356 | 0.345 | -3.09% | NO |
| internet_service | 0.234 | 0.198 | -15.38% | YES ← Investigate! |
| online_security | 0.212 | 0.201 | -5.19% | NO |
```

---

### WEEK 7: Visualization & Dashboarding

#### **Task 2.3.1: Build Interactive Dashboard**
**Duration:** 2 days | **Owner:** ML Engineer + Data Engineer

**Activities:**
- [ ] Choose dashboard framework (Streamlit, Dash, or Power BI)
- [ ] Create metrics overview page
- [ ] Create drift details page
- [ ] Create segment analysis page
- [ ] Create historical trends page
- [ ] Deploy dashboard

**Output:**
```python
# streamlit_app.py (Interactive Dashboard)

import streamlit as st
import pandas as pd
import plotly.express as px
from src.monitoring.pipeline import ChurnMonitoringPipeline
from src.analysis.root_cause_analysis import RootCauseAnalyzer

st.set_page_config(page_title="Churn Model Monitoring", layout="wide")

# Sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select Page", [
    "Overview",
    "Drift Analysis",
    "Performance Analysis",
    "Segment Breakdown",
    "Historical Trends"
])

# Load data
@st.cache_data
def load_metrics():
    query = "SELECT * FROM monitoring.metrics_log ORDER BY snapshot_date DESC LIMIT 100"
    return pd.read_sql(query, db_connection)

metrics_df = load_metrics()

if page == "Overview":
    st.title("Churn Model Monitoring - Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Get latest metrics
    latest = metrics_df.iloc[0]
    
    col1.metric("Current Recall", f"{latest['Recall']:.1%}", 
                delta=f"{latest['Recall_change']:.1%}")
    col2.metric("PSI Score", f"{latest['PSI_Score']:.3f}", 
                delta_color="off" if latest['PSI_Score'] < 0.25 else "inverse")
    col3.metric("Accuracy", f"{latest['Accuracy']:.1%}")
    col4.metric("Alert Count", latest['alert_count'])
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Recall Trend (Last 30 days)")
        recall_trend = metrics_df[metrics_df['metric_name'] == 'Recall'].tail(30)
        st.line_chart(recall_trend[['snapshot_date', 'metric_value']].set_index('snapshot_date'))
    
    with col2:
        st.subheader("Top Drifted Features")
        drift_features = metrics_df[metrics_df['metric_category'] == 'drift'].tail(25)
        top_drift = drift_features.nlargest(5, 'metric_value')
        st.bar_chart(top_drift[['feature_name', 'metric_value']].set_index('feature_name'))

if page == "Segment Breakdown":
    st.title("Performance by Customer Segment")
    
    segment_type = st.selectbox("Segment by:", ["Contract Type", "Tenure Band", "Charge Band"])
    
    if segment_type == "Contract Type":
        segment_data = load_segment_performance('contract_type')
        
        df_viz = pd.DataFrame(segment_data).T
        
        st.subheader("Recall by Contract Type")
        st.bar_chart(df_viz['recall'])
        
        st.subheader("Detailed Metrics")
        st.dataframe(df_viz)

# Dashboard deployed to: https://churn-monitoring.company.com
✅ Dashboard live
✅ Auto-refreshes every hour
✅ 5 pages, 20+ visualizations
✅ Mobile-responsive
```

---

#### **Task 2.3.2: Email Report Generation**
**Duration:** 1 day | **Owner:** ML Engineer

**Activities:**
- [ ] Create HTML email template
- [ ] Implement daily email generation
- [ ] Add key metrics to email
- [ ] Add action items section
- [ ] Setup email delivery

**Output:**
```html
<!-- templates/daily_monitoring_report.html -->

<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial; }
        .metric-card { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .status-pass { color: green; }
        .status-fail { color: red; }
        .status-warn { color: orange; }
    </style>
</head>
<body>
    <h2>Churn Model Monitoring Report - {{ date }}</h2>
    
    <h3>Executive Summary</h3>
    <div class="metric-card">
        <p><strong>Recall:</strong> <span class="status-pass">82.1%</span> (↑0.6% from yesterday)</p>
        <p><strong>Precision:</strong> <span class="status-pass">76.5%</span> (↓0.2%)</p>
        <p><strong>AUC-ROC:</strong> <span class="status-pass">0.924</span> (stable)</p>
        <p><strong>Data Drift (PSI):</strong> <span class="status-pass">0.08</span> (✅ No drift)</p>
        <p><strong>Alerts Generated:</strong> <span class="status-warn">1 Medium</span></p>
    </div>
    
    <h3>Alerts & Actions</h3>
    <div class="metric-card">
        <strong>🟡 MEDIUM: PSI_contract_type = 0.18</strong><br>
        <ul>
            <li>More monthly contracts in current period vs baseline</li>
            <li>Expected due to Q1 acquisition campaign</li>
            <li>Action: No intervention needed, continue monitoring</li>
        </ul>
    </div>
    
    <h3>Feature Drift (Top 5)</h3>
    <table border="1" cellpadding="10">
        <tr>
            <th>Feature</th>
            <th>PSI</th>
            <th>Status</th>
        </tr>
        <tr>
            <td>monthly_charges</td>
            <td>0.12</td>
            <td class="status-pass">✅ OK</td>
        </tr>
        <tr>
            <td>account_age</td>
            <td>0.08</td>
            <td class="status-pass">✅ OK</td>
        </tr>
        <tr>
            <td>contract_type</td>
            <td>0.18</td>
            <td class="status-warn">⚠️ Watch</td>
        </tr>
    </table>
    
    <h3>Segment Performance</h3>
    <p><strong>Best Performing:</strong> Two-year contracts (Recall: 89%)</p>
    <p><strong>Needs Attention:</strong> Month-to-month (Recall: 77%)</p>
    
    <h3>Recommended Actions</h3>
    <ol>
        <li>✅ Continue monitoring monthly contract segment</li>
        <li>✅ Collect feedback on why month-to-month harder to predict</li>
        <li>✅ Plan feature engineering workshop to improve for month-to-month</li>
    </ol>
    
    <hr>
    <p>Questions? Contact: ml-team@company.com</p>
    <p><a href="https://churn-monitoring.company.com">View Full Dashboard</a></p>
</body>
</html>

# Usage
from src.reporting.email_reporter import EmailReporter

reporter = EmailReporter('config/email_config.yaml')
html_report = reporter.generate_daily_report(metrics_df, alerts)
reporter.send_email(
    to=['ml-team@company.com', 'product@company.com'],
    subject=f"Churn Model Monitoring Report - {date}",
    html_content=html_report
)

✅ Email delivered daily at 5:00 AM UTC
✅ Recipients: 15 stakeholders
✅ Open rate: ~60%
✅ Click-through to dashboard: ~30%
```

---

### WEEK 8: Validation & Hardening

#### **Task 2.4.1: Comprehensive Testing & Validation**
**Duration:** 1.5 days | **Owner:** ML Engineer + QA

**Activities:**
- [ ] End-to-end testing with production-like data
- [ ] Validate metric calculations against manual checks
- [ ] Test error handling (missing data, API failures)
- [ ] Load testing (performance at scale)
- [ ] Disaster recovery testing (data loss, service interruption)

**Output:**
```
📄 testing/TEST_RESULTS_PHASE2.md

## Phase 2 Testing Results

### End-to-End Testing
✅ 50 test cases executed
✅ 50 passed, 0 failed
✅ Average execution time: 3.2 minutes
✅ Data integrity: 100% (no data loss)

### Metric Validation
✅ Compared Evidently metrics vs manual sklearn calculations
  - Recall: Match within 0.1% (sklearn: 0.821, Evidently: 0.8213)
  - Precision: Match within 0.1%
  - AUC-ROC: Match within 0.01%

### Error Handling
✅ Missing data handling:
  - NULL features → Handled correctly (skip in drift calculation)
  - Missing labels (with lag) → Expected, handled
  - API timeouts → Retry mechanism functional

✅ Edge cases:
  - Zero churn rate → Reported correctly
  - All same value → Drift detection skip appropriate
  - Extremely small batch → Handled gracefully

### Load Testing
✅ Performance at scale:
  - 100K records: 2.8 minutes
  - 1M records: 28.1 minutes
  - 10M records: Would require partitioning

✅ Memory usage:
  - 100K records: ~500 MB
  - 1M records: ~2.5 GB
  - Recommendation: Process in 100K batches for >1M

### Disaster Recovery
✅ Database failure recovery: OK
✅ Data warehouse downtime: Alert generated, graceful fallback
✅ Report generation failure: Logged, manual recovery possible
✅ Slack outage: Alert buffered, resent when service restored

## Overall Assessment: ✅ PRODUCTION-READY
```

---

#### **Task 2.4.2: Performance Optimization**
**Duration:** 1 day | **Owner:** ML Engineer + DevOps

**Activities:**
- [ ] Profile code execution bottlenecks
- [ ] Optimize pandas operations
- [ ] Cache intermediate results
- [ ] Parallelize where possible
- [ ] Optimize database queries

**Output:**
```python
# src/monitoring/pipeline_optimized.py

# BEFORE: 5.2 minutes for 100K records
# AFTER: 2.8 minutes (-46% improvement)

# Optimization 1: Vectorized PSI calculation
# BEFORE: Loop over columns
for col in columns:
    psi = calculate_psi(ref[col], cur[col])

# AFTER: Vectorized with numpy
def calculate_psi_vectorized(ref_dist, cur_dist):
    return np.sum((cur_dist - ref_dist) * np.log(cur_dist / ref_dist))
# Speed improvement: 3.5×

# Optimization 2: Caching reference data statistics
# BEFORE: Recompute reference stats every run
# AFTER: Cache reference quantiles, histograms
@lru_cache(maxsize=1)
def get_reference_stats(ref_data_hash):
    return compute_stats(ref_data)

# Speed improvement: 1.8×

# Optimization 3: Database batch insert
# BEFORE: Insert row-by-row (1000 rows = 1000 queries)
for _, row in metrics_df.iterrows():
    cursor.execute("INSERT INTO metrics_log VALUES (...)", row)

# AFTER: Batch insert
values = [tuple(row) for _, row in metrics_df.iterrows()]
cursor.executemany("INSERT INTO metrics_log VALUES (%s, %s, ...)", values)

# Speed improvement: 50×

## Final Performance
✅ Execution time: 2.8 minutes (target: <5 minutes) ✅
✅ Memory usage: 480 MB (sustainable)
✅ Database inserts: 0.3 seconds (was 15 seconds)
```

---

## SUMMARY: PHASE 2 OUTPUTS

**Total Effort:** 4 weeks | **Completeness:** 100%

### Key Deliverables:
✅ Live production monitoring (daily automated)
✅ Root cause analysis dashboard
✅ Feature importance tracking
✅ Interactive Streamlit dashboard
✅ Daily email reports
✅ Comprehensive testing & validation
✅ Performance optimization (46% faster)

### Key Files Created:
- `src/data/production_loader.py` (Production integration)
- `src/analysis/root_cause_analysis.py` (RCA logic)
- `src/analysis/feature_importance.py` (WoE/IV calculation)
- `streamlit_app.py` (Interactive dashboard)
- `src/reporting/email_reporter.py` (Email generation)
- `dags/churn_monitoring_dag.py` (Airflow orchestration)

### Success Criteria Met:
✅ Production data successfully integrated
✅ Daily monitoring fully automated
✅ All reports generated & delivered
✅ Dashboard live & accessible
✅ Testing comprehensive (50 test cases)
✅ Performance optimized (46% improvement)

### Handoff to Phase 3:
- System operating reliably in production
- All SLAs being met
- Operational team trained
- Ready for advanced features (Arize integration, deeper analysis)

---

## PHASE 3: ADVANCED FEATURES & OPTIMIZATION (Weeks 9-12)
### Sprint 3: Arize Integration, Deep Analysis, Scaling

*(This content would follow the same detailed format...)*

### HIGH-LEVEL PHASE 3 TASKS:

**Week 9: Arize Integration (Optional)**
- Task 3.1.1: Arize account setup & API integration
- Task 3.1.2: Historical data backfill to Arize
- Task 3.1.3: Configure Arize monitors & alerts

**Week 10: Advanced Monitoring Features**
- Task 3.2.1: Implement concept drift monitoring (actual churn rate changes)
- Task 3.2.2: Build segment-level drift detection
- Task 3.2.3: Add anomaly detection (isolation forests)

**Week 11: Production Hardening**
- Task 3.3.1: Implement circuit breakers & fallbacks
- Task 3.3.2: Setup monitoring for the monitoring system itself
- Task 3.3.3: Documentation of runbooks

**Week 12: Final Testing & Knowledge Transfer**
- Task 3.4.1: Production readiness review
- Task 3.4.2: Operational team training
- Task 3.4.3: Handoff & ongoing support plan

---

## FINAL PROJECT SUMMARY

### Timeline Overview

```
PHASE 1 (Weeks 1-4): Foundation
├─ Week 1: Research & Evaluation
├─ Week 2: Environment Setup
├─ Week 3: Core Implementation
└─ Week 4: Testing & Documentation

PHASE 2 (Weeks 5-8): Production Pilot
├─ Week 5: Production Integration & Pilot
├─ Week 6: Performance Analysis & RCA
├─ Week 7: Visualization & Dashboarding
└─ Week 8: Validation & Hardening

PHASE 3 (Weeks 9-12): Advanced Features
├─ Week 9: Optional Arize Integration
├─ Week 10: Advanced Monitoring
├─ Week 11: Production Hardening
└─ Week 12: Final Testing & Handoff
```

### Key Outputs by Category

**CODE:**
- ✅ 10+ Python modules (monitoring, analysis, reporting)
- ✅ 40+ unit tests, 100+ integration tests
- ✅ Airflow DAG for orchestration
- ✅ Streamlit dashboard application

**DOCUMENTATION:**
- ✅ Architecture & design documents
- ✅ Operational runbooks
- ✅ Troubleshooting guides
- ✅ Configuration manuals
- ✅ Metrics specification

**REPORTS & DASHBOARDS:**
- ✅ Daily HTML monitoring reports
- ✅ JSON metric snapshots
- ✅ Interactive Streamlit dashboard
- ✅ Email summaries
- ✅ Root cause analysis reports

**DATA STRUCTURES:**
- ✅ PostgreSQL schema for metrics logging
- ✅ CSV exports for BI integration
- ✅ S3 storage for historical snapshots

---

## SUCCESS METRICS

**By End of Phase 3 (Week 12):**

1. **Monitoring Coverage:**
   - [ ] 10/10 key metrics implemented & monitored
   - [ ] 100% daily report generation success rate
   - [ ] <1% false alert rate (tuned thresholds)

2. **Performance:**
   - [ ] <5 minute daily execution time
   - [ ] <1 MB daily storage per snapshot
   - [ ] <500 MB peak memory usage

3. **Operational:**
   - [ ] 99.5% uptime SLA achieved
   - [ ] <5 minute mean time to incident detection
   - [ ] <30 minute mean time to resolution

4. **Business Impact:**
   - [ ] 3+ instances of proactive issues caught
   - [ ] 2+ model retraining decisions enabled
   - [ ] 100% stakeholder adoption of reports

---

**Document Created:** 2025-01-05
**Last Updated:** 2025-01-05
**Status:** ACTIVE - Ready for Sprint Planning
