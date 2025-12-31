# backtest/fees.py

def crypto_fee(notional):
    """
    Alpaca crypto fee:
    0.15% per side (maker/taker blended)
    """
    return notional * 0.0025


def stock_fee(notional):
    """
    Alpaca stock fee:
    $0 commission, SEC + FINRA negligible -> ignored
    """
    return 0.0

