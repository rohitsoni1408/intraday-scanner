# -*- coding: utf-8 -*-
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime
from datetime import datetime, time as dt_time, timedelta
import time
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
    page_title="Ultimate Multi-Timeframe Confluence Terminal - Intraday & Weekly Edition", layout="wide"
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


# --- MARKET STATUS & LAST TRADING DATE HELPERS (FIXED FOR IST) ---
def get_ist_now():
    try:
        return datetime.now(ZoneInfo("Asia/Kolkata"))
    except Exception:
        from datetime import timezone
        IST = timezone(timedelta(hours=5, minutes=30))
        return datetime.now(IST)


def is_market_closed():
    now = get_ist_now()
    if now.weekday() >= 5:
        return True
    market_open = dt_time(9, 15)
    market_close = dt_time(15, 30)
    return not (market_open <= now.time() <= market_close)


def get_last_trading_date():
    now = get_ist_now()
    d = now.date()
    # If weekend or before market hours on a weekday, get the previous trading day
    if now.weekday() == 5:  # Saturday
        d -= timedelta(days=1)
    elif now.weekday() == 6:  # Sunday
        d -= timedelta(days=2)
    elif now.time() < dt_time(9, 15):
        d -= timedelta(days=1)
        if d.weekday() == 5:
            d -= timedelta(days=1)
        elif d.weekday() == 6:
            d -= timedelta(days=2)
    return d


# --- MAIN APP ---
st.title("👑 NSE Ultimate Confluence & Strategy Engine (F&O Universe)")
st.markdown(
    "Trading Terminal featuring **Weekly Trade Strategy**, **Intraday Strategies Hub**, **Intraday Backtester Hub**, **F&O 9:16-9:30 Gainer/Loser Hub**, **Top 1000 15m Institutional Breakout Scanner**, and **Terminal Guide**."
)

market_status = (
    "🔴 CLOSED (Post-Market / Last Trading Session Active)"
    if is_market_closed()
    else "🟢 OPEN (Live Scanning Active)"
)
st.markdown(f"**Market Status:** {market_status} | **Default Active Session Date:** {get_last_trading_date()}")
st.markdown("---")

# Initialize Strategy Scan Storage in Session State
if "strategy_scans" not in st.session_state:
    st.session_state["strategy_scans"] = {}

