from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import EMA, MACD
from surmount.logging import log
from surmount.data import Asset

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
        Zero-Lag Exponential Moving Average (ZLSMA).
        This is a placeholder function and might not directly mimic a true ZLSMA since Surmount AI might not support it directly.
        EMA is used as a proxy given the details in the prompt did not include a ZLSMA calculation directly.
        """
        return EMA(prices, length)

    def run(self, data):
        d = data["ohlcv"]
        allocation = {}
        for ticker in self.tickers:
            prices = d[ticker]["close"]  # Your price data series here
            zlsma = self.ZLSMA(prices)
            macd_signal = MACD(ticker, d, 12, 26)["signal"][-1]
            macd = MACD(ticker, d, 12, 26)["MACD"][-1]
            current_price = prices[-1]
            zlsma_value = zlsma[-1]
            
            # Check to buy condition: Current price crosses above ZLSMA AND MACD crosses bullish
            if current_price > zlsma_value and macd[-1] > macd_signal[-1] and not self.stop_loss.get(ticker):
                allocation[ticker] = 1.0  # Allocate 100% to this asset
                self.stop_loss[ticker] = zlsma_value * 0.99  # Stop loss at 1% below the ZLSMA
            elif self.stop_loss.get(ticker) and current_price <= self.stop_loss[ticker]:
                allocation[ticker] = 0  # Sell if stop loss is hit.
                del self.stop_loss[ticker]  # Remove the stop loss after selling
            else:
                allocation[ticker] = 0  # Not meeting conditions, do not allocate

        return TargetAllocation(allocation)