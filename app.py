import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import yfinance as yf
import numpy as np
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
st.markdown("Precision Trading Terminal featuring **Backtest Performance Summaries** and **Green/Red Risk Flags**.")

main_tab1, main_tab2, main_tab3 = st.tabs([
    "⚡ Intraday Engine (Tight Live & Post-Market)", 
    "📊 Precision Intraday Backtester Engine",
    "🗓️ Weekly MTF Tight-Risk Strategy Engine"
])

# --- UNIVERSE DEFINITION ---
LARGE_CAPS = {
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "BHARTIARTL", "ITC", "LT", "HINDUNILVR",
    "AXISBANK", "KOTAKBANK", "SUNPHARMA", "TITAN", "BAJFINANCE", "MARUTI", "NTPC", "POWERGRID", "ASIANPAINT",
    "ULTRACEMCO", "TATAMOTORS", "COALINDIA", "TATASTEEL", "ADANIENT", "ADANIPORTS", "JSWSTEEL", "HCLTECH",
    "ONGC", "M&M", "GRASIM", "BAJAJ-AUTO", "NESTLEIND", "SIEMENS", "BEL", "HAL", "IOC", "DLF", "VBL",
    "LODHA", "ZYDUSLIFE", "INDUSINDBK", "BAJAJHFL", "TORNTPHARM", "APOLLOHOSP", "HYUNDAI", "BAJAJFINSV",
    "DRREDDY", "SHREECEM", "BAJAJHLDNG", "UNITDSPR", "ABB", "EICHERMOT", "DIVISLAB", "LICI", "INDHOTEL",
    "ICICIGI", "CGPOWER", "TRENT", "MOTHERSON", "ADANIPOWER", "JINDALSTEL", "PFC", "TECHM", "LTIM", "WIPRO"
}

MID_CAPS = {
    "PERSISTENT", "POLYCAB", "DIXON", "COFORGE", "MPHASIS", "ASTRAL", "SUPREMEIND", "PAGEIND",
    "MUTHOOTFIN", "CHOLAFIN", "ASHOKLEY", "OBEROIRLTY", "BALKRISIND", "CUMMINSIND", "TIINDIA",
    "MAXHEALTH", "LUPIN", "AUROPHARMA", "BOSCHLTD", "BHARATFORG", "PIIND", "SRF", "IDEA", "YESBANK",
    "IDFCFIRSTB", "TATAINVEST", "KPRMILL", "NAUKRI", "LENSKART", "KALYANKJIL", "OFSS", "ANTHEM",
    "RADICO", "GLAXO", "LGEINDIA", "FEDERALBNK", "AJANTPHARM", "TATACOMM", "EXIDEIND", "OIL",
    "PETRONET", "LLOYDSME", "PREMIERENE", "LICHSGFIN", "ESCORTS", "GODREJPROP", "ABBOTINDIA", "BHEL"
}

LARGE_AND_MID_POOL = list(LARGE_CAPS.union(MID_CAPS))
DEFAULT_SCAN_CLAUSE = "( {cash} ( [0] 15 minute close > [0] 15 minute vwap and [0] 15 minute volume > 150000 and [0] 15 minute close > 50 ) )"

def classify_market_cap(symbol):
    sym = symbol.upper().strip()
    if sym in LARGE_CAPS:
        return "Large Cap"
    elif sym in MID_CAPS:
        return "Mid Cap"
    else:
        return "Small Cap"

def is_market_closed():
    now = datetime.now()
    if now.weekday() >= 5:
        return True
    market_open = time(9, 15)
    market_close = time(15, 30)
    return not (market_open <= now.time() <= market_close)

