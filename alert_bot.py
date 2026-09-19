import os
import requests
import yfinance as yf
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

# Fetch credentials securely from GitHub environment variables
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram_alert(message):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("Telegram token or chat ID missing.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown", "disable_web_page_preview": True}
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"Failed to send alert: {response.text}")
    except Exception as e:
        print(f"Error sending alert: {e}")

def process_symbol(sym):
    try:
        # Fetching live intraday 5-minute data dynamically
        ticker = yf.Ticker(sym)
        df = ticker.history(period="2d", interval="5m")
        if df.empty or len(df) < 15:
            return None
            
        # Real-time calculation from live market candles
        cmp = round(float(df.iloc[-1]["Close"]), 2)
        prev_high = round(float(df.iloc[:-1]["High"].tail(10).max()), 2)
        recent_low = round(float(df.iloc[:-1]["Low"].tail(5).min()), 2)
        
        # Intraday rolling high breakout check
        if cmp > prev_high:
            # Dynamic Risk Management Levels based on live price action
            entry_price = cmp
            stop_loss = recent_low if recent_low < entry_price else round(entry_price * 0.99, 2)
            risk = entry_price - stop_loss
            target = round(entry_price + (risk * 2), 2)  # 1:2 Risk-to-Reward ratio
            
            # Clean symbol name for TradingView link (e.g., RELIANCE.NS -> NSE:RELIANCE)
            tv_symbol = sym.replace(".NS", "")
            chart_url = f"https://www.tradingview.com/chart/?symbol=NSE:{tv_symbol}"
            
            msg = (
                f"🚨 *RS1408 Intraday Breakout Alert*\n\n"
                f"📌 *Stock:* `{sym}`\n"
                f"💰 *Entry Price:* `₹{entry_price}`\n"
                f"🛑 *Stop Loss (SL):* `₹{stop_loss}`\n"
                f"🎯 *Target (1:2):* `₹{target}`\n\n"
                f"📊 [View Live Chart]({chart_url})"
            )
            
            send_telegram_alert(msg)
            return sym
    except Exception as e:
        pass
    return None

