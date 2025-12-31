# Contributing to Algorithmic-Trading-Engine

Thanks for your interest in contributing! Please follow these guidelines to keep the repository safe and functional.

## Getting Started

1. **Fork the repo or clone it directly:**
```bash
git clone <repo-url>
cd Algorithmic-Trading-Engine

```

2. **Create a virtual environment:**
```bash
python -m venv env
source env/bin/activate   # Windows: env\Scripts\activate

```


3. **Install dependencies:**
```bash
pip install -r requirements.txt

```


4. **Add your Alpaca API credentials** in `API_Key&Secret.txt` (do not commit this file).

## Branching & Workflow

* **Work on a separate branch for each feature or fix:**
```bash
git checkout -b feature/my-feature

```


* **Make sure your code runs locally before committing.**
* **Commit messages should be clear and concise:**
* *Example:* `Add RSI calculation to indicators.py`
* *Example:* `Fix KeyError on crypto symbol`



## Important Rules

* **Do not commit your virtual environment (`env/`) or API keys.**
* Do not commit large files like logs or model weights unless necessary.
* Use the `.gitignore` provided to avoid accidentally committing sensitive or unnecessary files.
* Test changes locally before pushing to your branch.

## Pull Requests

1. **Push your branch to GitHub:**
```bash
git push origin feature/my-feature

```


2. Open a pull request with a clear description of your changes.
3. Pull requests will be reviewed before merging into the main branch.

## Code Style

* Follow consistent Python style (PEP8 recommended).
* Keep functions modular and files organized according to the project structure.
* No weird characters/emojis.

---

> **Notes:**
> * This repository is designed for **paper trading**. Do not connect live funds without testing.
> * Be careful with secrets; **never share API keys publicly.**
