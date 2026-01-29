import yaml
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import json
import warnings
warnings.filterwarnings('ignore')

from evidently import Regression, Report
from evidently.metrics import ValueDrift, RocAuc, RocAucByLabel
from evidently.presets import DataDriftPreset, ClassificationPreset
from evidently import Dataset
from evidently import DataDefinition
from evidently.legacy.metric_preset import TargetDriftPreset, DataQualityPreset
from sklearn.metrics import roc_auc_score
import scorecardpy as sc
import sys

SCR_PATH = 'D:/WORK_F88/Tracy/Projects/001_evidently_monitor_observation'
sys.path.append(SCR_PATH)

from src.monitoring.utils import (load_config, 
get_html_from_evidently,
get_from_file,
replace_html_content
)
from src.monitoring.metrics import (
    AUCMetric,
    GiniMetric,
    DefaultRateMetric,
    KSMetric,
    BasicWOEMetric,
    IVSummaryMetric,
    MyValueDrift,
    MyValueDriftCalculation,
    MyValueDrift_2,
    MyValueDriftCalculation_2,
)


class GenericModelMonitor:

    
    def __init__(self, config_path: str):
        self.config = load_config(config_path)
        
        self.model_name = self.config['model']['name']
        self.output_dir = self.config['output']['reports_dir']
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        self.numerical_columns = self.config['columns']['features_numeric']
        self.categorical_columns = self.config['columns']['features_categorical']
        self.id_column = self.config['columns']['id_column']
        self.timestamp_column = self.config['columns']['timestamp_column']
        self.target_column = self.config['columns']['target']
        self.predict_column = self.config['columns']['prediction']
        self.base_path = self.config['base_path']['path']
        # self.datetime_columns = self.config['columns']['datetime_column']
            
    def _to_evidently_dataset(
        self, 
        df: pd.DataFrame, 
        include_target: bool = False,
        include_prediction: bool = False,
        include_timestamp: bool = True,
    ) -> Dataset:
        """
        Chuyển pandas DataFrame thành Evidently Dataset với definition phù hợp.
        
        Args:
            df: DataFrame cần chuyển đổi
            include_target: Thêm target column vào numerical
            include_prediction: Thêm prediction column vào numerical
            include_timestamp: Bao gồm timestamp column trong Dataset (cho drift theo thời gian)
        """
        df = df.copy()
        
        # Xử lý timestamp_column: convert sang datetime nếu cần
        timestamp_col = None
        if include_timestamp and self.timestamp_column and self.timestamp_column in df.columns:
            if not pd.api.types.is_datetime64_any_dtype(df[self.timestamp_column]):
                print('converting timestamp column to datetime: ', self.timestamp_column)
                df[self.timestamp_column] = pd.to_datetime(df[self.timestamp_column],format='%Y%m%d', errors='coerce')
            timestamp_col = self.timestamp_column

        # if not pd.api.types.is_datetime64_any_dtype(df[self.datetime_columns]):
        #     df[self.datetime_columns] = pd.to_datetime(df[self.datetime_columns],format='%Y%m%d', errors='coerce')

        num_cols = [c for c in self.numerical_columns if c in df.columns]
        cat_cols = [c for c in self.categorical_columns if c in df.columns]
        
        # Thêm target/prediction vào numerical nếu có
        if include_target and self.target_column in df.columns:
            num_cols = num_cols + [self.target_column]
        if include_prediction and self.predict_column in df.columns:
            num_cols = num_cols + [self.predict_column]
        
        definition = DataDefinition(
            id_column=self.id_column if self.id_column in df.columns else None,
            timestamp=timestamp_col,  
            numerical_columns=num_cols,  
            categorical_columns=cat_cols,
        )
        
        return Dataset.from_pandas(df, data_definition=definition)
    
    def _merge_dataframes(
        self,
        features_df: pd.DataFrame,
        labels_df: Optional[pd.DataFrame] = None,
        score_df: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        """
        Merge features với labels và/hoặc score dựa trên id_column.
        Drop duplicates trước khi merge để tránh tăng số rows.
        """
        result = features_df.copy()
        
        # Drop duplicates trong result theo id_column
        # if self.id_column in result.columns:
        #     result = result.drop_duplicates(subset=[self.id_column], keep='first')
        
        if labels_df is not None:
            if self.id_column in labels_df.columns and self.id_column in result.columns:
                # Drop duplicates trong labels trước khi merge
                # labels_clean = labels_df.drop_duplicates(subset=[self.id_column], keep='first')
                labels_clean = labels_df.copy()
                result = result.merge(labels_clean, on=[self.id_column, self.timestamp_column], how='left')
            else:
                result[self.target_column] = labels_df[self.target_column].values
        
        if score_df is not None:
            if self.id_column in score_df.columns and self.id_column in result.columns:
                # Drop duplicates trong score trước khi merge
                # score_clean = score_df.drop_duplicates(subset=[self.id_column], keep='first')
                score_clean = score_df.copy()
                result = result.merge(score_clean, on=[self.id_column, self.timestamp_column], how='left')
            else:
                result[self.predict_column] = score_df[self.predict_column].values
        
        return result

    def check_data_quality(
        self, 
        cur_features: pd.DataFrame, 
        ref_features: pd.DataFrame,
        period: str
    ) -> Dict:
        """
        Kiểm tra chất lượng dữ liệu (chỉ cần features):
        - Missing values
        - Duplicates
        - Out-of-range values
        - Constant columns
        """
        print(f"▶ Data Quality Check...")
        from evidently import Report
        from evidently.metrics import (
            DatasetMissingValueCount, EmptyRowsCount, 
            DuplicatedRowCount, ConstantColumnsCount,
            ColumnCorrelationMatrix,ColumnCorrelations,
            DatasetCorrelations,
        )
        from evidently.presets import DataSummaryPreset

        # Convert to Evidently Dataset
        cur_dataset = self._to_evidently_dataset(cur_features)
        ref_dataset = self._to_evidently_dataset(ref_features)

        report = Report([
            DatasetMissingValueCount(),
            DuplicatedRowCount(),
            EmptyRowsCount(),
            ConstantColumnsCount(),
            DataSummaryPreset(),
            DatasetCorrelations(),
        ],
        include_tests=True
        )
        
        ev = report.run(cur_dataset, ref_dataset)
        result_json = ev.json()
        
        period_dir = Path(self.base_path) / self.output_dir / period
        period_dir.mkdir(parents=True, exist_ok=True)
        report_path = str(period_dir / f"{self.model_name}_{period}_data_quality.html")
        
        ev.save_html(report_path)
        print(f"  Save to: {report_path}")

        return result_json, ev, report_path
    
    def detect_drift(
        self, 
        cur_features: pd.DataFrame, 
        ref_features: pd.DataFrame,
        cur_score: pd.DataFrame,
        ref_score: pd.DataFrame,
        period: str
    ) -> Dict:
        """
        Phát hiện Drift (cần features + score + timestamp):
        - Numeric features: KS test hoặc Wasserstein
        - Categorical: Chi-square hoặc PSI
        - Score drift: PSI
        - Sử dụng timestamp_column để chia theo thời gian (không theo index)
        """
        print(f"▶ Drift Detection...")
        
        # Merge features + score (timestamp_column sẽ được merge cùng nếu có trong score)
        cur_df = self._merge_dataframes(cur_features, score_df=cur_score)
        ref_df = self._merge_dataframes(ref_features, score_df=ref_score)

        cur_dataset = self._to_evidently_dataset(cur_df, include_prediction=True, include_timestamp=True)
        ref_dataset = self._to_evidently_dataset(ref_df, include_prediction=True, include_timestamp=True)
        # print(f"cur_dataset: {cur_dataset.as_dataframe().head()}")
        drift_config = self.config['drift']
        
        # Build metrics list
        metrics = [
            
            MyValueDrift_2(
                column=self.predict_column, 
                method="psi", 
                timestamp_column=self.timestamp_column
            ),
            # Feature Drift
            DataDriftPreset(
                columns=[*self.numerical_columns, *self.categorical_columns],
                num_method=drift_config['method_numeric'],
                cat_method=drift_config['method_categorical'],
                include_tests=True
            ),
            ]
        
        report = Report(metrics, include_tests=True)
        
        ev = report.run(current_data=cur_dataset, reference_data=ref_dataset)
        
        period_dir = Path(self.base_path) / self.output_dir / period
        period_dir.mkdir(parents=True, exist_ok=True)
        drift_html_path = str(period_dir / f"{self.model_name}_{period}_drift.html")
        ev.save_html(drift_html_path)
        print(f"  Save to: {drift_html_path}")
     
        return ev.json(), ev, drift_html_path
    
    def evaluate_performance(
        self, 
        cur_labels: pd.DataFrame, 
        ref_labels: pd.DataFrame,
        cur_score: pd.DataFrame,
        ref_score: pd.DataFrame,
        period: str
    ) -> Dict:
        """
        Đánh giá performance (cần labels + score):
        - AUC-ROC
        - Gini = 2*AUC - 1
        - KS statistic
        """
        print(f"▶ Performance Evaluation...")
        
        # Merge labels + score
        cur_df = cur_labels.copy()
        cur_df[self.predict_column] = cur_score[self.predict_column].values
        
        ref_df = ref_labels.copy()
        ref_df[self.predict_column] = ref_score[self.predict_column].values
        
        # Convert to Evidently Dataset
        cur_dataset = self._to_evidently_dataset(cur_df, include_target=True, include_prediction=True)
        ref_dataset = self._to_evidently_dataset(ref_df, include_target=True, include_prediction=True)
         
        report = Report([
            AUCMetric(true_column=self.target_column, pred_column=self.predict_column),
            GiniMetric(true_column=self.target_column, pred_column=self.predict_column),
            KSMetric(true_column=self.target_column, pred_column=self.predict_column),
        ],
        # include_tests=True
        )
        ev = report.run(cur_dataset, ref_dataset)
        
        period_dir = Path(self.base_path) / self.output_dir / period
        period_dir.mkdir(parents=True, exist_ok=True)
        perf_html_path = str(period_dir / f"{self.model_name}_{period}_evaluate_performance.html")
        ev.save_html(perf_html_path)
        print(f"  Save to: {perf_html_path}")
    
        return ev.json(), ev, perf_html_path
    
    def evaluate_scorecard_health(
        self, 
        cur_features: pd.DataFrame, 
        ref_features: pd.DataFrame,
        cur_labels: pd.DataFrame,
        ref_labels: pd.DataFrame,
        period: str
    ) -> Dict:
        """
        Kiểm tra sức khỏe scorecard (cần features + labels):
        - Default rate
        - WoE/IV per feature
        - IV change monitoring
        """
        print(f"▶ Scorecard Health Check...")
        
        # Merge features + labels
        cur_df = self._merge_dataframes(cur_features, labels_df=cur_labels)
        ref_df = self._merge_dataframes(ref_features, labels_df=ref_labels)
        
        # Convert to Evidently Dataset
        cur_dataset = self._to_evidently_dataset(cur_df, include_target=True)
        ref_dataset = self._to_evidently_dataset(ref_df, include_target=True)
        
        report = Report([
            
            DefaultRateMetric(
                true_column=self.target_column, 
                pred_column=self.predict_column),
            IVSummaryMetric(
                numeric_features=self.numerical_columns,
                categorical_features=self.categorical_columns,
                target_column=self.target_column),
            BasicWOEMetric(
                features=self.numerical_columns + self.categorical_columns,
                target_column=self.target_column),
        ],
        # include_tests=True
        )
        ev = report.run(cur_dataset, ref_dataset)
        
        period_dir = Path(self.base_path) / self.output_dir / period
        period_dir.mkdir(parents=True, exist_ok=True)
        perf_html_path = str(period_dir / f"{self.model_name}_{period}_default_rate_iv_woe.html")
        ev.save_html(perf_html_path)
        print(f"  Save to: {perf_html_path}")
        
        return ev.json(), ev, perf_html_path


    def combine_html_reports(self, html_paths: List[str], period: str) -> str:
        print(f"\n▶ Building html reports")
        print(f"html_paths: {html_paths}")
        ev1_html = get_from_file(html_paths[0])
        ev2_html = get_from_file(html_paths[1])
        ev3_html = get_from_file(html_paths[2])
        ev4_html = get_from_file(html_paths[3])
        print(f"ev1_html: {ev1_html[:100]}")
        format_html_path = r'D:\WORK_F88\Tracy\Projects\001_evidently_monitor_observation\src\monitoring\format.html'
       
        new_content = f"""
        <div class="tab">
        <button class="tablinks active" onclick="openTab(event, 'tab1')">Overview</button>
        <button class="tablinks" onclick="openTab(event, 'tab2')">Data and Score Drift</button>
        <button class="tablinks" onclick="openTab(event, 'tab3')">Label</button>
        <button class="tablinks" onclick="openTab(event, 'tab4')">Model Discrimination</button>
        </div>

        <div id="tab1" class="tabcontent active">{ev1_html}</div>
        <div id="tab2" class="tabcontent">{ev2_html}</div>
        <div id="tab3" class="tabcontent">{ev3_html}</div>
        <div id="tab4" class="tabcontent">{ev4_html}</div>
        """

        # New: Make period a subfolder
        period_dir = Path(self.base_path) / self.output_dir / period
        period_dir.mkdir(parents=True, exist_ok=True)
        new_html_content = replace_html_content(format_html_path, new_content)
        output_html_path = str(period_dir / f"{self.model_name}_{period}_all_model_monitoring_report_tabs.html")
        with open(output_html_path, "w", encoding="utf-8") as f:
            f.write(new_html_content)
        print("Save to ", output_html_path)
        return output_html_path
    
    def run_monitoring(
        self, 
        period: str,
        # 3 DataFrames riêng biệt cho reference
        ref_features: pd.DataFrame,
        ref_labels: pd.DataFrame,
        ref_score: pd.DataFrame,
        # 3 DataFrames riêng biệt cho current
        cur_features: pd.DataFrame,
        cur_labels: pd.DataFrame,
        cur_score: pd.DataFrame,
        # Flags để bật/tắt từng report
        data_quality: bool = True,
        drift: bool = True,
        performance: bool = True,
        scorecard: bool = True
    ):
        """
        Chạy toàn bộ monitoring pipeline cho 1 period.
        
        Args:
            period: Tên period (dùng làm subfolder)
            ref_features: DataFrame chứa features của reference data
            ref_labels: DataFrame chứa labels (target) của reference data
            ref_score: DataFrame chứa score (prediction) của reference data
            cur_features: DataFrame chứa features của current data
            cur_labels: DataFrame chứa labels (target) của current data
            cur_score: DataFrame chứa score (prediction) của current data
            data_quality: Chạy Data Quality report (chỉ cần features)
            drift: Chạy Drift Detection report (cần features + score)
            performance: Chạy Performance Evaluation report (cần labels + score)
            scorecard: Chạy Scorecard Health report (cần features + labels)
        """
        print(f"\n{'='*70}")
        print(f"MODEL: {self.model_name} | PERIOD: {period}")
        print(f"{'='*70}")
        
        # Make period a subfolder for output
        period_dir = Path(self.base_path) / self.output_dir / period
        period_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n▶ Data shapes:")
        print(f"  Reference - features: {ref_features.shape}, labels: {ref_labels.shape}, score: {ref_score.shape}")
        print(f"  Current   - features: {cur_features.shape}, labels: {cur_labels.shape}, score: {cur_score.shape}")
        
        # Initialize variables
        ev_1 = ev_2 = ev_3 = ev_4 = None
        
        # 1. Data Quality (chỉ cần features)
        if data_quality:
            dq_result, ev_1, html_1 = self.check_data_quality(
                cur_features=cur_features, 
                ref_features=ref_features, 
                period=period
            )
        
        # 2. Drift Detection (cần features + score)
        if drift:
            drift_result, ev_2, html_2 = self.detect_drift(
                cur_features=cur_features, 
                ref_features=ref_features,
                cur_score=cur_score,
                ref_score=ref_score,
                period=period
            )
        
        # 3. Scorecard Health (cần features + labels)
        if scorecard:
            scorecard_result, ev_3, html_3 = self.evaluate_scorecard_health(
                cur_features=cur_features,
                ref_features=ref_features,
                cur_labels=cur_labels,
                ref_labels=ref_labels,
                period=period
            )
        
        # 4. Performance Evaluation (cần labels + score)
        if performance:
            perf_result, ev_4, html_4 = self.evaluate_performance(
                cur_labels=cur_labels,
                ref_labels=ref_labels,
                cur_score=cur_score,
                ref_score=ref_score,
                period=period
            )
        
        # Combine all reports if all flags are True
        if all([data_quality, drift, performance, scorecard]):
            ev_html1 = get_html_from_evidently(ev_1)
            ev_html2 = get_html_from_evidently(ev_2)
            ev_html3 = get_html_from_evidently(ev_3)
            ev_html4 = get_html_from_evidently(ev_4)
            format_html_path = r'D:\WORK_F88\Tracy\Projects\001_evidently_monitor_observation\src\monitoring\format.html'
       
            new_content = f"""
            <div class="tab">
            <button class="tablinks active" onclick="openTab(event, 'tab1')">Overview</button>
            <button class="tablinks" onclick="openTab(event, 'tab2')">Data and Score Drift</button>
            <button class="tablinks" onclick="openTab(event, 'tab3')">Scorecard Health</button>
            <button class="tablinks" onclick="openTab(event, 'tab4')">Model Performance</button>
            </div>

            <div id="tab1" class="tabcontent active">{ev_html1}</div>
            <div id="tab2" class="tabcontent">{ev_html2}</div>
            <div id="tab3" class="tabcontent">{ev_html3}</div>
            <div id="tab4" class="tabcontent">{ev_html4}</div>
            """

            new_html_content = replace_html_content(format_html_path, new_content)
            output_html_path = str(period_dir / f"{self.model_name}_{period}_all_model_monitoring_report_tabs.html")
            with open(output_html_path, "w", encoding="utf-8") as f:
                f.write(new_html_content)
            print(f"\n✅ Combined report saved to: {output_html_path}")
        else:
            output_html_path = str(period_dir)
            print(f"\n✅ Individual reports saved to: {output_html_path}")
            
        return output_html_path


# ===== USAGE =====
if __name__ == "__main__":
    # Khởi tạo monitor
    monitor = GenericModelMonitor(
        r'D:\WORK_F88\Tracy\Projects\001_evidently_monitor_observation\data\dummy_data\monitoring_config.yaml'
    )

    BASE_DATA_PATH = r'D:\WORK_F88\Tracy\Projects\001_evidently_monitor_observation\data\dummy_data'

    # ==================== Load DataFrames riêng biệt ====================
    # Reference data
    ref_features = pd.read_csv(f'{BASE_DATA_PATH}/ref_all_features.csv')
    ref_labels = pd.read_csv(f'{BASE_DATA_PATH}/ref_all_labels.csv')
    ref_score = pd.read_csv(f'{BASE_DATA_PATH}/ref_all_score.csv')

    # Current data
    cur_features = pd.read_csv(f'{BASE_DATA_PATH}/cur_all_features.csv')
    cur_labels = pd.read_csv(f'{BASE_DATA_PATH}/cur_all_labels.csv')
    cur_score = pd.read_csv(f'{BASE_DATA_PATH}/cur_all_score.csv')
    ref_labels.columns = ['CUSTOMER_CODE', 'LOAN_ID', 'LABEL', 'SCORING_DATE']

    result = monitor.run_monitoring(
    period='20260127',
    # Reference data (3 DataFrames)
    ref_features=ref_features,
    ref_labels=ref_labels,
    ref_score=ref_score,
    # Current data (3 DataFrames)
    cur_features=cur_features,
    cur_labels=cur_labels,
    cur_score=cur_score,
    # Flags
    data_quality=True,
    drift=True,
    performance=True,
    scorecard=True,
    # combine_reports=True
    )

    
    print(f"\n✅ Report saved to: {result}")