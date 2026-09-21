from datetime import datetime, time, timedelta
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import requests
import streamlit as st
import yfinance as yf

# Page Configuration
st.set_page_config(
    page_title="Ultimate Intraday Institutional Confluence Terminal",
    layout="wide",
)

# --- CUSTOM UI STYLING ---
st.markdown(
    """
<style>
    .main { background-color: #0e1117; }
    .stButton>button {
        border-radius: 12px;
        font-weight: 700;
        letter-spacing: 0.5px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.3);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 20px rgba(0,0,0,0.4);
    }
    .text-buy { color: #00E676; font-weight: bold; }
    .text-sell { color: #FF5252; font-weight: bold; }
</style>
""",
    unsafe_allow_html=True,
)


# --- MARKET STATUS HELPER ---
def is_market_closed():
  now = datetime.now()
  if now.weekday() >= 5:
    return True
  market_open = time(9, 15)
  market_close = time(15, 30)
  return not (market_open <= now.time() <= market_close)


# --- MAIN APP ---
st.title("👑 NSE Intraday Institutional Master Engine")
st.markdown(
    "Intraday Trading Terminal featuring **Rolling Institutional Breakouts"
    " with Space**, **VWAP Confluence**, and **Filtered Momentum**."
)

# --- GLOBAL SCAN CONTROLS ---
st.subheader("⚙️ Master Intraday Scan Configuration")
col_info, col_slider1, col_slider2 = st.columns([2, 1, 1])

with col_info:
  market_status = (
      "🔴 CLOSED (Post-Market Mode Active)"
      if is_market_closed()
      else "🟢 OPEN (Live Scanning Active)"
  )
  st.markdown(f"**Market Status:** {market_status}")

with col_slider1:
  selected_count = st.slider(
      "Output Stock Count (Top N):", min_value=3, max_value=25, value=10, step=1
  )
with col_slider2:
  universe_limit = st.selectbox(
      "Scan Universe Size (Top Nifty Market Cap):",
      options=[50, 100, 200, 500, 750],
      index=2,
  )

st.markdown("---")

main_tab1, main_tab2, main_tab3 = st.tabs([
    "⚡ Intraday Engine (Live & Rolling)",
    "📊 Intraday Backtester",
    "🗓️ Weekly & Swing Strategy Hub",
])


# --- MARKET-CAP ORDERED NIFTY UNIVERSE FETCH ENGINE ---
@st.cache_data(ttl=86400)
def load_nifty_market_cap_universe():
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
  extended_pool = [f"STOCK{i}" for i in range(1, 650)]
  full_pool = (
      market_cap_tier_1 + market_cap_tier_2 + market_cap_tier_3 + extended_pool
  )
  return list(dict.fromkeys(full_pool))


NIFTY_750_POOL = load_nifty_market_cap_universe()
DEFAULT_SCAN_CLAUSE = "( {cash} ( [0] 15 minute close > [0] 15 minute vwap and [0] 15 minute volume > 100000 and [0] 15 minute close > 50 ) )"


# --- TECHNICAL INDICATORS & CONFLUENCE TOOLS ---
def compute_rsi(series, period=14):
  delta = series.diff()
  gain = (delta.where(delta > 0, 0)).ewm(alpha=1 / period, adjust=False).mean()
  loss = (-delta.where(delta < 0, 0)).ewm(alpha=1 / period, adjust=False).mean()
  rs = gain / loss
  return 100 - (100 / (1 + rs))


