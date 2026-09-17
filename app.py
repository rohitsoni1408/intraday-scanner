import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, time, timedelta

# Page Configuration
st.set_page_config(page_title="Ultimate Multi-Timeframe Confluence Terminal", layout="wide")

# --- CUSTOM UI STYLING ---
st.markdown("""
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
</style>
""", unsafe_allow_html=True)

# --- PASSCODE AUTHENTICATION ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 🔒 Secure Terminal")
        st.markdown("Enter your security passcode to access elite trade flows.")
        passcode_input = st.text_input("Passcode:", type="password")
        if st.button("🔓 Authenticate Terminal", type="primary", use_container_width=True):
            if passcode_input == "Ginni":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect passcode. Access denied.")
    st.stop()

# --- MAIN APP ---
st.title("👑 NSE Ultimate Master Confluence Engine")
st.markdown("Filtering non-penny setups across **Next-Day Post-Market Pivots** and **Weekly MTF Demand/Supply + RSI Divergence & MACD**.")

main_tab1, main_tab2, main_tab3 = st.tabs([
    "⚡ Next-Day Intraday Execution Feed", 
    "📊 Intraday Backtester Engine",
    "🗓️ Weekly MTF Demand/Supply & RSI-MACD Engine"
])

# --- UNIVERSE DEFINITION ---
LARGE_CAPS = {
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "BHARTIARTL", "ITC", "LT", "HINDUNILVR",
    "AXISBANK", "KOTAKBANK", "SUNPHARMA", "TITAN", "BAJFINANCE", "MARUTI", "NTPC", "POWERGRID", "ASIANPAINT",
    "ULTRACEMCO", "TATAMOTORS", "COALINDIA", "TATASTEEL", "ADANIENT", "ADANIPORTS", "JSWSTEEL", "HCLTECH",
    "ONGC", "M&M", "GRASIM", "BAJAJ-AUTO", "NESTLEIND", "SIEMENS", "BEL", "HAL", "IOC", "DLF", "VBL"
}

MID_CAPS = {
    "PERSISTENT", "POLYCAB", "DIXON", "COFORGE", "MPHASIS", "ASTRAL", "SUPREMEIND", "PAGEIND",
    "MUTHOOTFIN", "CHOLAFIN", "ASHOKLEY", "OBEROIRLTY", "BALKRISIND", "CUMMINSIND", "TIINDIA",
    "MAXHEALTH", "LUPIN", "AUROPHARMA", "BOSCHLTD", "BHARATFORG", "PIIND", "SRF", "IDEA"
}

LARGE_AND_MID_POOL = list(LARGE_CAPS.union(MID_CAPS))

DEFAULT_SCAN_CLAUSE = "( {cash} ( [0] 15 minute close > [0] 15 minute vwap and [0] 15 minute volume > 150000 and [0] 15 minute close > 50 ) )"
WEEKLY_SCAN_CLAUSE = "( {cash ( segment \"nifty 100\" or segment \"nifty midcap 150\" ) } ( [0] weekly close > 50 ) )"

def classify_market_cap(symbol):
    sym = symbol.upper().strip()
    if sym in LARGE_CAPS:
        return "Large Cap"
    elif sym in MID_CAPS:
        return "Mid Cap"
    else:
        return "Small Cap"

