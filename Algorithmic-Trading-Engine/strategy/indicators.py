# strategy/indicators.py
import pandas as pd
import numpy as np

# --- Core Indicators (Only what is needed for Demo) ---

def DONCHIAN(df, period=20):
    """
    Shifted to prevent lookahead bias.
    Compares Today's Close to YESTERDAY'S High/Low.
    """
    d_high = df['high'].rolling(window=period).max().shift(1)
    d_low = df['low'].rolling(window=period).min().shift(1)
    return d_high, d_low

def prepare_data(df):
    """Unified Data Pipeline - Demo Version"""
    # Ensure column names are lower case for consistency
    df = df.rename(columns=str.lower)
    df = df.copy().sort_values("timestamp")
    
    # 1. Essential Trend Indicators
    df['donchian_high'], _ = DONCHIAN(df, period=20)
    _, df['donchian_low'] = DONCHIAN(df, period=10)
    
    # 2. Basic Moving Averages
    df["sma_50"] = df['close'].rolling(window=50).mean()

    # Note: Advanced oscillators have been removed for this public release.
    
    df = df.dropna()
    
    if 'timestamp' in df.columns:
        df.set_index('timestamp', inplace=True)
        
    return df