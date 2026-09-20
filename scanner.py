import requests
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

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

# حساب RSI الصحيح والدقيق بالنعومة المطلوبة بدون إخراج قيم NaN
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def check_reversal_candle(open_p, high_p, low_p, close_p, prev_open, prev_close):
    body = abs(close_p - open_p)
    lower_shadow = min(open_p, close_p) - low_p
    upper_shadow = high_p - max(open_p, close_p)
    
    is_hammer = (lower_shadow >= 1.2 * body) and (body > 0)
    is_engulfing = (prev_close < prev_open) and (close_p > open_p) and (close_p >= prev_open)
    is_strong_green = (close_p > open_p) and (lower_shadow >= body * 0.4)

    return is_hammer or is_engulfing or is_strong_green

def estimate_elliott_wave_weekly(close_prices, high_16, low_16):
    curr = close_prices.iloc[-1]
    if high_16 == low_16:
        return "غير محدد"
    
    retrace_ratio = (curr - low_16) / (high_16 - low_16)
    
    if 0.15 <= retrace_ratio <= 0.45:
        return "الموجة 2 (تأهب للـ 3 الأسبوعية)"
    elif 0.46 <= retrace_ratio <= 0.65:
        return "الموجة 4 (تأهب للـ 5 الأسبوعية)"
    elif retrace_ratio > 0.65:
        return "موجة دافعة صاعدة أسبوعياً"
    else:
        return "قاع تجميعي أسبوعي"

def get_realtime_price(ticker):
    try:
        t = yf.Ticker(ticker)
        fast = t.fast_info
        if 'lastPrice' in fast and fast['lastPrice'] is not None and fast['lastPrice'] > 0:
            return float(fast['lastPrice'])
        if 'previousClose' in fast and fast['previousClose'] is not None and fast['previousClose'] > 0:
            return float(fast['previousClose'])
    except Exception:
        pass
    return None

tickers = sorted(list(set(tickers)))

print(f"جاري فحص جميع أسهم البورصة المصرية على الفريم الأسبوعي بعدد {len(tickers)} سهم...")

for ticker in tickers:
    try:
        # 1. جلب البيانات الأسبوعية (1wk)
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

        # 2. جلب السعر الحي اللحظي بدقة
        live_price = get_realtime_price(ticker)
        hist_last_close = float(close.iloc[-1])
        
        if live_price is None or live_price <= 0:
            live_price = hist_last_close

        hist_prev_close = float(close.iloc[-2]) if len(close) > 1 else hist_last_close
        daily_change_pct = ((live_price - hist_prev_close) / hist_prev_close) * 100

        # 1. EMA 50 & EMA 200
        ema_50 = close.ewm(span=50, adjust=False).mean()
        ema_200 = close.ewm(span=200, adjust=False).mean() if len(close) >= 150 else close.ewm(span=20, adjust=False).mean()

        # 2. RSI الأسبوعي
        rsi = calculate_rsi(close, 14)

        # 3. MACD الأسبوعي
        ema_12 = close.ewm(span=12, adjust=False).mean()
        ema_26 = close.ewm(span=26, adjust=False).mean()
        macd_line = ema_12 - ema_26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        histogram = macd_line - signal_line

        # القيم الأسبوعية الأخيرة
        curr_close = close.iloc[-1]
        c_ema50, c_ema200 = ema_50.iloc[-1], ema_200.iloc[-1]
        c_rsi = rsi.iloc[-1]
        
        if pd.isna(c_rsi):
            continue

        c_macd, p_macd = macd_line.iloc[-1], macd_line.iloc[-2]
        c_signal = signal_line.iloc[-1]
        c_hist, p_hist = histogram.iloc[-1], histogram.iloc[-2]

        low_16 = low_p.iloc[-16:].min()
        high_16 = high_p.iloc[-16:].max()

        # --- حساب درجات المطابقة المرنة (Weekly Matching Score) ---
        score = 0
        matched_conditions = []

        # 1. الاتجاه العام أسبوعياً
        if c_ema50 >= c_ema200 or curr_close >= c_ema50:
            score += 1
            matched_conditions.append("اتجاه صاعد")

        # 2. نطاق RSI المرن (45 إلى 68 أسبوعياً)
        if 45 <= c_rsi <= 68:
            score += 1
            matched_conditions.append(f"RSI {round(float(c_rsi), 1)}")

        # 3. قُرب الدعم الأسبوعي
        near_support = (curr_close - low_16) / low_16 <= 0.12 or (abs(curr_close - c_ema50) / c_ema50 <= 0.04)
        if near_support:
            score += 1
            matched_conditions.append("منطقة دعم")

        # 4. شمعة انعكاسية أسبوعية
        is_reversal = check_reversal_candle(
            open_p.iloc[-1], high_p.iloc[-1], low_p.iloc[-1], close.iloc[-1],
            open_p.iloc[-2], close.iloc[-2]
        )
        if is_reversal:
            score += 1
            matched_conditions.append("شمعة انعكاسية")

        # 5. زخم الماكد الأسبوعي
        if (c_hist > p_hist) or (c_macd > p_macd):
            score += 1
            matched_conditions.append("زخم MACD")

        # إظهار أي سهم محقق 3 شروط أو أكثر
        if score >= 3:
            elliott_wave = estimate_elliott_wave_weekly(close, high_16, low_16)

            results.append({
                "Ticker": ticker,
                "Live_Price": f"{live_price:.4f}",       # عرض السعر الحي اللحظي بدقة
                "Change_%": f"{daily_change_pct:+.2f}%",  # نسبة التغير اليومية
                "Weekly_RSI": round(float(c_rsi), 1),
                "Score": f"{score}/5",
                "Matches": ", ".join(matched_conditions),
                "Elliott_Wave_W": elliott_wave
            })

    except Exception:
        continue

# ترتيب النتائج من الأقوى للأقل
results = sorted(results, key=lambda x: int(x['Score'].split('/')[0]), reverse=True)

# طباعة الجدول النهائي
print("\n" + "=" * 110)
print("     نتائج الفحص المرن على الفريم الأسبوعي للبورصة المصرية بالسعر اللحظي (مرتبة حسب الأقوى)     ")
print("=" * 110)

if results:
    res_df = pd.DataFrame(results)
    print(res_df.to_string(index=False))
else:
    print("لا توجد أسهم تطابق الحد الأدنى من الشروط الحالية.")
print("=" * 110)