# --- TECHNICAL INDICATOR HELPERS ---
def compute_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def compute_macd(series, fast=12, slow=26, signal=9):
    exp1 = series.ewm(span=fast, adjust=False).mean()
    exp2 = series.ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    hist = macd - signal_line
    return macd, signal_line, hist

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
            if df_intraday.empty:
                continue
                
            day_open = round(float(df_intraday.iloc[0]['Open']), 2)
            day_high = round(float(df_intraday['High'].max()), 2)
            day_low = round(float(df_intraday['Low'].min()), 2)
            cmp = round(float(df_intraday.iloc[-1]['Close']), 2)
            prev_close = round(float(ticker.fast_info.previous_close), 2) if ticker.fast_info.previous_close else cmp
            pct_change = round(((cmp - prev_close) / prev_close) * 100, 2) if prev_close else 0.0
            volume = int(df_intraday['Volume'].sum())

            total_vol = df_intraday['Volume'].sum()
            vwap = round(float((df_intraday['Close'] * df_intraday['Volume']).sum() / total_vol), 2) if total_vol > 0 else cmp

            data_dict[clean_sym] = {
                "cmp": cmp, "day_open": day_open, "prev_close": prev_close,
                "chg": pct_change, "vol": volume, "day_high": day_high,
                "day_low": day_low, "vwap": vwap
            }
        except Exception:
            continue
    return data_dict

def fetch_chartink_stocks(scan_condition):
    url = "https://chartink.com/screener/process"
    screener_main_url = "https://chartink.com/screener/"
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'})

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

# --- INTRADAY ENGINE (WITH RED/GREEN FLAGS) ---
def process_ultimate_confluence(stock_data, top_n_count, force_post_market=False):
    buy_list, sell_list = [], []
    extracted_symbols = [item.get('nsecode', item.get('symbol', '')).strip() for item in stock_data if item.get('nsecode', item.get('symbol', ''))]
    active_symbols = list(dict.fromkeys(extracted_symbols + LARGE_AND_MID_POOL[:30]))

    live_prices = fetch_live_market_data(active_symbols)
    closed = force_post_market or is_market_closed()

    for symbol in active_symbols:
        live_info = live_prices.get(symbol)
        if not live_info:
            continue
            
        cmp, day_open, pct_change, volume = live_info['cmp'], live_info['day_open'], live_info['chg'], live_info['vol']
        day_high, day_low, vwap = live_info['day_high'], live_info['day_low'], live_info['vwap']

        if cmp < 50.0:
            continue
        diff = day_high - day_low

        if not closed:
            # LIVE MARKET STRATEGY (Tight SL)
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
            execution_mode = "LIVE MARKET (TIGHT SL)"
        else:
            # POST-MARKET / NEXT-SESSION PLAN
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
            execution_mode = "NEXT-SESSION (TIGHT ENTRY)"

        # --- RISK ANALYSIS: GREEN/RED FLAGS ---
        red_reasons = []
        green_reasons = []

        if abs(pct_change) > 4.5:
            red_reasons.append("Extended Move (>4.5%)")
        if volume < 200000:
            red_reasons.append("Low Volume Liquidity")
        if pct_change >= 0 and cmp < vwap:
            red_reasons.append("Below VWAP in Bullish Setup")
        if pct_change < 0 and cmp > vwap:
            red_reasons.append("Above VWAP in Bearish Setup")

        if 1.0 <= abs(pct_change) <= 3.5:
            green_reasons.append("Healthy Momentum (1-3.5%)")
        if volume >= 500000:
            green_reasons.append("High Liquidity")
        if pct_change >= 0 and cmp >= vwap:
            green_reasons.append("Sustained Above VWAP")
        if pct_change < 0 and cmp <= vwap:
            green_reasons.append("Sustained Below VWAP")

        if len(red_reasons) > len(green_reasons):
            risk_flag = f"🔴 RED: {', '.join(red_reasons)}"
        elif green_reasons:
            risk_flag = f"🟢 GREEN: {', '.join(green_reasons)}"
        else:
            risk_flag = "🟡 NEUTRAL"

        stock_entry = {
            'Symbol': symbol, 'Category': classify_market_cap(symbol), 'Risk Analysis': risk_flag,
            'Session Open (₹)': day_open, 'Session High (₹)': day_high, 'Session Low (₹)': day_low, 
            'Last Close/CMP (₹)': cmp, 'VWAP (₹)': vwap, 'Tight Entry (₹)': entry_price, 
            'Small SL (₹)': sl, 'Target 1 (₹)': t1, 'Target 2 (₹)': t2, 'Mode': execution_mode,
            'Change (%)': f"{pct_change:+.2f}%", 'RawVolume': volume,
            'Live Chart': f"https://in.tradingview.com/chart/?symbol=NSE:{symbol}"
        }

        if pct_change >= 0:
            buy_list.append(stock_entry)
        else:
            sell_list.append(stock_entry)

    df_buy = pd.DataFrame(buy_list).sort_values(by='RawVolume', ascending=False).head(top_n_count) if buy_list else pd.DataFrame()
    df_sell = pd.DataFrame(sell_list).sort_values(by='RawVolume', ascending=False).head(top_n_count) if sell_list else pd.DataFrame()
    return df_buy, df_sell

