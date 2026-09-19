import os
import requests
import yfinance as yf
import pandas as pd

# Fetch credentials securely from GitHub environment variables
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram_alert(message):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("Telegram token or chat ID missing.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"Failed to send alert: {response.text}")
    except Exception as e:
        print(f"Error sending alert: {e}")

def check_market():
    # Customize your watch list or symbols to check here
    symbols = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]
    
    alert_triggered = False

    for sym in symbols:
        try:
            ticker = yf.Ticker(sym)
            df = ticker.history(period="2d", interval="5m")
            if df.empty or len(df) < 15:
                continue
                
            cmp = round(float(df.iloc[-1]["Close"]), 2)
            prev_high = round(float(df.iloc[:-1]["High"].tail(10).max()), 2)
            
            # Simple breakout check example
            if cmp > prev_high:
                msg = f"🚨 *RS1408_stock_bot Alert*\n\nSymbol: `{sym}`\nPrice: `₹{cmp}`\nTrigger: Crossed Rolling High!"
                send_telegram_alert(msg)
                alert_triggered = True
        except Exception as e:
            print(f"Error processing {sym}: {e}")
            
    if not alert_triggered:
        print("Scan completed: No breakouts matched at this time.")

if __name__ == "__main__":
    check_market()
