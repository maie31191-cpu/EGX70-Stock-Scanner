# EGX70-Stock-Scanner
Egyptian Stock Market Analysis
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

EGX_TICKERS = [
    "COMI.CA",
    "EAST.CA",
    "HRHO.CA",
    "MFPC.CA",
    "SWDY.CA",
    "ETEL.CA",
    "ABUK.CA",
    "TMGH.CA",
    "EKHO.CA",
    "ORAS.CA",
    "CAPD.CA",
    "ESRS.CA"
]

def analyze_weekly_stock(ticker):
    try:
        stock = yf.Ticker(ticker)
        
        hist = stock.history(period="2y", interval="1wk")
        if len(hist) < 50:
            return None

        close = hist['Close']
        
        sma_20 = close.rolling(window=20).mean().iloc[-1]
        sma_50 = close.rolling(window=50).mean().iloc[-1]
        current_price = close.iloc[-1]

        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = (100 - (100 / (1 + rs))).iloc[-1]

        info = stock.info
        pe_ratio = info.get('trailingPE', np.nan)
        pb_ratio = info.get('priceToBook', np.nan)
        revenue_growth = info.get('revenueGrowth', 0)

        score = 0

        if current_price > sma_20:
            score += 20
        if sma_20 > sma_50:
            score += 20
        if 40 <= rsi <= 60:
            score += 20
        elif rsi < 40:
            score += 15

        if pe_ratio and 0 < pe_ratio < 12:
            score += 15
        if pb_ratio and 0 < pb_ratio < 2:
            score += 10
        if revenue_growth and revenue_growth > 0.10:
            score += 15

        return {
            "Ticker": ticker.replace(".CA", ""),
            "Price (EGP)": round(current_price, 2),
            "RSI (14 Wk)": round(rsi, 2) if not np.isnan(rsi) else "N/A",
            "SMA 20": round(sma_20, 2),
            "SMA 50": round(sma_50, 2),
            "P/E Ratio": round(pe_ratio, 2) if pe_ratio and not np.isnan(pe_ratio) else "N/A",
            "P/B Ratio": round(pb_ratio, 2) if pb_ratio and not np.isnan(pb_ratio) else "N/A",
            "Score": score
        }

    except Exception as e:
        print(f"Error analyzing {ticker}: {e}")
        return None

def generate_pdf_report(dataframe, filename="EGX_Top_Weekly_Opportunities.pdf"):
    doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1A365D'),
        spaceAfter=12,
        alignment=1
    )
    
    subtitle_style = ParagraphStyle(
        'SubTitleStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#4A5568'),
        spaceAfter=20,
        alignment=1
    )

    story.append(Paragraph("EGX Weekly Stock Screener Report", title_style))
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Timeframe: Weekly (1W)", subtitle_style))
    story.append(Spacer(1, 10))

    data = [dataframe.columns.tolist()] + dataframe.values.tolist()
    
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2B6CB0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F7FAFC')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#EDF2F7')]),
    ]))
    
    story.append(table)
    
    story.append(Spacer(1, 20))
    note_style = ParagraphStyle('Note', parent=styles['Italic'], fontSize=8, textColor=colors.gray)
    story.append(Paragraph("Note: High score indicates combined technical momentum on the weekly timeframe and strong fundamental metrics.", note_style))

    doc.build(story)
    print(f"\nReport successfully saved to: {filename}")

if __name__ == "__main__":
    import subprocess
    import sys

    required_libraries = ["pandas", "numpy", "yfinance", "reportlab"]
    for lib in required_libraries:
        try:
            __import__(lib)
        except ImportError:
            print(f"Installing missing dependency: {lib}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib])

    print("Analyzing EGX stocks on weekly timeframe...")
    results = []

    for ticker in EGX_TICKERS:
        print(f"Processing {ticker}...")
        res = analyze_weekly_stock(ticker)
        if res:
            results.append(res)

    df = pd.DataFrame(results)
    
    if not df.empty:
        df = df.sort_values(by="Score", ascending=False).reset_index(drop=True)
        print("\n--- Best EGX Stock Opportunities ---")
        print(df.to_string(index=False))
        generate_pdf_report(df)
    else:
        print("No data found to generate the report.")