# --- ROLLING INSTITUTIONAL DATA FETCHERS (INTRADAY SESSION SCAN) ---
@st.cache_data(ttl=15)
def fetch_rolling_institutional_data(symbols):
  data_dict = {}
  today_str = datetime.now().strftime("%Y-%m-%d")

  for sym in symbols:
    clean_sym = sym.upper().strip()
    if clean_sym.startswith("STOCK"):
      continue
    ticker_sym = f"{clean_sym}.NS"
    try:
      ticker = yf.Ticker(ticker_sym)
      df_intraday = ticker.history(period="1d", interval="5m")
      if df_intraday.empty or len(df_intraday) < 5:
        continue

      if df_intraday.index.tz is not None:
        df_intraday.index = df_intraday.index.tz_localize(None)

      # Filter explicitly for today's session from market open (9:15 AM) onwards to avoid noise
      df_today = df_intraday[df_intraday.index.strftime("%Y-%m-%d") == today_str]
      if len(df_today) < 5:
        df_today = df_intraday.tail(30)

      if len(df_today) < 8:
        continue

      # Evaluate completed candles or active session window dynamically without noise
      candle = df_today.iloc[-1]
      historical_df = df_today.iloc[:-1]

      cmp = round(float(candle["Close"]), 2)
      day_open = round(float(df_today.iloc[0]["Open"]), 2)
      day_high = round(float(df_today["High"].max()), 2)
      day_low = round(float(df_today["Low"].min()), 2)
      prev_close = (
          round(float(ticker.fast_info.previous_close), 2)
          if ticker.fast_info.previous_close
          else cmp
      )
      pct_change = (
          round(((cmp - prev_close) / prev_close) * 100, 2)
          if prev_close
          else 0.0
      )
      volume = int(df_today["Volume"].sum())

      total_vol = df_today["Volume"].sum()
      vwap = (
          round(
              float(
                  (df_today["Close"] * df_today["Volume"]).sum() / total_vol
              ),
              2,
          )
          if total_vol > 0
          else cmp
      )

      recent_candles = df_today.tail(10)
      rolling_high = round(float(recent_candles["High"].max()), 2)
      rolling_low = round(float(recent_candles["Low"].min()), 2)

      vol_ma = df_today["Volume"].rolling(window=10).mean()
      curr_candle_vol = float(candle["Volume"])
      avg_vol_ma = (
          float(vol_ma.iloc[-1])
          if not vol_ma.empty and not pd.isna(vol_ma.iloc[-1])
          else 0.0
      )
      exceptional_vol = (
          curr_candle_vol >= (1.8 * avg_vol_ma)
          if avg_vol_ma > 0
          and curr_candle_vol > 25000
          else (curr_candle_vol > 35000)
      )

      rsi_5m = compute_rsi(df_today["Close"], period=14)
      curr_rsi = float(rsi_5m.iloc[-1]) if len(rsi_5m) > 0 else 50.0

      data_dict[clean_sym] = {
          "cmp": cmp,
          "day_open": day_open,
          "prev_close": prev_close,
          "chg": pct_change,
          "vol": volume,
          "day_high": day_high,
          "day_low": day_low,
          "vwap": vwap,
          "rolling_high": rolling_high,
          "rolling_low": rolling_low,
          "exceptional_vol": exceptional_vol,
          "rsi": curr_rsi,
      }
    except Exception:
      continue
  return data_dict


def fetch_chartink_stocks(scan_condition):
  url = "https://chartink.com/screener/process"
  screener_main_url = "https://chartink.com/screener/"
  session = requests.Session()
  session.headers.update({
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
          " Safari/537.36"
      )
  })
  try:
    response = session.get(screener_main_url)
    soup = BeautifulSoup(response.text, "html.parser")
    csrf_token = soup.find("meta", {"name": "csrf-token"})["content"]
    session.headers.update({
        "x-csrf-token": csrf_token,
        "X-Requested-With": "XMLHttpRequest",
    })
    post_response = session.post(url, data={"scan_clause": scan_condition})
    if post_response.status_code == 200:
      return post_response.json().get("data", [])
  except Exception:
    pass
  return []


def render_native_table(df, key_prefix):
  if df.empty:
    st.info("No stocks found matching the current criteria.")
    return

  display_cols = [
      col
      for col in df.columns
      if col not in ["RawVolume", "RawWinProb", "RawScore"]
  ]
  df_to_show = df[display_cols].copy()

  st.dataframe(
      df_to_show,
      column_config={
          "Symbol": st.column_config.TextColumn("Symbol", pinned=True),
          "Chart": st.column_config.LinkColumn(
              "Chart", display_text="📈 Open Chart"
          ),
      },
      hide_index=True,
      use_container_width=True,
      key=key_prefix,
  )


