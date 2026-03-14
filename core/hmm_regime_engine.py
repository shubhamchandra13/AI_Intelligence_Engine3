# ============================================================
# 🧠 HMM REGIME DETECTION ENGINE - SILENT & STABLE
# Fixed: Suppresses all 'init_params' overwriting logs.
# ============================================================

import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
import warnings
import os
import sys
import contextlib

# Suppress HMM Warnings
warnings.filterwarnings("ignore")

@contextlib.contextmanager
def silence_stderr():
    """Temporarily redirects stderr to devnull to silence library logs."""
    new_target = open(os.devnull, "w")
    old_stderr = sys.stderr
    sys.stderr = new_target
    try:
        yield
    finally:
        sys.stderr = old_stderr
        new_target.close()

class HMMRegimeEngine:
    def __init__(self, n_states=3):
        self.n_states = n_states
        # Removed 'init_params' from constructor to prevent 'overwritten' logs
        self.model = GaussianHMM(
            n_components=n_states, 
            covariance_type="diag", 
            n_iter=50,
            random_state=42
        )
        self.is_trained = False

    def _prepare_features(self, df):
        if len(df) < 60:
            return None
        
        # 1. Log Returns
        returns = np.log(df['close'] / df['close'].shift(1)).dropna()
        
        # 2. Range (Volatility)
        range_pct = ((df['high'] - df['low']) / df['close']).shift(1).dropna()
        
        # Syncing features
        features = pd.concat([returns, range_pct], axis=1).dropna()
        features.columns = ['returns', 'range']
        
        data = features.values
        jitter = np.random.normal(0, 1e-8, data.shape)
        return data + jitter

    def detect_regime(self, df):
        try:
            X = self._prepare_features(df)
            if X is None or len(X) < 100:
                return {"state": -1, "label": "INITIALIZING", "confidence": 0.0}

            # Silencing the 'fit' method specifically
            with silence_stderr():
                self.model.fit(X)
            
            self.is_trained = True
            states = self.model.predict(X)
            current_state = int(states[-1])
            
            probs = self.model.predict_proba(X[-1:])
            confidence = float(np.max(probs))

            state_means = self.model.means_[:, 0]
            sorted_states = np.argsort(state_means)
            
            labels = {}
            labels[sorted_states[0]] = "HMM_BEARISH"
            labels[sorted_states[1]] = "HMM_SIDEWAYS"
            labels[sorted_states[2]] = "HMM_BULLISH"

            return {
                "state": current_state,
                "label": labels.get(current_state, "UNKNOWN"),
                "confidence": round(confidence * 100, 2)
            }

        except Exception:
            return {"state": -1, "label": "HMM_CALCULATING", "confidence": 0.0}

    def get_transition_matrix(self):
        if not self.is_trained: return None
        return self.model.transmat_
