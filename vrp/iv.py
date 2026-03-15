import numpy as np
import pandas as pd
from soupsieve import closest
from scipy.stats import norm


def get_atm_iv(chain, spot: float, target_dte, method="nearest_strike") -> float:
    pass


def implied_volatility(market_price: float, S: float, K: float, T: float, r: float) -> float:
    """
    f(sigma) = black_scholes_call(S, K, T, r, sigma) - market_price
    Vega=S⋅T⋅N'(d1)

    Sigma_n+1=Sigma_n-Vega(Sigma_n)f(Sigma_n)

    let sigma = 0.2
    continue calculating until |f(sigma)| <= threshold error
    """
    sigma = 0.2
    error = black_scholes_call(S, K, T, r, sigma) - market_price
    iterations = 0
    while abs(error) > 0.005:
        d1 = (np.log(S/K) + (r + np.square(sigma) / 2) * T) / (sigma * np.sqrt(T))
        vega = S * np.sqrt(T) * norm.pdf(d1)
        sigma = sigma - error / vega

        error = black_scholes_call(S, K, T, r, sigma) - market_price
        iterations += 1
        if iterations > 100:
            raise ValueError(f"IV solver did not converge after 100 iterations. Last sigma: {sigma:.4f}")
    
    return sigma


def black_scholes_call(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """
    C=S⋅N(d1)-K⋅e-rT⋅N(d2)

    """
    d1 = (np.log(S/K) + (r + np.square(sigma) / 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - (sigma * np.sqrt(T))
    

    return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)

price = black_scholes_call(S=100, K=100, T=30/365, r=0.05, sigma=0.25)
print(price)
recovered_sigma = implied_volatility(price, S=100, K=100, T=30/365, r=0.05)
print(recovered_sigma)

    