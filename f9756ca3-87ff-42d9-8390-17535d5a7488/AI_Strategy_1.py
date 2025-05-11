import numpy as np
from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import EMA

class TradingStrategy(Strategy):
    def __init__(self):
        self.assets = ["SPY"]
        self.interval = "1h"  # Interval adherence is important for the data

    @property
    def data(self):
        # This example doesn't use additional data sources but can be extended to include them
        return []

    def run(self, data):
        # Access OHLCV data for SPY
        df = data["ohlcv"]["SPY"]  # Assuming 'ohlcv' is structured with tickers as keys

        # Compute technical indicators, simplifying the computation with example functions
        ema_short = EMA("SPY", df, 20)
        ema_long = EMA("SPY", df, 50)

        score = np.zeros(len(df))
        # Simplified scoring logic based on two EMAs for demonstration
        score[ema_short > ema_long] = 1

        # Determine allocation based on the most recent score
        # This is a simple example; your logic could be more complex
        allocation = 0.0  # Default to no allocation
        if score[-1] >= 1:  # Arbitrary scoring logic
            allocation = 1.0  # Fully allocate if condition met

        # Return allocations in the expected format
        return TargetAllocation({"SPY": allocation})

# Instantiate and run your strategy outside..