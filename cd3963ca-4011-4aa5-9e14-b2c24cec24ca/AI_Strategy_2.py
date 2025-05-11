from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import EMA, MACD, RSI, WillR, MFI, SMA, SO, Momentum, ATR, PPO
from surmount.logging import log
import pandas_ta as ta
import pandas as pd

class CustomTrendStrategy(Strategy):
    def __init__(self, threshold=7, zlsma_len=60):
        self.assets = ["SPY"]  # Example asset, can be replaced with any
        self.interval = "1day"  # Time interval for data
        self.threshold = threshold
        self.zlsma_len = zlsma_len

    @property
    def data(self):
        # This is where you can specify additional data sources if needed.
        return []

    def calculate_zlsma(self, data):
        """Calculate ZLSMA."""
        ema1 = ta.ema(data['close'], length=self.zlsma_len)
        ema2 = ta.ema(ema1, length=self.zlsma_len)
        zlsma = ema1 + (ema1 - ema2)
        return zlsma

    def run(self, data):
        asset = self.assets[0]  # For simplicity, we're considering a single asset strategy.
        ohlcv = data['ohlcv'][asset]

        # Convert to DataFrame for easier handling
        df = pd.DataFrame(ohlcv)

        # Calculate ZLSMA
        df['ZLSMA'] = self.calculate_zlsma(df)
        
        # Calculate technical indicators
        df['EMA20'] = ta.ema(df['close'], length=20)
        df['EMA50'] = ta.ema(df['close'], length=50)
        df['MACD_hist'] = MACD(asset, ohlcv, 12, 29)['histogram'][-1]
        df['RSI'] = RSI(asset, ohlcv, length=14)
        df['TRIX'] = ta.trix(df['close'], length=15)
        df['Stoch_K'], df['Stoch_D'] = ta.stoch(df['high'], df['low'], df['close'])
        df['MFI'] = MFI(asset, ohlcv, length=14)
        df['ROC'] = ta.roc(df['close'], length=12)
        df['CMO'] = ta.cmo(df['close'], length=14)

        # Evaluate entry conditions based on technical indicators
        score = 0
        score += (df['close'].iloc[-1] > df['ZLSMA'].iloc[-1])
        score += (df['EMA20'].iloc[-1] > df['EMA50'].iloc[-1])
        score += (df['MACD_hist'] > 0)
        score += (df['RSI'].iloc[-1] > 50)
        score += (df['TRIX'].iloc[-2] < df['TRIX'].iloc[-1])  # TRIX is rising
        score += (df['Stoch_K'].iloc[-2] < df['Stoch_K'].iloc[-1])  # WillR approximation with Stochastic K
        score += (df['MFI'].iloc[-1] > 50)
        score += (df['Stoch_K'].iloc[-1] > 50)
        score += (df['ROC'].iloc[-1] > 0)
        score += (df['CMO'].iloc[-1] > 0)

        # Determine trade entry
        allocation = 0
        if score >= self.threshold:
            allocation = 1  # Full allocation to this asset

        # TODO: Implement dynamic stop-loss and trailing stop logic
        # TODO: Implement exit conditions based on the cross under of the ZLSMA or stop-loss breach, or if the price increases 5% above ZLSMA
        
        return TargetAllocation({asset: allocation})