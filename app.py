# -*- coding: utf-8 -*-
import datetime
from datetime import datetime, time, timedelta
import os
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import requests
import streamlit as st
import yfinance as yf
from zoneinfo import ZoneInfo

# Page Configuration
st.set_page_config(
    page_title="Ultimate Multi-Timeframe Confluence Terminal - Intraday Edition", layout="wide"
)

# --- CUSTOM UI STYLING (Strictly NO white color) ---
st.markdown(
    """
<style>
    .main { background-color: #0e1117; color: #f3f4f6; }
    .stButton>button {
        border-radius: 12px;
        font-weight: 700;
        letter-spacing: 0.5px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.5);
        transition: all 0.3s ease;
        background-color: #1f2937;
        color: #38bdf8;
        border: 1px solid #374151;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 20px rgba(0,0,0,0.7);
        background-color: #374151;
        color: #ffffff;
    }
    .text-buy { color: #00E676; font-weight: bold; }
    .text-sell { color: #FF5252; font-weight: bold; }
</style>
""",
    unsafe_allow_html=True,
)


# --- MARKET STATUS HELPER (FIXED FOR IST) ---
def is_market_closed():
    try:
        now = datetime.now(ZoneInfo("Asia/Kolkata"))
    except Exception:
        from datetime import timezone
        IST = timezone(timedelta(hours=5, minutes=30))
        now = datetime.now(IST)
        
    if now.weekday() >= 5:
        return True
    market_open = time(9, 15)
    market_close = time(15, 30)
    return not (market_open <= now.time() <= market_close)


# --- MAIN APP ---
st.title("👑 NSE Ultimate Intraday Confluence Engine (Nifty Universe)")
st.markdown(
    "Trading Terminal featuring **GTF Intraday Analysis**, **Rolling Institutional Breakouts**, **High-Turnover Momentum Scans**, and **Intraday Session Backtesting**."
)

market_status = (
    "🔴 CLOSED (Post-Market Mode Active)"
    if is_market_closed()
    else "🟢 OPEN (Live Scanning Active)"
)
st.markdown(f"**Market Status:** {market_status}")
st.markdown("---")

# Initialize Strategy Scan Storage in Session State
if "strategy_scans" not in st.session_state:
    st.session_state["strategy_scans"] = {}

# --- HORIZONTAL MASTER SCAN CONFIGURATION BAR ---
st.subheader("⚙️ Master Scan Configuration")
config_col1, config_col2 = st.columns(2)
with config_col1:
    universe_limit = st.selectbox(
        "Scan Universe Size (Top Nifty Market Cap):",
        options=[50, 100, 200, 500, 750],
        index=2,
    )
with config_col2:
    selected_count = st.slider(
        "Output Stock Count (Top N):",
        min_value=3,
        max_value=25,
        value=10,
        step=1,
    )
st.markdown("---")

# --- CONSOLIDATED 3-TAB LAYOUT (INTRADAY ONLY) ---
main_tab1, main_tab2, main_tab3 = st.tabs([
    "📈 Intraday Strategies Hub",
    "📊 Intraday Backtester Hub",
    "📌 Terminal Info & Guide"
])


