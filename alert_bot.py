from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import json
import os
import pandas as pd
import requests
import yfinance as yf

# Fetch credentials securely from GitHub environment variables
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# File to persist sent alerts for the day and avoid duplicates
ALERT_FILE = "sent_alerts.json"


def get_today_date():
  return datetime.now().strftime("%Y-%m-%d")


def load_sent_alerts():
  if os.path.exists(ALERT_FILE):
    try:
      with open(ALERT_FILE, "r") as f:
        data = json.load(f)
        if data.get("date") == get_today_date():
          return set(data.get("symbols", []))
    except Exception:
      pass
  return set()


def save_sent_alert(sym):
  today = get_today_date()
  sent_symbols = load_sent_alerts()
  sent_symbols.add(sym)
  try:
    with open(ALERT_FILE, "w") as f:
      json.dump({"date": today, "symbols": list(sent_symbols)}, f)
  except Exception as e:
    print(f"Error saving sent alert: {e}")


def send_telegram_alert(message):
  if not TELEGRAM_TOKEN or not CHAT_ID:
    print("Telegram token or chat ID missing.")
    return
  url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
  payload = {
      "chat_id": CHAT_ID,
      "text": message,
      "parse_mode": "Markdown",
      "disable_web_page_preview": True,
  }
  try:
    response = requests.post(url, json=payload)
    if response.status_code != 200:
      print(f"Failed to send alert: {response.text}")
  except Exception as e:
    print(f"Error sending alert: {e}")


def process_symbol(sym):
  try:
    clean_sym = sym.upper().replace(".NS", "").strip()
    ticker = yf.Ticker(f"{clean_sym}.NS")
    df_intraday = ticker.history(period="2d", interval="5m")
    
    if df_intraday.empty or len(df_intraday) < 15:
      return None

    cmp = round(float(df_intraday.iloc[-1]["Close"]), 2)
    if cmp < 50.0:
      return None

    # Calculate VWAP
    total_vol = df_intraday["Volume"].sum()
    vwap = (
        round(
            float(
                (df_intraday["Close"] * df_intraday["Volume"]).sum()
                / total_vol
            ),
            2,
        )
        if total_vol > 0
        else cmp
    )

    # Rolling levels matching the main app terminal engine
    recent_candles = df_intraday.iloc[:-1].tail(12)
    rolling_high = round(float(recent_candles["High"].max()), 2)
    rolling_low = round(float(recent_candles["Low"].min()), 2)

    # Volume Surge Filter aligned with main app
    vol_ma = df_intraday["Volume"].rolling(window=20).mean()
    curr_candle_vol = float(df_intraday["Volume"].iloc[-1])
    avg_vol_ma = float(vol_ma.iloc[-1]) if not vol_ma.empty and not pd.isna(vol_ma.iloc[-1]) else 0.0
    exceptional_vol = curr_candle_vol > (avg_vol_ma * 1.5) if avg_vol_ma > 0 else False

    # Alignment with Main App Breakout Condition
    is_bullish_breakout = (cmp > rolling_high) and (cmp > vwap) and exceptional_vol

    if is_bullish_breakout:
      sent_symbols = load_sent_alerts()
      if clean_sym in sent_symbols:
        return None

      entry_price = cmp
      sl = round(min(rolling_low, entry_price * 0.995), 2)
      risk = entry_price - sl
      target_1 = round(entry_price + (risk * 1.5), 2)
      target_2 = round(entry_price + (risk * 3.0), 2)
      
      vol_multiplier = round(curr_candle_vol / avg_vol_ma, 1) if avg_vol_ma > 0 else 1.0
      chart_url = f"https://www.tradingview.com/chart/?symbol=NSE:{clean_sym}"

      msg = (
          f"🚨 *Ultimate Confluence Breakout Alert*\n\n"
          f"📌 *Stock:* `{clean_sym}`\n"
          f"💰 *Entry Price:* `₹{entry_price}`\n"
          f"🌊 *VWAP:* `₹{vwap}` | 🚀 *Rolling High:* `₹{rolling_high}`\n"
          f"🛑 *Stop Loss (SL):* `₹{sl}`\n"
          f"🎯 *Target 1:* `₹{target_1}` | *Target 2:* `₹{target_2}`\n"
          f"📦 *Volume Spike:* `{vol_multiplier}x` average\n\n"
          f"📊 [View Live Chart]({chart_url})"
      )

      send_telegram_alert(msg)
      save_sent_alert(clean_sym)
      return clean_sym

  except Exception as e:
    pass
  return None


def check_market():
  # Synchronized with main terminal universe scope
  symbols = [
      "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", "BHARTIARTL", "SBIN", "LTIM", "ITC", "HINDUNILVR",
      "LT", "BAJFINANCE", "AXISBANK", "KOTAKBANK", "MARUTI", "SUNPHARMA", "TITAN", "ULTRACEMCO", "NTPC", "ONGC",
      "POWERGRID", "ASIANPAINT", "ADANIENT", "ADANIPORTS", "COALINDIA", "TATASTEEL", "HINDALCO", "GRASIM", "TECHM", "WIPRO",
      "BAJAJFINSV", "SBILIFE", "HDFCLIFE", "DIVISLAB", "CIPLA", "EICHERMOT", "BPCL", "TATAMOTORS", "HEROMOTOCO", "BRITANNIA",
      "INDUSINDBK", "JSWSTEEL", "APOLLOHOSP", "DRREDDY", "SHRIRAMFIN", "M&M", "NESTLEIND", "TATACONSUM", "BAJAJ-AUTO", "HCLTECH",
      "SBICARD", "PIDILITIND", "SRF", "ATGL", "ADANIGREEN", "ADANIPOWER", "HAL", "BEL", "IOC", "GAIL",
      "ZOMATO", "PAYTM", "NYKAA", "POLICYBZR", "DELHIVERY", "DMART", "LUPIN", "TORNTPHARM", "CANBK", "PNB"
  ]

  print(f"Starting parallel intraday institutional scan for {len(symbols)} stocks...")

  alert_triggered = False
  with ThreadPoolExecutor(max_workers=20) as executor:
    futures = {executor.submit(process_symbol, sym): sym for sym in symbols}
    for future in as_completed(futures):
      if future.result():
        alert_triggered = True

  if not alert_triggered:
    print("Scan completed silently: No institutional volume breakouts matched.")


if __name__ == "__main__":
  check_market()
