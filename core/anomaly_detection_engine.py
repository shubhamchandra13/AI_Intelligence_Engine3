# ============================================================
# 🚨 ANOMALY DETECTION ENGINE - THE SAFETY GUARD (ZERO COST)
# Uses Isolation Forest to detect manipulative spikes/crashes.
# ============================================================

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
import warnings

warnings.filterwarnings("ignore")

class AnomalyDetectionEngine:
    def __init__(self, contamination=0.01):
        """
        contamination: Estimated % of outliers in data (1% is standard).
        """
        self.model = IsolationForest(contamination=contamination, random_state=42)
        self.is_trained = False

    def _prepare_features(self, df):
        if len(df) < 100: return None
        
        # Features: Price Velocity, Volume Spike, and Spread
        df['returns'] = df['close'].pct_change()
        df['vol_change'] = df['volume'].pct_change()
        df['range'] = (df['high'] - df['low']) / df['close']
        
        features = df[['returns', 'vol_change', 'range']].dropna()
        return features.values

    def check_anomaly(self, df):
        """
        Returns: { 'is_anomaly': bool, 'score': float, 'status': str }
        """
        try:
            X = self._prepare_features(df)
            if X is None:
                return {"is_anomaly": False, "score": 0.0, "status": "INITIALIZING"}

            # Fit on recent 500 candles to learn 'normal' behavior
            self.model.fit(X[-500:])
            
            # Predict latest candle
            # Result: 1 for normal, -1 for anomaly
            pred = self.model.predict(X[-1:])
            score = self.model.decision_function(X[-1:]) # Lower = more anomalous

            is_anomaly = True if pred[0] == -1 else False
            
            return {
                "is_anomaly": is_anomaly,
                "score": round(float(score[0]), 4),
                "status": "ANOMALY_DETECTED" if is_anomaly else "NORMAL"
            }

        except Exception:
            return {"is_anomaly": False, "score": 0.0, "status": "ERROR"}
