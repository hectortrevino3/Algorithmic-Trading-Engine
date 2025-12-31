# config.py
import json
import os
from datetime import time as dt_time
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

CREDENTIALS_FILE = "API_Key&Secret.txt"
SETTINGS_FILE = "settings.json"

# --- DEFAULTS ---
DEFAULT_CAPITAL = 1000.0
DEFAULT_DAYS = 365
DEFAULT_STRAT = "1"
DEFAULT_RECURRING_INVESTMENT = {
    "enabled": False, 
    "amount": 0.0, 
    "interval_days": 30
}

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {}
    try:
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading settings: {e}")
        return {}

settings = load_settings()

# --- EXPORTS ---
INITIAL_CAPITAL = settings.get("account", {}).get("initial_capital", DEFAULT_CAPITAL)
BACKTEST_DAYS = settings.get("account", {}).get("backtest_days", DEFAULT_DAYS)
PAPER_TEST = settings.get("account", {}).get("paper_mode", True)
RECURRING_INVESTMENT = settings["account"].get("recurring_investment", DEFAULT_RECURRING_INVESTMENT)

DEFAULT_STRATEGY_ID = settings.get("strategy", {}).get("default", DEFAULT_STRAT)

# Asset Lists
STOCK_LIST = settings.get("universe", {}).get("stocks", [])
CRYPTO_LIST = settings.get("universe", {}).get("crypto", [])
FULL_UNIVERSE = STOCK_LIST + CRYPTO_LIST

# --- TIMEFRAME ---
BAR_TIMEFRAME = TimeFrame(1, TimeFrameUnit.Day)
MARKET_OPEN = dt_time(9, 30) 
MARKET_CLOSE = dt_time(16, 00)