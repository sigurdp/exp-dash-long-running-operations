from time import sleep
import dash
from dash import html
from dash.dependencies import Input, Output, State
from dash.long_callback import DiskcacheLongCallbackManager
import pandas as pd
from concurrent.futures import ProcessPoolExecutor
from dacite import from_dict
from dataclasses import asdict

import diskcache

from app_types import ItemAddress, ItemsComputed, ItemsToCompute, PresentationConfig, ResultPollingState
from result_store import ResultStore

LONG_CALLBACK_MANAGER = DiskcacheLongCallbackManager(diskcache.Cache("./my_diskcache/for_long_callbacks"))
RESULT_STORE = ResultStore("./my_diskcache/result_store")

inventory_input_data = [
    [ "CAT",     "ITEM" ],
    [ "cat_a",   "item_1"],
    [ "cat_a",   "item_2"],
    [ "cat_a",   "item_3"],
    [ "cat_a",   "item_4"],
    [ "cat_b",   "item_1"],
    [ "cat_b",   "item_2"],
    [ "cat_b",   "item_101"],
    [ "cat_b",   "item_102"],
    [ "cat_b",   "item_103"],
]

INVENTORY_DF = pd.DataFrame(inventory_input_data[1:], columns=inventory_input_data[0])


#
# Look into: https://github.com/uqfoundation/multiprocess
#


