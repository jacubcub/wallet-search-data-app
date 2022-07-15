import streamlit as st
import pandas as pd
import requests
from subgrounds.subgrounds import Subgrounds
import utils
from string import Template

# State Initialization
if 'results_df' not in st.session_state:
    st.session_state['results_df'] = 'Try Searching!'

# aave v2 schema is different from standard lending schema and doesn't have liquidatee which we need
# however, standard lending schema does not have accounts so we can't see which user made a deposit for example
# let's use extended schema so we can use positions
# deployments = utils.get_deployments()
# lending_deployments = deployments['lending-protocols'].dropna(how='all')
# url = lending_deployments.loc['compound-v2','mainnet']
url = "https://api.thegraph.com/subgraphs/name/messari/aave-v2-avalanche-extended"
sg = Subgrounds()
lending = sg.load_subgraph(url)

@st.experimental_memo
def get_initial_data():
    return utils.get_all_open_positions(url)

open_positions_df = get_initial_data()

def submit_callback():
    st.write("in callback", st.session_state.asset_quantity_input, st.session_state.asset_select_input)
    filtered_df = open_positions_df[(open_positions_df["balance_adj"] > st.session_state.asset_quantity_input) & (open_positions_df["market.inputToken.symbol"] == st.session_state.asset_select_input)]    
    display_results = filtered_df[["account_id", "balance_adj", "market.inputToken.symbol", "balance_usd"]].copy()
    st.session_state["results_df"] = display_results


with st.form("search_filter_form"):
    st.write("Wallet Filter Form")
    asset_quanity = st.number_input("Asset Quantity", value=100, min_value=0, key="asset_quantity_input")
    asset_select = st.selectbox("Asset", ["WBTC.e", "AAVE.e", "USDC.e", "USDT.e", "WAVAX", "DAI.e", "WETH.e"], key="asset_select_input")
    submitted = st.form_submit_button("Search", on_click=submit_callback)
    if submitted:
        st.write("Searching for wallets with more than", asset_quanity, asset_select)


st.write(st.session_state["results_df"])
