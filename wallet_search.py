import streamlit as st
import pandas as pd
import requests
from subgrounds.subgrounds import Subgrounds
import utils
from string import Template

st.set_page_config(page_title="Wallet Search", page_icon="🔍", layout="wide")
st.title("🔍 Wallet Search")
st.text("AAVE V2 on Avalanche")

# State Initialization
if 'results_df' not in st.session_state:
    st.session_state['results_df'] = pd.DataFrame()

# aave v2 schema is different from standard lending schema
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
    if st.session_state.user_action_select_input == "Deposited":
        position_side = "LENDER"
        position_side_column_label = "CURRENT DEPOSITED"
    else:
        position_side = "BORROWER"
        position_side_column_label = "CURRENT BORROWED"

    filtered_df = open_positions_df[(open_positions_df["balance_adj"] > st.session_state.asset_quantity_input) 
                                    & (open_positions_df["market.inputToken.symbol"] == st.session_state.asset_select_input)
                                    & (open_positions_df["side"] == position_side)]    
    display_results = filtered_df[["account_id", "balance_adj", "market.inputToken.symbol", "balance_usd"]].copy()
    display_results.sort_values("balance_adj", ascending=False, inplace=True)
    display_results["balance_adj"] = display_results["balance_adj"].apply(lambda x: "{:,.1f}".format(x))
    display_results["balance_usd"] = display_results["balance_usd"].apply(lambda x: "${:,.2f}".format(x))
    display_results.rename(columns={"account_id": "ADDRESS", "balance_adj": position_side_column_label, "market.inputToken.symbol": "ASSET", "balance_usd": "VALUE"}, inplace=True)
    st.session_state["results_df"] = display_results


with st.form("search_filter_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        user_action_select = st.selectbox("Users that have:", ["Deposited", "Borrowed"], key="user_action_select_input")
    with col2:
        asset_quanity = st.number_input("More than:", value=100, min_value=0, key="asset_quantity_input")
    with col3:
        # TODO dynamically populate market token symbols
        asset_select = st.selectbox("Of this asset:", ["WBTC.e", "AAVE.e", "USDC.e", "USDT.e", "WAVAX", "DAI.e", "WETH.e"], key="asset_select_input")
    submitted = st.form_submit_button("Search", on_click=submit_callback)
    

if submitted:
    st.write("Showing users that have", user_action_select.lower(), "more than", asset_quanity, asset_select)

if not st.session_state["results_df"].empty:
    st.dataframe(st.session_state["results_df"])

if st.button("Clear Cache (Your next search may take a few minutes to re-pull data)"):
    get_initial_data.clear()
