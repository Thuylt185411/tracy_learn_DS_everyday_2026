# Enhanced ML Monitoring for Production Pipelines using Prefect, PostgreSQL, and Grafana

This example shows steps to integrate Evidently into your production pipeline using Prefect, PostgreSQL, and Grafana.

1. Run production ML pipelines for inference and monitoring with Prefect.[https://www.prefect.io/]
2. Generate data quality and model monitoring reports with EvidentlyAI
3. Save monitoring metrics to PostgreSQL database [https://www.postgresql.org/]
4. Visualize ML monitoring dashboards in Grafana [https://grafana.com/]

## Project Organization

```
├── README.md          <- The top-level README for developers using this project.
├── data
│   ├── features       <- Features for model training and inference.
│   ├── predictions    <- Generated predictions.
│   ├── raw            <- The original, immutable data dump.
│   └── reference      <- Reference datasets for monitoring.
│
├── grafana            <- Configs for Grafana dashboards
│
├── models             <- Trained and serialized models, model predictions, or model summaries
│
├── prefect            <- Prefect artifacts and DB
│
├── src                <- Source code for use in this project.
│   ├── monitoring     <- Common code for monitoring 
│   │
│   ├── pipelines      <- Source code for all pipelines
│   │
│   ├── scripts        <- Helper scripts
│   │
│   ├── utils          <- Utility functions and classes 
│
└── static             <- Assets for docs
```

### Installation

```
click
evidently==0.3.1
fastparquet==2023.2.0
httpx==0.23.3
pandas==1.5.3
python-dotenv>=0.5.1
prefect==2.9.0
psycopg2-binary==2.9.5
pyarrow==11.0.0
scikit-learn==1.2.2
sqlalchemy
tqdm
```

```
uv venv .venv
.\.venv\Scripts\activate
uv pip install -r 0_example\requirements.txt
```



BEST PRACTICE: https://github.com/evidentlyai/evidently/tree/ad71e132d59ac3a84fce6cf27bd50b12b10d9137/examples/integrations/postgres_grafana_batch_monitoring
