from dataclasses import asdict
from time import sleep
from typing import List

import dash
import diskcache
import pandas as pd
from dacite import from_dict
from dash import html
from dash.dependencies import Input, Output
from dash.long_callback import DiskcacheLongCallbackManager

from datatypes import ItemAddress, ItemsComputed, ItemsToCompute, PresentationConfig
from result_cache import ResultCache
from sequence_numbers import SequenceNumbers

LONG_CALLBACK_MANAGER = DiskcacheLongCallbackManager(diskcache.Cache("./my_diskcache/for_long_callbacks"))
RESULT_CACHE = ResultCache("./my_diskcache")
SEQUENCE_NUMBERS = SequenceNumbers("./my_diskcache")

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


# Notes:
#
# Maybe look into: https://github.com/uqfoundation/multiprocess
#


def register_callbacks(app: dash.Dash) -> None:

    # =========================================================================
    @app.callback(
        Output("category_dropdown", "options"),
        Output("category_dropdown", "value"),
        Input("dummy_div_1", "children")
    )
    def populate_category_dropdown(_dummy):
        print("populate_category_dropdown()")
        categories=INVENTORY_DF["CAT"].unique().tolist()

        options=[]
        for cat in categories:
            options.append({"label" : cat, "value": cat})

        return options, categories[0]


    # =========================================================================
    @app.callback(
        Output("items_checklist", "options"),
        Output("items_checklist", "value"),
        Input("category_dropdown", "value"),
        Input("items_checklist", "value"),
    )
    def update_items_checklist(selected_category, old_selected_items):
        print(f"update_items_checklist(selected_category={selected_category})")
        available_items = INVENTORY_DF.loc[INVENTORY_DF["CAT"] == selected_category]["ITEM"].tolist()
        options = []
        for i in available_items:
            options.append({ "label": i, "value": i})

        new_sel_items = []
        if old_selected_items:
            for i in old_selected_items:
                if i in available_items:
                    new_sel_items.append(i)

        if not new_sel_items:
            new_sel_items = [available_items[0]]

        return options, new_sel_items


    # =========================================================================
    @app.callback(
        Output("dummy_div_2", "children"),
        Input("clear_result_cache_button", "n_clicks"),
    )
    def clear_result_cache_button_clicked(_n_clicks):
        print("clear_result_cache_button_clicked()")
        RESULT_CACHE.clear_all_results()
        return ""


    # =========================================================================
    @app.callback(
        Output("presentation_config_store", "data"),
        Output("items_to_compute_store", "data"),
        Output("items_to_compute_store", "clear_data"),
        Input("category_dropdown", "value"),
        Input("items_checklist", "value"),
        Input("text_color_radioitems", "value"),
    )
    def determine_items_to_compute_and_present(category, selected_items, text_color):
        print(f"determine_items_to_compute_and_present()  category={category}, items={selected_items}")

        presentation_config = PresentationConfig(text_color=text_color)
        addresses_to_compute: List[ItemAddress] = []

        for item in selected_items:
            address = ItemAddress(category, item)
            presentation_config.addr_list.append(address)

            if not RESULT_CACHE.has_result(category, item):
                addresses_to_compute.append(address)

        if len(addresses_to_compute) > 0:
            items_to_compute = ItemsToCompute(batch_id=SEQUENCE_NUMBERS.generate("batchid"), addr_list=addresses_to_compute)
            return asdict(presentation_config), asdict(items_to_compute), False
        else:
            return asdict(presentation_config), dash.no_update, True


    # =========================================================================
    @app.long_callback(
        Output("items_computed_store", "data"),
        Input("items_to_compute_store", "data"),
        running=[(Output("dbg_is_computing_status_div", "children"), "compute RUNNING...", "compute not running")],
        progress=[Output("progress_store", "data")],
        manager=LONG_CALLBACK_MANAGER,
        interval=100,
        prevent_initial_call=True,
    )
    def compute_results(set_progress, items_to_compute_data):
        print("compute_results()")

        if not items_to_compute_data:
            print("no result to compute, returning immediately")
            return dash.no_update

        items_to_compute = from_dict(data_class=ItemsToCompute, data=items_to_compute_data)
        items_computed = ItemsComputed(batch_id=items_to_compute.batch_id)

        print(f"computing {len(items_to_compute.addr_list)} results, batch_id={items_to_compute.batch_id}")

        for addr in items_to_compute.addr_list:
            _fake_calculate_and_store_result(addr.category, addr.item_name)
            items_computed.addr_list.append(addr)

            # Here we're sending the entire ItemsComputed structure through the progress
            # mechanism, even though we're really only interested in signaling that something
            # new is available
            set_progress((asdict(items_computed),))

        return asdict(items_computed)


    # =========================================================================
    # Note that setting the progress_store's data property as input seems to continuously
    # trigger the callback. Is this a bug?
    # A work-around seems to be to only use the modified_timestamp attribute as input
    # instead - go figure!
    @app.callback(
        Output("main_presentation_div", component_property="children"),
        Input("presentation_config_store", component_property="data"),
        Input("items_computed_store", component_property="data"),
        Input("progress_store", component_property="modified_timestamp"),
        
    )
    def render_main_presentation(presentation_config_data, _items_computed_data, _progress_modified_timestamp):

        print("render_main_presentation()")
        #print("triggering on:", dash.callback_context.triggered)

        presentation_config = from_dict(data_class=PresentationConfig, data=presentation_config_data)

        html_items = []
        for addr in presentation_config.addr_list:
            result = RESULT_CACHE.get_result(addr.category, addr.item_name)
            html_items.append(html.Li(f"{addr.category}, {addr.item_name}: {result}"))

        return html.Div(
            style={"color": presentation_config.text_color},
            children=[
                html.U(html.B("MAIN PRESENTATION:")),
                html.P("Items:"),
                html.Ul(children=html_items),
            ]
        )


    # =========================================================================
    @app.callback(
        Output(component_id="dbg_info_div", component_property="children"),
        Input(component_id="presentation_config_store", component_property="data"),
        Input(component_id="items_to_compute_store", component_property="data"),
    )
    def update_debug_info(presentation_config_data, items_to_compute_data):
        print("update_debug_info()")

        items_to_compute = from_dict(data_class=ItemsToCompute, data=items_to_compute_data) if items_to_compute_data else ItemsToCompute(-1)
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
            html.P(f"Items to compute: (batch_id={items_to_compute.batch_id})"),
            html.Ul(children=compute_html_items),
        ]

        return children



# =========================================================================
def _fake_calculate_and_store_result(category: str, item_name: str) -> None:

    print(f"calculating item: category={category}, item_name={item_name}")

    sleep(2.1)
    result = f"COMPUTED#{category}_{item_name}"

    print(f"calculating done: category={category}, item_name={item_name}  --> result={result}")

    RESULT_CACHE.set_result(cat=category, item_name=item_name, res=result)
