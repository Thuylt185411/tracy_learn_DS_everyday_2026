from evidently import Dataset
from evidently.core.metric_types import ColumnMetric
from evidently.legacy.tests.base_test import TestStatus
from evidently.legacy.metric_results import ScatterField
from evidently.core.metric_types import MetricTestResult
import pandas as pd
import numpy as np
from evidently import Dataset
from evidently.legacy.renderers.html_widgets import table_data
from evidently.legacy.renderers.html_widgets import widget_tabs
from evidently.legacy.calculations.data_drift import ColumnDataDriftMetrics
from evidently.legacy.metric_results import HistogramData
from evidently.legacy.utils.visualizations import plot_agg_line_data
from evidently.legacy.utils.visualizations import plot_distr_with_perc_button
from evidently.legacy.utils.visualizations import plot_scatter_for_data_drift
from evidently.core.report import Context
from evidently.core.metric_types import SingleValue
from evidently.core.metric_types import SingleValueMetric
from evidently.core.metric_types import SingleValueCalculation
from evidently.legacy.options.data_drift import DataDriftOptions
from evidently.legacy.calculations.data_drift import get_one_column_drift
from evidently.legacy.options import ColorOptions
from evidently.legacy.options.base import Options
from evidently.legacy.metric_results import DatasetColumns
from evidently.legacy.metric_results import DatasetUtilityColumns
from evidently.legacy.renderers.html_widgets import CounterData
from evidently.legacy.renderers.html_widgets import TabData
from evidently.legacy.renderers.html_widgets import counter
from evidently.legacy.core import ColumnType
from evidently.legacy.renderers.html_widgets import plotly_figure

from typing import Optional
import numpy as np
import pandas as pd
DROP_COLS = ["CUSTOMER_CODE", "DATE_PARTITION", "DISBURSE_DATE_WID"]


class MyValueDrift(ColumnMetric, SingleValueMetric):
    column: str
    """Tên cột để phân tích drift."""
    method: Optional[str] = None
    """Drift detection method (auto-selected if None)."""
    threshold: Optional[float] = None
    """Drift threshold (uses method default if None)."""
    timestamp_column: Optional[str] = None
    """Tên cột timestamp để phân tích drift theo thời gian."""

