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

        # معالجة الأنسدة إذا كانت متداخلة
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
        
        # حساب نسبة المكسب / التغير اليومي (%)
        daily_change_pct = ((last_close - prev_close) / prev_close) * 100

        last_rsi = df['RSI'].iloc[last_idx]
        last_macd_hist = df['MACD_Hist'].iloc[last_idx]
        prev_macd_hist = df['MACD_Hist'].iloc[last_idx - 1]
        last_ema20 = df['EMA_20'].iloc[last_idx]
        last_ema50 = df['EMA_50'].iloc[last_idx]

        score = 0
        matches = []

        # 1. الاتجاه العام (اتجاه صاعد)
        if last_close > last_ema20 and last_ema20 > last_ema50:
            score += 1
            matches.append("اتجاه صاعد")

        # 2. مؤشر RSI (نطاق إيجابي)
        if 45 <= last_rsi <= 68:
            score += 1
            matches.append(f"RSI {last_rsi:.1f}")

        # 3. زخم MACD (تقاطع إيجابي أو تزايد الزخم)
        if last_macd_hist > 0 and last_macd_hist > prev_macd_hist:
            score += 1
            matches.append("زخم MACD")

        # 4. الشموع الانعكاسية (شمعة مطرقة أو ابتلاعية إيجابية)
        body = abs(last_close - open_p.iloc[last_idx])
        lower_shadow = min(last_close, open_p.iloc[last_idx]) - low.iloc[last_idx]
        if lower_shadow > 2 * body and body > 0:
            score += 1
            matches.append("شمعة انعكاسية")

        # 5. نموذج موجات إليوت التقريبي (إيقاع الموجة)
        wave_desc = "غير محدد"
        if last_close > last_ema50 and 50 <= last_rsi <= 65:
            score += 1
            wave_desc = "منطقة دعم الموجة 2 (تأهب للـ 3 اليومية)"
            matches.append("دعم الموجة 2")
        elif last_close > last_ema20 and last_rsi > 65:
            wave_desc = "موجة دافعة صاعدة يومياً"
        elif last_rsi < 48:
            wave_desc = "قاع تجميعي يومي"

        # ترشيح الأسهم الحاصلة على 3 درجات أو أكثر من 5
        if score >= 3:
            return {
                "Ticker": ticker,
                "Daily_Price": round(last_close, 2),
                "Change_%": f"{daily_change_pct:+.2f}%",  # يعرض نسبة التغير اليومية بالزائد أو الناقص
                "Daily_RSI": round(last_rsi, 1),
                "Score": f"{score}/5",
                "Matches": ", ".join(matches),
                "Elliott_Wave_D": wave_desc
            }

    except Exception as e:
        return None

    return None

def main():
    print("جاري فحص أسهم البورصة المصرية لتسويات اليوم...")
    results = []
    
    for ticker in EGX_TICKERS:
        res = analyze_stock(ticker)
        if res:
            results.append(res)

    if results:
        res_df = pd.DataFrame(results)
        print("\n=== نتائج الفحص النهائية المعتمدة ===")
        print(res_df.to_string(index=False))
    else:
        print("لم يتم العثور على أسهم تطابق الشروط حالياً.")

if __name__ == "__main__":
    main()
