from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import EMA, MACD, RSI, WillR, MFI, SO, Momentum, ATR
import pandas as pd

class TradingStrategy(Strategy):
    def __init__(self, zlsmaLen=47, entry_threshold=7):
        self.assets = ["YourAssetTickerHere"]  # Specify your asset
        self.interval = "1day"  # Choose your data interval
        self.zlsmaLen = zlsmaLen
        self.entry_threshold = entry_threshold
        # Redefine as needed
        self.stop_loss_pct = -0.01  # 1% below the ZLSMA
        self.entry_score = 0
        self.in_position = False
        self.stop_loss = None

    @property
    def data(self):
        # Define any additional data requirements
        return []

    def compute_zlsma(self, prices):
        ema1 = EMA("YourAssetTickerHere", prices, self.zlsmaLen)
        ema2 = EMA("YourAssetTickerHere", [{"YourAssetTickerHere": {"close": x}} for x in ema1], self.zlsmaLen)
        zlsma = [2 * e1 - e2 for e1, e2 in zip(ema1, ema2)]
        return zlsma

    def score_entry_conditions(self, data):
        score = 0
        close_prices = [x["YourAssetTickerHere"]["close"] for x in data["ohlcv"]]
        zlsma = self.compute_zlsma(data["ohlcv"])
        
        # Check each condition
        if close_prices[-1] > zlsma[-1]:
            score += 1
        if EMA("YourAssetTickerHere", data["ohlcv"], 20)[-1] > EMA("YourAssetTickerHere", data["ohlcv"], 50)[-1]:
            score += 1
        macd_histogram = MACD("YourAssetTickerHere", data["ohlcv"], 12, 29)["histogram"]
        if macd_histogram[-1] > 0:
            score += 1
        if RSI("YourAssetTickerHere", data["ohlcv"], 14)[-1] > 50:
            score += 1
        if Momentum("YourAssetTickerHere", data["ohlcv"], 15)[-1] > 0:  # TRIX approximation with momentum
            score += 1
        if WillR("YourAssetTickerHere", data["ohlcv"], 14)[-1] > -50:  # Approximation of conditions with available indicators
            score += 1
        if MFI("YourAssetTickerHere", data["ohlcv"], 14)[-1] > 50:
            score += 1
        if SO("YourAssetTickerHere", data["ohlcv"])[-1] > 50:  # Stochastic K approximation
            score += 1
        if Momentum("YourAssetTickerHere", data["ohlcv"], 12)[-1] > 0:  # ROC approximation with momentum
            score += 1
        if (RSI("YourAssetTickerHere", data["ohlcv"], 14)[-1] - 50) * 2 > 0:  # CMO approximation with RSI
            score += 1
        return score, zlsma

    def should_enter(self, score):
        return score >= self.entry_threshold and not self.in_position

    def should_exit(self, close_price, zlsma):
        return close_price < zlsma[-1] or (self.in_position and close_price < self.stop_loss)

    def update_stop_loss(self, zlsma):
        self.stop_loss = zlsma[-1] * (1 + self.stop_loss_pct)

    def run(self, data):
        score, zlsma = self.score_entry_conditions(data)
        close_price = data["ohlcv"][-1]["YourAssetTickerHere"]["close"]
        
        if self.should_enter(score):
            self.in_position = True
            self.update_stop_loss(zlsma)
            allocation = [{"ticker": "YourAssetTickerHere", "weight": 1}]
        elif self.should_exit(close_price, zlsma):
            self.in_position = False
            allocation = [{"ticker": "YourAssetTickerHere", "weight": 0}]
        else:
            if self.in_position and close_price > zlsma[-1]:
                self.update_stop_loss(zlsma)
            allocation = [{"ticker": "YourAssetTickerHere", "weight": 1 if self.in_position else 0}]
            
        # Plotting (conceptual, adjust according to Surmount capabilities)
        # plot(zlsma, color='white')
        # plot([self.stop_loss] * len(zlsma), color='orange')
        # plot([score] * len(close_price), color='fuchsia')
        
        return TargetAllocation(allocation)

# Ensure to replace "YourAssetTickerHere" with actual asset tickers you intend to trade.