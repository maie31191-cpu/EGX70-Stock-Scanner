# ============================================================
# EGX WEEKLY STOCK SCREENER - AUTO UPDATE VERSION
# ============================================================

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timezone

# ------------------------------------------------------------
# 1) قائمة الأسهم المصرية
# ------------------------------------------------------------

tickers = [
    # البنوك والخدمات المالية
    "COMI.CA", "HRHO.CA", "FWRY.CA", "CCAP.CA", "CIEB.CA", "ADIB.CA",
    "EXPA.CA", "EGBE.CA", "EIDF.CA", "BTFH.CA", "BINV.CA", "ATLC.CA",
    "VALO.CA", "SAIB.CA", "CANA.CA", "BLDY.CA", "CNTY.CA", "AIH.CA",
    "CICH.CA", "GRTE.CA", "EDBM.CA",

    # العقارات والتنمية
    "TMGH.CA", "PHDC.CA", "HELI.CA", "ORAS.CA", "EMFD.CA", "MNHD.CA",
    "ACGC.CA", "EGCH.CA", "AMER.CA", "ODHO.CA", "AREH.CA", "UNIT.CA",
    "PORT.CA", "EGAL.CA", "ROYO.CA", "ARAB.CA", "ZMID.CA", "MENA.CA",
    "TAQA.CA", "ORHD.CA", "DAPH.CA",

    # الكيماويات والأسمدة
    "ABUK.CA", "MFPC.CA", "AMOC.CA", "SKPC.CA", "KIMA.CA", "SVEN.CA",
    "EGAS.CA", "OIFI.CA", "FERT.CA", "ISMA.CA", "ICID.CA", "VERT.CA",
    "ASPC.CA", "SPMD.CA",

    # الأغذية والأدوية والاستهلاك
    "EAST.CA", "JUFO.CA", "ISPH.CA", "MCRO.CA", "EFID.CA", "DOMH.CA",
    "OLFI.CA", "ORWE.CA", "AUTO.CA", "OCDI.CA", "ALCN.CA", "ESRS.CA",
    "MORA.CA", "GOCO.CA", "AJWA.CA", "RAYA.CA", "OBRI.CA", "CLHO.CA",
    "PHAR.CA",

    # الاتصالات والتكنولوجيا والخدمات
    "SWDY.CA", "ETEL.CA", "EEII.CA", "CSAG.CA", "MPRC.CA", "UPSS.CA",
    "EPK.CA", "AIND.CA", "ELWA.CA", "MOIL.CA", "EITC.CA", "KRDI.CA"
]

tickers = sorted(list(set(tickers)))


# ------------------------------------------------------------
# 2) RSI
# ------------------------------------------------------------

def calculate_rsi(series, period=14):

    delta = series.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period
    ).mean()

    avg_loss = loss.ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period
    ).mean()

    rs = avg_gain / avg_loss

    rsi = 100 - (100 / (1 + rs))

    return rsi


# ------------------------------------------------------------
# 3) شمعة انعكاسية
# ------------------------------------------------------------

def check_reversal_candle(
    open_p,
    high_p,
    low_p,
    close_p,
    prev_open,
    prev_close
):

    body = abs(close_p - open_p)

    if body == 0:
        body = 0.000001

    lower_shadow = min(open_p, close_p) - low_p
    upper_shadow = high_p - max(open_p, close_p)

    # Hammer
    is_hammer = (
        lower_shadow >= 1.5 * body
        and upper_shadow <= body
    )

    # Bullish engulfing
    is_engulfing = (
        prev_close < prev_open
        and close_p > open_p
        and close_p >= prev_open
        and open_p <= prev_close
    )

    # Green candle with lower wick
    is_strong_green = (
        close_p > open_p
        and lower_shadow >= 0.4 * body
    )

    return (
        is_hammer
        or is_engulfing
        or is_strong_green
    )


# ------------------------------------------------------------
# 4) Elliott تقديري
# ------------------------------------------------------------

def estimate_elliott_wave_weekly(
    close_prices,
    high_prices,
    low_prices
):

    if len(close_prices) < 20:
        return "بيانات غير كافية"

    recent_high = high_prices.iloc[-16:].max()
    recent_low = low_prices.iloc[-16:].min()

    if recent_high == recent_low:
        return "غير محدد"

    curr = close_prices.iloc[-1]

    retrace_ratio = (
        (curr - recent_low)
        / (recent_high - recent_low)
    )

    if retrace_ratio < 0.15:
        return "قاع / بداية تجميع"

    elif 0.15 <= retrace_ratio <= 0.45:
        return "تأهب للموجة 3"

    elif 0.46 <= retrace_ratio <= 0.65:
        return "تأهب للموجة 5"

    elif retrace_ratio > 0.65:
        return "اتجاه دافع صاعد"

    return "غير محدد"


# ------------------------------------------------------------
# 5) استخراج الأعمدة
# ------------------------------------------------------------

