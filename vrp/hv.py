# hv.py
import pandas as pd
import numpy as np

def _close_to_close_hv(prices: pd.Series, window: int) -> pd.Series:
    # Step 1: compute log returns
    # Step 2: compute rolling std over `window` trading days
    # Step 3: annualize
    log_returns = np.log(prices / prices.shift(1))
    rolling_vol = log_returns.rolling(window=window).std(ddof=1)

    return rolling_vol * np.sqrt(252)

_HV_METHODS = {
    "close_to_close": _close_to_close_hv,
    # future methods get registered here
}

def compute_hv(prices: pd.Series, window: int, method: str = "close_to_close") -> pd.Series:
    # dispatch to the right method, raise a clear error if method is unknown
    if method not in _HV_METHODS:
        raise ValueError(
            f'Unknown HV method "{method}". '
            f'Valid options are: {list(_HV_METHODS.keys())}'
        )
    return _HV_METHODS[method](prices, window)

def get_current_hv(prices: pd.Series, window: int, method: str = "close_to_close") -> float:
    # call compute_hv and return the last non-null value
    series = compute_hv(prices, window, method)
    if series.empty:
        raise ValueError(f"Not enough data to compute HV with window={window}. Need at least {window+1} prices.")
    
    return float(series.iloc[-1])

def get_avg_hv(prices: pd.Series, window: int, method: str = "close_to_close") ->float:
    return float(compute_hv(prices, window, method).mean())
