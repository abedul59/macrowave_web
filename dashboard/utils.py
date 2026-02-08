import yfinance as yf
import requests
import pandas as pd
from bs4 import BeautifulSoup
from fredapi import Fred
import os
import datetime

# 請確保在 Render 的環境變數設定 FRED_API_KEY
FRED_KEY = os.environ.get('FRED_API_KEY', '你的_FRED_KEY_填在這')
fred = Fred(api_key=FRED_KEY)

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

def get_yfinance_data(ticker):
    try:
        t = yf.Ticker(ticker)
        # 抓取最新價格
        data = t.history(period="1d")
        if not data.empty:
            return data['Close'].iloc[-1]
    except:
        pass
    return 0.0

def get_us_bond_10y():
    # 美債 10Y (Yahoo: ^TNX)
    val = get_yfinance_data("^TNX")
    return val if val else 0.0

def get_jp_bond_10y():
    # 嘗試抓取日債，CNYES 是較穩定的靜態頁面
    try:
        url = "https://www.cnyes.com/futures/html5chart/JP10YY.html"
        r = requests.get(url, headers=HEADERS, timeout=5)
        df = pd.read_html(r.text)[0]
        return float(df.iloc[0][1])
    except:
        return 0.0

def get_crb_index():
    # CRB 指數，Yahoo Finance 代號通常是 CL=F (原油) 作為參考，或抓取網頁
    # 這裡示範抓取 Oil 作為原物料代表，因為免費 CRB 數據源難找
    # 若堅持 CRB，可用 requests 抓 StockQ
    try:
        r = requests.get('https://www.stockq.org/index/CRB.php', headers=HEADERS, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        # 需要根據 StockQ 結構解析，這裡簡化使用 Yahoo 的原油代替示範
        return get_yfinance_data("CL=F") 
    except:
        return 0.0

def get_fred_series(series_id):
    try:
        s = fred.get_series(series_id)
        return s.iloc[-1]
    except:
        return 0.0

def get_fred_history(series_id, limit=6):
    try:
        s = fred.get_series(series_id)
        return s.tail(limit).tolist()
    except:
        return []

def get_twse_market_value():
    # 證交所市值 (改用 requests 抓 CSV 連結，比 Selenium 快)
    # 簡化：直接抓取證交所 API
    try:
        date_str = datetime.datetime.now().strftime("%Y%m%d")
        url = f"https://www.twse.com.tw/exchangeReport/MI_INDEX?response=json&date={date_str}&type=ALL"
        # 這裡實作複雜，為求網頁不卡死，建議暫時回傳模擬數據或使用固定 API
        # 或是抓取 twse 統計頁面
        return 50000000 # 範例值，實際需解析 JSON
    except:
        return 0

def get_metals_status():
    # 貴金屬偵測 (使用 yfinance)
    metals = {
        "Gold": "GC=F", "Silver": "SI=F", 
        "Copper": "HG=F", "Platinum": "PL=F" # 鎳錫在 Yahoo 較難抓，用白金代替示範
    }
    results = []
    has_crash = False
    
    for name, ticker in metals.items():
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="6mo")
            if not hist.empty:
                high = hist['High'].max()
                current = hist['Close'].iloc[-1]
                drop = (high - current) / high * 100
                status = "Safe"
                if drop >= 50:
                    status = "Danger"
                    has_crash = True
                results.append({
                    "name": name, "current": round(current, 2),
                    "high": round(high, 2), "drop": round(drop, 2),
                    "status": status
                })
        except:
            pass
    return results, has_crash

def update_all_data():
    data = {}
    
    # 1. 美日利差
    us_10y = get_us_bond_10y()
    jp_10y = get_jp_bond_10y()
    spread = us_10y - jp_10y
    data['us_jp_spread'] = {
        'us': round(us_10y, 2), 'jp': round(jp_10y, 2), 
        'spread': round(spread, 2),
        'status': 'Danger' if spread < 2.0 else 'Safe'
    }

    # 2. Mark 17 部分指標 (FRED)
    # PMI: FRED NAPM 經常失效，這裡改用 ISM API 或固定數值
    # 為確保網站穩定，我們用 "GDP" 或 "Unemployment" 示範 FRED 連接
    unrate = get_fred_series('UNRATE')
    
    data['mark17'] = []
    score = 0
    
    # 失業率邏輯
    ur_status = "Safe"
    if unrate > 4.5: 
        score += 3; ur_status = "Danger"
    elif unrate > 4: 
        score += 1; ur_status = "Warning"
    
    data['mark17'].append({
        'item': '失業率 (Unemployment)', 'value': f"{unrate}%", 
        'score': score, 'status': ur_status
    })

    # 總分建議
    advice = "Safe"
    if score >= 15: advice = "Flee"
    elif score >= 12: advice = "Reduce"
    elif score >= 6: advice = "Caution"
    
    data['total_score'] = score
    data['advice'] = advice

    # 3. 貴金屬
    metals, crash = get_metals_status()
    data['metals'] = metals
    
    return data