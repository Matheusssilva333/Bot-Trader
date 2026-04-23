import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np

from src.utils.logger import setup_logger

logger = setup_logger("DataManager")

class DataManager:
    """
    Handles financial data collection and processing focusing on B3 (Mini Índice/Dólar).
    """
    
    def __init__(self, asset_type: str = "WDO"):
        # Proxies for B3: BRL=X (Dólar), ^BVSP (Índice Bovespa)
        self.asset_map = {
            "WDO": "BRL=X", # Proxy para tendência do Dólar
            "WIN": "^BVSP", # Proxy para tendência do Índice
            "DOLAR": "BRL=X"
        }
        self.asset_type = asset_type.upper()
        self.symbol = self.asset_map.get(self.asset_type, "BRL=X")

    def fetch_data(self, period: str = "7d", interval: str = "5m"):
        """
        Fetches historical data with fallbacks.
        """
        try:
            logger.info(f"Buscando dados para {self.asset_type} (Ticker: {self.symbol})...")
            df = yf.download(self.symbol, period=period, interval=interval, threads=False, progress=False)
            
            if df.empty or len(df) < 30:
                logger.warning(f"Dados insuficientes para {interval}. Tentando 15m...")
                df = yf.download(self.symbol, period="30d", interval="15m", threads=False, progress=False)

            if df.empty:
                logger.error(f"Erro crítico: Yahoo Finance retornou DataFrame vazio para {self.symbol}")
                raise ValueError(f"Ticker {self.symbol} não retornou dados.")

            # Fix for MultiIndex columns in new yfinance versions
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            df.columns = [col.lower() for col in df.columns]
            
            # Basic validation
            required = ['open', 'high', 'low', 'close']
            for col in required:
                if col not in df.columns:
                    raise ValueError(f"Coluna obrigatória {col} faltando nos dados.")
            
            return df
        except Exception as e:
            logger.error(f"Erro ao baixar dados: {e}")
            raise e

    def add_indicators(self, df: pd.DataFrame):
        """
        Adiciona indicadores focados em Volume, Preço e Topos/Fundos (Price Action).
        """
        df = df.copy()
        
        # 1. TENDÊNCIA DE PREÇO (Price)
        df.ta.ema(length=9, append=True)
        df.ta.ema(length=21, append=True)
        df.ta.macd(append=True)
        
        # 2. TOPOS E FUNDOS (Support & Resistance / Extremes)
        # Donchian Channels (identifica topos e fundos recentes)
        df.ta.donchian(lower_length=20, upper_length=20, append=True)
        # Bollinger Bands (Extremos de volatilidade)
        df.ta.bbands(length=20, std=2, append=True)
        
        # 3. VOLUME
        # Como índices/moedas no YF às vezes não têm volume, fazemos um fallback seguro
        if 'volume' in df.columns and df['volume'].sum() > 0:
            df.ta.vwap(append=True)
            df.ta.obv(append=True)
            df['volume_ema'] = df['volume'].ewm(span=20, adjust=False).mean()
        else:
            # Fake volume features se não existir para não quebrar o XGBoost
            df['vwap'] = df['close']
            df['obv'] = 0
            df['volume_ema'] = 0
            
        # Price Action / Returns
        df['returns'] = df['close'].pct_change()
        
        # Target variable: 1 se fechamento seguinte for maior que o atual (COMPRA), 0 se menor (VENDA)
        df['target'] = (df['close'].shift(-1) > df['close']).astype(int)
        
        # Clean up NaNs
        df.dropna(inplace=True)
        
        return df

if __name__ == "__main__":
    dm = DataManager()
    data = dm.fetch_data(period="5d", interval="15m")
    data_with_indicators = dm.add_indicators(data)
    print(data_with_indicators.tail())
