# Algorithmic-Trading-Engine

Professional algorithmic trading framework for Stocks & Crypto using the Alpaca API.

This system serves as a "Commander" interface that allows for modular strategy selection, batch backtesting, and live paper trading. 

## Project Structure

- `main.py` - **The Commander.** The main interface that handles the menu, orchestrates batch backtesting, and manages the live trading loop.
- `strategy/loader.py` - Dynamic module loader that allows switching between strategies.
- `strategy/indicators.py` - **Technical Library.** Computes the core math and prepares the dataframes for the strategies.
- `data/feed.py` - **Smart Fetch Engine.** Loads historical data with UTC sanitization, strict API compliance (15-min delay for free plans), and auto-caching.
- `backtest/portfolio.py` - Simulation engine that handles PnL calculations, slippage (0.03%), and generates batch reports.
- `execution/trader.py` - Handles buy/sell orders via Alpaca API.
- `config.py` - Manages global settings, asset lists, and API credentials.
- `settings.json` - User-configurable parameters for capital, universe, and default strategy.

## Setup

1. Clone the repo
```bash
git clone <repo-url>
cd Algorithmic-Trading-Engine

```

2. Create a virtual environment and install dependencies

```bash
python -m venv env
source env/bin/activate  # Windows: env\Scripts\activate
pip install pandas numpy alpaca-py scikit-learn

```

*(Note: If you have a `requirements.txt`, you can use `pip install -r requirements.txt`)*

3. Add your Alpaca API credentials
Create a file named `API_Key&Secret.txt` in the root folder.

**Format:**

```text
Key: YOUR_API_KEY
Sec: YOUR_API_SECRET
```

4. Usage

```bash
python main.py

```

*This will start the trading bot (paper trading recommended). Press Ctrl+C to stop.*

5. Notes

* Crypto trades run 24/7.
* Stock trades only during market hours (config.py).
* `env/` is ignored to keep repo clean.
