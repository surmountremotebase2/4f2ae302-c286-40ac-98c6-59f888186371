from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import EMA, MACD, RSI, ROC
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

    def ZLSMA(self, prices, length=60):
        ema1 = EMA(prices, length)
        ema2 = EMA(ema1, length)
        return [a + (a - b) for a, b in zip(ema1, ema2)]

    def TRIX(self, prices, length=15):
        return EMA(EMA(EMA(prices, length), length), length)

    def STOCH(self, close, high, low, period):
        stoch_vals = []
        for i in range(len(close)):
            if i < period:
                stoch_vals.append(0)
            else:
                lowest = min(low[i - period:i])
                highest = max(high[i - period:i])
                stoch_vals.append(100 * (close[i] - lowest) / (highest - lowest) if highest != lowest else 0)
        return stoch_vals

    def CMO(self, prices, period):
        cmo_vals = []
        for i in range(len(prices)):
            if i < period:
                cmo_vals.append(0)
            else:
                delta = [prices[j] - prices[j - 1] for j in range(i - period + 1, i + 1)]
                gains = sum([d for d in delta if d > 0])
                losses = sum([-d for d in delta if d < 0])
                denominator = gains + losses
                cmo_vals.append(100 * (gains - losses) / denominator if denominator != 0 else 0)
        return cmo_vals

    def run(self, data):
        allocation = {}
        for ticker, ohlcv in data["ohlcv"].items():
            close = ohlcv["close"]
            high = ohlcv["high"]
            low = ohlcv["low"]

            zlsma = self.ZLSMA(close)
            ema20 = EMA(close, 20)
            ema50 = EMA(close, 50)
            macd = MACD(ticker, data["ohlcv"], 12, 29)
            rsi = RSI(close, 14)
            trix = self.TRIX(close, 15)
            willr = self.STOCH(close, high, low, 14)
            mfi = self.STOCH(close, high, low, 14)  # simplified proxy
            stoch_k = self.STOCH(close, high, low, 14)
            roc = ROC(close, 12)
            cmo = self.CMO(close, 14)

            i = len(close) - 1  # last bar index
            score = 0
            score += 1 if close[i] > zlsma[i] else 0
            score += 1 if ema20[-1] > ema50[-1] else 0
            score += 1 if macd["MACD"][-1] > macd["signal"][-1] else 0
            score += 1 if rsi[-1] > 50 else 0
            score += 1 if trix[-1] > trix[-2] else 0
            score += 1 if willr[-1] > willr[-2] else 0
            score += 1 if mfi[-1] > 50 else 0
            score += 1 if stoch_k[-1] > 50 else 0
            score += 1 if roc[-1] > 0 else 0
            score += 1 if cmo[-1] > 0 else 0

            threshold = 7
            stop_offset = 0.005  # 0.5%

            current_price = close[-1]
            zlsma_value = zlsma[-1]

            if score >= threshold and not self.stop_loss.get(ticker):
                allocation[ticker] = 1.0
                self.stop_loss[ticker] = zlsma_value * (1 - stop_offset)
                log(f"BUY {ticker} at {current_price} | Stop: {self.stop_loss[ticker]} | Score: {score}")

            elif self.stop_loss.get(ticker) and current_price < self.stop_loss[ticker]:
                allocation[ticker] = 0
                del self.stop_loss[ticker]
                log(f"SELL {ticker} at {current_price} (Stop hit)")

            else:
                allocation[ticker] = 0

        return TargetAllocation(allocation)