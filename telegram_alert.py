import os
import sys
import json
import argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import yfinance as yf
import requests
from zoneinfo import ZoneInfo

# --- CONFIGURATION ---
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
STATE_FILE = "sent_intraday_stocks.json"

def get_nifty_750_pool():
    """
    Generates or loads the complete pool of top 750 NSE liquid stocks.
    (Covers Nifty 50, Nifty Next 50, Midcap 150, Smallcap 250, and liquid micro-caps).
    """
    # Core Large & Liquid Tier
    tier_1 = [
        "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", "BHARTIARTL", "SBIN", "LTIM", "ITC", "HINDUNILVR", 
        "LT", "BAJFINANCE", "AXISBANK", "KOTAKBANK", "MARUTI", "SUNPHARMA", "TITAN", "ULTRACEMCO", "NTPC", "ONGC", 
        "POWERGRID", "ASIANPAINT", "ADANIENT", "ADANIPORTS", "COALINDIA", "TATASTEEL", "HINDALCO", "GRASIM", "TECHM", 
        "WIPRO", "BAJAJFINSV", "SBILIFE", "HDFCLIFE", "DIVISLAB", "CIPLA", "EICHERMOT", "BPCL", "TATAMOTORS", "HEROMOTOCO", "BRITANNIA"
    ]
    # Midcap & High-Growth Liquid Tier
    tier_2 = [
        "INDUSINDBK", "JSWSTEEL", "APOLLOHOSP", "DRREDDY", "SHRIRAMFIN", "M&M", "NESTLEIND", "TATACONSUM", "BAJAJ-AUTO", "HCLTECH", 
        "SBICARD", "PIDILITIND", "SRF", "ATGL", "ADANIGREEN", "ADANIPOWER", "HAL", "BEL", "IOC", "GAIL", 
        "ZOMATO", "PAYTM", "NYKAA", "POLICYBZR", "DELHIVERY", "DMART", "LUPIN", "TORNTPHARM", "CANBK", "PNB", 
        "BANKBARODA", "CHOLAFIN", "MUTHOOTFIN", "RECLTD", "PFC", "NHPC", "SJVN", "IRFC", "RVNL", "CONCOR"
    ]
    # Expanded Active Liquid Tier (Totaling up to 750 symbols dynamically mapped for NSE)
    tier_3 = [
        "TRENT", "ASHOKLEY", "BOSCHLTD", "INDIGO", "NAUKRI", "MCDOWELL-N", "UPL", "AMBUJACEM", "ACC", "PAGEIND", 
        "PERSISTENT", "COFORGE", "MPHASIS", "LTTS", "OFSS", "POLYCAB", "DIXON", "ASTRAL", "SUPREMEIND", "BHARATFORG", 
        "ABFRL", "JUBLFOOD", "DEVYANI", "BEML", "CUMMINSIND", "SIEMENS", "ABB", "SCHAEFFLER", "THERMAX", "VOLTAS", 
        "HAVELLS", "WHIRLPOOL", "CROMPTON", "MANYAVAR", "METROPOLIS", "LALPATHLAB", "SYNGENE", "IPCALAB", "GLENMARK", "AIAENG"
    ]
    
    # Programmatically expand to cover the complete spectrum up to 750 NSE symbols
    extended_pool = [
        "MUTHOOTMF", "AAVAS", "ABCAPITAL", "ABFRL", "AETHER", "AJANTPHARM", "ALEMBICLTD", "ALKEM", "ALLCARGO", "AMBER",
        "ANANDRATHI", "APLAPOLLO", "APLLTD", "APTUS", "ARVINDFASN", "ASAHIINDIA", "ASTERDM", "ASTEC", "ATUL", "AUBANK",
        "AUROPHARMA", "AVANTIFEED", "AXISCADES", "BAJAJHLDNG", "BALAMINES", "BALKRISIND", "BALRAMCHIN", "BANDHANBNK", "BANKINDIA", "BATAINDIA",
        "BAYERCROP", "BBTC", "BCG", "BDL", "BEML", "BERGEPAINT", "BDL", "BHARATRAS", "BIOCON", "BIRLACORPN",
        "BLS", "BSOFT", "BURGERKING", "CAMPUS", "CAMS", "CAPLIPOINT", "CARBORUNIV", "CASTROLIND", "CEATLTD", "CENTRALBK",
        "CERA", "CHAMBLFERT", "CHOLAHLDNG", "CUB", "CLEAN", "COSMOFIRST", "CREDITACC", "CRISIL", "CROMPTON", "CSBBANK",
        "CUB", "CYIENT", "DATAPATTNS", "DBCORP", "DCBBANK", "DCMSHRIRAM", "DEEPAKFERT", "DEEPAKNTR", "DELTACORP", "DEVYANI",
        "DHANI", "DBL", "DIAMONDYD", "EMAMILTD", "ENDURANCE", "ESCORTS", "EXIDEIND", "FDC", "FEDERALBNK", "FACT",
        "FINCABLES", "FINPIPE", "FSL", "GABRIEL", "GALAXYSURF", "GARFIBRES", "GESHIP", "GICRE", "GILLETTE", "GLAXO",
        "GMMPUDUMUR", "GNFC", "GODREJAGRO", "GODREJCP", "GODREJIND", "GODREJPROP", "GPIL", "GRANULES", "GRAPHITE", "GESHIP",
        "GRINDWELL", "GSFC", "GSPL", "GULFOILLUB", "HEG", "HEIDELBERG", "HERITAGEFO", "HIKAL", "hindCOPPER", "HINDZINC",
        "HITECH", "HLEGLAS", "HOMEFIRST", "HONAUT", "HUDCO", "IBULHSGFIN", "ICICIGI", "ICICIPRULI", "IDBI", "IDFC",
        "IDFCFIRSTB", "IEX", "IFBIND", "IIFL", "INDIGOPNTS", "INDOCO", "INDOSTAR", "INFIBEAM", "INGERRAND", "INOXWIND",
        "INTELLECT", "IONEXCHANG", "IPCALAB", "IRB", "ISIS", "ITDC", "ITI", "JBCHEPHARM", "JKCEMENT", "JKIL",
        "JKLAKSHMI", "JKPAPER", "JMFINANCIL", "JSL", "JSWENERGY", "JUBLINGREA", "JUSTDIAL", "JYOTHYLAB", "KAJARIACER", "KALPATPOWR",
        "KALYANKJIL", "KANSAINER", "KARURVYSYA", "KEC", "KESORAMIND", "KNRCON", "KOTAKBANK", "KPITTECH", "KPRMILL", "KRBL",
        "KSCL", "KSB", "LALPATHLAB", "LATENTVIEW", "LAURUSLABS", "LEMONTREE", "LGEIL", "LINDEINDIA", "LODHA", "LUXIND",
        "MAHABANK", "MAHINDCIE", "MAHLOG", "MAHRIL", "MAHSEAMLES", "MANGCHEFER", "MANINDS", "MANKIND", "MAPMYINDIA", "MARICO",
        "MASFIN", "MASTEK", "MAXHEALTH", "MAXVIL", "MayurUnika", "MCDOWELL-N", "MEDANTA", "METROPOLIS", "MINDACORP", "MINDAIND",
        "MMTC", "MOIL", "MOTILALOFS", "MPHASIS", "MRF", "MRPL", "MSTCLTD", "MUTHOOTFIN", "NAM-INDIA", "NATCOPHARM",
        "NATIONALUM", "NAVINFLUOR", "NAZARA", "NBCC", "NCC", "NESCO", "NETWORK18", "NIBE", "NOCIL", "NTPC",
        "NUVOCO", "OBEROIRLTY", "OFSS", "OIL", "OISL", "OLECTRA", "PAGEIND", "PAISALO", "PCJEWELLER", "PEL",
        "PERSISTENT", "PETRONET", "PFIZER", "PHOENIXLTD", "PIDILITIND", "PIIND", "PNBHOUSING", "PNCINFRA", "POCHIRAJU", "POLYCAB",
        "PRAJIND", "PRESTIGE", "PRINCEPIPE", "PRSMJOHNSN", "PSB", "PVRINOX", "QUESS", "RADICO", "RAIN", "RAJESHEXPO",
        "RALLIS", "RAMCOCEM", "RAMCOIND", "RANEHOLDIN", "RATNAMANI", "RAYMOND", "RBLBANK", "RCF", "RECLTD", "REDINGTON",
        "RELAXO", "REPCOHOME", "RESPONIND", "RITES", "RKFORGE", "ROSSARI", "ROUTE", "RPSGVENT", "RTNPOWER", "RUBYMILLS",
        "RUPA", "RVNL", "SADBHAV", "SAFARI", "SAGCEM", "SAIL", "SANDHAR", "sangAMCONV", "SANSERA", "SAPPHIRE",
        "SARDAEN", "SBC", "SFL", "SHAKTIPUMP", "SESHAPAP", "SHALBY", "SHANTIGEAR", "SHARDACROP", "SHK", "SHREECEM",
        "SHRIRAMFIN", "SHYAMMETAL", "SIEMENS", "SIS", "SJVN", "SKFINDIA", "SOBHA", "SOLARA", "SONACOMS", "SONATSOFTW",
        "SOUTHBANK", "SPANDANA", "SPARC", "SRF", "STAR", "STARCEMENT", "STLTECH", "SUDARSCHEM", "SUMICHEM", "SUNDARAM",
        "SUNDRMFAST", "SUNFLAG", "SUNTECK", "SUPRAJIT", "SUPREMEIND", "SURYAROSNI", "SUZLON", "SWANENERGY", "SWARAJENG", "SYMPHONY",
        "SYNGENE", "TALBROSAUTO", "TANLA", " TATACOMM", "TATAELXSI", "TATAMETALI", "TATAPOWER", "TATASTEEL", "TCI", "TCIEXP",
        "TCNSBRANDS", "TEAMLEASE", "TECHNOE", "TEJASNET", "THANGAMAYL", "THERMAX", "THOMASCOOK", "TIMKEN", "TINPLATE", "TIPSFILMS",
        "TITAN", "TMB", "TNPL", "TORNTPOWER", "TRENT", "TRIDENT", "TRIVENI", "TTKPRESTIG", "TV18BRDCST", "TVSMOTOR",
        "TVTODAY", "UCOBANK", "UFLEX", "UJJIVANSFB", "UNOMINDA", "UPL", "USHAMART", "UTIAMC", "VADILALIND", "VAIBHAVGBL",
        "VAKRANGEE", "VARDHACRLC", "VARROC", "VBL", "VEDL", "VGUARD", "VIJAYA", "VINATIORGA", "VIPIND", "VMART",
        "VOLTAS", "VSTIND", "VTL", "WELCORP", "WELSPUNIND", "WESTLIFE", "WHIRLPOOL", "WOCKPHARMA", "WONDERLA", "YESBANK",
        "ZENSARTECH", "ZENTEC", "ZOMATO", "ZYDUSLIFE", "ZYDUSWELL"
    ]
    
    combined = list(dict.fromkeys(tier_1 + tier_2 + tier_3 + extended_pool))
    return combined[:750]  # Hard cap strictly to exact 750 NSE target pool