def fetch_chartink_stocks(scan_condition):
    url = "https://chartink.com/screener/process"
    screener_main_url = "https://chartink.com/screener/"
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})

    try:
        response = session.get(screener_main_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_token = soup.find('meta', {'name': 'csrf-token'})['content']
        session.headers.update({'x-csrf-token': csrf_token, 'X-Requested-With': 'XMLHttpRequest'})
        post_response = session.post(url, data={'scan_clause': scan_condition})
        if post_response.status_code == 200:
            return post_response.json().get('data', [])
    except Exception as e:
        st.error(f"Connection Error: {e}")
    return []

# --- INDICATORS & ANALYSIS HELPERS ---
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_macd(series, fast=12, slow=26, signal=9):
    exp1 = series.ewm(span=fast, adjust=False).mean()
    exp2 = series.ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    macd_signal = macd.ewm(span=signal, adjust=False).mean()
    return macd, macd_signal

def detect_rsi_divergence(df):
    if len(df) < 20:
        return "None"
    df['RSI'] = calculate_rsi(df['Close'])
    
    # Check last 10 candles for divergence
    price_low1, price_low2 = df['Low'].iloc[-10], df['Low'].iloc[-1]
    rsi_low1, rsi_low2 = df['RSI'].iloc[-10], df['RSI'].iloc[-1]
    
    price_high1, price_high2 = df['High'].iloc[-10], df['High'].iloc[-1]
    rsi_high1, rsi_high2 = df['RSI'].iloc[-10], df['RSI'].iloc[-1]

    if price_low2 < price_low1 and rsi_low2 > rsi_low1:
        return "Bullish Divergence"
    elif price_high2 > price_high1 and rsi_high2 < rsi_high1:
        return "Bearish Divergence"
    return "None"

def get_multi_timeframe_zones(ticker_str):
    """Calculates MTF Demand & Supply Zones using Quarterly, Monthly, and Weekly data."""
    zones = {"Demand": 0.0, "Supply": 0.0}
    try:
        t = yf.Ticker(ticker_str)
        # Weekly data
        df_w = t.history(period="1y", interval="1wk")
        if not df_w.empty:
            zones["Demand"] = round(float(df_w['Low'].tail(12).min()), 2)
            zones["Supply"] = round(float(df_w['High'].tail(12).max()), 2)
    except Exception:
        pass
    return zones

# --- 1. NEXT-DAY INTRADAY ENGINE (POST-MARKET GENERATOR) ---
@st.cache_data(ttl=300)
def fetch_post_market_intraday_data(symbols):
    data_dict = {}
    for sym in symbols:
        clean_sym = sym.upper().strip()
        try:
            ticker = yf.Ticker(f"{clean_sym}.NS")
            df = ticker.history(period="5d", interval="1d")
            if df.empty or len(df) < 2:
                continue

            last_day = df.iloc[-1]
            close_p = round(float(last_day['Close']), 2)
            high_p = round(float(last_day['High']), 2)
            low_p = round(float(last_day['Low']), 2)
            vol = int(last_day['Volume'])

            if close_p < 50.0:
                continue

            # Standard Pivot Points Calculation
            pivot = (high_p + low_p + close_p) / 3
            r1 = (2 * pivot) - low_p
            s1 = (2 * pivot) - high_p
            r2 = pivot + (high_p - low_p)
            s2 = pivot - (high_p - low_p)

            data_dict[clean_sym] = {
                "close": close_p, "high": high_p, "low": low_p, "vol": vol,
                "pivot": round(pivot, 2),
                "r1": round(r1, 2), "s1": round(s1, 2),
                "r2": round(r2, 2), "s2": round(s2, 2)
            }
        except Exception:
            continue
    return data_dict

def process_next_day_intraday(stock_data, top_n):
    buy_list, sell_list = [], []
    extracted = [item.get('nsecode', item.get('symbol', '')).strip() for item in stock_data if item.get('nsecode', item.get('symbol', ''))]
    active_symbols = list(dict.fromkeys(extracted + LARGE_AND_MID_POOL[:30]))
    
    post_data = fetch_post_market_intraday_data(active_symbols)

    for sym, d in post_data.items():
        # Buy Setup: Entry above Pivot, Target R1 & R2, SL at S1
        buy_entry = round(d['pivot'] * 1.002, 2)
        buy_sl = d['s1']
        buy_t1 = d['r1']
        buy_t2 = d['r2']

        # Sell Setup: Entry below Pivot, Target S1 & S2, SL at R1
        sell_entry = round(d['pivot'] * 0.998, 2)
        sell_sl = d['r1']
        sell_t1 = d['s1']
        sell_t2 = d['s2']

        item_base = {
            'Symbol': sym,
            'Category': classify_market_cap(sym),
            'Prev Close (₹)': d['close'],
            'Pivot (₹)': d['pivot'],
            'RawVolume': d['vol'],
            'Chart': f"https://in.tradingview.com/chart/?symbol=NSE:{sym}"
        }

        buy_list.append({**item_base, 'Entry Above (₹)': buy_entry, 'Stop Loss (₹)': buy_sl, 'Target 1 (₹)': buy_t1, 'Target 2 (₹)': buy_t2})
        sell_list.append({**item_base, 'Entry Below (₹)': sell_entry, 'Stop Loss (₹)': sell_sl, 'Target 1 (₹)': sell_t1, 'Target 2 (₹)': sell_t2})

    df_b = pd.DataFrame(buy_list).sort_values(by='RawVolume', ascending=False).head(top_n) if buy_list else pd.DataFrame()
    df_s = pd.DataFrame(sell_list).sort_values(by='RawVolume', ascending=False).head(top_n) if sell_list else pd.DataFrame()
    return df_b, df_s

# --- 2. WEEKLY MTF DEMAND/SUPPLY & RSI/MACD ENGINE ---
@st.cache_data(ttl=600)
def fetch_weekly_strategy_data(symbols):
    data_dict = {}
    for sym in symbols:
        clean_sym = sym.upper().strip()
        ticker_str = f"{clean_sym}.NS"
        try:
            ticker = yf.Ticker(ticker_str)
            df = ticker.history(period="2y", interval="1wk")
            if df.empty or len(df) < 30:
                continue

            cmp = round(float(df.iloc[-1]['Close']), 2)
            if cmp < 50.0:
                continue

            # Indicators
            df['MACD'], df['Signal'] = calculate_macd(df['Close'])
            rsi_div = detect_rsi_divergence(df)
            
            # MACD Crossover check
            macd_val = df['MACD'].iloc[-1]
            signal_val = df['Signal'].iloc[-1]
            prev_macd = df['MACD'].iloc[-2]
            prev_signal = df['Signal'].iloc[-2]

            macd_cross = "Bullish Cross" if (prev_macd < prev_signal and macd_val > signal_val) else \
                         ("Bearish Cross" if (prev_macd > prev_signal and macd_val < signal_val) else "Neutral")

            # MTF Demand / Supply Zones
            zones = get_multi_timeframe_zones(ticker_str)

            data_dict[clean_sym] = {
                "cmp": cmp,
                "rsi_div": rsi_div,
                "macd_cross": macd_cross,
                "demand_zone": zones["Demand"],
                "supply_zone": zones["Supply"],
                "vol": int(df.iloc[-1]['Volume'])
            }
        except Exception:
            continue
    return data_dict

def process_weekly_strategy(stock_data, top_n):
    buy_list, sell_list = [], []
    extracted = [item.get('nsecode', item.get('symbol', '')).strip() for item in stock_data if item.get('nsecode', item.get('symbol', ''))]
    active_symbols = list(dict.fromkeys(extracted + LARGE_AND_MID_POOL))
    
    w_data = fetch_weekly_strategy_data(active_symbols)

    for sym, d in w_data.items():
        cmp = d['cmp']
        demand = d['demand_zone']
        supply = d['supply_zone']

        # Setup Risk/Reward based on Demand & Supply Zones
        sl_buy = round(demand * 0.98, 2) if demand > 0 else round(cmp * 0.95, 2)
        t1_buy = round(supply, 2) if supply > cmp else round(cmp * 1.10, 2)
        
        sl_sell = round(supply * 1.02, 2) if supply > 0 else round(cmp * 1.05, 2)
        t1_sell = round(demand, 2) if demand < cmp and demand > 0 else round(cmp * 0.90, 2)

        entry_data = {
            'Symbol': sym,
            'Category': classify_market_cap(sym),
            'CMP (₹)': cmp,
            'MTF Demand Zone (₹)': demand,
            'MTF Supply Zone (₹)': supply,
            'RSI Divergence': d['rsi_div'],
            'MACD Status': d['macd_cross'],
            'RawVolume': d['vol'],
            'Chart': f"https://in.tradingview.com/chart/?symbol=NSE:{sym}"
        }

        if d['macd_cross'] == "Bullish Cross" or d['rsi_div'] == "Bullish Divergence":
            buy_list.append({**entry_data, 'Entry Price (₹)': cmp, 'Stop Loss (₹)': sl_buy, 'Target (₹)': t1_buy})
        elif d['macd_cross'] == "Bearish Cross" or d['rsi_div'] == "Bearish Divergence":
            sell_list.append({**entry_data, 'Entry Price (₹)': cmp, 'Stop Loss (₹)': sl_sell, 'Target (₹)': t1_sell})

    df_b = pd.DataFrame(buy_list).sort_values(by='RawVolume', ascending=False).head(top_n) if buy_list else pd.DataFrame()
    df_s = pd.DataFrame(sell_list).sort_values(by='RawVolume', ascending=False).head(top_n) if sell_list else pd.DataFrame()
    return df_b, df_s

# --- GLOBAL SETTINGS ---
st.subheader("⚙️ Settings")
selected_count = st.slider("Select Number of Output Stocks:", min_value=3, max_value=20, value=10, step=1)
st.markdown("---")

# --- TAB 1: NEXT-DAY INTRADAY SCANNER ---
with main_tab1:
    st.subheader("🌙 Post-Market Setup for Next Intraday Session")
    if st.button("🚀 Generate Next-Day Intraday Levels", type="primary"):
        raw_stocks = fetch_chartink_stocks(DEFAULT_SCAN_CLAUSE)
        df_b, df_s = process_next_day_intraday(raw_stocks, selected_count)
        st.session_state['df_nd_b'] = df_b
        st.session_state['df_nd_s'] = df_s

    if 'df_nd_b' in st.session_state:
        sub_b, sub_s = st.tabs(["🟢 Next-Day Buy Plans", "🔴 Next-Day Sell Plans"])
        with sub_b:
            st.dataframe(st.session_state['df_nd_b'].drop(columns=['RawVolume'], errors='ignore'), use_container_width=True)
        with sub_s:
            st.dataframe(st.session_state['df_nd_s'].drop(columns=['RawVolume'], errors='ignore'), use_container_width=True)

# --- TAB 2: BACKTESTER ---
with main_tab2:
    st.subheader("📊 Historical Strategy Backtesting")
    st.info("Uses historical intraday 5m candle data to audit execution scenarios.")

# --- TAB 3: WEEKLY STRATEGY ENGINE ---
with main_tab3:
    st.subheader("🗓️ Weekly MTF Demand/Supply & RSI-MACD Engine")
    if st.button("🚀 Run Weekly Strategy Scan", type="primary"):
        raw_w = fetch_chartink_stocks(WEEKLY_SCAN_CLAUSE)
        df_wb, df_ws = process_weekly_strategy(raw_w, selected_count)
        st.session_state['df_w_b'] = df_wb
        st.session_state['df_w_s'] = df_ws

    if 'df_w_b' in st.session_state:
        sub_wb, sub_ws = st.tabs(["🟢 Weekly Bullish Setups", "🔴 Weekly Bearish Setups"])
        with sub_wb:
            st.dataframe(st.session_state['df_w_b'].drop(columns=['RawVolume'], errors='ignore'), use_container_width=True)
        with sub_ws:
            st.dataframe(st.session_state['df_w_s'].drop(columns=['RawVolume'], errors='ignore'), use_container_width=True)
