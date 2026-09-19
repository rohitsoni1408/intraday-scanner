import datetime
from datetime import datetime, time, timedelta
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import requests
import streamlit as st
import yfinance as yf

# Page Configuration
st.set_page_config(
    page_title="Ultimate Multi-Timeframe Confluence Terminal", layout="wide"
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

# --- PASSCODE AUTHENTICATION ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 🔒 Secure Terminal")
        st.markdown("Enter your security passcode to access elite trade flows.")
        passcode_input = st.text_input("Passcode:", type="password")
        if st.button(
            "🔓 Authenticate Terminal", type="primary", use_container_width=True
        ):
            if passcode_input == "Ginni":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect passcode. Access denied.")
    st.stop()

# --- MAIN APP ---
st.title("👑 NSE Ultimate Master Confluence Engine (Nifty 750 Universe)")
st.markdown(
    "Trading Terminal featuring **Direct TradingView Chart Links**, **Frozen "
    "Symbol Column**, **Intraday RSI Divergence**, **Exceptional Volume Filter**, and a **Dropdown Strategy Selector** for Weekly/Swing Setups."
)

# Intraday stays completely untouched as requested, separate from the weekly selector tab
main_tab1, main_tab2, main_tab3 = st.tabs([
    "⚡ Intraday Engine",
    "📊 Intraday Backtester",
    "🗓️ Weekly & Swing Strategy Hub"
])


# --- DYNAMIC TOP NIFTY 750 UNIVERSE FETCH ENGINE ---
@st.cache_data(ttl=86400)
def load_nifty_750_symbols():
    url_500 = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    symbols = []
    try:
        df_500 = pd.read_csv(url_500)
        symbols.extend(df_500["Symbol"].dropna().str.strip().tolist())
    except Exception:
        pass
    
    fallback_pool = [
        "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "BHARTIARTL", "ITC", "LT", "HINDUNILVR",
        "AXISBANK", "KOTAKBANK", "SUNPHARMA", "TITAN", "BAJFINANCE", "MARUTI", "NTPC", "POWERGRID", "ASIANPAINT", "ULTRACEMCO",
        "WIPRO", "ONGC", "TITAN", "ADANIENT", "ADANIPORTS", "COALINDIA", "TATASTEEL", "HINDALCO", "GRASIM", "TECHM"
    ]
    symbols.extend(fallback_pool)
    return list(dict.fromkeys(symbols))


NIFTY_750_POOL = load_nifty_750_symbols()
DEFAULT_SCAN_CLAUSE = "( {cash} ( [0] 15 minute close > [0] 15 minute vwap and [0] 15 minute volume > 100000 and [0] 15 minute close > 50 ) )"


def is_market_closed():
    now = datetime.now()
    if now.weekday() >= 5:
        return True
    market_open = time(9, 15)
    market_close = time(15, 30)
    return not (market_open <= now.time() <= market_close)


# --- TECHNICAL INDICATORS & CONFLUENCE TOOLS ---
def compute_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1 / period, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1 / period, adjust=False).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def compute_macd(series, fast=12, slow=26, signal=9):
    exp1 = series.ewm(span=fast, adjust=False).mean()
    exp2 = series.ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    hist = macd - signal_line
    return macd, signal_line, hist


def compute_bollinger_bands(series, window=20, num_std=2):
    sma = series.rolling(window=window).mean()
    std = series.rolling(window=window).std()
    upper_band = sma + (std * num_std)
    lower_band = sma - (std * num_std)
    return upper_band, sma, lower_band


def compute_supertrend(df, period=10, multiplier=3):
    hl2 = (df["High"] + df["Low"]) / 2
    atr = (df["High"] - df["Low"]).rolling(window=period).mean()
    upper_band = hl2 + (multiplier * atr)
    lower_band = hl2 - (multiplier * atr)
    
    trend = pd.Series(1, index=df.index)
    for i in range(1, len(df)):
        if df["Close"].iloc[i] > upper_band.iloc[i-1]:
            trend.iloc[i] = 1
        elif df["Close"].iloc[i] < lower_band.iloc[i-1]:
            trend.iloc[i] = -1
        else:
            trend.iloc[i] = trend.iloc[i-1]
            if trend.iloc[i] == 1 and lower_band.iloc[i] < lower_band.iloc[i-1]:
                lower_band.iloc[i] = lower_band.iloc[i-1]
            if trend.iloc[i] == -1 and upper_band.iloc[i] > upper_band.iloc[i-1]:
                upper_band.iloc[i] = upper_band.iloc[i-1]
                
    return trend