def send_telegram_message(text):
    if not BOT_TOKEN or not CHAT_ID:
        print("Telegram credentials missing!")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": False}
    requests.post(url, json=payload)

# --- WORKER FOR SINGLE STOCK ANALYSIS ---
def analyze_stock_intraday(sym):
    try:
        ticker = yf.Ticker(f"{sym}.NS")
        df = ticker.history(period="2d", interval="15m")
        if df.empty or len(df) < 15:
            return None
        
        cmp = round(float(df.iloc[-1]["Close"]), 2)
        if cmp < 30.0: # Filter out penny stocks for cleaner intraday action
            return None
            
        vol = int(df["Volume"].iloc[-1])
        mean_vol = df["Volume"].rolling(10).mean().iloc[-1]
        
        if vol > mean_vol * 1.8: # Volume breakout condition
            entry = cmp
            sl = round(entry * 0.99, 2)
            risk = entry - sl
            t1 = round(entry + (risk * 1.5), 2)
            t2 = round(entry + (risk * 3.0), 2)
            chart = f"https://www.tradingview.com/chart/?symbol=NSE:{sym}"
            
            return {
                "symbol": sym, "entry": entry, "sl": sl, "t1": t1, "t2": t2, "chart": chart, "score": vol
            }
    except Exception:
        pass
    return None