def register_callbacks(app: dash.Dash) -> None:

    # =========================
    @app.callback(
        Output(component_id='category_dropdown', component_property='options'),
        Output(component_id='category_dropdown', component_property='value'),
        Input(component_id="dummy_div_1", component_property="children")
    )
    def populate_category_dropdown(dummy):
        print(f"populate_category_dropdown()")
        categories=INVENTORY_DF["CAT"].unique().tolist()
        
        options=[]
        for cat in categories:
            options.append({"label" : cat, "value": cat})

        return options, categories[0]


    # =========================
    @app.callback(
        Output(component_id="selected_items_list", component_property="options"),
        Output(component_id="selected_items_list", component_property="value"),
        Input(component_id='category_dropdown', component_property='value'),
        Input(component_id="selected_items_list", component_property="value"),
    )
    def update_selected_items_list(selected_category, old_sel_items):
        print(f"update_selected_items_list(selected_category={selected_category})")
        available_items = INVENTORY_DF.loc[INVENTORY_DF["CAT"] == selected_category]["ITEM"].tolist()
        options = []
        for i in available_items:
            options.append({ "label": i, "value": i})

        new_sel_items = []
        if old_sel_items:
            for i in old_sel_items:
                if i in available_items:
                    new_sel_items.append(i)

        if not new_sel_items:
            new_sel_items = [available_items[0]]

        return options, new_sel_items


    # =========================
    @app.callback(
        Output(component_id="dummy_div_2", component_property="children"),
        Input(component_id="clear_result_store_button", component_property="n_clicks"),
    )
    def clear_result_store_button_clicked(n_clicks):
        print(f"clear_result_store_button_clicked()")
        RESULT_STORE.clear_all_results()
        return ""


    # =========================
    @app.callback(
        Output(component_id="presentation_config_store", component_property="data"),
        Output(component_id="items_to_compute_store", component_property="data"),
        Output(component_id="items_to_compute_store", component_property="clear_data"),
        Input(component_id="category_dropdown", component_property="value"),
        Input(component_id="selected_items_list", component_property="value"),
        Input(component_id="text_color_radioitems", component_property="value"),
    )
    def determine_items_to_compute_and_present(category, selected_items, text_color):
        print(f"determine_items_to_compute_and_present()  category={category}, items={selected_items}")
        
        items_to_compute = ItemsToCompute()
        presentation_config = PresentationConfig(text_color=text_color)

        for item in selected_items:
            item_address = ItemAddress(category, item)
            presentation_config.addr_list.append(item_address)

            if not RESULT_STORE.has_result(category, item):
                items_to_compute.addr_list.append(item_address)

        if len(items_to_compute.addr_list) > 0:
            return asdict(presentation_config), asdict(items_to_compute), False
        else:
            return asdict(presentation_config), dash.no_update, True


    # =========================
    @app.long_callback(
        Output(component_id="items_computed_store", component_property="data"),
        Output(component_id="debug_compute_info_div", component_property="children"),
        Input(component_id="items_to_compute_store", component_property="data"),
        running=[
            (Output("compute_results_status_div", "children"), "compute RUNNING...", "compute finished"),
            (Output("result_polling_interval", "disabled"), False, True)
        ],
        manager=LONG_CALLBACK_MANAGER,
        interval=1000,
        prevent_initial_call=True,
    )
    def compute_results(items_to_compute_data):
        print(f"compute_results()")
        
        if not items_to_compute_data:
            print(f"no result to compute, returning immediately")
            return dash.no_update, dash.no_update

        items_to_compute = from_dict(data_class=ItemsToCompute, data=items_to_compute_data)
        items_computed = ItemsComputed()

        compute_dbg_info_list = []

        for index, addr in enumerate(items_to_compute.addr_list):
            res = _fake_calculate_item(index, addr.category, addr.item_name)
            items_computed.addr_list.append(addr)
            
            info_str = f"{addr} --> {res}"
            compute_dbg_info_list.append(info_str)

        html_list_items = [html.Li(info_str) for info_str in compute_dbg_info_list]
        children = [
            html.B("Debug computed info:"),
            html.Ul(children=html_list_items)
        ]

        return asdict(items_computed), children


    # =========================
    @app.callback(
        Output(component_id="main_presentation_div", component_property="children"),
        Input(component_id="presentation_config_store", component_property="data"),
        Input(component_id="items_computed_store", component_property="data"),
        Input(component_id="result_polling_state_store", component_property="data"),
    )
    def render_main_presentation(presentation_config_data, _items_computed_data, _result_polling_state):
        print(f"render_main_presentation()")

        presentation_config = from_dict(data_class=PresentationConfig, data=presentation_config_data)

        presentation_html_items = []
        for addr in presentation_config.addr_list:
            result = RESULT_STORE.get_result(addr.category, addr.item_name)
            presentation_html_items.append(html.Li(f"{addr.category}, {addr.item_name}: {result}"))

        return html.Div(
            style={"color": presentation_config.text_color}, 
            children=[
                html.U(html.B("MAIN PRESENTATION:")),
                html.P("Items:"),
                html.Ul(children=presentation_html_items),
            ]
        )


    # =========================
    @app.callback(
        Output(component_id="result_polling_state_store", component_property="data"),
        Output(component_id="debug_result_polling_div", component_property="children"),
        Input(component_id="result_polling_interval", component_property="n_intervals"),
        State(component_id="items_to_compute_store", component_property="data"),
        State(component_id="items_to_compute_store", component_property="modified_timestamp"),
        State(component_id="result_polling_state_store", component_property="data"),
        prevent_initial_call = True
    )
    def poll_for_new_results(n_intervals, items_to_compute_data, items_to_compute_timestamp, old_result_polling_state_data):
        print(f"poll_for_new_results({n_intervals})")

        items_to_compute = from_dict(data_class=ItemsToCompute, data=items_to_compute_data) if items_to_compute_data else ItemsToCompute()

        old_polling_state = from_dict(data_class=ResultPollingState, data=old_result_polling_state_data) if old_result_polling_state_data else None
        new_polling_state = ResultPollingState(compute_timestamp=items_to_compute_timestamp)

        for addr in items_to_compute.addr_list:
            if not RESULT_STORE.has_result(addr.category, addr.item_name):
                new_polling_state.missing_addr_list.append(addr)

        tot_count = len(items_to_compute.addr_list)
        missing_count = len(new_polling_state.missing_addr_list)

        debug_div_children = [
            html.U(html.B("Debug polling info:")),
            html.P(f"n_intervals={n_intervals}"),
            html.P(f"computed {tot_count - missing_count} of {tot_count}")
        ]

        if old_polling_state and old_polling_state == new_polling_state:
            return dash.no_update, debug_div_children
        else:
            return asdict(new_polling_state), debug_div_children


    # =========================
    @app.callback(
        Output(component_id="debug_info_div", component_property="children"),
        Input(component_id="items_to_compute_store", component_property="data"),
        Input(component_id="presentation_config_store", component_property="data"),
    )
    def update_debug_info(items_to_compute_data, presentation_config_data):
        print(f"update_debug_info()")
        
        items_to_compute = from_dict(data_class=ItemsToCompute, data=items_to_compute_data) if items_to_compute_data else ItemsToCompute()
        presentation_config = from_dict(data_class=PresentationConfig, data=presentation_config_data)

        presentation_html_items = [html.Li(str(addr)) for addr in presentation_config.addr_list]
        compute_html_items = [html.Li(str(addr)) for addr in items_to_compute.addr_list]

        children = [
            html.U(html.B("Debug info:")),
            html.P([
                "Presentation config:", html.Br(), 
                f"text_color={presentation_config.text_color}"
            ]),
            html.P("Items to present:"),
            html.Ul(children=presentation_html_items),
            html.P("Items to compute:"),
            html.Ul(children=compute_html_items)
        ]

        return children



def _fake_calculate_item(index: int, category: str, item_name: str):
    
    print(f"calculating item {index}: category={category}, item_name={item_name}")
    sleep(0.5*(index+1))
    
    result = f"COMPUTED#{category}_{item_name}"

    RESULT_STORE.set_result(cat=category, item_name=item_name, res=result)

    return result