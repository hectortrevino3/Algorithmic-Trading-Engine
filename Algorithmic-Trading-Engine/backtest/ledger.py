# backtest/ledger.py
from dataclasses import dataclass

@dataclass
class Trade:
    idx: int
    side: str
    dt: str
    conf: dict
    price: float
    pnl: float
    position: float
    cumulative_pnl: float