# --- HORIZONTAL MASTER SCAN CONFIGURATION BAR ---
st.subheader("⚙ Master Scan Configuration")
config_col1, config_col2 = st.columns(2)
with config_col1:
    universe_limit = st.selectbox(
        "Scan Universe Size (Top Nifty Market Cap):",
        options=[50, 100, 200, 500, 750, 1000],
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

# --- CONSOLIDATED 6-TAB LAYOUT ---
main_tab_weekly, main_tab1, main_tab2, main_tab_gainer_loser, main_tab3, main_tab4 = st.tabs([
    "📅 Weekly Trade Strategy",
    "📈 Intraday Strategies Hub",
    "📊 Intraday Backtester Hub",
    "⚡ F&O 9:16-9:30 Gainer/Loser Hub",
    "⚡ Top 1000 15m Scanner",
    "📌 Terminal Info & Guide"
])


# --- OFFICIAL NSE F&O OPTION SECURITIES UNIVERSE POOL ---
@st.cache_data(ttl=86400)
def load_nse_fno_universe():
    fno_universe = [
        "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", "BHARTIARTL", "SBIN", "ITC", "HINDUNILVR",
        "LT", "BAJFINANCE", "AXISBANK", "KOTAKBANK", "MARUTI", "SUNPHARMA", "TITAN", "ULTRACEMCO", "NTPC", "ONGC",
        "POWERGRID", "ASIANPAINT", "ADANIENT", "ADANIPORTS", "COALINDIA", "TATASTEEL", "HINDALCO", "GRASIM", "TECHM", "WIPRO",
        "BAJAJFINSV", "SBILIFE", "HDFCLIFE", "DIVISLAB", "CIPLA", "EICHERMOT", "BPCL", "TATAMOTORS", "HEROMOTOCO", "BRITANNIA",
        "INDUSINDBK", "JSWSTEEL", "APOLLOHOSP", "DRREDDY", "SHRIRAMFIN", "M&M", "NESTLEIND", "TATACONSUM", "BAJAJ-AUTO", "HCLTECH",
        "SBICARD", "PIDILITIND", "SRF", "HAL", "BEL", "IOC", "GAIL", "ZOMATO", "PAYTM", "LUPIN", "TORNTPHARM", "CANBK", "PNB",
        "BANKBARODA", "CHOLAFIN", "MUTHOOTFIN", "RECLTD", "PFC", "NHPC", "IRFC", "CONCOR", "TRENT", "ASHOKLEY", "INDIGO",
        "UPL", "AMBUJACEM", "ACC", "PERSISTENT", "COFORGE", "MPHASIS", "POLYCAB", "DIXON", "ASTRAL", "SUPREMEIND", "BHARATFORG",
        "ABFRL", "JUBLFOOD", "SIEMENS", "ABB", "VOLTAS", "HAVELLS", "CROMPTON", "METROPOLIS", "LALPATHLAB", "SYNGENE", "IPCALAB",
        "GLENMARK", "APOLLOTYRE", "JIOFIN", "TATATECH", "HUDCO", "IREDA", "MAZDOCK", "COCHINSHIP", "BDL", "MOTHERSON", "SONACOMS",
        "STARHEALTH", "MEDANTA", "KPITTECH", "CYIENT", "SUZLON", "IDFCFIRSTB", "YESBANK", "NAVINFLUOR", "ABSLAMC", "ALKEM",
        "AMBER", "APLAPOLLO", "AUBANK", "AUROPHARMA", "BALKRISIND", "BALRAMCHIN", "BATAINDIA", "BERGEPAINT", "BSOFT", "CHAMBLFERT",
        "CUMMINSIND", "DEEPAKNTR", "DELTACORP", "ESCORTS", "EXIDEIND", "FEDERALBNK", "GNFC", "GODREJCP", "GODREJPROP", "GRANULES",
        "HINDCOPPER", "HINDPETRO", "HINDZINC", "ICICIGI", "ICICIPRULI", "IEX", "IGL", "INDIGOPNTS", "IPCALAB", "JKCEMENT",
        "LALPATHLAB", "LAURUSLABS", "LICHSGFIN", "LODHA", "M&MFIN", "MANAPPURAM", "MARICO", "MAXHEALTH", "MCX", "MUTHOOTFIN",
        "NAM-INDIA", "NATCOPHARM", "NATIONALUM", "NAVA", "NBCC", "NCC", "NLCINDIA", "NMDC", "OBEROIRLTY", "OFSS", "PEL",
        "PETRONET", "PHOENIXLTD", "PIIND", "PNBHOUSING", "PNCINFRA", "PRESTIGE", "PVRINOX", "RADICO", "RAMCOCEM", "RBLBANK",
        "RELAXO", "SBICARD", "SHREECEM", "SRF", "STAR", "SUNTV", "TATACOMM", "TATAELXSI", "TORNTPHARM", "TORNTPOWER", "TVSMOTOR",
        "UJJIVAN", "UPL", "VEDL", "VGUARD", "VOLTAS", "WHIRLPOOL", "ZEEL", "ZYDUSLIFE"
    ]
    return list(dict.fromkeys(fno_universe))


@st.cache_data(ttl=86400)
def load_nifty_market_cap_universe():
    universe = [
        "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", "BHARTIARTL", "SBIN", "LTIM", "ITC", "HINDUNILVR",
        "LT", "BAJFINANCE", "AXISBANK", "KOTAKBANK", "MARUTI", "SUNPHARMA", "TITAN", "ULTRACEMCO", "NTPC", "ONGC",
        "POWERGRID", "ASIANPAINT", "ADANIENT", "ADANIPORTS", "COALINDIA", "TATASTEEL", "HINDALCO", "GRASIM", "TECHM", "WIPRO",
        "BAJAJFINSV", "SBILIFE", "HDFCLIFE", "DIVISLAB", "CIPLA", "EICHERMOT", "BPCL", "TATAMOTORS", "HEROMOTOCO", "BRITANNIA",
        "INDUSINDBK", "JSWSTEEL", "APOLLOHOSP", "DRREDDY", "SHRIRAMFIN", "M&M", "NESTLEIND", "TATACONSUM", "BAJAJ-AUTO", "HCLTECH",
        "SBICARD", "PIDILITIND", "SRF", "ATGL", "ADANIGREEN", "ADANIPOWER", "HAL", "BEL", "IOC", "GAIL",
        "ZOMATO", "PAYTM", "NYKAA", "POLICYBZR", "DELHIVERY", "DMART", "LUPIN", "TORNTPHARM", "CANBK", "PNB",
        "BANKBARODA", "CHOLAFIN", "MUTHOOTFIN", "RECLTD", "PFC", "NHPC", "SJVN", "IRFC", "RVNL", "CONCOR",
        "TRENT", "ASHOKLEY", "BOSCHLTD", "INDIGO", "NAUKRI", "MCDOWELL-N", "UPL", "AMBUJACEM", "ACC", "PAGEIND",
        "PERSISTENT", "COFORGE", "MPHASIS", "LTTS", "OFSS", "POLYCAB", "DIXON", "ASTRAL", "SUPREMEIND", "BHARATFORG",
        "ABFRL", "JUBLFOOD", "DEVYANI", "BEML", "CUMMINSIND", "SIEMENS", "ABB", "SCHAEFFLER", "THERMAX", "VOLTAS",
        "HAVELLS", "WHIRLPOOL", "CROMPTON", "MANYAVAR", "METROPOLIS", "LALPATHLAB", "SYNGENE", "IPCALAB", "GLENMARK", "AIAENG",
        "MANKIND", "SUNTV", "APOLLOTYRE", "STLTECH", "WELCORP", "JIOFIN", "TATATECH", "HUDCO", "IREDA", "MAZDOCK",
        "COCHINSHIP", "BDL", "MOTHERSON", "SONACOMS", "ANANDRATHI", "CEINFO", "MAPMYINDIA", "STARHEALTH", "MEDANTA", "KPITTECH",
        "CYIENT", "TITAGARH", "TEXMACO", "SUZLON", "IDFCFIRSTB", "YESBANK", "JPPOWER", "ZENSARTECH", "INTELLECT", "BSOFT",
        "NAVINFLUOR", "ABSLAMC", "AETHER", "AJANTPHARM", "ALEMBICLTD", "ALKEM", "AMBER", "ANURAS", "APLAPOLLO", "APTUS",
        "ARVINDFASN", "ASAHIINDIA", "ASTERDM", "ASTEC", "ATUL", "AUBANK", "AUROPHARMA", "AVANTIFEED", "AXISCADES", "BAJAJELEC",
        "BALAMINES", "BALKRISIND", "BALRAMCHIN", "BATAINDIA", "BAYERCROP", "BBTC", "BCG", "BERGEPAINT", "BFUTILITIE", "BGRENERGY",
        "BHARATRAS", "BIRLACORPN", "BLS", "BURGERKING", "CCL", "CEATLTD", "CENTRALBK", "CENTURYPLY", "CERA", "CHAMBLFERT",
        "CHOLAHLDNG", "CIGNITITEC", "CUB", "DBCORP", "DBL", "DCAL", "DCBBANK", "DCMSHRIRAM", "DEEPAKFERT", "DEEPAKNTR",
        "DELTACORP", "DHANI", "DISHTV", "DRAM", "DREDGECORP", "EASEMYTRIP", "EDELWEISS", "EIDPARRY", "ELGIEQUIP", "EMAMILTD",
        "ENDURANCE", "ENGINERSIN", "EPL", "EQUITASBNK", "ERIS", "ESCORTS", "EXIDEIND", "FDC", "FEDERALBNK", "FINCABLES",
        "FINPIPE", "FSL", "GABRIEL", "GALAXYSURF", "GARFIBRES", "GESHIP", "GHCL", "GICRE", "GILLETTE", "GLAXO",
        "GLS", "GMMPFAUDLR", "GMRINFRA", "GNFC", "GODREJAGRO", "GODREJCP", "GODREJIND", "GODREJPROP", "GPIL", "GRANULES",
        "GRAPHITE", "GSFC", "GSPL", "GUJGASLTD", "GULFOILLUB", "HEG", "HEIDELBERG", "HERITGFOOD", "HIKAL", "HINDCOPPER",
        "HINDPETRO", "HINDZINC", "HITECH", "HMT", "HSCL", "IBULHSGFIN", "ICICIGI", "ICICIPRULI", "IEX", "IFBIND",
        "IFCI", "IGL", "IIFL", "INDIGOPNTS", "INDOCO", "INDOSTAR", "INFIBEAM", "INGERRAND", "IOB", "IOLCP",
        "IRB", "ISGEC", "ITI", "JAGRAN", "JAICORPLTD", "JBCHEPHARM", "JKCEMENT", "JKIL", "JKLAKSHMI", "JKPAPER",
        "JMFINANCIL", "JSL", "JSWENERGY", "JUBLINGL", "JUSTDIAL", "JYOTHYLAB", "KAJARIACER", "KALPATPOWR", "KALYANKJIL",
        "KANSAINER", "KTKBANK", "KEC", "KEI", "KFINTECH", "KNRCON", "KOTAKBANK", "KPIL", "KRBL", "KSCL", "KSB",
        "LAOPALA", "LAURUSLABS", "LEMONTREE", "LICHSGFIN", "LINDEINDIA", "LODHA", "LUXIND", "M&MFIN", "MAHABANK",
        "MAHINDRAEP", "MAHLOG", "MAHSEAMLES", "MANAPPURAM", "MAPMYINDIA", "MARICO", "MASFIN", "MAXHEALTH", "MAZDA", "MBLINFRA",
        "MCDHOLDING", "MEDPLUS", "METROPOLIS", "MHRIL", "MIDHANI", "MINDACORP", "MMTC", "MOIL", "MOL", "MOTHERSON",
        "MPHASIS", "MRF", "MRPL", "MSTCLTD", "MTARTECH", "MUTHOOTCAP", "NAM-INDIA", "NATCOPHARM", "NATIONALUM", "NAVA",
        "NBCC", "NCC", "NESCO", "NEOGEN", "NOCIL", "NLCINDIA", "NMDC", "NUVAMA", "OBEROIRLTY", "OIL", "OISL", "OLECTRA",
        "OMAXE", "ONMOBILE", "ORCHPHARMA", "ORIENTELEC", "OSWALAGRO", "PAISALO", "PCJEWELLER", "PEL", "PETRONET",
        "PFIZER", "PHOENIXLTD", "PIIND", "PNBHOUSING", "PNCINFRA", "PRAJIND", "PRESTIGE", "PRSMJOHNSN", "PSPPROJECT",
        "PVRINOX", "QUESS", "RADICO", "RAIN", "RAJESHEXPO", "RALLIS", "RANEHOLDIN", "RATNAMANI", "RAYMOND", "RCF",
        "RELAXO", "RENUKA", "REPCOHOME", "RITES", "RPSGVENT", "RTNPOWER", "RUBYMILLS", "RUSPER", "SADBHAV", "SAFARI",
        "SAIL", "SANDUMA", "SANGAMIND", "SANOFI", "SANSERA", "SAPPHIRE", "SARDAEN", "SBC", "SCHNEIDER", "SCI",
        "SEQUENT", "SFL", "SHANTIGEAR", "SHARDACROP", "SHILPAMED", "SHK", "SHOPERSTOP", "SHREECEM", "SHRIRAMPS", "SIS",
        "SKFINDIA", "SOBHA", "SOLARA", "SONATASW", "SOUTHBANK", "SPANDANA", "SPARC", "SRHHYPOLTD", "STAR", "STARCEMENT",
        "STOVEKRAFT", "SUBEXLTD", "SUMIT", "SUNDARAM", "SUNDRMFAST", "SUNCLAY", "SUNFLAG", "SUPRIYA", "SUTLEJTEX", "SUVEN",
        "SUVENPHAR", "SUZLON", "SWANENERGY", "SWARAJENG", "SYMPHONY", "TASTYBITE", "TATACELE", "TATACOMM", "TATAELXSI",
        "TATAMETALI", "TATAINVEST", "TCI", "TCIEXP", "TCNSBRANDS", "TEAMLEASE", "TECHNOE", "TEJASNET", "THANGAMAYL",
        "THOMASCOOK", "TIMKEN", "TIRUMALCHM", "TITAN", "TMRV", "TNPL", "TOKYOPLAST", "TORNTPHARM", "TORNTPOWER", "TPLPLAST",
        "TRIDENT", "TRITURBINE", "TIINDIA", "UCOBANK", "UFLEX", "UJJIVAN", "UJJIVANSFB", "UNICHEMLAB", "UNIMARC", "UNIONBANK",
        "USHAMART", "VAIBHAVGBL", "VAKRANGEE", "VARROC", "VBL", "VEDL", "VGUARD", "VINATIORGA", "VIPIND", "VMART",
        "VOLTAMP", "VSTIND", "VTL", "WABAG", "WELENT", "WSTCSTPAPR", "WHIRLPOOL", "WOCKPHARMA", "WONDERLA", "XPROINDIA",
        "ZENTEC", "ZODIAC", "ZYDUSLIFE", "ZYDUSWELL"
    ]
    return list(dict.fromkeys(universe))


NIFTY_1000_POOL = load_nifty_market_cap_universe()
NSE_FNO_POOL = load_nse_fno_universe()

SMALL_CAP_IPO_FALLBACK_POOL = [
    "ZOMATO", "PAYTM", "NYKAA", "POLICYBZR", "DELHIVERY", "JIOFIN", "TATATECH",
    "IRFC", "RVNL", "NHPC", "SJVN", "HUDCO", "IREDA", "MAZDOCK", "COCHINSHIP",
    "BDL", "BEL", "HAL", "MOTHERSON", "SONACOMS", "ANANDRATHI", "CEINFO",
    "MAPMYINDIA", "STARHEALTH", "MEDANTA", "KPITTECH", "CYIENT", "BEML",
    "TITAGARH", "TEXMACO", "SUZLON", "IDFCFIRSTB", "YESBANK", "JPPOWER",
    "BCG", "ZENSARTECH", "INTELLECT", "BSOFT", "NAVINFLUOR"
]

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


def compute_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1 / period, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1 / period, adjust=False).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


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


