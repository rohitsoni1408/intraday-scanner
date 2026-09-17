import datetime
import pytz
import pandas as pd
import yfinance as yf

# -------------------------------------------------------------------
# Configuration & Watchlist
# -------------------------------------------------------------------
WATCHLIST = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "ICICIBANK.NS", "HDFCBANK.NS"]
TIMEZONE = pytz.timezone("Asia/Kolkata")

def is_market_open():
    """Checks if Indian markets (NSE/BSE) are currently open."""
    now = datetime.datetime.now(TIMEZONE)
    # Monday = 0, Sunday = 6
    if now.weekday() >= 5:
        return False
    
    market_start = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_end = now.replace(hour=15, minute=30, second=0, microsecond=0)
    return market_start <= now <= market_end

def scan_symbol(symbol, market_active):
    ticker = yf.Ticker(symbol)
    
    if market_active:
        # Fetch Intraday 5-min data for live scanning
        df = ticker.history(period="1d", interval="5m")
        if df.empty:
            return None
        
        latest_price = df['Close'].iloc[-1]
        high_20 = df['High'].tail(20).max()
        low_20 = df['Low'].tail(20).min()
        
        # Simple intraday breakout logic
        if latest_price >= high_20:
            signal = "LIVE BUY BREAKOUT"
            entry = latest_price
            sl = low_20
            target = entry + (entry - sl) * 1.5
        elif latest_price <= low_20:
            signal = "LIVE SELL BREAKOUT"
            entry = latest_price
            sl = high_20
            target = entry - (sl - entry) * 1.5
        else:
            return None
            
        return {
            "Symbol": symbol,
            "Mode": "Live Intraday",
            "Signal": signal,
            "Entry": round(entry, 2),
            "SL": round(sl, 2),
            "Target 1": round(target, 2),
            "Target 2": round(entry + (entry - sl) * 2.5 if "BUY" in signal else entry - (sl - entry) * 2.5, 2)
        }

    else:
        # Fetch Daily data for Next-Session Planning
        df = ticker.history(period="5d", interval="1d")
        if len(df) < 2:
            return None
        
        prev_day = df.iloc[-1]
        close = prev_day['Close']
        pdh = prev_day['High']
        pdl = prev_day['Low']
        atr = (pdh - pdl)  # Simple Daily Range as ATR substitute
        
        # Key Level Setup for Next Session
        # Long above PDH + Buffer; Short below PDL - Buffer
        buy_entry = pdh + (atr * 0.05)
        buy_sl = pdh - (atr * 0.3)
        buy_t1 = buy_entry + (atr * 0.8)
        buy_t2 = buy_entry + (atr * 1.5)
        
        sell_entry = pdl - (atr * 0.05)
        sell_sl = pdl + (atr * 0.3)
        sell_t1 = sell_entry - (atr * 0.8)
        sell_t2 = sell_entry - (atr * 1.5)

        return {
            "Symbol": symbol,
            "Mode": "Next Session Prep",
            "PDH (High)": round(pdh, 2),
            "PDL (Low)": round(pdl, 2),
            "Bullish Entry": round(buy_entry, 2),
            "Bullish SL": round(buy_sl, 2),
            "Bullish T1": round(buy_t1, 2),
            "Bearish Entry": round(sell_entry, 2),
            "Bearish SL": round(sell_sl, 2),
            "Bearish T1": round(sell_t1, 2),
        }

def run_scanner():
    active = is_market_open()
    status_str = "OPEN (Scanning Live)" if active else "CLOSED (Preparing Next Session Levels)"
    print(f"\n--- Market Status: {status_str} ---")
    
    results = []
    for sym in WATCHLIST:
        data = scan_symbol(sym, active)
        if data:
            results.append(data)
            
    if results:
        res_df = pd.DataFrame(results)
        print(res_df.to_string(index=False))
    else:
        print("No setup signals triggered.")

if __name__ == "__main__":
    run_scanner()
