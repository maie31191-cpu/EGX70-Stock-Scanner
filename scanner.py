import yfinance as yf
import pandas as pd
import ta

# قائمة بأبرز أسهم البورصة المصرية EGX
tickers = [
    "COMI.CA", "EAST.CA", "TMGH.CA", "HRHO.CA", "SWDY.CA", 
    "MFPC.CA", "EKHO.CA", "ETEL.CA", "AMOC.CA", "CERE.CA",
    "ESRS.CA", "ORWE.CA", "ISPH.CA", "PHDC.CA", "ABUK.CA",
    "HELI.CA", "AUTO.CA", "BINV.CA", "JUFO.CA", "ORAS.CA"
]

results = []

for ticker in tickers:
    try:
        # جلب بيانات السهم اليومية
        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        
        if df.empty or len(df) < 200:
            continue

        # التعامل مع أبعاد البيانات في yfinance
        if isinstance(df.columns, pd.MultiIndex):
            close_prices = df['Close'][ticker]
        else:
            close_prices = df['Close']

        # 1. حساب المتوسطات الأسية EMA 50 & EMA 200
        ema_50 = ta.trend.ema_indicator(close_prices, window=50)
        ema_200 = ta.trend.ema_indicator(close_prices, window=200)

        # 2. حساب مؤشر القوة النسبية RSI 14
        rsi = ta.momentum.rsi(close_prices, window=14)

        # 3. حساب مؤشر MACD والهستوجرام
        macd_object = ta.trend.MACD(close_prices)
        macd_line = macd_object.macd()
        signal_line = macd_object.macd_signal()
        histogram = macd_object.macd_diff()

        # أخذ قيم آخر شمعة (إغلاق الجلسة) والشمعة التي قبلها
        last_close = close_prices.iloc[-1]
        curr_ema50 = ema_50.iloc[-1]
        curr_ema200 = ema_200.iloc[-1]
        curr_rsi = rsi.iloc[-1]
        
        curr_macd = macd_line.iloc[-1]
        curr_signal = signal_line.iloc[-1]
        prev_macd = macd_line.iloc[-2]
        prev_signal = signal_line.iloc[-2]
        
        curr_hist = histogram.iloc[-1]
        prev_hist = histogram.iloc[-2]

        # الشروط المطلوب تحققها:
        # الشرط الأول: EMA 50 أعلى من EMA 200
        cond1 = curr_ema50 > curr_ema200
        
        # الشرط الثاني: RSI بين 50 و 65
        cond2 = 50 <= curr_rsi <= 65
        
        # الشرط الثالث: تقاطع MACD لأعلى (كان تحته وأصبح فوقه) مع زخم في الهستوجرام (ارتفاع قيمة الهستوجرام)
        macd_cross_up = (prev_macd <= prev_signal) and (curr_macd > curr_signal)
        histogram_momentum = curr_hist > prev_hist and curr_hist > 0
        cond3 = macd_cross_up and histogram_momentum

        # تجميع الأسهم التي تطابق كافة الشروط
        if cond1 and cond2 and cond3:
            results.append({
                "Ticker": ticker,
                "Price": round(last_close, 2),
                "RSI": round(curr_rsi, 2),
                "EMA_50": round(curr_ema50, 2),
                "EMA_200": round(curr_ema200, 2),
                "Signal": "فرصة دخول ممتازة"
            })

    except Exception as e:
        continue

# طباعة الجدول النهائي
results_df = pd.DataFrame(results)

print("=" * 65)
print("             نتائج فحص البورصة المصرية (EGX) - شروط التقاطع والزخم             ")
print("=" * 65)

if not results_df.empty:
    print(results_df.to_string(index=False))
else:
    print("لا توجد أسهم تطابق الشروط الفنية المحددة في إغلاق اليوم.")
print("=" * 65)
