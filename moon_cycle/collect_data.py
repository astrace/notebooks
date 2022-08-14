"""Gather historical crypto price data from the CoinGecko API."""

from datetime import datetime
from functools import reduce
import json
import pandas as pd
import time

from pycoingecko import CoinGeckoAPI
cg = CoinGeckoAPI()

# get coin id to ticker mapping
filename = "CoinGecko_coinID_to_ticker.json"
try:
    with open(filename, "r") as f:
        COIN_ID_TO_TICKER = json.load(f)
except:
    l = cg.get_coins_list()
    COIN_ID_TO_TICKER = {d['id']:d['symbol'] for d in l}
    COIN_ID_TO_TICKER["crypto20"] = "C20"
    with open(filename, 'w') as f:
        json.dump(COIN_ID_TO_TICKER, f)


def historical_prices(
        coin_id, from_date, to_date,
        currency="USD", filename=None
    ):

    ticker = COIN_ID_TO_TICKER[coin_id].upper()
    from_ts = int(datetime.strptime(from_date, "%d-%m-%Y").timestamp())
    to_ts = int(datetime.strptime(to_date, "%d-%m-%Y").timestamp())
    
    print("Getting {} ({}) price data...".format(ticker, coin_id))
    
    result_json = cg.get_coin_market_chart_range_by_id(coin_id, currency, from_ts, to_ts)

    dfs = [
        pd.DataFrame(
            [[t[0]//1000, t[1]] for t in result_json[x]],
            columns=['unixtime', x]
        ).set_index('unixtime')
        for x in result_json.keys()
    ]
    df = reduce(lambda df1, df2: df1.join(df2), dfs)

    # add date
    df["date"] = [str(datetime.fromtimestamp(ts)) for ts in df.index]
    # add ticker
    df["ticker"] = ticker + "|" + currency
    # change column order
    df = df[["date"] + ["ticker"] + list(df.columns[:-2])]

    if not filename:
        filename = "./data/CoinGecko_{}{}_{}_{}.csv".format(
                ticker, currency,
                df.iloc[0].date[:10],
                df.iloc[-1].date[:10]
        )

    df.to_csv(filename)
    print('Saved to {}'.format(filename))
    

if __name__ == "__main__":
    # Top 30 coins as of Aug. 14, 2002
    # Not including stables or wrapped tokens
    coin_ids = [
        "bitcoin",
        "ethereum",
        "binancecoin",
        "ripple",
        "cardano",
        "solana",
        "polkadot",
        "dogecoin",
        "avalanche-2",
        "staked-ether",
        "shiba-inu",
        "matic-network",
        "tron",
        "ethereum-classic",
        "okb",
        "near",
        "leo-token",
        "litecoin",
        "chainlink",
        "ftx-token",
        "uniswap",
        "crypto-com-chain",
        "cosmos",
        "stellar",
        "monero",
        "flow",
        "bitcoin-cash",
        "algorand",
        "vechain",
        "filecoin"
    ]
    for cid in coin_ids:
        historical_prices(cid, "01-01-2009", "01-08-2022")
        time.sleep(5) # in case of rate limits
