from flask import Flask, render_template, request, jsonify
import requests
import yfinance as yf
import time

app = Flask(__name__)

FINNHUB_API_KEY = "dav9i3hr01qp1e4m5elgdav9i3hr01qp1e4m5em0"

# Sunucuyu yormamak için 2 dakikalık basit bellek önbelleği (Cache)
STOCKS_CACHE = {
    'data': [],
    'last_updated': 0
}

def fetch_live_stocks():
    """Top US Stocks için yfinance kullanarak canlı fiyat ve geçmiş grafik verilerini çeker."""
    now = time.time()
    # 2 dakika (120 saniye) geçmediyse önbellekteki veriyi dön
    if STOCKS_CACHE['data'] and (now - STOCKS_CACHE['last_updated'] < 120):
        return STOCKS_CACHE['data']

    target_tickers = [
        {"ticker": "AAPL", "name": "Apple Inc."},
        {"ticker": "NVDA", "name": "NVIDIA Corp."},
        {"ticker": "TSLA", "name": "Tesla Inc."},
        {"ticker": "AMZN", "name": "Amazon.com Inc."},
        {"ticker": "MSFT", "name": "Microsoft Corp."},
        {"ticker": "F", "name": "Ford Motor Company"},
        {"ticker": "GE", "name": "General Electric"},
        {"ticker": "V", "name": "Visa"},
        {"ticker": "AAL", "name": "American Airlines"},
        {"ticker": "AMD", "name": "Advanced Micro Devices, Inc."},
        {"ticker": "GOOGL", "name": "Alphabet Inc."}
    ]

    live_stocks = []
    
    # Tüm sembolleri tek seferde yfinance ile sorgula (Daha hızlıdır)
    symbols_str = " ".join([item["ticker"] for item in target_tickers])
    try:
        tickers = yf.Tickers(symbols_str)
        
        for item in target_tickers:
            sym = item["ticker"]
            t = tickers.tickers[sym]
            
            # Son 5 günlük saatlik veriyi çekerek çizgi grafik için history dizisi oluştur
            df = t.history(period="5d", interval="60m")
            
            if not df.empty:
                current_price = float(df['Close'].iloc[-1])
                prev_close = float(df['Close'].iloc[0]) # Periyot başı fiyatı
                
                price_change = current_price - prev_close
                pct_change = (price_change / prev_close) * 100 if prev_close != 0 else 0
                
                # Kartın altındaki mini trend grafiği için son 10 kapanış fiyatı
                history_points = [round(float(p), 2) for p in df['Close'].tail(10).tolist()]
                
                live_stocks.append({
                    "ticker": sym,
                    "name": item["name"],
                    "price": f"${current_price:.2f}",
                    "change": f"{'+' if pct_change >= 0 else ''}{pct_change:.2f}%",
                    "history": history_points,
                    "is_up": price_change >= 0
                })
            else:
                # Veri alınamazsa yedek değer
                live_stocks.append({
                    "ticker": sym,
                    "name": item["name"],
                    "price": "N/A",
                    "change": "0.00%",
                    "history": [0, 0, 0],
                    "is_up": True
                })
                
        STOCKS_CACHE['data'] = live_stocks
        STOCKS_CACHE['last_updated'] = now
        return live_stocks

    except Exception as e:
        print(f"Stock fetch error: {e}")
        # Hata durumunda var olan cache'i dön
        return STOCKS_CACHE['data'] if STOCKS_CACHE['data'] else target_tickers


@app.route('/')
def index():
    # USD Bazlı Döviz Kurları
    rates = {
        'EUR': '0.91',
        'GBP': '0.76',
        'JPY': '148.50'
    }

    # Sağ Taraf Canlı Hisse Döngüsü Verileri (yfinance ile canlı çekiliyor)
    stocks = fetch_live_stocks()

    # Kripto Para Verileri
    cryptos = [
        {"symbol": "BTC/USD", "name": "Bitcoin", "price": "$63,450.00", "change": "+2.40%"},
        {"symbol": "ETH/USD", "name": "Ethereum", "price": "$2,640.50", "change": "+1.85%"},
        {"symbol": "SOL/USD", "name": "Solana", "price": "$152.30", "change": "-0.75%"}
    ]

    return render_template('index.html', rates=rates, stocks=stocks, cryptos=cryptos)