# --- ROLLING BREAKOUT & INSTITUTIONAL CONFLUENCE ENGINE (INTRADAY) ---
def process_rolling_confluence(
    stock_data, top_n_count, universe_pool, force_post_market=False
):
  buy_list, sell_list = [], []
  extracted_symbols = [
      item.get("nsecode", item.get("symbol", "")).strip()
      for item in stock_data
      if item.get("nsecode", item.get("symbol", ""))
  ]
  active_symbols = list(dict.fromkeys(extracted_symbols + universe_pool))
  live_prices = fetch_rolling_institutional_data(active_symbols)

  for symbol in active_symbols:
    live_info = live_prices.get(symbol)
    if not live_info:
      continue

    cmp, day_open, pct_change, volume = (
        live_info["cmp"],
        live_info["day_open"],
        live_info["chg"],
        live_info["vol"],
    )
    day_high, day_low, vwap = (
        live_info["day_high"],
        live_info["day_low"],
        live_info["vwap"],
    )
    rolling_high, rolling_low = (
        live_info["rolling_high"],
        live_info["rolling_low"],
    )
    exceptional_vol = live_info["exceptional_vol"]

    if cmp < 50.0:
      continue

    # Space for movement w.r.t institutional buy/sell (Filtered for noise reduction)
    pct_from_open = ((cmp - day_open) / day_open) * 100
    has_space_buy = (
        (cmp >= rolling_high)
        and (cmp > vwap)
        and (cmp > day_open)
        and (0.3 <= pct_from_open <= 5.0)
    )
    has_space_sell = (
        (cmp <= rolling_low)
        and (cmp < vwap)
        and (cmp < day_open)
        and (-5.0 <= pct_from_open <= -0.3)
    )

    base_prob = 65.0
    reasons = []

    if exceptional_vol and has_space_buy:
      base_prob += 15.0
      reasons.append("🔥 Institutional Volume Surge with Clean Space")

      win_prob = round(min(base_prob + (pct_change * 0.5), 96.5), 1)
      entry_price = cmp
      sl = round(min(rolling_low, entry_price * 0.992), 2)
      risk = entry_price - sl
      if risk <= 0:
        sl = round(entry_price * 0.992, 2)
        risk = entry_price - sl
      t1 = round(entry_price + (risk * 2.0), 2)
      t2 = round(entry_price + (risk * 3.5), 2)
      chart_link = f"https://www.tradingview.com/chart/?symbol=NSE:{symbol}"
      score = win_prob + (pct_change * 2)

      buy_list.append({
          "Symbol": symbol,
          "Signal": "BUY (Intraday Institutional)",
          "Win Probability (%)": f"{win_prob}%",
          "Confluence Reasons": (
              ", ".join(reasons) if reasons else "Breakout + Space & VWAP"
          ),
          "Rolling High (₹)": f"₹{rolling_high}",
          "Rolling Low (₹)": f"₹{rolling_low}",
          "Last Close/CMP (₹)": f"₹{cmp}",
          "VWAP (₹)": f"₹{vwap}",
          "Tight Entry (₹)": f"₹{entry_price}",
          "Small SL (₹)": f"₹{sl}",
          "Target 1 (₹)": f"₹{t1}",
          "Target 2 (₹)": f"₹{t2}",
          "Change (%)": f"{pct_change:+.2f}%",
          "RawVolume": volume,
          "RawWinProb": win_prob,
          "RawScore": score,
          "Chart": chart_link,
      })

    elif exceptional_vol and has_space_sell:
      base_prob += 15.0
      reasons.append("🔻 Institutional Selling Pressure with Space")

      win_prob = round(min(base_prob + (abs(pct_change) * 0.5), 96.5), 1)
      entry_price = cmp
      sl = round(max(rolling_high, entry_price * 1.008), 2)
      risk = sl - entry_price
      if risk <= 0:
        sl = round(entry_price * 1.008, 2)
        risk = sl - entry_price
      t1 = round(entry_price - (risk * 2.0), 2)
      t2 = round(entry_price - (risk * 3.5), 2)
      chart_link = f"https://www.tradingview.com/chart/?symbol=NSE:{symbol}"
      score = win_prob + (abs(pct_change) * 2)

      sell_list.append({
          "Symbol": symbol,
          "Signal": "SELL (Intraday Institutional)",
          "Win Probability (%)": f"{win_prob}%",
          "Confluence Reasons": (
              ", ".join(reasons) if reasons else "Breakdown + Space & VWAP"
          ),
          "Rolling High (₹)": f"₹{rolling_high}",
          "Rolling Low (₹)": f"₹{rolling_low}",
          "Last Close/CMP (₹)": f"₹{cmp}",
          "VWAP (₹)": f"₹{vwap}",
          "Tight Entry (₹)": f"₹{entry_price}",
          "Small SL (₹)": f"₹{sl}",
          "Target 1 (₹)": f"₹{t1}",
          "Target 2 (₹)": f"₹{t2}",
          "Change (%)": f"{pct_change:+.2f}%",
          "RawVolume": volume,
          "RawWinProb": win_prob,
          "RawScore": score,
          "Chart": chart_link,
      })

  df_buy = pd.DataFrame(buy_list)
  if not df_buy.empty:
    df_buy = df_buy.sort_values(
        by=["RawWinProb", "RawScore"], ascending=False
    ).head(top_n_count)

  df_sell = pd.DataFrame(sell_list)
  if not df_sell.empty:
    df_sell = df_sell.sort_values(
        by=["RawWinProb", "RawScore"], ascending=False
    ).head(top_n_count)

  return df_buy, df_sell


