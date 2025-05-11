from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import EMA, MACD, RSI
from surmount.logging import log

class TradingStrategy(Strategy):
    def __init__(self):
        self.tickers = ["SPY"]
        self.stop_loss = {}

    @property
    def interval(self):
        return "1day"

    @property
    def assets(self):
        return self.tickers

    @property
    def data(self):
        return []

    def ZLSMA(self, prices, length=50):
        ema1 = EMA(prices, length)
        ema2 = EMA(ema1, length)
        return [a + (a - b) for a, b in zip(ema1, ema2)]

    def run(self, data):
        allocation = {}

        for ticker, ohlcv in data["ohlcv"].items():
            prices = ohlcv["close"]
            zlsma = self.ZLSMA(prices)
            macd = MACD(ticker, data["ohlcv"], 12, 26)
            rsi = RSI(prices, 14)
            ema20 = EMA(prices, 20)
            ema50 = EMA(prices, 50)

            current_price = prices[-1]
            zlsma_value = zlsma[-1]

            # Score logic
            score = 0
            if current_price > zlsma_value:
                score += 1
            if ema20[-1] > ema50[-1]:
                score += 1
            if macd["MACD"][-1] > macd["signal"][-1]:
                score += 1

            # Entry
            if score >= 3 and not self.stop_loss.get(ticker):
                allocation[ticker] = 1.0
                self.stop_loss[ticker] = zlsma_value * 0.99
                log(f"BUY {ticker} at {current_price} | Stop loss: {self.stop_loss[ticker]}")

            # Exit
            elif self.stop_loss.get(ticker) and current_price <= self.stop_loss[ticker]:
                allocation[ticker] = 0
                del self.stop_loss[ticker]
                log(f"SELL {ticker} at {current_price} (stop loss hit)")

            else:
                allocation[ticker] = 0

        return TargetAllocation(allocation)