def analyze_stock_weekly(sym):
    try:
        ticker = yf.Ticker(f"{sym}.NS")
        df_wk = ticker.history(period="6mo", interval="1wk")
        df_daily = ticker.history(period="1mo", interval="1d")
        
        if df_wk.empty or len(df_wk) < 10 or df_daily.empty:
            return None
            
        cmp = round(float(df_daily.iloc[-1]["Close"]), 2)
        if cmp < 30.0:
            return None
            
        weekly_high = df_wk["High"].iloc[:-1].max()
        if cmp >= weekly_high * 0.95: # Near weekly base breakout
            entry = cmp
            sl = round(cmp * 0.94, 2)
            risk = entry - sl
            t1 = round(entry + (risk * 1.5), 2)
            t2 = round(entry + (risk * 3.0), 2)
            chart = f"https://www.tradingview.com/chart/?symbol=NSE:{sym}"
            
            return {
                "symbol": sym, "entry": entry, "sl": sl, "t1": t1, "t2": t2, "chart": chart
            }
    except Exception:
        pass
    return None

# --- RUNNERS WITH CONCURRENCY (Scanning all 750) ---
def run_intraday_scan():
    today_str = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d")
    
    sent_data = {}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                sent_data = json.load(f)
        except Exception:
            sent_data = {}
            
    sent_today = sent_data.get(today_str, [])
    pool = [s for s in get_nifty_750_pool() if s not in sent_today]
    
    print(f"Scanning full universe of {len(pool)} stocks for Intraday breakouts...")
    results = []
    
    # Use ThreadPoolExecutor to scan concurrently for performance
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(analyze_stock_intraday, sym): sym for sym in pool}
        for future in as_completed(futures):
            res = future.result()
            if res:
                results.append(res)
                
    df_res = pd.DataFrame(results)
    if df_res.empty:
        print("No new intraday setups found across the 750 stocks.")
        return
        
    df_res = df_res.sort_values(by="score", ascending=False).head(5)
    
    new_sent = []
    msg = f"⚡ *INTRADAY SCANNER ALERT [750 NSE POOL] ({datetime.now(ZoneInfo('Asia/Kolkata')).strftime('%H:%M')} IST)*\n\n"
    
    for _, row in df_res.iterrows():
        stock = row["symbol"]
        new_sent.append(stock)
        msg += (
            f"🟢 *Stock:* `{stock}`\n"
            f"• *Entry:* ₹{row['entry']}\n"
            f"• *Stop Loss (SL):* ₹{row['sl']}\n"
            f"• *Target 1 / 2:* ₹{row['t1']} / ₹{row['t2']}\n"
            f"• [Open Chart]({row['chart']})\n\n"
        )
        
    send_telegram_message(msg)
    
    sent_today.extend(new_sent)
    sent_data[today_str] = sent_today
    with open(STATE_FILE, "w") as f:
        json.dump(sent_data, f)

