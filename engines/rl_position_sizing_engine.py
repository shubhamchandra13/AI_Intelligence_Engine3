import json
import os
import numpy as np
from datetime import datetime

class RLPositionSizingEngine:
    """
    Reinforcement Learning (RL) Position Sizing Engine.
    Uses Q-Learning Lite to optimize lot sizes based on past performance.
    'Experience' is stored in q_table.json.
    """
    def __init__(self, q_table_path="database/rl_q_table.json"):
        self.q_table_path = q_table_path
        self.learning_rate = 0.1
        self.discount_factor = 0.9
        self.exploration_rate = 0.2  # 20% chance to explore different sizes
        
        # Actions: Lot Multipliers (0.5x, 0.75x, 1.0x, 1.25x, 1.5x)
        self.actions = [0.5, 0.75, 1.0, 1.25, 1.5]
        self.q_table = self._load_q_table()

    def _load_q_table(self):
        if os.path.exists(self.q_table_path):
            try:
                with open(self.q_table_path, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_q_table(self):
        os.makedirs(os.path.dirname(self.q_table_path), exist_ok=True)
        with open(self.q_table_path, 'w') as f:
            json.dump(self.q_table, f, indent=4)

    def _get_state_key(self, regime, confidence):
        # State = (Regime Name + Confidence Bracket)
        conf_bracket = int(confidence / 10) * 10
        return f"{regime}_{conf_bracket}"

    def get_optimal_multiplier(self, regime, confidence):
        """
        Decides the best lot multiplier for the current state.
        """
        state = self._get_state_key(regime, confidence)
        
        # Exploration vs Exploitation
        if np.random.random() < self.exploration_rate or state not in self.q_table:
            return np.random.choice(self.actions)
        
        # Exploitation: Pick action with highest Q-value
        q_values = self.q_table[state]
        best_action_idx = np.argmax(q_values)
        return self.actions[best_action_idx]

    def update_knowledge(self, regime, confidence, multiplier, pnl_pct):
        """
        Updates the Q-Table based on the result of a trade.
        Reward = PnL % (Positive if Profit, Negative if Loss)
        """
        state = self._get_state_key(regime, confidence)
        action_idx = self.actions.index(multiplier) if multiplier in self.actions else 2 # Default to 1.0x
        
        if state not in self.q_table:
            self.q_table[state] = [0.0] * len(self.actions)
            
        # Reward calculation: PnL % is the core signal
        reward = pnl_pct 
        
        # Q-Learning Formula: Q(s,a) = Q(s,a) + alpha * [reward + gamma * max(Q(s')) - Q(s,a)]
        old_q = self.q_table[state][action_idx]
        new_q = old_q + self.learning_rate * (reward - old_q)
        
        self.q_table[state][action_idx] = round(new_q, 4)
        self._save_q_table()
        
        return f"RL Knowledge Updated: State={state}, Action={multiplier}x, Q={round(new_q, 4)}"
