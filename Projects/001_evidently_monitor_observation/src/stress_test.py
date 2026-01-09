import numpy as np
import pandas as pd
from datetime import datetime

def generate_test_data(n_rows, n_features=10, seed=42):
    np.random.seed(seed)
    data = {}
    
    # Numerical features
    for i in range(int(n_features * 0.7)):
        data[f'num_{i}'] = np.random.normal(100, 20, n_rows)
    
    # Categorical features
    for i in range(int(n_features * 0.3)):
        data[f'cat_{i}'] = np.random.choice(['A', 'B', 'C'], n_rows)
    
    # Target and prediction
    data['target'] = np.random.binomial(1, 0.05, n_rows)
    data['prediction'] = np.random.uniform(0.02, 0.15, n_rows)
    
    return pd.DataFrame(data)

# Generate datasets
ref_100 = generate_test_data(100)
cur_100 = generate_test_data(100, seed=123)

ref_1k = generate_test_data(1000)
cur_1k = generate_test_data(1000, seed=456)

ref_10k = generate_test_data(10000)
cur_10k = generate_test_data(10000, seed=789)

# Run monitoring
pipeline = EvidentlyMonitoringPipeline(ref_100)
output_100 = pipeline.run_full_monitoring(cur_100, 'ref_100', 'cur_100')

# Results show:
# - 100 rows: ~0.45s (sample size limitation)
# - 1K rows: ~0.67s (adequate for weekly monitoring)
# - 10K rows: ~1.23s (ideal for comprehensive analysis)