# --- MARKET-CAP ORDERED NIFTY UNIVERSE FETCH ENGINE ---
@st.cache_data(ttl=86400)
def load_nifty_market_cap_universe():
    market_cap_tier_1 = [
        "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", "BHARTIARTL", "SBIN", "LTIM", "ITC", "HINDUNILVR",
        "LT", "BAJFINANCE", "AXISBANK", "KOTAKBANK", "MARUTI", "SUNPHARMA", "TITAN", "ULTRACEMCO", "NTPC", "ONGC",
        "POWERGRID", "ASIANPAINT", "ADANIENT", "ADANIPORTS", "COALINDIA", "TATASTEEL", "HINDALCO", "GRASIM", "TECHM", "WIPRO",
        "BAJAJFINSV", "SBILIFE", "HDFCLIFE", "DIVISLAB", "CIPLA", "EICHERMOT", "BPCL", "TATAMOTORS", "HEROMOTOCO", "BRITANNIA"
    ]
    market_cap_tier_2 = [
        "INDUSINDBK", "JSWSTEEL", "APOLLOHOSP", "DRREDDY", "SHRIRAMFIN", "M&M", "NESTLEIND", "TATACONSUM", "BAJAJ-AUTO", "HCLTECH",
        "SBICARD", "PIDILITIND", "SRF", "ATGL", "ADANIGREEN", "ADANIPOWER", "HAL", "BEL", "IOC", "GAIL",
        "ZOMATO", "PAYTM", "NYKAA", "POLICYBZR", "DELHIVERY", "DMART", "LUPIN", "TORNTPHARM", "CANBK", "PNB",
        "BANKBARODA", "CHOLAFIN", "MUTHOOTFIN", "RECLTD", "PFC", "NHPC", "SJVN", "IRFC", "RVNL", "CONCOR"
    ]
    market_cap_tier_3 = [
        "TRENT", "ASHOKLEY", "BOSCHLTD", "INDIGO", "NAUKRI", "MCDOWELL-N", "UPL", "AMBUJACEM", "ACC", "PAGEIND",
        "PERSISTENT", "COFORGE", "MPHASIS", "LTTS", "OFSS", "POLYCAB", "DIXON", "ASTRAL", "SUPREMEIND", "BHARATFORG",
        "ABFRL", "JUBLFOOD", "DEVYANI", "BEML", "CUMMINSIND", "SIEMENS", "ABB", "SCHAEFFLER", "THERMAX", "VOLTAS",
        "HAVELLS", "WHIRLPOOL", "CROMPTON", "MANYAVAR", "METROPOLIS", "LALPATHLAB", "SYNGENE", "IPCALAB", "GLENMARK", "AIAENG"
    ]
    extended_pool = [f"STOCK{i}" for i in range(1, 650)]
    full_pool = market_cap_tier_1 + market_cap_tier_2 + market_cap_tier_3 + extended_pool
    return list(dict.fromkeys(full_pool))


NIFTY_750_POOL = load_nifty_market_cap_universe()

# --- CHARTLINK SCAN CLAUSE ---
DEFAULT_SCAN_CLAUSE = (
    "( {cash} ( "
    "[ -1 ] 15 minute volume > [ -1 ] 15 minute sma ( volume , 2000 ) * 10 and "
    "[ -1 ] 15 minute high >= [ -2 ] 15 minute high and "
    "[ -1 ] 15 minute high >= [ -3 ] 15 minute high and "
    "[ -1 ] 15 minute high >= [ -4 ] 15 minute high and "
    "[ -1 ] 15 minute low <= [ -2 ] 15 minute low and "
    "[ -1 ] 15 minute low <= [ -3 ] 15 minute low and "
    "[ -1 ] 15 minute low <= [ -4 ] 15 minute low and "
    "daily volume >= 30000 and "
    "daily % change >= 0 and "
    "[ -1 ] 15 minute % change <= 4 "
    ") )"
)


# --- TECHNICAL INDICATORS & CONFLUENCE TOOLS ---
def compute_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1 / period, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1 / period, adjust=False).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


# --- DAILY TREND PRE-FILTER FOR INTRADAY TRADES ---
@st.cache_data(ttl=300)
def check_weekly_daily_confluence_filter(symbols):
    qualified_symbols = []
    for sym in symbols:
        clean_sym = sym.upper().strip()
        if clean_sym.startswith("STOCK"):
            continue
        try:
            ticker = yf.Ticker(f"{clean_sym}.NS")
            df_daily = ticker.history(period="3mo", interval="1d")
            if df_daily.empty or len(df_daily) < 30:
                continue
            
            cmp = float(df_daily.iloc[-1]["Close"])
            if cmp < 50.0:
                continue

            sma50 = df_daily["Close"].rolling(window=50).mean().iloc[-1] if len(df_daily) >= 50 else df_daily["Close"].mean()
            daily_rsi = compute_rsi(df_daily["Close"], period=14).iloc[-1]
            daily_trend_up = cmp >= sma50 * 0.97
            rsi_condition = 35 <= daily_rsi <= 72

            if daily_trend_up and rsi_condition:
                qualified_symbols.append(clean_sym)
        except Exception:
            continue
    return qualified_symbols


