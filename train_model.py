from src.data.data_manager import DataManager
from src.models.predictor import TradingPredictor
from src.utils.logger import setup_logger
import os

logger = setup_logger("TrainModel")

def main():
    logger.info("--- Iniciando Treinamento do Modelo AI (Foco na B3) ---")
    
    # Train for WDO (Dólar) as an example, but you can iterate over both
    asset = "WDO" # Change to "WIN" for Mini Índice
    dm = DataManager(asset_type=asset) 
    
    # Fetch 60 days of 5m data for training
    try:
        data = dm.fetch_data(period="60d", interval="5m")
        processed_data = dm.add_indicators(data)
        
        predictor = TradingPredictor()
        acc, prec = predictor.train(processed_data)
        
        logger.info(f"\nTreinamento Finalizado!")
        logger.info(f"Acurácia: {acc:.2%}")
        logger.info(f"Precisão: {prec:.2%}")
        logger.info("O arquivo 'src/models/trading_model.json' foi gerado com sucesso.")
        
    except Exception as e:
        logger.error(f"Erro durante o treinamento: {e}")

if __name__ == "__main__":
    main()