@st.cache_data(ttl=300)
def process_weekly_strategy(universe_pool, top_n_count):
    buy_list = []
    for sym in universe_pool:
        clean_sym = sym.upper().strip()
        if clean_sym.startswith("STOCK"):
            continue
        try:
            ticker = yf.Ticker(f"{clean_sym}.NS")
            df_weekly = ticker.history(period="1y", interval="1wk")
            if df_weekly.empty or len(df_weekly) < 20:
                continue
            if df_weekly.index.tz is not None:
                df_weekly.index = df_weekly.index.tz_localize(None)

            df_weekly["EMA_20"] = df_weekly["Close"].ewm(span=20, adjust=False).mean()
            df_weekly["RSI"] = compute_rsi(df_weekly["Close"], period=14)

            latest = df_weekly.iloc[-1]
            prev = df_weekly.iloc[-2]
            cmp = round(float(latest["Close"]), 2)

            if cmp < 50.0:
                continue

            is_weekly_trend_up = cmp > latest["EMA_20"] and latest["Close"] > prev["High"]
            rsi_val = float(latest["RSI"])
            if not (50 <= rsi_val <= 75 and is_weekly_trend_up):
                continue

            win_prob = 88.5
            sl = round(float(latest["Low"]) * 0.98, 2)
            risk = cmp - sl
            if risk <= 0:
                risk = cmp * 0.01
                sl = cmp - risk

            t1 = round(cmp + (risk * 2.0), 2)
            t2 = round(cmp + (risk * 4.0), 2)
            profit_pct = round(((t2 - cmp) / cmp) * 100, 2)
            score = win_prob + profit_pct

            buy_list.append({
                "Symbol": clean_sym,
                "Signal": "WEEKLY SWING BUY",
                "Win Probability (%)": f"{win_prob}%",
                "Confluence Reasons": "Weekly EMA 20 Support + Higher High Breakout + RSI Bullish",
                "Weekly Close (₹)": f"₹{cmp}",
                "Weekly SL (₹)": f"₹{sl}",
                "Target 1 (2R) (₹)": f"₹{t1}",
                "Target 2 (4R) (₹)": f"₹{t2}",
                "Gain (%)": f"{profit_pct:+.2f}%",
                "RawProfit": profit_pct,
                "RawWinProb": win_prob,
                "RawScore": score,
                "Chart": f"https://www.tradingview.com/chart/?symbol=NSE:{clean_sym}"
            })
        except Exception:
            continue

    df_res = pd.DataFrame(buy_list)
    if not df_res.empty:
        df_res = df_res.sort_values(by=["RawProfit", "RawWinProb", "RawScore"], ascending=False).head(top_n_count)
    return df_res


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
        col for col in df.columns if col not in ["RawVolume", "RawWinProb", "RawScore", "RawProfitPct", "RawPnL", "RawProfit", "DataFrame1m", "RawChg", "RawDelta"]
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


def scan_single_stock_top1000(ticker):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="5d", interval="15m")

        if df.empty or len(df) < 60:
            return None

        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)

        df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()
        df["EMA_50"] = df["Close"].ewm(span=50, adjust=False).mean()
        df["EMA_200"] = df["Close"].ewm(span=200, adjust=False).mean()

        df["BB_Middle"] = df["Close"].rolling(window=20).mean()
        df["BB_Std"] = df["Close"].rolling(window=20).std()
        df["BB_Upper"] = df["BB_Middle"] + (df["BB_Std"] * 2)
        df["BB_Lower"] = df["BB_Middle"] - (df["BB_Std"] * 2)
        df["BB_Bandwidth"] = (df["BB_Upper"] - df["BB_Lower"]) / df["BB_Middle"]

        df["Vol_SMA_50"] = df["Volume"].rolling(window=50).mean()
        df["RSI_14"] = compute_rsi(df["Close"], period=14)

        latest = df.iloc[-1]
        prev_few = df.iloc[-6:-1]
        cmp = round(float(latest["Close"]), 2)

        if cmp < 30.0:
            return None

        is_trend_bullish = (
            cmp > latest["EMA_20"]
