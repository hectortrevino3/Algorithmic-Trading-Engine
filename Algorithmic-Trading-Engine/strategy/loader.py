# strategy/loader.py
import importlib

# Map string names to module filenames
STRATEGY_MAP = {
    "1": "strategy.strategy1",
    "2": "strategy.strategy1",
    "3": "strategy.strategy1",
    "strategy1": "strategy.strategy1",
    "strategy2": "strategy.strategy2",
    "strategy3": "strategy.strategy3"
}

def load_strategy(selection):
    sel = str(selection).strip().lower()
    module_name = STRATEGY_MAP.get(sel)
    
    try:
        mod = importlib.import_module(module_name)
        return mod
    except ImportError as e:
        print(f"Failed to load strategy {module_name}: {e}")
        return None

def get_strategy_name(selection):
    sel = str(selection).strip().lower()
    if "strategy1" in sel or sel == "1": return "STRATEGY1"
    if "strategy1" in sel or sel == "2": return "STRATEGY2"
    if "strategy1" in sel or sel == "3": return "STRATEGY3"
    return "UNKNOWN"