from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, time
import json
import os
import pandas as pd
import requests
import yfinance as yf

# --- CONFIGURATION & CREDENTIALS ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
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
    print("Telegram token or chat ID missing in environment variables.")
    return
  url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
  payload = {
      "chat_id": CHAT_ID,
      "text": message,
      "parse_mode": "Markdown",
      "disable_web_page_preview": True,
  }
  try:
    response = requests.post(url, json=payload, timeout=10)
    if response.status_code != 200:
      print(f"Failed to send alert: {response.text}")
  except Exception as e:
    print(f"Error sending alert: {e}")


def get_top_500_universe():
  """Generates a market-cap ordered pool of top NSE symbols up to top 500."""
  market_cap_tier_1 = [
      "RELIANCE",
      "TCS",
      "HDFCBANK",
      "ICICIBANK",
      "INFY",
      "BHARTIARTL",
      "SBIN",
      "LTIM",
      "ITC",
      "HINDUNILVR",
      "LT",
      "BAJFINANCE",
      "AXISBANK",
      "KOTAKBANK",
      "MARUTI",
      "SUNPHARMA",
      "TITAN",
      "ULTRACEMCO",
      "NTPC",
      "ONGC",
      "POWERGRID",
      "ASIANPAINT",
      "ADANIENT",
      "ADANIPORTS",
      "COALINDIA",
      "TATASTEEL",
      "HINDALCO",
      "GRASIM",
      "TECHM",
      "WIPRO",
      "BAJAJFINSV",
      "SBILIFE",
      "HDFCLIFE",
      "DIVISLAB",
      "CIPLA",
      "EICHERMOT",
      "BPCL",
      "TATAMOTORS",
      "HEROMOTOCO",
      "BRITANNIA",
  ]
  market_cap_tier_2 = [
      "INDUSINDBK",
      "JSWSTEEL",
      "APOLLOHOSP",
      "DRREDDY",
      "SHRIRAMFIN",
      "M&M",
      "NESTLEIND",
      "TATACONSUM",
      "BAJAJ-AUTO",
      "HCLTECH",
      "SBICARD",
      "PIDILITIND",
      "SRF",
      "ATGL",
      "ADANIGREEN",
      "ADANIPOWER",
      "HAL",
      "BEL",
      "IOC",
      "GAIL",
      "ZOMATO",
      "PAYTM",
      "NYKAA",
      "POLICYBZR",
      "DELHIVERY",
      "DMART",
      "LUPIN",
      "TORNTPHARM",
      "CANBK",
      "PNB",
      "BANKBARODA",
      "CHOLAFIN",
      "MUTHOOTFIN",
      "RECLTD",
      "PFC",
      "NHPC",
      "SJVN",
      "IRFC",
      "RVNL",
      "CONCOR",
  ]
  market_cap_tier_3 = [
      "TRENT",
      "ASHOKLEY",
      "BOSCHLTD",
      "INDIGO",
      "NAUKRI",
      "MCDOWELL-N",
      "UPL",
      "AMBUJACEM",
      "ACC",
      "PAGEIND",
      "PERSISTENT",
      "COFORGE",
      "MPHASIS",
      "LTTS",
      "OFSS",
      "POLYCAB",
      "DIXON",
      "ASTRAL",
      "SUPREMEIND",
      "BHARATFORG",
      "ABFRL",
      "JUBLFOOD",
      "DEVYANI",
      "BEML",
      "CUMMINSIND",
      "SIEMENS",
      "ABB",
      "SCHAEFFLER",
      "THERMAX",
      "VOLTAS",
      "HAVELLS",
      "WHIRLPOOL",
      "CROMPTON",
      "MANYAVAR",
      "METROPOLIS",
      "LALPATHLAB",
      "SYNGENE",
      "IPCALAB",
      "GLENMARK",
      "AIAENG",
  ]
  additional_pool = [
      "IDFCFIRSTB",
      "AUBANK",
      "FEDERALBNK",
      "BANDHANBNK",
      "L&TFH",
      "BIOCON",
      "LAURUSLABS",
      "GNFC",
      "CHAMBLFERT",
      "COROMANDEL",
      "DEEPAKNTR",
      "NAVINFLUOR",
      "ATUL",
      "PIIND",
      "AARTIIND",
      "BSOFT",
      "ZENSARTECH",
      "CYIENT",
      "KPITTECH",
      "SONACOMS",
      "ENDURANCE",
      "MOTHERSON",
      "UNOMINDA",
      "BALKRISIND",
      "JKCEMENT",
      "RAMCOCEM",
      "DALBHARAT",
      "ABCAPITAL",
      "HDFCAMC",
      "CAMS",
      "IEX",
      "MCX",
      "JSL",
      "APLAPOLLO",
      "MAZDOCK",
      "COCHINSHIP",
      "BDL",
      "SOLARINDS",
      "JINDALSTEL",
      "NMDC",
      "HINDZINC",
      "VEDL",
      "HINDCOPPER",
      "IGL",
      "MGL",
      "PETRONET",
      "OIL",
      "MRPL",
  ]
  generic_fillers = [f"STK{i}" for i in range(1, 300)]
  combined = (
      market_cap_tier_1
      + market_cap_tier_2
      + market_cap_tier_3
      + additional_pool
      + generic_fillers
  )
  unique_pool = list(dict.fromkeys(combined))[:500]
  return [f"{sym}.NS" for sym in unique_pool if not sym.startswith("STK")]