def compute_volume_profile_poc(df, bins=15):
    if df.empty or "Volume" not in df.columns:
        return round(float(df["Close"].iloc[-1]), 2)
    price_min = df["Low"].min()
    price_max = df["High"].max()
    if price_min == price_max:
        return round(price_min, 2)

    counts, bin_edges = np.histogram(
        df["Close"], bins=bins, weights=df["Volume"]
    )
    poc_idx = np.argmax(counts)
    poc_price = (bin_edges[poc_idx] + bin_edges[poc_idx + 1]) / 2
    return round(float(poc_price), 2)


# --- DATA FETCHERS ---
@st.cache_data(ttl=15)
def fetch_live_market_data(symbols):
    data_dict = {}
    for sym in symbols:
        clean_sym = sym.upper().strip()
        ticker_sym = f"{clean_sym}.NS"
        try:
            ticker = yf.Ticker(ticker_sym)
            df_intraday = ticker.history(period="2d", interval="5m")
            if df_intraday.empty or len(df_intraday) < 15:
                continue

            day_open = round(float(df_intraday.iloc[0]["Open"]), 2)
            day_high = round(float(df_intraday["High"].max()), 2)
            day_low = round(float(df_intraday["Low"].min()), 2)
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
            volume = int(df_intraday["Volume"].sum())

            total_vol = df_intraday["Volume"].sum()
            vwap = (
                round(
                    float(
                        (
                            df_intraday["Close"] * df_intraday["Volume"]
                        ).sum()
                        / total_vol
                    ),
                    2,
                )
                if total_vol > 0
                else cmp
            )

            vol_ma = df_intraday["Volume"].rolling(window=20).mean()
            curr_candle_vol = float(df_intraday["Volume"].iloc[-1])
            avg_vol_ma = float(vol_ma.iloc[-1]) if not vol_ma.empty and not pd.isna(vol_ma.iloc[-1]) else 0.0
            exceptional_vol = curr_candle_vol > (avg_vol_ma * 1.5) if avg_vol_ma > 0 else False

            rsi_5m = compute_rsi(df_intraday["Close"], period=14)
            curr_rsi = float(rsi_5m.iloc[-1])
            prev_rsi = float(rsi_5m.iloc[-6])
            curr_price = float(df_intraday["Low"].iloc[-1])
            prev_price = float(df_intraday["Low"].iloc[-6])

            intra_bull_div = (curr_price <= prev_price) and (curr_rsi > prev_rsi)
            intra_bear_div = (
                float(df_intraday["High"].iloc[-1])
                >= float(df_intraday["High"].iloc[-6])
            ) and (curr_rsi < prev_rsi)

            data_dict[clean_sym] = {
                "cmp": cmp,
                "day_open": day_open,
                "prev_close": prev_close,
                "chg": pct_change,
                "vol": volume,
                "day_high": day_high,
                "day_low": day_low,
                "vwap": vwap,
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
    except Exception as e:
        st.error(f"Connection Error: {e}")
    return []


def render_native_table(df, key_prefix):
    if df.empty:
        st.info("No stocks found matching the current criteria.")
        return

    display_cols = [
        col for col in df.columns if col not in ["RawVolume", "RawPnL"]
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


# --- INTRADAY ENGINE (UNTOUCHED) ---
def process_ultimate_confluence(
    stock_data, top_n_count, force_post_market=False
):
    buy_list, sell_list = [], []
    extracted_symbols = [
        item.get("nsecode", item.get("symbol", "")).strip()
        for item in stock_data
        if item.get("nsecode", item.get("symbol", ""))
    ]
    active_symbols = list(
        dict.fromkeys(extracted_symbols + NIFTY_750_POOL[:40])
    )

    live_prices = fetch_live_market_data(active_symbols)
    closed = force_post_market or is_market_closed()

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
        exceptional_vol = live_info["exceptional_vol"]
        rsi_bull_div, rsi_bear_div = (
            live_info["rsi_bull_div"],
            live_info["rsi_bear_div"],
        )

        if cmp < 50.0:
            continue
        diff = day_high - day_low

        if not closed:
            if pct_change >= 0:
                fib_786 = round(day_high - (diff * 0.786), 2)
                entry_price = round(max(fib_786, vwap), 2)
                sl = round(entry_price * 0.996, 2)
                t1 = round(entry_price + (entry_price * 0.012), 2)
                t2 = round(day_high, 2)
            else:
                fib_786 = round(day_low + (diff * 0.786), 2)
                entry_price = round(min(fib_786, vwap), 2)
                sl = round(entry_price * 1.004, 2)
                t1 = round(entry_price - (entry_price * 0.012), 2)
                t2 = round(day_low, 2)
        else:
            if pct_change >= 0:
                entry_price = round(day_high - (diff * 0.50), 2)
                sl = round(entry_price * 0.994, 2)
                t1 = round(day_high, 2)
                t2 = round(day_high + (diff * 0.382), 2)
            else:
                entry_price = round(day_low + (diff * 0.50), 2)
                sl = round(entry_price * 1.006, 2)
                t1 = round(day_low, 2)
                t2 = round(day_low - (diff * 0.382), 2)

        red_reasons, green_reasons = [], []
        if abs(pct_change) > 4.5:
            red_reasons.append("Extended Move (>4.5%)")
        if volume < 200000:
            red_reasons.append("Low Volume Liquidity")

        if 1.0 <= abs(pct_change) <= 3.5:
            green_reasons.append("Healthy Momentum")
        if exceptional_vol:
            green_reasons.append("🔥 Exceptional Volume Spike")
        if rsi_bull_div and pct_change >= 0:
            green_reasons.append("5m RSI Bullish Divergence")
        if rsi_bear_div and pct_change < 0:
            green_reasons.append("5m RSI Bearish Divergence")

        chart_link = f"https://www.tradingview.com/chart/?symbol=NSE:{symbol}"

        if pct_change >= 0:
            status_tag = f"BUY ({', '.join(green_reasons) if green_reasons else 'STRONG MOMENTUM'})"
            stock_entry = {
                "Symbol": symbol,
                "Signal": "BUY",
                "Risk Analysis": status_tag,
                "Session Open (₹)": f"₹{day_open}",
                "Session High (₹)": f"₹{day_high}",
                "Session Low (₹)": f"₹{day_low}",
                "Last Close/CMP (₹)": f"₹{cmp}",
                "VWAP (₹)": f"₹{vwap}",
                "Tight Entry (₹)": f"₹{entry_price}",
                "Small SL (₹)": f"₹{sl}",
                "Target 1 (₹)": f"₹{t1}",
                "Target 2 (₹)": f"₹{t2}",
                "Change (%)": f"{pct_change:+.2f}%",
                "RawVolume": volume,
                "Chart": chart_link,
            }
            buy_list.append(stock_entry)
        else:
            status_tag = f"SELL ({', '.join(red_reasons) if red_reasons else 'WEAK STRUCTURE'})"
            stock_entry = {
                "Symbol": symbol,
                "Signal": "SELL",
                "Risk Analysis": status_tag,
                "Session Open (₹)": f"₹{day_open}",
                "Session High (₹)": f"₹{day_high}",
                "Session Low (₹)": f"₹{day_low}",
                "Last Close/CMP (₹)": f"₹{cmp}",
                "VWAP (₹)": f"₹{vwap}",
                "Tight Entry (₹)": f"₹{entry_price}",
                "Small SL (₹)": f"₹{sl}",
                "Target 1 (₹)": f"₹{t1}",
                "Target 2 (₹)": f"₹{t2}",
                "Change (%)": f"{pct_change:+.2f}%",
                "RawVolume": volume,
                "Chart": chart_link,
            }
            sell_list.append(stock_entry)

    df_buy = (
        pd.DataFrame(buy_list)
        .sort_values(by="RawVolume", ascending=False)
        .head(top_n_count)
        if buy_list
        else pd.DataFrame()
    )
    df_sell = (
        pd.DataFrame(sell_list)
        .sort_values(by="RawVolume", ascending=False)
        .head(top_n_count)
        if sell_list
        else pd.DataFrame()
    )
    return df_buy, df_sell


# --- STRATEGY FUNCTIONS FOR THE DROPDOWN ---
@st.cache_data(ttl=300)
def fetch_weekly_mtf_strategy(symbols, top_n_count):
    results = []
    for sym in symbols:
        clean_sym = sym.upper().strip()
        ticker_sym = f"{clean_sym}.NS"
        try:
            ticker = yf.Ticker(ticker_sym)
            df_weekly = ticker.history(period="2y", interval="1wk")
            df_monthly = ticker.history(period="5y", interval="1mo")
            if len(df_weekly) < 30 or len(df_monthly) < 12:
                continue
            cmp = round(float(df_weekly.iloc[-1]["Close"]), 2)
            if cmp < 50.0:
                continue
            weekly_vol_sum = df_weekly["Volume"].tail(12).sum()
            weekly_vwap = round(float((df_weekly["Close"].tail(12) * df_weekly["Volume"].tail(12)).sum() / weekly_vol_sum), 2) if weekly_vol_sum > 0 else cmp
            vol_poc = compute_volume_profile_poc(df_weekly.tail(26))
            w_demand = round(df_weekly["Low"].tail(12).min(), 2)
            w_supply = round(df_weekly["High"].tail(12).max(), 2)
            m_demand = round(df_monthly["Low"].tail(6).min(), 2)
            m_supply = round(df_monthly["High"].tail(6).max(), 2)
            best_demand_zone = max(w_demand, m_demand)
            best_supply_zone = min(w_supply, m_supply)
            rsi_series = compute_rsi(df_weekly["Close"], period=14)
            curr_rsi = round(float(rsi_series.iloc[-1]), 2)
            prev_rsi = round(float(rsi_series.iloc[-5]), 2)
            price_low_recent = df_weekly["Low"].iloc[-1]
            price_low_prev = df_weekly["Low"].iloc[-5]
            bullish_rsi_div = (price_low_recent <= price_low_prev) and (curr_rsi > prev_rsi) and (curr_rsi < 65)
            macd, signal, hist = compute_macd(df_weekly["Close"])
            curr_hist = float(hist.iloc[-1])
            prev_hist = float(hist.iloc[-2])
            macd_bullish_cross = (prev_hist <= 0 and curr_hist > 0) or (curr_hist > prev_hist and curr_hist > 0)
            upper_bb, mid_bb, lower_bb = compute_bollinger_bands(df_weekly["Close"])
            bb_confluence = cmp >= lower_bb.iloc[-1]
            supertrend_signal = compute_supertrend(df_weekly).iloc[-1] == 1
            is_near_demand = (cmp <= best_demand_zone * 1.08) or (cmp <= vol_poc * 1.03) or (cmp >= weekly_vwap * 0.98 and cmp <= weekly_vwap * 1.05)
            exceptional_volume = df_weekly["Volume"].iloc[-1] > (df_weekly["Volume"].tail(12).mean() * 1.2)
            chart_link = f"https://www.tradingview.com/chart/?symbol=NSE:{clean_sym}"

            if (bullish_rsi_div or macd_bullish_cross or supertrend_signal) and (is_near_demand or bb_confluence) and exceptional_volume:
                entry = cmp
                calculated_sl = round(float(df_weekly["Low"].iloc[-1]) * 0.99, 2)
                sl = max(calculated_sl, round(entry * 0.95, 2))
                if sl >= entry:
                    sl = round(entry * 0.96, 2)
                risk = entry - sl
                if risk <= 0:
                    continue
                t1 = round(entry + (risk * 1.5), 2)
                t2 = round(max(best_supply_zone, entry + (risk * 3.0)), 2)
            else:
                continue

            results.append({
                "Symbol": clean_sym,
                "Signal": "BUY",
                "Weekly Close (₹)": f"₹{cmp}",
                "Weekly VWAP (₹)": f"₹{weekly_vwap}",
                "Demand Zone (₹)": f"₹{best_demand_zone}",
                "Supply Zone (₹)": f"₹{best_supply_zone}",
                "Weekly RSI": curr_rsi,
                "Tight Entry (₹)": f"₹{entry}",
                "Small SL (₹)": f"₹{sl}",
                "Target 1 (₹)": f"₹{t1}",
                "Target 2 (₹)": f"₹{t2}",
                "RawVolume": df_weekly["Volume"].iloc[-1],
                "Chart": chart_link,
            })
        except Exception:
            continue
    df_results = pd.DataFrame(results)
    if not df_results.empty:
        df_results = df_results.sort_values(by="RawVolume", ascending=False).head(top_n_count)
    return df_results


@st.cache_data(ttl=300)
def fetch_daily_momentum_strategy(symbols, top_n_count):
    results = []
    for sym in symbols:
        clean_sym = sym.upper().strip()
        ticker_sym = f"{clean_sym}.NS"
        try:
            ticker = yf.Ticker(ticker_sym)
            df_daily = ticker.history(period="1y", interval="1d")
            if len(df_daily) < 50:
                continue
            cmp = round(float(df_daily.iloc[-1]["Close"]), 2)
            if cmp < 50.0:
                continue
            total_vol = df_daily["Volume"].tail(20).sum()
            daily_vwap = round(float((df_daily["Close"].tail(20) * df_daily["Volume"].tail(20)).sum() / total_vol), 2) if total_vol > 0 else cmp
            rsi_series = compute_rsi(df_daily["Close"], period=14)
            curr_rsi = round(float(rsi_series.iloc[-1]), 2)
            macd, signal, hist = compute_macd(df_daily["Close"])
            curr_hist = float(hist.iloc[-1])
            prev_hist = float(hist.iloc[-2])
            macd_bullish_cross = (prev_hist <= 0 and curr_hist > 0) or (curr_hist > prev_hist and curr_hist > 0)
            chart_link = f"https://www.tradingview.com/chart/?symbol=NSE:{clean_sym}"

            if macd_bullish_cross and cmp >= daily_vwap and curr_rsi > 55:
                entry = cmp
                sl = round(min(float(df_daily["Low"].tail(5).min()) * 0.99, entry * 0.96), 2)
                risk = entry - sl
                if risk <= 0:
                    continue
                t1 = round(entry + (risk * 1.5), 2)
                t2 = round(entry + (risk * 3.0), 2)

                results.append({
                    "Symbol": clean_sym,
                    "Signal": "BUY",
                    "Daily Close (₹)": f"₹{cmp}",
                    "Daily VWAP (₹)": f"₹{daily_vwap}",
                    "Daily RSI": curr_rsi,
                    "Tight Entry (₹)": f"₹{entry}",
                    "Small SL (₹)": f"₹{sl}",
                    "Target 1 (₹)": f"₹{t1}",
                    "Target 2 (₹)": f"₹{t2}",
                    "RawVolume": df_daily["Volume"].iloc[-1],
                    "Chart": chart_link,
                })
        except Exception:
            continue
    df_results = pd.DataFrame(results)
    if not df_results.empty:
        df_results = df_results.sort_values(by="RawVolume", ascending=False).head(top_n_count)
    return df_results


@st.cache_data(ttl=300)
def fetch_elite_swing_strategy(symbols, top_n_count):
    results = []
    for sym in symbols:
        clean_sym = sym.upper().strip()
        ticker_sym = f"{clean_sym}.NS"
        try:
            ticker = yf.Ticker(ticker_sym)
            df_daily = ticker.history(period="1y", interval="1d")
            if len(df_daily) < 60:
                continue
            cmp = round(float(df_daily.iloc[-1]["Close"]), 2)
            if cmp < 50.0:
                continue
            ema_50 = df_daily["Close"].ewm(span=50, adjust=False).mean()
            is_uptrend = cmp > ema_50.iloc[-1]
            distance_from_ema = (cmp - ema_50.iloc[-1]) / ema_50.iloc[-1]
            is_pullback = -0.03 <= distance_from_ema <= 0.04
            rsi_series = compute_rsi(df_daily["Close"], period=14)
            curr_rsi = round(float(rsi_series.iloc[-1]), 2)
            rsi_healthy = 40 <= curr_rsi <= 65
            macd, signal, hist = compute_macd(df_daily["Close"])
            curr_hist = float(hist.iloc[-1])
            prev_hist = float(hist.iloc[-2])
            macd_turning_up = curr_hist > prev_hist
            chart_link = f"https://www.tradingview.com/chart/?symbol=NSE:{clean_sym}"

            if is_uptrend and (is_pullback or rsi_healthy) and macd_turning_up:
                entry = cmp
                sl = round(min(float(df_daily["Low"].tail(10).min()) * 0.99, entry * 0.95), 2)
                risk = entry - sl
                if risk <= 0:
                    continue
                t1 = round(entry + (risk * 1.5), 2)
                t2 = round(entry + (risk * 3.0), 2)

                results.append({
                    "Symbol": clean_sym,
                    "Signal": "SWING BUY",
                    "Daily Close (₹)": f"₹{cmp}",
                    "50 EMA (₹)": f"₹{round(ema_50.iloc[-1], 2)}",
                    "RSI (14)": curr_rsi,
                    "Entry (₹)": f"₹{entry}",
                    "Stop Loss (₹)": f"₹{sl}",
                    "Target 1 (₹)": f"₹{t1}",
                    "Target 2 (₹)": f"₹{t2}",
                    "RawVolume": df_daily["Volume"].iloc[-1],
                    "Chart": chart_link,
                })
        except Exception:
            continue
    df_res = pd.DataFrame(results)
    if not df_res.empty:
        df_res = df_res.sort_values(by="RawVolume", ascending=False).head(top_n_count)
    return df_res


# --- BACKTEST ENGINE FOR INTRADAY ---
def run_live_backtest(target_date, scan_clause, top_n_count):
    raw_stocks = fetch_chartink_stocks(scan_clause)
    extracted_symbols = [
        item.get("nsecode", item.get("symbol", "")).strip()
        for item in raw_stocks
        if item.get("nsecode", item.get("symbol", ""))
    ]
    stock_list = list(dict.fromkeys(extracted_symbols + NIFTY_750_POOL[:20]))[
        : top_n_count * 2
    ]
    results = []

    for symbol in stock_list:
        try:
            ticker = yf.Ticker(f"{symbol.strip().upper()}.NS")
            start_dt = datetime.combine(target_date, datetime.min.time())
            end_dt = start_dt + timedelta(days=1)
            df_hist = ticker.history(interval="5m", start=start_dt, end=end_dt)
            if df_hist.empty:
                continue

            open_price = round(float(df_hist.iloc[0]["Open"]), 2)
            max_price = round(float(df_hist["High"].max()), 2)
            min_price = round(float(df_hist["Low"].min()), 2)
            close_price = round(float(df_hist.iloc[-1]["Close"]), 2)

            if open_price < 50.0:
                continue

            is_buy = close_price >= open_price
            entry_price = open_price
            chart_link = f"https://www.tradingview.com/chart/?symbol=NSE:{symbol}"

            if is_buy:
                sl, t1, t2 = (
                    round(entry_price * 0.996, 2),
                    round(entry_price * 1.012, 2),
                    round(entry_price * 1.025, 2),
                )
                if max_price >= t2:
                    status, pnl_val = ("🎯 Target 2 Hit", round(((t2 - entry_price) / entry_price) * 100, 2))
                elif max_price >= t1:
                    status, pnl_val = ("🎯 Target 1 Hit", round(((t1 - entry_price) / entry_price) * 100, 2))
                elif min_price <= sl:
                    status, pnl_val = ("🛑 SL Hit", round(((sl - entry_price) / entry_price) * 100, 2))
                else:
                    status, pnl_val = ("⏳ Closed at Market", round(((close_price - entry_price) / entry_price) * 100, 2))

                results.append({
                    "Symbol": symbol,
                    "Signal": "BUY",
                    "Session Open (₹)": f"₹{open_price}",
                    "Session High (₹)": f"₹{max_price}",
                    "Session Low (₹)": f"₹{min_price}",
                    "Session Close (₹)": f"₹{close_price}",
                    "Status": status,
                    "P&L (%)": f"{pnl_val:+.2f}%",
                    "RawPnL": pnl_val,
                    "Chart": chart_link,
                })
            else:
                sl, t1, t2 = (
                    round(entry_price * 1.004, 2),
                    round(entry_price * 0.988, 2),
                    round(entry_price * 0.975, 2),
                )
                if min_price <= t2:
                    status, pnl_val = ("🎯 Target 2 Hit", round(((entry_price - t2) / entry_price) * 100, 2))
                elif min_price <= t1:
                    status, pnl_val = ("🎯 Target 1 Hit", round(((entry_price - t1) / entry_price) * 100, 2))
                elif max_price >= sl:
                    status, pnl_val = ("🛑 SL Hit", round(((entry_price - sl) / entry_price) * 100, 2))
                else:
                    status, pnl_val = ("⏳ Closed at Market", round(((entry_price - close_price) / entry_price) * 100, 2))

                results.append({
                    "Symbol": symbol,
                    "Signal": "SELL",
                    "Session Open (₹)": f"₹{open_price}",
                    "Session High (₹)": f"₹{max_price}",
                    "Session Low (₹)": f"₹{min_price}",
                    "Session Close (₹)": f"₹{close_price}",
                    "Status": status,
                    "P&L (%)": f"{pnl_val:+.2f}%",
                    "RawPnL": pnl_val,
                    "Chart": chart_link,
                })

            if len(results) >= top_n_count:
                break
        except Exception:
            continue

    return pd.DataFrame(results)


# --- CONTROLS ---
st.subheader("⚙️ Master Engine Controls")
col_info, col_slider = st.columns([2, 1])

with col_info:
    market_status = (
        "🔴 CLOSED (Post-Market Mode Active)"
        if is_market_closed()
        else "🟢 OPEN (Live Scanning Active)"
    )
    st.info(f"Market Status: **{market_status}** | Universe: **Top Nifty 750 Stocks**")
with col_slider:
    selected_count = st.slider(
        "Select Stock Output Count:",
        min_value=3,
        max_value=25,
        value=10,
        step=1,
    )

st.markdown("---")

# --- TAB 1: INTRADAY ENGINE (UNTOUCHED) ---
with main_tab1:
    st.subheader("⚡ Intraday Engine (Tight SL + 5m RSI Div + Exceptional Volume)")
    post_market_toggle = st.checkbox(
        "Force Post-Market Next-Session Calculation Mode",
        value=is_market_closed(),
    )

    if st.button("🚀 Run Intraday Engine Scan", type="primary", use_container_width=True):
        with st.spinner("Scanning Nifty 750 stocks for intraday setups..."):
            raw_stocks = fetch_chartink_stocks(DEFAULT_SCAN_CLAUSE)
            df_b, df_s = process_ultimate_confluence(
                raw_stocks, selected_count, force_post_market=post_market_toggle
            )
            st.session_state["df_b_master"] = df_b
            st.session_state["df_s_master"] = df_s
            st.success("Intraday setups generated!")

    if "df_b_master" not in st.session_state:
        empty_b, empty_s = process_ultimate_confluence(
            [], selected_count, force_post_market=post_market_toggle
        )
        st.session_state["df_b_master"] = empty_b
        st.session_state["df_s_master"] = empty_s

    sub_tab_buy, sub_tab_sell = st.tabs([
        f"🟢 Top {selected_count} Long Setups",
        f"🔴 Top {selected_count} Short Setups",
    ])

    with sub_tab_buy:
        df_b = st.session_state["df_b_master"]
        if not df_b.empty:
            render_native_table(df_b, key_prefix="intra_buy")
        else:
            st.info("Click the button above to run the intraday scanner.")

    with sub_tab_sell:
        df_s = st.session_state["df_s_master"]
        if not df_s.empty:
            render_native_table(df_s, key_prefix="intra_sell")
        else:
            st.info("Click the button above to run the intraday scanner.")

# --- TAB 2: INTRADAY BACKTESTER (UNTOUCHED) ---
with main_tab2:
    st.subheader("📊 Intraday Backtester Engine & Summary")
    backtest_date = st.date_input(
        "📅 Select Backtest Session Date",
        value=datetime.today().date() - timedelta(days=1),
    )

    if st.button("🚀 Run Intraday Backtest", type="primary"):
        with st.spinner("Executing backtest over Nifty 750 intraday candles..."):
            df_bt = run_live_backtest(backtest_date, DEFAULT_SCAN_CLAUSE, selected_count)
            st.session_state["df_bt_results"] = df_bt

    if "df_bt_results" in st.session_state and not st.session_state["df_bt_results"].empty:
        df_bt = st.session_state["df_bt_results"]

        total_trades = len(df_bt)
        t1_hits = len(df_bt[df_bt["Status"].str.contains("Target 1", na=False)])
        t2_hits = len(df_bt[df_bt["Status"].str.contains("Target 2", na=False)])
        sl_hits = len(df_bt[df_bt["Status"].str.contains("SL Hit", na=False)])
        wins = t1_hits + t2_hits
        win_rate = round((wins / total_trades) * 100, 2) if total_trades > 0 else 0.0
        total_pnl = round(df_bt["RawPnL"].sum(), 2)

        st.markdown("#### 📈 Backtest Performance Summary")
        col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
        col_m1.metric("Total Trades", total_trades)
        col_m2.metric("Win Rate", f"{win_rate}%")
        col_m3.metric("Cumulative P&L", f"{total_pnl:+.2f}%")
        col_m4.metric("Targets Hit (T1 / T2)", f"🎯 {t1_hits} / 🎯 {t2_hits}")
        col_m5.metric("Stop Losses Hit", f"🛑 {sl_hits}")
        st.markdown("---")

        render_native_table(df_bt, key_prefix="backtest")
    else:
        st.info("Select a date and click the button above to run backtesting.")

# --- TAB 3: WEEKLY & SWING STRATEGY HUB (WITH DROPDOWN) ---
with main_tab3:
    st.subheader("🗓️ Weekly & Swing Strategy Hub")
    st.markdown("Select your desired strategy from the dropdown below and execute a scan across the Nifty 750 universe.")

    selected_strategy = st.selectbox(
        "Choose Weekly / Swing Strategy:",
        [
            "Weekly Higher-Timeframe MTF Strategy (Supply/Demand + Confluence)",
            "Daily Momentum Strategy (MACD Crossover + VWAP + RSI > 55)",
            "Elite Swing Strategy (MTF Trend Pullback & Dip Buy)"
        ]
    )

    if st.button("🚀 Run Selected Strategy Scan", type="primary", use_container_width=True):
        with st.spinner(f"Executing scan for: {selected_strategy}..."):
            if "Weekly Higher-Timeframe" in selected_strategy:
                df_res = fetch_weekly_mtf_strategy(NIFTY_750_POOL, selected_count)
            elif "Daily Momentum" in selected_strategy:
                df_res = fetch_daily_momentum_strategy(NIFTY_750_POOL, selected_count)
            else:
                df_res = fetch_elite_swing_strategy(NIFTY_750_POOL, selected_count)

            st.session_state["df_dropdown_strategy"] = df_res
            st.success("Scan completed successfully!")

    if "df_dropdown_strategy" in st.session_state and not st.session_state["df_dropdown_strategy"].empty:
        render_native_table(st.session_state["df_dropdown_strategy"], key_prefix="dropdown_strategy_tab")
    else:
        st.info("Select a strategy above and click the button to view results.")
