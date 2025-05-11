import pandas as pd
import numpy as np
from surmount.base_class import Strategy


class IndicatorUtils:
    @staticmethod
    def ema(series, period):
        return series.ewm(span=period, adjust=False).mean()

    @staticmethod
    def rsi(series, period):
        delta = series.diff()
        gain = delta.where(delta > 0, 0).rolling(period).mean()
        loss = -delta.where(delta < 0, 0).rolling(period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    def roc(series, period):
        return ((series - series.shift(period)) / series.shift(period)) * 100

    @staticmethod
    def cmo(series, period):
        delta = series.diff()
        up = delta.where(delta > 0, 0).rolling(period).sum()
        down = -delta.where(delta < 0, 0).rolling(period).sum()
        return 100 * (up - down) / (up + down)

    @staticmethod
    def stoch(close, high, low, period):
        lowest = low.rolling(period).min()
        highest = high.rolling(period).max()
        return 100 * (close - lowest) / (highest - lowest)


class TradingStrategy(Strategy):
    def __init__(self):
        self.name = "White Line Strategy - Clean Syntax"
        self.interval = "1d"         # Must be a string key Surmount recognizes
        self.assets = ["SPY"]
        self.score_limit = 7
        self.sl_offset = 0.005       # 0.5%
        self.in_trade = False
        self.stop_price = None

    def run(self, data: pd.DataFrame):
        close = data["close"]
        high = data["high"]
        low = data["low"]

        # === Compute Indicators ===
        zlsma_len = 60
        ema1 = IndicatorUtils.ema(close, zlsma_len)
        ema2 = IndicatorUtils.ema(ema1, zlsma_len)
        zlsma = ema1 + (ema1 - ema2)

        ema_short = IndicatorUtils.ema(close, 20)
        ema_long = IndicatorUtils.ema(close, 50)

        macd_line = IndicatorUtils.ema(close, 12) - IndicatorUtils.ema(close, 29)
        macd_hist = macd_line - IndicatorUtils.ema(macd_line, 9)

        rsi_val = IndicatorUtils.rsi(close, 14)
        trix = IndicatorUtils.ema(IndicatorUtils.ema(IndicatorUtils.ema(close, 15), 15), 15)
        willr = IndicatorUtils.stoch(close, high, low, 14)
        mfi = IndicatorUtils.stoch(close, high, low, 14)  # proxy for simplicity
        stoch_k = IndicatorUtils.stoch(close, high, low, 14)
        roc_val = IndicatorUtils.roc(close, 12)
        cmo_val = IndicatorUtils.cmo(close, 14)

        # === Score Logic ===
        score = (
            (close > zlsma).astype(int) +
            (ema_short > ema_long).astype(int) +
            (macd_hist > 0).astype(int) +
            (rsi_val > 50).astype(int) +
            (trix > trix.shift(1)).astype(int) +
            (willr > willr.shift(1)).astype(int) +
            (mfi > 50).astype(int) +
            (stoch_k > 50).astype(int) +
            (roc_val > 0).astype(int) +
            (cmo_val > 0).astype(int)
        )

        # === Signal Logic ===
        signals = []
        for i in range(zlsma_len, len(data)):
            if not self.in_trade and score[i] >= self.score_limit:
                self.in_trade = True
                self.stop_price = zlsma[i] * (1 - self.sl_offset)
                signals.append({"action": "buy", "index": i})
            elif self.in_trade:
                if close[i] > zlsma[i]:
                    self.stop_price = zlsma[i]
                if close[i] < self.stop_price or (
                    close[i - 1] > zlsma[i - 1] and close[i] < zlsma[i]
                ):
                    self.in_trade = False
                    self.stop_price = None
                    signals.append({"action": "sell", "index": i})

        return signals