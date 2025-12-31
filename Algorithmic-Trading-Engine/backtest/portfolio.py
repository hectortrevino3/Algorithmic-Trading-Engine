# backtest/portfolio.py
import pandas as pd
import os
from datetime import datetime, timedelta
from strategy.indicators import prepare_data

# Use the config defaults, but allow overrides
from config import RECURRING_INVESTMENT, DEFAULT_RECURRING_INVESTMENT

SLIPPAGE = 0.0003

def run_portfolio_simulation(ticker_data_map, initial_capital, strategy_module, dca_amount=None, dca_interval=None):
    
    # 1. PREPARE DATA
    processed_data = {}
    for symbol, df in ticker_data_map.items():
        # Ensure data is prepped (if not already)
        if 'sma_40' not in df.columns:
            pdf = prepare_data(df)
        else:
            pdf = df
            
        if not pdf.empty:
            processed_data[symbol] = pdf

    if not processed_data:
        return [], initial_capital

    all_dates = sorted(list(set().union(*[df.index for df in processed_data.values()])))
    
    # 2. SETUP ACCOUNTS & DCA
    cash = initial_capital
    holdings = None # Strict One Position
    ledger = []
    
    # --- DCA CONFIG ---
    config_amount = RECURRING_INVESTMENT.get("amount", DEFAULT_RECURRING_INVESTMENT["amount"])
    config_interval = RECURRING_INVESTMENT.get("interval_days", DEFAULT_RECURRING_INVESTMENT["interval_days"])

    # Priority: Function Args > Config File
    final_dca_amount = dca_amount if dca_amount is not None else config_amount
    final_dca_interval = dca_interval if dca_interval is not None else config_interval
    
    # Enable if amount > 0
    dca_enabled = (final_dca_amount > 0)
    
    # Calculate first deposit date
    if all_dates:
        next_deposit_date = all_dates[0] + timedelta(days=final_dca_interval)
    else:
        next_deposit_date = datetime.now() # Fallback

    total_invested = initial_capital

    # 3. MAIN LOOP
    for current_date in all_dates:
        
        # --- [A] RECURRING DEPOSIT LOGIC ---
        if dca_enabled and current_date >= next_deposit_date:
            cash += final_dca_amount
            total_invested += final_dca_amount
            
            # Calculate Total Balance for Log
            current_equity = cash
            if holdings and holdings['symbol'] in processed_data:
                # If we hold stock, add its value
                # We need the price for TODAY to show accurate balance in log
                sym = holdings['symbol']
                if current_date in processed_data[sym].index:
                    price_now = processed_data[sym].loc[current_date]['close']
                    current_equity += holdings['qty'] * price_now
            
            ledger.append({
                "Date": current_date, 
                "Action": "DEPOSIT", 
                "Symbol": "CASH", 
                "Price": final_dca_amount, 
                "PnL": 0, 
                "Balance": current_equity
            })
            
            # Schedule next deposit
            next_deposit_date += timedelta(days=final_dca_interval)


        # --- [B] EXIT LOGIC ---
        if holdings:
            symbol = holdings['symbol']
            # Only process if we have data for this symbol today
            if symbol in processed_data and current_date in processed_data[symbol].index:
                df = processed_data[symbol]
                row = df.loc[current_date]
                
                # Calculate current equity for the strategy to see
                current_val = cash + (holdings['qty'] * row['close'])
                
                # CALL STRATEGY (With Persistent State)
                decision, _, new_state, _ = strategy_module.get_decision(row, holdings['state'], symbol, current_val)
                holdings['state'] = new_state
                
                if decision == "SELL_SIGNAL":
                    sell_price = row['close'] * (1 - SLIPPAGE)
                    revenue = holdings['qty'] * sell_price
                    profit = revenue - holdings['cost_basis']
                    cash += revenue
                    ledger.append({
                        "Date": current_date, 
                        "Action": "SELL", 
                        "Symbol": symbol, 
                        "Price": sell_price, 
                        "PnL": profit, 
                        "Balance": cash
                    })
                    holdings = None

        # --- [C] ENTRY LOGIC ---
        # Only buy if we aren't holding anything and have Cash
        if holdings is None and cash > 0:
            best_score = -1
            best_pick = None
            
            # Scan all symbols to find the best one
            for symbol, df in processed_data.items():
                if current_date in df.index:
                    row = df.loc[current_date]
                    # Pass empty state {} because we are not in a position
                    decision, _, _, score = strategy_module.get_decision(row, {}, symbol, cash)
                    
                    if decision == "BUY_SIGNAL" and score > best_score:
                        best_score = score
                        best_pick = {"symbol": symbol, "price": row['close']}
            
            if best_pick:
                buy_price = best_pick['price'] * (1 + SLIPPAGE)
                qty = cash / buy_price # ALL IN
                
                if qty > 0:
                    holdings = {
                        "symbol": best_pick['symbol'], 
                        "qty": qty, 
                        "cost_basis": cash, 
                        # Initialize State
                        "state": {
                            "position": 1, 
                            "highest_price": buy_price, 
                            "entry_price": buy_price, 
                            "cooldown": 0
                        }
                    }
                    cash = 0
                    ledger.append({
                        "Date": current_date, 
                        "Action": "BUY", 
                        "Symbol": best_pick['symbol'], 
                        "Price": buy_price, 
                        "PnL": 0, 
                        "Balance": 0
                    })

    # 4. FINAL TALLY
    final_value = cash
    if holdings and holdings['symbol'] in processed_data:
        sym = holdings['symbol']
        last_price = processed_data[sym].iloc[-1]['close']
        final_value = holdings['qty'] * last_price
    
    # Store Total Invested for the Writer to calculate ROI
    ledger.append({"TOTAL_INVESTED": total_invested})
    
    return ledger, final_value

def write_portfolio_backtest(ledger, final_equity, strategy_name, period_label, universe_name):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder = os.path.join("backtest", "results", strategy_name)
    os.makedirs(folder, exist_ok=True)
    
    # Extract Total Invested if hidden in ledger
    total_invested = 1000.0 # fallback
    if ledger and isinstance(ledger[-1], dict) and "TOTAL_INVESTED" in ledger[-1]:
        total_invested = ledger.pop()['TOTAL_INVESTED']

    roi = ((final_equity - total_invested) / total_invested) * 100 if total_invested > 0 else 0
    
    filename = f"backtest_{universe_name}_{period_label}_{ts}.txt"
    path = os.path.join(folder, filename)
    
    with open(path, "w") as f:
        f.write(f"STRATEGY: {strategy_name}\n")
        f.write(f"UNIVERSE: {universe_name}\n")
        f.write(f"PERIOD:   {period_label}\n")
        f.write(f"INVESTED: ${total_invested:,.2f}\n")
        f.write(f"FINAL:    ${final_equity:,.2f}\n")
        f.write(f"RETURN:   {roi:.2f}%\n")
        f.write("-" * 65 + "\n")
        
        for t in ledger:
            date_str = t['Date'].strftime('%Y-%m-%d')
            
            if t['Action'] == "DEPOSIT":
                f.write(f"{date_str} | {t['Action']:<7} | {t['Symbol']:<6} | {t['Price']:<8.2f} | +{t['Price']:<7.2f} | {t['Balance']:.2f}\n")
            else:
                pnl = f"{t['PnL']:,.2f}" if t['PnL'] != 0 else "-"
                # Handle balance display for BUY
                bal = t['Balance']
                f.write(f"{date_str} | {t['Action']:<7} | {t['Symbol']:<6} | {t['Price']:<8.2f} | {pnl:<8} | {bal:.2f}\n")
                
    print(f"Log: {path}")