# --- WEEKLY MTF STRATEGY ENGINE (WITH RED/GREEN FLAGS) ---
@st.cache_data(ttl=300)
def fetch_weekly_mtf_strategy(symbols):
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

            cmp = round(float(df_weekly.iloc[-1]['Close']), 2)
            if cmp < 50.0:
                continue

            # 1. MTF Demand & Supply Zones
            w_demand = round(df_weekly['Low'].tail(8).min(), 2)
            w_supply = round(df_weekly['High'].tail(8).max(), 2)
            m_demand = round(df_monthly['Low'].tail(4).min(), 2)
            m_supply = round(df_monthly['High'].tail(4).max(), 2)

            best_demand_zone = max(w_demand, m_demand)
            best_supply_zone = min(w_supply, m_supply)

            # 2. RSI & Divergence
            rsi_series = compute_rsi(df_weekly['Close'], period=14)
            curr_rsi = round(float(rsi_series.iloc[-1]), 2)
            prev_rsi = round(float(rsi_series.iloc[-5]), 2)
            
            price_low_recent = df_weekly['Low'].iloc[-1]
            price_low_prev = df_weekly['Low'].iloc[-5]
            price_high_recent = df_weekly['High'].iloc[-1]
            price_high_prev = df_weekly['High'].iloc[-5]

            bullish_rsi_div = (price_low_recent <= price_low_prev) and (curr_rsi > prev_rsi) and (curr_rsi < 60)
            bearish_rsi_div = (price_high_recent >= price_high_prev) and (curr_rsi < prev_rsi) and (curr_rsi > 40)

            # 3. MACD Crossover Engine
            macd, signal, hist = compute_macd(df_weekly['Close'])
            curr_hist = float(hist.iloc[-1])
            prev_hist = float(hist.iloc[-2])
            macd_bullish_cross = (prev_hist <= 0 and curr_hist > 0) or (curr_hist > prev_hist and curr_hist > 0)
            macd_bearish_cross = (prev_hist >= 0 and curr_hist < 0) or (curr_hist < prev_hist and curr_hist < 0)

            # Setup Logic
            if bullish_rsi_div or (macd_bullish_cross and cmp <= best_demand_zone * 1.03):
                setup_type = "🟢 Bullish Demand Zone Bounce"
                entry = cmp
                sl = round(best_demand_zone * 0.985, 2)
                t1 = round(cmp + ((best_supply_zone - cmp) * 0.4), 2)
                t2 = round(best_supply_zone, 2)
            elif bearish_rsi_div or (macd_bearish_cross and cmp >= best_supply_zone * 0.97):
                setup_type = "🔴 Bearish Supply Zone Rejection"
                entry = cmp
                sl = round(best_supply_zone * 1.015, 2)
                t1 = round(cmp - ((cmp - best_demand_zone) * 0.4), 2)
                t2 = round(best_demand_zone, 2)
            else:
                setup_type = "🟡 Neutral / No Tight Entry"
                entry, sl, t1, t2 = cmp, round(cmp * 0.985, 2), round(cmp * 1.05, 2), round(cmp * 1.10, 2)

            # --- WEEKLY RISK ANALYSIS (RED/GREEN FLAGS) ---
            w_reds, w_greens = [], []

            if curr_rsi > 75:
                w_reds.append("Extreme Overbought RSI (>75)")
            if curr_rsi < 25:
                w_reds.append("Extreme Oversold RSI (<25)")
            if cmp >= best_supply_zone * 0.98 and setup_type.startswith("🟢"):
                w_reds.append("Bullish Entry Near Supply Overhead")

            if bullish_rsi_div and macd_bullish_cross:
                w_greens.append("Dual Confluence (Bull Divergence + MACD Cross)")
            if bearish_rsi_div and macd_bearish_cross:
                w_greens.append("Dual Confluence (Bear Divergence + MACD Cross)")
            if cmp <= best_demand_zone * 1.02 and setup_type.startswith("🟢"):
                w_greens.append("At Strong Demand Zone Support")

            if w_reds:
                weekly_flag = f"🔴 RED: {', '.join(w_reds)}"
            elif w_greens:
                weekly_flag = f"🟢 GREEN: {', '.join(w_greens)}"
            else:
                weekly_flag = "🟡 NEUTRAL"

            results.append({
                'Symbol': clean_sym,
                'Category': classify_market_cap(clean_sym),
                'Risk Analysis': weekly_flag,
                'Weekly Close (₹)': cmp,
                'MTF Demand Zone (₹)': best_demand_zone,
                'MTF Supply Zone (₹)': best_supply_zone,
                'Weekly RSI (14)': curr_rsi,
                'RSI Divergence': "Bullish Divergence" if bullish_rsi_div else ("Bearish Divergence" if bearish_rsi_div else "None"),
                'MACD Crossover': "Bullish Cross" if macd_bullish_cross else ("Bearish Cross" if macd_bearish_cross else "Neutral"),
                'Strategy Setup': setup_type,
                'Tight Entry (₹)': entry,
                'Small SL (₹)': sl,
                'Target 1 (₹)': t1,
                'Target 2 (₹)': t2,
                'Chart': f"https://in.tradingview.com/chart/?symbol=NSE:{clean_sym}"
            })
        except Exception:
            continue

    return pd.DataFrame(results)

