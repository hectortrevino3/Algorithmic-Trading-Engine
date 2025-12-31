# data/feed.py
import pandas as pd
from datetime import datetime, timezone
from alpaca.data.requests import StockBarsRequest, CryptoBarsRequest
from config import CRYPTO_LIST

def load_bars(stock_client, crypto_client, symbol, timeframe, start_date, end_date):
    """
    Universal Data Loader.
    Sanitizes dates to Naive UTC to prevent API timezone conflicts.
    """
    
    # --- DATE SANITIZATION ---
    # Convert to Naive UTC (strip timezone info but keep UTC time)
    # This prevents the "Invalid Date" or "Request Error" from Alpaca SDK
    if start_date.tzinfo is not None:
        start_date = start_date.astimezone(timezone.utc).replace(tzinfo=None)
    if end_date.tzinfo is not None:
        end_date = end_date.astimezone(timezone.utc).replace(tzinfo=None)

    # --- CRYPTO HANDLER ---
    if symbol in CRYPTO_LIST:
        request = CryptoBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=timeframe,
            start=start_date,
            end=end_date,
            limit=10000 
        )
        try:
            bars = crypto_client.get_crypto_bars(request)
            df = bars.df
        except Exception as e:
            print(f"   [Crypto Error: {e}]")
            return pd.DataFrame()
        
    # --- STOCK HANDLER ---
    else:
        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=timeframe,
            start=start_date,
            end=end_date,
            limit=10000,
            adjustment='split'
        )
        try:
            bars = stock_client.get_stock_bars(request)
            df = bars.df
        except Exception as e:
            # Reveal the error!
            print(f"   [Stock Error: {e}]")
            return pd.DataFrame()

    # Clean Index
    if not df.empty:
        df = df.reset_index()
        # Alpaca returns MultiIndex (symbol, timestamp). We want just timestamp rows.
        if 'symbol' in df.columns:
            df = df.drop(columns=['symbol'])
            
    return df