import numpy as np
import pandas as pd

class VolatilityForecaster:
    """
    GARCH(1,1) Volatility Forecasting Engine.
    Predicts future volatility clustering for institutional-grade SL/Target adjustment.
    """
    def __init__(self, window=100):
        self.window = window
        self.alpha = 0.05  # Weight on recent shocks (arch)
        self.beta = 0.90   # Weight on previous volatility (garch)
        self.omega = 0.05  # Long-run average volatility (omega = gamma * long_run_var)

    def forecast(self, df):
        """
        Calculates GARCH-style volatility forecast.
        """
        if df is None or len(df) < self.window:
            return {"forecast_vol": 0.0, "regime": "NORMAL", "confidence": "LOW"}

        # 1. Calculate Log Returns
        # We use 5-minute equivalent or 1-minute data returns
        returns = np.log(df['close'] / df['close'].shift(1)).dropna().tail(self.window).values
        
        # 2. Estimate current variance (sigma^2)
        # Using a simplified Recursive Variance approach (GARCH-Lite)
        # sigma_t^2 = omega + alpha * epsilon_{t-1}^2 + beta * sigma_{t-1}^2
        
        variances = []
        curr_var = np.var(returns) # Initial seed
        
        for r in returns:
            # epsilon^2 is the squared return (shock)
            new_var = self.omega + (self.alpha * (r**2)) + (self.beta * curr_var)
            variances.append(new_var)
            curr_var = new_var
            
        # 3. Forecast Next Period Volatility (Annualized)
        forecast_var = self.omega + (self.alpha * (returns[-1]**2)) + (self.beta * variances[-1])
        forecast_std = np.sqrt(forecast_var)
        
        # Annualize (assuming 1-minute candles, ~375 per day, 252 days)
        # We'll use a relative "Volatility Index" instead of raw % for easier logic
        vol_index = forecast_std * 1000 
        
        # 4. Detect Regime Change (Volatility Clustering)
        historical_std = np.std(returns)
        clustering_ratio = forecast_std / historical_std if historical_std > 0 else 1.0
        
        regime = "NORMAL"
        if clustering_ratio > 1.5: regime = "EXPANDING_SHOCK"
        elif clustering_ratio < 0.7: regime = "CALM_BEFORE_STORM"
        elif clustering_ratio > 1.2: regime = "HIGH_VOL_CLUSTER"

        return {
            "forecast_vol": round(vol_index, 3),
            "regime": regime,
            "clustering_ratio": round(clustering_ratio, 2),
            "risk_multiplier": round(clustering_ratio, 2) if clustering_ratio > 1.0 else 1.0,
            "target_multiplier": 1.2 if regime == "HIGH_VOL_CLUSTER" else 1.0
        }

    def get_sl_adjustment(self, forecast_res):
        """
        Returns a multiplier for Stop Loss based on volatility clustering.
        If high vol is predicted, SL needs to be wider to avoid noise.
        """
        ratio = forecast_res.get("clustering_ratio", 1.0)
        if ratio > 1.3:
            return 1.25 # 25% wider SL
        elif ratio > 1.1:
            return 1.10 # 10% wider SL
        return 1.0
