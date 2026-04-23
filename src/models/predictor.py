import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score
from sklearn.preprocessing import StandardScaler
import pandas as pd
import pickle
import os
import joblib

class TradingPredictor:
    """
    ML Predictor for market direction using XGBoost with Scaling.
    """
    
    def __init__(self, model_path: str = "src/models/trading_model.json", scaler_path: str = "src/models/scaler.joblib"):
        self.model_path = model_path
        self.scaler_path = scaler_path
        self.scaler = StandardScaler()
        self.model = xgb.XGBClassifier(
            n_estimators=300,
            learning_rate=0.03,
            max_depth=8,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            eval_metric='logloss'
        )

    def prepare_data(self, df: pd.DataFrame, is_training: bool = False):
        """
        Splits data into features (X) and target (y).
        Scales features if scaler is available.
        """
        X = df.drop(columns=['target']) if 'target' in df.columns else df
        
        if is_training:
            X_scaled = self.scaler.fit_transform(X)
            # Save scaler for inference
            os.makedirs(os.path.dirname(self.scaler_path), exist_ok=True)
            joblib.dump(self.scaler, self.scaler_path)
            return pd.DataFrame(X_scaled, columns=X.columns), df['target']
        else:
            if os.path.exists(self.scaler_path):
                self.scaler = joblib.load(self.scaler_path)
                X_scaled = self.scaler.transform(X)
                return pd.DataFrame(X_scaled, columns=X.columns)
            return X

    def train(self, df: pd.DataFrame):
        """
        Trains the model on provided historical data with TimeSeries cross-validation.
        """
        from sklearn.model_selection import TimeSeriesSplit
        import numpy as np
        
        X, y = self.prepare_data(df, is_training=True)
        
        tscv = TimeSeriesSplit(n_splits=5)
        acc_scores = []
        prec_scores = []
        
        print("Realizando validação cruzada profissional...")
        for train_index, test_index in tscv.split(X):
            X_train, X_test = X.iloc[train_index], X.iloc[test_index]
            y_train, y_test = y.iloc[train_index], y.iloc[test_index]
            
            self.model.fit(X_train, y_train)
            preds = self.model.predict(X_test)
            
            acc_scores.append(accuracy_score(y_test, preds))
            prec_scores.append(precision_score(y_test, preds, zero_division=0))
            
        avg_acc = np.mean(acc_scores)
        avg_prec = np.mean(prec_scores)
        
        print(f"Treinando modelo final. Acurácia: {avg_acc:.2%}")
        self.model.fit(X, y)
        self.save_model()
        return avg_acc, avg_prec

    def save_model(self):
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        self.model.save_model(self.model_path)

    def load_model(self):
        if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
            self.model.load_model(self.model_path)
            self.scaler = joblib.load(self.scaler_path)
            return True
        return False

    def predict_next(self, current_data_row: pd.DataFrame):
        """
        Predicts the direction of the next candle with confidence scaling.
        """
        try:
            X = self.prepare_data(current_data_row, is_training=False)
            
            prob = self.model.predict_proba(X)[0][1]
            prediction = 1 if prob > 0.5 else 0
            return prediction, prob
        except Exception as e:
            print(f"Erro na predição: {e}")
            return 0, 0.5