# --- INTRADAY TIGHT BACKTESTER (WITH PERFORMANCE SUMMARY) ---
def run_live_backtest(target_date, scan_clause, top_n_count):
    raw_stocks = fetch_chartink_stocks(scan_clause)
    extracted_symbols = [item.get('nsecode', item.get('symbol', '')).strip() for item in raw_stocks if item.get('nsecode', item.get('symbol', ''))]
    stock_list = list(dict.fromkeys(extracted_symbols + LARGE_AND_MID_POOL[:20]))[:top_n_count*2]
    results = []
    
    for symbol in stock_list:
        try:
            ticker = yf.Ticker(f"{symbol.strip().upper()}.NS")
            start_dt = datetime.combine(target_date, datetime.min.time())
            end_dt = start_dt + timedelta(days=1)
            df_hist = ticker.history(interval="5m", start=start_dt, end=end_dt)
            if df_hist.empty:
                continue
                
            open_price = round(float(df_hist.iloc[0]['Open']), 2)
            max_price = round(float(df_hist['High'].max()), 2)
            min_price = round(float(df_hist['Low'].min()), 2)
            close_price = round(float(df_hist.iloc[-1]['Close']), 2)

            if open_price < 50.0:
                continue

            is_buy = close_price >= open_price
            signal = "BUY" if is_buy else "SELL"
            entry_price = open_price
            
            if is_buy:
                sl, t1, t2 = round(entry_price * 0.996, 2), round(entry_price * 1.012, 2), round(entry_price * 1.025, 2)
                if max_price >= t2:
                    status, pnl_val = "🎯 Target 2 Hit", round(((t2 - entry_price) / entry_price) * 100, 2)
                elif max_price >= t1:
                    status, pnl_val = "🎯 Target 1 Hit", round(((t1 - entry_price) / entry_price) * 100, 2)
                elif min_price <= sl:
                    status, pnl_val = "🛑 SL Hit", round(((sl - entry_price) / entry_price) * 100, 2)
                else:
                    status, pnl_val = "⏳ Closed at Market", round(((close_price - entry_price) / entry_price) * 100, 2)
            else:
                sl, t1, t2 = round(entry_price * 1.004, 2), round(entry_price * 0.988, 2), round(entry_price * 0.975, 2)
                if min_price <= t2:
                    status, pnl_val = "🎯 Target 2 Hit", round(((entry_price - t2) / entry_price) * 100, 2)
                elif min_price <= t1:
                    status, pnl_val = "🎯 Target 1 Hit", round(((entry_price - t1) / entry_price) * 100, 2)
                elif max_price >= sl:
                    status, pnl_val = "🛑 SL Hit", round(((entry_price - sl) / entry_price) * 100, 2)
                else:
                    status, pnl_val = "⏳ Closed at Market", round(((entry_price - close_price) / entry_price) * 100, 2)

            results.append({
                "Symbol": symbol, "Category": classify_market_cap(symbol), "Signal": signal,
                "Session Open (₹)": open_price, "Session High (₹)": max_price, "Session Low (₹)": min_price,
                "Session Close (₹)": close_price, "Tight Entry (₹)": entry_price, "Small SL (₹)": sl,
                "Target 1 (₹)": t1, "Target 2 (₹)": t2, "Status": status, 
                "P&L (%)": f"{pnl_val:+.2f}%", "RawPnL": pnl_val,
                "Chart": f"https://in.tradingview.com/chart/?symbol=NSE:{symbol}"
            })
            
            if len(results) >= top_n_count:
                break
        except Exception:
            continue

    return pd.DataFrame(results)