class MyValueDriftCalculation(SingleValueCalculation[MyValueDrift]):
    def calculate(
        self,
        context: "Context",
        current_data: Dataset,
        reference_data: Optional[Dataset],
    ) -> SingleValue:
        """
        Tính value drift cho một cột kèm theo phân nhóm theo cột timestamp (nếu có).
        Nếu self.metric.timestamp_column được cung cấp, drift sẽ tính trong từng nhóm timestamp,
        sau đó trả về số liệu tổng quan hoặc thêm thông tin theo từng mốc thời gian.
        """
        column = self.metric.column
        column_type = current_data.column(column).type

        if reference_data is None:
            raise ValueError("Reference data is required for Value Drift")

        timestamp_col = self.metric.timestamp_column

        if not timestamp_col:
            options = DataDriftOptions(
                all_features_stattest=self.metric.method,
                all_features_threshold=self.metric.threshold,
            )

            drift = get_one_column_drift(
                current_data=current_data.as_dataframe(),
                reference_data=reference_data.as_dataframe(),
                column_name=column,
                options=options,
                dataset_columns=DatasetColumns(
                    utility_columns=DatasetUtilityColumns(),
                    num_feature_names=[column] if column_type == ColumnType.Numerical else [],
                    cat_feature_names=[column] if column_type == ColumnType.Categorical else [],
                    text_feature_names=[column] if column_type == ColumnType.Text else [],
                    datetime_feature_names=[column] if column_type == ColumnType.Datetime else [],
                    target_names=None,
                ),
                column_type=column_type,
                agg_data=True,
            )

            if self.metric.method is None:
                self.resolve_parameter("method", drift.stattest_name)
            if self.metric.threshold is None:
                self.resolve_parameter("threshold", drift.stattest_threshold)
            result = self.result(drift.drift_score)
            result.widget = self._render(drift, Options(), ColorOptions())
            return result

        # --- Drift theo từng nhóm timestamp ---
        # So sánh: current[mỗi timestamp] vs reference (toàn bộ)
        current_df = current_data.as_dataframe()
        reference_df = reference_data.as_dataframe()

        # Kiểm tra tồn tại cột timestamp trong current
        if timestamp_col not in current_df.columns:
            raise ValueError(f"Timestamp column '{timestamp_col}' not found in current dataset.")

        # Ép kiểu datetime cho current
        if not np.issubdtype(current_df[timestamp_col].dtype, np.datetime64):
            try:
                current_df[timestamp_col] = pd.to_datetime(current_df[timestamp_col])
            except Exception:
                pass

        # Lấy các timestamp unique từ current (sắp xếp tăng dần)
        timestamps = np.sort(current_df[timestamp_col].dropna().unique())
        print(f"    Found {len(timestamps)} unique timestamps in current data")

        # Phân tích drift: current[mỗi timestamp] vs reference (toàn bộ)
        drift_scores = []
        drift_detecteds = []
        group_results = []
        
        for ts in timestamps:
            # Lấy slice của current tại timestamp này
            cur_slice = current_df[current_df[timestamp_col] == ts]

            # Nếu nhóm có quá ít sample thì bỏ qua
            if len(cur_slice) < 10:
                continue

            # So sánh với TOÀN BỘ reference (không phải cùng timestamp)
            drift = get_one_column_drift(
                current_data=cur_slice,
                reference_data=reference_df,  # Toàn bộ reference
                column_name=column,
                options=DataDriftOptions(
                    all_features_stattest=self.metric.method,
                    all_features_threshold=self.metric.threshold,
                ),
                dataset_columns=DatasetColumns(
                    utility_columns=DatasetUtilityColumns(),
                    num_feature_names=[column] if column_type == ColumnType.Numerical else [],
                    cat_feature_names=[column] if column_type == ColumnType.Categorical else [],
                    text_feature_names=[column] if column_type == ColumnType.Text else [],
                    datetime_feature_names=[column] if column_type == ColumnType.Datetime else [],
                    target_names=None,
                ),
                column_type=column_type,
                agg_data=True,
            )
            drift_scores.append((ts, drift.drift_score))
            drift_detecteds.append((ts, drift.drift_detected))
            group_results.append((ts, drift))

        # Tổng kết theo từng thời điểm
        df_res = pd.DataFrame({
            "timestamp": [ts for ts, _ in drift_scores],
            "drift_score": [score for _, score in drift_scores],
            "drift_detected": [det for _, det in drift_detecteds],
        })
        print(f"    Drift results: {len(df_res)} time periods analyzed")

        # Tổng hợp: % drift_detected, score trung bình
        avg_score = df_res["drift_score"].mean() if not df_res.empty else np.nan
        drift_rate = df_res["drift_detected"].mean() if not df_res.empty else np.nan
        n_drifted = df_res["drift_detected"].sum() if not df_res.empty else 0
        
        print(f"    Average drift score: {avg_score:.4f}")
        print(f"    Drift detected in {n_drifted}/{len(df_res)} periods ({drift_rate*100:.1f}%)")

        # Trả về kết quả tổng hợp
        result_obj = self.result(avg_score)
        
        # Threshold và method
        threshold = self.metric.threshold if self.metric.threshold else 0.1
        method_name = self.metric.method if self.metric.method else "PSI"
        
        # Xác định drift status tổng thể (dựa trên avg_score và threshold)
        overall_drift_detected = avg_score > threshold if not np.isnan(avg_score) else False
        drift_status = "detected" if overall_drift_detected else "not detected"
        
        # Vẽ widgets
        widgets = []
        import plotly.graph_objects as go
        
        # 1. Counter widget - Thông tin tổng hợp
        summary_text = (
            f"Data drift {drift_status}. "
            f"Drift detection method: {method_name.upper()}. "
            f"Avg drift score: {avg_score:.3f}"
        )
        if not df_res.empty:
            summary_text += f" | Drifted periods: {n_drifted}/{len(df_res)} ({drift_rate*100:.1f}%)"
        
        widgets.append(
            counter(
                counters=[
                    CounterData(
                        summary_text,
                        f"Drift in column '{column}'",
                    )
                ],
                title="",
            )
        )
        
        # 2. Chart - Drift over time
        if not df_res.empty:
            fig = go.Figure()
            
            # Drift Score line
            fig.add_trace(go.Scatter(
                x=df_res["timestamp"],
                y=df_res["drift_score"],
                mode="lines+markers",
                name="Drift Score (PSI)",
                line=dict(color="blue", width=2),
                marker=dict(size=8)
            ))
            
            # Threshold line
            fig.add_hline(
                y=threshold, 
                line_dash="dash", 
                line_color="red",
                annotation_text=f"Threshold ({threshold})",
                annotation_position="top right"
            )
            
            # Highlight drifted points
            drifted = df_res[df_res["drift_detected"]]
            if not drifted.empty:
                fig.add_trace(go.Scatter(
                    x=drifted["timestamp"],
                    y=drifted["drift_score"],
                    mode="markers",
                    name="Drift Detected",
                    marker=dict(color="red", size=12, symbol="x")
                ))
            
            fig.update_layout(
                title=f"Score Drift over Time: '{column}'",
                xaxis_title="Timestamp",
                yaxis_title="Drift Score (PSI)",
                height=400,
                showlegend=True,
                legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
            )
            
            widgets.append(plotly_figure(title="", figure=fig))
        else:
            # Nếu không có data, hiển thị thông báo
            fig = go.Figure()
            fig.add_annotation(
                text="No valid timestamp periods found for drift analysis",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
            fig.update_layout(height=200)
            widgets.append(plotly_figure(title="", figure=fig))
        
        result_obj.widget = widgets
        return result_obj

    def display_name(self) -> str:
        if self.metric.timestamp_column:
            return f"Value drift for {self.metric.column} by {self.metric.timestamp_column}"
        else:
            return f"Value drift for {self.metric.column}"

    # Có thể giữ nguyên render chuẩn cho trường hợp không timestamp
    def _render(self, result: "ColumnDataDriftMetrics", options, color_options):
        if result.drift_detected:
            drift = "detected"
        else:
            drift = "not detected"

        drift_score = round(result.drift_score, 3)
        tabs = []
        if result.scatter is not None:
            if options.render_options.raw_data:
                if not isinstance(result.scatter, ScatterField):
                    raise ValueError("Result have incompatible type")
                scatter_fig = plot_scatter_for_data_drift(
                    curr_y=result.scatter.scatter[result.column_name].tolist(),
                    curr_x=result.scatter.scatter[result.scatter.x_name].tolist(),
                    y0=result.scatter.plot_shape["y0"],
                    y1=result.scatter.plot_shape["y1"],
                    y_name=result.column_name,
                    x_name=result.scatter.x_name,
                    color_options=color_options,
                )
            else:
                scatter_fig = plot_agg_line_data(
                    curr_data=result.scatter.scatter,
                    ref_data=None,
                    line=(result.scatter.plot_shape["y0"] + result.scatter.plot_shape["y1"]) / 2,
                    std=(result.scatter.plot_shape["y0"] - result.scatter.plot_shape["y1"]) / 2,
                    xaxis_name=result.scatter.x_name,
                    xaxis_name_ref=None,
                    yaxis_name=f"{result.column_name} (mean +/- std)",
                    color_options=color_options,
                    return_json=False,
                    line_name="reference (mean)",
                )
            tabs.append(TabData("DATA DRIFT", plotly_figure(title="", figure=scatter_fig)))

        if result.current.distribution is not None and result.reference.distribution is not None:
            distr_fig = plot_distr_with_perc_button(
                hist_curr=HistogramData.from_distribution(result.current.distribution),
                hist_ref=HistogramData.from_distribution(result.reference.distribution),
                xaxis_name="",
                yaxis_name="Count",
                yaxis_name_perc="Percent",
                same_color=False,
                color_options=color_options,
                subplots=False,
                to_json=False,
            )
            tabs.append(TabData("DATA DISTRIBUTION", plotly_figure(title="", figure=distr_fig)))

        if (
            result.current.characteristic_examples is not None
            and result.reference.characteristic_examples is not None
            and result.current.characteristic_words is not None
            and result.reference.characteristic_words is not None
        ):
            current_table_words = table_data(
                title="",
                column_names=["", ""],
                data=[[el, ""] for el in result.current.characteristic_words],
            )
            reference_table_words = table_data(
                title="",
                column_names=["", ""],
                data=[[el, ""] for el in result.reference.characteristic_words],
            )
            current_table_examples = table_data(
                title="",
                column_names=["", ""],
                data=[[el, ""] for el in result.current.characteristic_examples],
            )
            reference_table_examples = table_data(
                title="",
                column_names=["", ""],
                data=[[el, ""] for el in result.reference.characteristic_examples],
            )

            tabs = [
                TabData(title="current: characteristic words", widget=current_table_words),
                TabData(
                    title="reference: characteristic words",
                    widget=reference_table_words,
                ),
                TabData(
                    title="current: characteristic examples",
                    widget=current_table_examples,
                ),
                TabData(
                    title="reference: characteristic examples",
                    widget=reference_table_examples,
                ),
            ]
        render_result = [
            counter(
                counters=[
                    CounterData(
                        (
                            f"Data drift {drift}. "
                            f"Drift detection method: {result.stattest_name}. "
                            f"Drift score: {drift_score}"
                        ),
                        f"Drift in column '{result.column_name}'",
                    )
                ],
                title="",
            )
        ]
        if len(tabs) > 0:
            render_result.append(
                widget_tabs(
                    title="",
                    tabs=tabs,
                )
            )
        return render_result


class MyValueDrift_2(ColumnMetric, SingleValueMetric):
    """Detect data drift for a specific column by comparing distributions.

    Calculates drift score between current and reference datasets for a single column.
    Supports numerical, categorical, and text columns with various drift detection methods.
    Requires reference data to compute drift.


    See Also:
    * [Drift Methods Documentation](https://docs.evidentlyai.com/metrics/customize_data_drift) for available methods.
    """

    method: Optional[str] = None
    """Drift detection method (auto-selected if None)."""
    threshold: Optional[float] = None
    """Drift threshold (uses method default if None)."""
    timestamp_column: Optional[str] = None
    """Timestamp column (uses method default if None)."""



class MyValueDriftCalculation_2(SingleValueCalculation[MyValueDrift_2]):
    def calculate(self, context: "Context", 
    current_data: Dataset, 
    reference_data: Optional[Dataset],
    timestamp_column: Optional[str] = None
    ) -> SingleValue:
        column = self.metric.column
        column_type = current_data.column(column).type
        if reference_data is None:
            raise ValueError("Reference data is required for Value Drift")
        options = DataDriftOptions(
            all_features_stattest=self.metric.method,
            all_features_threshold=self.metric.threshold,
        )

        drift = get_one_column_drift(
            current_data=current_data.as_dataframe(),
            reference_data=reference_data.as_dataframe(),
            column_name=column,
            options=options,
            dataset_columns=DatasetColumns(
                utility_columns=DatasetUtilityColumns(date=self.metric.timestamp_column),
                num_feature_names=[column] if column_type == ColumnType.Numerical else [],
                cat_feature_names=[column] if column_type == ColumnType.Categorical else [],
                text_feature_names=[column] if column_type == ColumnType.Text else [],
                datetime_feature_names=[column] if column_type == ColumnType.Datetime else [],
                target_names=None,
            ),
            column_type=column_type,
            agg_data=True,
        )

        if self.metric.method is None:  # Only if it was auto-resolved
            self.resolve_parameter("method", drift.stattest_name)
        if self.metric.threshold is None:
            self.resolve_parameter("threshold", drift.stattest_threshold)
        result = self.result(drift.drift_score)
        result.widget = self._render(drift, Options(), ColorOptions())
        if self.metric.tests is None and context.configuration.include_tests:
            # todo: move to _default_tests
            result.set_tests(
                [
                    MetricTestResult(
                        id="drift",
                        name=f"Value Drift for column {self.metric.column}",
                        description=f"Drift score is {drift.drift_score:0.2f}. "
                        f"The drift detection method is {drift.stattest_name}. "
                        f"The drift threshold is {drift.stattest_threshold:0.2f}.",
                        status=TestStatus.FAIL if drift.drift_detected else TestStatus.SUCCESS,
                        metric_config=self.to_metric_config(),
                        test_config={},
                        # bound_test=ValueDriftBoundTest(
                        #     test=ValueDriftTest(),
                        #     metric_fingerprint=self.to_metric().metric_id,
                        # ),
                    )
                ]
            )
        return result

    def display_name(self) -> str:
        return f"Value drift for {self.metric.column}"

    def _render(self, result: ColumnDataDriftMetrics, options, color_options):
        if result.drift_detected:
            drift = "detected"

        else:
            drift = "not detected"

        drift_score = round(result.drift_score, 3)
        tabs = []
        if result.scatter is not None:
            if options.render_options.raw_data:
                if not isinstance(result.scatter, ScatterField):
                    raise ValueError("Result have incompatible type")
                scatter_fig = plot_scatter_for_data_drift(
                    curr_y=result.scatter.scatter[result.column_name].tolist(),
                    curr_x=result.scatter.scatter[result.scatter.x_name].tolist(),
                    y0=result.scatter.plot_shape["y0"],
                    y1=result.scatter.plot_shape["y1"],
                    y_name=result.column_name,
                    x_name=result.scatter.x_name,
                    color_options=color_options,
                )
            else:
                scatter_fig = plot_agg_line_data(
                    curr_data=result.scatter.scatter,
                    ref_data=None,
                    line=(result.scatter.plot_shape["y0"] + result.scatter.plot_shape["y1"]) / 2,
                    std=(result.scatter.plot_shape["y0"] - result.scatter.plot_shape["y1"]) / 2,
                    xaxis_name=result.scatter.x_name,
                    xaxis_name_ref=None,
                    yaxis_name=f"{result.column_name} (mean +/- std)",
                    color_options=color_options,
                    return_json=False,
                    line_name="reference (mean)",
                )
            tabs.append(TabData("DATA DRIFT", plotly_figure(title="", figure=scatter_fig)))

        if result.current.distribution is not None and result.reference.distribution is not None:
            distr_fig = plot_distr_with_perc_button(
                hist_curr=HistogramData.from_distribution(result.current.distribution),
                hist_ref=HistogramData.from_distribution(result.reference.distribution),
                xaxis_name="",
                yaxis_name="Count",
                yaxis_name_perc="Percent",
                same_color=False,
                color_options=color_options,
                subplots=False,
                to_json=False,
            )
            tabs.append(TabData("DATA DISTRIBUTION", plotly_figure(title="", figure=distr_fig)))

        if (
            result.current.characteristic_examples is not None
            and result.reference.characteristic_examples is not None
            and result.current.characteristic_words is not None
            and result.reference.characteristic_words is not None
        ):
            current_table_words = table_data(
                title="",
                column_names=["", ""],
                data=[[el, ""] for el in result.current.characteristic_words],
            )
            reference_table_words = table_data(
                title="",
                column_names=["", ""],
                data=[[el, ""] for el in result.reference.characteristic_words],
            )
            current_table_examples = table_data(
                title="",
                column_names=["", ""],
                data=[[el, ""] for el in result.current.characteristic_examples],
            )
            reference_table_examples = table_data(
                title="",
                column_names=["", ""],
                data=[[el, ""] for el in result.reference.characteristic_examples],
            )

            tabs = [
                TabData(title="current: characteristic words", widget=current_table_words),
                TabData(
                    title="reference: characteristic words",
                    widget=reference_table_words,
                ),
                TabData(
                    title="current: characteristic examples",
                    widget=current_table_examples,
                ),
                TabData(
                    title="reference: characteristic examples",
                    widget=reference_table_examples,
                ),
            ]
        render_result = [
            counter(
                counters=[
                    CounterData(
                        (
                            f"Data drift {drift}. "
                            f"Drift detection method: {result.stattest_name}. "
                            f"Drift score: {drift_score}"
                        ),
                        f"Drift in column '{result.column_name}'",
                    )
                ],
                title="",
            )
        ]
        if len(tabs) > 0:
            render_result.append(
                widget_tabs(
                    title="",
                    tabs=tabs,
                )
            )
        return render_result