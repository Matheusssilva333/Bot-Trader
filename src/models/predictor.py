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
        Trains the model on provided historical data.
        """
        X, y = self.prepare_data(df)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
        
        print("Training model...")
        self.model.fit(X_train, y_train)
        
        # Validation
        preds = self.model.predict(X_test)
        acc = accuracy_score(y_test, preds)
        prec = precision_score(y_test, preds)
        
        print(f"Model Training Complete. Accuracy: {acc:.2%}, Precision: {prec:.2%}")
        self.save_model()
        return acc, prec

    def save_model(self):
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
