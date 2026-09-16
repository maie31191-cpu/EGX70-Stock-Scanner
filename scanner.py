import yfinance as yf
import pandas as pd
import numpy as np

# قائمة أسهم البورصة المصرية النشطة بالكامل
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
    # 1. شمعة المطرقة (Hammer)
    body = abs(close_p - open_p)
    lower_shadow = min(open_p, close_p) - low_p
    upper_shadow = high_p - max(open_p, close_p)
    is_hammer = (lower_shadow >= 2 * body) and (upper_shadow <= body * 0.5) and (body > 0)
    
    # 2. شمعة الابتلاع الإيجابي (Bullish Engulfing)
    prev_body_red = prev_close < prev_open
    curr_body_green = close_p > open_p
    is_engulfing = prev_body_red and curr_body_green and (open_p <= prev_close) and (close_p >= prev_open)
    
    # 3. شمعة انعكاسية قياسية (إغلاق أعمق فوق الافتتاح وبذيل سفلي)
    is_strong_green = (close_p > open_p) and (lower_shadow > body * 0.8)

    return is_hammer or is_engulfing or is_strong_green

def estimate_elliott_wave(close_prices, high_20, low_20):
    curr = close_prices.iloc[-1]
    if high_20 == low_20:
        return "غير محدد"
    
    # نسبة الارتداد من القاع مقارنة بالقمة (Fibonacci Retracement Level)
    retrace_ratio = (curr - low_20) / (high_20 - low_20)
    
    if 0.20 <= retrace_ratio <= 0.45:
        return "نهاية الموجة 2 (تأهب للموجة 3)"
    elif 0.46 <= retrace_ratio <= 0.65:
        return "نهاية الموجة 4 (تأهب للموجة 5)"
    elif retrace_ratio > 0.65:
        return "بداية موجة دافعة جديدة"
    else:
        return "ارتكاز على القاع (تجميع)"

tickers = sorted(list(set(tickers)))

print(f"جاري فحص جميع أسهم البورصة المصرية طبقاً للشروط المتقدمة بعدد {len(tickers)} سهم...")

for ticker in tickers:
    try:
        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        
        if df.empty or len(df) < 200:
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

        # 1. EMA 50 & EMA 200
        ema_50 = close.ewm(span=50, adjust=False).mean()
        ema_200 = close.ewm(span=200, adjust=False).mean()

        # 2. RSI 14
        rsi = calculate_rsi(close, 14)

        # 3. MACD & Signal Line
        ema_12 = close.ewm(span=12, adjust=False).mean()
        ema_26 = close.ewm(span=26, adjust=False).mean()
        macd_line = ema_12 - ema_26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        histogram = macd_line - signal_line

        # قيم الإغلاق والشمعة الأخيرة
        curr_close = close.iloc[-1]
        c_ema50, c_ema200 = ema_50.iloc[-1], ema_200.iloc[-1]
        c_rsi = rsi.iloc[-1]
        
        c_macd, p_macd = macd_line.iloc[-1], macd_line.iloc[-2]
        c_signal = signal_line.iloc[-1]
        c_hist, p_hist = histogram.iloc[-1], histogram.iloc[-2]

        # --- اختبار الشروط المطلوبة ---
        
        # أ) الاتجاه الصاعد العامة (EMA 50 > EMA 200)
        cond_ema = c_ema50 > c_ema200

        # ب) RSI فوق 50 وتحت 65
        cond_rsi = 50 <= c_rsi <= 65

        # ج) مرحلة دعم قوي (السعر قادم من مستوى دعم خلال آخر 20 شمعة)
        low_20 = low_p.iloc[-20:].min()
        high_20 = high_p.iloc[-20:].max()
        near_support = (curr_close - low_20) / low_20 <= 0.05  # السعر قريب من الدعم بحد أقصى 5%
        cond_support = near_support or (curr_close >= c_ema50 and abs(curr_close - c_ema50)/c_ema50 <= 0.02)

        # د) وجود شمعة تعكس التصحيح (Candlestick Reversal)
        cond_reversal = is_bullish_reversal_pattern(
            open_p.iloc[-1], high_p.iloc[-1], low_p.iloc[-1], close.iloc[-1],
            open_p.iloc[-2], close.iloc[-2]
        )

        # هـ) زخم شرائي في الماكد (قبل أو بداية التقاطع)
        macd_rising = c_macd > p_macd
        hist_rising = c_hist > p_hist
        cond_macd_momentum = macd_rising and hist_rising and (c_macd < c_signal or abs(c_macd - c_signal) < 0.05)

        # دمج جميع الشروط
        if cond_ema and cond_rsi and cond_support and cond_reversal and cond_macd_momentum:
            
            # تقدير مرحلة أليوت
            elliott_wave = estimate_elliott_wave(close, high_20, low_20)

            results.append({
                "Ticker": ticker,
                "Price": round(float(curr_close), 2),
                "RSI": round(float(c_rsi), 2),
                "EMA_50": round(float(c_ema50), 2),
                "EMA_200": round(float(c_ema200), 2),
                "Candle_Signal": "انعكاس إيجابي",
                "Elliott_Wave": elliott_wave
            })

    except Exception:
        continue

# طباعة الجدول النهائي
print("\n" + "=" * 85)
print("       فرص البورصة المصرية (دعم قوي + شمعة انعكاس + RSI 50-65 + موجات أليوت)       ")
print("=" * 85)

if results:
    res_df = pd.DataFrame(results)
    print(res_df.to_string(index=False))
else:
    print("لا توجد أسهم تطابق كافة هذه الشروط الفنية المركبة في إغلاق اليوم.")
print("=" * 85)
