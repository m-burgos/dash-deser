import os
import json
import base64
from functools import lru_cache

import pandas as pd
import plotly.graph_objects as go

# Configuration
DATA_DIR = os.environ.get("DROPOUT_DATA_DIR", "data")
SEMESTERS = list(range(1, 8))  # S1 .. S7

# CSV column -> display label. Order = strict order used in the boxplot figure.
METRIC_COLUMNS = {
    "Accuracy": "Accuracy",
    "Precision": "Precision",
    "Recall": "Recall",
    "F1": "F1",
    "ROC-AUC": "AUC",
    "Brier": "Brier",
}
METRIC_ORDER = list(METRIC_COLUMNS.keys())

DIAGNOSTIC_FIGS = {
    "calibration_curve": "",
    "confusion_matrix": "",
    "pr_curve": "",
    "roc_curve": "",
}

CLASS_LABELS = {"0": "No dropout (0)", "1": "Dropout (1)"}

# Colours
DIST_COLORS = {"0": "#2D9CDB", "1": "#F2994A"}     # blue (class 0) / orange (class 1)
BOX_PALETTE = ["#4C78A8", "#54A24B", "#B279A2", "#F58518", "#72B7B2", "#E45756"]
MODELS = ['AdaBoost', 'Balanced Random Forest', 'Calibrated Random Forest', 'CatBoost', 'Decision Tree', 'Dummy (prior)', 'Linear SVM', 
          'Logistic Regression', 'Naive Bayes', 'Nearest Neighbors', 'Neural Net', 'QDA', 'Random Forest', 'RBF SVM', 'XGBoost']


# Path builders
def semester_dir(n: int) -> str:
    return os.path.join(DATA_DIR, f"S{n}")


def metrics_csv_path(n: int) -> str:
    return os.path.join(semester_dir(n), "metrics", "metrics_per_fold.csv")


def calibration_overlay_path(n: int) -> str:
    return os.path.join(semester_dir(n), "calibration", "calibration_overlay.png")


def diagnostic_fig_path(n: int, model: str, stem: str) -> str:
    return os.path.join(semester_dir(n), "diagnostics", model, f"{stem}.png")


def config_path(n: int) -> str:
    return os.path.join(semester_dir(n), "config.json")


# Loaders (cached) 
@lru_cache(maxsize=None)
def load_semester_config(n):
    with open(config_path(n), "r", encoding="utf-8") as f:
        return json.load(f)

@lru_cache(maxsize=None)
def load_metrics(n: int) -> pd.DataFrame:
    """Per-fold metrics for semester n. Cached; treat as read-only."""
    return pd.read_csv(metrics_csv_path(n))

@lru_cache(maxsize=None)
def get_models(n: int) -> tuple:
    """Model names for semester n, alphabetical (case-insensitive)."""
    try:
        models = list(load_semester_config(n)["classifiers"])
    except Exception:
        models = []
    if not models:
        models = load_metrics(n)["Modelo"].unique().tolist()
    return tuple(sorted(models, key=lambda s: str(s).lower()))

@lru_cache(maxsize=None)
def encode_image(path: str):
    """Base64 data URI for a PNG, or None if missing."""
    if not path or not os.path.exists(path):
        return None
    with open(path, "rb") as fh:
        data = base64.b64encode(fh.read()).decode("ascii")
    return f"data:image/png;base64,{data}"


# Figure builders  
def _fmt_pct(p: float) -> str:
    """Two-decimal percent with comma decimal separator (e.g. 69,03%)."""
    return f"{p:.2f}".replace(".", ",") + "%"


def build_distribution_figure(n: int) -> go.Figure:
    """Single horizontal stacked 100% bar: class 0 (blue) + class 1 (orange)."""
    cfg = load_semester_config(n)
    dist = {str(k): float(v) for k, v in cfg["target_distribution"].items()}
    total = sum(dist.values())
    pct = {k: (v * 100 if total <= 1.5 else v) for k, v in dist.items()}

    fig = go.Figure()
    for k in sorted(pct.keys()):  # "0" then "1"
        p = pct[k]
        fig.add_trace(go.Bar(
            x=[p], y=["target"], orientation="h",
            name=CLASS_LABELS.get(k, k),
            marker_color=DIST_COLORS.get(k, "#999999"),
            text=[_fmt_pct(p)], textposition="inside", insidetextanchor="middle",
            textfont=dict(color="white", size=15),
            hovertemplate=f"{CLASS_LABELS.get(k, k)}: {_fmt_pct(p)}<extra></extra>",
        ))

    fig.update_layout(
        barmode="stack",
        height=80,
        margin=dict(l=6, r=6, t=6, b=6),
        showlegend=False,
        xaxis=dict(visible=False, range=[0, 100]),
        yaxis=dict(visible=False),
        plot_bgcolor="white", paper_bgcolor="white",
        bargap=0,
    )
    return fig


def empty_figure(message: str = "No data") -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=message, showarrow=False,
                       font=dict(size=14, color="#999"))
    fig.update_layout(height=460, xaxis=dict(visible=False), yaxis=dict(visible=False),
                      margin=dict(l=20, r=20, t=20, b=20))
    return fig


def build_boxplots_figure(n: int, model: str | None) -> go.Figure:
    """6 vertical boxplots for a SINGLE model, strict metric order, y fixed 0-1.

    Each box shows the metric across the 5x5 = 25 CV folds; fold values are
    overlaid as points so it doubles as a scatter.
    """
    if model is None:
        return empty_figure("Select a model")

    df = load_metrics(n)
    sub = df[df["Modelo"] == model]
    if sub.empty:
        return empty_figure(f"No rows for {model} in S{n}")

    fig = go.Figure()
    for metric, color in zip(METRIC_ORDER, BOX_PALETTE):
        if metric not in sub.columns:
            continue
        fig.add_trace(go.Box(
            y=sub[metric],
            name=METRIC_COLUMNS[metric],
            boxpoints="all", jitter=0.4, pointpos=0,
            marker=dict(size=4, color=color, opacity=0.55),
            line=dict(color=color),
            fillcolor=color,
            opacity=0.55,
            showlegend=False,
        ))

    fig.update_layout(
        #title=f"S{n} - {model}: metric distributions (5x5 CV)",
        height=280,
        margin=dict(l=45, r=20, t=55, b=40),
        yaxis=dict(range=[0, 1], title="Value", gridcolor="#eee"),
        xaxis=dict(title="", categoryorder="array",
                   categoryarray=list(METRIC_COLUMNS.values())),
        plot_bgcolor="white", paper_bgcolor="white",
    )
    return fig