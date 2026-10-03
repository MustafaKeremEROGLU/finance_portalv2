from flask import Flask, render_template, request, jsonify
import requests
import yfinance as yf

app = Flask(__name__)

# Finnhub API Key (Varsa tırnak içine yazabilirsiniz)
FINNHUB_API_KEY = "YOUR_FINNHUB_API_KEY"

@app.route('/')
def index():
    # USD Bazlı Döviz Kurları (USD/EUR, USD/GBP, USD/JPY)
    rates = {
        'EUR': '0.91',
        'GBP': '0.76',
        'JPY': '148.50'
    }

    # Sağ Taraf Canlı Hisse Döngüsü Verileri
    stocks = [
        {"ticker": "AAPL", "name": "Apple Inc.", "price": "$224.23", "change": "+1.45%", "history": [220, 221, 222, 221.5, 223, 224.23]},
        {"ticker": "NVDA", "name": "NVIDIA Corp.", "price": "$128.05", "change": "+3.12%", "history": [122, 124, 125, 126.5, 127, 128.05]},
        {"ticker": "TSLA", "name": "Tesla Inc.", "price": "$251.10", "change": "-0.85%", "history": [255, 254, 253, 252, 251.5, 251.10]},
        {"ticker": "AMZN", "name": "Amazon.com Inc.", "price": "$186.40", "change": "+0.92%", "history": [183, 184, 185, 184.8, 186, 186.40]},
        {"ticker": "MSFT", "name": "Microsoft Corp.", "price": "$448.90", "change": "-0.30%", "history": [451, 450, 449.5, 450, 448.9, 448.90]},
        {"ticker": "GOOGL", "name": "Alphabet Inc.", "price": "$179.80", "change": "+2.10%", "history": [175, 176, 177, 178, 179, 179.80]}
    ]

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
    if not FINNHUB_API_KEY or FINNHUB_API_KEY == "YOUR_FINNHUB_API_KEY":
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
        return jsonify({"error": "Lütfen bir sembol girin."}), 400

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
            return jsonify({"error": f"'{symbol}' sembolü için veri bulunamadı."}), 404

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
        return jsonify({"error": f"Veri çekme hatası: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True)