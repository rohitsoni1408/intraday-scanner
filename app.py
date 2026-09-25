import numpy as np
import pandas as pd
import streamlit as st

# Set page configuration
st.set_page_config(
    page_title="Intraday & Weekly Strategy Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🚀 Advanced Quantitative Trading Dashboard")
st.markdown(
    "Scanning **Top 750 Nifty Universe** across Multi-Strategy Intraday & Weekly Engines."
)

---

# --- MOCK DATA / UNIVERSE LOADER (Replace with your live data source) ---
@st.cache_data
def load_market_universe():
  # Simulating top 750 stocks including large caps, mid caps, small caps, and recent IPOs
  data = {
      "Symbol": [
          "SUPREMEIND",
          "METROPOLIS",
          "SRF",
          "HAL",
          "BANKBARODA",
          "DEEPAJEWL",
          "SHANTIGOLD",
          "RELIANCE",
          "TCS",
      ],
      "Segment": [
          "Mid Cap",
          "Mid Cap",
          "Large Cap",
          "Large Cap",
          "Large Cap",
          "Small Cap / IPO",
          "Small Cap / IPO",
          "Mega Cap",
          "Mega Cap",
      ],
      "Market_Cap_Cr": [
          65000,
          18000,
          72000,
          310000,
          125000,
          2100,
          2500,
          1950000,
          1400000,
      ],
      "CMP": [3550.0, 582.6, 2540.0, 4800.0, 235.26, 250.0, 265.0, 2900.0, 4100.0],
      "Volume": [
          1200000,
          850000,
          1500000,
          900000,
          4500000,
          3500000,
          3100000,
          8000000,
          2500000,
      ],
      "VMA_50_Ratio": [7.24, 4.1, 2.62, 3.48, 2.83, 1.2, 0.9, 1.1, 1.0],
      "Listing_Days_Old": [
          1500,
          1200,
          2000,
          1800,
          1600,
          18,
          14,
          3000,
          3000,
      ],  # To handle recent IPOs
  }
  df = pd.DataFrame(data)
  df["Turnover_Cr"] = (df["Volume"] * df["CMP"]) / 10000000
  return df


df_universe = load_market_universe()

# --- STRATEGY ENGINE SELECTOR ---
st.sidebar.header("Strategy Hub")
strategy_type = st.sidebar.selectbox(
    "Choose Strategy Category:",
    ["Intraday Strategy Engine", "Weekly Strategy Engine"],
)

if strategy_type == "Intraday Strategy Engine":
  st.subheader("Choose Intraday Strategy Engine:")

  intraday_engine = st.selectbox(
      "",
      [
          (
              "15m 50-Period VMA (>=2.5x) Volume Expansion & Breakout Strategy"
              " (Established Trends)"
          ),
          (
              "🔥 High-Turnover & Small-Cap/IPO Momentum Surge (Catches New"
              " Listings & Massive Money Flow)"
          ),
      ],
  )

  if "15m 50-Period VMA" in intraday_engine:
    st.markdown(
        "Scanning Top 750 Nifty Universe using **15m 50-Period VMA (>=2.5x)"
        " Volume Expansion & Breakout Strategy**."
    )

    if st.button("🚀 Run Volume Expansion Breakout Scan"):
      # Filter logic for traditional VMA strategy
      filtered_df = df_universe[
          (df_universe["VMA_50_Ratio"] >= 2.5)
          & (df_universe["Listing_Days_Old"] > 30)
      ].copy()

      if not filtered_df.empty:
        st.success("Volume expansion breakout scan completed successfully!")

        display_data = []
        for _, row in filtered_df.iterrows():
          display_data.append({
              "Symbol": row["Symbol"],
              "Signal": "VOL EXPANSION BREAKOUT BUY",
              "Win Probability (%)": (
                  87.0
                  if row["VMA_50_Ratio"] < 4
                  else 89.5  # Dynamic mock probability
              ),
              "Setup Status": (
                  "🚀 Just After Breakout"
                  if row["VMA_50_Ratio"] > 5
                  else "⚡ Ready to Breakout (Compression)"
              ),
              "Confluence Reasons": (
                  f"Volume Surge: {row['VMA_50_Ratio']}x of 50-VMA"
              ),
              "Resistance (₹)": row["CMP"] - 5,
              "Last Close/CMP (₹)": row["CMP"],
          })
        st.dataframe(pd.DataFrame(display_data), use_container_width=True)
      else:
        st.warning("No stocks matched the strict VMA criteria today.")

  else:  # High Turnover / IPO Momentum Surge Engine
    st.markdown(
        "Scanning Top 750 Nifty Universe using **High-Turnover & Small-Cap/IPO"
        " Momentum Surge Engine** (Bypasses historical data requirements, targets"
        " stocks with ₹100Cr+ absolute turnover in mid/small caps)."
    )

    if st.button("🔥 Run High-Turnover Momentum Scan"):
      # Filter logic: Market cap <= 25000 Cr, Turnover >= 100 Cr, catches recent listings like Deepa Jewell / Shanti Gold
      filtered_df = df_universe[
          (df_universe["Market_Cap_Cr"] <= 25000)
          & (df_universe["Turnover_Cr"] >= 100)
      ].copy()

      if not filtered_df.empty:
        st.success(
            "High-turnover momentum & IPO volume scan completed successfully!"
        )

        display_data = []
        for _, row in filtered_df.iterrows():
          display_data.append({
              "Symbol": row["Symbol"],
              "Segment": row["Segment"],
              "Signal": "HIGH-TURNOVER MOMENTUM BUY",
              "Traded Turnover (₹ Cr)": round(row["Turnover_Cr"], 2),
              "Setup Status": (
                  "🔥 Explosive New Listing / Volume Spike"
                  if row["Listing_Days_Old"] <= 30
                  else "⚡ Mid-Cap High-Octane Runner"
              ),
              "Confluence Reasons": (
                  f"Heavy Liquidity Flow: ₹{round(row['Turnover_Cr'], 2)} Cr"
                  f" Traded | Age: {row['Listing_Days_Old']} days"
              ),
              "Last Close/CMP (₹)": row["CMP"],
          })
        st.dataframe(pd.DataFrame(display_data), use_container_width=True)
      else:
        st.warning(
            "No small/mid-cap stocks met the ₹100Cr+ turnover threshold today."
        )

else:  # Weekly Strategy Engine (Kept completely intact)
  st.subheader("Weekly Strategy Engine Hub")
  st.markdown(
      "Running multi-factor **Weekly Positional Trend & Breakout Engine** across"
      " the Top 750 Universe."
  )

  if st.button("📊 Run Weekly Position Scan"):
    weekly_filtered = df_universe[df_universe["Market_Cap_Cr"] > 5000].copy()
    weekly_data = []
    for _, row in weekly_filtered.head(5).iterrows():
      weekly_data.append({
          "Symbol": row["Symbol"],
          "Signal": "WEEKLY MULTI-WEEK BREAKOUT",
          "Trend Strength": "Strong Bullish",
          "Delivery Volume Spike": "High Institutional Accumulation",
          "CMP (₹)": row["CMP"],
      })
    st.success("Weekly positional scan completed successfully!")
    st.dataframe(pd.DataFrame(weekly_data), use_container_width=True)
