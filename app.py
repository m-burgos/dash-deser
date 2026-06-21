import dash
from dash import dcc, html, Input, Output, State

import helpers as H

app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "panel de resultados"
server = app.server

# Styles                                                                       #
PANEL = {"border": "1px solid #d0d0d0", "borderRadius": "6px", "padding": "12px",
         "marginBottom": "14px", "background": "#ffffff"}
PANEL_TITLE = {"margin": "0 0 8px 0", "fontSize": "15px", "color": "#333"}
PLACEHOLDER = {"display": "flex", "alignItems": "center", "justifyContent": "center",
               "height": "120px", "color": "#999", "fontStyle": "italic",
               "border": "1px dashed #ccc", "borderRadius": "4px", "background": "#fafafa"}
RADIO_LABEL = {"marginRight": "14px", "display": "inline-block", "whiteSpace": "nowrap"}


def placeholder(text: str):
    return html.Div(text, style=PLACEHOLDER)


def image_or_placeholder(src, alt, style=None):
    if src:
        st = {"width": "100%", "height": "auto", "objectFit": "contain"}
        if style:
            st.update(style)
        return html.Img(src=src, alt=alt, style=st, className="expandable-img")
    return placeholder(f"{alt}: not found")


def diagnostic_cell(title: str, src):
    """One of the 4 diagnostics, sized to a quarter of the row."""
    return html.Div(
        [
            html.Div(title, style={"fontSize": "12px", "color": "#666",
                                   "marginBottom": "4px", "fontWeight": 600,
                                   "textAlign": "center"}),
            image_or_placeholder(src, title, {"maxHeight": "350px"}),
        ],
        style={"flex": "1 1 0", "minWidth": 0},
    )


# Layout
left_column = html.Div(
    [
        html.Div(
            [
                html.H4("Semester", style=PANEL_TITLE),
                dcc.RadioItems(
                    id="sem-selector",
                    options=[{"label": f"S{n}", "value": n} for n in H.SEMESTERS],
                    value=H.SEMESTERS[0],
                    inline=True,
                    labelStyle=RADIO_LABEL,
                ),
            ],
            style=PANEL,
        ),
        html.Div(
            [
                html.H4("Target distribution", style=PANEL_TITLE),
                dcc.Graph(id="dist-graph", config={"displayModeBar": False}),
                html.Div(
                    "Blue = no dropout (0) · Orange = dropout (1)",
                    style={"fontSize": "12px", "color": "#888", "marginTop": "4px"},
                ),
            ],
            style=PANEL,
        ),
        html.Div(
            [
                html.H4("Calibration overlay (all models)", style=PANEL_TITLE),
                html.Div(id="overlay-container"),
            ],
            style=PANEL,
        ),
    ],
    style={"flex": "0 0 20%", "minWidth": "200px"},
)

right_column = html.Div(
    [
        html.Div(
            [
                html.H4("Model", style=PANEL_TITLE),
                dcc.RadioItems(
                    id="model-selector",
                    options=[{"label": x, "value": x} for x in H.MODELS],
                    value=H.MODELS[0],
                    inline=True,
                    labelStyle=RADIO_LABEL,
                ),
            ],
            style=PANEL,
        ),
        html.Div(
            [
                html.Div(id="diag-grid", style={"display": "flex", "gap": "8px", "alignItems": "flex-start"}),
            ],
            style=PANEL,
        ),
        html.Div(
            [
                dcc.Graph(id="box-graph", config={"displayModeBar": False}),
            ],
            style=PANEL,
        ),
    ],
    style={"flex": "1", "minWidth": "480px"},
)

app.layout = html.Div(
    [
        # Lightbox overlay (hidden by default; managed by assets/lightbox.js)
        html.Div(
            html.Img(id="lightbox-img"),
            id="lightbox-overlay",
            className="lightbox-overlay",
        ),
        html.H2("Deserción por semestre", style={"margin": "12px 16px"}),
        html.Div(
            [left_column, right_column],
            style={"display": "flex", "gap": "16px", "padding": "0 16px 24px 16px",
                   "alignItems": "flex-start"},
        ),
    ],
    style={"fontFamily": "system-ui, sans-serif", "background": "#f4f5f7",
           "minHeight": "100vh"},
)


# Callbacks
def _resolve_model(model, models):
    if model in models:
        return model
    if H.DEFAULT_MODEL in models:
        return H.DEFAULT_MODEL
    return models[0] if models else None


@app.callback(
    Output("dist-graph", "figure"),
    Output("overlay-container", "children"),
    Output("model-selector", "options"),
    Output("model-selector", "value"),
    Input("sem-selector", "value"),
    State("model-selector", "value"),
)
def on_semester(n, current_model):
    """Semester change -> distribution bar, calibration overlay, model radio.

    The selected model is held across semesters (same model names everywhere).
    """
    n = int(n)
    fig = H.build_distribution_figure(n)
    overlay = image_or_placeholder(
        H.encode_image(H.calibration_overlay_path(n)),
        "calibration_overlay"
    )
    models = list(H.get_models(n))
    options = [{"label": m, "value": m} for m in models]
    value = _resolve_model(current_model, models)
    return fig, overlay, options, value


@app.callback(
    Output("diag-grid", "children"),
    Output("box-graph", "figure"),
    Input("sem-selector", "value"),
    Input("model-selector", "value"),
)
def on_selection(n, model):
    """Any change to semester or model -> 4 diagnostics + the single-model boxplots."""
    n = int(n)
    model = _resolve_model(model, list(H.get_models(n)))
    if model is None:
        return [placeholder("No models available")], H.empty_figure("No models")

    cells = [
        diagnostic_cell(title, H.encode_image(H.diagnostic_fig_path(n, model, stem)))
        for stem, title in H.DIAGNOSTIC_FIGS.items()
    ]
    return cells, H.build_boxplots_figure(n, model)

if __name__ == "__main__":
    app.run()