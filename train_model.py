from src.data.data_manager import DataManager
from src.models.predictor import TradingPredictor
from src.utils.logger import setup_logger
import pandas as pd
import os

logger = setup_logger("TrainModel")

def main():
    logger.info("🚀 Iniciando Treinamento Profissional do Modelo Trading Pro AI...")
    
    # Lista de ativos para compor a base de dados do modelo
    assets = ["WDO", "WIN"]
    combined_data = []

    for asset in assets:
        logger.info(f"Coletando dados históricos para {asset}...")
        dm = DataManager(asset_type=asset) 
        try:
            # 60 dias é o máximo para 5m data no Yahoo Finance
            data = dm.fetch_data(period="60d", interval="5m")
            processed = dm.add_indicators(data)
            combined_data.append(processed)
            logger.info(f"✅ {asset}: {len(processed)} linhas processadas.")
        except Exception as e:
            logger.warning(f"⚠️ Falha ao coletar dados para {asset}: {e}")

    if not combined_data:
        logger.error("❌ Erro: Nenhum dado foi coletado para o treinamento.")
        return

    # Combina todos os dados em um único DataFrame para treinamento robusto
    df_final = pd.concat(combined_data)
    logger.info(f"📊 Base de dados final: {len(df_final)} linhas.")

    try:
        predictor = TradingPredictor()
        acc, prec = predictor.train(df_final)
        
        logger.info(f"✅ Treinamento Concluído com Sucesso!")
        logger.info(f"📈 Performance Média (Cross-Validation):")
        logger.info(f"   - Acurácia: {acc:.2%}")
        logger.info(f"   - Precisão: {prec:.2%}")
        
    except Exception as e:
        logger.error(f"❌ Erro fatal no treinamento: {e}")

if __name__ == "__main__":
    main()
