import yaml
import pandas as pd

DROP_COLS = ["CUSTOMER_CODE", "DATE_PARTITION", "DISBURSE_DATE_WID"]


def load_config(config_path: str):
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)
    

def replace_html_content(format_html_path, new_content):
    """Replace content in HTML with new content."""
    with open(format_html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    new_html_content = html_content.replace("{add_html_content}", new_content)
    return new_html_content

def get_html_from_evidently(ev_report):
    """Return HTML content as string from Evidently report object."""
    import tempfile
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
    ev_report.save_html(tmp.name)
    with open(tmp.name, "r", encoding="utf-8") as f:
        html = f.read()
    return html

def get_from_file(path):
    print(f"path: {path}")
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
    # Remove <!DOCTYPE html>
    html = html.replace("<!DOCTYPE html>", "")
    # Remove <html> and </html> tags (case-insensitive, possibly with attributes)
    import re
    html = re.sub(r"<html[^>]*>", "", html, flags=re.IGNORECASE)
    html = re.sub(r"</html>", "", html, flags=re.IGNORECASE)
    return html

def add_label_cols(df: pd.DataFrame, label_col: str) -> pd.DataFrame:
    df = df.copy()
    df[label_col] = pd.to_numeric(df[label_col], errors="coerce")
    df = df.dropna(subset=[label_col])
    df = df[df[label_col].isin([0, 1])].copy()
    df["Y_BAD"] = 1 - df[label_col]  # bad=1 khi không quay lại
    return df

def preprocess_for_woe_iv(
    df: pd.DataFrame,
    label_col: str,
    num_cols: list[str],
    cat_cols: list[str],
    add_isna_flags: bool = True,
) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.str.strip()
    df = df.drop(columns=DROP_COLS, errors="ignore")

    # numeric: to_numeric, giữ NaN
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
            if add_isna_flags:
                df[f"{c}_isna"] = df[c].isna().astype(int)

    # categorical: fill NaN -> "MISSING"
    for c in cat_cols:
        if c in df.columns:
            df[c] = df[c].astype("object").fillna("MISSING")

    df = add_label_cols(df, label_col)
    return df
