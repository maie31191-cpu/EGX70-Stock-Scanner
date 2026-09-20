import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

# قائمة أسهم البورصة المصرية الرئيسية
EGX_TICKERS = [
    "COMI.CA", "FWRY.CA", "EAST.CA", "EKHO.CA", "ABUK.CA", "MFPC.CA", "HRHO.CA",
    "SWDY.CA", "ETEL.CA", "TMGH.CA", "ORAS.CA", "AMOC.CA", "SKPC.CA", "CIRA.CA",
    "ISPH.CA", "CICH.CA", "ORWE.CA", "AUTO.CA", "PHDC.CA", "HELI.CA", "MNHD.CA",
    "OCDI.CA", "ESRS.CA", "EGCH.CA", "JUFO.CA", "DOMT.CA", "BINV.CA", "ARCC.CA",
    "ORHD.CA", "BTFH.CA", "EXPA.CA", "MCRO.CA"
]

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_macd(series, fast=12, slow=26, signal=9):
    exp1 = series.ewm(span=fast, adjust=False).mean()
    exp2 = series.ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    histogram = macd - signal_line
    return macd, signal_line, histogram

def analyze_stock(ticker):
    try:
        # جلب البيانات التاريخية لآخر 6 أشهر
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if df.empty or len(df) < 50:
            return None

        # معالجة الأعمدة المتداخلة
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        close = df['Close']
        high = df['High']
        low = df['Low']
        open_p = df['Open']

        # حساب المؤشرات الفنية
        df['RSI'] = calculate_rsi(close)
        macd, signal_line, hist = calculate_macd(close)
        df['MACD'] = macd
        df['MACD_Signal'] = signal_line
        df['MACD_Hist'] = hist
        df['EMA_20'] = close.ewm(span=20, adjust=False).mean()
        df['EMA_50'] = close.ewm(span=50, adjust=False).mean()

        last_idx = -1
        last_close = close.iloc[last_idx]
        prev_close = close.iloc[last_idx - 1]
        
        # نسبة التغير اليومية
        daily_change_pct = ((last_close - prev_close) / prev_close) * 100

        last_rsi = df['RSI'].iloc[last_idx]
        last_macd_hist = df['MACD_Hist'].iloc[last_idx]
        prev_macd_hist = df['MACD_Hist'].iloc[last_idx - 1]
        last_ema20 = df['EMA_20'].iloc[last_idx]
        last_ema50 = df['EMA_50'].iloc[last_idx]

        score = 0
        matches = []

        # 1. شرط الاتجاه الصاعد (السعر فوق المتوسطات والمتوسط السريع فوق البطء)
        if last_close > last_ema20 and last_ema20 > last_ema50:
            score += 1
            matches.append("اتجاه صاعد")

        # 2. شرط RSI المثالي (بين 45 و 68)
        if 45 <= last_rsi <= 68:
            score += 1
            matches.append(f"RSI {last_rsi:.1f}")

        # 3. شرط زخم MACD (تزايد الأعمدة الإيجابية)
        if last_macd_hist > 0 and last_macd_hist > prev_macd_hist:
            score += 1
            matches.append("زخم MACD")

        # 4. شرط الشموع الانعكاسية (ظل سفلي ضعف جسم الشمعة)
        body = abs(last_close - open_p.iloc[last_idx])
        lower_shadow = min(last_close, open_p.iloc[last_idx]) - low.iloc[last_idx]
        if lower_shadow > 2 * body and body > 0:
            score += 1
            matches.append("شمعة للانعكاس")

        # 5. شرط موجات إليوت
        wave_desc = "غير محدد"
        if last_close > last_ema50 and 50 <= last_rsi <= 65:
            score += 1
            wave_desc = "دعم الموجة 2 (تأهب للـ 3)"
            matches.append("دعم الموجة 2")
        elif last_close > last_ema20 and last_rsi > 65:
            wave_desc = "موجة دافعة صاعدة"
        elif last_rsi < 48:
            wave_desc = "قاع تجميعي"

        # إعادة الشرط الصارم: يجب أن يحقق السهم 3 شروط أو أكثر من أصل 5
        if score >= 3:
            return {
                "Ticker": ticker,
                "Daily_Price": round(last_close, 2),
                "Change_%": daily_change_pct,
                "Daily_RSI": round(last_rsi, 1),
                "Score": f"{score}/5",
                "Matches": ", ".join(matches),
                "Elliott_Wave_D": wave_desc
            }

    except Exception as e:
        return None

    return None

def main():
    print("جاري فحص الأسهم وتطبيق الشروط الفنية الصارمة...")
    results = []
    
    for ticker in EGX_TICKERS:
        res = analyze_stock(ticker)
        if res:
            results.append(res)

    if results:
        res_df = pd.DataFrame(results)
        # ترتيب الأسهم التي اجتازت الشروط حسب نسبة الربح
        res_df = res_df.sort_values(by="Change_%", ascending=False)
        
        # تنسيق المخرجات
        res_df["Change_%"] = res_df["Change_%"].apply(lambda x: f"{x:+.2f}%")
        
        print("\n=== الأسهم المقبولة فقط (التي حققت الشروط الصارمة 3/5 أو أكثر) ===")
        print(res_df.to_string(index=False))
    else:
        print("لم ينطبق التصفية الصارمة (3/5) على أي سهم في جلسة اليوم.")

if __name__ == "__main__":
    main()
