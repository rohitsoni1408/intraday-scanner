import os
import json
import time
from datetime import datetime
import concurrent.futures
import requests
import pandas as pd
import yfinance as yf

# Telegram Configuration from GitHub Secrets
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

STATE_FILE = "sent_intraday_stocks.json"

def send_telegram_message(message):
    """Sends an alert message to the configured Telegram chat."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials missing!")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"Telegram API Error: {response.text}")
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

def load_sent_state():
    """Loads state to avoid duplicate intraday alerts during the same session."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_sent_state(state):
    """Saves the current alert state to disk."""
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)
    except Exception as e:
        print(f"Failed to save state: {e}")

def get_nifty_750_pool():
    """
    Returns the comprehensive pool of NSE stocks (Top 750 universe).
    You can expand or link this to your custom stock ticker list.
    """
    # Example representation for top NSE liquid tickers. 
    # Replace or extend with your complete list of 750 NSE symbols ending with '.NS'
    try:
        url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
        # Fallback or direct load logic if using local CSV/dynamic fetch
        df = pd.read_csv(url)
        symbols = [str(sym).strip() + ".NS" for sym in df['Symbol'].tolist()]
        return symbols[:750]
    except Exception:
        # Fallback sample list if network fetch fails
        sample_stocks = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS"]
        return sample_stocks

def scan_intraday_stock(ticker):
    """Scans an individual stock for intraday volume and price breakouts."""
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="5d", interval="15m")
        if df.empty or len(df) < 10:
            return None
        
        current_price = df['Close'].iloc[-1]
        prev_volume = df['Volume'].iloc[-2]
        curr_volume = df['Volume'].iloc[-1]
        
        # Intraday breakout condition (e.g., volume spike with upward momentum)
        if curr_volume > (prev_volume * 2.5) and current_price > df['High'].iloc[-2]:
            return {
                "ticker": ticker,
                "price": current_price,
                "type": "INTRADAY"
            }
    except Exception:
        pass
    return None

def scan_weekly_stock(ticker):
    """
    Scans an individual stock for multi-month structural base breakouts.
    Strictly uses confirmed market CLOSING prices, ignoring all intraday noise.
    """
    try:
        stock = yf.Ticker(ticker)
        # Fetch daily or weekly historical data to evaluate structural closes
        df = stock.history(period="1y", interval="1d")
        if df.empty or len(df) < 100:
            return None
        
        # Resample or extract weekly closing data
        weekly_df = df['Close'].resample('W').last().dropna()
        if len(weekly_df) < 12:
            return None
            
        # Multi-month structural high (e.g., past 24 weeks high)
        weekly_high = weekly_df.iloc[-24:-1].max()
        
        # STRICT CLOSING PRICE CHECK: Using latest confirmed market close only
        latest_close = df['Close'].iloc[-1]
        
        if latest_close >= (weekly_high * 0.95):
            return {
                "ticker": ticker,
                "close_price": latest_close,
                "weekly_high": weekly_high,
                "type": "WEEKLY"
            }
    except Exception:
        pass
    return None

def main():
    print("Initializing Full 750 NSE Stock Scanner...")
    stocks = get_nifty_750_pool()
    print(f"Loaded {len(stocks)} stocks into scanning pool.")
    
    # Determine scan type based on time or execution argument
    # (Weekly scan runs around 8:30 AM IST / Pre-market close evaluation)
    current_hour = datetime.now().hour
    is_weekly_schedule = (current_hour < 9) # Runs during early morning schedule
    
    matches = []
    
    if is_weekly_schedule:
        print("Running Weekly Structural Base Scan (Strict Closing Basis)...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            results = executor.map(scan_weekly_stock, stocks)
            for r in results:
                if r:
                    matches.load if hasattr(matches, 'load') else matches.append(r) # standard append
        
        if matches:
            msg = "🚀 *WEEKLY STRUCTURAL BASE BREAKOUTS (750 NSE)* 🚀\n\n"
            for m in matches:
                msg += f"• *{m['ticker']}*\n  Close: ₹{m['close_price']:.2f} | Base High: ₹{m['weekly_high']:.2f}\n\n"
            send_telegram_message(msg)
        else:
            print("No weekly setup matches found across the 750 stocks based on closing prices.")
            
    else:
        print("Running Intraday Volume Breakout Scan...")
        sent_state = load_sent_state()
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            results = executor.map(scan_intraday_stock, stocks)
            for r in results:
                if r:
                    t = r['ticker']
                    if sent_state.get(t) != today_str:
                        matches.append(r)
                        sent_state[t] = today_str
                        
        save_sent_state(sent_state)
        
        if matches:
            msg = "⚡ *INTRADAY VOLUME BREAKOUT ALERT* ⚡\n\n"
            for m in matches:
                msg += f"• *{m['ticker']}* @ ₹{m['price']:.2f}\n"
            send_telegram_message(msg)
        else:
            print("No intraday breakout matches found in this cycle.")

if __name__ == "__main__":
    main()
