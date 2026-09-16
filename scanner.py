import yfinance as yf
import pandas as pd
import numpy as np

# قائمة شاملة لكافة أسهم البورصة المصرية النشطة
tickers = [
    # البنوك والخدمات المالية
    "COMI.CA", "HRHO.CA", "FWRY.CA", "CCAP.CA", "CIEB.CA", "ADIB.CA", "EXPA.CA", 
    "EGBE.CA", "EIDF.CA", "BTFH.CA", "BINV.CA", "ATLC.CA", "VALO.CA", "SAIB.CA",
    "CANA.CA", "BLDY.CA", "CNTY.CA", "AIH.CA", "CICH.CA", "GRTE.CA", "EDBM.CA",
    
    # العقارات والتنمية والتطوير العمراني
    "TMGH.CA", "PHDC.CA", "HELI.CA", "ORAS.CA", "EMFD.CA", "MNHD.CA", "ACGC.CA", 
    "EGCH.CA", "AMER.CA", "ODHO.CA", "AREH.CA", "UNIT.CA", "PORT.CA", "EGAL.CA",
    "ROYO.CA", "ARAB.CA", "ZMID.CA", "MENA.CA", "TAQA.CA", "ORHD.CA", "DAPH.CA",
    
    # الكيماويات والبتروكيماويات والأسمدة
    "ABUK.CA", "MFPC.CA", "AMOC.CA", "SKPC.CA", "KIMA.CA", "SVEN.CA", "EGAS.CA", 
    "OIFI.CA", "FERT.CA", "ISMA.CA", "ICID.CA", "VERT.CA", "ASPC.CA", "SPMD.CA",
    
    # الأغذية، الأدوية والمنتجات الاستهلاكية
    "EAST.CA", "JUFO.CA", "ISPH.CA", "MCRO.CA", "EFID.CA", "DOMH.CA", "OLFI.CA", 
    "ORWE.CA", "AUTO.CA", "OCDI.CA", "ALCN.CA", "ESRS.CA", "MORA.CA", "GOCO.CA", 
    "AJWA.CA", "RAYA.CA", "OBRI.CA", "CLHO.CA", "PHAR.CA",
    
    # الاتصالات، التكنولوجيا والخدمات
    "SWDY.CA", "ETEL.CA", "EEII.CA", "CSAG.CA", "MPRC.CA", "UPSS.CA", "EPK.CA", 
    "AIND.CA", "ELWA.CA", "MOIL.CA", "EITC.CA", "KRDI.CA"
]

results = []

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

tickers = sorted(list(set(tickers)))

print(f"جاري فحص جميع أسهم البورصة المصرية بعدد {len(tickers)} سهم...")

for ticker in tickers:
    try:
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

        # 3. MACD (12, 26, 9) & Signal Line
        ema_12 = close.ewm(span=12, adjust=False).mean()
        ema_26 = close.ewm(span=26, adjust=False).mean()
        macd_line = ema_12 - ema_26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        histogram = macd_line - signal_line

        # القيم الحالية للسهم
        curr_close = close.iloc[-1]
        c_ema50, c_ema200 = ema_50.iloc[-1], ema_200.iloc[-1]
        c_rsi = rsi.iloc[-1]
        c_macd, c_signal = macd_line.iloc[-1], signal_line.iloc[-1]
        c_hist, p_hist = histogram.iloc[-1], histogram.iloc[-2]

        # -------------------------------------------------------------
        # شروط الاعتماد الاستباقي (قبل التقاطع بين MACD و Signal Line):
        # -------------------------------------------------------------
        # 1. اتجاه صاعد عام (EMA 50 أعلى من EMA 200)
        cond1 = c_ema50 > c_ema200
        
        # 2. RSI في نطاق ارتكاز وتجميع ممتاز (45 إلى 60)
        cond2 = 45 <= c_rsi <= 60
        
        # 3. التأكد التام من أن الماكد "لسه مقطعش" لكنه قريب جداً ويرتفع:
        macd_below_signal = c_macd < c_signal           # الماكد أسفل خط الإشارة (لم يتقاطعا بعد)
        hist_rising = c_hist > p_hist                   # الهستوجرام يتصاعد للأعلى
        gap = c_signal - c_macd                         # الفجوة بين الخطين
        narrow_gap = gap < (abs(c_macd) * 0.4 + 0.1)    # المسافة بينهما ضيقة جداً وقريبة من التلامس

        cond3 = macd_below_signal and hist_rising and narrow_gap

        if cond1 and cond2 and cond3:
            results.append({
                "Ticker": ticker,
                "Price": round(float(curr_close), 2),
                "RSI": round(float(c_rsi), 2),
                "MACD": round(float(c_macd), 3),
                "Signal_Line": round(float(c_signal), 3),
                "Status": "قبل التقاطع - قاطرة صعود وشيكة"
            })

    except Exception:
        continue

# طباعة الجدول النهائي
print("\n" + "=" * 70)
print("     أسهم البورصة المصرية التي لم تقطع بعد وقريبة من تقاطع MACD & Signal     ")
print("=" * 70)

if results:
    res_df = pd.DataFrame(results)
    print(res_df.to_string(index=False))
else:
    print("لا توجد أسهم حالياً في مرحلة التهيؤ قبل التقاطع مباشرة.")
print("=" * 70)
