# main.py
import time
import logging
import os
import pandas as pd
from datetime import datetime, timedelta, timezone

from alpaca.data.historical import StockHistoricalDataClient, CryptoHistoricalDataClient

from data.feed import load_bars
from execution.trader import init_trader
from strategy.indicators import prepare_data
from strategy.loader import STRATEGY_MAP, load_strategy, get_strategy_name
from backtest.portfolio import run_portfolio_simulation, write_portfolio_backtest
from config import (
    BACKTEST_DAYS, CREDENTIALS_FILE, RECURRING_INVESTMENT, STOCK_LIST, CRYPTO_LIST, FULL_UNIVERSE,
    BAR_TIMEFRAME, INITIAL_CAPITAL, DEFAULT_STRATEGY_ID
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

API_KEY, API_SECRET = None, None
stock_client = None
crypto_client = None
trader = None
STATE = {}
CURRENT_STRATEGY = None 
STRAT_NAME = "Unknown"

def setup():
    global API_KEY, API_SECRET, stock_client, crypto_client, trader, CURRENT_STRATEGY, STRAT_NAME
    try:
        with open(CREDENTIALS_FILE, "r") as f:
            lines = f.readlines()
        key_line = next((line for line in lines if line.startswith("Key:")), None)
        secret_line = next((line for line in lines if line.startswith("Sec:")), None)
        
        API_KEY = key_line.split(":")[1].strip()
        API_SECRET = secret_line.split(":")[1].strip()
        
        stock_client = StockHistoricalDataClient(API_KEY, API_SECRET)
        crypto_client = CryptoHistoricalDataClient(API_KEY, API_SECRET)
        trader = init_trader(API_KEY, API_SECRET)
        
        CURRENT_STRATEGY = load_strategy(DEFAULT_STRATEGY_ID)
        STRAT_NAME = get_strategy_name(DEFAULT_STRATEGY_ID)
        
    except Exception as e:
        print(f"Setup Error: {e}")
        exit()

def play_sound():
    sound_file = "notification.wav"
    if os.path.exists(sound_file):
        try:
            import winsound
            winsound.PlaySound(sound_file, winsound.SND_FILENAME)
        except: pass 

def parse_period_string(input_str):
    periods = []
    parts = input_str.split(',')
    max_lookback = 0
    
    for part in parts:
        part = part.strip()
        if '-' in part:
            try:
                start, end = map(int, part.split('-'))
                periods.append((max(start, end), min(start, end)))
                if max(start, end) > max_lookback: max_lookback = max(start, end)
            except: pass
        else:
            try:
                days = int(part)
                periods.append((days, 0))
                if days > max_lookback: max_lookback = days
            except: pass
            
    return periods, max_lookback

def run_backtest_mode(target_universe, selection_name):
    if not CURRENT_STRATEGY:
        print("Error: No strategy loaded.")
        return

    print(f"\nBatch Backtest Mode [{selection_name}]")
    
    # --- CUSTOM PROMPTS ---
    # 1. Initial Capital
    cap_str = input(f"Initial Capital (Default ${INITIAL_CAPITAL}): ").strip()
    sim_capital = float(cap_str) if cap_str else float(INITIAL_CAPITAL)
    
    # 2. Periods
    period_input = input("Enter Periods (e.g., 365, 730, 3650): ").strip()
    if not period_input: period_input = str(BACKTEST_DAYS)
    
    # 3. Recurring Investment
    print("\n--- Recurring Investment (DCA) ---")
    dca_amt_str = input(f"Amount per deposit (Default ${RECURRING_INVESTMENT['amount']}): ").strip()
    dca_amount = float(dca_amt_str) if dca_amt_str else RECURRING_INVESTMENT["amount"]

    
    dca_interval = 30
    if dca_amount > 0:
        dca_int_str = input(f"Interval in Days (Default {RECURRING_INVESTMENT['interval_days']}): ").strip()
        dca_interval = int(dca_int_str) if dca_int_str else RECURRING_INVESTMENT["interval_days"]

    periods, max_days_needed = parse_period_string(period_input)
    
    # --- SMART FETCH ---
    print(f"\n>>> SMART FETCH: Downloading {max_days_needed} days...")
    master_cache = {}
    
    fetch_end = datetime.now(timezone.utc) - timedelta(minutes=15)
    fetch_start = fetch_end - timedelta(days=max_days_needed + 365) 
    
    for symbol in target_universe:
        print(f"Caching {symbol}...", end=" ")
        try:
            raw_df = load_bars(stock_client, crypto_client, symbol, BAR_TIMEFRAME, fetch_start, fetch_end)
            if not raw_df.empty:
                full_df = prepare_data(raw_df)
                if not full_df.empty:
                    master_cache[symbol] = full_df
                    print("OK")
                else: print("No Indicators")
            else: pass 
        except Exception as e: print(f"Err: {e}")

    if not master_cache:
        print("No data cached. Aborting.")
        return

    # --- BATCH EXECUTION ---
    print(f"\n>>> EXECUTING {len(periods)} SIMULATIONS FROM MEMORY...")
    
    for start_days, end_days in periods:
        
        sim_end_dt = datetime.now(timezone.utc) - timedelta(days=end_days)
        sim_start_dt = datetime.now(timezone.utc) - timedelta(days=start_days)
        period_label = f"{start_days}-{end_days}"
        
        print(f"\nRunning: {selection_name} | {period_label}")
        
        current_ticker_map = {}
        for symbol, df in master_cache.items():
            mask = (df.index >= sim_start_dt) & (df.index <= sim_end_dt)
            sliced_df = df.loc[mask]
            if not sliced_df.empty:
                current_ticker_map[symbol] = sliced_df
        
        if not current_ticker_map:
            print("No data in this time slice.")
            continue

        # Pass Dynamic DCA Settings
        ledger, final_equity = run_portfolio_simulation(
            current_ticker_map, 
            sim_capital, 
            CURRENT_STRATEGY,
            dca_amount=dca_amount,
            dca_interval=dca_interval
        )
        
        print(f"Result: ${final_equity:,.2f}")
        write_portfolio_backtest(ledger, final_equity, STRAT_NAME, period_label, selection_name)

    print("\n>>> ALL BATCHES COMPLETE.")
    play_sound()

def get_asset_selection():
    print("\n1. Stocks (Settings)")
    print("2. Crypto (Settings)")
    print("3. Full Universe")
    print("4. Custom")
    
    u = input("Select: ")
    if u == "1": return STOCK_LIST, "Stocks"
    if u == "2": return CRYPTO_LIST, "Crypto"
    if u == "3": return FULL_UNIVERSE, "Full"
    if u == "4":
        sym = input("Symbols: ").upper()
        return [s.strip() for s in sym.split(',')], "Custom"
    return None, None

def main_menu():
    global CURRENT_STRATEGY, STRAT_NAME
    setup()
    
    while True:
        print(f"\nCOMMANDER [{STRAT_NAME}]")
        print("1. Backtest")
        print("2. Live Trade")
        print("3. Strategy Select")
        print("4. Exit")
        
        choice = input("Option: ")

        if choice == "1":
            target, name = get_asset_selection()
            if target: run_backtest_mode(target, name)
        
        elif choice == "2":
            target, name = get_asset_selection()
            if target:
                print(f"Live Trading {name}... (Ctrl+C to stop)")
                try:
                    while True: time.sleep(60)
                except KeyboardInterrupt: pass
        
        elif choice == "3":
            print(f"1: {get_strategy_name(1)} | 2: {get_strategy_name(2)} | 3: {get_strategy_name(3)}")
            sel = input("ID: ")
            mod = load_strategy(sel)
            if mod:
                CURRENT_STRATEGY = mod
                STRAT_NAME = get_strategy_name(sel)
                print(f"Switched to {STRAT_NAME}")
        
        elif choice == "4":
            exit()

if __name__ == "__main__":
    main_menu()
