"""
NAME
    Arbitrage_bot.py

DESCRIPTION
    Testing the concept of crupto arbitrage on different excahnges
"""

from collections import defaultdict
import datetime
from operator import itemgetter
from time import time
import csv

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
    start_time = time()
    csvfile = open("arbitrage.csv", "w", newline="", encoding="UTF8")
    result_writer = csv.writer(csvfile, delimiter=",")
    result_writer.writerow(["timestamp", "coins", "profit"])

    n = 0
    while n < ITERATIONS:
        n += 1
        prices = get_prices()
        triangles = list(find_triangles(prices))
        if triangles:
            for triangle in sorted(triangles, key=itemgetter("profit"), reverse=True):
                describe_triangle(prices, triangle, result_writer)
            print("______")


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
    for triangle in recurse_triangle(prices, starting_coin, starting_coin):
        coins = set(triangle["coins"])
        if not any(prev_triangle == coins for prev_triangle in triangles):
            yield triangle
            triangles.append(coins)
    starting_coin = "BUSD"
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
