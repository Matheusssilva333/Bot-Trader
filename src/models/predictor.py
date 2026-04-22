import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score
import pandas as pd
import pickle
import os

class TradingPredictor:
    """
    ML Predictor for market direction using XGBoost.
    """
    
    def __init__(self, model_path: str = "src/models/trading_model.json"):
        self.model_path = model_path
        self.model = xgb.XGBClassifier(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=6,
            random_state=42,
            use_label_encoder=False,
            eval_metric='logloss'
        )

    def prepare_data(self, df: pd.DataFrame):
        """
        Splits data into features (X) and target (y).
        """
        # Drop non-feature columns
        X = df.drop(columns=['target'])
        y = df['target']
        return X, y

    def train(self, df: pd.DataFrame):
        """
        Trains the model on provided historical data with TimeSeries cross-validation.
        """
        from sklearn.model_selection import TimeSeriesSplit
        import numpy as np
        
        X, y = self.prepare_data(df)
        
        tscv = TimeSeriesSplit(n_splits=5)
        acc_scores = []
        prec_scores = []
        
        print("Realizando validação cruzada (TimeSeriesSplit)...")
        for train_index, test_index in tscv.split(X):
            X_train, X_test = X.iloc[train_index], X.iloc[test_index]
            y_train, y_test = y.iloc[train_index], y.iloc[test_index]
            
            self.model.fit(X_train, y_train)
            preds = self.model.predict(X_test)
            
            acc_scores.append(accuracy_score(y_test, preds))
            # Handle zero division if a model predicts all one class
            prec_scores.append(precision_score(y_test, preds, zero_division=0))
            
        avg_acc = np.mean(acc_scores)
        avg_prec = np.mean(prec_scores)
        
        print(f"Validação Completa. Acurácia Média: {avg_acc:.2%}, Precisão Média: {avg_prec:.2%}")
        
        print("Treinando modelo final com todos os dados...")
        self.model.fit(X, y)
        self.save_model()
        return avg_acc, avg_prec

    def save_model(self):
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        self.model.save_model(self.model_path)
        print(f"Model saved to {self.model_path}")

    def load_model(self):
        if os.path.exists(self.model_path):
            self.model.load_model(self.model_path)
            print("Model loaded successfully.")
            return True
        return False

    def predict_next(self, current_data_row: pd.DataFrame):
        """
        Predicts the direction of the next candle.
        Returns (Prediction, Probability)
        """
        # Ensure only feature columns are passed
        X = current_data_row.copy()
        if 'target' in X.columns:
            X = X.drop(columns=['target'])
            
        prob = self.model.predict_proba(X)[0][1]
        prediction = 1 if prob > 0.5 else 0
        return prediction, prob