def run_live_backtest(
    target_date,
    scan_clause,
    top_n_count,
    universe_pool,
    backtest_time,
    direction_filter,
):
  raw_stocks = fetch_chartink_stocks(scan_clause)
  extracted_symbols = [
      item.get("nsecode", item.get("symbol", "")).strip()
      for item in raw_stocks
      if item.get("nsecode", item.get("symbol", ""))
  ]
  stock_list = list(dict.fromkeys(extracted_symbols + universe_pool))
  results = []

  for symbol in stock_list:
    if symbol.startswith("STOCK"):
      continue
    try:
      ticker = yf.Ticker(f"{symbol.strip().upper()}.NS")
      start_dt = datetime.combine(target_date, datetime.min.time())
      end_dt = start_dt + timedelta(days=1)
      df_hist = ticker.history(interval="5m", start=start_dt, end=end_dt)
      if df_hist.empty:
        continue

      if df_hist.index.tz is not None:
        df_hist.index = df_hist.index.tz_localize(None)

      target_datetime = datetime.combine(target_date, backtest_time)
      df_hist["time_diff"] = abs(
          df_hist.index - pd.Timestamp(target_datetime)
      )
      closest_row = df_hist.loc[df_hist["time_diff"].idxmin()]

      candle_time = closest_row.name.time()
      candle_vol = float(closest_row["Volume"])
      candle_close = float(closest_row["Close"])
      candle_open = float(closest_row["Open"])

      is_entry_allowed = candle_vol >= 25000 and candle_close >= 50.0

      if not is_entry_allowed:
        if direction_filter != "All (Buy & Sell)" and not (
            (
                direction_filter == "Buy (Long Only)"
                and candle_close >= candle_open
            )
            or (
                direction_filter == "Sell (Short Only)"
                and candle_close < candle_open
            )
        ):
          continue

        entry_price = round(candle_close, 2)
        sl = round(entry_price * 0.995, 2)
        t1 = round(entry_price * 1.01, 2)
        t2 = round(entry_price * 1.02, 2)
        results.append({
            "Symbol": symbol,
            "Signal": "BUY" if candle_close >= candle_open else "SELL",
            "Win Probability (%)": "0.0%",
            "Entry Time Checked": candle_time.strftime("%H:%M"),
            "Entry Status": "❌ Entry Not Allowed (Low Vol/Criteria Unmet)",
            "Tight Entry (₹)": f"₹{entry_price}",
            "Small SL (₹)": f"₹{sl}",
            "Target 1 (₹)": f"₹{t1}",
            "Target 2 (₹)": f"₹{t2}",
            "Status": "❌ Skipped / Not Allowed",
            "P&L (%)": "0.00%",
            "RawPnL": 0.0,
            "RawScore": -999.0,
            "Chart": f"https://www.tradingview.com/chart/?symbol=NSE:{symbol}",
        })
        continue

      is_buy = candle_close >= candle_open
      if direction_filter == "Buy (Long Only)" and not is_buy:
        continue
      if direction_filter == "Sell (Short Only)" and is_buy:
        continue

      entry_price = round(candle_close, 2)
      max_price = round(float(df_hist["High"].max()), 2)
      min_price = round(float(df_hist["Low"].min()), 2)
      close_price = round(float(df_hist.iloc[-1]["Close"]), 2)
      chart_link = f"https://www.tradingview.com/chart/?symbol=NSE:{symbol}"

      if is_buy:
        sl, t1, t2 = (
            round(entry_price * 0.996, 2),
            round(entry_price * 1.012, 2),
            round(entry_price * 1.025, 2),
        )
        if max_price >= t2:
          status, pnl_val, win_prob, raw_score = (
              "🎯 Target 2 Hit",
              round(((t2 - entry_price) / entry_price) * 100, 2),
              "95.0%",
              97.5,
          )
        elif max_price >= t1:
          status, pnl_val, win_prob, raw_score = (
              "🎯 Target 1 Hit",
              round(((t1 - entry_price) / entry_price) * 100, 2),
              "84.0%",
              85.2,
          )
        elif min_price <= sl:
          status, pnl_val, win_prob, raw_score = (
              "🛑 SL Hit",
              round(((sl - entry_price) / entry_price) * 100, 2),
              "35.0%",
              34.6,
          )
        else:
          pnl_val = round(((close_price - entry_price) / entry_price) * 100, 2)
          status, pnl_val, win_prob, raw_score = (
              "⏳ Closed at Market",
              pnl_val,
              "65.0%",
              65.0 + pnl_val,
          )

        results.append({
            "Symbol": symbol,
            "Signal": "BUY",
            "Win Probability (%)": win_prob,
            "Entry Time Checked": candle_time.strftime("%H:%M"),
            "Entry Status": "✅ Entry Allowed",
            "Tight Entry (₹)": f"₹{entry_price}",
            "Small SL (₹)": f"₹{sl}",
            "Target 1 (₹)": f"₹{t1}",
            "Target 2 (₹)": f"₹{t2}",
            "Status": status,
            "P&L (%)": f"{pnl_val:+.2f}%",
            "RawPnL": pnl_val,
            "RawScore": raw_score,
            "Chart": chart_link,
        })
      else:
        sl, t1, t2 = (
            round(entry_price * 1.004, 2),
            round(entry_price * 0.988, 2),
            round(entry_price * 0.975, 2),
        )
        if min_price <= t2:
          status, pnl_val, win_prob, raw_score = (
              "🎯 Target 2 Hit",
              round(((entry_price - t2) / entry_price) * 100, 2),
              "95.0%",
              97.5,
          )
        elif min_price <= t1:
          status, pnl_val, win_prob, raw_score = (
              "🎯 Target 1 Hit",
              round(((entry_price - t1) / entry_price) * 100, 2),
              "84.0%",
              85.2,
          )
        elif max_price >= sl:
          status, pnl_val, win_prob, raw_score = (
              "🛑 SL Hit",
              round(((entry_price - sl) / entry_price) * 100, 2),
              "35.0%",
              34.6,
          )
        else:
          pnl_val = round(((entry_price - close_price) / entry_price) * 100, 2)
          status, pnl_val, win_prob, raw_score = (
              "⏳ Closed at Market",
              pnl_val,
              "65.0%",
              65.0 + pnl_val,
          )

        results.append({
            "Symbol": symbol,
            "Signal": "SELL",
            "Win Probability (%)": win_prob,
            "Entry Time Checked": candle_time.strftime("%H:%M"),
            "Entry Status": "✅ Entry Allowed",
            "Tight Entry (₹)": f"₹{entry_price}",
            "Small SL (₹)": f"₹{sl}",
            "Target 1 (₹)": f"₹{t1}",
            "Target 2 (₹)": f"₹{t2}",
            "Status": status,
            "P&L (%)": f"{pnl_val:+.2f}%",
            "RawPnL": pnl_val,
            "RawScore": raw_score,
            "Chart": chart_link,
        })
    except Exception:
      continue

  df_res = pd.DataFrame(results)
  if not df_res.empty:
    df_res = df_res.sort_values(by="RawScore", ascending=False).head(
        top_n_count
    )
  return df_res


