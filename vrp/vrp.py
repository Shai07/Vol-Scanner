# vrp.py
from iv import get_atm_iv
from hv import get_current_hv, get_avg_hv
import yfinance as yf
from typing import NamedTuple

class VRPResult(NamedTuple):
    vrp_current: float # IV - Current_IV
    vrp_average: float # IV - Average_IV
    iv: float
    hv_current: float
    hv_avg: float
    ticker: str
    hv_window: int
    target_dte: int

def compute_vrp(ticker: str, hv_window: int, lookback: float, target_dte: int, r: float = 0.05) -> VRPResult:
    # 1. fetch price history
    # 2. compute current HV
    # 3. compute ATM IV
    # 4. return VRP = IV - HV

    tk = yf.Ticker(ticker)
    hist = tk.history(period=f"{lookback}d")
    prices = hist["Close"]

    
    atm_iv = get_atm_iv(ticker, target_dte, r)[0]
    historical_vol = get_current_hv(prices, hv_window)
    average_vol = get_avg_hv(prices, hv_window)
    result = VRPResult(vrp_current=(atm_iv - historical_vol), vrp_average=(atm_iv - average_vol), iv=atm_iv, hv_current=historical_vol, hv_avg=average_vol, ticker=ticker, hv_window=hv_window, target_dte=target_dte)
    
    return result
