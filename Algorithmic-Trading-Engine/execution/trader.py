# execution/trader.py
import time
import json
import os
import pandas as pd
from datetime import datetime, timezone, timedelta
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.timeframe import TimeFrame

# INTEGRATION
from strategy.indicators import prepare_data
from strategy.titan import get_decision
from data.feed import load_bars 

# --- STATE MANAGEMENT ---
STATE_FILE = "trade_state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except: pass
    return {}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=4)

def init_trader(api_key, api_secret, paper=True):
    return TradingClient(api_key, api_secret, paper=paper)

def get_account_cash(trader):
    try:
        acct = trader.get_account()
        return float(acct.cash), float(acct.buying_power)
    except Exception as e:
        print(f"Error fetching account info: {e}")
        return 0.0, 0.0

def get_position_details(trader, symbol):
    try:
        pos = trader.get_open_position(symbol)
        return float(pos.qty), float(pos.avg_entry_price)
    except:
        return 0.0, 0.0

def execute_cycle(trader, stock_client, crypto_client, symbols):
    """
    Main Live Trading Loop
    """
    print(f"\n--- Scan Cycle: {datetime.now(timezone.utc).strftime('%H:%M:%S')} ---")
    
    # 1. Load Persistent State (Crucial for Trailing Stops)
    state_db = load_state()
    
    cash, buying_power = get_account_cash(trader)
    print(f"Cash: ${cash:.2f} | Buying Power: ${buying_power:.2f}")

    for symbol in symbols:
        try:
            # --- A. Smart Fetch (Last 100 Days) ---
            end_dt = datetime.now(timezone.utc)
            start_dt = end_dt - timedelta(days=100)
            
            # Use the robust load_bars from data/feed.py
            df = load_bars(stock_client, crypto_client, symbol, "1Day", start_dt, end_dt)
            
            if df.empty or len(df) < 50:
                print(f"Skipping {symbol}: Insufficient data (Rows: {len(df)})")
                continue
                
            # --- B. Calculate Indicators ---
            df = prepare_data(df)
            latest = df.iloc[-1]
            current_price = latest['close']
            
            # --- C. Build Context ---
            qty_held, avg_entry = get_position_details(trader, symbol)
            
            # Retrieve Symbol State from DB
            sym_state = state_db.get(symbol, {
                "highest_price": 0.0, 
                "entry_price": 0.0,
                "cooldown": 0
            })
            
            # Sync DB with Reality
            if qty_held == 0:
                sym_state["highest_price"] = 0.0
                sym_state["entry_price"] = 0.0
            else:
                if current_price > sym_state["highest_price"]:
                    sym_state["highest_price"] = current_price
                if sym_state["entry_price"] == 0:
                    sym_state["entry_price"] = avg_entry
            
            # Decrement Cooldown
            if sym_state["cooldown"] > 0:
                sym_state["cooldown"] -= 1

            # Prepare Context
            context = {
                "holdings": qty_held,
                "entry_price": sym_state["entry_price"],
                "highest_price": sym_state["highest_price"],
                "cooldown": sym_state["cooldown"]
            }
            
            # --- D. Get Strategy Decision ---
            equity = cash + (qty_held * current_price)
            action = get_decision(latest, context, symbol, equity)
            
            if action != "HOLD":
                print(f"{symbol}: {action} signal at ${current_price:.2f}")

            # --- E. Execute Orders ---
            
            # BUY LOGIC
            if action == "BUY" and qty_held == 0:
                
                # SMART BUFFER LOGIC
                if "/" in symbol:
                    # CRYPTO: 2% Buffer (Fees + Volatility)
                    buffer = 0.98
                else:
                    # STOCKS: 1% Buffer (Market Order Safety)
                    buffer = 0.99
                
                alloc_amount = buying_power * buffer
                
                # Check if we have enough cash to buy at least 1 unit (or fractional)
                if alloc_amount > (current_price * 0.01):
                    qty_to_buy = alloc_amount / current_price
                    qty_to_buy = float(round(qty_to_buy, 4))
                    
                    if qty_to_buy > 0:
                        print(f"EXECUTING BUY: {symbol} x {qty_to_buy} (${alloc_amount:.2f})")
                        
                        req = MarketOrderRequest(
                            symbol=symbol,
                            qty=qty_to_buy,
                            side=OrderSide.BUY,
                            time_in_force=TimeInForce.GTC
                        )
                        trader.submit_order(req)
                        
                        # Update State Immediately
                        sym_state["entry_price"] = current_price
                        sym_state["highest_price"] = current_price
            
            # SELL LOGIC
            elif action == "SELL" and qty_held > 0:
                print(f"EXECUTING SELL: {symbol} x {qty_held}")
                
                req = MarketOrderRequest(
                    symbol=symbol,
                    qty=qty_held,
                    side=OrderSide.SELL,
                    time_in_force=TimeInForce.GTC
                )
                trader.submit_order(req)
                
                # Reset State
                sym_state["entry_price"] = 0.0
                sym_state["highest_price"] = 0.0
                sym_state["cooldown"] = 5 

            # Save updated state back to DB object
            state_db[symbol] = sym_state
            
        except Exception as e:
            print(f"Error processing {symbol}: {e}")
            
    # Save DB to file at end of cycle
    save_state(state_db)
    print("--- Cycle Complete ---")