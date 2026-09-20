import yfinance as yf
import pandas as pd
import numpy as np

# =========================================================
# قائمة أسهم البورصة المصرية
# =========================================================
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

tickers = sorted(list(set(tickers)))

# =========================================================
# 1. الشروط الفنية الأصلية (نفس المعادلات بالكامل)
# =========================================================
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
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

def estimate_elliott_wave_weekly(curr_price, high_16, low_16):
    if high_16 == low_16 or pd.isna(high_16) or pd.isna(low_16):
        return "غير محدد"
    
    retrace_ratio = (curr_price - low_16) / (high_16 - low_16)
    
    if 0.15 <= retrace_ratio <= 0.45:
        return "الموجة 2 (تأهب للـ 3 الأسبوعية)"
    elif 0.46 <= retrace_ratio <= 0.65:
        return "الموجة 4 (تأهب للـ 5 الأسبوعية)"
    elif retrace_ratio > 0.65:
        return "موجة دافعة صاعدة أسبوعياً"
    else:
        return "قاع تجميعي أسبوعي"

# =========================================================
# 2. جلب البيانات دفعة واحدة لعدم الحظر ولضمان السرعة
# =========================================================
print(f"جاري جلب بيانات {len(tickers)} سهم في البورصة المصرية دفعة واحدة...\n")

# جلب البيانات لجميع الأسهم دفعة واحدة
data_all = yf.download(tickers, period="2y", interval="1d", group_by='ticker', auto_adjust=False, progress=False)

results = []

for ticker in tickers:
    try:
        if ticker in data_all.columns.levels[0]:
            df_daily = data_all[ticker][['Open', 'High', 'Low', 'Close']].dropna()
        else:
            continue

        if df_daily.empty or len(df_daily) < 100:
            continue

        # السعر اللحظي المباشر لآخر تنفيذ متاح
        live_price = float(df_daily['Close'].iloc[-1])
        prev_close = float(df_daily['Close'].iloc[-2]) if len(df_daily) > 1 else live_price
        daily_change_pct = ((live_price - prev_close) / prev_close) * 100

        # التحويل للفريم الأسبوعي الدقيق
        weekly = df_daily.resample('W-FRI').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last'
        }).dropna()

        if len(weekly) < 30:
            continue

        close_w = weekly['Close']
        open_w = weekly['Open']
        high_w = weekly['High']
        low_w = weekly['Low']

        # المؤشرات الفنية الأسبوعية
        ema_50 = close_w.ewm(span=50, adjust=False).mean()
        ema_200 = close_w.ewm(span=200, adjust=False).mean() if len(close_w) >= 150 else close_w.ewm(span=20, adjust=False).mean()
        rsi_w = calculate_rsi(close_w, 14)

        ema_12 = close_w.ewm(span=12, adjust=False).mean()
        ema_26 = close_w.ewm(span=26, adjust=False).mean()
        macd_line = ema_12 - ema_26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        histogram = macd_line - signal_line

        curr_close = float(close_w.iloc[-1])
        c_ema50 = float(ema_50.iloc[-1])
        c_ema200 = float(ema_200.iloc[-1])
        c_rsi = float(rsi_w.iloc[-1])

        if np.isnan(c_rsi):
            continue

        c_macd, p_macd = float(macd_line.iloc[-1]), float(macd_line.iloc[-2])
        c_hist, p_hist = float(histogram.iloc[-1]), float(histogram.iloc[-2])

        low_16 = float(low_w.iloc[-16:].min())
        high_16 = float(high_w.iloc[-16:].max())

        # حساب درجات الشروط الخمسة الأصلية
        score = 0
        matched_conditions = []

        # الشرط 1: اتجاه صاعد
        if curr_close >= c_ema50 or c_ema50 >= c_ema200:
            score += 1
            matched_conditions.append("اتجاه صاعد")

        # الشرط 2: RSI أسبوعي (45 إلى 68)
        if 45 <= c_rsi <= 68:
            score += 1
            matched_conditions.append(f"RSI {round(c_rsi, 1)}")

        # الشرط 3: قرب منطقة الدعم
        near_support = (curr_close - low_16) / low_16 <= 0.12 or (abs(curr_close - c_ema50) / c_ema50 <= 0.04)
        if near_support:
            score += 1
            matched_conditions.append("منطقة دعم")

        # الشرط 4: شمعة للانعكاس
        is_reversal = check_reversal_candle(
            open_w.iloc[-1], high_w.iloc[-1], low_w.iloc[-1], close_w.iloc[-1],
            open_w.iloc[-2], close_w.iloc[-2]
        )
        if is_reversal:
            score += 1
            matched_conditions.append("شمعة للانعكاس")

        # الشرط 5: زخم MACD
        if (c_hist > p_hist) or (c_macd > p_macd):
            score += 1
            matched_conditions.append("زخم MACD")

        # تصفية الأسهم التي تطابق 3 شروط أو أكثر
        if score >= 3:
            elliott_wave = estimate_elliott_wave_weekly(curr_close, high_16, low_16)

            results.append({
                "Ticker": ticker,
                "Live_Price": f"{live_price:.4f}",
                "Change_%": f"{daily_change_pct:+.2f}%",
                "Weekly_RSI": round(c_rsi, 1),
                "Score": f"{score}/5",
                "Matches": ", ".join(matched_conditions),
                "Elliott_Wave_W": elliott_wave
            })

    except Exception:
        continue

# =========================================================
# 3. عرض النتائج
# =========================================================
results = sorted(results, key=lambda x: int(x['Score'].split('/')[0]), reverse=True)

print("=" * 115)
print("     نتائج الفحص الأسبوعي للبورصة المصرية بالسعر اللحظي (مرتبة حسب الأقوى)     ")
print("=" * 115)

if results:
    res_df = pd.DataFrame(results)
    print(res_df.to_string(index=False))
else:
    print("لا توجد أسهم تطابق 3 شروط أو أكثر حالياً.")

print("=" * 115)
