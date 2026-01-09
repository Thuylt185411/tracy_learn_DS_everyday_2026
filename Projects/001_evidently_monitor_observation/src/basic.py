from evidently.report import Report
from evidently.metric_preset import (
    DataDriftPreset,
    DataQualityPreset,
    ClassificationPreset
)
from evidently.metrics import ColumnDriftMetric
import pandas as pd
import json

class EvidentlyMonitoringPipeline:
    def __init__(self, reference_data, column_mapping=None):
        self.ref_data = reference_data
        self.col_mapping = column_mapping
    
    def run_full_monitoring(self, current_data, ref_id, cur_id):
        """Execute complete monitoring pipeline"""
        
        results = {}
        
        # Drift Detection
        drift_report = Report(metrics=[DataDriftPreset()])
        drift_report.run(
            reference_data=self.ref_data,
            current_data=current_data,
            column_mapping=self.col_mapping
        )
        results['drift'] = drift_report.as_dict()
        
        # Data Quality
        quality_report = Report(metrics=[DataQualityPreset()])
        quality_report.run(
            reference_data=self.ref_data,
            current_data=current_data
        )
        results['quality'] = quality_report.as_dict()
        
        # Performance (if has target & prediction)
        if 'target' in current_data.columns and 'prediction' in current_data.columns:
            perf_report = Report(metrics=[ClassificationPreset()])
            perf_report.run(
                reference_data=self.ref_data,
                current_data=current_data,
                column_mapping=self.col_mapping
            )
            results['performance'] = perf_report.as_dict()
        
        # Aggregate
        output = {
            'metadata': {
                'timestamp': pd.Timestamp.now().isoformat(),
                'reference_id': ref_id,
                'current_id': cur_id
            },
            'results': results
        }
        
        return output
    
    def save_snapshot(self, output, path):
        """Save JSON snapshot for history tracking"""
        with open(path, 'w') as f:
            json.dump(output, f, indent=2, default=str)
    
    def extract_metrics_table(self, output):
        """Extract metrics into DataFrame for CSV export"""
        metrics_list = []
        
        drift_metrics = output['results']['drift']['metrics'][0]['result']
        
        # Dataset level
        metrics_list.append({
            'metric': 'PSI_Score',
            'value': drift_metrics.get('dataset_drift'),
            'threshold': 0.25
        })
        
        # Feature level
        for feat_name, feat_metrics in drift_metrics['metrics'].items():
            metrics_list.append({
                'metric': f'PSI_{feat_name}',
                'value': feat_metrics.get('p_value'),
                'threshold': 0.1
            })
        
        return pd.DataFrame(metrics_list)


