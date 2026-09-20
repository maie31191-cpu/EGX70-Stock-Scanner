import requests
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# =========================================================
# EGX AUTO UPDATE STOCK SCREENER
# EGID FEED + YAHOO HISTORICAL DATA
# =========================================================

EGID_BASE = "https://ticker.egidegypt.com"

# =========================================================
# الأسهم
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

tickers = sorted(set(tickers))


# =========================================================
# RSI
# =========================================================

def calculate_rsi(series, period=14):

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

    engulfing = (
        pc < po
        and c > o
        and c >= po
        and o <= pc
    )

    strong_green = (
        c > o
        and lower_shadow >= body * 0.4
    )

    return hammer or engulfing or strong_green


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
# محاولة استخراج السعر من أي شكل JSON
# =========================================================

def find_price_in_json(obj):

    price_keys = [
        "lastPrice",
        "LastPrice",
        "last",
        "Last",
        "price",
        "Price",
        "close",
        "Close",
        "lastTradePrice",
        "LastTradePrice"
    ]

    if isinstance(obj, dict):

        for key in price_keys:

            if key in obj:

                value = obj[key]

                try:
                    value = float(value)

                    if value > 0:
                        return value

                except:
                    pass

        for value in obj.values():

            result = find_price_in_json(value)

            if result is not None:
                return result

    elif isinstance(obj, list):

        for item in obj:

            result = find_price_in_json(item)

            if result is not None:
                return result

    return None


# =========================================================
# السعر الحالي من EGID FEED
# =========================================================

def get_live_price_from_egid(ticker):

    # نحذف .CA لأن بعض APIs تستخدم رمز EGX فقط
    symbol = ticker.replace(".CA", "")

    urls = [

        f"{EGID_BASE}/api/Feed/GetMarketWatchForSymbol?symbol={symbol}",

        f"{EGID_BASE}/api/Feed/GetTodayMarketWatch",

        f"{EGID_BASE}/api/Feed/GetAllMarketWatch"

    ]

    for url in urls:

        try:

            response = requests.get(
                url,
                timeout=10
            )

            if response.status_code != 200:
                continue

            data = response.json()

            # البحث المباشر داخل البيانات
            if "GetMarketWatchForSymbol" in url:

                price = find_price_in_json(data)

                if price is not None:
                    return price, "EGID Feed"

            else:

                # في البيانات العامة نبحث عن رمز السهم أولاً
                def search_symbol(obj):

                    if isinstance(obj, dict):

                        text = str(obj).upper()

                        if symbol.upper() in text:

                            price = find_price_in_json(obj)

                            if price is not None:
                                return price

                        for v in obj.values():

                            result = search_symbol(v)

                            if result is not None:
                                return result

                    elif isinstance(obj, list):

                        for item in obj:

                            result = search_symbol(item)

                            if result is not None:
                                return result

                    return None

                price = search_symbol(data)

                if price is not None:
                    return price, "EGID Feed"

        except Exception:
            continue

    return None, None


# =========================================================
# البداية
# =========================================================

print("=" * 110)

print(
    "EGX AUTO UPDATE STOCK SCREENER"
)

print("=" * 110)

print(
    "وقت التشغيل:",
    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
)

print(
    "جاري جلب أحدث سعر متاح..."
)

print()


results = []

errors = []


# =========================================================
# الفحص
# =========================================================