def clean_downloaded_data(df, ticker):

    if df.empty:
        return None

    # التعامل مع MultiIndex من yfinance
    if isinstance(df.columns, pd.MultiIndex):

        try:
            close = df["Close"][ticker]
            open_p = df["Open"][ticker]
            high_p = df["High"][ticker]
            low_p = df["Low"][ticker]
            volume = df["Volume"][ticker]

        except Exception:

            close = df["Close"].iloc[:, 0]
            open_p = df["Open"].iloc[:, 0]
            high_p = df["High"].iloc[:, 0]
            low_p = df["Low"].iloc[:, 0]
            volume = df["Volume"].iloc[:, 0]

    else:

        close = df["Close"]
        open_p = df["Open"]
        high_p = df["High"]
        low_p = df["Low"]
        volume = df["Volume"]

    result = pd.DataFrame({
        "Open": open_p,
        "High": high_p,
        "Low": low_p,
        "Close": close,
        "Volume": volume
    })

    result = result.dropna()

    return result


# ------------------------------------------------------------
# 6) وقت تشغيل الفحص
# ------------------------------------------------------------

run_time = datetime.now()

print("\n" + "=" * 100)
print("        EGX AUTO UPDATE WEEKLY STOCK SCREENER")
print("=" * 100)

print(f"وقت تشغيل الفحص: {run_time.strftime('%Y-%m-%d %H:%M:%S')}")

print(f"عدد الأسهم: {len(tickers)}")

print("\nجاري تحميل أحدث البيانات المتاحة...")
print("من فضلك انتظر...\n")


# ------------------------------------------------------------
# 7) النتائج
# ------------------------------------------------------------

results = []


# ------------------------------------------------------------
# 8) فحص كل سهم
# ------------------------------------------------------------

