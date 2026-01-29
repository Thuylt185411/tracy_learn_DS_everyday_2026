from sklearn.metrics import roc_auc_score
import scorecardpy as sc


from evidently import Dataset
import pandas as pd
import numpy as np
from evidently import Dataset
from evidently.core.report import Context
from evidently.core.metric_types import SingleValue
from evidently.core.metric_types import SingleValueMetric
from evidently.core.metric_types import SingleValueCalculation
from evidently.legacy.renderers.html_widgets import plotly_figure
import plotly.graph_objects as go

from typing import List, Optional

class IVSummaryMetric(SingleValueMetric):
    target_column: str
    numeric_features: List[str]
    categorical_features: List[str]
    top_n: int = 30
    add_reference_plot: bool = True  


def _prepare_data_for_iv(df: pd.DataFrame, num_cols: List[str], cat_cols: List[str]) -> pd.DataFrame:
    """
    Chuẩn bị dữ liệu cho tính IV:
    - Điền NA cho numerical bằng median
    - Tạo cột _isna flag cho numerical columns có NA
    """
    df = df.copy()
    df.columns = df.columns.str.strip()
    
    for col in num_cols:
        if col in df.columns:
            if df[col].isna().any():
                df[f"{col}_isna"] = df[col].isna().astype(int)
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
    
    for col in cat_cols:
        if col in df.columns:
            df[col] = df[col].fillna("MISSING").astype(str)
    
    return df


class IVSummaryMetricImplementation(SingleValueCalculation[IVSummaryMetric]):
    def calculate(
        self, 
        context: Context, 
        current_data: Dataset, 
        reference_data: Optional[Dataset],
    ) -> SingleValue:
        tgt = self.metric.target_column.strip()
        num = self.metric.numeric_features
        cat = self.metric.categorical_features
        add_reference_plot = self.metric.add_reference_plot  # Lấy từ Metric class

        cur = current_data.as_dataframe().drop(
            columns=["CUSTOMER_CODE", "DATE_PARTITION", "DISBURSE_DATE_WID"], 
            errors="ignore")

        # Chuẩn bị dữ liệu current
        cur_prep = _prepare_data_for_iv(cur, num, cat)

        # Chuẩn bị dữ liệu reference nếu cần
        ref_prep = None
        if reference_data is not None and add_reference_plot:
            ref = reference_data.as_dataframe().drop(
                columns=["CUSTOMER_CODE", "DATE_PARTITION", "DISBURSE_DATE_WID"], 
                errors="ignore")
            ref_prep = _prepare_data_for_iv(ref, num, cat)

        # Lấy danh sách features để tính IV
        feats = [c for c in (num + [f"{c}_isna" for c in num] + cat) if c in cur_prep.columns and c != tgt]

        # Tính IV current
        iv_cur = sc.iv(cur_prep, y=tgt, x=feats)
        if "iv" not in iv_cur.columns and "info_value" in iv_cur.columns:
            iv_cur = iv_cur.rename(columns={"info_value": "iv"})
        iv_cur = iv_cur.rename(columns={"variable": "feature"})[["feature", "iv"]].sort_values("iv", ascending=False).reset_index(drop=True)

        mean_iv_cur = float(iv_cur["iv"].mean()) if len(iv_cur) else np.nan
        pct_iv_low_cur = float((iv_cur["iv"] < 0.02).mean()) if len(iv_cur) else np.nan

        mean_iv_ref = np.nan
        pct_iv_low_ref = np.nan
        iv_ref = None

        # Tính IV reference nếu cần
        if reference_data is not None and add_reference_plot and ref_prep is not None:
            feats_ref = [c for c in feats if c in ref_prep.columns]
            iv_ref = sc.iv(ref_prep, y=tgt, x=feats_ref)
            if "iv" not in iv_ref.columns and "info_value" in iv_ref.columns:
                iv_ref = iv_ref.rename(columns={"info_value": "iv"})
            iv_ref = iv_ref.rename(columns={"variable": "feature"})[["feature", "iv"]].sort_values("iv", ascending=False).reset_index(drop=True)
            mean_iv_ref = float(iv_ref["iv"].mean()) if len(iv_ref) else np.nan
            pct_iv_low_ref = float((iv_ref["iv"] < 0.02).mean()) if len(iv_ref) else np.nan

        # Visualization
        fig = go.Figure()
        
        # Vẽ reference nếu có (full data, không lấy top)
        if add_reference_plot and reference_data is not None and iv_ref is not None and len(iv_ref):
            fig.add_trace(go.Bar(
                x=iv_ref["feature"],
                y=iv_ref["iv"],
                name="Reference IV",
                marker_color="orange",
                opacity=0.5,
            ))

        # Luôn vẽ current (full data, không lấy top)
        fig.add_trace(go.Bar(
            x=iv_cur["feature"],
            y=iv_cur["iv"],
            name="Current IV",
            marker_color="blue",
            opacity=0.7 if (add_reference_plot and reference_data is not None and iv_ref is not None) else 1.0,
        ))

        # Title với thông tin thống kê
        if add_reference_plot and reference_data is not None and iv_ref is not None:
            mega_title = (
                f'IV Summary<br>'
                f'Current: mean_iv={mean_iv_cur:.4f} | pct_iv_low={pct_iv_low_cur:.2%} '
                f'<br>Reference: mean_iv={mean_iv_ref:.4f} | pct_iv_low={pct_iv_low_ref:.2%}'
            )
        else:
            mega_title = (
                f'IV Summary<br>'
                f'mean_iv={mean_iv_cur:.4f} | pct_iv_low={pct_iv_low_cur:.2%}'
            )

        fig.update_layout(
            title=mega_title,
            xaxis_title="Feature",
            yaxis_title="IV",
            height=420,
            margin=dict(l=40, r=20, t=60, b=130),
            barmode="group" if (add_reference_plot and reference_data is not None and iv_ref is not None) else "relative",
            legend_title="Data",
        )

        # Ghi chú ref/cur nổi bật trên chart nếu có cả 2
        if add_reference_plot and reference_data is not None and iv_ref is not None:
            fig.add_annotation(
                xref="paper", yref="paper", x=0, y=1.1, showarrow=False,
                text="<b>Current = blue, Reference = orange</b>", font=dict(size=13, color="black")
            )

        result = self.result(value=mean_iv_cur)
        result.widget = [plotly_figure(title="IV Summary (Current/Reference)", figure=fig)]
        
        # Return với reference result nếu có
        if reference_data is not None and iv_ref is not None:
            result_ref = self.result(value=mean_iv_ref)
            return result, result_ref
        
        return result

    def display_name(self) -> str:
        return "IV Summary"
