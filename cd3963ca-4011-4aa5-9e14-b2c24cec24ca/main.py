from surmount.base_class import Strategy, TargetAllocation
from surmount.technical_indicators import SMA
from surmount.logging import log
from surmount.data import SocialSentiment

class TradingStrategy(Strategy):
    def __init__(self):
        # Define the tickers to monitor
        self.tickers = ["AAPL", "GOOGL", "MSFT", "TSLA"]

        # Add SocialSentiment data for each ticker to the data_list
        self.data_list = [SocialSentiment(ticker) for ticker in self.tickers]

    @property
    def interval(self):
        # Analyze daily social sentiment
        return "1day"

    @property
    def assets(self):
        # The assets being observed
        return self.tickers

    @property
    def data(self):
        # Data components required for this strategy
        return self.data_list

    def run(self, data):
        # Initialize allocation dictionary with no investment
        allocation_dict = {ticker: 0 for ticker in self.tickers}

        # Iterate over each ticker
        for ticker in self.tickers:
            # Accessing social sentiment data
            sentiment_data = data[("social_sentiment", ticker)]
            if sentiment_data and len(sentiment_data) >= 5:
                # Calculate the 5-day SMA of twitterSentiment
                sentiment_values = [d["twitterSentiment"] for d in sentiment_data[-5:]]
                sentiment_sma = sum(sentiment_values) / len(sentiment_values)
                
                # Determine if the latest sentiment is greater than the SMA
                current_sentiment = sentiment_values[-1]
                if current_sentiment > sentiment_sma:
                    log(f"Increasing sentiment for {ticker}, current: {current_sentiment}, SMA: {sentiment_sma}")
                    # Allocate a fraction if current sentiment is positive and trending up
                    allocation_dict[ticker] = 0.25  # Investing 25% per selected asset

        # Normalize allocations to not exceed total investment of 1
        total_allocation = sum(allocation_dict.values())
        if total_allocation > 1:
            allocation_dict = {ticker: alloc/total_allocation for ticker, alloc in allocation_dict.items()}

        return TargetAllocation(allocation_dict)