# iv.py
import numpy as np
import pandas as pd
from scipy.stats import norm
import yfinance as yf
from datetime import datetime, timedelta


def get_atm_iv(ticker: str, target_dte, r: float = 0.05) -> tuple[float, float, float]:
    calls, puts, S, closest_exp = fetch_chain(ticker, target_dte)
    actual_dte = (datetime.strptime(closest_exp, "%Y-%m-%d") - datetime.today()).days
    T = actual_dte / 365
    
    calls_filtered = calls[(calls['bid'] > 0) & (calls['ask'] > 0) & (calls['openInterest'] > 0)]
    atm_call = calls_filtered.iloc[(calls_filtered['strike'] - S).abs().argsort().iloc[0]]

    puts_filtered = puts[(puts['bid'] > 0) & (puts['ask'] > 0) & (puts['openInterest'] > 0)]
    atm_put = puts_filtered.iloc[(puts_filtered['strike'] - S).abs().argsort().iloc[0]]

    call_market_price = (atm_call['bid'] + atm_call['ask']) / 2
    put_market_price = (atm_put['bid'] + atm_put['ask']) / 2
    
    call_sigma = implied_volatility(call_market_price, S, atm_call['strike'], T, r, "call")
    put_sigma = implied_volatility(put_market_price, S, atm_put['strike'], T, r, "put")

    avg_iv = (call_sigma + put_sigma) / 2
    
    return avg_iv, call_sigma, put_sigma
    

def fetch_chain(ticker: str, target_dte: int) -> tuple[pd.DataFrame, pd.DataFrame, float, str]:
    # returns calls, puts, spot
    target_date = datetime.today() + timedelta(days=target_dte)
    tk = yf.Ticker(ticker)
    expirations = tk.options          # tuple of date strings
    
    closest_exp = min(expirations, key=lambda exp: abs(datetime.strptime(exp, "%Y-%m-%d") - target_date))

    
    spot = tk.fast_info['last_price']
    chain = tk.option_chain(closest_exp)  # curr 
    calls = chain.calls
    puts = chain.puts

    return calls, puts, spot, closest_exp
    


def implied_volatility(market_price: float, S: float, K: float, T: float, r: float, option_type="call") -> float:
    """
    f(sigma) = black_scholes_call(S, K, T, r, sigma) - market_price
    Vega=S⋅T⋅N'(d1)

    Sigma_n+1=Sigma_n-Vega(Sigma_n)f(Sigma_n)

    let sigma = 0.2
    continue calculating until |f(sigma)| <= threshold error
    """
    sigma = 0.2
    error = black_scholes(S, K, T, r, sigma, option_type) - market_price
    iterations = 0
    while abs(error) > 0.005:
        d1 = (np.log(S/K) + (r + np.square(sigma) / 2) * T) / (sigma * np.sqrt(T))
        vega = S * np.sqrt(T) * norm.pdf(d1)
        sigma = sigma - error / vega

        error = black_scholes(S, K, T, r, sigma, option_type) - market_price
        iterations += 1
        if iterations > 100:
            raise ValueError(f"IV solver did not converge after 100 iterations. Last sigma: {sigma:.4f}")
    
    return sigma


def black_scholes(S: float, K: float, T: float, r: float, sigma: float, option_type="call") -> float:
    """
    C=S⋅N(d1)-K⋅e-rT⋅N(d2)
    P = K⋅e-rT⋅N(-d2) - S⋅N(-d1)

    """
    multiplier = 1 if option_type == "call" else -1
    d1 = (np.log(S/K) + (r + np.square(sigma) / 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - (sigma * np.sqrt(T))
    

    return multiplier * (S * norm.cdf(multiplier * d1) - K * np.exp(-r * T) * norm.cdf(multiplier * d2))