import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime, time, timedelta

# Page Configuration
st.set_page_config(page_title="NSE 750 Multi-Timeframe Terminal", layout="wide")

# --- CUSTOM UI STYLING & COLOR CODING ---
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
    .buy-text { color: #00FF7F !important; font-weight: bold; }
    .sell-text { color: #FF4500 !important; font-weight: bold; }
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
st.title("👑 NSE 750 Ultimate Master Confluence Engine")
st.markdown("Complete Multi-Timeframe Suite featuring **NSE 750 Universe**, **Volume Profile POC**, **RSI Divergence**, and **Color-Coded Signals**.")

main_tab1, main_tab2, main_tab3 = st.tabs([
    "⚡ Intraday Engine (RSI Divergence & VWAP)", 
    "📊 Precision Intraday Backtester Engine",
    "🗓️ Weekly MTF Strategy (Volume Profile & MTF Zones)"
])

# --- TOP NSE 750 UNIVERSE ---
NSE_750_CORE = [
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "BHARTIARTL", "ITC", "LT", "HINDUNILVR",
    "AXISBANK", "KOTAKBANK", "SUNPHARMA", "TITAN", "BAJFINANCE", "MARUTI", "NTPC", "POWERGRID", "ASIANPAINT",
    "ULTRACEMCO", "TATAMOTORS", "COALINDIA", "TATASTEEL", "ADANIENT", "ADANIPORTS", "JSWSTEEL", "HCLTECH",
    "ONGC", "M&M", "GRASIM", "BAJAJ-AUTO", "NESTLEIND", "SIEMENS", "BEL", "HAL", "IOC", "DLF", "VBL",
    "LODHA", "ZYDUSLIFE", "INDUSINDBK", "BAJAJHFL", "TORNTPHARM", "APOLLOHOSP", "HYUNDAI", "BAJAJFINSV",
    "DRREDDY", "SHREECEM", "BAJAJHLDNG", "UNITDSPR", "ABB", "EICHERMOT", "DIVISLAB", "LICI", "INDHOTEL",
    "ICICIGI", "CGPOWER", "TRENT", "MOTHERSON", "ADANIPOWER", "JINDALSTEL", "PFC", "TECHM", "LTIM", "WIPRO",
    "PERSISTENT", "POLYCAB", "DIXON", "COFORGE", "MPHASIS", "ASTRAL", "SUPREMEIND", "PAGEIND",
    "MUTHOOTFIN", "CHOLAFIN", "ASHOKLEY", "OBEROIRLTY", "BALKRISIND", "CUMMINSIND", "TIINDIA",
    "MAXHEALTH", "LUPIN", "AUROPHARMA", "BOSCHLTD", "BHARATFORG", "PIIND", "SRF", "IDEA", "YESBANK",
    "IDFCFIRSTB", "TATAINVEST", "KPRMILL", "NAUKRI", "KALYANKJIL", "OFSS", "RADICO", "GLAXO", "FEDERALBNK",
    "AJANTPHARM", "TATACOMM", "EXIDEIND", "OIL", "PETRONET", "LICHSGFIN", "ESCORTS", "GODREJPROP", "ABBOTINDIA", "BHEL"
]

DEFAULT_SCAN_CLAUSE = "( {cash} ( [0] 15 minute close > [0] 15 minute vwap and [0] 15 minute volume > 100000 and [0] 15 minute close > 50 ) )"

def is_market_closed():
    now = datetime.now()
    if now.weekday() >= 5:
        return True
    return not (time(9, 15) <= now.time() <= time(15, 30))

# --- INDICATORS & CALCULATORS ---
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

def compute_volume_profile_poc(df, bins=20):
    """Calculates Point of Control (POC) price level with the highest volume density."""
    if df.empty or 'Volume' not in df.columns:
        return float(df['Close'].iloc[-1]) if not df.empty else 0.0
    price_bins = pd.cut(df['Close'], bins=bins)
    vol_profile = df.groupby(price_bins, observed=False)['Volume'].sum()
    poc_bin = vol_profile.idxmax()
    return round(float(poc_bin.mid), 2)

# --- CHARTINK & LIVE DATA FETCHERS ---
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
        st.error(f"Chartink Fetch Error: {e}")
    return []

@st.cache_data(ttl=15)
def fetch_live_market_data(symbols):
    data_dict = {}
    for sym in symbols:
        clean_sym = sym.upper().strip()
        try:
            ticker = yf.Ticker(f"{clean_sym}.NS")
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

            # 5M Intraday RSI Divergence Calculation
            rsi_5m = compute_rsi(df_intraday['Close'], period=14)
            curr_rsi = rsi_5m.iloc[-1]
            prev_rsi = rsi_5m.iloc[-6]
            price_curr = df_intraday['Close'].iloc[-1]
            price_prev = df_intraday['Close'].iloc[-6]

            bull_div = (price_curr <= price_prev) and (curr_rsi > prev_rsi)
            bear_div = (price_curr >= price_prev) and (curr_rsi < prev_rsi)

            data_dict[clean_sym] = {
                "cmp": cmp, "day_open": day_open, "prev_close": prev_close,
                "chg": pct_change, "vol": volume, "day_high": day_high,
                "day_low": day_low, "vwap": vwap, "bull_div": bull_div, "bear_div": bear_div
            }
        except Exception:
            continue
    return data_dict

# --- INTRADAY ENGINE ---
def process_ultimate_confluence(stock_data, top_n_count, force_post_market=False):
    buy_list, sell_list = [], []
    extracted = [item.get('nsecode', item.get('symbol', '')).strip() for item in stock_data if item.get('nsecode', item.get('symbol', ''))]
    active_symbols = list(dict.fromkeys(extracted + NSE_750_CORE))[:top_n_count*3]

    live_prices = fetch_live_market_data(active_symbols)
    closed = force_post_market or is_market_closed()

    for symbol in active_symbols:
        live_info = live_prices.get(symbol)
        if not live_info or live_info['cmp'] < 50.0:
            continue
            
        cmp, day_open, pct_change, volume = live_info['cmp'], live_info['day_open'], live_info['chg'], live_info['vol']
        day_high, day_low, vwap = live_info['day_high'], live_info['day_low'], live_info['vwap']
        bull_div, bear_div = live_info['bull_div'], live_info['bear_div']
        diff = day_high - day_low

        if not closed:
            if pct_change >= 0:
                fib_786 = round(day_high - (diff * 0.786), 2)
                entry_price = round(max(fib_786, vwap), 2)
                sl = round(entry_price * 0.996, 2)
                t1, t2 = round(entry_price * 1.012, 2), round(day_high, 2)
            else:
                fib_786 = round(day_low + (diff * 0.786), 2)
                entry_price = round(min(fib_786, vwap), 2)
                sl = round(entry_price * 1.004, 2)
                t1, t2 = round(entry_price * 0.988, 2), round(day_low, 2)
            execution_mode = "LIVE MARKET"
        else:
            if pct_change >= 0:
                entry_price = round(day_high - (diff * 0.50), 2)
                sl = round(entry_price * 0.994, 2)
                t1, t2 = round(day_high, 2), round(day_high + (diff * 0.382), 2)
            else:
                entry_price = round(day_low + (diff * 0.50), 2)
                sl = round(entry_price * 1.006, 2)
                t1, t2 = round(day_low, 2), round(day_low - (diff * 0.382), 2)
            execution_mode = "NEXT-SESSION PLAN"

        # Signal Green/Red Bolding Logic
        if pct_change >= 0:
            flag = f"🟢 BUY: Healthy Vol ({volume:,}) | RSI Bull Div: {bull_div}"
            buy_list.append({
                'Symbol': f"<span class='buy-text'>{symbol}</span>",
                'Signal': "<span class='buy-text'>BUY</span>",
                'Risk Analysis': f"<span class='buy-text'>{flag}</span>",
                'Last Close/CMP (₹)': f"<span class='buy-text'>₹{cmp:.2f}</span>",
                'VWAP (₹)': f"<span class='buy-text'>₹{vwap:.2f}</span>",
                'Tight Entry (₹)': f"<span class='buy-text'>₹{entry_price:.2f}</span>",
                'Small SL (₹)': f"<span class='buy-text'>₹{sl:.2f}</span>",
                'Target 1 (₹)': f"<span class='buy-text'>₹{t1:.2f}</span>",
                'Target 2 (₹)': f"<span class='buy-text'>₹{t2:.2f}</span>",
                'Change (%)': f"<span class='buy-text'>{pct_change:+.2f}%</span>",
                'RawVolume': volume,
                'Chart': f"https://in.tradingview.com/chart/?symbol=NSE:{symbol}"
            })
        else:
            flag = f"🔴 SELL: High Vol ({volume:,}) | RSI Bear Div: {bear_div}"
            sell_list.append({
                'Symbol': f"<span class='sell-text'>{symbol}</span>",
                'Signal': "<span class='sell-text'>SELL</span>",
                'Risk Analysis': f"<span class='sell-text'>{flag}</span>",
                'Last Close/CMP (₹)': f"<span class='sell-text'>₹{cmp:.2f}</span>",
                'VWAP (₹)': f"<span class='sell-text'>₹{vwap:.2f}</span>",
                'Tight Entry (₹)': f"<span class='sell-text'>₹{entry_price:.2f}</span>",
                'Small SL (₹)': f"<span class='sell-text'>₹{sl:.2f}</span>",
                'Target 1 (₹)': f"<span class='sell-text'>₹{t1:.2f}</span>",
                'Target 2 (₹)': f"<span class='sell-text'>₹{t2:.2f}</span>",
                'Change (%)': f"<span class='sell-text'>{pct_change:+.2f}%</span>",
                'RawVolume': volume,
                'Chart': f"https://in.tradingview.com/chart/?symbol=NSE:{symbol}"
            })

    df_b = pd.DataFrame(buy_list).sort_values(by='RawVolume', ascending=False).head(top_n_count) if buy_list else pd.DataFrame()
    df_s = pd.DataFrame(sell_list).sort_values(by='RawVolume', ascending=False).head(top_n_count) if sell_list else pd.DataFrame()
    return df_b, df_s

# --- WEEKLY MULTI-TIMEFRAME ENGINE (VWAP + VOLUME PROFILE + RSI/MACD) ---
@st.cache_data(ttl=300)
def fetch_weekly_mtf_strategy(symbols):
    results = []
    
    for sym in symbols[:100]:
        clean_sym = sym.upper().strip()
        try:
            ticker = yf.Ticker(f"{clean_sym}.NS")
            df_daily = ticker.history(period="6mo", interval="1d")
            df_weekly = ticker.history(period="2y", interval="1wk")
            df_monthly = ticker.history(period="5y", interval="1mo")
            
            if len(df_weekly) < 20 or len(df_monthly) < 6:
                continue

            cmp = round(float(df_weekly.iloc[-1]['Close']), 2)
            if cmp < 50.0:
                continue

            # 1. Weekly VWAP Calculation
            weekly_vol = df_weekly['Volume'].tail(10).sum()
            weekly_vwap = round(float((df_weekly['Close'].tail(10) * df_weekly['Volume'].tail(10)).sum() / weekly_vol), 2) if weekly_vol > 0 else cmp

            # 2. Volume Profile Point of Control (POC)
            vol_poc = compute_volume_profile_poc(df_daily)

            # 3. Demand / Supply Zones
            w_demand = round(df_weekly['Low'].tail(8).min(), 2)
            w_supply = round(df_weekly['High'].tail(8).max(), 2)
            m_demand = round(df_monthly['Low'].tail(4).min(), 2)
            m_supply = round(df_monthly['High'].tail(4).max(), 2)
            best_demand = max(w_demand, m_demand)
            best_supply = min(w_supply, m_supply)

            # 4. Weekly RSI Divergence
            rsi_w = compute_rsi(df_weekly['Close'], period=14)
            curr_rsi = round(float(rsi_w.iloc[-1]), 2)
            prev_rsi = round(float(rsi_w.iloc[-5]), 2)
            bull_div = (df_weekly['Low'].iloc[-1] <= df_weekly['Low'].iloc[-5]) and (curr_rsi > prev_rsi)
            bear_div = (df_weekly['High'].iloc[-1] >= df_weekly['High'].iloc[-5]) and (curr_rsi < prev_rsi)

            # 5. MACD Crossover
            macd, signal, hist = compute_macd(df_weekly['Close'])
            macd_bull = float(hist.iloc[-1]) > 0 and float(hist.iloc[-2]) <= 0
            macd_bear = float(hist.iloc[-1]) < 0 and float(hist.iloc[-2]) >= 0

            # Confluence Logic
            if (cmp >= weekly_vwap or cmp >= vol_poc) and (bull_div or macd_bull or cmp <= best_demand * 1.05):
                setup_type = "<span class='buy-text'>STRONG BUY (MTF Confluence)</span>"
                entry = cmp
                sl = round(min(best_demand, vol_poc) * 0.985, 2)
                t1 = round(cmp + (best_supply - cmp) * 0.5, 2)
                t2 = round(best_supply, 2)
                flag = "<span class='buy-text'>🟢 STRONG BUY: Above Weekly VWAP/POC & Demand Confluence</span>"
            elif (cmp <= weekly_vwap or cmp <= vol_poc) and (bear_div or macd_bear or cmp >= best_supply * 0.95):
                setup_type = "<span class='sell-text'>STRONG SELL (MTF Distribution)</span>"
                entry = cmp
                sl = round(max(best_supply, vol_poc) * 1.015, 2)
                t1 = round(cmp - (cmp - best_demand) * 0.5, 2)
                t2 = round(best_demand, 2)
                flag = "<span class='sell-text'>🔴 STRONG SELL: Below Weekly VWAP/POC & Supply Overhead</span>"
            else:
                setup_type = "<span>NEUTRAL RANGE</span>"
                entry, sl, t1, t2 = cmp, round(cmp * 0.98, 2), round(cmp * 1.05, 2), round(cmp * 1.10, 2)
                flag = "🟡 NEUTRAL: Consolidating near POC"

            results.append({
                'Symbol': f"<span class='buy-text'>{clean_sym}</span>" if "BUY" in setup_type else f"<span class='sell-text'>{clean_sym}</span>",
                'Strategy Setup': setup_type,
                'Risk Analysis': flag,
                'Weekly Close (₹)': cmp,
                'Weekly VWAP (₹)': weekly_vwap,
                'Volume POC (₹)': vol_poc,
                'MTF Demand Zone (₹)': best_demand,
                'MTF Supply Zone (₹)': best_supply,
                'Weekly RSI': curr_rsi,
                'Tight Entry (₹)': entry,
                'Small SL (₹)': sl,
                'Target 1 (₹)': t1,
                'Target 2 (₹)': t2,
                'Chart': f"https://in.tradingview.com/chart/?symbol=NSE:{clean_sym}"
            })
        except Exception:
            continue

    return pd.DataFrame(results)

# --- BACKTEST ENGINE ---
def run_live_backtest(target_date, scan_clause, top_n_count):
    raw_stocks = fetch_chartink_stocks(scan_clause)
    extracted = [item.get('nsecode', item.get('symbol', '')).strip() for item in raw_stocks if item.get('nsecode', item.get('symbol', ''))]
    stock_list = list(dict.fromkeys(extracted + NSE_750_CORE[:30]))[:top_n_count*2]
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

            is_buy = close_price >= open_price
            signal_color = "buy-text" if is_buy else "sell-text"
            signal_label = "BUY" if is_buy else "SELL"
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
                "Symbol": f"<span class='{signal_color}'>{symbol}</span>",
                "Signal": f"<span class='{signal_color}'>{signal_label}</span>",
                "Session Open (₹)": open_price, "Session High (₹)": max_price, "Session Low (₹)": min_price,
                "Session Close (₹)": close_price, "Tight Entry (₹)": entry_price, "Small SL (₹)": sl,
                "Target 1 (₹)": t1, "Target 2 (₹)": t2, "Status": status, 
                "P&L (%)": f"<span class='{signal_color}'>{pnl_val:+.2f}%</span>", "RawPnL": pnl_val,
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
    st.info(f"Market Status: **{market_status}** | Universe: **Top NSE 750**")
with col_slider:
    selected_count = st.slider("Select Output Count:", min_value=3, max_value=25, value=10, step=1)

st.markdown("---")

# --- TAB 1: INTRADAY ENGINE ---
with main_tab1:
    st.subheader("⚡ Intraday Engine (5M RSI Divergence + VWAP Confluence)")
    post_market_toggle = st.checkbox("Force Post-Market Next-Session Plan", value=is_market_closed())
    
    if st.button("🚀 Run Intraday Engine Scan", type="primary", use_container_width=True):
        with st.spinner("Scanning NSE 750 universe for intraday setups..."):
            raw_stocks = fetch_chartink_stocks(DEFAULT_SCAN_CLAUSE)
            df_b, df_s = process_ultimate_confluence(raw_stocks, selected_count, force_post_market=post_market_toggle)
            st.session_state['df_b_master'] = df_b
            st.session_state['df_s_master'] = df_s

    if 'df_b_master' not in st.session_state:
        empty_b, empty_s = process_ultimate_confluence([], selected_count, force_post_market=post_market_toggle)
        st.session_state['df_b_master'], st.session_state['df_s_master'] = empty_b, empty_s

    sub_tab_buy, sub_tab_sell = st.tabs([f"🟢 Top {selected_count} BUY Setups", f"🔴 Top {selected_count} SELL Setups"])

    with sub_tab_buy:
        df_b = st.session_state['df_b_master']
        if not df_b.empty:
            st.write(df_b.drop(columns=['RawVolume'], errors='ignore').to_html(escape=False, index=False), unsafe_allow_html=True)
        else:
            st.info("Click the button above to run the intraday scanner.")

    with sub_tab_sell:
        df_s = st.session_state['df_s_master']
        if not df_s.empty:
            st.write(df_s.drop(columns=['RawVolume'], errors='ignore').to_html(escape=False, index=False), unsafe_allow_html=True)
        else:
            st.info("Click the button above to run the intraday scanner.")

# --- TAB 2: INTRADAY BACKTESTER ---
with main_tab2:
    st.subheader("📊 Intraday Backtester Engine & Performance Summary")
    backtest_date = st.date_input("📅 Select Backtest Session Date", value=datetime.today().date() - timedelta(days=1))

    if st.button("🚀 Run Intraday Backtest", type="primary"):
        with st.spinner("Backtesting intraday candles..."):
            df_bt = run_live_backtest(backtest_date, DEFAULT_SCAN_CLAUSE, selected_count)
            st.session_state['df_bt_results'] = df_bt

    if 'df_bt_results' in st.session_state and not st.session_state['df_bt_results'].empty:
        df_bt = st.session_state['df_bt_results']
        total_trades = len(df_bt)
        t1_hits = len(df_bt[df_bt['Status'].str.contains("Target 1", na=False)])
        t2_hits = len(df_bt[df_bt['Status'].str.contains("Target 2", na=False)])
        sl_hits = len(df_bt[df_bt['Status'].str.contains("SL Hit", na=False)])
        win_rate = round(((t1_hits + t2_hits) / total_trades) * 100, 2) if total_trades > 0 else 0.0
        total_pnl = round(df_bt['RawPnL'].sum(), 2)

        col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
        col_m1.metric("Total Executed Trades", total_trades)
        col_m2.metric("Overall Win Rate", f"{win_rate}%")
        col_m3.metric("Total Cumulative P&L", f"{total_pnl:+.2f}%")
        col_m4.metric("Target Hits (T1 / T2)", f"🎯 {t1_hits} / 🎯 {t2_hits}")
        col_m5.metric("Stop Loss Hits", f"🛑 {sl_hits}")
        st.markdown("---")

        st.write(df_bt.drop(columns=['RawPnL'], errors='ignore').to_html(escape=False, index=False), unsafe_allow_html=True)

# --- TAB 3: WEEKLY MTF STRATEGY ---
with main_tab3:
    st.subheader("🗓️ Weekly MTF Strategy (Weekly VWAP + Volume Profile POC + RSI Divergence)")
    st.markdown("Scans NSE 750 for **Strong Buy / Strong Sell** setups using **Weekly VWAP**, **Volume Profile POC**, and **Multi-Timeframe Demand/Supply Confluence**.")

    if st.button("🚀 Run Weekly MTF Strategy Scan", type="primary", use_container_width=True):
        with st.spinner("Running Multi-Timeframe Volume Profile and VWAP analysis across NSE 750..."):
            df_mtf = fetch_weekly_mtf_strategy(NSE_750_CORE)
            st.session_state['df_mtf_strategy'] = df_mtf

    if 'df_mtf_strategy' in st.session_state and not st.session_state['df_mtf_strategy'].empty:
        st.write(st.session_state['df_mtf_strategy'].head(selected_count).to_html(escape=False, index=False), unsafe_allow_html=True)