for number, ticker in enumerate(tickers, 1):

    print(
        f"[{number}/{len(tickers)}] {ticker}",
        end=" ... "
    )

    try:

        # =====================================================
        # السعر الحالي من EGID
        # =====================================================

        live_price, source = get_live_price_from_egid(
            ticker
        )


        # =====================================================
        # التاريخ الأسبوعي من Yahoo
        # =====================================================

        data = yf.download(
            ticker,
            period="5y",
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=False
        )

        if data is None or data.empty:

            print("لا توجد بيانات تاريخية")

            errors.append(ticker)

            continue


        # إصلاح MultiIndex
        if isinstance(
            data.columns,
            pd.MultiIndex
        ):

            data.columns = (
                data.columns
                .get_level_values(0)
            )


        required = [
            "Open",
            "High",
            "Low",
            "Close"
        ]


        if not all(
            x in data.columns
            for x in required
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


        # =====================================================
        # لو EGID لم يرجع السعر
        # نستخدم آخر سعر متاح من Yahoo كاحتياطي
        # =====================================================

        if live_price is None:

            live_price = float(
                data["Close"].iloc[-1]
            )

            source = "Yahoo - احتياطي"


        latest_date = data.index[-1]


        # =====================================================
        # تحويل إلى أسبوعي
        # =====================================================

        weekly = data.resample(
            "W-FRI"
        ).agg({

            "Open": "first",
            "High": "max",
            "Low": "min",
            "Close": "last"

        }).dropna()


        if len(weekly) < 50:

            print("أسابيع غير كافية")

            continue


        # =====================================================
        # استخدام آخر أسبوع مكتمل
        # =====================================================

        today = pd.Timestamp.today()

        last_week = weekly.index[-1]

        if last_week > today:

            weekly = weekly.iloc[:-1]


        if len(weekly) < 50:
            continue


        # =====================================================
        # المؤشرات
        # =====================================================

        close = weekly["Close"]

        open_p = weekly["Open"]

        high = weekly["High"]

        low = weekly["Low"]


        ema50 = close.ewm(
            span=50,
            adjust=False
        ).mean()


        ema200 = close.ewm(
            span=200,
            adjust=False
        ).mean()


        rsi = calculate_rsi(
            close,
            14
        )


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


        histogram = (
            macd - signal
        )


        # =====================================================
        # القيم الحالية
        # =====================================================

        c = float(
            close.iloc[-1]
        )

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


        # =====================================================
        # الدعم
        # =====================================================

        low16 = float(
            low.iloc[-16:].min()
        )


        distance_support = (
            (c - low16)
            / low16
        )


        distance_ema = (
            abs(c - e50)
            / e50
        )


        # =====================================================
        # Score
        # =====================================================

        score = 0

        conditions = []


        # الاتجاه
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


        # RSI
        if 45 <= r <= 68:

            score += 1

            conditions.append(
                f"RSI {r:.1f}"
            )


        # الدعم
        if (
            distance_support <= 0.12
            or distance_ema <= 0.04
        ):

            score += 1

            conditions.append(
                "منطقة دعم"
            )


        # شمعة انعكاسية
        if reversal_candle(

            open_p.iloc[-1],
            high.iloc[-1],
            low.iloc[-1],
            close.iloc[-1],

            open_p.iloc[-2],
            close.iloc[-2]

        ):

            score += 1

            conditions.append(
                "شمعة انعكاسية"
            )


        # MACD
        if (
            hist_now > hist_prev
            or macd_now > macd_prev
        ):

            score += 1

            conditions.append(
                "زخم MACD"
            )


        # Elliott
        wave = elliott_signal(
            close,
            high,
            low
        )


        # =====================================================
        # حفظ الأسهم التي حققت 3/5 أو أكثر
        # =====================================================

        if score >= 3:

            results.append({

                "Ticker":
                    ticker,

                "Today_Price":
                    round(
                        live_price,
                        2
                    ),

                "Price_Source":
                    source,

                "Price_Date":
                    str(
                        latest_date.date()
                    ),

                "Weekly_Close":
                    round(
                        c,
                        2
                    ),

                "Weekly_RSI":
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
            f"تم | السعر = {live_price:.2f} | Score = {score}/5"
        )


    except Exception as e:

        print(
            "خطأ"
        )

        errors.append(
            f"{ticker}: {e}"
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
# النتائج
# =========================================================

print("\n")

print("=" * 120)

print(
    "                 الأسهم المطابقة"
)

print("=" * 120)


if results:

    result_df = pd.DataFrame(
        results
    )

    print(
        result_df.to_string(
            index=False
        )
    )

else:

    print(
        "لا توجد أسهم حققت 3 شروط أو أكثر."
    )


# =========================================================
# أخطاء التحميل
# =========================================================

print("\n")

print("=" * 120)

print(
    "                 الأسهم التي لم يتم تحميلها"
)

print("=" * 120)


if errors:

    for error in errors:
        print(error)

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
    "شغلي Run مرة أخرى للحصول على أحدث تحديث متاح."
)

print(
    "Today_Price = السعر الحالي الذي تم الحصول عليه."
)

print(
    "Weekly_RSI و Score = التحليل الأسبوعي."
)

print(
    "Elliott = إشارة تقديرية وليست تأكيدًا لموجة إليوت."
)

print("=" * 120)