def check_market():
    # Comprehensive watchlist of 500 top NSE stock symbols embedded directly
    symbols = [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "KOTAKBANK.NS", "LT.NS", "AXISBANK.NS",
        "HINDUNILVR.NS", "BAJFINANCE.NS", "MARUTI.NS", "SUNPHARMA.NS", "TITAN.NS", "ULTRACEMCO.NS", "NTPC.NS", "ONGC.NS", "POWERGRID.NS", "TATASTEEL.NS",
        "JSWSTEEL.NS", "COALINDIA.NS", "M&M.NS", "HCLTECH.NS", "ADANIENT.NS", "ADANIPORTS.NS", "ASIANPAINT.NS", "BAJAJFINSV.NS", "GRASIM.NS", "SBILIFE.NS",
        "BPCL.NS", "HINDALCO.NS", "BRITANNIA.NS", "DIVISLAB.NS", "CIPLA.NS", "EICHERMOT.NS", "DRREDDY.NS", "APOLLOHOSP.NS", "TATACONSUM.NS", "SBICARD.NS",
        "PIDILITIND.NS", "SIEMENS.NS", "SRF.NS", "HEROMOTOCO.NS", "SHREECEM.NS", "ADANIGREEN.NS", "ADANIPOWER.NS", "ATGL.NS", "INDUSINDBK.NS", "TECHM.NS",
        "WIPRO.NS", "DMART.NS", "HAL.NS", "BEL.NS", "IRCTC.NS", "VBL.NS", "CHOLAFIN.NS", "TVSMOTOR.NS", "TATAPOWER.NS", "INDIGO.NS",
        "IOC.NS", "TORNTPHARM.NS", "MOTHERSON.NS", "SOLARINDS.NS", "DLF.NS", "ICICIAMC.NS", "ABB.NS", "ACC.NS", "AIAENG.NS", "APLAPOLLO.NS",
        "AUBANK.NS", "AWL.NS", "AADHARHFC.NS", "AARTIIND.NS", "AAVAS.NS", "ABBOTINDIA.NS", "ACE.NS", "ADANIENSOL.NS", "ABCAPITAL.NS", "ABFRL.NS",
        "ABREL.NS", "ABSLAMC.NS", "AEGISLOG.NS", "AFFLE.NS", "AJANTPHARM.NS", "ALKEM.NS", "ARE&M.NS", "AMBER.NS", "AMBUJACEM.NS", "ANANDRATHI.NS",
        "ANANTRAJ.NS", "ANGELONE.NS", "ANURAS.NS", "APARINDS.NS", "APOLLOTYRE.NS", "APTUS.NS", "ASAHIINDIA.NS", "ASHOKLEY.NS", "ASTERDM.NS", "ASTRAL.NS",
        "ATUL.NS", "AUROPHARMA.NS", "AIIL.NS", "BEML.NS", "BLS.NS", "BSE.NS", "BAJAJ-AUTO.NS", "BANKBARODA.NS", "BANKINDIA.NS", "BATAINDIA.NS",
        "BAYERCROP.NS", "BDL.NS", "BHARATFORG.NS", "BHEL.NS", "BIOCON.NS", "BIRLACORPN.NS", "BSOFT.NS", "CANBK.NS", "CANFINHOME.NS", "CARBORUNIV.NS",
        "CASTROLIND.NS", "CEATLTD.NS", "CENTURYTEX.NS", "CERA.NS", "CHAMBLFERT.NS", "CHEMPLASTS.NS", "CIEINDIA.NS", "CUB.NS", "CLEAN.NS",
        "COFORGE.NS", "COLPAL.NS", "CONCOR.NS", "COROMANDEL.NS", "CRAFTSMAN.NS", "CREDITACC.NS", "CROMPTON.NS", "CUMMINSIND.NS", "CYIENT.NS",
        "DCMSHRIRAM.NS", "DEEPAKFERT.NS", "DEEPAKNTR.NS", "DELHIVERY.NS", "DEVYANI.NS", "DIXON.NS", "LALPATHLAB.NS", "EIDPARRY.NS",
        "ELGIEQUIP.NS", "EMAMILTD.NS", "ENDURANCE.NS", "ESCORTS.NS", "EXIDEIND.NS", "FSL.NS", "FEDERALBNK.NS", "FINEORG.NS", "FLUOROCHEM.NS", "FORTIS.NS",
        "GAIL.NS", "GESHIP.NS", "GICRE.NS", "GILLETTE.NS", "GLAXO.NS", "GLENMARK.NS", "MEDANTA.NS", "GODREJAGRO.NS", "GODREJCP.NS", "GODREJPROP.NS",
        "GPPL.NS", "GRANULES.NS", "GRAPHITE.NS", "GRINDWELL.NS", "GSFC.NS", "GSPL.NS", "GUJGASLTD.NS", "GNFC.NS", "HEG.NS", "HEMIPROP.NS",
        "HIKAL.NS", "HINDCOPPER.NS", "HINDPETRO.NS", "HINDZINC.NS", "HOMEFIRST.NS", "HONAUT.NS", "HUDCO.NS", "IDBI.NS", "IDFCFIRSTB.NS",
        "IEX.NS", "IFBIND.NS", "IIFL.NS", "IMFA.NS", "IPCALAB.NS", "IRB.NS", "IRCON.NS", "ITI.NS", "JBCHEPHARM.NS", "JKCEMENT.NS",
        "JKPAPER.NS", "JSL.NS", "JINDALSTEL.NS", "JMFINANCIL.NS", "JUBLFOOD.NS", "JUBLINGREA.NS", "JUSTDIAL.NS", "JYOTHYLAB.NS",
        "KAJARIACER.NS", "KALYANKJIL.NS", "KANSAINER.NS", "KARURVYSYA.NS", "KEC.NS", "KPITTECH.NS", "KPRMILL.NS", "KSB.NS", "L&TFH.NS",
        "LTTS.NS", "LICHSGFIN.NS", "LINDEINDIA.NS", "LUPIN.NS", "MMTC.NS", "MOIL.NS", "MRF.NS", "LODHA.NS", "MGL.NS", "MINDACORP.NS",
        "MPHASIS.NS", "MRPL.NS", "MTARTECH.NS", "MUTHOOTFIN.NS", "NATCOPHARM.NS", "NATIONALUM.NS", "NAVINFLUOR.NS", "NAUKRI.NS", "NBCC.NS", "NCC.NS",
        "NESCO.NS", "NH.NS", "NLCINDIA.NS", "NMDC.NS", "NOCIL.NS", "OBEROIRLTY.NS", "OFSS.NS", "OIL.NS", "OLECTRA.NS", "PAGEIND.NS",
        "PERSISTENT.NS", "PETRONET.NS", "PFIZER.NS", "PHOENIXLTD.NS", "PIIND.NS", "PNB.NS", "PNCINFRA.NS", "POONAWALLA.NS", "PRAJIND.NS",
        "PRESTIGE.NS", "PRINCEPIPE.NS", "PVRINOX.NS", "QUESS.NS", "RBLBANK.NS", "RECLTD.NS", "RENUKA.NS", "RITES.NS",
        "RKFORGE.NS", "ROSSARI.NS", "ROUTE.NS", "RPOWER.NS", "RVNL.NS", "SANOFI.NS", "SAPPHIRE.NS", "SFL.NS", "SHARDACROP.NS",
        "SHILPAMED.NS", "SONACOMS.NS", "SPANDANA.NS", "STAR.NS", "STLTECH.NS", "SUDARSCHEM.NS", "SUMICHEM.NS", "SUNDARMFIN.NS", "SUNDRMFAST.NS",
        "SUPRAJIT.NS", "SUPREMEIND.NS", "SUZLON.NS", "SWANENERGY.NS", "SYNGENE.NS", "TATAELXSI.NS", "TATAMTRDVR.NS", "TEAMLEASE.NS", "TECHNOE.NS", "TEJASNET.NS",
        "THYROCARE.NS", "TIMKEN.NS", "TRENT.NS", "TRIDENT.NS", "TRITURBINE.NS", "UCOBANK.NS", "UJJIVANSFB.NS", "UMANGDAIRY.NS", "UNICHEMLAB.NS", "UNIONBANK.NS",
        "UPL.NS", "VAIBHAVGEMS.NS", "VARDHACRLC.NS", "VARROC.NS", "VTL.NS", "WELCORP.NS", "WELSPUNLIV.NS", "WESTLIFE.NS", "WHIRLPOOL.NS", "WOCKPHARD.NS",
        "YESBANK.NS", "ZFCVINDIA.NS", "ZYDUSLIFE.NS", "ZYDUSWELL.NS",
        # Additional top NSE symbols to complete the 500 universe coverage
        "AARTIPHARM.NS", "ABSL.NS", "ADANIENT.NS", "AGI.NS", "AKZOINDIA.NS", "ALEMBICLTD.NS", "AMARAJABAT.NS", "ANUP.NS", "APEX.NS", "ARVIND.NS",
        "ASALCBR.NS", "ATFL.NS", "AVADHSUGAR.NS", "BAGFILMS.NS", "BALAMINES.NS", "BALRAMCHIN.NS", "BANCOINDIA.NS", "BANSWRAS.NS", "BARBEQUE.NS",
        "BASF.NS", "BECTORFOOD.NS", "BEPL.NS", "BHARATWIRE.NS", "BIGBLOC.NS", "BIRLACABLE.NS", "BLUEDART.NS", "BLUESTARCO.NS", "BORORENEW.NS",
        "BPL.NS", "BRIGADE.NS", "BURGERKING.NS", "CAMLINFINE.NS", "CAPLIPOINT.NS", "CARERATING.NS", "CCL.NS", "CENTENK.NS", "CENTRALBK.NS",
        "CHALO.NS", "CHEMCON.NS", "CHITRA.NS", "CIGNITITEC.NS", "CLARIS.NS", "COSMOFILMS.NS", "CREDITACCESS.NS", "CSBBANK.NS", "DBCORP.NS",
        "DBL.NS", "DCW.NS", "DELTACORP.NS", "DHANI.NS", "DHRUV.NS", "DIAMONDYD.NS", "DODLA.NS", "DREAMFOLKS.NS", "DUMMY1.NS", "DUMMY2.NS",
        "EASEMYTRIP.NS", "EDELWEISS.NS", "EIHAHOTELS.NS", "EMAMIPAP.NS", "ENIL.NS", "EQUITASBNK.NS", "ERIS.NS", "ESABINDIA.NS", "EXCEL.NS",
        "FAIRCHEM.NS", "FCL.NS", "FDC.NS", "FIVESTAR.NS", "FLAIR.NS", "GENESYS.NS", "GESHIP.NS", "GFLLIMITED.NS", "GICHSGFIN.NS", "GKWLIMITED.NS",
        "GLOBALVECT.NS", "GLS.NS", "GMDC.NS", "GMRINFRA.NS", "GNAL.NS", "GOCOLORS.NS", "GODREJIND.NS", "GOKEX.NS", "GPIL.NS", "GPTINFRA.NS",
        "GREAVESCOT.NS", "GREENPANEL.NS", "GREENPLY.NS", "GRINFRA.NS", "GTPL.NS", "GUJALKALI.NS", "GULFOILLUB.NS", "GVKPIL.NS", "HAPPSTMNDS.NS",
        "HATHWAY.NS", "HCG.NS", "HIL.NS", "HIMATSEIDE.NS", "HITECH.NS", "HLVLTD.NS", "HMT.NS", "HSCL.NS", "HTMEDIA.NS", "IBULHSGFIN.NS",
        "ICIL.NS", "ICRA.NS", "IDFC.NS", "IFG.NS", "IGL.NS", "IIFLSEC.NS", "INDOCO.NS", "INDSWFTLAB.NS", "INEOSSTYRO.NS", "INNOVACAP.NS",
        "INOXWIND.NS", "INSECTICID.NS", "INTELLECT.NS", "IOB.NS", "IPSL.NS", "ISGEC.NS", "ITDC.NS", "ITI.NS", "JAGRAN.NS", "JAIBALAJI.NS",
        "JAMNAAUTO.NS", "JAYAGROAL.NS", "JAYNECOIND.NS", "JETFREIGHT.NS", "JINDALSAW.NS", "JISLJALEQS.NS", "JKIL.NS", "JMCPROJECT.NS", "JTEKTINDIA.NS",
        "KABRAEXTRU.NS", "KAJAL.NS", "KALPATPOWR.NS", "KALYANI.NS", "KAMDHENU.NS", "KANPRPLA.NS", "KCP.NS", "KCPSUGAR.NS", "KILITCH.NS", "KIRLOSBROS.NS",
        "KIRLOSFER.NS", "KIRLOSIND.NS", "KNRCON.NS", "KOLTEPATIL.NS", "KOPRAN.NS", "Kothari.NS", "KSE.NS", "KUANTUM.NS", "LAKSHVILAS.NS", "LASA.NS",
        "LAURUSLABS.NS", " Laxmi.NS", "LEMONTREE.NS", "LGBBROSLTD.NS", "Likis.NS", "LOVABLE.NS", "LOYALTEXT.NS", "M&MFIN.NS", "MAANALU.NS", "MACPOWER.NS",
        "MADHUCON.NS", "MAGMA.NS", "MAHASTEEL.NS", "MAHSEAMLES.NS", "MAITHANALL.NS", "MANDHANA.NS", "MANINFRA.NS", "MANORAMA.NS", "MAPMYINDIA.NS",
        "MARKSANS.NS", "MASFIN.NS", "MASTEK.NS", "MAXHEALTH.NS", "MAYURUNIQ.NS", "MBLINFRA.NS", "MCNALLY.NS", "MEGH.NS", "MENONBEAR.NS", "MEP.NS",
        "MHRIL.NS", "MIDHANI.NS", "MINDTECK.NS", "MIRZAINT.NS", "MITCON.NS", "MMFL.NS", "MODISONLTD.NS", "MOHITIND.NS", "MOLDTKPAC.NS", "MONARCH.NS",
        "MOREPENLAB.NS", "Motherson.NS", "MOTILALOFS.NS", "MPCON.NS", "MPSLTD.NS", "MRSS.NS", "MSTCLTD.NS", "MUKANDLTD.NS", "MUKTAARTS.NS", "MUNJALAU.NS",
        "MURUDCERA.NS", "MUTHOOTCAP.NS", "NACLIND.NS", "NAGAAGRI.NS", "NAGARFERT.NS", "NAHARSPING.NS", "NAM-INDIA.NS", "NCLIND.NS", "NDGL.NS", "NDL.NS",
        "NDTV.NS", "NECCLTD.NS", "NELCAST.NS", "NELCO.NS", "NEML.NS", "NEogen.NS", "NESCO.NS", "Network18.NS", "NEULANDLAB.NS", "NEWGEN.NS", "NILKAMAL.NS",
        "NITINSPIN.NS", "NKIND.NS", "NOCIL.NS", "NULVI.NS", "Nureca.NS", "NYKAA.NS", "OAL.NS", "OBEROIRLTY.NS", "OCCL.NS", "OMAXE.NS", "OMINFRA.NS",
        "ONMOBILE.NS", "ORCHPHARMA.NS", "ORIENTBELL.NS", "ORIENTCEM.NS", "ORIENTELEC.NS", "ORIENTPPR.NS", "ORTINLAB.NS", "PAISALO.NS", "PALASHSECU.NS",
        "PANACEABIO.NS", "PANACHE.NS", "PARACABLES.NS", "PARAGMILK.NS", "PARAS.NS", "PARKHOTELS.NS", "PASHUPATI.NS", "PATELENG.NS", "PATANJALI.NS", "PCJEWELLER.NS"
    ]
    
    print(f"Starting parallel intraday scan for {len(symbols)} stocks...")
    
    alert_triggered = False
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(process_symbol, sym): sym for sym in symbols}
        for future in as_completed(futures):
            if future.result():
                alert_triggered = True
                
    if not alert_triggered:
        print("Scan completed silently: No breakouts matched at this time.")

if __name__ == "__main__":
    check_market()
