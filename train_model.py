from src.data.data_manager import DataManager
from src.models.predictor import TradingPredictor
import os

def main():
    print("--- Inciando Treinamento do Modelo AI ---")
    dm = DataManager(symbol="EURUSD=X") # Example asset
    
    # Fetch 60 days of 5m data for training
    try:
        data = dm.fetch_data(period="60d", interval="5m")
        processed_data = dm.add_indicators(data)
        
        predictor = TradingPredictor()
        acc, prec = predictor.train(processed_data)
        
        print(f"\nTreinamento Finalizado!")
        print(f"Acurácia: {acc:.2%}")
        print(f"Precisão: {prec:.2%}")
        print("\nO arquivo 'src/models/trading_model.json' foi gerado com sucesso.")
        
    except Exception as e:
        print(f"Erro durante o treinamento: {e}")

if __name__ == "__main__":
    main()
