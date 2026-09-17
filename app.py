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

# --- MAIN APP (Unlocked) ---
st.title("👑 NSE Ultimate Master Confluence Engine")
st.markdown("Filtering high-probability setups across **Intraday Timeframes & Weekly Strong-Buy Confluence Matrix**.")

main_tab1, main_tab2, main_tab3 = st.tabs([
    "⚡ Intraday Engine (Live & Post-Market)", 
    "📊 Intraday Time-Based Backtester Engine",
    "👑 Weekly Strong-Buy Confluence Engine"
])

# --- EXPANDED LARGE & MID CAP UNIVERSE ---
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

# --- INDICATOR CALCULATIONS ---
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

# --- INTRADAY ENGINE ---
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
            if pct_change >= 0:
                fib_618 = round(day_high - (diff * 0.618), 2)
                entry_price = fib_618 if fib_618 > day_low else round(cmp * 0.995, 2)
                sl, t1, t2 = round(entry_price * 0.99, 2), round(day_high, 2), round(day_high + (diff * 0.5), 2)
            else:
                fib_618 = round(day_low + (diff * 0.618), 2)
                entry_price = fib_618 if fib_618 < day_high else round(cmp * 1.005, 2)
                sl, t1, t2 = round(entry_price * 1.01, 2), round(day_low, 2), round(day_low - (diff * 0.5), 2)
            execution_type = "LIVE EXECUTION"
        else:
            if pct_change >= 0:
                entry_price, sl = round(day_high - (diff * 0.382), 2), round(day_low, 2)
                t1, t2 = round(day_high + (diff * 0.382), 2), round(day_high + (diff * 0.618), 2)
            else:
                entry_price, sl = round(day_low + (diff * 0.382), 2), round(day_high, 2)
                t1, t2 = round(day_low - (diff * 0.382), 2), round(day_low - (diff * 0.618), 2)
            execution_type = "NEXT SESSION PLAN"

        stock_entry = {
            'Symbol': symbol, 'Category': classify_market_cap(symbol), 'Session Open (₹)': day_open,
            'Session High (₹)': day_high, 'Session Low (₹)': day_low, 'Last Close/CMP (₹)': cmp,
            'VWAP (₹)': vwap, 'Next Entry (₹)': entry_price, 'Stop Loss (₹)': sl,
            'Target 1 (₹)': t1, 'Target 2 (₹)': t2, 'Mode': execution_type,
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

# --- TIME-BASED INTRADAY BACKTESTER ---
def run_time_based_backtest(target_date, target_time_str, top_n_count):
    raw_stocks = fetch_chartink_stocks(DEFAULT_SCAN_CLAUSE)
    extracted_symbols = [item.get('nsecode', item.get('symbol', '')).strip() for item in raw_stocks if item.get('nsecode', item.get('symbol', ''))]
    stock_list = list(dict.fromkeys(extracted_symbols + LARGE_AND_MID_POOL[:25]))[:top_n_count * 2]
    results = []
    
    entry_time_obj = datetime.strptime(target_time_str, "%H:%M").time()

    for symbol in stock_list:
        try:
            ticker = yf.Ticker(f"{symbol.strip().upper()}.NS")
            start_dt = datetime.combine(target_date, datetime.min.time())
            end_dt = start_dt + timedelta(days=1)
            df_hist = ticker.history(interval="5m", start=start_dt, end=end_dt)

            if df_hist.empty:
                continue

            # Time filtering for intraday entry
            df_hist.index = pd.to_datetime(df_hist.index)
            candles_at_after = df_hist[df_hist.index.time >= entry_time_obj]
            if candles_at_after.empty:
                continue

            entry_row = candles_at_after.iloc[0]
            entry_time_actual = candles_at_after.index[0].strftime("%H:%M")
            entry_price = round(float(entry_row['Open']), 2)

            post_entry_candles = candles_at_after.iloc[1:]
            if post_entry_candles.empty:
                continue

            max_price = round(float(post_entry_candles['High'].max()), 2)
            min_price = round(float(post_entry_candles['Low'].min()), 2)
            close_price = round(float(post_entry_candles.iloc[-1]['Close']), 2)

            if entry_price < 50.0:
                continue

            # Simple Trend Bias Check based on entry vs day open
            day_open = float(df_hist.iloc[0]['Open'])
            is_buy = entry_price >= day_open
            signal = "BUY" if is_buy else "SELL"

            if is_buy:
                sl, t1, t2 = round(entry_price * 0.99, 2), round(entry_price * 1.015, 2), round(entry_price * 1.03, 2)
                if max_price >= t2:
                    status, pnl = "🎯 Target 2 Hit", round(((t2 - entry_price) / entry_price) * 100, 2)
                elif max_price >= t1:
                    status, pnl = "🎯 Target 1 Hit", round(((t1 - entry_price) / entry_price) * 100, 2)
                elif min_price <= sl:
                    status, pnl = "🛑 SL Hit", round(((sl - entry_price) / entry_price) * 100, 2)
                else:
                    status, pnl = "⏳ Closed at EOD", round(((close_price - entry_price) / entry_price) * 100, 2)
            else:
                sl, t1, t2 = round(entry_price * 1.01, 2), round(entry_price * 0.985, 2), round(entry_price * 0.97, 2)
                if min_price <= t2:
                    status, pnl = "🎯 Target 2 Hit", round(((entry_price - t2) / entry_price) * 100, 2)
                elif min_price <= t1:
                    status, pnl = "🎯 Target 1 Hit", round(((entry_price - t1) / entry_price) * 100, 2)
                elif max_price >= sl:
                    status, pnl = "🛑 SL Hit", round(((entry_price - sl) / entry_price) * 100, 2)
                else:
                    status, pnl = "⏳ Closed at EOD", round(((entry_price - close_price) / entry_price) * 100, 2)

            results.append({
                "Symbol": symbol, "Category": classify_market_cap(symbol), "Signal": signal,
                "Trigger Time": entry_time_actual, "Entry Price (₹)": entry_price,
                "EOD High (₹)": max_price, "EOD Low (₹)": min_price, "EOD Close (₹)": close_price,
                "Stop Loss (₹)": sl, "Target 1 (₹)": t1, "Target 2 (₹)": t2,
                "Status": status, "P&L (%)": f"{pnl:+.2f}%",
                "Chart": f"https://in.tradingview.com/chart/?symbol=NSE:{symbol}"
            })

            if len(results) >= top_n_count:
                break
        except Exception:
            continue

    return pd.DataFrame(results)

# --- WEEKLY STRONG-BUY CONFLUENCE ENGINE ---
@st.cache_data(ttl=300)
def fetch_weekly_strong_buys(symbols):
    """Calculates MTF Demand Zones, Breakouts, RSI Divergence, MACD Crossovers, and VWAP for STRONG BUY stocks only."""
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

            # 1. Best Demand Zone Calculation (Lowest low of swing bases)
            w_demand_zone = round(df_weekly['Low'].tail(16).min(), 2)
            m_demand_zone = round(df_monthly['Low'].tail(8).min(), 2)
            best_demand_zone = max(w_demand_zone, m_demand_zone)
            
            # Resistance/Breakout Zone (Recent peak)
            resistance_peak = round(df_weekly['High'].iloc[-12:-1].max(), 2)

            # 2. Weekly VWAP Calculation (20-Period Rolling VWAP baseline)
            total_vol = df_weekly['Volume'].tail(20).sum()
            weekly_vwap = round(float((df_weekly['Close'].tail(20) * df_weekly['Volume'].tail(20)).sum() / total_vol), 2) if total_vol > 0 else cmp

            # 3. RSI & RSI Divergence Calculation
            rsi_series = compute_rsi(df_weekly['Close'], period=14)
            current_rsi = round(float(rsi_series.iloc[-1]), 2)
            prev_rsi = round(float(rsi_series.iloc[-5]), 2)

            price_low_recent = df_weekly['Low'].iloc[-1]
            price_low_prev = df_weekly['Low'].iloc[-5]

            # Bullish RSI Divergence: Price lower/equal low, RSI higher low
            bullish_rsi_div = (price_low_recent <= price_low_prev) and (current_rsi > prev_rsi) and (current_rsi < 65)

            # 4. MACD Crossover Engine
            macd, signal, hist = compute_macd(df_weekly['Close'])
            curr_hist = float(hist.iloc[-1])
            prev_hist = float(hist.iloc[-2])
            macd_bullish_cross = (prev_hist <= 0 and curr_hist > 0) or (curr_hist > prev_hist and curr_hist > 0)

            # 5. Breakout Identification
            is_breakout = (cmp > resistance_peak) or (cmp >= resistance_peak * 0.98 and df_weekly['Volume'].iloc[-1] > df_weekly['Volume'].tail(5).mean())

            # --- STRICT STRONG BUY CONFLUENCE FILTER ---
            # Criteria: Above VWAP AND near/above Demand Zone + (Breakout OR Bullish RSI Divergence OR Bullish MACD Cross)
            near_demand = cmp >= best_demand_zone and cmp <= best_demand_zone * 1.18
            above_vwap = cmp > weekly_vwap

            strong_buy_reasons = []
            if is_breakout:
                strong_buy_reasons.append("💥 Resistance Breakout")
            if bullish_rsi_div:
                strong_buy_reasons.append("📈 Bullish RSI Divergence")
            if macd_bullish_cross:
                strong_buy_reasons.append("⚡ MACD Bullish Cross")
            if near_demand:
                strong_buy_reasons.append("🛡️ At Best Demand Zone")

            # Must meet at least 2 key bullish signals + VWAP confirmation for STRONG BUY classification
            if above_vwap and len(strong_buy_reasons) >= 2:
                sl = round(best_demand_zone * 0.96, 2)
                t1 = round(cmp * 1.12, 2)
                t2 = round(cmp * 1.25, 2)
                confluence_score = f"🔥 STRONG BUY ({len(strong_buy_reasons)} Factors)"

                results.append({
                    'Symbol': clean_sym,
                    'Category': classify_market_cap(clean_sym),
                    'Weekly Close (₹)': cmp,
                    'Best Demand Zone (₹)': best_demand_zone,
                    'Weekly VWAP (₹)': weekly_vwap,
                    'RSI (14)': current_rsi,
                    'RSI Divergence': "Bullish Divergence" if bullish_rsi_div else "None",
                    'MACD Status': "Bullish Cross" if macd_bullish_cross else "Neutral",
                    'Breakout Status': "Confirmed Breakout" if is_breakout else "Building Base",
                    'Confluence Details': " + ".join(strong_buy_reasons),
                    'Rating': confluence_score,
                    'Entry (₹)': cmp,
                    'Stop Loss (₹)': sl,
                    'Target 1 (₹)': t1,
                    'Target 2 (₹)': t2,
                    'Chart': f"https://in.tradingview.com/chart/?symbol=NSE:{clean_sym}"
                })
        except Exception:
            continue

    return pd.DataFrame(results)

# --- GLOBAL CONTROLS ---
st.subheader("⚙️ Master Engine Controls")
col_info, col_slider = st.columns([2, 1])

with col_info:
    market_status = "🔴 CLOSED (Post-Market Mode Active)" if is_market_closed() else "🟢 OPEN (Live Scanning Active)"
    st.info(f"Market Status: **{market_status}** | Universe: Large & Mid Caps")
with col_slider:
    selected_count = st.slider("Select Stock Output Count:", min_value=3, max_value=20, value=10, step=1)

st.markdown("---")

# --- TAB 1: INTRADAY SCANNER ---
with main_tab1:
    st.subheader("⚡ Intraday Master Engine")
    post_market_toggle = st.checkbox("Force Post-Market Next-Session Calculation Mode", value=is_market_closed())
    
    if st.button("🚀 Run Intraday Scan", type="primary", use_container_width=True):
        with st.spinner("Processing intraday metrics..."):
            raw_stocks = fetch_chartink_stocks(DEFAULT_SCAN_CLAUSE)
            df_b, df_s = process_ultimate_confluence(raw_stocks, selected_count, force_post_market=post_market_toggle)
            st.session_state['df_b_master'] = df_b
            st.session_state['df_s_master'] = df_s
            st.success("Intraday levels generated!")

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
                column_config={"Live Chart": st.column_config.LinkColumn("TradingView", display_text="📈 Chart")}
            )
        else:
            st.info("Click the button above to run intraday scan.")

    with sub_tab_sell:
        df_s = st.session_state['df_s_master']
        if not df_s.empty:
            st.dataframe(
                df_s.drop(columns=['RawVolume'], errors='ignore'),
                use_container_width=True,
                column_config={"Live Chart": st.column_config.LinkColumn("TradingView", display_text="📈 Chart")}
            )
        else:
            st.info("Click the button above to run intraday scan.")