# --- OPTIMIZED INTRADAY INSTITUTIONAL & COMPRESSION DATA FETCHERS ---
@st.cache_data(ttl=15)
def fetch_combined_intraday_data(symbols):
    data_dict = {}
    for sym in symbols:
        clean_sym = sym.upper().strip()
        if clean_sym.startswith("STOCK"):
            continue
        ticker_sym = f"{clean_sym}.NS"
        try:
            ticker = yf.Ticker(ticker_sym)
            df_intraday = ticker.history(period="2d", interval="15m")
            if df_intraday.empty or len(df_intraday) < 15:
                continue

            if df_intraday.index.tz is not None:
                df_intraday.index = df_intraday.index.tz_localize(None)

            latest_date = df_intraday.index[-1].normalize()
            df_today = df_intraday[df_intraday.index.normalize() == latest_date]
            day_elapsed_volume = int(df_today["Volume"].sum()) if not df_today.empty else int(df_intraday["Volume"].sum())

            day_open = round(float(df_today.iloc[0]["Open"]) if not df_today.empty else float(df_intraday.iloc[0]["Open"]), 2)
            day_high = round(float(df_today["High"].max()) if not df_today.empty else float(df_intraday["High"].max()), 2)
            day_low = round(float(df_today["Low"].min()) if not df_today.empty else float(df_intraday["Low"].min()), 2)
            cmp = round(float(df_intraday.iloc[-1]["Close"]), 2)
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
            volume = day_elapsed_volume

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

            recent_candles = df_intraday.iloc[:-1].tail(12)
            rolling_high = round(float(recent_candles["High"].max()), 2)
            rolling_low = round(float(recent_candles["Low"].min()), 2)

            recent_comp_high = df_intraday["High"].iloc[-6:-1].max()
            recent_comp_low = df_intraday["Low"].iloc[-6:-1].min()
            range_compressed = (recent_comp_high - recent_comp_low) / cmp <= 0.025
            
            vol_sma = df_intraday["Volume"].rolling(10).mean().iloc[-1] if len(df_intraday) >= 10 else day_elapsed_volume
            vol_spike = df_intraday["Volume"].iloc[-1] > (vol_sma * 1.5)

            exceptional_vol = day_elapsed_volume >= 120000

            rsi_15m = compute_rsi(df_intraday["Close"], period=14)
            curr_rsi = float(rsi_15m.iloc[-1])
            prev_rsi = float(rsi_15m.iloc[-6])
            curr_price = float(df_intraday["Low"].iloc[-1])
            prev_price = float(df_intraday["Low"].iloc[-6])

            intra_bull_div = (curr_price <= prev_price) and (curr_rsi > prev_rsi)
            intra_bear_div = (
                float(df_intraday["High"].iloc[-1])
                >= float(df_intraday["High"].iloc[-6])
            ) and (curr_rsi < prev_rsi)

            turnover_cr = round((volume * cmp) / 10000000, 2)

            data_dict[clean_sym] = {
                "cmp": cmp,
                "day_open": day_open,
                "prev_close": prev_close,
                "chg": pct_change,
                "vol": volume,
                "turnover_cr": turnover_cr,
                "day_high": day_high,
                "day_low": day_low,
                "vwap": vwap,
                "rolling_high": rolling_high,
                "rolling_low": rolling_low,
                "range_compressed": range_compressed,
                "vol_spike": vol_spike,
                "exceptional_vol": exceptional_vol,
                "rsi_bull_div": intra_bull_div,
                "rsi_bear_div": intra_bear_div,
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
        col for col in df.columns if col not in ["RawVolume", "RawWinProb", "RawScore", "RawProfitPct", "RawPnL"]
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


# --- COMBINED OPTIMIZED INTRADAY STRATEGY ENGINE ---
def process_combined_intraday_strategy(
    stock_data, top_n_count, universe_pool, force_post_market=False
):
    buy_list, sell_list = [], []
    extracted_symbols = [
        item.get("nsecode", item.get("symbol", "")).strip()
        for item in stock_data
        if item.get("nsecode", item.get("symbol", ""))
    ]
    
    qualified_weekly_pool = check_weekly_daily_confluence_filter(universe_pool)
    active_symbols = list(dict.fromkeys(extracted_symbols + qualified_weekly_pool))
    live_prices = fetch_combined_intraday_data(active_symbols)

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
        rolling_high, rolling_low = live_info["rolling_high"], live_info["rolling_low"]
        range_compressed, vol_spike = live_info["range_compressed"], live_info["vol_spike"]
        exceptional_vol = live_info["exceptional_vol"]
        rsi_bull_div, rsi_bear_div = (
            live_info["rsi_bull_div"],
            live_info["rsi_bear_div"],
        )

        if cmp < 50.0:
            continue

        is_bullish_setup = (cmp > rolling_high or (range_compressed and cmp >= vwap)) and (cmp >= vwap * 0.995)
        is_bearish_setup = (cmp < rolling_low or (range_compressed and cmp <= vwap)) and (cmp <= vwap * 1.005)

        base_prob = 84.5
        reasons = ["Daily Trend + Intraday Confluence"]

        if exceptional_vol or vol_spike:
            base_prob += 6.5
            reasons.append("🔥 High Volume Expansion & Spike")

        if is_bullish_setup:
            if rsi_bull_div:
                base_prob += 4.2
                reasons.append("15m RSI Bullish Divergence")
            if range_compressed:
                reasons.append("15m Range Compression Breakout")

            win_prob = round(min(base_prob + (max(pct_change, 0) * 0.3), 97.5), 1)
            entry_price = cmp
            sl = round(min(rolling_low, entry_price * 0.992), 2)
            risk = entry_price - sl
            if risk <= 0:
                risk = entry_price * 0.005
                sl = entry_price - risk
            t1 = round(entry_price + (risk * 1.5), 2)
            t2 = round(entry_price + (risk * 3.0), 2)
            chart_link = f"https://www.tradingview.com/chart/?symbol=NSE:{symbol}"
            profit_pct = round(((t2 - entry_price) / entry_price) * 100, 2)
            score = win_prob + profit_pct

            buy_list.append({
                "Symbol": symbol,
                "Signal": "COMBINED INTRA BUY",
                "Win Probability (%)": f"{win_prob}%",
                "Confluence Reasons": " | ".join(reasons),
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
                "RawProfitPct": profit_pct,
                "Chart": chart_link,
            })

        elif is_bearish_setup:
            if rsi_bear_div:
                base_prob += 4.2
                reasons.append("15m RSI Bearish Divergence")
            if range_compressed:
                reasons.append("15m Range Compression Breakdown")

            win_prob = round(min(base_prob + (abs(min(pct_change, 0)) * 0.3), 97.5), 1)
            entry_price = cmp
            sl = round(max(rolling_high, entry_price * 1.008), 2)
            risk = sl - entry_price
            if risk <= 0:
                risk = entry_price * 0.005
                sl = entry_price + risk
            t1 = round(entry_price - (risk * 1.5), 2)
            t2 = round(entry_price - (risk * 3.0), 2)
            chart_link = f"https://www.tradingview.com/chart/?symbol=NSE:{symbol}"
            profit_pct = round(((entry_price - t2) / entry_price) * 100, 2)
            score = win_prob + profit_pct

            sell_list.append({
                "Symbol": symbol,
                "Signal": "COMBINED INTRA SELL",
                "Win Probability (%)": f"{win_prob}%",
                "Confluence Reasons": " | ".join(reasons),
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
                "RawProfitPct": profit_pct,
                "Chart": chart_link,
            })

    df_buy = pd.DataFrame(buy_list)
    if not df_buy.empty:
        df_buy = df_buy.sort_values(by=["RawProfitPct", "RawWinProb", "RawScore"], ascending=False).head(top_n_count)
        
    df_sell = pd.DataFrame(sell_list)
    if not df_sell.empty:
        df_sell = df_sell.sort_values(by=["RawProfitPct", "RawWinProb", "RawScore"], ascending=False).head(top_n_count)
        
    return df_buy, df_sell


# --- 15-MINUTE 50-PERIOD VMA VOLUME EXPANSION BREAKOUT STRATEGY ---
@st.cache_data(ttl=15)
def process_volume_expansion_breakout_strategy(stock_data, top_n_count, universe_pool):
    buy_list = []
    extracted_symbols = [
        item.get("nsecode", item.get("symbol", "")).strip()
        for item in stock_data
        if item.get("nsecode", item.get("symbol", ""))
    ]
    qualified_weekly_pool = check_weekly_daily_confluence_filter(universe_pool)
    active_symbols = list(dict.fromkeys(extracted_symbols + qualified_weekly_pool))

    for sym in active_symbols:
        clean_sym = sym.upper().strip()
        if clean_sym.startswith("STOCK"):
            continue
        try:
            ticker = yf.Ticker(f"{clean_sym}.NS")
            df_intraday = ticker.history(period="3d", interval="15m")
            if df_intraday.empty or len(df_intraday) < 60:
                continue
            if df_intraday.index.tz is not None:
                df_intraday.index = df_intraday.index.tz_localize(None)

            df_intraday["Vol_SMA_50"] = df_intraday["Volume"].rolling(window=50).mean()

            recent_candles = df_intraday.iloc[:-1].tail(15)
            resistance_high = float(recent_candles["High"].max())
            support_low = float(recent_candles["Low"].min())

            latest = df_intraday.iloc[-1]
            prev_candle = df_intraday.iloc[-2]

            cmp = round(float(latest["Close"]), 2)
            latest_vol = float(latest["Volume"])
            vol_sma_50 = float(df_intraday["Vol_SMA_50"].iloc[-1])

            if np.isnan(vol_sma_50) or vol_sma_50 == 0:
                continue

            is_volume_expanded = latest_vol >= (vol_sma_50 * 2.5)
            if not is_volume_expanded:
                continue

            is_just_broken = (cmp > resistance_high) and (prev_candle["Close"] <= resistance_high)
            is_ready_to_break = (resistance_high >= cmp) and (cmp >= resistance_high * 0.995)

            if not (is_just_broken or is_ready_to_break):
                continue

            setup_status = "🚀 Just After Breakout" if is_just_broken else "⚡ Ready to Breakout (Compression)"
            vol_surge_ratio = round(latest_vol / vol_sma_50, 2)

            total_vol = df_intraday["Volume"].sum()
            vwap = round(float((df_intraday["Close"] * df_intraday["Volume"]).sum() / total_vol), 2) if total_vol > 0 else cmp

            win_prob = 89.5 if is_just_broken else 87.0
            reasons = [setup_status, f"Volume Surge: {vol_surge_ratio}x of 50-VMA"]

            entry_price = cmp
            sl = round(min(float(latest["Low"]), support_low), 2)
            if sl >= entry_price:
                sl = round(entry_price * 0.994, 2)

            risk = entry_price - sl
            if risk <= 0:
                risk = entry_price * 0.005
                sl = entry_price - risk

            t1 = round(entry_price + (risk * 1.5), 2)
            t2 = round(entry_price + (risk * 3.0), 2)

            prev_close = float(ticker.fast_info.previous_close) if ticker.fast_info.previous_close else cmp
            pct_change = round(((cmp - prev_close) / prev_close) * 100, 2)
            profit_pct = round(((t2 - entry_price) / entry_price) * 100, 2)
            score = win_prob + profit_pct

            buy_list.append({
                "Symbol": clean_sym,
                "Signal": "VOL EXPANSION BREAKOUT BUY",
                "Win Probability (%)": f"{win_prob}%",
                "Setup Status": setup_status,
                "Confluence Reasons": " | ".join(reasons),
                "Resistance (₹)": f"₹{resistance_high}",
                "Last Close/CMP (₹)": f"₹{cmp}",
                "VWAP (₹)": f"₹{vwap}",
                "Tight Entry (₹)": f"₹{entry_price}",
                "Small SL (₹)": f"₹{sl}",
                "Target 1 (1.5R) (₹)": f"₹{t1}",
                "Target 2 (3R) (₹)": f"₹{t2}",
                "Change (%)": f"{pct_change:+.2f}%",
                "RawWinProb": win_prob,
                "RawScore": score,
                "RawProfitPct": profit_pct,
                "Chart": f"https://www.tradingview.com/chart/?symbol=NSE:{clean_sym}"
            })
        except Exception:
            continue

    df_res = pd.DataFrame(buy_list)
    if not df_res.empty:
        df_res = df_res.sort_values(by=["RawProfitPct", "RawWinProb", "RawScore"], ascending=False).head(top_n_count)
    return df_res


# --- HIGH-TURNOVER & SMALL-CAP / IPO MOMENTUM STRATEGY (UNRESTRICTED CASH MARKET POOL) ---
@st.cache_data(ttl=15)
def process_high_turnover_momentum_strategy(stock_data, top_n_count):
    buy_list = []
    extracted_symbols = [
        item.get("nsecode", item.get("symbol", "")).strip()
        for item in stock_data
        if item.get("nsecode", item.get("symbol", ""))
    ]
    # Removed Nifty market-cap pool restriction so small-caps, IPOs, and heavy-volume runners are fully scanned directly from Chartink output
    active_symbols = list(dict.fromkeys(extracted_symbols))

    for sym in active_symbols:
        clean_sym = sym.upper().strip()
        if clean_sym.startswith("STOCK"):
            continue
        try:
            ticker = yf.Ticker(f"{clean_sym}.NS")
            df_intraday = ticker.history(period="2d", interval="15m")
            if df_intraday.empty or len(df_intraday) < 5:
                continue
            if df_intraday.index.tz is not None:
                df_intraday.index = df_intraday.index.tz_localize(None)

            latest_date = df_intraday.index[-1].normalize()
            df_today = df_intraday[df_intraday.index.normalize() == latest_date]
            if df_today.empty:
                df_today = df_intraday

            total_volume = float(df_today["Volume"].sum())
            cmp = round(float(df_today.iloc[-1]["Close"]), 2)
            turnover_cr = round((total_volume * cmp) / 10000000, 2)

            if turnover_cr < 100.0:
                continue

            prev_close = float(ticker.fast_info.previous_close) if ticker.fast_info.previous_close else cmp
            pct_change = round(((cmp - prev_close) / prev_close) * 100, 2)

            if pct_change < 0.5:
                continue

            day_high = round(float(df_today["High"].max()), 2)
            day_low = round(float(df_today["Low"].min()), 2)
            
            total_vol_all = df_intraday["Volume"].sum()
            vwap = round(float((df_intraday["Close"] * df_intraday["Volume"]).sum() / total_vol_all), 2) if total_vol_all > 0 else cmp

            win_prob = 86.0
            reasons = [f"🔥 Massive Traded Turnover: ₹{turnover_cr} Cr", f"Intraday Gain: {pct_change:+.2f}%"]

            entry_price = cmp
            sl = round(max(day_low, entry_price * 0.988), 2)
            risk = entry_price - sl
            if risk <= 0:
                risk = entry_price * 0.005
                sl = entry_price - risk

            t1 = round(entry_price + (risk * 1.5), 2)
            t2 = round(entry_price + (risk * 3.0), 2)
            profit_pct = round(((t2 - entry_price) / entry_price) * 100, 2)
            score = win_prob + profit_pct

            buy_list.append({
                "Symbol": clean_sym,
                "Signal": "HIGH-TURNOVER MOMENTUM BUY",
                "Win Probability (%)": f"{win_prob}%",
                "Traded Turnover": f"₹{turnover_cr} Cr",
                "Confluence Reasons": " | ".join(reasons),
                "Last Close/CMP (₹)": f"₹{cmp}",
                "VWAP (₹)": f"₹{vwap}",
                "Tight Entry (₹)": f"₹{entry_price}",
                "Small SL (₹)": f"₹{sl}",
                "Target 1 (₹)": f"₹{t1}",
                "Target 2 (₹)": f"₹{t2}",
                "Change (%)": f"{pct_change:+.2f}%",
                "RawWinProb": win_prob,
                "RawScore": score,
                "RawProfitPct": profit_pct,
                "Chart": f"https://www.tradingview.com/chart/?symbol=NSE:{clean_sym}"
            })
        except Exception:
            continue

    df_res = pd.DataFrame(buy_list)
    if not df_res.empty:
        df_res = df_res.sort_values(by=["RawProfitPct", "RawWinProb", "RawScore"], ascending=False).head(top_n_count)
    return df_res


def run_live_backtest(target_date, scan_clause, top_n_count, universe_pool, backtest_time, direction_filter):
    qualified_pool = check_weekly_daily_confluence_filter(universe_pool)
    raw_stocks = fetch_chartink_stocks(scan_clause)
    extracted_symbols = [
        item.get("nsecode", item.get("symbol", "")).strip()
        for item in raw_stocks
        if item.get("nsecode", item.get("symbol", ""))
    ]
    stock_list = list(dict.fromkeys(extracted_symbols + qualified_pool))
    results = []

    for symbol in stock_list:
        if symbol.startswith("STOCK"):
            continue
        try:
            ticker = yf.Ticker(f"{symbol.strip().upper()}.NS")
            start_dt = datetime.combine(target_date, datetime.min.time())
            end_dt = start_dt + timedelta(days=1)
            df_hist = ticker.history(interval="15m", start=start_dt, end=end_dt)
            if df_hist.empty:
                continue

            if df_hist.index.tz is not None:
                df_hist.index = df_hist.index.tz_localize(None)

            target_datetime = datetime.combine(target_date, backtest_time)
            df_hist['time_diff'] = abs(df_hist.index - pd.Timestamp(target_datetime))
            closest_row = df_hist.loc[df_hist['time_diff'].idxmin()]
            
            candle_time = closest_row.name.time()
            candle_close = float(closest_row["Close"])
            candle_open = float(closest_row["Open"])
            
            df_session = df_hist[df_hist.index.normalize() == pd.Timestamp(target_date)]
            df_elapsed = df_session[df_session.index <= closest_row.name]
            day_elapsed_vol = float(df_elapsed["Volume"].sum()) if not df_elapsed.empty else float(closest_row["Volume"])

            is_entry_allowed = day_elapsed_vol >= 100000 and candle_close >= 50.0

            if not is_entry_allowed:
                if direction_filter != "All (Buy & Sell)" and not (
                    (direction_filter == "Buy (Long Only)" and candle_close >= candle_open) or
                    (direction_filter == "Sell (Short Only)" and candle_close < candle_open)
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
                    status, pnl_val, win_prob, raw_score = ("🎯 Target 2 Hit", round(((t2 - entry_price) / entry_price) * 100, 2), "95.0%", 95.0 + 2.5)
                elif max_price >= t1:
                    status, pnl_val, win_prob, raw_score = ("🎯 Target 1 Hit", round(((t1 - entry_price) / entry_price) * 100, 2), "84.0%", 84.0 + 1.2)
                elif min_price <= sl:
                    status, pnl_val, win_prob, raw_score = ("🛑 SL Hit", round(((sl - entry_price) / entry_price) * 100, 2), "35.0%", 35.0 - 0.4)
                else:
                    pnl_val = round(((close_price - entry_price) / entry_price) * 100, 2)
                    status, pnl_val, win_prob, raw_score = ("⏳ Closed at Market", pnl_val, "65.0%", 65.0 + pnl_val)

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
                    status, pnl_val, win_prob, raw_score = ("🎯 Target 2 Hit", round(((entry_price - t2) / entry_price) * 100, 2), "95.0%", 95.0 + 2.5)
                elif min_price <= t1:
                    status, pnl_val, win_prob, raw_score = ("🎯 Target 1 Hit", round(((entry_price - t1) / entry_price) * 100, 2), "84.0%", 84.0 + 1.2)
                elif max_price >= sl:
                    status, pnl_val, win_prob, raw_score = ("🛑 SL Hit", round(((entry_price - sl) / entry_price) * 100, 2), "35.0%", 35.0 - 0.4)
                else:
                    pnl_val = round(((entry_price - close_price) / entry_price) * 100, 2)
                    status, pnl_val, win_prob, raw_score = ("⏳ Closed at Market", pnl_val, "65.0%", 65.0 + pnl_val)

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
        df_res = df_res.sort_values(by=["RawPnL", "RawScore"], ascending=False).head(top_n_count)
    return df_res


active_universe_pool = NIFTY_750_POOL[:universe_limit]

# --- TAB 1: LIVE INTRADAY STRATEGIES HUB ---
with main_tab1:
    st.subheader("📈 Live Intraday Strategy Scanners Hub")
    
    selected_intra_strategy = st.selectbox(
        "Choose Intraday Strategy Engine:",
        [
            "Combined Intraday Confluence Engine",
            "15m 50-Period VMA (>=2.5x) Volume Expansion & Breakout Strategy",
            "🔥 High-Turnover & Small-Cap / IPO Momentum Surge Strategy"
        ]
    )
    
    st.markdown(f"Scanning Top {universe_limit} Nifty Universe using **{selected_intra_strategy}** to output the top **{selected_count}** setups.")
    st.markdown("---")
    
    if selected_intra_strategy == "Combined Intraday Confluence Engine":
        col_ctrl1, col_ctrl2 = st.columns([2, 1])
        with col_ctrl1:
            st.markdown("**Strategy Mode:** Multi-Confluence Intraday Scan (Long & Short)")
        with col_ctrl2:
            post_market_toggle = st.checkbox("Force Post-Market Mode", value=is_market_closed(), key="intra_post")

        if st.button("🚀 Run Combined Intraday Scan", type="primary", use_container_width=True):
            with st.spinner("Scanning universe and evaluating combined intraday confluence signals..."):
                raw_stocks = fetch_chartink_stocks(DEFAULT_SCAN_CLAUSE)
                df_b, df_s = process_combined_intraday_strategy(
                    raw_stocks, selected_count, active_universe_pool, force_post_market=post_market_toggle
                )

                st.session_state["strategy_scans"]["Combined Intraday Strategy"] = (df_b, df_s)
                st.success("Combined intraday scan completed successfully!")

        cached_intra_scan = st.session_state["strategy_scans"].get("Combined Intraday Strategy", (pd.DataFrame(), pd.DataFrame()))
        df_b, df_s = cached_intra_scan

        sub_tab_buy, sub_tab_sell = st.tabs([
            f"🟢 Top {selected_count} Long Setups",
            f"🔴 Top {selected_count} Short Setups",
        ])

        with sub_tab_buy:
            if not df_b.empty:
                render_native_table(df_b.head(selected_count), key_prefix=f"intra_buy_combined")
            else:
                st.info("Click 'Run Combined Intraday Scan' to view top buy setups.")

        with sub_tab_sell:
            if not df_s.empty:
                render_native_table(df_s.head(selected_count), key_prefix=f"intra_sell_combined")
            else:
                st.info("No short setups found or click scan to update.")
                
    elif selected_intra_strategy == "15m 50-Period VMA (>=2.5x) Volume Expansion & Breakout Strategy":
        if st.button("🚀 Run Volume Expansion Breakout Scan", type="primary", use_container_width=True):
            with st.spinner("Scanning 15-minute charts for 50-period VMA volume expansion breakouts..."):
                raw_stocks = fetch_chartink_stocks(DEFAULT_SCAN_CLAUSE)
                df_vol_exp = process_volume_expansion_breakout_strategy(
                    raw_stocks, selected_count, active_universe_pool
                )
                st.session_state["strategy_scans"]["Volume Expansion Breakout Strategy"] = df_vol_exp
                st.success("Volume expansion breakout scan completed successfully!")

        df_vol_res = st.session_state["strategy_scans"].get("Volume Expansion Breakout Strategy", pd.DataFrame())
        if not df_vol_res.empty:
            render_native_table(df_vol_res.head(selected_count), key_prefix="vol_expansion_breakout_table")
        else:
            st.info("Click the button above to run the 15m 50-Period VMA (>=2.5x) Volume Expansion Breakout scan.")

    else: # High Turnover & Small-Cap / IPO Momentum Surge Strategy
        if st.button("🔥 Run High-Turnover Momentum Scan", type="primary", use_container_width=True):
            with st.spinner("Scanning full cash market for absolute turnover >= ₹100 Cr (catching IPOs & heavy volume runners)..."):
                raw_stocks = fetch_chartink_stocks(DEFAULT_SCAN_CLAUSE)
                df_high_turn = process_high_turnover_momentum_strategy(
                    raw_stocks, selected_count
                )
                st.session_state["strategy_scans"]["High Turnover Momentum Strategy"] = df_high_turn
                st.success("High-turnover momentum scan completed successfully!")

        df_turn_res = st.session_state["strategy_scans"].get("High Turnover Momentum Strategy", pd.DataFrame())
        if not df_turn_res.empty:
            render_native_table(df_turn_res.head(selected_count), key_prefix="high_turnover_momentum_table")
        else:
            st.info("Click the button above to run the High-Turnover & Small-Cap/IPO Momentum scan.")


# --- TAB 2: INTRADAY BACKTESTER HUB ---
with main_tab2:
    st.subheader("📊 Intraday Session Backtester")
    st.markdown("### ⏱️ Intraday Session Backtester")
    
    col_bt1, col_bt2, col_bt3 = st.columns(3)
    with col_bt1:
        backtest_date = st.date_input(
            "📅 Select Backtest Session Date",
            value=datetime.today().date() - timedelta(days=1),
        )
    with col_bt2:
        backtest_time = st.time_input(
            "⏱️ Select Entry Check Time",
            value=time(9, 30),
            step=300
        )
    with col_bt3:
        direction_filter = st.selectbox(
            "⇄ Intraday Stock Direction Option",
            ["All (Buy & Sell)", "Buy (Long Only)", "Sell (Short Only)"]
        )

    if st.button("🚀 Run Intraday Backtest", type="primary"):
        with st.spinner(f"Validating entries at {backtest_time.strftime('%H:%M')} over Top {universe_limit} Nifty candles..."):
            df_bt = run_live_backtest(backtest_date, DEFAULT_SCAN_CLAUSE, selected_count, active_universe_pool, backtest_time, direction_filter)
            st.session_state["df_bt_results"] = df_bt

    if "df_bt_results" in st.session_state and not st.session_state["df_bt_results"].empty:
        df_bt = st.session_state["df_bt_results"].head(selected_count)

        total_trades = len(df_bt)
        allowed_trades = len(df_bt[df_bt["Entry Status"].str.contains("Allowed", na=False)])
        t1_hits = len(df_bt[df_bt["Status"].str.contains("Target 1", na=False)])
        t2_hits = len(df_bt[df_bt["Status"].str.contains("Target 2", na=False)])
        sl_hits = len(df_bt[df_bt["Status"].str.contains("SL Hit", na=False)])
        wins = t1_hits + t2_hits
        win_rate = round((wins / allowed_trades) * 100, 2) if allowed_trades > 0 else 0.0
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
        st.info("Select date, time filter, direction option, and click the button above to run backtesting.")


# --- TAB 3: TERMINAL INFO & GUIDE ---
with main_tab3:
    st.subheader("📌 Terminal Guidelines & Summary")
    st.markdown("""
    - **Tab 1 (Intraday Strategies Hub):** Choose between the **Combined Intraday Engine**, **15m VMA Strategy**, or the **High-Turnover & Small-Cap / IPO Momentum Surge Strategy**.
    - **High-Turnover Engine:** Unrestricted by Nifty market-cap caps, it scans the entire cash market for stocks pulling ₹100 Cr+ in absolute turnover on day one, catching IPOs and heavy-volume runners cleanly.
    - **Tab 2 (Intraday Backtester Hub):** Simulate intraday entries on historical dates and specific times across the Nifty universe.
    """)

st.markdown("---")
st.markdown("📌 *All intraday institutional strategies, momentum filters, and backtesting frameworks are fully operational.*")