# --- MASTER CONTROLS ---
st.subheader("⚙️ Master Engine Controls")
col_info, col_slider = st.columns([2, 1])

with col_info:
    market_status = "🔴 CLOSED (Post-Market Mode Active)" if is_market_closed() else "🟢 OPEN (Live Scanning Active)"
    st.info(f"Market Status: **{market_status}** | Universe: Large & Mid Caps")
with col_slider:
    selected_count = st.slider("Select Stock Output Count:", min_value=3, max_value=20, value=10, step=1)

st.markdown("---")

# --- TAB 1: INTRADAY ENGINE ---
with main_tab1:
    st.subheader("⚡ Intraday Engine (Tight Entry, Ultra-Small SL & Risk Flags)")
    post_market_toggle = st.checkbox("Force Post-Market Next-Session Calculation Mode", value=is_market_closed())
    
    if st.button("🚀 Run Intraday Engine Scan", type="primary", use_container_width=True):
        with st.spinner("Calculating precision entries, micro stop losses, and risk flags..."):
            raw_stocks = fetch_chartink_stocks(DEFAULT_SCAN_CLAUSE)
            df_b, df_s = process_ultimate_confluence(raw_stocks, selected_count, force_post_market=post_market_toggle)
            st.session_state['df_b_master'] = df_b
            st.session_state['df_s_master'] = df_s
            st.success("Tightened intraday setups generated!")

    if 'df_b_master' not in st.session_state:
        empty_b, empty_s = process_ultimate_confluence([], selected_count, force_post_market=post_market_toggle)
        st.session_state['df_b_master'] = empty_b
        st.session_state['df_s_master'] = empty_s

    sub_tab_buy, sub_tab_sell = st.tabs([f"🟢 Top {selected_count} Long Setups", f"🔴 Top {selected_count} Short Setups"])

    with sub_tab_buy:
        df_b = st.session_state['df_b_master']
        if not df_b.empty:
            st.dataframe(
                df_b.drop(columns=['RawVolume'], errors='ignore'),
                use_container_width=True,
                column_config={"Live Chart": st.column_config.LinkColumn("TradingView", display_text="📈 Open Chart")}
            )
        else:
            st.info("Click the button above to run the intraday scanner.")

    with sub_tab_sell:
        df_s = st.session_state['df_s_master']
        if not df_s.empty:
            st.dataframe(
                df_s.drop(columns=['RawVolume'], errors='ignore'),
                use_container_width=True,
                column_config={"Live Chart": st.column_config.LinkColumn("TradingView", display_text="📈 Open Chart")}
            )
        else:
            st.info("Click the button above to run the intraday scanner.")

