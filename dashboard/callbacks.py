"""Dashboard interactivity: data -> KPIs + figures, wired to Dash callbacks.

All the real work lives in pure functions (`compute_kpis`, `build_price_figure`,
`build_zscore_figure`, `render`) that take data and return plain objects. The
Dash callback is a thin wrapper that calls `render`, so the logic is unit-testable
without a running server or a browser.
"""

from __future__ import annotations

import logging

import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, html

from analytics.forecasting import PriceForecaster
from config import COMMODITIES, Commodity
from dashboard.layout import COLORS
from storage.repository import CommodityRepository

logger = logging.getLogger(__name__)

_PLOT_BG = "rgba(0, 0, 0, 0)"
_FORECAST_STEPS = 8


def _empty_figure(message: str) -> go.Figure:
    """A blank, on-theme figure with a centered message."""
    fig = go.Figure()
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=_PLOT_BG,
        plot_bgcolor=_PLOT_BG,
        height=360,
        font={"family": "Plus Jakarta Sans, Inter, sans-serif"},
        annotations=[
            {
                "text": message,
                "xref": "paper",
                "yref": "paper",
                "x": 0.5,
                "y": 0.5,
                "showarrow": False,
                "font": {"color": COLORS["muted"], "size": 15},
            }
        ],
    )
    return fig


def compute_kpis(df: pd.DataFrame, commodity: Commodity) -> dict:
    """Compute the three headline KPIs from the latest row.

    Returns a dict with formatted strings and the raw WoW sign (for coloring).
    """
    if df.empty:
        return {"current": "—", "wow": "—", "avg": "—", "wow_sign": 0}

    last = df.iloc[-1]
    current = f"${last['value']:,.2f}"
    avg = (
        f"${last['rolling_avg_4w']:,.2f}"
        if pd.notna(last.get("rolling_avg_4w"))
        else "—"
    )
    wow_val = last.get("pct_change")
    if pd.isna(wow_val):
        wow, wow_sign = "—", 0
    else:
        wow, wow_sign = f"{wow_val:+.2f}%", (1 if wow_val >= 0 else -1)
    return {"current": current, "wow": wow, "avg": avg, "wow_sign": wow_sign}


def build_price_figure(
    history: pd.DataFrame, forecast: pd.DataFrame | None, commodity: Commodity
) -> go.Figure:
    """Price history line + forecast overlay with a 95% confidence band."""
    if history.empty:
        return _empty_figure("No market data recorded for this selection")

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=history["date"],
            y=history["value"],
            mode="lines",
            name="Spot Price",
            line={"color": COLORS["accent"], "width": 2.2},
        )
    )

    # Highlight flagged outliers, if present.
    if "is_outlier" in history.columns:
        is_out = history["is_outlier"].fillna(False).astype(bool)
        out = history[is_out]
        if not out.empty:
            fig.add_trace(
                go.Scatter(
                    x=out["date"],
                    y=out["value"],
                    mode="markers",
                    name="Anomaly (Hampel 3.5σ)",
                    marker={
                        "color": COLORS["down"],
                        "size": 8,
                        "symbol": "diamond",
                        "line": {"width": 1.5, "color": "#ffffff"},
                    },
                )
            )

    if forecast is not None and not forecast.empty:
        # Anchor the forecast to the last actual point for visual continuity.
        anchor_d, anchor_v = history["date"].iloc[-1], history["value"].iloc[-1]
        fdates = [anchor_d, *forecast["date"]]
        fmean = [anchor_v, *forecast["forecast"]]
        flo = [anchor_v, *forecast["lower"]]
        fhi = [anchor_v, *forecast["upper"]]

        # Confidence band (upper out, lower back, filled).
        fig.add_trace(
            go.Scatter(
                x=[*fdates, *fdates[::-1]],
                y=[*fhi, *flo[::-1]],
                fill="toself",
                fillcolor="rgba(0, 240, 255, 0.08)",
                line={"width": 0},
                name="95% Confidence Band",
                hoverinfo="skip",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=fdates,
                y=fmean,
                mode="lines",
                name="ARIMA(1,1,1) Forecast",
                line={"color": COLORS["up"], "width": 2.2, "dash": "dot"},
            )
        )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=_PLOT_BG,
        plot_bgcolor=_PLOT_BG,
        height=380,
        margin={"l": 55, "r": 25, "t": 48, "b": 40},
        title={
            "text": f"{commodity.label} — Price Trajectory & Horizon Forecast",
            "font": {"size": 15, "weight": 600, "color": COLORS["text"]},
        },
        font={"family": "Plus Jakarta Sans, Inter, sans-serif"},
        yaxis_title=commodity.unit,
        hovermode="x unified",
        hoverlabel={
            "bgcolor": "#0d1321",
            "bordercolor": "rgba(255,255,255,0.15)",
            "font": {"family": "Plus Jakarta Sans, sans-serif", "size": 12},
        },
        legend={"orientation": "h", "y": -0.18, "font": {"size": 12}},
    )
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(255, 255, 255, 0.05)",
        zeroline=False,
    )
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(255, 255, 255, 0.05)",
        zeroline=False,
    )
    return fig


