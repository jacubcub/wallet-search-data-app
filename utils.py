from turtle import position
import pandas as pd
import requests


def get_deployments() -> pd.DataFrame:
    url = "https://subgraphs.messari.io/deployments.json"
    response = requests.get(url).json()

    df = pd.DataFrame(response)

    df2 = df.stack().to_frame()
    types = [item[1] for item in df2.index]

    deployments = pd.DataFrame(df2[0].tolist())
    deployments.index = df.index

    # set schema in index
    deployments["schema"] = types
    deployments = deployments.set_index([deployments.index, "schema"])

    # bring up schema to second level of axis=1 & sort
    deployments = deployments.unstack().swaplevel(axis=1).sort_index(axis=1)
    return deployments

def get_all_open_positions(subgraph_url: str) -> pd.DataFrame:
    """Gets all open positions from extended lending subgraph

    Args:
        subgraph_url (str): URL of extended lending subgraph

    Returns:
        pd.DataFrame: Pandas DataFrame of positions with columns
            ['balance', 'side', 'market.inputTokenPriceUSD',
            'market.inputToken.symbol', 'market.inputToken.decimals', 'account_id', 'balance_adj', 'balance_usd]
    """
    last_id = "0x0000000000000000000000000000000000000000"
    data_list = []
    first = 500

    while True:
        all_positions_query = """
            query($first: Int, $last_id: String){
                accounts(first: $first, where: {openPositionCount_gt: 0, id_gt: $last_id}, orderBy: id) {
                    account_id: id
                    positions(where: {hashClosed: null}) {
                        balance
                        side
                        market {
                            inputTokenPriceUSD
                            inputToken {
                                symbol
                                decimals
                            }
                        }
                    }
                }
            }
            """

        payload = {
            "query": all_positions_query, 
            "variables": {
                "first": first,
                "last_id": last_id
            }
        }
        resp = requests.post(subgraph_url, json=payload)
        data = resp.json()
        data_list.extend(data["data"]["accounts"])

        if (len(data["data"]["accounts"]) != first):
            break

        # get into df to get max account_id
        tmp_df = pd.json_normalize(data["data"]["accounts"], "positions", ["account_id"])
        last_id = tmp_df["account_id"].max()
        print("Progress: ", "{:.1%}".format(int(last_id[:5], 16) / 0xfff), end="\r", flush=True)
    
    positions_df = pd.json_normalize(data_list, "positions", ["account_id"])
    positions_df["balance"] = positions_df["balance"].apply(int) # numbers too large for pd.to_numeric()
    positions_df["market.inputTokenPriceUSD"] = pd.to_numeric(positions_df["market.inputTokenPriceUSD"])
    positions_df["balance_adj"] = positions_df["balance"] / (10 ** positions_df["market.inputToken.decimals"])
    positions_df["balance_usd"] = positions_df["balance_adj"] * positions_df["market.inputTokenPriceUSD"]
    return positions_df