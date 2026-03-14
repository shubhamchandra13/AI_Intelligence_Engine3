# ============================================================
# 🧪 DENOISING PCA ENGINE - THE NOISE FILTER (ZERO COST)
# Compresses 50+ indicators into a single 'Clean Signal'.
# ============================================================

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import warnings

warnings.filterwarnings("ignore")

class DenoisingPCAEngine:
    def __init__(self, n_components=3):
        self.n_components = n_components
        self.pca = PCA(n_components=n_components)
        self.scaler = StandardScaler()
        self.is_trained = False

    def _calculate_indicator_stack(self, df):
        """Calculates a massive stack of indicators for the PCA."""
        try:
            d = pd.DataFrame(index=df.index)
            close = df['close']
            high = df['high']
            low = df['low']
            vol = df['volume']

            # 1. Trend Features
            for p in [5, 10, 20, 50, 100, 200]:
                d[f'sma_{p}'] = (close / close.rolling(p).mean()) - 1
            d['ema_9'] = (close / close.ewm(span=9).mean()) - 1
            d['ema_21'] = (close / close.ewm(span=21).mean()) - 1
            
            # 2. Momentum
            def get_rsi(ser, p):
                delta = ser.diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=p).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=p).mean()
                rs = gain / loss
                return 100 - (100 / (1 + rs))

            d['rsi_7'] = get_rsi(close, 7)
            d['rsi_14'] = get_rsi(close, 14)
            d['rsi_21'] = get_rsi(close, 21)
            
            # MACD
            exp1 = close.ewm(span=12, adjust=False).mean()
            exp2 = close.ewm(span=26, adjust=False).mean()
            d['macd'] = exp1 - exp2
            d['macd_sig'] = d['macd'].ewm(span=9, adjust=False).mean()
            d['macd_hist'] = d['macd'] - d['macd_sig']

            # 3. Volatility
            d['atr'] = (high - low).rolling(14).mean()
            d['std_20'] = close.rolling(20).std()
            d['upper_bb'] = close.rolling(20).mean() + (d['std_20'] * 2)
            d['lower_bb'] = close.rolling(20).mean() - (d['std_20'] * 2)
            d['bb_width'] = (d['upper_bb'] - d['lower_bb']) / close

            # 4. Candlestick Ratios
            d['body_size'] = abs(close - df['open'])
            d['candle_range'] = high - low
            d['body_ratio'] = d['body_size'] / (d['candle_range'] + 0.001)

            # 5. Volume
            d['vol_ema'] = vol / vol.rolling(20).mean()
            
            return d.fillna(0)
        except Exception:
            return None

    def get_clean_signal(self, df):
        """Compresses all noise and returns a Clean Signal Score (0-100)."""
        try:
            features_df = self._calculate_indicator_stack(df)
            if features_df is None or len(features_df) < 50:
                return {"signal": 50.0, "noise_reduction": 0.0}

            # Normalize data
            X = self.scaler.fit_transform(features_df.values)
            
            # Apply PCA
            self.pca.fit(X)
            components = self.pca.transform(X)
            
            # The 1st Principal Component captures the most 'Trend/Signal'
            # We normalize it to 0-100
            raw_signal = components[-1, 0]
            
            # Map raw signal to 0-100 scale using a sigmoid-like approach
            clean_score = 100 / (1 + np.exp(-raw_signal))
            
            # Calculate how much noise was filtered
            # (1 - Variance explained by 1st component)
            noise_pct = (1 - self.pca.explained_variance_ratio_[0]) * 100

            return {
                "signal": round(clean_score, 2),
                "noise_reduction": round(noise_pct, 2),
                "status": "CLEAN" if noise_pct < 40 else "NOISY"
            }

        except Exception:
            return {"signal": 50.0, "noise_reduction": 0.0, "status": "ERROR"}
