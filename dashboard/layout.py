"""Static layout for the commodity dashboard.

`build_layout` returns the Dash component tree: a header, the control row
(commodity dropdown + date-range picker), three KPI cards, and two charts.
Component values are populated at runtime by the callbacks (Chunk 7 callbacks).
"""

from __future__ import annotations

from dash import dcc, html

# --- Modern SaaS Design Tokens (Dark-first, Glassmorphism, Linear/Stripe aesthetic)
COLORS = {
    "bg": "#06090e",
    "panel": "rgba(13, 19, 33, 0.75)",
    "panel_alt": "rgba(20, 29, 48, 0.65)",
    "text": "#f8fafc",
    "muted": "#94a3b8",
    "faint": "#64748b",
    "accent": "#00f0ff",
    "accent_blue": "#38bdf8",
    "up": "#10b981",
    "down": "#f43f5e",
    "border": "rgba(255, 255, 255, 0.08)",
}

_LABEL_STYLE = {
    "color": COLORS["muted"],
    "fontSize": "11px",
    "fontWeight": "600",
    "textTransform": "uppercase",
    "letterSpacing": "0.08em",
    "marginBottom": "8px",
}

_VALUE_STYLE = {
    "color": COLORS["text"],
    "fontSize": "32px",
    "fontWeight": "800",
    "fontFamily": "Plus Jakarta Sans, Inter, sans-serif",
    "letterSpacing": "-0.02em",
}

_GRAPH_CONFIG = {
    "displayModeBar": False,
    "responsive": True,
}


_CARD_STYLE = {
    "backgroundColor": COLORS["panel_alt"],
    "background": "linear-gradient(135deg, rgba(20, 29, 48, 0.65) 0%, rgba(12, 18, 30, 0.8) 100%)",
    "backdropFilter": "blur(12px)",
    "WebkitBackdropFilter": "blur(12px)",
    "borderRadius": "14px",
    "padding": "20px 24px",
    "flex": "1",
    "border": f"1px solid {COLORS['border']}",
    "boxShadow": "0 8px 24px -6px rgba(0, 0, 0, 0.4)",
}


def _kpi_card(label: str, value_id: str, badge_text: str | None = None) -> html.Div:
    """A single SaaS metric card with subtle glassmorphism and animated glow."""
    badge = (
        html.Span(
            badge_text,
            style={
                "fontSize": "10px",
                "fontWeight": "600",
                "letterSpacing": "0.05em",
                "padding": "2px 8px",
                "borderRadius": "12px",
                "backgroundColor": "rgba(56, 189, 248, 0.12)",
                "color": COLORS["accent_blue"],
                "border": "1px solid rgba(56, 189, 248, 0.25)",
            },
        )
        if badge_text
        else None
    )

    return html.Div(
        className="kpi-card",
        style=_CARD_STYLE,
        children=[
            html.Div(
                [
                    html.Span(label, style=_LABEL_STYLE),
                    badge,
                ],
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "center",
                },
            ),
            html.Div("—", id=value_id, style=_VALUE_STYLE),
        ],
    )


