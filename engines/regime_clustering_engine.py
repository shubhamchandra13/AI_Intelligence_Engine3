import numpy as np
import pandas as pd
from datetime import datetime

class RegimeClusteringEngine:
    """
    Market Regime 2.0: Unsupervised Clustering Algorithm.
    Identifies 4 hidden 'Market Moods' using multi-dimensional price/volume data.
    """
    def __init__(self, lookback=200):
        self.lookback = lookback
        # Regime Definitions (Simulated Centroids for K-Means Lite)
        self.regimes = {
            0: {"name": "STEADY_TRENDING", "risk": "MODERATE", "target": "HIGH", "color": "green"},
            1: {"name": "HIGH_VOL_PANIC", "risk": "EXTREME", "target": "SCALPING", "color": "red"},
            2: {"name": "QUIET_SIDEWAYS", "risk": "LOW", "target": "MODERATE", "color": "blue"},
            3: {"name": "EXHAUSTION_REVERSAL", "risk": "HIGH", "target": "TIGHT", "color": "yellow"}
        }

    def detect_regime_v2(self, df):
        """
        Uses a mathematical clustering approach to identify the current market regime.
        """
        if df is None or len(df) < self.lookback:
            return {"regime": "SCANNING", "confidence": 0.5, "mood": "NEUTRAL"}

        # 1. Feature Engineering
        # Calculate returns, volatility (ATR), and volume relative to average
        returns = df['close'].pct_change(5).tail(self.lookback).values
        volatility = (df['high'] - df['low']).rolling(20).mean().tail(self.lookback).values
        volume_z = (df['volume'] - df['volume'].rolling(50).mean()) / df['volume'].rolling(50).std()
        volume_z = volume_z.tail(self.lookback).values

        # 2. Normalize and Handle NaNs
        def clean(arr):
            arr = np.nan_to_num(arr)
            if np.std(arr) > 0:
                return (arr - np.mean(arr)) / np.std(arr)
            return arr

        f1 = clean(returns)[-1]  # Momentum
        f2 = clean(volatility)[-1] # Volatility
        f3 = clean(volume_z)[-1]  # Volume Pressure

        # 3. K-Means Lite (Euclidean distance to 'Ideal' regime centers)
        # Centers [Momentum, Volatility, Volume]
        centers = {
            0: [1.5, -0.5, 0.5],   # Steady Trending (High Mom, Low Vol, Mod Volm)
            1: [-0.5, 2.0, 2.0],   # High Vol Panic (Low Mom, High Vol, High Volm)
            2: [0.0, -1.5, -1.0],  # Quiet Sideways (No Mom, No Vol, No Volm)
            3: [-1.5, 1.0, 0.0]    # Exhaustion (Negative Mom, Rising Vol)
        }

        distances = {}
        current_features = [f1, f2, f3]
        
        for idx, center in centers.items():
            dist = np.sqrt(np.sum((np.array(current_features) - np.array(center))**2))
            distances[idx] = dist

        # Find closest regime
        best_idx = min(distances, key=distances.get)
        regime_info = self.regimes[best_idx]
        
        # Confidence based on distance (closer = higher confidence)
        confidence = 1.0 / (1.0 + distances[best_idx])

        return {
            "regime": regime_info["name"],
            "risk_profile": regime_info["risk"],
            "target_profile": regime_info["target"],
            "confidence": round(confidence, 2),
            "features": {
                "momentum": round(f1, 2),
                "volatility": round(f2, 2),
                "volume_pressure": round(f3, 2)
            }
        }

    def get_strategy_adjustment(self, regime_data):
        """
        Returns multipliers for strategy parameters based on the detected regime.
        """
        regime = regime_data.get("regime")
        
        if regime == "STEADY_TRENDING":
            return {"sl_mult": 1.0, "tp_mult": 1.5, "trail_sl": True}
        elif regime == "HIGH_VOL_PANIC":
            return {"sl_mult": 1.5, "tp_mult": 0.8, "trail_sl": False}
        elif regime == "QUIET_SIDEWAYS":
            return {"sl_mult": 0.8, "tp_mult": 0.5, "trail_sl": False}
        elif regime == "EXHAUSTION_REVERSAL":
            return {"sl_mult": 1.2, "tp_mult": 1.0, "trail_sl": True}
            
        return {"sl_mult": 1.0, "tp_mult": 1.0, "trail_sl": False}