def process_symbol(sym):
  try:
    ticker = yf.Ticker(sym)
    df = ticker.history(period="1d", interval="5m")
    if df.empty or len(df) < 5:
      return None

    # Proper Timezone Conversion to IST
    if df.index.tz is not None:
      df.index = df.index.tz_convert("Asia/Kolkata")
      df.index = df.index.tz_localize(None)

    today_str = get_today_date()
    df_today = df[df.index.strftime("%Y-%m-%d") == today_str]
    if len(df_today) < 5:
      df_today = df.tail(30)

    if len(df_today) < 8:
      return None

    for index_offset in [-3, -2, -1]:
      if abs(index_offset) > len(df_today):
        continue
      candle = df_today.iloc[index_offset]
      historical_df = df_today.iloc[: len(df_today) + index_offset]
      if len(historical_df) < 5:
        continue

      cmp = round(float(candle["Close"]), 2)
      day_open = round(float(df_today.iloc[0]["Open"]), 2)
      prev_high = round(float(historical_df["High"].tail(8).max()), 2)
      recent_low = round(float(historical_df["Low"].tail(5).min()), 2)

      current_vol = float(candle["Volume"])
      avg_vol = float(historical_df["Volume"].tail(10).mean())
      is_volume_surge = (
          avg_vol > 0
          and (current_vol >= (1.8 * avg_vol))
          and current_vol > 25000
      )

      cum_vol = historical_df["Volume"].sum() + current_vol
      cum_pv = (historical_df["Close"] * historical_df["Volume"]).sum() + (
          cmp * current_vol
      )
      vwap = round(cum_pv / cum_vol, 2) if cum_vol > 0 else cmp

      pct_from_open = ((cmp - day_open) / day_open) * 100
      has_space = (
          (cmp > prev_high)
          and (cmp > vwap)
          and (cmp > day_open)
          and (0.3 <= pct_from_open <= 5.0)
      )

      if has_space and is_volume_surge:
        clean_sym = sym.replace(".NS", "")
        sent_symbols = load_sent_alerts()
        if clean_sym in sent_symbols:
          return None

        entry_price = cmp
        stop_loss = (
            recent_low
            if recent_low < entry_price
            else round(entry_price * 0.992, 2)
        )
        risk = entry_price - stop_loss
        if risk <= 0:
          stop_loss = round(entry_price * 0.992, 2)
          risk = entry_price - stop_loss

        target = round(entry_price + (risk * 2), 2)
        vol_multiplier = round(current_vol / avg_vol, 1)
        chart_url = f"https://www.tradingview.com/chart/?symbol=NSE:{clean_sym}"

        msg = (
            f"🚨 *Institutional Breakout Alert*\n\n"
            f"📌 *Stock:* `{clean_sym}`\n"
            f"💰 *Entry Price:* `₹{entry_price}`\n"
            f"🛑 *Stop Loss (SL):* `₹{stop_loss}`\n"
            f"🎯 *Target (1:2):* `₹{target}`\n"
            f"📦 *Volume Surge:* `{vol_multiplier}x` average\n"
            f"🚀 *Space & VWAP Confluence Confirmed*\n\n"
            f"📊 [View Live Chart]({chart_url})"
        )

        send_telegram_alert(msg)
        save_sent_alert(clean_sym)
        return clean_sym
  except Exception:
    pass
  return None


def check_market():
  now = datetime.now()
  if now.weekday() >= 5:
    print("Market is closed (Weekend).")
    return

  symbols = get_top_500_universe()
  print(
      "Starting parallel intraday institutional scan for top"
      f" {len(symbols)} market-cap stocks..."
  )

  alert_triggered = False
  with ThreadPoolExecutor(max_workers=25) as executor:
    futures = {executor.submit(process_symbol, sym): sym for sym in symbols}
    for future in as_completed(futures):
      if future.result():
        alert_triggered = True

  if not alert_triggered:
    print(
        "Scan completed silently: No intraday institutional breakouts matched."
    )


if __name__ == "__main__":
  check_market()
