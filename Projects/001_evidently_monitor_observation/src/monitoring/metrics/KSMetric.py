from evidently import Dataset
from evidently.core.report import Context
from evidently.core.metric_types import SingleValue
from evidently.core.metric_types import SingleValueMetric
from evidently.core.metric_types import SingleValueCalculation
from evidently.core.metric_types import BoundTest
from evidently.tests import Reference, eq
from typing import List, Optional, Tuple

import plotly.graph_objects as go
from evidently.legacy.renderers.html_widgets import plotly_figure

import numpy as np


class KSMetric(SingleValueMetric):
    true_column: str   # y_true (bad=1 good=0)
    pred_column: str   # y_pred (PD/proba)

    def _default_tests(self) -> List[BoundTest]:
        # ví dụ: KS không nên = 0
        return [eq(0.0).bind_single(self.get_fingerprint())]

    def _default_tests_with_reference(self) -> List[BoundTest]:
        # ví dụ: KS current không lệch quá 5% so với reference
        return [eq(Reference(relative=0.05)).bind_single(self.get_fingerprint())]


def _downsample_for_plot_percent(x: np.ndarray, y: np.ndarray, max_points: int = 2000) -> Tuple[np.ndarray, np.ndarray]:
    """
    Downsample arrays for plotting to reduce HTML size.
    X được quy đổi thành % population (0..100).
    KS value is still calculated from FULL data - this only affects visualization.
    """
    n = len(x)
    x_percent = x / max(1, n-1) * 100
    if n <= max_points:
        return x_percent, y
    indices = np.linspace(0, n - 1, max_points, dtype=int)
    return x_percent[indices], y[indices]


def _ks_series(y_true: np.ndarray, 
                y_pred: np.ndarray
            ) -> Tuple[float, int, np.ndarray, np.ndarray, np.ndarray]:
    """
    Return:
      ks_value, ks_index, p_sorted, cum_bad, cum_good
    Convention: bad=1, good=0; sort by y_pred desc (risk high first)
    
    NOTE: KS value is calculated from FULL data for accuracy.
    """
    y_true = np.asarray(y_true).astype(int)
    y_pred = np.asarray(y_pred).astype(float)

    order = np.argsort(-y_pred)
    y_sorted = y_true[order]
    p_sorted = y_pred[order]

    total_bad = (y_sorted == 1).sum()
    total_good = (y_sorted == 0).sum()

    if total_bad == 0 or total_good == 0:
        return np.nan, 0, p_sorted, np.zeros_like(p_sorted, dtype=float), np.zeros_like(p_sorted, dtype=float)

    cum_bad = np.cumsum(y_sorted == 1) / total_bad
    cum_good = np.cumsum(y_sorted == 0) / total_good

    ks_arr = np.abs(cum_bad - cum_good)
    ks_index = int(np.argmax(ks_arr))
    ks_value = float(ks_arr[ks_index])
    return ks_value, ks_index, p_sorted, cum_bad, cum_good


class KSMetricImplementation(SingleValueCalculation[KSMetric]):
    # Max points for visualization (reduces HTML from ~60MB to ~1MB)
    MAX_PLOT_POINTS = 2000

    def calculate(
        self,
        context: Context,
        current_data: Dataset,
        reference_data: Optional[Dataset],
    ) -> SingleValue:
        # ---- current ----
        y_true = np.array(current_data.column(self.metric.true_column).data)
        y_pred = np.array(current_data.column(self.metric.pred_column).data)

        # KS value calculated from FULL data (accurate!)
        ks_value, ks_index, p_sorted, cum_bad, cum_good = _ks_series(y_true, y_pred)

        # ---- plotly figure (KS curve) ----
        fig = go.Figure()
        x_full = np.arange(len(cum_bad))
        # Chuyển sang phần trăm population
        x_percent, cum_bad_ds = _downsample_for_plot_percent(x_full, cum_bad, self.MAX_PLOT_POINTS)
        _, cum_good_ds = _downsample_for_plot_percent(x_full, cum_good, self.MAX_PLOT_POINTS)

        # CDF curves - Current data (downsampled for plot)
        fig.add_trace(go.Scatter(
            x=x_percent,
            y=cum_bad_ds,
            mode="lines",
            name=f"Current Cum Bad (KS={ks_value:.3f})",
            line=dict(color="blue")
        ))
        fig.add_trace(go.Scatter(
            x=x_percent,
            y=cum_good_ds,
            mode="lines",
            name="Current Cum Good",
            line=dict(color="green")
        ))

        # KS vertical line (using original accurate ks_index)
        if not np.isnan(ks_value) and len(x_full) > 0:
            # X location của ks_index theo % population
            x_ks_percent = ks_index / max(1, len(x_full)-1) * 100
            fig.add_shape(
                type="line",
                x0=x_ks_percent, x1=x_ks_percent,
                y0=float(cum_good[ks_index]), y1=float(cum_bad[ks_index]),
                line=dict(dash="dash", color="red")
            )
            fig.add_annotation(
                x=x_ks_percent,
                y=float(cum_bad[ks_index]),
                text=f"KS={ks_value:.3f}<br>p≈{float(p_sorted[ks_index]):.4f}",
                showarrow=True,
                arrowhead=2
            )

        # Reference data processing
        result_ref = None
        if reference_data is not None:
            ref_y_true = np.array(reference_data.column(self.metric.true_column).data)
            ref_y_pred = np.array(reference_data.column(self.metric.pred_column).data)
            
            # KS value from FULL reference data (accurate!)
            ref_ks, _, _, ref_cum_bad, ref_cum_good = _ks_series(ref_y_true, ref_y_pred)
            
            result_ref = self.result(value=ref_ks)

            # Downsample reference for plotting
            ref_x_full = np.arange(len(ref_cum_bad))
            ref_x_percent, ref_cum_bad_ds = _downsample_for_plot_percent(ref_x_full, ref_cum_bad, self.MAX_PLOT_POINTS)
            _, ref_cum_good_ds = _downsample_for_plot_percent(ref_x_full, ref_cum_good, self.MAX_PLOT_POINTS)

            # Overlay reference curves (downsampled)
            fig.add_trace(go.Scatter(
                x=ref_x_percent,
                y=ref_cum_bad_ds,
                mode="lines",
                name=f"REF Cum Bad (KS={ref_ks:.3f})",
                line=dict(dash="dot", color="lightblue")
            ))
            fig.add_trace(go.Scatter(
                x=ref_x_percent,
                y=ref_cum_good_ds,
                mode="lines",
                name="REF Cum Good",
                line=dict(dash="dot", color="lightgreen")
            ))

        fig.update_layout(
            title=f"KS Curve: {self.metric.true_column} vs {self.metric.pred_column}",
            xaxis_title="Population percentile (%) (sorted by predicted risk desc)",
            yaxis_title="Cumulative rate",
            legend_title="",
            template="plotly_white"
        )

        # Tạo result và gắn widget
        result = self.result(value=ks_value)
        result.widget = [plotly_figure(title=self.display_name(), figure=fig)]

        # Return đúng format: tuple nếu có reference, single nếu không
        if reference_data is not None:
            return result, result_ref
        else:
            return result

    def display_name(self) -> str:
        return f"KS metric for {self.metric.true_column} vs {self.metric.pred_column}"

