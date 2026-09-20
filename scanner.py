import pandas as pd
import numpy as np
import yfinance as yf

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
        # جلب البيانات لآخر 6 أشهر مع تعطيل التخزين المؤقت
        ticker_obj = yf.Ticker(ticker)
        df = ticker_obj.history(period="6mo", interval="1d", auto_adjust=False)
        
        if df.empty or len(df) < 50:
            return None

        # استخدام Adj Close للسعر الدقيق الفعلي أو Close إن لم يتوفر
        if 'Adj Close' in df.columns and not df['Adj Close'].isna().all():
            close = df['Adj Close']
        else:
            close = df['Close']

        high = df['High']
        low = df['Low']
        open_p = df['Open']

        # حساب المؤشرات الفنية
        df['RSI'] = calculate_rsi(close)
        macd, signal_line, hist = calculate_macd(close)
        df['MACD_Hist'] = hist
        df['EMA_20'] = close.ewm(span=20, adjust=False).mean()
        df['EMA_50'] = close.ewm(span=50, adjust=False).mean()

        last_idx = -1
        # السعر الدقيق الحقيقي بدقة أصلية بدون تقريب مسبق
        last_close = float(close.iloc[last_idx])
        prev_close = float(close.iloc[last_idx - 1])
        
        # حساب نسبة التغير اليومية
        daily_change_pct = ((last_close - prev_close) / prev_close) * 100

        last_rsi = float(df['RSI'].iloc[last_idx])
        last_macd_hist = float(df['MACD_Hist'].iloc[last_idx])
        prev_macd_hist = float(df['MACD_Hist'].iloc[last_idx - 1])
        last_ema20 = float(df['EMA_20'].iloc[last_idx])
        last_ema50 = float(df['EMA_50'].iloc[last_idx])

        score = 0
        matches = []

        # 1. الاتجاه الصاعد
        if last_close > last_ema20 and last_ema20 > last_ema50:
            score += 1
            matches.append("اتجاه صاعد")

        # 2. نطاق RSI
        if 45 <= last_rsi <= 68:
            score += 1
            matches.append(f"RSI {last_rsi:.1f}")

        # 3. زخم MACD
        if last_macd_hist > 0 and last_macd_hist > prev_macd_hist:
            score += 1
            matches.append("زخم MACD")

        # 4. الشمعة الانعكاسية
        body = abs(last_close - float(open_p.iloc[last_idx]))
        lower_shadow = min(last_close, float(open_p.iloc[last_idx])) - float(low.iloc[last_idx])
        if lower_shadow > 2 * body and body > 0:
            score += 1
            matches.append("شمعة للانعكاس")

        # 5. تحليل موجات إليوت
        wave_desc = "غير محدد"
        if last_close > last_ema50 and 50 <= last_rsi <= 65:
            score += 1
            wave_desc = "دعم الموجة 2 (تأهب للـ 3)"
            matches.append("دعم الموجة 2")
        elif last_close > last_ema20 and last_rsi > 65:
            wave_desc = "موجة دافعة صاعدة"
        elif last_rsi < 48:
            wave_desc = "قاع تجميعي"

        # شرط الترشيح الصارم (3/5 على الأقل)
        if score >= 3:
            return {
                "Ticker": ticker,
                "Exact_Price": f"{last_close:.4f}",  # إظهار السعر بدقة 4 أرقام عشريّة كـ String لمنع التقريب
                "Change_%": daily_change_pct,
                "Daily_RSI": round(last_rsi, 1),
                "Score": f"{score}/5",
                "Matches": ", ".join(matches),
                "Elliott_Wave": wave_desc
            }

    except Exception as e:
        return None

    return None

def main():
    print("جاري فحص الأسهم وتطبيق الشروط مع استخراج السعر الدقيق...")
    results = []
    
    for ticker in EGX_TICKERS:
        res = analyze_stock(ticker)
        if res:
            results.append(res)

    if results:
        res_df = pd.DataFrame(results)
        res_df = res_df.sort_values(by="Change_%", ascending=False)
        res_df["Change_%"] = res_df["Change_%"].apply(lambda x: f"{x:+.2f}%")
        
        print("\n=== نتائج الفحص الصارم بالسعر الفعلي الدقيق ===")
        print(res_df.to_string(index=False))
    else:
        print("لم تعثر التصفية الصارمة (3/5) على أسهم مطابقة اليوم.")

if __name__ == "__main__":
    main()
