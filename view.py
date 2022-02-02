from dash import dcc
from dash import html

def create_layout() -> html.Div:
    return html.Div([
        html.Label("Categoy:"),
        dcc.Dropdown(id="category_dropdown"),

        html.Br(),
        html.Label("Selected items:"),
        dcc.Checklist(id="selected_items_list", labelStyle={"display": "block"}),

        html.Br(),
        html.Label("Presentation text color:"),
        dcc.RadioItems(id="text_color_radioitems", options=["black", "red", "blue"], value="black"),

        html.Hr(),
        html.Button('Clear Result Store', id='clear_result_store_button'),

        html.Hr(),
        html.Div(id="main_presentation_div"),

        html.Hr(),
        html.Br(),
        html.Div(id="compute_results_status_div"),
        html.Br(),
        html.Div(id="debug_compute_info_div"),

        html.Hr(),
        html.Div(id="debug_result_polling_div"),

        html.Hr(),
        html.Div(id="debug_info_div"),

        # Non visual components
        dcc.Store(id="items_to_compute_store"),
        dcc.Store(id="items_computed_store"),
        dcc.Store(id="presentation_config_store"),

        dcc.Store(id="result_polling_state_store"),
        dcc.Interval(id="result_polling_interval", interval=250, disabled=True),

        html.Div(id="dummy_div_1"),
        html.Div(id="dummy_div_2"),
    ])

