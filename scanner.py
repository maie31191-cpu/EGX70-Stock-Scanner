import yfinance as yf
import pandas as pd
import numpy as np

# قائمة شاملة لجميع أسهم البورصة المصرية النشطة
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

def is_bullish_reversal_pattern(open_p, high_p, low_p, close_p, prev_open, prev_close):
    body = abs(close_p - open_p)
    lower_shadow = min(open_p, close_p) - low_p
    upper_shadow = high_p - max(open_p, close_p)
    
    # 1. شمعة المطرقة الأسبوعية (Hammer)
    is_hammer = (lower_shadow >= 1.2 * body) and (body > 0)
    # 2. شمعة ابتلاع إيجابي أسبوعية (Bullish Engulfing)
    is_engulfing = (prev_close < prev_open) and (close_p > open_p) and (close_p >= prev_open)
    # 3. إغلاق أسبوعي أخضر قوي بذيل سفلي
    is_strong_green = (close_p > open_p) and (lower_shadow >= body * 0.5)

    return is_hammer or is_engulfing or is_strong_green

def estimate_elliott_wave_weekly(close_prices, high_20, low_20):
    curr = close_prices.iloc[-1]
    if high_20 == low_20:
        return "غير محدد"
    
    retrace_ratio = (curr - low_20) / (high_20 - low_20)
    
    if 0.15 <= retrace_ratio <= 0.45:
        return "نهاية الموجة 2 (تأهب للـ 3 الأسبوعية)"
    elif 0.46 <= retrace_ratio <= 0.65:
        return "نهاية الموجة 4 (تأهب للـ 5 الأسبوعية)"
    elif retrace_ratio > 0.65:
        return "بداية موجة دافعة أسبوعية"
    else:
        return "ارتكاز قاع أسبوعي (تجميع)"

tickers = sorted(list(set(tickers)))

print(f"جاري فحص جميع أسهم البورصة المصرية على الفريم الأسبوعي بعدد {len(tickers)} سهم...")

for ticker in tickers:
    try:
        # جلب البيانات الأسبوعية (1wk)
        df = yf.download(ticker, period="3y", interval="1wk", progress=False)
        df = df.dropna()

        if df.empty or len(df) < 30:
            continue

        if isinstance(df.columns, pd.MultiIndex):
            close = df['Close'][ticker]
            open_p = df['Open'][ticker]
            high_p = df['High'][ticker]
            low_p = df['Low'][ticker]
        else:
            close = df['Close']
            open_p = df['Open']
            high_p = df['High']
            low_p = df['Low']

        # 1. EMA 50 & EMA 200 (أو EMA 20 للفريم الأسبوعي المرتكز)
        ema_50 = close.ewm(span=50, adjust=False).mean()
        ema_200 = close.ewm(span=200, adjust=False).mean() if len(close) >= 200 else close.ewm(span=100, adjust=False).mean()

        # 2. RSI الأسبوعي (14 أسبوع)
        rsi = calculate_rsi(close, 14)

        # 3. MACD الأسبوعي (12, 26, 9)
        ema_12 = close.ewm(span=12, adjust=False).mean()
        ema_26 = close.ewm(span=26, adjust=False).mean()
        macd_line = ema_12 - ema_26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        histogram = macd_line - signal_line

        # القيم الأسبوعية الحالية والسابقة
        curr_close = close.iloc[-1]
        c_ema50, c_ema200 = ema_50.iloc[-1], ema_200.iloc[-1]
        c_rsi = rsi.iloc[-1]
        
        c_macd, p_macd = macd_line.iloc[-1], macd_line.iloc[-2]
        c_signal = signal_line.iloc[-1]
        c_hist, p_hist = histogram.iloc[-1], histogram.iloc[-2]

        # --- شروط الفحص الأسبوعي ---
        
        # أ) اتجاه صاعد عام (EMA 50 أعلى من EMA 200 أو فوق EMA 50)
        cond_ema = (c_ema50 >= c_ema200) or (curr_close >= c_ema50)

        # ب) RSI بين 50 و 65 أسبوعياً
        cond_rsi = 50 <= c_rsi <= 65

        # ج) السهم في منطقة دعم أسبوعي قوي (قريب من قاع آخر 16 أسبوعاً أو متوسط EMA 50)
        low_16 = low_p.iloc[-16:].min()
        high_16 = high_p.iloc[-16:].max()
        near_support = (curr_close - low_16) / low_16 <= 0.10 # قريب من الدعم بنسبة 10%
        cond_support = near_support or (abs(curr_close - c_ema50) / c_ema50 <= 0.04)

        # د) شمعة انعكاسية تدل على إنهاء التصحيح الأسبوعي
        cond_reversal = is_bullish_reversal_pattern(
            open_p.iloc[-1], high_p.iloc[-1], low_p.iloc[-1], close.iloc[-1],
            open_p.iloc[-2], close.iloc[-2]
        )

        # هـ) زخم شرائي في MACD (ارتفاع الماكد أو الهستوجرام الأسبوعي)
        cond_macd = (c_hist > p_hist) or (c_macd > p_macd)

        # دمج الشروط
        if cond_ema and cond_rsi and cond_support and cond_reversal and cond_macd:
            
            # تحديد مرحلة موجات أليوت الأسبوعية
            elliott_wave = estimate_elliott_wave_weekly(close, high_16, low_16)

            results.append({
                "Ticker": ticker,
                "Price": round(float(curr_close), 2),
                "Weekly_RSI": round(float(c_rsi), 2),
                "EMA_50": round(float(c_ema50), 2),
                "Signal": "انعكاس أسبوعي إيجابي",
                "Elliott_Wave_W": elliott_wave
            })

    except Exception:
        continue

# طباعة الجدول النهائي
print("\n" + "=" * 85)
print("     نتائج الفريم الأسبوعي للبورصة المصرية (دعم + شمعة انعكاس + RSI 50-65 + أليوت)     ")
print("=" * 85)

if results:
    res_df = pd.DataFrame(results)
    print(res_df.to_string(index=False))
else:
    print("لا توجد أسهم تطابق الشروط الفنية الأسبوعية كاملة في إغلاق هذا الأسبوع.")
print("=" * 85)
