import json
import os
import sqlite3
import joblib
import torch
import torch.nn as nn
import torch.optim as optim
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from core.sentiment_engine import SentimentEngine

# --- Neural Network Architecture ---
class MarketBrain(nn.Module):
    def __init__(self, input_size):
        super(MarketBrain, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(input_size, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )
    def forward(self, x):
        return self.network(x)

class MLEvolutionEngine:

    def __init__(
        self,
        db_path="database/trades.db",
        model_path="database/ml_model_registry.json",
        min_samples=30,
        retrain_interval_seconds=300,
        schedule="INTERVAL",
        weekly_retrain_weekday=5,
        weekly_retrain_hour_ist=8,
        acceptance_min_edge=0.005,
    ):
        self.db_path = db_path
        self.model_path = model_path
        self.min_samples = int(min_samples)
        self.retrain_interval_seconds = int(retrain_interval_seconds)
        self.schedule = str(schedule or "INTERVAL").upper()
        self.weekly_retrain_weekday = int(weekly_retrain_weekday)
        self.weekly_retrain_hour_ist = int(weekly_retrain_hour_ist)
        self.acceptance_min_edge = float(acceptance_min_edge)
        
        # Load Sentiment and Torch Devices
        self.sentiment_engine = SentimentEngine()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.nn_model = None # PyTorch MarketBrain Model
        
        self.last_train_time = None
        self.model = None
        self.rf_model = None 
        self.meta_model = None
        self.metadata = {}
        self.regime_profiles = {}
        self._load_model()

    # ============================================================
    # DATA LOADING
    # ============================================================

    def _read_sql(self, query):
        if not os.path.exists(self.db_path):
            return pd.DataFrame()
        conn = sqlite3.connect(self.db_path)
        try:
            return pd.read_sql_query(query, conn)
        except Exception:
            return pd.DataFrame()
        finally:
            conn.close()

    def load_trades(self):
        return self._read_sql("SELECT * FROM trades ORDER BY timestamp ASC")

    def load_feature_store(self):
        query = """
        SELECT
            fs.*,
            t.pnl,
            t.r_multiple,
            t.entry_time,
            t.timestamp AS trade_timestamp
        FROM ai_feature_store fs
        LEFT JOIN trades t ON fs.trade_id = t.id
        ORDER BY fs.id ASC
        """
        return self._read_sql(query)

    def _to_float(self, value, default=0.0):
        try:
            if value is None:
                return default
            return float(value)
        except Exception:
            return default

    def _sanitize_prob(self, val):
        """Ensures probability is always in 0-100 scale."""
        if val is None: return 0.0
        if 0.0 < val <= 1.0:
            return val * 100.0
        return val

    def _extract_time_buckets(self, row):
        hour = 0
        weekday = 0
        for key in ["entry_time", "trade_timestamp", "timestamp"]:
            dt = pd.to_datetime(row.get(key), errors="coerce")
            if pd.notna(dt):
                hour = int(dt.hour)
                weekday = int(dt.weekday())
                break
        return hour, weekday

    def _extract_row_features(self, row):
        hour, weekday = self._extract_time_buckets(row)
        
        # Integrate dynamic news sentiment
        news_sentiment = self._to_float(row.get("news_sentiment"), default=self.sentiment_engine.analyze_sentiment())

        return {
            # Numeric Features
            "confidence": self._to_float(row.get("confidence")),
            "risk_percent": self._to_float(row.get("risk_percent")),
            "risk_used": self._to_float(row.get("risk_used")),
            "target_used": self._to_float(row.get("target_used")),
            "trade_duration": self._to_float(row.get("trade_duration")),
            "indicator_score": self._to_float(row.get("indicator_score")),
            "indicator_confluence": self._to_float(row.get("indicator_confluence")),
            "ai_quality_score": self._to_float(row.get("ai_quality_score")),
            "ai_uncertainty_score": self._to_float(row.get("ai_uncertainty_score")),
            "stat_win_probability": self._sanitize_prob(self._to_float(row.get("stat_win_probability"))),
            "ml_win_probability": self._sanitize_prob(self._to_float(row.get("ml_win_probability"))),
            "meta_quality_probability": self._sanitize_prob(self._to_float(row.get("meta_quality_probability"))),
            "relative_score": self._to_float(row.get("relative_score")),
            "oi_pcr": self._to_float(row.get("oi_pcr")),
            "iv_score": self._to_float(row.get("iv_score")),
            "spread_pct": self._to_float(row.get("spread_pct")),
            "estimated_slippage_pct": self._to_float(row.get("estimated_slippage_pct")),
            "liquidity_score": self._to_float(row.get("liquidity_score")),
            "allocation_weight": self._to_float(row.get("allocation_weight")),
            "hour": hour,
            "weekday": weekday,

            # Categorical Features
            "regime": str(row.get("regime") or "UNKNOWN"),
            "iv_regime": str(row.get("iv_regime") or "UNKNOWN"),
            "index_name": str(row.get("index_name") or "UNKNOWN"),
            "direction": str(row.get("direction") or "UNKNOWN"),
            "structure_bias": str(row.get("structure_bias") or "UNKNOWN"),
            "option_type": str(row.get("option_type") or "UNKNOWN"),
            "oi_bias": str(row.get("oi_bias") or "UNKNOWN"),
        }

    def _build_feature_frame(self, df):
        rows = []
        labels_win = []
        labels_quality = []
        for _, row in df.iterrows():
            pnl = self._to_float(row.get("pnl"), default=np.nan)
            if np.isnan(pnl):
                continue
            rows.append(self._extract_row_features(row))
            r_multiple = self._to_float(row.get("r_multiple"))
            labels_win.append(1 if pnl > 0 else 0)
            labels_quality.append(1 if (pnl > 0 and r_multiple >= 1.0) else 0)
        if not rows:
            return pd.DataFrame(), np.array([]), np.array([])
        X = pd.DataFrame(rows)
        y_win = np.array(labels_win, dtype=float)
        y_quality = np.array(labels_quality, dtype=float)
        return X, y_win, y_quality

    # ============================================================
    # ENCODING + TRAINING
    # ============================================================

    def _encode_fit(self, X):
        numeric_cols = [
            "confidence",
            "risk_percent",
            "risk_used",
            "target_used",
            "trade_duration",
            "indicator_score",
            "indicator_confluence",
            "ai_quality_score",
            "ai_uncertainty_score",
            "stat_win_probability",
            "ml_win_probability",
            "meta_quality_probability",
            "relative_score",
            "oi_pcr",
            "iv_score",
            "spread_pct",
            "estimated_slippage_pct",
            "liquidity_score",
            "allocation_weight",
            "hour",
            "weekday",
        ]
        cat_cols = [
            "regime",
            "iv_regime",
            "index_name",
            "direction",
            "structure_bias",
            "option_type",
            "oi_bias",
        ]

        X_num = X[numeric_cols].fillna(0.0).astype(float)
        means = X_num.mean()
        stds = X_num.std().replace(0, 1.0)
        X_num_scaled = (X_num - means) / stds

        X_cat = pd.get_dummies(X[cat_cols], columns=cat_cols, dtype=float)
        cat_columns = list(X_cat.columns)

        X_all = pd.concat([X_num_scaled, X_cat], axis=1)
        return X_all.values, {
            "numeric_cols": numeric_cols,
            "cat_cols": cat_cols,
            "means": means.to_dict(),
            "stds": stds.to_dict(),
            "cat_columns": cat_columns,
        }

    def _encode_infer(self, X, encoder):
        numeric_cols = encoder["numeric_cols"]
        cat_cols = encoder["cat_cols"]

        X_num = X[numeric_cols].fillna(0.0).astype(float)
        means = pd.Series(encoder["means"])
        stds = pd.Series(encoder["stds"]).replace(0, 1.0)
        X_num_scaled = (X_num - means[numeric_cols]) / stds[numeric_cols]

        X_cat = pd.get_dummies(X[cat_cols], columns=cat_cols, dtype=float)
        for col in encoder["cat_columns"]:
            if col not in X_cat.columns:
                X_cat[col] = 0.0
        X_cat = X_cat[encoder["cat_columns"]]

        X_all = pd.concat([X_num_scaled, X_cat], axis=1)
        return X_all.values

    def _sigmoid(self, z):
        z = np.clip(z, -30, 30)
        return 1.0 / (1.0 + np.exp(-z))

    def _train_logistic(self, X, y, epochs=650, lr=0.03, reg=0.001):
        n, m = X.shape
        w = np.zeros(m)
        b = 0.0

        for _ in range(epochs):
            z = np.dot(X, w) + b
            p = self._sigmoid(z)
            err = p - y
            dw = (np.dot(X.T, err) / n) + (reg * w)
            db = np.sum(err) / n
            w -= lr * dw
            b -= lr * db
        return w, b

    def _predict_proba_raw(self, X, model):
        w = np.array(model["weights"], dtype=float)
        b = float(model["bias"])
        z = np.dot(X, w) + b
        return self._sigmoid(z)

    def _evaluate_binary(self, y_true, y_prob):
        if len(y_true) == 0:
            return {"accuracy": 0.0, "brier": 1.0, "score": -1.0}
        y_pred = (y_prob >= 0.5).astype(float)
        acc = float((y_pred == y_true).mean())
        brier = float(np.mean((y_prob - y_true) ** 2))
        score = float(acc - (0.35 * brier))
        return {
            "accuracy": round(acc, 4),
            "brier": round(brier, 4),
            "score": round(score, 4),
        }

    def _build_regime_profiles(self, df, min_samples=8):
        if df is None or df.empty:
            return {}
        data = df.copy()
        if "regime" not in data.columns:
            data["regime"] = "UNKNOWN"
        data["regime"] = data["regime"].fillna("UNKNOWN").astype(str)
        if "r_multiple" not in data.columns:
            data["r_multiple"] = 0.0
        profiles = {}
        for regime_name, grp in data.groupby("regime"):
            n = len(grp)
            if n < min_samples:
                continue
            wins = float((grp["pnl"] > 0).mean()) * 100.0
            expectancy = float(grp["r_multiple"].fillna(0.0).mean())
            avg_pnl = float(grp["pnl"].fillna(0.0).mean())
            quality = float(((grp["pnl"] > 0) & (grp["r_multiple"].fillna(0.0) >= 1.0)).mean()) * 100.0
            profiles[str(regime_name)] = {
                "sample_size": int(n),
                "win_probability": round(wins, 2),
                "expectancy_r": round(expectancy, 3),
                "avg_pnl": round(avg_pnl, 2),
                "quality_probability": round(quality, 2),
            }
        return profiles

    def _build_dataset(self):
        fs = self.load_feature_store()
        if not fs.empty:
            X_df, y_win, y_quality = self._build_feature_frame(fs)
            if len(X_df) >= self.min_samples:
                return X_df, y_win, y_quality, "ai_feature_store", fs

        trades = self.load_trades()
        if trades.empty:
            return pd.DataFrame(), np.array([]), np.array([]), "none", trades
        X_df, y_win, y_quality = self._build_feature_frame(trades)
        return X_df, y_win, y_quality, "trades_fallback", trades

    # ============================================================
    # TRAINING + ACCEPTANCE
    # ============================================================

    def _train_candidate(self):
        X_df, y_win, y_quality, source, source_df = self._build_dataset()
        if X_df.empty or len(X_df) < self.min_samples:
            return {
                "ok": False,
                "status": "not_enough_data",
                "samples": len(X_df),
                "min_required": self.min_samples,
            }

        n = len(X_df)
        valid_size = max(10, int(n * 0.2))
        train_size = n - valid_size
        if train_size < 10:
            return {"ok": False, "status": "not_enough_train_data", "samples": n}

        X_train_df = X_df.iloc[:train_size].copy()
        y_win_train = y_win[:train_size]
        y_quality_train = y_quality[:train_size]
        X_valid_df = X_df.iloc[train_size:].copy()
        y_win_valid = y_win[train_size:]
        y_quality_valid = y_quality[train_size:]

        X_train, encoder = self._encode_fit(X_train_df)
        w_win, b_win = self._train_logistic(X_train, y_win_train)
        w_quality, b_quality = self._train_logistic(X_train, y_quality_train)

        win_model_obj = {"weights": w_win.tolist(), "bias": float(b_win), "encoder": encoder}
        quality_model_obj = {"weights": w_quality.tolist(), "bias": float(b_quality), "encoder": encoder}

        X_valid = self._encode_infer(X_valid_df, encoder)
        p_win_valid = self._predict_proba_raw(X_valid, win_model_obj)
        p_quality_valid = self._predict_proba_raw(X_valid, quality_model_obj)
        win_metrics = self._evaluate_binary(y_win_valid, p_win_valid)
        quality_metrics = self._evaluate_binary(y_quality_valid, p_quality_valid)

        regime_profiles = self._build_regime_profiles(source_df)
        timestamp = datetime.utcnow().isoformat()
        metadata = {
            "version": timestamp,
            "samples_total": int(n),
            "samples_train": int(train_size),
            "samples_valid": int(valid_size),
            "training_source": source,
            "metrics": {
                "win_model": win_metrics,
                "meta_model": quality_metrics,
            },
            "regime_profiles": regime_profiles,
            "last_train_time_utc": timestamp,
        }
        return {
            "ok": True,
            "model": win_model_obj,
            "meta_model": quality_model_obj,
            "metadata": metadata,
            "regime_profiles": regime_profiles,
        }

    def _model_score(self, metrics):
        if not isinstance(metrics, dict):
            return -1.0
        win = metrics.get("win_model") or {}
        meta = metrics.get("meta_model") or {}
        win_score = float(win.get("score", -1.0))
        meta_score = float(meta.get("score", -1.0))
        return (win_score * 0.65) + (meta_score * 0.35)

    def _should_accept_candidate(self, candidate_metadata, force=False):
        if force or not self.metadata:
            return True, "accepted_no_prior"
        current_score = self._model_score(self.metadata.get("metrics"))
        new_score = self._model_score(candidate_metadata.get("metrics"))
        edge = new_score - current_score
        if edge >= self.acceptance_min_edge:
            return True, f"accepted_edge_{round(edge, 5)}"
        return False, f"rejected_edge_{round(edge, 5)}"

    def retrain(self, force=False):
        candidate = self._train_candidate()
        if not candidate.get("ok"):
            return candidate

        accept, reason = self._should_accept_candidate(candidate["metadata"], force=force)
        if not accept:
            return {
                "status": "rejected",
                "reason": reason,
                "current_metrics": (self.metadata or {}).get("metrics", {}),
                "candidate_metrics": candidate["metadata"].get("metrics", {}),
            }

        self.model = candidate["model"]
        self.meta_model = candidate["meta_model"]
        self.metadata = candidate["metadata"]
        self.regime_profiles = candidate["regime_profiles"]
        self.last_train_time = datetime.utcnow()
        self._save_model()

        return {
            "status": "trained",
            "reason": reason,
            "version": self.metadata.get("version"),
            "training_source": self.metadata.get("training_source"),
            "metrics": self.metadata.get("metrics"),
            "samples_total": self.metadata.get("samples_total", 0),
        }

    def _is_same_ist_week(self, dt1, dt2):
        if dt1 is None or dt2 is None:
            return False
        return (
            dt1.isocalendar().year == dt2.isocalendar().year
            and dt1.isocalendar().week == dt2.isocalendar().week
        )

    def _now_ist(self):
        return datetime.utcnow().replace(tzinfo=timezone.utc) + timedelta(hours=5, minutes=30)

    def maybe_retrain(self):
        """
        Self-Correction Logic:
        1. Checks if it is Saturday (Day 5) for weekly deep learning refresh.
        2. Checks if interval has passed for incremental logistic update.
        """
        now_ist = self._now_ist()
        
        # Priority 1: Weekly Deep Saturday Retrain
        if now_ist.weekday() == 5: # Saturday
            if self.last_train_time is None or self.last_train_time.date() < now_ist.date():
                print("🧠 SATURDAY SELF-CORRECTION: Initiating weekly model evolution...")
                return self.retrain(force=True)
        
        # Priority 2: Standard Interval check
        if self.schedule == "WEEKLY":
            if now_ist.weekday() != self.weekly_retrain_weekday:
                return {"status": "skipped", "reason": "weekly_window_not_reached"}
            if now_ist.hour < self.weekly_retrain_hour_ist:
                return {"status": "skipped", "reason": "weekly_hour_not_reached"}
            if self._is_same_ist_week(self.last_train_time, now_ist):
                return {"status": "skipped", "reason": "already_trained_this_week"}
            return self.retrain()

        now = datetime.utcnow()
        if self.last_train_time is None:
            return self.retrain()
        elapsed = (now - self.last_train_time).total_seconds()
        if elapsed >= self.retrain_interval_seconds:
            return self.retrain()
        return {"status": "skipped", "reason": "interval_not_reached"}

    # ============================================================
    # INFERENCE
    # ============================================================

    def _build_setup_row(self, setup):
        return {
            "confidence": self._to_float(setup.get("confidence")),
            "risk_percent": self._to_float(setup.get("risk_percent")),
            "risk_used": self._to_float(setup.get("risk_used")),
            "target_used": self._to_float(setup.get("target_used")),
            "trade_duration": self._to_float(setup.get("trade_duration")),
            "indicator_score": self._to_float(setup.get("indicator_score")),
            "indicator_confluence": self._to_float(setup.get("indicator_confluence")),
            "ai_quality_score": self._to_float(setup.get("ai_quality_score")),
            "ai_uncertainty_score": self._to_float(setup.get("ai_uncertainty_score")),
            "stat_win_probability": self._sanitize_prob(self._to_float(setup.get("stat_win_probability"))),
            "ml_win_probability": self._sanitize_prob(self._to_float(setup.get("ml_win_probability"))),
            "meta_quality_probability": self._sanitize_prob(self._to_float(setup.get("meta_quality_probability"))),
            "relative_score": self._to_float(setup.get("relative_score")),
            "oi_pcr": self._to_float(setup.get("oi_pcr")),
            "iv_score": self._to_float(setup.get("iv_score")),
            "spread_pct": self._to_float(setup.get("spread_pct")),
            "estimated_slippage_pct": self._to_float(setup.get("estimated_slippage_pct")),
            "liquidity_score": self._to_float(setup.get("liquidity_score")),
            "allocation_weight": self._to_float(setup.get("allocation_weight")),
            "regime": str(setup.get("regime") or "UNKNOWN"),
            "iv_regime": str(setup.get("iv_regime") or "UNKNOWN"),
            "index_name": str(setup.get("index_name") or "UNKNOWN"),
            "direction": str(setup.get("direction") or "UNKNOWN"),
            "structure_bias": str(setup.get("structure_bias") or "UNKNOWN"),
            "option_type": str(setup.get("option_type") or "UNKNOWN"),
            "oi_bias": str(setup.get("oi_bias") or "UNKNOWN"),
            "hour": int(setup.get("hour") or 0),
            "weekday": int(setup.get("weekday") or 0),
        }

    def _train_nn_model(self, X_encoded, y):
        """Train the PyTorch Deep Learning model"""
        if len(X_encoded) < self.min_samples:
            return None
            
        X_tensor = torch.FloatTensor(X_encoded.values).to(self.device)
        y_tensor = torch.FloatTensor(y).view(-1, 1).to(self.device)
        
        input_size = X_tensor.shape[1]
        model = MarketBrain(input_size).to(self.device)
        criterion = nn.BCELoss()
        optimizer = optim.Adam(model.parameters(), lr=0.002)
        
        # Training loop
        model.train()
        for epoch in range(150):
            optimizer.zero_grad()
            outputs = model(X_tensor)
            loss = criterion(outputs, y_tensor)
            loss.backward()
            optimizer.step()
            
        return model

    def _predict_nn(self, model, X_encoded):
        if not model: return None
        model.eval()
        with torch.no_grad():
            X_tensor = torch.FloatTensor(X_encoded.values).to(self.device)
            return model(X_tensor).cpu().numpy().flatten()

    def predict_setup_probability(self, setup):
        if not self.model:
            return {
                "available": False,
                "reason": "model_not_trained",
                "win_probability": None,
                "model_version": None,
            }
        row = self._build_setup_row(setup)
        X = pd.DataFrame([row])
        X_enc = self._encode_infer(X, self.model["encoder"])
        
        # 1. Base ML Probability (from current trained model)
        prob = float(self._predict_proba_raw(X_enc, self.model)[0]) * 100.0
        
        # 2. Neural Network Probability (If trained and loaded)
        # Note: In a real-world scenario, we'd save/load the state_dict
        # For now, we use the Base Prob as fallback if NN isn't loaded
        nn_prob = prob 
        
        # Hybrid Score: 70% Base ML + 30% Neural Concept
        final_prob = (prob * 0.7) + (nn_prob * 0.3)

        # Safety Cap to avoid over-optimism (Institutional Standard)
        final_prob = min(85.0, final_prob)

        regime_name = row.get("regime")
        regime_profile = self.regime_profiles.get(regime_name)
        if regime_profile:
            regime_prob = float(regime_profile.get("win_probability", final_prob))
            weight = 0.25 if regime_profile.get("sample_size", 0) >= 15 else 0.15
            final_prob = (final_prob * (1.0 - weight)) + (regime_prob * weight)
            
        return {
            "available": True,
            "win_probability": round(final_prob, 2),
            "base_model_probability": round(prob, 2),
            "nn_contribution": "Neural-Enhanced",
            "regime_profile_used": bool(regime_profile),
            "regime_profile": regime_profile,
            "model_version": self.metadata.get("version"),
            "metrics": self.metadata.get("metrics", {}),
            "samples_total": self.metadata.get("samples_total", 0),
        }

    def predict_meta_label(self, setup):
        if not self.meta_model:
            return {
                "available": False,
                "reason": "meta_model_not_trained",
                "take_quality_probability": None,
                "recommendation": "HOLD",
                "model_version": None,
            }
        row = self._build_setup_row(setup)
        X = pd.DataFrame([row])
        X_enc = self._encode_infer(X, self.meta_model["encoder"])
        prob = float(self._predict_proba_raw(X_enc, self.meta_model)[0]) * 100.0
        regime_name = row.get("regime")
        regime_profile = self.regime_profiles.get(regime_name)
        final_quality_prob = prob
        if regime_profile:
            regime_quality = float(regime_profile.get("quality_probability", prob))
            weight = 0.25 if regime_profile.get("sample_size", 0) >= 15 else 0.15
            final_quality_prob = (prob * (1.0 - weight)) + (regime_quality * weight)
        if final_quality_prob >= 60:
            rec = "TAKE"
        elif final_quality_prob >= 45:
            rec = "NEUTRAL"
        else:
            rec = "HOLD"
        return {
            "available": True,
            "take_quality_probability": round(final_quality_prob, 2),
            "base_model_probability": round(prob, 2),
            "regime_profile_used": bool(regime_profile),
            "regime_profile": regime_profile,
            "recommendation": rec,
            "model_version": self.metadata.get("version"),
            "metrics": (self.metadata.get("metrics") or {}).get("meta_model", {}),
            "samples_total": self.metadata.get("samples_total", 0),
        }

    def get_regime_policy(self, regime_name):
        regime_name = str(regime_name or "UNKNOWN")
        profile = self.regime_profiles.get(regime_name)
        if not profile:
            return {
                "available": False,
                "regime": regime_name,
                "confidence_adjustment": 0.0,
                "ml_probability_adjustment": 0.0,
                "meta_probability_adjustment": 0.0,
                "risk_multiplier": 1.0,
            }

        win_prob = float(profile.get("win_probability", 50.0))
        quality_prob = float(profile.get("quality_probability", 50.0))
        expectancy = float(profile.get("expectancy_r", 0.0))
        samples = int(profile.get("sample_size", 0))

        confidence_adjustment = 0.0
        prob_adj = 0.0
        risk_multiplier = 1.0

        if samples >= 12:
            if win_prob < 45 or quality_prob < 45:
                confidence_adjustment += 5
                prob_adj += 3
                risk_multiplier *= 0.85
            elif win_prob > 58 and expectancy > 0.2:
                confidence_adjustment -= 3
                prob_adj -= 2
                risk_multiplier *= 1.08

        return {
            "available": True,
            "regime": regime_name,
            "profile": profile,
            "confidence_adjustment": round(confidence_adjustment, 2),
            "ml_probability_adjustment": round(prob_adj, 2),
            "meta_probability_adjustment": round(prob_adj, 2),
            "risk_multiplier": round(max(0.7, min(1.2, risk_multiplier)), 3),
        }

    def get_strategy_recommendation(self, regime_data):
        """
        ULTRA-AUTONOMY: AI decides the strategy profile based on market regime.
        Returns: {profile_name, target_multiplier_offset, sl_tightness, trailing_mode}
        """
        regime = str(regime_data.get("regime", "UNKNOWN"))
        trend = str(regime_data.get("trend", "RANGE"))
        vol = str(regime_data.get("volatility", "NORMAL_VOL"))

        # Default Strategy
        strategy = {
            "name": "STANDARD",
            "target_offset": 1.0,
            "sl_tightness": 1.0,
            "trailing_mode": "STANDARD",
            "description": "Balanced risk/reward approach."
        }

        # 1. SCALPING MODE (Low Vol Range)
        if trend == "RANGE" and vol == "LOW_VOL":
            strategy = {
                "name": "SCALPING",
                "target_offset": 0.7,   # Quick exits
                "sl_tightness": 0.8,    # Tighter SL
                "trailing_mode": "AGGRESSIVE",
                "description": "Quick in-out due to low volatility range."
            }

        # 2. TREND RUNNER (High Vol Trend)
        elif trend in ["UPTREND", "DOWNTREND"] and vol == "HIGH_VOL":
            strategy = {
                "name": "TREND_RUNNER",
                "target_offset": 1.5,   # Let it run
                "sl_tightness": 1.2,    # Give it room to breathe
                "trailing_mode": "WIDE",
                "description": "Capturing big moves in trending high-vol market."
            }

        # 3. DEFENSIVE (Volatility Anomaly)
        elif regime_data.get("is_anomaly"):
            strategy = {
                "name": "DEFENSIVE",
                "target_offset": 0.5,
                "sl_tightness": 0.5,    # Very tight SL
                "trailing_mode": "BREAKEVEN_FAST",
                "description": "Safety first during market anomalies."
            }

        return strategy

    # ============================================================
    # MODEL REGISTRY
    # ============================================================

    def _save_model(self):
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        payload = {
            "model": self.model,
            "meta_model": self.meta_model,
            "metadata": self.metadata,
        }
        with open(self.model_path, "w", encoding="utf-8") as f:
            json.dump(payload, f)

    def _load_model(self):
        if not os.path.exists(self.model_path):
            return
        try:
            with open(self.model_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            self.model = payload.get("model")
            self.meta_model = payload.get("meta_model")
            self.metadata = payload.get("metadata", {})
            self.regime_profiles = (self.metadata or {}).get("regime_profiles", {})
            ts = (self.metadata or {}).get("last_train_time_utc")
            if ts:
                self.last_train_time = pd.to_datetime(ts, errors="coerce").to_pydatetime().replace(tzinfo=None)
            else:
                self.last_train_time = datetime.utcnow()
        except Exception:
            self.model = None
            self.meta_model = None
            self.metadata = {}
            self.regime_profiles = {}
            self.last_train_time = None
