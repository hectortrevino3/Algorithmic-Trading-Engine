# strategy/strategy1.py

def get_decision(row, state, symbol_name, equity):
    """
    SAMPLE STRATEGY
    """
    
    # 1. Setup State
    st = state.copy()
    if "position" not in st: st["position"] = 0.0
    if "entry_price" not in st: st["entry_price"] = 0.0
    
    # 2. Unpack Data
    close = row.get('close', 0.0)
    donchian_high = row.get('donchian_high', 0.0)
    donchian_low = row.get('donchian_low', 0.0)
    
    # 3. Entry Logic
    # logic: If price breaks the upper channel, buy. 
    if st["position"] == 0:
        if close > donchian_high:
            st["entry_price"] = close
            # Return "BUY_SIGNAL", quantity (0=calc auto), state, trade_score (default 1.0)
            return "BUY_SIGNAL", 0.0, st, 1.0

    # 4. Exit Logic
    # logic: If price breaks the lower channel, sell.
    if st["position"] > 0:
        if close < donchian_low:
            return "SELL_SIGNAL", 0.0, st, 0.0

    return "HOLD", 0.0, st, 0.0