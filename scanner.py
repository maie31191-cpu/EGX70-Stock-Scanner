import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# =========================================================
# EGX WEEKLY SCREENER - AUTO UPDATE
# =========================================================

tickers = [
    "COMI.CA", "HRHO.CA", "FWRY.CA", "CCAP.CA", "CIEB.CA",
    "ADIB.CA", "EXPA.CA", "EGBE.CA", "EIDF.CA", "BTFH.CA",
    "BINV.CA", "ATLC.CA", "VALO.CA", "SAIB.CA", "CANA.CA",
    "BLDY.CA", "CNTY.CA", "AIH.CA", "CICH.CA", "GRTE.CA",

    "TMGH.CA", "PHDC.CA", "HELI.CA", "ORAS.CA", "EMFD.CA",
    "MNHD.CA", "ACGC.CA", "EGCH.CA", "AMER.CA", "ODHO.CA",
    "AREH.CA", "UNIT.CA", "PORT.CA", "EGAL.CA", "ROYO.CA",
    "ARAB.CA", "ZMID.CA", "MENA.CA", "TAQA.CA", "ORHD.CA",

    "ABUK.CA", "MFPC.CA", "AMOC.CA", "SKPC.CA", "KIMA.CA",
    "SVEN.CA", "EGAS.CA", "OIFI.CA", "FERT.CA", "ISMA.CA",
    "ICID.CA", "VERT.CA", "ASPC.CA", "SPMD.CA",

    "EAST.CA", "JUFO.CA", "ISPH.CA", "MCRO.CA", "EFID.CA",
    "DOMH.CA", "OLFI.CA", "ORWE.CA", "AUTO.CA", "OCDI.CA",
    "ALCN.CA", "ESRS.CA", "MORA.CA", "GOCO.CA", "AJWA.CA",
    "RAYA.CA", "OBRI.CA", "CLHO.CA", "PHAR.CA",

    "SWDY.CA", "ETEL.CA", "EEII.CA", "CSAG.CA", "MPRC.CA",
    "UPSS.CA", "EPK.CA", "AIND.CA", "ELWA.CA", "MOIL.CA",
    "EITC.CA", "KRDI.CA"
]


# =========================================================
# RSI
# =========================================================

def RSI(series, period=14):

    delta = series.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(
        alpha=1 / period,
        adjust=False
    ).mean()

    avg_loss = loss.ewm(
        alpha=1 / period,
        adjust=False
    ).mean()

    rs = avg_gain / avg_loss

    return 100 - (100 / (1 + rs))


# =========================================================
# شمعة انعكاسية
# =========================================================

def reversal_candle(o, h, l, c, po, pc):

    body = abs(c - o)

    if body == 0:
        body = 0.000001

    lower_shadow = min(o, c) - l
    upper_shadow = h - max(o, c)

    hammer = (
        lower_shadow >= body * 1.5
        and upper_shadow <= body
    )

    bullish_engulfing = (
        pc < po
        and c > o
        and c >= po
        and o <= pc
    )

    strong_green = (
        c > o
        and lower_shadow >= body * 0.4
    )

    return (
        hammer
        or bullish_engulfing
        or strong_green
    )


# =========================================================
# Elliott تقديري
# =========================================================

def elliott_signal(close, high, low):

    if len(close) < 20:
        return "غير محدد"

    low16 = low.iloc[-16:].min()
    high16 = high.iloc[-16:].max()

    if high16 == low16:
        return "غير محدد"

    current = close.iloc[-1]

    ratio = (
        current - low16
    ) / (
        high16 - low16
    )

    if ratio < 0.15:
        return "قاع تجميعي"

    elif ratio <= 0.45:
        return "تأهب للموجة 3"

    elif ratio <= 0.65:
        return "تأهب للموجة 5"

    else:
        return "موجة دافعة صاعدة"


# =========================================================
# بداية الفحص
# =========================================================

print("=" * 100)
print("EGX WEEKLY STOCK SCREENER")
print("=" * 100)

print(
    "وقت التشغيل:",
    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
)

print(
    "عدد الأسهم:",
    len(tickers)
)

print("\nجاري تحميل البيانات...\n")


results = []

errors = []


# =========================================================
# فحص الأسهم
# =========================================================