def build_layout(
    commodities: dict,
    default_key: str,
    date_min: str | None,
    date_max: str | None,
) -> html.Div:
    """Build the full dashboard layout with SaaS-grade visual hierarchy.

    Args:
        commodities: The COMMODITIES catalog (key -> Commodity).
        default_key: Commodity selected on first load.
        date_min/date_max: ISO date bounds for the date-range picker.
    """
    options = [{"label": c.label, "value": key} for key, c in commodities.items()]

    return html.Div(
        style={
            "backgroundColor": COLORS["bg"],
            "minHeight": "100vh",
            "padding": "32px 48px",
            "fontFamily": "Plus Jakarta Sans, Inter, system-ui, -apple-system, sans-serif",
        },
        children=[
            # --- Top SaaS Navigation / Header -------------------------------
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Span(
                                        "⚡ QUANTITATIVE ENERGY INTELLIGENCE",
                                        style={
                                            "fontSize": "11px",
                                            "fontWeight": "700",
                                            "letterSpacing": "0.1em",
                                            "color": COLORS["accent"],
                                            "textTransform": "uppercase",
                                            "backgroundColor": "rgba(0, 240, 255, 0.08)",
                                            "padding": "4px 10px",
                                            "borderRadius": "20px",
                                            "border": "1px solid rgba(0, 240, 255, 0.2)",
                                            "display": "inline-block",
                                            "marginBottom": "10px",
                                        },
                                    ),
                                    html.H1(
                                        "Energy Market Intelligence",
                                        style={
                                            "color": COLORS["text"],
                                            "margin": "0",
                                            "fontSize": "30px",
                                            "fontWeight": "800",
                                            "letterSpacing": "-0.03em",
                                        },
                                    ),
                                    html.P(
                                        "Institutional-grade monitoring, volatility surface, and ARIMA(1,1,1) probabilistic forecasting",
                                        style={
                                            "color": COLORS["muted"],
                                            "margin": "6px 0 0 0",
                                            "fontSize": "14px",
                                            "fontWeight": "400",
                                        },
                                    ),
                                ]
                            ),
                            # Status indicators
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Span(
                                                "●",
                                                style={
                                                    "color": COLORS["up"],
                                                    "marginRight": "6px",
                                                    "fontSize": "12px",
                                                },
                                            ),
                                            html.Span(
                                                "EIA v2 Stream Active",
                                                style={
                                                    "color": "#e2e8f0",
                                                    "fontSize": "12px",
                                                    "fontWeight": "600",
                                                },
                                            ),
                                        ],
                                        style={
                                            "padding": "6px 14px",
                                            "borderRadius": "20px",
                                            "backgroundColor": "rgba(16, 185, 129, 0.1)",
                                            "border": "1px solid rgba(16, 185, 129, 0.25)",
                                            "display": "flex",
                                            "alignItems": "center",
                                        },
                                    ),
                                    html.Div(
                                        [
                                            html.Span(
                                                "95% CI Interval",
                                                style={
                                                    "color": COLORS["accent_blue"],
                                                    "fontSize": "12px",
                                                    "fontWeight": "600",
                                                },
                                            ),
                                        ],
                                        style={
                                            "padding": "6px 14px",
                                            "borderRadius": "20px",
                                            "backgroundColor": "rgba(56, 189, 248, 0.1)",
                                            "border": "1px solid rgba(56, 189, 248, 0.25)",
                                            "display": "flex",
                                            "alignItems": "center",
                                        },
                                    ),
                                ],
                                style={"display": "flex", "gap": "10px"},
                            ),
                        ],
                        style={
                            "display": "flex",
                            "justifyContent": "space-between",
                            "alignItems": "flex-end",
                            "flexWrap": "wrap",
                            "gap": "16px",
                        },
                    ),
                ],
                style={"marginBottom": "28px"},
            ),
            # --- Controls Bar ---------------------------------------------
            html.Div(
                className="glass-panel",
                style={
                    "backgroundColor": "rgba(13, 19, 33, 0.75)",
                    "backdropFilter": "blur(16px)",
                    "WebkitBackdropFilter": "blur(16px)",
                    "border": f"1px solid {COLORS['border']}",
                    "borderRadius": "14px",
                    "padding": "16px 24px",
                    "display": "flex",
                    "gap": "32px",
                    "alignItems": "center",
                    "flexWrap": "wrap",
                    "marginBottom": "24px",
                },
                children=[
                    html.Div(
                        [
                            html.Div("Commodity Asset", style=_LABEL_STYLE),
                            dcc.Dropdown(
                                id="commodity-dropdown",
                                options=options,
                                value=default_key,
                                clearable=False,
                                style={"width": "300px"},
                            ),
                        ]
                    ),
                    html.Div(
                        [
                            html.Div("Historical Window", style=_LABEL_STYLE),
                            dcc.DatePickerRange(
                                id="date-range",
                                min_date_allowed=date_min,
                                max_date_allowed=date_max,
                                start_date=date_min,
                                end_date=date_max,
                                display_format="YYYY-MM-DD",
                            ),
                        ]
                    ),
                ],
            ),
            # --- Headline Metrics / KPI Cards -----------------------------
            html.Div(
                [
                    _kpi_card("Spot Price", "kpi-current", "LATEST QUOTE"),
                    _kpi_card("Week-over-Week Momentum", "kpi-wow", "DELTA"),
                    _kpi_card("4-Week Moving Baseline", "kpi-avg", "SMA(4W)"),
                ],
                style={"display": "flex", "gap": "20px", "marginBottom": "24px"},
            ),
            # --- Interactive Visualizations -------------------------------
            dcc.Loading(
                color=COLORS["accent"],
                children=[
                    html.Div(
                        dcc.Graph(id="price-chart", config=_GRAPH_CONFIG),
                        className="glass-panel",
                        style={
                            "backgroundColor": "rgba(13, 19, 33, 0.75)",
                            "backdropFilter": "blur(16px)",
                            "WebkitBackdropFilter": "blur(16px)",
                            "border": f"1px solid {COLORS['border']}",
                            "borderRadius": "16px",
                            "padding": "14px",
                            "marginBottom": "20px",
                            "boxShadow": "0 10px 30px -10px rgba(0, 0, 0, 0.5)",
                        },
                    ),
                    html.Div(
                        dcc.Graph(id="zscore-chart", config=_GRAPH_CONFIG),
                        className="glass-panel",
                        style={
                            "backgroundColor": "rgba(13, 19, 33, 0.75)",
                            "backdropFilter": "blur(16px)",
                            "WebkitBackdropFilter": "blur(16px)",
                            "border": f"1px solid {COLORS['border']}",
                            "borderRadius": "16px",
                            "padding": "14px",
                            "marginBottom": "24px",
                            "boxShadow": "0 10px 30px -10px rgba(0, 0, 0, 0.5)",
                        },
                    ),
                ],
            ),
            # --- Footer ---------------------------------------------------
            html.Div(
                [
                    html.Div(
                        "Market Data Source: U.S. Energy Information Administration (EIA v2 REST API) • "
                        "Forecasting Engine: Statsmodels ARIMA(1,1,1) with 95% Confidence Bounds • "
                        "Anomaly Detection: Hampel Filter (Rolling MAD 3.5σ)",
                        style={"color": COLORS["faint"], "fontSize": "12px"},
                    ),
                ],
                style={
                    "borderTop": f"1px solid {COLORS['border']}",
                    "paddingTop": "18px",
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "center",
                },
            ),
        ],
    )
