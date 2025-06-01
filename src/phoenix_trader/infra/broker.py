import os, datetime as dt, duckdb, yfinance as yf

BROKER = os.getenv("BROKER", "paper")

if BROKER == "alpaca":
    import alpaca_trade_api as tradeapi
    API = tradeapi.REST(os.getenv("ALPACA_KEY_ID"), os.getenv("ALPACA_SECRET"),
                        "https://paper-api.alpaca.markets")
else:
    DB = duckdb.connect("data/trades.duckdb")
    DB.execute("""CREATE TABLE IF NOT EXISTS trades (
                    ts TIMESTAMP, ticker TEXT, side TEXT, qty INT, price DOUBLE)""")

def submit(symbol, qty, side):
    now = dt.datetime.utcnow()
    if BROKER == "alpaca":
        API.submit_order(symbol, qty, side, "market", "gtc")
        price = API.get_last_trade(symbol).price
    else:
        price = yf.download(symbol, period="1d", interval="1m")["Close"].iloc[-1]
        price *= (1 + (0.001 if side == "buy" else -0.001))
        DB.execute("INSERT INTO trades VALUES (?, ?, ?, ?, ?)",
                   (now, symbol, side, qty, price))
    print(f"[ORDER] {side.upper()} {qty} {symbol} @ {price:.2f} ({BROKER})")
    return f"{symbol}-{now:%H%M%S}"

def pnl_today():
    if BROKER == "alpaca":
        a = API.get_account()
        return float(a.equity) - float(a.last_equity)
    pnl = duckdb.query(
        "SELECT SUM(CASE WHEN side='sell' THEN price*qty ELSE -price*qty END) "
        "FROM trades WHERE CAST(ts AS DATE)=CURRENT_DATE"
    ).fetchone()[0]
    return pnl or 0.0