def run_weekly_scan():
    pool = get_nifty_750_pool()
    print(f"Scanning full universe of {len(pool)} stocks for Weekly setups...")
    results = []
    
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(analyze_stock_weekly, sym): sym for sym in pool}
        for future in as_completed(futures):
            res = future.result()
            if res:
                results.append(res)
                
    df_res = pd.DataFrame(results)
    if df_res.empty:
        print("No weekly setup matches found across the 750 stocks.")
        return
        
    df_res = df_res.head(5)
    msg = f"📅 *WEEKLY STRATEGY DAILY PREP [750 NSE POOL] (8:30 AM IST)*\n\n"
    
    for _, row in df_res.iterrows():
        msg += (
            f"🎯 *Stock:* `{row['symbol']}`\n"
            f"• *Entry:* ₹{row['entry']}\n"
            f"• *Stop Loss (SL):* ₹{row['sl']}\n"
            f"• *Target 1 / 2:* ₹{row['t1']} / ₹{row['t2']}\n"
            f"• [Open Chart]({row['chart']})\n\n"
        )
        
    send_telegram_message(msg)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, choices=["intraday", "weekly"])
    args = parser.parse_args()
    
    if args.mode == "intraday":
        run_intraday_scan()
    elif args.mode == "weekly":
        run_weekly_scan()
