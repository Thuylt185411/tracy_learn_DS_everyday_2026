import scorecardpy as sc


from evidently import Dataset
from evidently.core.report import Context
from evidently.core.metric_types import SingleValue
from evidently.core.metric_types import SingleValueMetric
from evidently.core.metric_types import SingleValueCalculation
import plotly.graph_objects as go
from evidently.legacy.renderers.html_widgets import plotly_figure

from typing import List, Optional, Dict
import pandas as pd

# Thêm logic LABEL theo rule như cell ở đầu
def add_label_col(df: pd.DataFrame, target_col: str):
    # Gọi trực tiếp logic phân loại LABEL good/bad như ở cell đầu file
    df = df.copy()
    df.columns = df.columns.str.strip()
    if target_col not in df.columns:
        raise KeyError(f"Target column '{target_col}' not found. Available columns: {list(df.columns)[:30]}")
    # Lấy lại logic mapping
    df['LABEL'] = ['good' if x == 1 else 'bad' for x in df[target_col]]
    return df

class BasicWOEMetric(SingleValueMetric):
    target_column: str           # y: 0/1 (bad=1)
    features: List[str]          # list feature columns
    top_n: int = 50              # show top N features (by order), for readability

class BasicWOEMetricImplementation(SingleValueCalculation[BasicWOEMetric]):
    def _preprocess_df(self, df: pd.DataFrame, target: str, features: List[str]) -> tuple:
        # Strip all column names and drop unwanted columns
        df = df.copy()
        df.columns = df.columns.str.strip()
        df = df.drop(columns=["CUSTOMER_CODE", "DATE_PARTITION", "DISBURSE_DATE_WID"], errors="ignore")

        # Ensure target exists
        if target not in df.columns:
            raise KeyError(f"Target column '{target}' not found after column cleanup. Available columns: {list(df.columns)[:30]}")

        # Only keep valid features and target
        selected_features = [c for c in features if c in df.columns and c != target]
        df = add_label_col(df, target)
        df = df[selected_features + ["LABEL"]]

        return df, selected_features

    def _calc_woe(self, df, features, target, breaks_list=None):
        """
        Tính WOE bins cho dataframe.
        Nếu breaks_list được cung cấp, sẽ sử dụng breaks đó thay vì tự động tính.
        """
        # Process DataFrame before calculation
        df_proc, used_features = self._preprocess_df(df, target, features)
        work = df_proc
        
        if breaks_list is not None:
            # Áp dụng breaks đã có (từ reference) cho current
            bins = sc.woebin(work, y='LABEL', x=used_features, breaks_list=breaks_list)
        else:
            # Tự động tính bins
            bins = sc.woebin(work, y='LABEL', x=used_features)
        return bins, used_features

    def _extract_breaks_from_bins(self, bins: Dict) -> Dict:
        """
        Trích xuất breaks từ bins dict để tái sử dụng cho dataset khác.
        """
        breaks_list = {}
        for feat, bin_df in bins.items():
            if bin_df is not None and len(bin_df) > 0 and 'breaks' in bin_df.columns:
                # Lấy breaks từ bin_df, bỏ qua 'missing' và 'special'
                breaks = bin_df['breaks'].dropna().tolist()
                breaks = [b for b in breaks if b not in ['missing', 'special', 'Missing', 'Special']]
                if breaks:
                    breaks_list[feat] = breaks
        return breaks_list

    def calculate(
        self,
        context: Context,
        current_data: Dataset,
        reference_data: Optional[Dataset],
    ) -> SingleValue:
        features = [c.strip() for c in self.metric.features]
        target_col = self.metric.target_column

        # ---- reference_data (tính bins trước để lấy breaks) ----
        bins_ref = None
        show_feats_ref = None
        breaks_list = None
        
        if reference_data is not None:
            df_ref = reference_data.as_dataframe()
            bins_ref, use_feats_ref = self._calc_woe(df_ref, features, target_col)
            show_feats_ref = use_feats_ref[:self.metric.top_n]
            # Trích xuất breaks từ reference để áp dụng cho current
            breaks_list = self._extract_breaks_from_bins(bins_ref)

        # ---- current_data (dùng cùng breaks với reference nếu có) ----
        df_cur = current_data.as_dataframe()
        bins_cur, use_feats_cur = self._calc_woe(df_cur, features, target_col, breaks_list=breaks_list)
        show_feats_cur = use_feats_cur[:self.metric.top_n]

        widgets = []
        from plotly.subplots import make_subplots
        top_feats = show_feats_cur[:]

        for f in top_feats:
            bin_cur = bins_cur.get(f)
            bin_ref = bins_ref.get(f) if (bins_ref is not None and f in bins_ref) else None

            if (bin_cur is None or len(bin_cur) == 0) and (bin_ref is None or len(bin_ref) == 0):
                continue

            def find_bad_col(df_bin):
                if df_bin is None:
                    return None
                for c in ["badprob", "bad_rate", "badrate"]:
                    if c in df_bin.columns:
                        return c
                return None

            bad_col_cur = find_bad_col(bin_cur)
            bad_col_ref = find_bad_col(bin_ref)

            x_cur = bin_cur["bin"].astype(str) if (bin_cur is not None and "bin" in bin_cur.columns) else None
            x_ref = bin_ref["bin"].astype(str) if (bin_ref is not None and "bin" in bin_ref.columns) else None

            # Sanity check: dùng bin từ current nếu bin_ref bị thiếu hoặc khác
            x_vals = x_cur if x_cur is not None else x_ref
            subplot_titles = ["Current", "Reference"]

            fig = make_subplots(
                rows=1, cols=2, shared_yaxes=False,
                subplot_titles=subplot_titles
            )

            if bin_cur is not None and len(bin_cur):
                woe_cur = pd.to_numeric(bin_cur["woe"], errors="coerce") if "woe" in bin_cur.columns else None
                badrate_cur = pd.to_numeric(bin_cur[bad_col_cur], errors="coerce") if bad_col_cur else None
                fig.add_trace(
                    go.Bar(x=x_cur, y=woe_cur, name="WOE", yaxis="y1", marker_color="#1f77b4"),
                    row=1, col=1,
                )
                fig.add_trace(
                    go.Scatter(x=x_cur, y=badrate_cur, name="Bad rate", mode="lines+markers",
                               marker_color="#ff7f0e", yaxis="y2"),
                    row=1, col=1,
                )
            if bin_ref is not None and len(bin_ref):
                woe_ref = pd.to_numeric(bin_ref["woe"], errors="coerce") if "woe" in bin_ref.columns else None
                badrate_ref = pd.to_numeric(bin_ref[bad_col_ref], errors="coerce") if bad_col_ref else None
                fig.add_trace(
                    go.Bar(x=x_ref, y=woe_ref, name="WOE", yaxis="y1", marker_color="#1f77b4", showlegend=False),
                    row=1, col=2,
                )
                fig.add_trace(
                    go.Scatter(x=x_ref, y=badrate_ref, name="Bad rate", mode="lines+markers",
                               marker_color="#ff7f0e", yaxis="y2", showlegend=False),
                    row=1, col=2,
                )

            fig.update_layout(
                title=f"WOE & Bad Rate by Bin — {f}",
                height=420,
                margin=dict(l=40, r=40, t=60, b=60),
            )
            fig.update_xaxes(title_text="Bin", row=1, col=1)
            fig.update_xaxes(title_text="Bin", row=1, col=2)
            fig.update_yaxes(title_text="WOE", row=1, col=1, side="left")
            fig.update_yaxes(title_text="WOE", row=1, col=2, side="left")

            widgets.append(plotly_figure(title=f"WOE: {f} (Current / Reference)", figure=fig))

        result_ref = None
        if reference_data is not None and bins_ref is not None:
            result_ref = self.result(value=1)

        result = self.result(value=1)
        result.widget = widgets

        if reference_data is not None and result_ref is not None:
            return result, result_ref
        else:
            return result

    def display_name(self) -> str:
        return "Basic WOE per feature"