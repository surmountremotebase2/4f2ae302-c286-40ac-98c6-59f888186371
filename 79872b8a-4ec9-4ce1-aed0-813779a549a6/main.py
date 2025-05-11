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
        """
        Proxy ZLSMA: uses double EMA smoothing
        """
        ema1 = EMA(prices, length)
        ema2 = EMA(ema1, length)
        return [a + (a - b) for a, b in zip(ema1, ema2)]

    def run(self, data):
        d = data["ohlcv"]
        allocation = {}

        for ticker in self.tickers:
            prices = d[ticker]["close"]
            zlsma = self.ZLSMA(prices)
            macd = MACD(ticker, d, 12, 26)
            rsi = RSI(prices, 14)
            ema20 = EMA(prices, 20)
            ema50 = EMA(prices, 50)

            current_price = prices[-1]
            zlsma_value = zlsma[-1]

            # Score-based logic (3 simple signals)
            score = 0
            if current_price > zlsma_value:
                score += 1
            if ema20[-1] > ema50[-1]:
                score += 1
            if macd["MACD"][-1] > macd["signal"][-1]:
                score += 1

            # Entry condition: all 3 signals align
            if score >= 3 and not self.stop_loss.get(ticker):
                allocation[ticker] = 1.0
                self.stop_loss[ticker] = zlsma_value * 0.99  # 1% below ZLSMA
                log(f"BUY {ticker} at {current_price} | Stop loss set at {self.stop_loss[ticker]}")
            
            # Exit if stop-loss hit
            elif self.stop_loss.get(ticker) and current_price <= self.stop_loss[ticker]:
                allocation[ticker] = 0
                del self.stop_loss[ticker]
                log(f"SELL {ticker} at {current_price} (stop loss hit)")

            # Hold position, no new entry
            else:
                allocation[ticker] = 0

        return TargetAllocation(allocation)