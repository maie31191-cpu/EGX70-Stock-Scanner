import yfinance as yf
import pandas as pd
import numpy as np

# قائمة شاملة لجميع أسهم البورصة المصرية (EGX30 + EGX70 والشركات النشطة)
tickers = [
    # أسهم مؤشر EGX30 والقطاع المالي والبنوك
    "COMI.CA", "HRHO.CA", "FWRY.CA", "EAST.CA", "SWDY.CA", "TMGH.CA", "MFPC.CA", 
    "ABUK.CA", "EKHO.CA", "ETEL.CA", "AMOC.CA", "CIEB.CA", "ADIB.CA", "EXPA.CA", 
    "EGBE.CA", "EIDF.CA", "BTFH.CA", "BINV.CA", "ATLC.CA", "VALO.CA", "CCAP.CA",

    # أسهم العقارات والإنشاءات والخدمات الهندسية (EGX30 & EGX70)
    "PHDC.CA", "HELI.CA", "ORAS.CA", "EMFD.CA", "MNHD.CA", "ORWE.CA", "ACGC.CA", 
    "EGCH.CA", "AMER.CA", "ODHO.CA", "AREH.CA", "UNIT.CA", "PORT.CA", "EGAL.CA",

    # أسهم البتروكيماويات والأسمدة والطاقة
    "SKPC.CA", "KIMA.CA", "TAQA.CA", "SVEN.CA", "EGAS.CA", "OIFI.CA",

    # أسهم الصناعة والمنتجات الاستهلاكية والأغذية والأدوية (EGX70 & EGX30)
    "ISPH.CA", "JUFO.CA", "MCRO.CA", "AUTO.CA", "EFID.CA", "DOMH.CA", "OLFI.CA", 
    "ARAB.CA", "RAYA.CA", "RTVC.CA", "OCDI.CA", "ALCN.CA", "LCSW.CA", "ESRS.CA", 
    "MORA.CA", "GOCO.CA", "DAPH.CA",

    # أسهم الشحن والنقل والتغليف والخدمات
    "EEII.CA", "CSAG.CA", "MPRC.CA", "UPSS.CA", "EPK.CA", "AIND.CA", "ELWA.CA", 
    "MOIL.CA", "MIPH.CA", "VERT.CA", "SPMD.CA"
]

results = []

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# إزالة أي تكرارات وترتيب الرموز
tickers = sorted(list(set(tickers)))

print(f"جاري فحص جميع أسهم البورصة المصرية (EGX30 + EGX70) بعدد {len(tickers)} سهم...")

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

        # 1. حساب المتوسطات الأسية EMA 50 & EMA 200
        ema_50 = close.ewm(span=50, adjust=False).mean()
        ema_200 = close.ewm(span=200, adjust=False).mean()

        # 2. حساب مؤشر القوة النسبية RSI 14
        rsi = calculate_rsi(close, 14)

        # 3. حساب مؤشر MACD (12, 26, 9) والهستوجرام
        ema_12 = close.ewm(span=12, adjust=False).mean()
        ema_26 = close.ewm(span=26, adjust=False).mean()
        macd_line = ema_12 - ema_26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        histogram = macd_line - signal_line

        # أخذ قيم الإغلاق الحالي والشمعة السابقة
        curr_close = close.iloc[-1]
        c_ema50, c_ema200 = ema_50.iloc[-1], ema_200.iloc[-1]
        c_rsi = rsi.iloc[-1]
        
        c_macd, c_signal = macd_line.iloc[-1], signal_line.iloc[-1]
        p_macd, p_signal = macd_line.iloc[-2], signal_line.iloc[-2]
        
        c_hist, p_hist = histogram.iloc[-1], histogram.iloc[-2]

        # الشروط المطلوبة:
        # 1. EMA 50 أعلى من EMA 200
        cond1 = c_ema50 > c_ema200
        
        # 2. RSI بين 50 و 65
        cond2 = 50 <= c_rsi <= 65
        
        # 3. تقاطع MACD لأعلى مع زيادة في الهستوجرام (زخم إيجابي)
        macd_cross_up = (p_macd <= p_signal) and (c_macd > c_signal)
        hist_momentum = (c_hist > p_hist) and (c_hist > 0)
        cond3 = macd_cross_up and hist_momentum

        # إضافة السهم الذي تحققت فيه جميع الشروط الفنية
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
print("       نتائج فحص البورصة المصرية (EGX30 + EGX70) - شروط التقاطع والزخم       ")
print("=" * 65)

if results:
    res_df = pd.DataFrame(results)
    print(res_df.to_string(index=False))
else:
    print("لا توجد أسهم تطابق كافة الشروط الفنية في إغلاق اليوم.")
print("=" * 65)