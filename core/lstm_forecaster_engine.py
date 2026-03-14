# ============================================================
# 🔮 LSTM PRICE FORECASTER - PERSISTENT VERSION (ZERO COST)
# Uses PyTorch (CPU) to predict the next 5-10 minutes.
# Fixed: Saves and loads model weights to/from disk.
# ============================================================

import torch
import torch.nn as nn
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import warnings
import os

warnings.filterwarnings("ignore")

MODEL_DIR = "database/models"
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)

class PriceLSTM(nn.Module):
    def __init__(self, input_size=1, hidden_size=32, num_layers=1, output_size=1):
        super(PriceLSTM, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        out, _ = self.lstm(x, (h0, c0))
        out = self.fc(out[:, -1, :])
        return out

class LSTMForecasterEngine:
    def __init__(self, symbol="NIFTY", window_size=60, forecast_steps=10):
        self.symbol = symbol
        self.window_size = window_size
        self.forecast_steps = forecast_steps
        self.model = PriceLSTM()
        self.scaler = MinMaxScaler()
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=0.01)
        self.criterion = nn.MSELoss()
        self.is_trained = False
        self.model_path = os.path.join(MODEL_DIR, f"lstm_{symbol.lower()}.pth")
        
        # Load existing model if available
        self._load_model()

    def _load_model(self):
        if os.path.exists(self.model_path):
            try:
                self.model.load_state_dict(torch.load(self.model_path))
                self.model.eval()
                self.is_trained = True
            except: pass

    def _save_model(self):
        try:
            torch.save(self.model.state_dict(), self.model_path)
        except: pass

    def _prepare_data(self, df):
        if len(df) < self.window_size + self.forecast_steps + 50:
            return None, None
        
        data = df['close'].values.reshape(-1, 1)
        scaled_data = self.scaler.fit_transform(data)
        
        X, y = [], []
        for i in range(len(scaled_data) - self.window_size - self.forecast_steps):
            X.append(scaled_data[i : i + self.window_size])
            y.append(scaled_data[i + self.window_size + self.forecast_steps - 1])
            
        return torch.FloatTensor(np.array(X)), torch.FloatTensor(np.array(y))

    def train_incremental(self, df):
        try:
            X, y = self._prepare_data(df)
            if X is None: return False
            
            self.model.train()
            X_train, y_train = X[-200:], y[-200:]
            
            for epoch in range(5):
                self.optimizer.zero_grad()
                outputs = self.model(X_train)
                loss = self.criterion(outputs, y_train)
                loss.backward()
                self.optimizer.step()
            
            self.is_trained = True
            self._save_model() # Save after training
            return True
        except Exception:
            return False

    def predict_future(self, df):
        try:
            if not self.is_trained:
                if not self.train_incremental(df):
                    return {"direction": "NEUTRAL", "forecast": 0.0, "status": "INITIALIZING"}

            self.model.eval()
            data = df['close'].values.reshape(-1, 1)
            # Need to refit scaler on current window for prediction
            self.scaler.fit(data[-200:])
            scaled_input = self.scaler.transform(data[-self.window_size:])
            input_tensor = torch.FloatTensor(scaled_input).unsqueeze(0)
            
            with torch.no_grad():
                pred_scaled = self.model(input_tensor)
                
            predicted_price = float(self.scaler.inverse_transform(pred_scaled.numpy())[0,0])
            current_price = float(df['close'].iloc[-1])
            
            diff = ((predicted_price / current_price) - 1) * 100
            
            direction = "NEUTRAL"
            if diff > 0.05: direction = "UPWARD"
            elif diff < -0.05: direction = "DOWNWARD"
            
            return {
                "direction": direction,
                "forecast_diff_pct": round(diff, 3),
                "forecast_price": round(predicted_price, 2),
                "status": "READY"
            }
        except Exception:
            return {"direction": "NEUTRAL", "forecast": 0.0, "status": "ERROR"}