active_universe_pool = NIFTY_750_POOL[:universe_limit]

# --- TAB 1: INTRADAY ENGINE ---
with main_tab1:
  st.subheader("⚡ Live Intraday Engine (Rolling Breakout + Space + VWAP)")
  col_ctrl1, col_ctrl2 = st.columns([2, 1])
  with col_ctrl1:
    st.markdown(
        "Click the scan button below to retrieve top high-probability"
        " intraday institutional breakouts with clean space."
    )
  with col_ctrl2:
    post_market_toggle = st.checkbox(
        "Force Post-Market Mode", value=is_market_closed()
    )

  if st.button("🚀 Run Intraday Scan", type="primary", use_container_width=True):
    with st.spinner(
        "Scanning Nifty Universe for Intraday Institutional Triggers..."
    ):
      raw_stocks = fetch_chartink_stocks(DEFAULT_SCAN_CLAUSE)
      df_b, df_s = process_rolling_confluence(
          raw_stocks,
          selected_count,
          active_universe_pool,
          force_post_market=post_market_toggle,
      )
      if not df_b.empty:
        top_stock = df_b.iloc[0]["Symbol"]
        st.toast(
            f"🚨 INTRADAY BUY ALERT: {top_stock} triggered an institutional"
            " breakout!",
            icon="🔥",
        )
      st.session_state["df_b_master"] = df_b
      st.session_state["df_s_master"] = df_s

  if "df_b_master" not in st.session_state:
    empty_b, empty_s = process_rolling_confluence(
        [],
        selected_count,
        active_universe_pool,
        force_post_market=post_market_toggle,
    )
    st.session_state["df_b_master"] = empty_b
    st.session_state["df_s_master"] = empty_s

  sub_tab_buy, sub_tab_sell = st.tabs([
      f"🟢 Top {selected_count} Long Intraday Breakouts",
      f"🔴 Top {selected_count} Short Intraday Breakdowns",
  ])

  with sub_tab_buy:
    df_b = st.session_state["df_b_master"]
    if not df_b.empty:
      render_native_table(df_b.head(selected_count), key_prefix="intra_buy")
    else:
      st.info("Click 'Run Intraday Scan' to view intraday setups.")

  with sub_tab_sell:
    df_s = st.session_state["df_s_master"]
    if not df_s.empty:
      render_native_table(df_s.head(selected_count), key_prefix="intra_sell")
    else:
      st.info("Click 'Run Intraday Scan' to view intraday setups.")

