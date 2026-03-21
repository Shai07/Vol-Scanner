# scanner.py
import json
from vrp import compute_vrp, VRPResult

def load_config(path: str = "config.json") -> dict:
    try: 
        with open(path, "r") as f: 
            data = json.load(f)
            return data
    except FileNotFoundError:
        print(f"Config file not found at {path}")
        return {}
    except json.JSONDecodeError:
        print(f"Config file is not valid JSON")
        return {}
    

def run_scanner(config: dict) -> list[VRPResult]:
    # loop over watchlist, collect results
    # handle errors per ticker gracefully
    results = []
    for ticker in config["watchlist"]:
        try:
            for date in config["target_dte"]:
                results.append(compute_vrp(ticker, config["hv_window"], config["lookback"], date, config["risk_free_rate"]))
        except Exception as e:
            print(f"⚠ Skipping {ticker}: {e}")

    return results

def print_results(results: list[VRPResult], flag_threshold: float, flag_percentile: int) -> None:
    # sort by vrp_current descending
    # print header
    # print each row with flag if applicable
    results.sort(key= lambda tk: tk.vrp_current, reverse=True)
    # header
    print(f"{'Ticker':<8} {'IV':>8} {'TTE': >5} {'HV Current':>12} {'HV Avg':>10} {'VRP Current':>12} {'VRP Avg':>10} {'Flag':>6}")
    print("─" * 78)

    for result in results:
        flag = result.vrp_current >= flag_threshold
        print(f"{result.ticker:<8} {result.iv:>8.2%} {result.target_dte:>5} {result.hv_current:>12.2%} {result.hv_avg:>10.2%} {result.vrp_current:>12.2%} {result.vrp_average:>10.2%} {flag:>6}")


if __name__ == "__main__":
    config = load_config()
    results = run_scanner(config)
    print_results(results, config["flag_threshold"], config["flag_percentile"])
