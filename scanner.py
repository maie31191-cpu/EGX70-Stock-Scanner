import yfinance as yf
import pandas as pd
import numpy as np

# قائمة كاملة وشاملة لكافة الأسهم المدرجة بالبورصة المصرية
tickers = [
    # البنوك والخدمات المالية
    "COMI.CA", "HRHO.CA", "FWRY.CA", "CCAP.CA", "CIEB.CA", "ADIB.CA", "EXPA.CA", 
    "EGBE.CA", "EIDF.CA", "BTFH.CA", "BINV.CA", "ATLC.CA", "VALO.CA", "SAIB.CA",
    "CANA.CA", "BLDY.CA", "CNTY.CA", "AIH.CA", "CICH.CA", "GRTE.CA", "BINV.CA",
    "BOHI.CA", "EDBM.CA", "FRPX.CA", "EACB.CA", "KADP.CA", "EFIC.CA",
    
    # العقارات والتنمية والتطوير العمراني
    "TMGH.CA", "PHDC.CA", "HELI.CA", "ORAS.CA", "EMFD.CA", "MNHD.CA", "ACGC.CA", 
    "EGCH.CA", "AMER.CA", "ODHO.CA", "AREH.CA", "UNIT.CA", "PORT.CA", "EGAL.CA",
    "ROYO.CA", "ARAB.CA", "ZMID.CA", "MENA.CA", "TAQA.CA", "ORHD.CA", "DAPH.CA",
    "MEPA.CA", "ARPI.CA", "ELKA.CA", "UEGC.CA", "RTVC.CA", "HELI.CA", "AFMC.CA",
    
    # الكيماويات والبتروكيماويات والأسمدة والموارد الأساسية
    "ABUK.CA", "MFPC.CA", "AMOC.CA", "SKPC.CA", "KIMA.CA", "SVEN.CA", "EGAS.CA", 
    "OIFI.CA", "FERT.CA", "ISMA.CA", "ICID.CA", "VERT.CA", "ASPC.CA", "IPMI.CA",
    "PACH.CA", "MIPH.CA", "LCSW.CA", "SPMD.CA",
    
    # الأغذية، المشروبات، الأدوية والرعاية الصحية
    "EAST.CA", "JUFO.CA", "ISPH.CA", "MCRO.CA", "EFID.CA", "DOMH.CA", "OLFI.CA", 
    "ORWE.CA", "AUTO.CA", "OCDI.CA", "ALCN.CA", "ESRS.CA", "MORA.CA", "GOCO.CA", 
    "AJWA.CA", "RAYA.CA", "NINH.CA", "OBRI.CA", "DPH.CA", "CLHO.CA", "PHAR.CA",
    "SUCE.CA", "ADCI.CA", "BIGP.CA", "SFC.CA", "AXPH.CA", "LATO.CA",
    
    # الاتصالات، التكنولوجيا، الشحن والنقل والخدمات
    "SWDY.CA", "ETEL.CA", "EEII.CA", "CSAG.CA", "MPRC.CA", "UPSS.CA", "EPK.CA", 
    "AIND.CA", "ELWA.CA", "MOIL.CA", "EITC.CA", "KRDI.CA", "ACEX.CA", "CMRT.CA",
    "DSCW.CA", "TOWR.CA", "LATT.CA", "KASB.CA"
]

results = []

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# إزالة أي رموز مكررة وترتيبها
tickers = sorted(list(set(tickers)))

print(f"جاري فحص جميع أسهم البورصة المصرية السوق بالكامل بعدد {len(tickers)} سهم...")

for ticker in tickers:
    try:
        # جلب بيانات السهم اليومية
        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        
        if df.empty or len(df) < 200:
            continue

        if isinstance(df.columns, pd.MultiIndex):
            close = df['Close'][ticker]
        else:
            close = df['Close']

        # 1. EMA 50 & EMA 200
        ema_50 = close.ewm(span=50, adjust=False).mean()
        ema_200 = close.ewm(span=200, adjust=False).mean()

        # 2. RSI 14
        rsi = calculate_rsi(close, 14)

        # 3. MACD (12, 26, 9) والهستوجرام
        ema_12 = close.ewm(span=12, adjust=False).mean()
        ema_26 = close.ewm(span=26, adjust=False).mean()
        macd_line = ema_12 - ema_26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        histogram = macd_line - signal_line

        # قيم الإغلاق والشمعة السابقة
        curr_close = close.iloc[-1]
        c_ema50, c_ema200 = ema_50.iloc[-1], ema_200.iloc[-1]
        c_rsi = rsi.iloc[-1]
        
        c_macd, c_signal = macd_line.iloc[-1], signal_line.iloc[-1]
        p_macd, p_signal = macd_line.iloc[-2], signal_line.iloc[-2]
        
        c_hist, p_hist = histogram.iloc[-1], histogram.iloc[-2]

        # الشروط:
        # 1. EMA 50 فوق EMA 200
        cond1 = c_ema50 > c_ema200
        
        # 2. RSI بين 50 و 65
        cond2 = 50 <= c_rsi <= 65
        
        # 3. تقاطع MACD لأعلى مع زخم إيجابي في الهستوجرام
        macd_cross_up = (p_macd <= p_signal) and (c_macd > c_signal)
        hist_momentum = (c_hist > p_hist) and (c_hist > 0)
        cond3 = macd_cross_up and hist_momentum

        if cond1 and cond2 and cond3:
            results.append({
                "Ticker": ticker,
                "Price": round(float(curr_close), 2),
                "RSI": round(float(c_rsi), 2),
                "EMA_50": round(float(c_ema50), 2),
                "EMA_200": round(float(c_ema200), 2),
                "Signal": "فرصة دخول ممتازة"
            })

    except Exception:
        continue

# طباعة الجدول النهائي
print("\n" + "=" * 65)
print("         نتائج فحص السوق الكامل - جميع أسهم البورصة المصرية         ")
print("=" * 65)

if results:
    res_df = pd.DataFrame(results)
    print(res_df.to_string(index=False))
else:
    print("لا توجد أسهم تطابق كافة الشروط الفنية في إغلاق اليوم.")
print("=" * 65)
