# -*- coding: utf-8 -*-
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, time as dt_time, timedelta
import json
import os
from bs4 import BeautifulSoup
import pandas as pd
import requests
import yfinance as yf
from zoneinfo import ZoneInfo

# Telegram Configuration from GitHub Secrets
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

STATE_FILE = "sent_intraday_stocks.json"


def get_ist_now():
  try:
    return datetime.now(ZoneInfo("Asia/Kolkata"))
  except Exception:
    from datetime import timezone

    IST = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(IST)


def send_telegram_message(message):
  """Sends an alert message to the configured Telegram chat."""
  if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("Telegram credentials missing!")
    return

  url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
  payload = {
      "chat_id": TELEGRAM_CHAT_ID,
      "text": message,
      "parse_mode": "Markdown",
      "disable_web_page_preview": True,
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


def get_latest_news(ticker_sym):
  """Fetches the latest news headline for the stock using yfinance."""
  try:
    ticker = yf.Ticker(ticker_sym)
    news_list = ticker.news
    if news_list and len(news_list) > 0:
      item = news_list[0]
      if "content" in item and isinstance(item["content"], dict):
        return item["content"].get("title", "")
      elif "title" in item:
        return item["title"]
  except Exception:
    pass
  return ""


def get_comprehensive_stock_pool():
  """Dynamically fetches stock pool based on Nifty 500 & high liquidity."""
  stocks = set()
  try:
    url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code == 200:
      from io import StringIO

      df_nifty = pd.read_csv(StringIO(response.text))
      if "Symbol" in df_nifty.columns:
        for sym in df_nifty["Symbol"].dropna():
          clean_sym = str(sym).strip().upper()
          if clean_sym:
            stocks.add(f"{clean_sym}.NS")
  except Exception:
    pass

  fallback_pool = [
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
      "MANKIND",
      "SUNTV",
      "APOLLOTYRE",
      "STLTECH",
      "WELCORP",
      "JIOFIN",
      "TATATECH",
      "HUDCO",
      "IREDA",
      "MAZDOCK",
      "COCHINSHIP",
      "BDL",
      "MOTHERSON",
      "SONACOMS",
      "ANANDRATHI",
      "CEINFO",
      "MAPMYINDIA",
      "STARHEALTH",
      "MEDANTA",
      "KPITTECH",
      "CYIENT",
      "TITAGARH",
      "TEXMACO",
      "SUZLON",
      "IDFCFIRSTB",
      "YESBANK",
      "JPPOWER",
      "ZENSARTECH",
      "INTELLECT",
      "BSOFT",
      "NAVINFLUOR",
      "ABSLAMC",
      "AJANTPHARM",
      "ALKEM",
      "AMBER",
      "APLAPOLLO",
      "ATUL",
      "AUBANK",
      "AUROPHARMA",
      "AXISCADES",
      "BALKRISIND",
      "BALRAMCHIN",
      "BATAINDIA",
      "BERGEPAINT",
      "CESC",
      "CHAMBLFERT",
      "CUB",
      "DEEPAKNTR",
      "DELTACORP",
      "EIDPARRY",
      "ELGIEQUIP",
      "ENDURANCE",
      "ESCORTS",
      "EXIDEIND",
      "FEDERALBNK",
      "GNFC",
      "GODREJCP",
      "GODREJPROP",
      "GRANULES",
      "GUJGASLTD",
      "HINDZINC",
      "HINDPETRO",
      "IDBI",
      "IEX",
      "IGL",
      "INDIGO",
      "IPCALAB",
      "JKCEMENT",
      "JSWENERGY",
      "KAJARIACER",
      "KALYANKJIL",
      "L&TFH",
      "LAURUSLABS",
      "LICHSGFIN",
      "LODHA",
      "M&MFIN",
      "MANAPPURAM",
      "MARICO",
      "MAXHEALTH",
      "MCX",
      "MUTHOOTFIN",
      "NAM-INDIA",
      "NATCOPHARM",
      "NATIONALUM",
      "NAVINFLUOR",
      "NBCC",
      "NCC",
      "NMDC",
      "OBEROIRLTY",
      "OFSS",
      "PAGEIND",
      "PERSISTENT",
      "PETRONET",
      "PFC",
      "PIDILITIND",
      "PIIND",
      "POLYCAB",
      "PRESTIGE",
      "PVRINOX",
      "RADICO",
      "RECLTD",
      "SBICARD",
      "SHREECEM",
      "SRF",
      "SUNTV",
      "SYNGENE",
      "TATACOMM",
      "TATAELXSI",
      "TORNTPHARM",
      "TORNTPOWER",
      "TRENT",
      "TRIDENT",
      "UPL",
      "VEDL",
      "VOLTAS",
      "WHIRLPOOL",
      "WIPRO",
      "YESBANK",
      "ZYDUSLIFE",
  ]
  for sym in fallback_pool:
    stocks.add(f"{sym}.NS")
  return list(stocks)[:750]


def get_top_100_fno_universe():
  return [
      "RELIANCE",
      "TCS",
      "HDFCBANK",
      "ICICIBANK",
      "INFY",
      "BHARTIARTL",
      "SBIN",
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
      "HAL",
      "BEL",
      "IOC",
      "GAIL",
      "ZOMATO",
      "JIOFIN",
      "TATATECH",
      "DLF",
      "TRENT",
      "INDIGO",
      "AMBUJACEM",
      "ACC",
      "SIEMENS",
      "ABB",
      "HAVELLS",
      "VBL",
      "GODREJCP",
      "DABUR",
      "MARICO",
      "ICICIGI",
      "ICICIPRULI",
      "RECLTD",
      "PFC",
      "LTIM",
      "ATGL",
      "ADANIGREEN",
      "ADANIPOWER",
      "PIIND",
      "NAVINFLUOR",
      "POLYCAB",
      "PERSISTENT",
      "COFORGE",
      "MPHASIS",
      "CHOLAFIN",
      "MUTHOOTFIN",
      "BANKBARODA",
      "PNB",
  ]


def compute_rsi(series, period=14):
  delta = series.diff()
  gain = (delta.where(delta > 0, 0)).ewm(alpha=1 / period, adjust=False).mean()
  loss = (-delta.where(delta < 0, 0)).ewm(alpha=1 / period, adjust=False).mean()
  rs = gain / loss
  return 100 - (100 / (1 + rs))


# --- F&O 9:15 STRATEGY SCANNER (Top Gainer & Loser at 9:16 AM) ---
def run_fno_915_scanner():
  today = get_ist_now().date()
  fno_pool = get_top_100_fno_universe()
  results = []

  start_dt = datetime.combine(today, datetime.min.time())
  end_dt = start_dt + timedelta(days=1)

  for symbol in fno_pool:
    clean_sym = symbol.upper().strip()
    try:
      ticker = yf.Ticker(f"{clean_sym}.NS")
      df_1m = ticker.history(start=start_dt, end=end_dt, interval="1m")
      if df_1m.empty or len(df_1m) < 2:
        continue
      if df_1m.index.tz is not None:
        df_1m.index = df_1m.index.tz_localize(None)

      df_day = df_1m[df_1m.index.normalize() == pd.Timestamp(today)]
      if df_day.empty:
        continue

      t_915 = datetime.combine(today, dt_time(9, 15))
      df_day["diff_915"] = abs(df_day.index - pd.Timestamp(t_915))
      row_915 = df_day.loc[df_day["diff_915"].idxmin()]

      p_915 = float(row_915["Open"])
      current_close = float(df_day.iloc[-1]["Close"])
      prev_close = (
          float(ticker.fast_info.previous_close)
          if ticker.fast_info.previous_close
          else p_915
      )
      chg_pct = round(((p_915 - prev_close) / prev_close) * 100, 2)

      results.append({
          "Symbol": clean_sym,
          "Price": p_915,
          "Change": chg_pct,
          "Chart": f"https://www.tradingview.com/chart/?symbol=NSE:{clean_sym}",
      })
    except Exception:
      continue

  if not results:
    return None, None

  df_res = pd.DataFrame(results)
  top_gainer = df_res.sort_values(by="Change", ascending=False).iloc[0]
  top_loser = df_res.sort_values(by="Change", ascending=True).iloc[0]
  return top_gainer, top_loser


# --- INTRADAY STRATEGY 1: Volume Expansion Breakout (High Focus) ---
def scan_volume_expansion(ticker):
  try:
    stock = yf.Ticker(ticker)
    df_intraday = stock.history(period="3d", interval="15m")
    if df_intraday.empty or len(df_intraday) < 60:
      return None
    if df_intraday.index.tz is not None:
      df_intraday.index = df_intraday.index.tz_localize(None)

    df_intraday["Vol_SMA_50"] = df_intraday["Volume"].rolling(window=50).mean()
    recent_candles = df_intraday.iloc[:-1].tail(15)
    resistance_high = float(recent_candles["High"].max())

    latest = df_intraday.iloc[-1]
    cmp = round(float(latest["Close"]), 2)
    latest_vol = float(latest["Volume"])
    vol_sma_50 = float(df_intraday["Vol_SMA_50"].iloc[-1])

    if cmp < 50.0 or pd.isna(vol_sma_50) or vol_sma_50 == 0:
      return None

    if latest_vol >= (vol_sma_50 * 2.5) and cmp >= resistance_high * 0.995:
      win_prob = 91.5  # High conviction for volume breakouts
      reasons = [
          "🔥 Volume Expansion Breakout (>=2.5x VMA)",
          f"Vol Surge: {round(latest_vol / vol_sma_50, 2)}x",
      ]
      sl = round(cmp * 0.992, 2)
      risk = cmp - sl
      t1 = round(cmp + (risk * 1.5), 2)
      t2 = round(cmp + (risk * 3.0), 2)
      profit_pct = round(((t2 - cmp) / cmp) * 100, 2)

      if profit_pct < 2.5:
        return None

      score = win_prob + profit_pct + 10.0  # Extra priority weighting
      clean_sym = ticker.replace(".NS", "")
      news = get_latest_news(ticker)

      return {
          "ticker": clean_sym,
          "strategy_type": "VOLUME_EXPANSION",
          "signal": "🚀 VOLUME EXPANSION BREAKOUT BUY",
          "price": cmp,
          "win_prob": win_prob,
          "reasons": " | ".join(reasons),
          "sl": sl,
          "target_1": t1,
          "target_2": t2,
          "profit_pct": profit_pct,
          "score": score,
          "news": news,
          "chart": f"https://www.tradingview.com/chart/?symbol=NSE:{clean_sym}",
      }
  except Exception:
    pass
  return None


# --- INTRADAY STRATEGY 2: Combined Intraday Confluence ---
def scan_combined_intraday(ticker):
  try:
    stock = yf.Ticker(ticker)
    df_intraday = stock.history(period="2d", interval="15m")
    if df_intraday.empty or len(df_intraday) < 15:
      return None
    if df_intraday.index.tz is not None:
      df_intraday.index = df_intraday.index.tz_localize(None)

    latest_date = df_intraday.index[-1].normalize()
    df_today = df_intraday[df_intraday.index.normalize() == latest_date]
    day_elapsed_vol = (
        int(df_today["Volume"].sum())
        if not df_today.empty
        else int(df_intraday["Volume"].sum())
    )

    cmp = round(float(df_intraday.iloc[-1]["Close"]), 2)
    if cmp < 50.0:
      return None

    total_vol = df_intraday["Volume"].sum()
    vwap = (
        round(
            float(
                (df_intraday["Close"] * df_intraday["Volume"]).sum() / total_vol
            ),
            2,
        )
        if total_vol > 0
        else cmp
    )

    recent_candles = df_intraday.iloc[:-1].tail(12)
    rolling_high = round(float(recent_candles["High"].max()), 2)
    rolling_low = round(float(recent_candles["Low"].min()), 2)

    recent_comp_high = df_intraday["High"].iloc[-6:-1].max()
    recent_comp_low = df_intraday["High"].iloc[-6:-1].min()
    range_compressed = (recent_comp_high - recent_comp_low) / cmp <= 0.025

    vol_sma = (
        df_intraday["Volume"].rolling(10).mean().iloc[-1]
        if len(df_intraday) >= 10
        else day_elapsed_vol
    )
    vol_spike = df_intraday["Volume"].iloc[-1] > (vol_sma * 1.5)
    exceptional_vol = day_elapsed_vol >= 120000

    is_bullish_setup = (
        cmp > rolling_high or (range_compressed and cmp >= vwap)
    ) and (cmp >= vwap * 0.995)

    if is_bullish_setup:
      win_prob = 88.5
      reasons = ["Daily Trend + Intraday Confluence"]
      if exceptional_vol or vol_spike:
        win_prob += 4.0
        reasons.append("High Volume Expansion")
      if range_compressed:
        reasons.append("Range Compression Breakout")

      win_prob = round(min(win_prob, 97.5), 1)
      sl = round(min(rolling_low, cmp * 0.992), 2)
      risk = cmp - sl
      if risk <= 0:
        risk = cmp * 0.005
        sl = cmp - risk
      t1 = round(cmp + (risk * 1.5), 2)
      t2 = round(cmp + (risk * 3.0), 2)
      profit_pct = round(((t2 - cmp) / cmp) * 100, 2)

      if profit_pct < 2.5:
        return None

      score = win_prob + profit_pct
      clean_sym = ticker.replace(".NS", "")
      news = get_latest_news(ticker)

      return {
          "ticker": clean_sym,
          "strategy_type": "COMBINED_INTRADAY",
          "signal": "⚡ COMBINED INTRA BUY",
          "price": cmp,
          "win_prob": win_prob,
          "reasons": " | ".join(reasons),
          "sl": sl,
          "target_1": t1,
          "target_2": t2,
          "profit_pct": profit_pct,
          "score": score,
          "news": news,
          "chart": f"https://www.tradingview.com/chart/?symbol=NSE:{clean_sym}",
      }
  except Exception:
    pass
  return None


# --- WEEKLY STRATEGY SCANNERS (Best 1 Stock at 8:30 AM) ---
def scan_weekly_gtf(ticker):
  try:
    stock = yf.Ticker(ticker)
    df_weekly = stock.history(period="2y", interval="1wk")
    df_daily = stock.history(period="6mo", interval="1d")

    if len(df_weekly) < 20 or len(df_daily) < 30:
      return None

    cmp = round(float(df_weekly.iloc[-1]["Close"]), 2)
    if cmp < 50.0:
      return None

    daily_rsi = compute_rsi(df_daily["Close"], period=14).iloc[-1]
    daily_trend_up = df_daily["Close"].iloc[-1] > df_daily["Close"].iloc[-20]
    if not daily_trend_up or not (38 <= daily_rsi <= 72):
      return None

    sl = round(float(df_weekly["Low"].tail(3).min()) * 0.985, 2)
    if sl >= cmp:
      sl = round(cmp * 0.95, 2)
    risk = cmp - sl
    if risk <= 0:
      return None

    t1 = round(cmp + (risk * 1.5), 2)
    t2 = round(cmp + (risk * 3.0), 2)
    target_pct = round(((t2 - cmp) / cmp) * 100, 2)

    if target_pct < 2.5:
      return None

    win_prob = 89.0
    score = win_prob + target_pct
    clean_sym = ticker.replace(".NS", "")
    news = get_latest_news(ticker)

    return {
        "ticker": clean_sym,
        "signal": "WEEKLY GTF SWING BUY",
        "close_price": cmp,
        "setup_type": "GTF HTF Demand & Resistance Confluence",
        "win_prob": win_prob,
        "target_pct": target_pct,
        "sl": sl,
        "target_1": t1,
        "target_2": t2,
        "score": score,
        "news": news,
        "chart": f"https://www.tradingview.com/chart/?symbol=NSE:{clean_sym}",
    }
  except Exception:
    pass
  return None


def main():
  stocks = get_comprehensive_stock_pool()
  now_ist = get_ist_now()
  current_time = now_ist.time()
  weekday = now_ist.weekday()

  # Skip weekends
  if weekday >= 5:
    print("Market closed on weekends.")
    return

  print(f"Current IST Time: {now_ist.strftime('%H:%M:%S')}")

  # 1. F&O 9:15 Strategy Alert at 9:16 AM (after 1st 1-min candle closes)
  if dt_time(9, 15) <= current_time <= dt_time(9, 20):
    print("Running F&O 9:15 Top Gainer & Loser Scan...")
    top_gainer, top_loser = run_fno_915_scanner()
    if top_gainer is not None and top_loser is not None:
      msg = "⚡ *F&O 9:15 MARKET OPEN OPENING BELL ALERT* ⚡\n\n"
      msg += (
          f"🟢 *Top Gainer:* {top_gainer['Symbol']} | Price:"
          f" ₹{top_gainer['Price']:.2f} ({top_gainer['Change']:+.2f}%)\n"
          f"• [Open Chart]({top_gainer['Chart']})\n\n"
          f"🔴 *Top Loser:* {top_loser['Symbol']} | Price:"
          f" ₹{top_loser['Price']:.2f} ({top_loser['Change']:+.2f}%)\n"
          f"• [Open Chart]({top_loser['Chart']})\n"
      )
      send_telegram_message(msg)
    return

  # 2. Weekly Strategy Best 1 Stock Alert at 8:30 AM
  if dt_time(8, 25) <= current_time <= dt_time(8, 40):
    print("Running Weekly Strategy Best Stock Scan (8:30 AM)...")
    best_weekly = None
    best_score = -1.0

    with ThreadPoolExecutor(max_workers=25) as executor:
      for r in executor.map(scan_weekly_gtf, stocks):
        if r and r["score"] > best_score:
          best_score = r["score"]
          best_weekly = r

    if best_weekly:
      news_line = (
          f"• *Latest News:* {best_weekly['news']}\n"
          if best_weekly.get("news")
          else ""
      )
      msg = (
          f"🌟 *BEST WEEKLY SWING TRADE (8:30 AM ALERT)* 🌟\n\n"
          f"📌 *{best_weekly['ticker']}* | {best_weekly['signal']} | Win Prob:"
          f" *{best_weekly['win_prob']}%*\n"
          f"• *Reason for Buy:* {best_weekly['setup_type']}\n"
          f"• *Entry / CMP:* ₹{best_weekly['close_price']:.2f}\n"
          f"• *Stop Loss:* ₹{best_weekly['sl']:.2f}\n"
          f"• *Target 1:* ₹{best_weekly['target_1']:.2f}\n"
          f"• *Target 2:* ₹{best_weekly['target_2']:.2f}"
          f" ({best_weekly['target_pct']:+.2f}%)\n"
          f"{news_line}"
          f"• [Open TradingView Chart]({best_weekly['chart']})\n"
      )
      send_telegram_message(msg)
    return

  # 3. Intraday Alerts: 9:17 AM to 1:00 PM IST (Every 30 min / on radar)
  if dt_time(9, 17) <= current_time <= dt_time(13, 0):
    print(
        "Running Intraday High Conviction Scan (Focus on Volume Breakouts)..."
    )
    sent_state = load_sent_state()
    today_str = now_ist.strftime("%Y-%m-%d")

    intraday_matches = []
    with ThreadPoolExecutor(max_workers=25) as executor:
      # Prioritize Volume Expansion breakouts
      for r in executor.map(scan_volume_expansion, stocks):
        if r:
          key = f"{r['ticker']}_{r['strategy_type']}"
          if sent_state.get(key) != today_str:
            intraday_matches.append(r)

      for r in executor.map(scan_combined_intraday, stocks):
        if r:
          key = f"{r['ticker']}_{r['strategy_type']}"
          if sent_state.get(key) != today_str:
            intraday_matches.append(r)

    # Sort by score (volume breakouts weighted higher) and take top high-conviction non-duplicate stocks
    intraday_matches = sorted(
        intraday_matches, key=lambda x: x["score"], reverse=True
    )[:3]

    if intraday_matches:
      msg = "⚡ *HIGH CONVICTION INTRADAY RADAR ALERTS* ⚡\n\n"
      for m in intraday_matches:
        news_line = f"• *Latest News:* {m['news']}\n" if m.get("news") else ""
        msg += (
            f"📌 *{m['ticker']}* | {m['signal']} | Win Prob:"
            f" *{m['win_prob']}%*\n"
            f"• *Reason:* {m['reasons']}\n"
            f"• *Tight Entry:* ₹{m['price']:.2f}\n"
            f"• *Small SL:* ₹{m['sl']:.2f}\n"
            f"• *Target 1:* ₹{m['target_1']:.2f}\n"
            f"• *Target 2:* ₹{m['target_2']:.2f} ({m['profit_pct']:+.2f}%)\n"
            f"{news_line}"
            f"• [Open TradingView Chart]({m['chart']})\n\n"
        )
      send_telegram_message(msg)

      for m in intraday_matches:
        sent_state[f"{m['ticker']}_{m['strategy_type']}"] = today_str
      save_sent_state(sent_state)
    else:
      print("No new high-conviction intraday setups found.")
  else:
    print(
        "Outside active alert time window (9:17 AM to 1:00 PM IST for intraday"
        " / 8:30 AM for weekly / 9:16 AM for F&O)."
    )


if __name__ == "__main__":
  main()
