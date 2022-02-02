from dash import dcc, html


def create_layout() -> html.Div:
    return html.Div([
        html.Label("Categoy:"),
        dcc.Dropdown(id="category_dropdown"),

        html.Br(),
        html.Label("Selected items:"),
        dcc.Checklist(id="items_checklist", labelStyle={"display": "block"}),

        html.Br(),
        html.Label("Presentation text color:"),
        dcc.RadioItems(id="text_color_radioitems", options=["black", "red", "blue"], value="black"),

        html.Hr(),
        html.Button("Clear Result Cache", id="clear_result_cache_button"),

        html.Hr(),
        html.Div(id="main_presentation_div"),

        html.Hr(),
        html.Div(id="dbg_info_div"),
        html.Br(),
        html.Div(id="dbg_is_computing_status_div"),

        # Non visual components
        dcc.Store(id="items_to_compute_store"),
        dcc.Store(id="presentation_config_store"),

        dcc.Store(id="items_computed_store"),
        dcc.Store(id="progress_store"),

        html.Div(id="dummy_div_1"),
        html.Div(id="dummy_div_2"),
    ])
