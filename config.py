"""
NAME
    config.py

DESCRIPTION
    Obtains the API keys from enviroment var
"""

import os

API_KEY = os.environ.get("BINANCE_API_KEY")
API_SECRET = os.environ.get("BINANCE_API_SECRET")