# --- TAB 2: TIME-BASED INTRADAY BACKTESTER ---
with main_tab2:
    st.subheader("📊 Time-Based Intraday Backtester Engine")
    st.markdown("Evaluate trade execution outcomes based on specific **Intraday Entry Timestamps**.")
    
    col_date, col_time = st.columns(2)
    with col_date:
        backtest_date = st.date_input("📅 Select Backtest Session Date", value=datetime.today().date() - timedelta(days=1))
    with col_time:
        selected_time = st.selectbox("⏰ Select Intraday Entry Time Window:", ["09:30", "10:00", "10:30", "11:00", "12:00", "13:00"], index=1)

    if st.button("🚀 Run Time-Based Intraday Backtest", type="primary", use_container_width=True):
        with st.spinner(f"Fetching intraday 5m candle data for {backtest_date} at {selected_time}..."):
            df_bt = run_time_based_backtest(backtest_date, selected_time, selected_count)
            if not df_bt.empty:
                st.dataframe(
                    df_bt,
                    use_container_width=True,
                    column_config={
                        "Entry Price (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                        "Stop Loss (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                        "Target 1 (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                        "Target 2 (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                        "Chart": st.column_config.LinkColumn("TradingView", display_text="📈 Chart")
                    }
                )
            else:
                st.error("No intraday candle data available for selected date/time.")

# --- TAB 3: WEEKLY STRONG-BUY ENGINE ---
with main_tab3:
    st.subheader("👑 Weekly Strong-Buy Confluence Engine")
    st.markdown("Filters **ONLY Strong Buy Stocks** matching Demand Zones, Breakouts, Weekly VWAP, RSI Divergence & MACD Crossovers.")

    if st.button("🚀 Scan Weekly Strong-Buy Stocks", type="primary", use_container_width=True):
        with st.spinner("Executing multi-timeframe weekly confluence screening..."):
            df_strong_buys = fetch_weekly_strong_buys(LARGE_AND_MID_POOL)
            st.session_state['df_strong_buys'] = df_strong_buys
            st.success("Weekly Strong Buy screening completed!")

    if 'df_strong_buys' in st.session_state and not st.session_state['df_strong_buys'].empty:
        st.dataframe(
            st.session_state['df_strong_buys'].head(selected_count),
            use_container_width=True,
            column_config={
                "Weekly Close (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                "Best Demand Zone (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                "Weekly VWAP (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                "Entry (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                "Stop Loss (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                "Target 1 (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                "Target 2 (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                "Chart": st.column_config.LinkColumn("TradingView", display_text="📈 View MTF Chart")
            }
        )
    elif 'df_strong_buys' in st.session_state and st.session_state['df_strong_buys'].empty:
        st.warning("No stocks currently meet the strict 5-factor Strong Buy criteria.")
    else:
        st.info("Click the button above to run the Weekly Strong Buy Scanner.")
