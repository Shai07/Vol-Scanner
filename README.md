# Vol-Scanner

A modular volatility analysis toolkit for equity options. Currently includes a **Volatility Risk Premium (VRP) scanner** that identifies mispricings between implied and realized volatility across a user-defined watchlist.

---

## Project Structure

```
Vol-Scanner/
├── requirements.txt
└── vrp/
    ├── hv.py           # Historical volatility engine
    ├── iv.py           # Implied volatility extraction pipeline
    ├── vrp.py          # VRP computation and result model
    ├── scanner.py      # Watchlist scanner and terminal output
    ├── sectors.py      # Predefined sector baskets
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

### `sectors.py` — Sector Baskets

Contains predefined watchlists organized by market sector. Users select a sector in `config.json` rather than maintaining a manual ticker list, making intra-sector VRP comparisons straightforward.

Available sectors: `technology`, `biotechnology`, `healthcare`, `financials`, `energy`, `industrials`, `consumer_discretionary`, `consumer_staples`, `utilities`, `real_estate`, `materials`, `communication_services`, `defense`, `semiconductors`, `software`, `etfs`

Each basket contains 20 tickers. The `etfs` basket is useful as a broad market benchmark.

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

VRP Current by Ticker × TTE
──────────────────────────────────────────────────
Ticker           30d       45d       60d       90d      180d
──────────────────────────────────────────────────
TSLA          17.39%    17.15%    15.98%    14.86%    16.78%
META           9.47%    16.19%    14.60%    12.52%    12.70%
GOOGL         11.04%    14.63%    13.99%    12.69%    13.16%
WDC            8.88%    10.27%    12.57%       N/A     7.93%

VRP Average by Ticker × TTE
──────────────────────────────────────────────────
Ticker           30d       45d       60d       90d      180d
──────────────────────────────────────────────────
TSLA           6.29%     6.05%     4.88%     3.76%     5.68%
META           3.22%     9.94%     8.35%     6.27%     6.45%
GOOGL          7.81%    11.40%    10.76%     9.46%     9.93%
WDC           19.59%    20.98%    23.27%       N/A    18.64%
```

The scanner produces three views of the data:
- **Ranked table** — all (ticker, expiry) combinations sorted by `vrp_current` descending, with flags
- **VRP Current pivot** — each ticker's `vrp_current` across all expiries side by side, making term structure patterns immediately visible
- **VRP Average pivot** — same layout for `vrp_average`, showing how current VRP compares to the longer-run average

`N/A` appears when a ticker had no valid options data for a given expiry.

---

## Configuration

Edit `vrp/config.json` to customize the scanner:

```json
{
  "sector": "technology",
  "hv_window": 30,
  "use_custom_hv_window": false,
  "lookback": 180,
  "target_dte": [30, 45, 60, 75, 90, 105],
  "risk_free_rate": 0.05,
  "flag_threshold": 0.05,
  "hv_method": "close_to_close"
}
```

| Parameter | Description |
|---|---|
| `sector` | Sector basket to scan. Must match a key in `sectors.py` |
| `hv_window` | Rolling window for HV calculation (calendar days). Only used when `use_custom_hv_window` is `true` |
| `use_custom_hv_window` | If `false` (default), HV window matches each TTE for apples-to-apples comparison (30d IV vs 30d HV). If `true`, uses `hv_window` for all expiries |
| `lookback` | History window for average HV (calendar days) |
| `target_dte` | List of target expiries to scan (calendar days) |
| `risk_free_rate` | Risk-free rate used in Black-Scholes |
| `flag_threshold` | Flag if `VRP` exceeds this value (e.g. 0.05 = 5%). Positive triggers ⚠ HIGH, negative triggers ⚠ LOW |
| `hv_method` | HV calculation method (`close_to_close`) |

---

## Installation

```bash
git clone https://github.com/Shai07/Vol-Scanner.git
cd Vol-Scanner
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