for i, ticker in enumerate(tickers, 1):

    print(
        f"[{i}/{len(tickers)}] {ticker}",
        end=" ... "
    )

    try:

        # -----------------------------------------------
        # تحميل البيانات اليومية
        # -----------------------------------------------

        data = yf.download(
            ticker,
            period="5y",
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=False
        )

        if data is None or data.empty:

            print("لا توجد بيانات")

            errors.append(ticker)

            continue


        # -----------------------------------------------
        # إصلاح MultiIndex
        # -----------------------------------------------

        if isinstance(data.columns, pd.MultiIndex):

            data.columns = data.columns.get_level_values(0)


        # -----------------------------------------------
        # التأكد من الأعمدة
        # -----------------------------------------------

        required = [
            "Open",
            "High",
            "Low",
            "Close"
        ]

        if not all(
            col in data.columns
            for col in required
        ):

            print("أعمدة ناقصة")

            errors.append(ticker)

            continue


        data = data[
            required
        ].dropna()


        if len(data) < 100:

            print("بيانات غير كافية")

            errors.append(ticker)

            continue


        # =================================================
        # أحدث سعر
        # =================================================

        latest_price = float(
            data["Close"].iloc[-1]
        )

        latest_date = data.index[-1]


        # =================================================
        # تحويل البيانات اليومية إلى أسبوعية
        # =================================================

        weekly = data.resample(
            "W-FRI"
        ).agg({

            "Open": "first",
            "High": "max",
            "Low": "min",
            "Close": "last"

        }).dropna()


        # =================================================
        # حذف الأسبوع الجاري
        # =================================================

        today = pd.Timestamp.today()

        current_week_friday = (
            today
            + pd.offsets.Week(
                weekday=4
            )
        )

        if (
            len(weekly) > 1
            and weekly.index[-1] > today
        ):

            weekly = weekly.iloc[:-1]


        if len(weekly) < 50:

            print("أسابيع غير كافية")

            errors.append(ticker)

            continue


        # =================================================
        # الأسعار الأسبوعية
        # =================================================

        close = weekly["Close"]
        open_p = weekly["Open"]
        high = weekly["High"]
        low = weekly["Low"]


        # =================================================
        # EMA
        # =================================================

        ema50 = close.ewm(
            span=50,
            adjust=False
        ).mean()

        ema200 = close.ewm(
            span=200,
            adjust=False
        ).mean()


        # =================================================
        # RSI
        # =================================================

        rsi = RSI(
            close,
            14
        )


        # =================================================
        # MACD
        # =================================================

        ema12 = close.ewm(
            span=12,
            adjust=False
        ).mean()

        ema26 = close.ewm(
            span=26,
            adjust=False
        ).mean()

        macd = ema12 - ema26

        signal = macd.ewm(
            span=9,
            adjust=False
        ).mean()

        histogram = macd - signal


        # =================================================
        # آخر أسبوع
        # =================================================

        c = float(close.iloc[-1])

        e50 = float(
            ema50.iloc[-1]
        )

        e200 = float(
            ema200.iloc[-1]
        )

        r = float(
            rsi.iloc[-1]
        )

        macd_now = float(
            macd.iloc[-1]
        )

        macd_prev = float(
            macd.iloc[-2]
        )

        hist_now = float(
            histogram.iloc[-1]
        )

        hist_prev = float(
            histogram.iloc[-2]
        )


        # =================================================
        # آخر 16 أسبوع
        # =================================================

        low16 = float(
            low.iloc[-16:].min()
        )

        high16 = float(
            high.iloc[-16:].max()
        )


        # =================================================
        # SCORE
        # =================================================

        score = 0

        conditions = []


        # -------------------------------------------------
        # 1 - الاتجاه
        # -------------------------------------------------

        if c > e50:

            score += 1

            if e50 > e200:

                conditions.append(
                    "اتجاه صاعد قوي"
                )

            else:

                conditions.append(
                    "فوق EMA50"
                )


        # -------------------------------------------------
        # 2 - RSI
        # -------------------------------------------------

        if 45 <= r <= 68:

            score += 1

            conditions.append(
                f"RSI {r:.1f}"
            )


        # -------------------------------------------------
        # 3 - الدعم
        # -------------------------------------------------

        distance_support = (
            (c - low16)
            / low16
        )

        distance_ema = abs(
            c - e50
        ) / e50


        if (
            distance_support <= 0.12
            or distance_ema <= 0.04
        ):

            score += 1

            conditions.append(
                "منطقة دعم"
            )


        # -------------------------------------------------
        # 4 - شمعة انعكاسية
        # -------------------------------------------------

        rev = reversal_candle(

            open_p.iloc[-1],
            high.iloc[-1],
            low.iloc[-1],
            close.iloc[-1],

            open_p.iloc[-2],
            close.iloc[-2]

        )


        if rev:

            score += 1

            conditions.append(
                "شمعة انعكاسية"
            )


        # -------------------------------------------------
        # 5 - MACD
        # -------------------------------------------------

        if (
            hist_now > hist_prev
            or macd_now > macd_prev
        ):

            score += 1

            conditions.append(
                "زخم MACD"
            )


        # =================================================
        # Elliott
        # =================================================

        wave = elliott_signal(
            close,
            high,
            low
        )


        # =================================================
        # حفظ النتيجة
        # =================================================

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
                        latest_date.date()
                    ),

                "Weekly_Close":
                    round(
                        c,
                        2
                    ),

                "Weekly_Date":
                    str(
                        weekly.index[-1].date()
                    ),

                "RSI":
                    round(
                        r,
                        1
                    ),

                "Score":
                    f"{score}/5",

                "Conditions":
                    "، ".join(
                        conditions
                    ),

                "Elliott":
                    wave

            })


        print(
            f"تم | Score = {score}/5"
        )


    except Exception as e:

        print(
            "خطأ"
        )

        errors.append(
            f"{ticker} -> {str(e)}"
        )


# =========================================================
# ترتيب النتائج
# =========================================================

results = sorted(

    results,

    key=lambda x:
        int(
            x["Score"].split("/")[0]
        ),

    reverse=True

)


# =========================================================
# عرض النتائج
# =========================================================

print("\n\n")
print("=" * 120)
print("                 النتائج النهائية")
print("=" * 120)


if len(results) > 0:

    df_results = pd.DataFrame(
        results
    )

    print(
        df_results.to_string(
            index=False
        )
    )

else:

    print(
        "لم يتم العثور على أسهم تحقق 3 شروط أو أكثر."
    )


# =========================================================
# الأسهم التي حدث بها خطأ
# =========================================================

print("\n")
print("=" * 120)
print("الأسهم التي لم يتم تحميل بياناتها")
print("=" * 120)


if errors:

    for item in errors:

        print(
            item
        )

else:

    print(
        "لا توجد أخطاء."
    )


# =========================================================
# النهاية
# =========================================================

print("\n")
print("=" * 120)

print(
    "انتهى الفحص."
)

print(
    "عند تشغيل الكود مرة أخرى سيتم تحميل البيانات من جديد."
)

print("=" * 120)