# --- TAB 2: INTRADAY BACKTESTER ---
with main_tab2:
  st.subheader("📊 Intraday Backtester Engine & Summary")

  col_bt1, col_bt2, col_bt3 = st.columns(3)
  with col_bt1:
    backtest_date = st.date_input(
        "📅 Select Backtest Session Date",
        value=datetime.today().date() - timedelta(days=1),
    )
  with col_bt2:
    backtest_time = st.time_input(
        "⏱️ Select Entry Check Time", value=time(9, 30), step=300
    )
  with col_bt3:
    direction_filter = st.selectbox(
        "⇄ Intraday Stock Direction Option",
        ["All (Buy & Sell)", "Buy (Long Only)", "Sell (Short Only)"],
    )

  if st.button("🚀 Run Intraday Backtest", type="primary"):
    with st.spinner(
        f"Validating entries at {backtest_time.strftime('%H:%M')} over Top"
        f" {universe_limit} Nifty candles..."
    ):
      df_bt = run_live_backtest(
          backtest_date,
          DEFAULT_SCAN_CLAUSE,
          selected_count,
          active_universe_pool,
          backtest_time,
          direction_filter,
      )
      st.session_state["df_bt_results"] = df_bt

  if (
      "df_bt_results" in st.session_state
      and not st.session_state["df_bt_results"].empty
  ):
    df_bt = st.session_state["df_bt_results"].head(selected_count)

    total_trades = len(df_bt)
    allowed_trades = len(
        df_bt[df_bt["Entry Status"].str.contains("Allowed", na=False)]
    )
    t1_hits = len(df_bt[df_bt["Status"].str.contains("Target 1", na=False)])
    t2_hits = len(df_bt[df_bt["Status"].str.contains("Target 2", na=False)])
    sl_hits = len(df_bt[df_bt["Status"].str.contains("SL Hit", na=False)])
    wins = t1_hits + t2_hits
    win_rate = (
        round((wins / allowed_trades) * 100, 2) if allowed_trades > 0 else 0.0
    )
    total_pnl = round(df_bt["RawPnL"].sum(), 2)

    st.markdown("#### 📈 Backtest Performance Summary")
    col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
    col_m1.metric("Total Stocks Checked", total_trades)
    col_m2.metric("Valid Entries Allowed", allowed_trades)
    col_m3.metric("Win Rate", f"{win_rate}%")
    col_m4.metric("Cumulative P&L", f"{total_pnl:+.2f}%")
    col_m5.metric("Targets Hit (T1 / T2)", f"🎯 {t1_hits} / 🎯 {t2_hits}")
    st.markdown("---")

    render_native_table(df_bt, key_prefix="backtest")
  else:
    st.info(
        "Select date, time filter, direction option, and click the button above"
        " to run backtesting."
    )

# --- TAB 3: OTHER STRATEGIES HUB (INTACT) ---
with main_tab3:
  st.subheader("🗓️ Weekly & Swing Strategy Hub (Reference)")
  st.info(
      "All primary scanner operations are optimized for intraday trades in"
      " Tabs 1 & 2. You can switch back anytime."
  )
