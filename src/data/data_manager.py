import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np

class DataManager:
    """
    Handles financial data collection and processing.
    """
    
    def __init__(self, symbol: str = "EURUSD=X"):
        self.symbol = symbol

    def fetch_data(self, period: str = "60d", interval: str = "5m"):
        """
        Fetches historical data from Yahoo Finance.
        """
        print(f"Fetching data for {self.symbol}...")
        df = yf.download(self.symbol, period=period, interval=interval)
        if df.empty:
            raise ValueError(f"No data found for {self.symbol}")
        
        # Standardize column names to lowercase
        df.columns = [col.lower() for col in df.columns]
        return df

    def add_indicators(self, df: pd.DataFrame):
        """
        Adds 20+ technical indicators for ML training.
        """
        df = df.copy()
        
        # Trend Indicators
        df.ta.ema(length=9, append=True)
        df.ta.ema(length=20, append=True)
        df.ta.ema(length=50, append=True)
        df.ta.adx(append=True)
        
        # Momentum Indicators
        df.ta.rsi(length=14, append=True)
        df.ta.macd(append=True)
        df.ta.stoch(append=True)
        
        # Volatility Indicators
        df.ta.bbands(length=20, std=2, append=True)
        df.ta.atr(length=14, append=True)
        
        # Volume (if available)
        if 'volume' in df.columns and df['volume'].sum() > 0:
            df.ta.obv(append=True)
            df.ta.vwap(append=True)
            
        # Price Action / Returns
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        
        # Target variable: 1 if next close > current close, 0 otherwise
        df['target'] = (df['close'].shift(-1) > df['close']).astype(int)
        
        # Clean up NaNs
        df.dropna(inplace=True)
        
        return df

if __name__ == "__main__":
    dm = DataManager()
    data = dm.fetch_data(period="5d", interval="15m")
    data_with_indicators = dm.add_indicators(data)
    print(data_with_indicators.tail())
