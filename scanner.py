import pandas as pd
import yfinance as yf
import numpy as np

# قائمة موسعة تشمل أنشط أسهم البورصة المصرية (EGX30 & EGX70)
EGX_ALL_STOCKS = [
    "COMI.CA", "EAST.CA", "SWDY.CA", "HRHO.CA", "MFPC.CA", "HELI.CA", "TMGH.CA",
    "MCRO.CA", "BTFH.CA", "EFIH.CA", "ABUK.CA", "ETEL.CA", "EKHO.CA", "AMOC.CA",
    "ORAS.CA", "CERE.CA", "ISPH.CA", "CLHO.CA", "JUFO.CA", "PHDC.CA", "MNHD.CA",
    "AUTO.CA", "ALCN.CA", "SKPC.CA", "EGAL.CA", "GBCO.CA", "ORWE.CA", "BINV.CA",
    "RTAI.CA", "ACGC.CA", "CCAP.CA", "PORT.CA", "KABO.CA", "ESRS.CA", "EFTC.CA"
]

def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def scan_egx_market():
    results = []
    print("--- جاري فحص جميع أسهم البورصة المصرية واختيار الأفضل (فريم أسبوعي) ---\n")
    
    for ticker in EGX_ALL_STOCKS:
        try:
            stock = yf.Ticker(ticker)
            # جلب البيانات لآخر سنتين بفريم أسبوعي
            df = stock.history(period="2y", interval="1wk")
            if df.empty or len(df) < 15:
                continue

            df['RSI'] = calculate_rsi(df['Close'])
            latest_price = round(df['Close'].iloc[-1], 2)
            latest_rsi = round(df['RSI'].iloc[-1], 2)

            # البيانات المالية
            info = stock.info
            pe_ratio = round(info.get('trailingPE', 0), 2) if info.get('trailingPE') else np.nan
            pb_ratio = round(info.get('priceToBook', 0), 2) if info.get('priceToBook') else np.nan

            # تحديد جودة الفرصة
            opportunity = "عادي"
            score = 0  # نقاط لترتيب الأفضلية

            if latest_rsi <= 35:
                opportunity = "فرصة ذهبية (تجميع حاد)"
                score += 3
            elif 35 < latest_rsi <= 45:
                opportunity = "فرصة ارتداد جيدة"
                score += 2
            elif latest_rsi >= 70:
                opportunity = "تشبع شرائي (قريب من قمة)"
                score -= 1

            if not np.isnan(pe_ratio) and 0 < pe_ratio < 10:
                score += 1
            if not np.isnan(pb_ratio) and 0 < pb_ratio < 1.5:
                score += 1

            results.append({
                'Ticker': ticker,
                'Price': latest_price,
                'RSI_Weekly': latest_rsi,
                'P/E': pe_ratio,
                'P/B': pb_ratio,
                'Opportunity': opportunity,
                'Score': score
            })
        except Exception:
            continue

    if not results:
        print("لم يتم العثور على بيانات الماركت.")
        return

    # تحويل لجدول وترتيب الأسهم من الأفضل للأقل
    res_df = pd.DataFrame(results)
    res_df = res_df.sort_values(by=['Score', 'RSI_Weekly'], ascending=[False, True])
    
    # عرض أفضل الأسهم فقط (Top Opportunities)
    top_picks = res_df[res_df['Score'] > 0].drop(columns=['Score'])
    
    print("=== أفضل الأسهم المرشحة للارتداد والتجميع ===")
    if not top_picks.empty:
        print(top_picks.to_string(index=False))
    else:
        print("جميع الأسهم الحالية في مستويات متوسطة، لا يوجد أسهم في قيعان حادة حالياً.")

if __name__ == "__main__":
    scan_egx_market()
