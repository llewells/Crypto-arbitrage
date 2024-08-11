"""
NAME
    Arbitrage_bot.py

DESCRIPTION
    Testing the concept of crupto arbitrage on different exchanges

NOTES
    - logic grabs prices for every token, then pulls only the primary tokens.
    - once prices have been collected for primarty tokens, triangle are found recursivly.
    - search space is large for each token; timing is important for success, prices like to be out of date.

TODO
    - Reduce time between prices and identifing triangles (parrarellisum?)
    - identify all paths before getting prices
    - confirm logic w.r.t fee calculation; currentl value is hardcoded; obtain fee for each order?
    - can orders be processed simtaniously?xtzbnb

        i.e. usdt->btc->ltc->usdt would have 3 buy order actions are the same time.
        For this to work does it mean that each token needs a set amount?
    - add parameter to handle slippage.

"""

from collections import defaultdict
import datetime
from operator import itemgetter
from time import time
import csv
from tqdm import tqdm

from binance.client import Client

from config import API_KEY, API_SECRET


FEE = 0.00075  # Binance VIP0 level spot-trade transaction fee for "Taker" (limit order)
ITERATIONS = 5000  # iterations to run
PRIMARY = [
    "ETH",
    "USDT",
    "BTC",
    "BUSD",
    "BNB",
    "ADA",
    "SOL",
    "LINK",
    "LTC",
    "UNI",
    "XTZ",
]


def main():

    arb_file = open("arbitrage.csv", "w", newline="", encoding="UTF8")
    result_writer = csv.writer(arb_file, delimiter=",")
    result_writer.writerow(["timestamp", "coins", "profit"])

    stats_file = open("stats.csv", "w", newline="", encoding="UTF8")
    stat_writer = csv.writer(stats_file, delimiter=",")
    stat_writer.writerow(["iter", "duration", "found"])

    n = 0
    while n < ITERATIONS:
        n += 1
        start_time = time()
        prices = get_prices()
        triangles = list(find_triangles(prices))
        find_time = time() - start_time
        print(f"ITER {n} - Time searching for triangles: {find_time} seconds")
        if triangles:
            # this would be where buy instrructions would sit.
            for triangle in sorted(triangles, key=itemgetter("profit"), reverse=True):
                describe_triangle(prices, triangle, result_writer)
            print("______")
        stat_writer.writerow([n, find_time, bool(triangles)])


def get_prices():
    client = Client(API_KEY, API_SECRET)
    prices = client.get_orderbook_tickers()
    prepared = defaultdict(dict)
    for ticker in prices:
        pair = ticker["symbol"]
        ask = float(ticker["askPrice"])
        bid = float(ticker["bidPrice"])
        if ask == 0.0:
            continue
        for primary in PRIMARY:
            if pair.endswith(primary):
                secondary = pair[: -len(primary)]
                prepared[primary][secondary] = 1 / ask
                prepared[secondary][primary] = bid
    return prepared


def find_triangles(prices):
    triangles = []
    starting_coin = "USDT"
    # for starting_coin in prices:
    for triangle in recurse_triangle(prices, starting_coin, starting_coin):
        coins = set(triangle["coins"])
        if not any(prev_triangle == coins for prev_triangle in triangles):
            yield triangle
            triangles.append(coins)


def recurse_triangle(prices, current_coin, starting_coin, depth_left=3, amount=1.0):
    if depth_left > 0:
        pairs = prices[current_coin]
        for coin, price in pairs.items():
            new_price = (amount * price) * (1.0 - FEE)
            for triangle in recurse_triangle(
                prices, coin, starting_coin, depth_left - 1, new_price
            ):
                triangle["coins"] = triangle["coins"] + [current_coin]
                yield triangle
    elif current_coin == starting_coin and amount > 1.0:
        yield {"coins": [current_coin], "profit": amount}


def describe_triangle(prices, triangle, result_writer):
    coins = triangle["coins"]
    price_percentage = (triangle["profit"] - 1.0) * 100
    print(
        f"{datetime.datetime.now()} {'->'.join(coins):26} {round(price_percentage, 4):-7}% profit"
    )
    result_writer.writerow(
        [datetime.datetime.now(), "->".join(coins), round(price_percentage, 4)]
    )

    for i in range(len(coins) - 1):
        first = coins[i]
        second = coins[i + 1]
        print(f"     {second:4} / {first:4}: {prices[first][second]:-17.8f}")
    print("")


if __name__ == "__main__":
    main()