for ticker in tickers:

    try:

        # ====================================================
        # أولاً: البيانات الأسبوعية
        # ====================================================

        weekly_raw = yf.download(
            ticker,
            period="5y",
            interval="1wk",
            auto_adjust=False,
            progress=False,
            threads=False
        )

        weekly = clean_downloaded_data(
            weekly_raw,
            ticker
        )

        if weekly is None or len(weekly) < 60:
            continue

        weekly = weekly.sort_index()

        # ----------------------------------------------------
        # حذف الأسبوع الحالي غير المكتمل
        # ----------------------------------------------------

        today = pd.Timestamp.now()

        last_date = weekly.index[-1]

        # إذا كانت آخر شمعة ما زالت أسبوعًا جاريًا
        # نستخدم آخر أسبوع مكتمل للتحليل
        if last_date >= today - pd.Timedelta(days=6):

            completed_weekly = weekly.iloc[:-1].copy()

        else:

            completed_weekly = weekly.copy()

        if len(completed_weekly) < 50:
            continue

        # ====================================================
        # السعر الأحدث المتاح
        # ====================================================

        daily_raw = yf.download(
            ticker,
            period="10d",
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=False
        )

        daily = clean_downloaded_data(
            daily_raw,
            ticker
        )

        if daily is None or daily.empty:
            continue

        daily = daily.sort_index()

        latest_price = float(
            daily["Close"].iloc[-1]
        )

        latest_price_date = daily.index[-1]

        # ====================================================
        # البيانات الأسبوعية للتحليل
        # ====================================================

        close = completed_weekly["Close"]
        open_p = completed_weekly["Open"]
        high_p = completed_weekly["High"]
        low_p = completed_weekly["Low"]

        # ====================================================
        # EMA 50
        # ====================================================

        ema_50 = close.ewm(
            span=50,
            adjust=False
        ).mean()

        # ====================================================
        # EMA 200
        # ====================================================

        ema_200 = close.ewm(
            span=200,
            adjust=False
        ).mean()

        # ====================================================
        # RSI أسبوعي
        # ====================================================

        rsi = calculate_rsi(
            close,
            14
        )

        # ====================================================
        # MACD أسبوعي
        # ====================================================

        ema_12 = close.ewm(
            span=12,
            adjust=False
        ).mean()

        ema_26 = close.ewm(
            span=26,
            adjust=False
        ).mean()

        macd_line = ema_12 - ema_26

        signal_line = macd_line.ewm(
            span=9,
            adjust=False
        ).mean()

        histogram = (
            macd_line
            - signal_line
        )

        # ====================================================
        # القيم الأخيرة
        # ====================================================

        curr_close = float(close.iloc[-1])

        c_ema50 = float(
            ema_50.iloc[-1]
        )

        c_ema200 = float(
            ema_200.iloc[-1]
        )

        c_rsi = float(
            rsi.iloc[-1]
        )

        c_macd = float(
            macd_line.iloc[-1]
        )

        p_macd = float(
            macd_line.iloc[-2]
        )

        c_signal = float(
            signal_line.iloc[-1]
        )

        p_signal = float(
            signal_line.iloc[-2]
        )

        c_hist = float(
            histogram.iloc[-1]
        )

        p_hist = float(
            histogram.iloc[-2]
        )

        # ====================================================
        # الدعم والمقاومة
        # ====================================================

        low_16 = float(
            low_p.iloc[-16:].min()
        )

        high_16 = float(
            high_p.iloc[-16:].max()
        )

        support_distance = (
            (curr_close - low_16)
            / low_16
        )

        ema50_distance = abs(
            curr_close - c_ema50
        ) / c_ema50

        # ====================================================
        # SCORE
        # ====================================================

        score = 0

        matched_conditions = []

        # ----------------------------------------------------
        # 1 - الاتجاه
        # ----------------------------------------------------

        if (
            curr_close > c_ema50
            and c_ema50 > c_ema200
        ):

            score += 1

            matched_conditions.append(
                "اتجاه صاعد قوي"
            )

        elif curr_close > c_ema50:

            score += 1

            matched_conditions.append(
                "اتجاه صاعد"
            )

        # ----------------------------------------------------
        # 2 - RSI
        # ----------------------------------------------------

        if 45 <= c_rsi <= 68:

            score += 1

            matched_conditions.append(
                f"RSI {c_rsi:.1f}"
            )

        # ----------------------------------------------------
        # 3 - الدعم
        # ----------------------------------------------------

        near_support = (
            support_distance <= 0.12
            or ema50_distance <= 0.04
        )

        if near_support:

            score += 1

            matched_conditions.append(
                "منطقة دعم"
            )

        # ----------------------------------------------------
        # 4 - شمعة انعكاسية
        # ----------------------------------------------------

        is_reversal = check_reversal_candle(
            open_p.iloc[-1],
            high_p.iloc[-1],
            low_p.iloc[-1],
            close.iloc[-1],
            open_p.iloc[-2],
            close.iloc[-2]
        )

        if is_reversal:

            score += 1

            matched_conditions.append(
                "شمعة انعكاسية"
            )

        # ----------------------------------------------------
        # 5 - MACD
        # ----------------------------------------------------

        macd_positive_momentum = (
            c_hist > p_hist
            or c_macd > p_macd
            or (
                c_macd > c_signal
                and c_hist > 0
            )
        )

        if macd_positive_momentum:

            score += 1

            matched_conditions.append(
                "زخم MACD"
            )

        # ====================================================
        # Elliott
        # ====================================================

        elliott_wave = estimate_elliott_wave_weekly(
            close,
            high_p,
            low_p
        )

        # ====================================================
        # لا نعرض إلا 3/5 أو أكثر
        # ====================================================

        if score >= 3:

            results.append({

                "Ticker":
                    ticker,

                "Latest_Price":
                    round(
                        latest_price,
                        2
                    ),

                "Price_Date":
                    str(
                        latest_price_date.date()
                    ),

                "Weekly_Close":
                    round(
                        curr_close,
                        2
                    ),

                "Weekly_Data_Date":
                    str(
                        completed_weekly.index[-1].date()
                    ),

                "Weekly_RSI":
                    round(
                        c_rsi,
                        1
                    ),

                "Score":
                    f"{score}/5",

                "Matches":
                    ", ".join(
                        matched_conditions
                    ),

                "Elliott_Wave":
                    elliott_wave

            )

    except Exception as e:

        # نتجاهل السهم الذي حدث فيه خطأ
        # ونكمل بقية الأسهم

        continue


# ============================================================
# 9) ترتيب النتائج
# ============================================================

def score_number(x):

    try:
        return int(
            x["Score"].split("/")[0]
        )

    except:
        return 0


results = sorted(
    results,
    key=lambda x: (
        score_number(x),
        x["Weekly_RSI"]
        if not pd.isna(x["Weekly_RSI"])
        else -1
    ),
    reverse=True
)


# ============================================================
# 10) عرض النتائج
# ============================================================

print("\n" + "=" * 120)

print(
    "             نتائج الفحص الأسبوعي - AUTO UPDATE"
)

print("=" * 120)


if results:

    res_df = pd.DataFrame(results)

    print(
        res_df.to_string(
            index=False
        )
    )

else:

    print(
        "لا توجد أسهم تحقق 3 شروط أو أكثر."
    )


print("=" * 120)

print(
    "\nملاحظات:"
)

print(
    "1- Latest_Price = أحدث سعر يومي استطاع المصدر توفيره."
)

print(
    "2- Weekly_Close = آخر إغلاق أسبوعي مكتمل مستخدم في التحليل."
)

print(
    "3- Price_Date = تاريخ أحدث سعر."
)

print(
    "4- Weekly_Data_Date = تاريخ الأسبوع المستخدم في التحليل."
)

print(
    "5- Elliott Wave هنا تقدير فني آلي وليست تأكيدًا لموجة إليوت."
)

print(
    "6- عند تشغيل الكود مرة أخرى سيتم تحميل البيانات من جديد."
)

print("=" * 120)