def build_zscore_figure(df: pd.DataFrame, commodity: Commodity) -> go.Figure:
    """Z-score bar chart, color-coded by volatility magnitude."""
    if df.empty or "z_score" not in df.columns or df["z_score"].dropna().empty:
        return _empty_figure("No volatility metrics available for this selection")

    z = df["z_score"]

    def _color(v: float) -> str:
        if pd.isna(v):
            return COLORS["muted"]
        if abs(v) >= 2:
            return COLORS["down"]
        if abs(v) >= 1:
            return "#f59e0b"
        return COLORS["accent"]

    fig = go.Figure(
        go.Bar(
            x=df["date"],
            y=z,
            marker_color=[_color(v) for v in z],
            name="Z-score",
        )
    )
    for level, color in ((2, COLORS["down"]), (-2, COLORS["down"])):
        fig.add_hline(
            y=level,
            line_dash="dot",
            line_color="rgba(244, 63, 94, 0.4)",
            line_width=1.5,
        )
    fig.add_hline(y=0, line_color="rgba(255, 255, 255, 0.15)", line_width=1)

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=_PLOT_BG,
        plot_bgcolor=_PLOT_BG,
        height=280,
        margin={"l": 55, "r": 25, "t": 48, "b": 40},
        title={
            "text": f"{commodity.label} — Normalized Volatility Surface (Z-score vs 4-Week Moving Window)",
            "font": {"size": 14, "weight": 600, "color": COLORS["text"]},
        },
        font={"family": "Plus Jakarta Sans, Inter, sans-serif"},
        yaxis_title="z-score (σ)",
        hovermode="x unified",
        hoverlabel={
            "bgcolor": "#0d1321",
            "bordercolor": "rgba(255,255,255,0.15)",
            "font": {"family": "Plus Jakarta Sans, sans-serif", "size": 12},
        },
    )
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(255, 255, 255, 0.05)",
        zeroline=False,
    )
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(255, 255, 255, 0.05)",
        zeroline=False,
    )
    return fig


def _forecast_for(history: pd.DataFrame) -> pd.DataFrame | None:
    """Fit ARIMA and forecast, returning None if the series is unsuitable."""
    try:
        return PriceForecaster().fit(history).predict(steps=_FORECAST_STEPS)
    except Exception as exc:  # forecast is best-effort; never break the page
        logger.warning("Forecast skipped: %s", exc)
        return None


def render(
    repo: CommodityRepository,
    commodity_key: str,
    start_date: str | None,
    end_date: str | None,
):
    """Produce (price_fig, zscore_fig, kpi_current, kpi_wow, kpi_avg).

    This is the testable core of the callback — no Dash machinery required.
    """
    commodity = COMMODITIES[commodity_key]
    df = repo.get_processed(commodity.series_id, start_date, end_date)

    kpis = compute_kpis(df, commodity)
    forecast = _forecast_for(df) if not df.empty else None
    price_fig = build_price_figure(df, forecast, commodity)
    zscore_fig = build_zscore_figure(df, commodity)

    wow_color = {1: COLORS["up"], -1: COLORS["down"], 0: COLORS["text"]}[
        kpis["wow_sign"]
    ]
    wow_component = html.Span(
        kpis["wow"],
        style={"color": wow_color, "fontWeight": "700"},
    )

    if kpis["current"] != "—":
        current_component = html.Div(
            [
                html.Span(kpis["current"]),
                html.Span(
                    f" {commodity.unit}",
                    style={
                        "fontSize": "13px",
                        "color": COLORS["muted"],
                        "marginLeft": "6px",
                        "fontWeight": "500",
                    },
                ),
            ]
        )
    else:
        current_component = html.Span("—")

    if kpis["avg"] != "—":
        avg_component = html.Div(
            [
                html.Span(kpis["avg"]),
                html.Span(
                    f" {commodity.unit}",
                    style={
                        "fontSize": "13px",
                        "color": COLORS["muted"],
                        "marginLeft": "6px",
                        "fontWeight": "500",
                    },
                ),
            ]
        )
    else:
        avg_component = html.Span("—")

    return price_fig, zscore_fig, current_component, wow_component, avg_component


def register_callbacks(app, repo: CommodityRepository) -> None:
    """Wire the dashboard controls to `render` via a single Dash callback."""

    @app.callback(
        Output("price-chart", "figure"),
        Output("zscore-chart", "figure"),
        Output("kpi-current", "children"),
        Output("kpi-wow", "children"),
        Output("kpi-avg", "children"),
        Input("commodity-dropdown", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
    )
    def _update(commodity_key, start_date, end_date):
        return render(repo, commodity_key, start_date, end_date)
