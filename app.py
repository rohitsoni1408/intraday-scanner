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
            if df_weekly.empty or
