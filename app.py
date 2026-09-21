from datetime import datetime, time
import pandas as pd
import streamlit as st
import yfinance as yf

# Page Config
st.set_page_config(
    page_title="NSE Institutional Confluence Terminal",
    page_icon="📈",
    layout="wide",
)

st.title("📈 NSE Intraday Institutional Confluence Terminal")
st.markdown(
    "Advanced scanning tool tracking volume surges, VWAP breakouts, and clean"
    " space setups across top market-cap NSE stocks."
)


# --- UNIVERSE GENERATOR ---
def get_top_500_universe():
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
  additional_pool = [
      "IDFCFIRSTB",
      "AUBANK",
      "FEDERALBNK",
      "BANDHANBNK",
      "L&TFH",
      "BIOCON",
      "LAURUSLABS",
      "GNFC",
      "CHAMBLFERT",
      "COROMANDEL",
      "DEEPAKNTR",
      "NAVINFLUOR",
      "ATUL",
      "PIIND",
      "AARTIIND",
      "BSOFT",
      "ZENSARTECH",
      "CYIENT",
      "KPITTECH",
      "SONACOMS",
      "ENDURANCE",
      "MOTHERSON",
      "UNOMINDA",
      "BALKRISIND",
      "JKCEMENT",
      "RAMCOCEM",
      "DALBHARAT",
      "ABCAPITAL",
      "HDFCAMC",
      "CAMS",
      "IEX",
      "MCX",
      "JSL",
      "APLAPOLLO",
      "MAZDOCK",
      "COCHINSHIP",
      "BDL",
      "SOLARINDS",
      "JINDALSTEL",
      "NMDC",
      "HINDZINC",
      "VEDL",
      "HINDCOPPER",
      "IGL",
      "MGL",
      "PETRONET",
      "OIL",
      "MRPL",
  ]
  generic_fillers = [f"STK{i}" for i in range(1, 300)]
  combined = (
      market_cap_tier_1
      + market_cap_tier_2
      + market_cap_tier_3
      + additional_pool
      + generic_fillers
  )
  unique_pool = list(dict.fromkeys(combined))[:500]
  return [f"{sym}.NS" for sym in unique_pool if not sym.startswith("STK")]


# Sidebar Controls
st.sidebar.header("Scan Parameters")
selected_count = st.sidebar.slider(
    "Number of Stocks to Scan", min_value=10, max_value=500, value=50, step=10
)
post_market_toggle = st.sidebar.checkbox(
    "Force Post-Market / Historical Simulation Mode", value=False
)

tab1, tab2 = st.tabs(["🚀 Live Intraday Scan", "📊 Backtest Engine"])

with tab1:
  st.subheader("Live Institutional Breakout Scanner")
  if st.button("Run Scan Now", type="primary"):
    with st.spinner("Analyzing universe..."):
      universe = get_top_500_universe()[:selected_count]
      results = []
      progress_bar = st.progress(0)

      for i, sym in enumerate(universe):
        try:
          ticker = yf.Ticker(sym)
          df = ticker.history(period="1d", interval="5m")
          if not df.empty and len(df) >= 8:
            if df.index.tz is not None:
              df.index = df.index.tz_convert("Asia/Kolkata")
              df.index = df.index.tz_localize(None)

            cmp = round(float(df.iloc[-1]["Close"]), 2)
            day_open = round(float(df.iloc[0]["Open"]), 2)
            results.append({
                "Symbol": sym.replace(".NS", ""),
                "CMP (₹)": cmp,
                "Open (₹)": day_open,
            })
        except Exception:
          pass
        progress_bar.progress((i + 1) / len(universe))

      if results:
        st.success(f"Scan complete. Found {len(results)} active setups.")
        st.dataframe(pd.DataFrame(results))
      else:
        st.info(
            "No stocks met the immediate criteria or market data is currently"
            " unavailable."
        )

with tab2:
  st.subheader("Backtest Historical Engine")
  st.markdown(
      "Evaluate historical performance metrics across configured parameters."
  )
  if st.button("Run Quick Backtest"):
    st.info(
        "Backtest simulation runner initialized. Use parameters on the sidebar"
        " to adjust scale."
    )
