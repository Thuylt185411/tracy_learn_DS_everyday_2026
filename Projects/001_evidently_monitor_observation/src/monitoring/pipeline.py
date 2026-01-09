from evidently.report import Report
from evidently.metric_preset import (
    DataDriftPreset,
    ClassificationPreset,
    DataQualityPreset
)

report = Report(metrics=[
    DataDriftPreset(),          # Feature drift (PSI)
    ClassificationPreset(),     # Recall, Precision, AUC
    DataQualityPreset()         # Missing values, outliers
])

report.run(reference_data, current_data)
report.save_html('report.html')