# --- TAB 2: INTRADAY BACKTESTER WITH SUMMARY METRICS ---
with main_tab2:
    st.subheader("📊 Intraday Backtester Engine & Performance Summary")
    backtest_date = st.date_input("📅 Select Backtest Session Date", value=datetime.today().date() - timedelta(days=1))

    if st.button("🚀 Run Intraday Backtest", type="primary"):
        with st.spinner("Processing intraday historical candles and compiling summary metrics..."):
            df_bt = run_live_backtest(backtest_date, DEFAULT_SCAN_CLAUSE, selected_count)
            st.session_state['df_bt_results'] = df_bt

    if 'df_bt_results' in st.session_state and not st.session_state['df_bt_results'].empty:
        df_bt = st.session_state['df_bt_results']
        
        # --- BACKTEST SUMMARY CALCULATIONS ---
        total_trades = len(df_bt)
        t1_hits = len(df_bt[df_bt['Status'].str.contains("Target 1", na=False)])
        t2_hits = len(df_bt[df_bt['Status'].str.contains("Target 2", na=False)])
        sl_hits = len(df_bt[df_bt['Status'].str.contains("SL Hit", na=False)])
        wins = t1_hits + t2_hits
        win_rate = round((wins / total_trades) * 100, 2) if total_trades > 0 else 0.0
        total_pnl = round(df_bt['RawPnL'].sum(), 2)

        # --- SUMMARY DISPLAY CARDS ---
        st.markdown("#### 📈 Backtest Session Performance Summary")
        col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
        col_m1.metric("Total Executed Trades", total_trades)
        col_m2.metric("Overall Win Rate", f"{win_rate}%")
        col_m3.metric("Total Cumulative P&L", f"{total_pnl:+.2f}%")
        col_m4.metric("Target Hits (T1 / T2)", f"🎯 {t1_hits} / 🎯 {t2_hits}")
        col_m5.metric("Stop Loss Hits", f"🛑 {sl_hits}")
        st.markdown("---")

        st.dataframe(
            df_bt.drop(columns=['RawPnL'], errors='ignore'),
            use_container_width=True,
            column_config={"Chart": st.column_config.LinkColumn("TradingView", display_text="📈 Chart")}
        )
    else:
        st.info("Select a date and click the button above to execute backtesting.")

# --- TAB 3: WEEKLY MTF STRATEGY ENGINE WITH RISK FLAGS ---
with main_tab3:
    st.subheader("🗓️ Weekly MTF Demand/Supply & RSI/MACD Engine (With Risk Flags)")
    st.markdown("Precision strategy with **1.5% Stop Losses**, featuring **Red/Green Flag Risk Ratings** for trade filtering.")

    if st.button("🚀 Run Weekly MTF Strategy Scan", type="primary", use_container_width=True):
        with st.spinner("Filtering weekly setups for tight-risk entry structures and evaluating risk flags..."):
            df_mtf = fetch_weekly_mtf_strategy(LARGE_AND_MID_POOL)
            st.session_state['df_mtf_strategy'] = df_mtf
            st.success("Weekly MTF tight-risk scanning complete!")

    if 'df_mtf_strategy' in st.session_state and not st.session_state['df_mtf_strategy'].empty:
        st.dataframe(
            st.session_state['df_mtf_strategy'].head(selected_count),
            use_container_width=True,
            column_config={
                "Weekly Close (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                "MTF Demand Zone (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                "MTF Supply Zone (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                "Tight Entry (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                "Small SL (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                "Target 1 (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                "Target 2 (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                "Chart": st.column_config.LinkColumn("TradingView", display_text="📈 View MTF Chart")
            }
        )
    else:
        st.info("Click the button above to run the Weekly MTF Strategy scanner.")
