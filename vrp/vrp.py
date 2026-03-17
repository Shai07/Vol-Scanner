# vrp.py
from iv import get_atm_iv
from hv import get_current_hv
import yfinance as yf
from typing import NamedTuple

class VRPResult(NamedTuple):
    vrp: float
    iv: float
    hv: float
    ticker: str
    hv_window: int
    target_dte: int

def compute_vrp(ticker: str, hv_window: int, target_dte: int, r: float = 0.05) -> VRPResult:
    # 1. fetch price history
    # 2. compute current HV
    # 3. compute ATM IV
    # 4. return VRP = IV - HV
    years_needed = (hv_window / 252) + 0.5
    period = f"{max(1, round(years_needed))}y"


    tk = yf.Ticker(ticker)
    hist = tk.history(period=period)
    prices = hist["Close"]

    
    atm_iv = get_atm_iv(ticker, target_dte, r)[0]
    historical_vol = get_current_hv(prices, hv_window)
    result = VRPResult(vrp=(atm_iv - historical_vol), iv=atm_iv, hv=historical_vol, ticker=ticker, hv_window=hv_window, target_dte=target_dte)
    
    return result



result = compute_vrp("SPY", 252, 30)
print(f"Ticker:     {result.ticker}")
print(f"IV (30d):   {result.iv:.2%}")
print(f"HV (252d):  {result.hv:.2%}")
print(f"VRP:        {result.vrp:.2%}")