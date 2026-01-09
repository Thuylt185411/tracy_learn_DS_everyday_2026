from evidently.report import Report
from evidently.metric_preset import (
    DataDriftPreset,
    DataQualityPreset,
    ClassificationPreset
)
from evidently.metrics import ColumnDriftMetric
import pandas as pd
import json


DataDriftPreset()

# Custom method selection
from evidently.metrics import ColumnDriftMetric

report = Report(metrics=[
    ColumnDriftMetric(
        column_name='prediction_score',
        stattest_name='psi'  # PSI
    ),
    ColumnDriftMetric(
        column_name='age',
        stattest_name='wasserstein'  # Wasserstein distance
    )
])