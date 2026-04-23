import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np
import requests
from src.utils.logger import setup_logger

logger = setup_logger("DataManager")

class DataManager:
    """
    Handles financial data collection and processing focusing on B3 (Mini Índice/Dólar).
    """
    
    def __init__(self, asset_type: str = "WDO"):
        # Proxies for B3: USDBRL=X (Dólar), ^BVSP (Índice Bovespa)
        self.asset_map = {
            "WDO": "USDBRL=X", 
            "WIN": "^BVSP",
            "DOLAR": "USDBRL=X"
        }
        self.asset_type = asset_type.upper()
        self.symbol = self.asset_map.get(self.asset_type, "USDBRL=X")

    def fetch_data(self, period: str = "15d", interval: str = "5m"):
        """
        Fetches historical data with advanced fallbacks and browser emulation.
        """
        # Create a session with a User-Agent to avoid blocks on cloud environments
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

        try:
            logger.info(f"Buscando dados para {self.asset_type} (Ticker: {self.symbol})...")
            
            # Use the session in yfinance
            df = yf.download(
                self.symbol, 
                period=period, 
                interval=interval, 
                threads=False, 
                progress=False,
                session=session
            )
            
            # Fallback 1: Try a different interval if data is missing
            if df.empty or len(df) < 10:
                logger.warning(f"Dados insuficientes para {interval}. Tentando 15m...")
                df = yf.download(self.symbol, period="30d", interval="15m", threads=False, progress=False, session=session)

            # Fallback 2: Try an alternative ticker for WIN if ^BVSP fails
            if df.empty and self.asset_type == "WIN":
                logger.warning("Tentando ticker alternativo para WIN (EWZ)...")
                df = yf.download("EWZ", period="15d", interval="5m", threads=False, progress=False, session=session)

            if df.empty:
                logger.error(f"Não foi possível obter nenhum dado para {self.symbol}")
                raise ValueError(f"Ticker {self.symbol} sem dados.")

            # Fix for any column format (MultiIndex or Tuples)
            df.columns = [str(col[0] if isinstance(col, tuple) else col).lower() for col in df.columns]

            
            # Ensure index is datetime
            df.index = pd.to_datetime(df.index)
            
            # Fallback for missing Volume (Common in currencies/indexes on YF)
            if 'volume' not in df.columns or df['volume'].sum() == 0:
                df['volume'] = 1000 # Placeholder for indicators that require volume
            
            # Drop rows with all NaNs
            df.dropna(how='all', inplace=True)
            
            return df
        except Exception as e:
            logger.error(f"Erro no DataManager: {e}")
            raise e

    def add_indicators(self, df: pd.DataFrame):
        """
        Adiciona indicadores focados em Volume, Preço e Price Action.
        """
        df = df.copy()
        
        try:
            # 1. TENDÊNCIA
            df.ta.ema(length=9, append=True)
            df.ta.ema(length=21, append=True)
            
            # 2. VOLATILIDADE E EXTREMOS
            df.ta.bbands(length=20, std=2, append=True)
            df.ta.rsi(length=14, append=True)
            
            # 3. SUPORTE E RESISTÊNCIA
            df.ta.donchian(lower_length=20, upper_length=20, append=True)
            
            # Target variable (para o XGBoost)
            df['target'] = (df['close'].shift(-1) > df['close']).astype(int)
            
            # Limpar nulos gerados pelos indicadores
            df.dropna(inplace=True)
            
            if df.empty:
                logger.error("DataFrame ficou vazio após adicionar indicadores.")
                raise ValueError("Dados insuficientes para calcular indicadores.")
                
            return df
        except Exception as e:
            logger.error(f"Erro ao adicionar indicadores: {e}")
            raise e

if __name__ == "__main__":
    dm = DataManager()
    data = dm.fetch_data()
    data_with_indicators = dm.add_indicators(data)
    print(data_with_indicators.tail())
