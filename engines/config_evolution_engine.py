import json
import os
from .evaluation_engine import EvaluationEngine

class ConfigEvolutionEngine:
    """
    Evaluates performance and tuning of strategy parameters based on live and replay data.
    """
    def __init__(self, db_path="database/trades.db", params_path="database/optimized_params.json"):
        self.evaluation_engine = EvaluationEngine(db_path=db_path)
        self.params_path = params_path
        self.current_config = self._load_config()

    def _load_config(self):
        if os.path.exists(self.params_path):
            with open(self.params_path, "r") as f:
                return json.load(f)
        return {
            "version": "1.0",
            "min_confidence": 20,
            "target_multiplier": 1.5,
            "loss_cooldown_minutes": 0
        }

    def _save_config(self, config):
        os.makedirs(os.path.dirname(self.params_path), exist_ok=True)
        with open(self.params_path, "w") as f:
            json.dump(config, f, indent=4)

    def generate_challenger(self, metrics):
        """
        Creates a new candidate config based on evaluation metrics.
        """
        challenger = self.current_config.copy()
        
        # Simple tuning logic
        if metrics.get("win_rate", 0) < 40:
            challenger["min_confidence"] += 5
        elif metrics.get("win_rate", 0) > 55:
            challenger["min_confidence"] = max(10, challenger["min_confidence"] - 2)
            
        challenger["version"] = f"1.{int(challenger['version'].split('.')[1]) + 1}"
        return challenger

    def evaluate_and_evolve(self):
        print("Running evolution cycle...")
        
        # Get live and replay metrics
        live_metrics = self.evaluation_engine.evaluate_performance(trade_mode="LIVE_PAPER")
        replay_metrics = self.evaluation_engine.evaluate_performance(trade_mode="HISTORICAL_REPLAY")
        
        print("Live Metrics:", live_metrics)
        print("Replay Metrics:", replay_metrics)
        
        # Decide if we need to tune
        if live_metrics.get("total_trades", 0) < 10 and replay_metrics.get("total_trades", 0) < 10:
            print("Not enough data to evolve.")
            return
            
        # Prioritize live metrics if sufficient, otherwise use replay
        metrics_to_use = live_metrics if live_metrics.get("total_trades", 0) >= 10 else replay_metrics
        
        challenger_config = self.generate_challenger(metrics_to_use)
        
        # Promotion criteria
        if metrics_to_use.get("win_rate", 0) > 0: # simplified promotion check
            print(f"Promoting challenger config {challenger_config['version']}")
            self._save_config(challenger_config)
            self.current_config = challenger_config
        else:
            print("Challenger did not pass promotion checks.")
