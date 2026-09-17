import pandas as pd
import yfinance as yf


def fetch_stock_data(ticker, period="6m", interval="1d"):
    """Fetch historical stock data along with current live price."""
    stock = yf.Ticker(ticker)
    df = stock.history(period=period, interval=interval)

    # Fetch live real-time price (Current Price / LTP)
    # yfinance provides live price via fast_info or info
    try:
        current_price = stock.fast_info["lastPrice"]
    except Exception:
        current_price = df["Close"].iloc[-1]  # Fallback to last close

    return df, round(current_price, 2)


def run_scanner_and_backtest(tickers):
    backtest_results = []
    live_scan_results = []

    for ticker in tickers:
        df, current_price = fetch_stock_data(ticker)

        if df.empty:
            continue

        # Simple Technical Strategy: 20-day Simple Moving Average (SMA)
        df["SMA20"] = df["Close"].rolling(window=20).mean()

        # ----------------------------------------------------
        # 1. BACKTEST LOGIC (Historical Signal Check)
        # ----------------------------------------------------
        # Look for past signals (e.g., Close crossed above SMA20)
        for i in range(1, len(df)):
            if (
                df["Close"].iloc[i - 1] <= df["SMA20"].iloc[i - 1]
                and df["Close"].iloc[i] > df["SMA20"].iloc[i]
            ):
                backtest_results.append(
                    {
                        "Ticker": ticker,
                        "Date": df.index[i].strftime("%Y-%m-%d"),
                        "Signal": "BUY",
                        "Signal Price": round(
                            df["Close"].iloc[i], 2
                        ),  # Price on signal date
                        "Current Price": current_price,  # Latest real-time price
                    }
                )

        # ----------------------------------------------------
        # 2. LIVE SCAN LOGIC (Current Bar / Today's Scan)
        # ----------------------------------------------------
        latest_bar = df.iloc[-1]
        prev_bar = df.iloc[-2]

        is_buy_signal = (
            prev_bar["Close"] <= prev_bar["SMA20"]
            and current_price > latest_bar["SMA20"]
        )

        live_scan_results.append(
            {
                "Ticker": ticker,
                "Current Price": current_price,  # Latest market price
                "SMA20": round(latest_bar["SMA20"], 2),
                "Status": "BUY TRIGGERED" if is_buy_signal else "NEUTRAL",
            }
        )

    # Convert to DataFrames for dynamic display
    df_backtest = pd.DataFrame(backtest_results)
    df_live = pd.DataFrame(live_scan_results)

    return df_backtest, df_live


# Define stock watchlist
symbols = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS"]

# Execute scanner & backtest
df_backtest, df_live = run_scanner_and_backtest(symbols)

print("=== BACKTEST RESULTS WITH CURRENT PRICE ===")
print(df_backtest.to_string(index=False))

print("\n=== LIVE SCAN RESULTS WITH CURRENT PRICE ===")
print(df_live.to_string(index=False))