@app.route('/get_news', methods=['GET'])
def get_news():
    """Finnhub üzerinden canlı haber çeker, hata veya key yoksa yedek haberleri sunar."""
    if not FINNHUB_API_KEY or FINNHUB_API_KEY == "dav9i3hr01qp1e4m5elgdav9i3hr01qp1e4m5em0":
        return jsonify([
            {"id": 1, "headline": "Federal Reserve signals potential rate adjustments amid market volatility", "url": "#", "source": "MarketWatch"},
            {"id": 2, "headline": "Global tech stocks rally following impressive quarterly earnings reports", "url": "#", "source": "Bloomberg"},
            {"id": 3, "headline": "Oil prices stabilize as crude inventories show unexpected drop", "url": "#", "source": "Reuters"},
            {"id": 4, "headline": "Treasury yields fluctuate as investors digest latest inflation figures", "url": "#", "source": "CNBC"}
        ])

    try:
        url = f"https://finnhub.io/api/v1/news?category=general&token={FINNHUB_API_KEY}"
        res = requests.get(url, timeout=10)
        data = res.json()
        
        if isinstance(data, list) and len(data) > 0:
            news_list = []
            for item in data[:15]:
                news_list.append({
                    "id": item.get("id"),
                    "headline": item.get("headline"),
                    "url": item.get("url"),
                    "source": item.get("source")
                })
            return jsonify(news_list)
    except Exception as e:
        print(f"News fetch error: {e}")

    return jsonify([
        {"id": 1, "headline": "Federal Reserve signals potential rate adjustments amid market volatility", "url": "#", "source": "MarketWatch"},
        {"id": 2, "headline": "Global tech stocks rally following impressive quarterly earnings reports", "url": "#", "source": "Bloomberg"},
        {"id": 3, "headline": "Oil prices stabilize as crude inventories show unexpected drop", "url": "#", "source": "Reuters"},
        {"id": 4, "headline": "Treasury yields fluctuate as investors digest latest inflation figures", "url": "#", "source": "CNBC"}
    ])


@app.route('/search_stock', methods=['GET'])
def search_stock():
    symbol = request.args.get('symbol', '').upper()
    period = request.args.get('period', '1d')

    if not symbol:
        return jsonify({"error": "Plese enter a symbol."}), 400

    period_map = {
        '1d': ('1d', '15m'),
        '1w': ('5d', '60m'),
        '1m': ('1mo', '1d'),
        '1y': ('1y', '1wk')
    }

    yf_period, yf_interval = period_map.get(period, ('1d', '15m'))

    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=yf_period, interval=yf_interval)

        if df.empty:
            return jsonify({"error": f"'{symbol}' Couldn't find data."}), 404

        info = ticker.info
        name = info.get('shortName') or info.get('longName') or symbol

        candles = []
        for index, row in df.iterrows():
            candles.append({
                'x': int(index.timestamp() * 1000),
                'o': round(float(row['Open']), 2),
                'h': round(float(row['High']), 2),
                'l': round(float(row['Low']), 2),
                'c': round(float(row['Close']), 2)
            })

        latest_close = candles[-1]['c']
        first_open = candles[0]['o']
        price_change = latest_close - first_open
        pct_change = (price_change / first_open) * 100
        change_str = f"{'+' if price_change >= 0 else ''}{price_change:.2f} ({pct_change:+.2f}%)"

        return jsonify({
            'ticker': symbol,
            'name': name,
            'price': f"${latest_close:.2f}",
            'change': change_str,
            'candles': candles
        })

    except Exception as e:
        return jsonify({"error": f"Cant pull data: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True)
