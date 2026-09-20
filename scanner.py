import yfinance as yf
import pandas as pd
import numpy as np

# قائمة أسهم البورصة المصرية
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

def check_reversal_candle(open_p, high_p, low_p, close_p, prev_open, prev_close):
    body = abs(close_p - open_p)
    lower_shadow = min(open_p, close_p) - low_p
    upper_shadow = high_p - max(open_p, close_p)
    
    is_hammer = (lower_shadow >= 1.2 * body) and (body > 0)
    is_engulfing = (prev_close < prev_open) and (close_p > open_p) and (close_p >= prev_open)
    is_strong_green = (close_p > open_p) and (lower_shadow >= body * 0.4)

    return is_hammer or is_engulfing or is_strong_green

def estimate_elliott_wave_daily(close_prices, high_20, low_20):
    curr = close_prices.iloc[-1]
    if high_20 == low_20:
        return "غير محدد"
    
    retrace_ratio = (curr - low_20) / (high_20 - low_20)
    
    if 0.15 <= retrace_ratio <= 0.45:
        return "الموجة 2 (تأهب للـ 3 اليومية)"
    elif 0.46 <= retrace_ratio <= 0.65:
        return "الموجة 4 (تأهب للـ 5 اليومية)"
    elif retrace_ratio > 0.65:
        return "موجة دافعة صاعدة يومياً"
    else:
        return "قاع تجميعي يومي"

tickers = sorted(list(set(tickers)))

print(f"جاري فحص جميع أسهم البورصة المصرية على الفريم اليومي بعدد {len(tickers)} سهم...")

for ticker in tickers:
    try:
        # جلب البيانات اليومية (1d)
        df = yf.download(ticker, period="1y", interval="1d", progress=False)
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

        # 1. EMA 20 & EMA 50 اليومي
        ema_20 = close.ewm(span=20, adjust=False).mean()
        ema_50 = close.ewm(span=50, adjust=False).mean()

        # 2. RSI اليومي
        rsi = calculate_rsi(close, 14)

        # 3. MACD اليومي
        ema_12 = close.ewm(span=12, adjust=False).mean()
        ema_26 = close.ewm(span=26, adjust=False).mean()
        macd_line = ema_12 - ema_26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        histogram = macd_line - signal_line

        curr_close = close.iloc[-1]
        c_ema20, c_ema50 = ema_20.iloc[-1], ema_50.iloc[-1]
        c_rsi = rsi.iloc[-1]
        
        c_macd, p_macd = macd_line.iloc[-1], macd_line.iloc[-2]
        c_hist, p_hist = histogram.iloc[-1], histogram.iloc[-2]

        low_20 = low_p.iloc[-20:].min()
        high_20 = high_p.iloc[-20:].max()

        score = 0
        matched_conditions = []

        # 1. الاتجاه العام اليومي
        if curr_close >= c_ema20 or c_ema20 >= c_ema50:
            score += 1
            matched_conditions.append("اتجاه صاعد")

        # 2. RSI اليومي المرن (45 إلى 68)
        if 45 <= c_rsi <= 68:
            score += 1
            matched_conditions.append(f"RSI {round(c_rsi, 1)}")

        # 3. قرب الدعم اليومي
        near_support = (curr_close - low_20) / low_20 <= 0.08 or (abs(curr_close - c_ema20) / c_ema20 <= 0.03)
        if near_support:
            score += 1
            matched_conditions.append("منطقة دعم")

        # 4. شمعة انعكاسية يومية
        is_reversal = check_reversal_candle(
            open_p.iloc[-1], high_p.iloc[-1], low_p.iloc[-1], close.iloc[-1],
            open_p.iloc[-2], close.iloc[-2]
        )
        if is_reversal:
            score += 1
            matched_conditions.append("شمعة انعكاسية")

        # 5. زخم MACD اليومي
        if (c_hist > p_hist) or (c_macd > p_macd):
            score += 1
            matched_conditions.append("زخم MACD")

        if score >= 3:
            elliott_wave = estimate_elliott_wave_daily(close, high_20, low_20)

            results.append({
                "Ticker": ticker,
                "Daily_Price": round(float(curr_close), 2),
                "Daily_RSI": round(float(c_rsi), 1),
                "Score": f"{score}/5",
                "Matches": ", ".join(matched_conditions),
                "Elliott_Wave_D": elliott_wave
            })

    except Exception:
        continue

results = sorted(results, key=lambda x: int(x['Score'].split('/')[0]), reverse=True)

print("\n" + "=" * 95)
print("     نتائج الفحص اليومي للبورصة المصرية (تحديث يوم بيوم - إغلاق الجلسة)     ")
print("=" * 95)

if results:
    res_df = pd.DataFrame(results)
    print(res_df.to_string(index=False))
else:
    print("لا توجد أسهم تطابق الحد الأدنى من الشروط اليومية.")
print("=" * 95)
 