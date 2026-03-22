# Vol-Scanner

A modular volatility analysis toolkit for equity options. Currently includes a **Volatility Risk Premium (VRP) scanner** that identifies mispricings between implied and realized volatility across a user-defined watchlist.

---

## Project Structure

```
Vol-Scanner/
└── vrp/
    ├── hv.py           # Historical volatility engine
    ├── iv.py           # Implied volatility extraction pipeline
    ├── vrp.py          # VRP computation and result model
    ├── scanner.py      # Watchlist scanner and terminal output
    └── config.json     # User configuration
```

More scanner types will be added in future releases.

---

## What is the Volatility Risk Premium?

The VRP is the difference between **implied volatility (IV)** — what the options market prices in — and **historical volatility (HV)** — what volatility has actually been:

```
VRP = IV − HV
```

A **positive VRP** means options are expensive relative to realized vol — historically favorable for vol sellers.  
A **negative VRP** means options are cheap relative to realized vol — potentially favorable for vol buyers.

---

## Modules

### `hv.py` — Historical Volatility Engine

Computes rolling historical volatility from daily close prices using a modular, extensible design. New HV methods (Parkinson, Yang-Zhang, etc.) can be added by registering them in `_HV_METHODS` without changing any other code.

**Key functions:**
- `compute_hv(prices, window, method)` → `pd.Series` of rolling annualized HV
- `get_current_hv(prices, window, method)` → latest HV as a single float
- `get_avg_hv(prices, window, method)` → mean HV over the provided price history

Currently supported methods: `close_to_close`

---

### `iv.py` — Implied Volatility Pipeline

Extracts ATM implied volatility from live options chain data via Yahoo Finance. Implements Black-Scholes pricing and a Newton-Raphson IV solver from scratch.

**Key functions:**
- `black_scholes(S, K, T, r, sigma, option_type)` → theoretical option price
- `implied_volatility(market_price, S, K, T, r, option_type)` → IV via Newton-Raphson
- `fetch_chain(ticker, target_dte)` → pulls live options chain, selects closest expiry
- `get_atm_iv(ticker, target_dte, r)` → returns `(avg_iv, call_iv, put_iv)`

ATM IV is computed as the average of the call and put IV at the nearest strike to spot, using bid-ask midpoint prices.

---

### `vrp.py` — VRP Computation

Wires together `hv.py` and `iv.py` into a single result object.

**Key function:**
```python
compute_vrp(ticker, hv_window, lookback, target_dte, r) -> VRPResult
```

**`VRPResult` fields:**

| Field | Description |
|---|---|
| `vrp_current` | IV minus current HV |
| `vrp_average` | IV minus average HV over lookback |
| `iv` | ATM implied volatility |
| `hv_current` | Most recent rolling HV value |
| `hv_avg` | Mean rolling HV over lookback period |
| `ticker` | Ticker symbol |
| `hv_window` | Rolling window used for HV (calendar days) |
| `lookback` | Lookback period for avg HV (calendar days) |
| `target_dte` | Target days to expiration for IV |

---

### `scanner.py` — Watchlist Scanner

Reads `config.json`, runs `compute_vrp` for each ticker across all configured expiries, and prints a ranked terminal table with flags for unusual readings. Failed tickers or expiries are skipped gracefully with a warning.

**Run the scanner:**
```bash
cd vrp
python3 scanner.py
```

**Example output:**
```
Ticker         IV   TTE   HV Current     HV Avg  VRP Current    VRP Avg     Flag
──────────────────────────────────────────────────────────────────────────────────
TSLA       49.22%    30       31.83%     42.93%       17.39%      6.29%   ⚠ HIGH
TSLA       48.99%    45       31.83%     42.93%       17.15%      6.05%   ⚠ HIGH
META       42.74%    45       26.55%     32.80%       16.19%      9.94%   ⚠ HIGH
GOOGL      34.47%    30       23.43%     26.66%       11.04%      7.81%   ⚠ HIGH
AAPL       25.34%    30       27.03%     22.22%       -1.70%      3.11%    ⚠ LOW
```

Results are sorted by `vrp_current` descending so the most interesting names surface at the top. Each ticker appears once per configured expiry, allowing term structure comparisons across the watchlist.

---

## Configuration

Edit `vrp/config.json` to customize the scanner:

```json
{
  "watchlist": ["SPY", "QQQ", "AAPL", "TSLA", "NVDA"],
  "hv_window": 30,
  "lookback": 180,
  "target_dte": [30, 45, 60, 90, 180],
  "risk_free_rate": 0.05,
  "flag_threshold": 0.05,
  "hv_method": "close_to_close"
}
```

| Parameter | Description |
|---|---|
| `watchlist` | List of ticker symbols to scan |
| `hv_window` | Rolling window for HV calculation (calendar days) |
| `lookback` | History window for average HV (calendar days) |
| `target_dte` | List of target expiries to scan (calendar days) |
| `risk_free_rate` | Risk-free rate used in Black-Scholes |
| `flag_threshold` | Flag if `VRP` exceeds this value (e.g. 0.05 = 5%). Positive triggers ⚠ HIGH, negative triggers ⚠ LOW |
| `hv_method` | HV calculation method (`close_to_close`) |

---

## Installation

```bash
git clone https://github.com/Shai07/Vol-Scanner.git
cd Vol-Scanner/
pip install -r requirements.txt
cd vrp
python3 scanner.py
```

**Dependencies:**
- `numpy`
- `pandas`
- `scipy`
- `yfinance`

---

## Methodology Notes

- **HV** is computed using close-to-close log returns, annualized by √252, with `ddof=1` (Bessel's correction)
- **IV** is extracted from live options chains using bid-ask midpoint prices, averaged across ATM call and put
- **T** in Black-Scholes uses calendar days / 365, consistent with market convention
- **VRP** is expressed as a decimal (e.g. 0.05 = 5 percentage points of annualized vol)
- Failed tickers or expiries (e.g. insufficient liquidity) are skipped with a warning and do not interrupt the scan

---

## Roadmap

- [ ] Additional HV methods (Parkinson, Garman-Klass, Yang-Zhang)
- [ ] Matplotlib visualizations of IV vs HV discrepancy per ticker
- [ ] Historical VRP time series using WRDS/OptionMetrics data
- [ ] Additional scanner types beyond VRP
